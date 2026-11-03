#!/usr/bin/env node
// Node 20+, standard library only. Importable client and CLI; no embedded secrets.
import https from 'node:https';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { randomUUID } from 'node:crypto';
import { pipeline } from 'node:stream/promises';

const sensitive = /^(?:.*(?:token|secret|password|authorization|api.?key|cookie|private.?key).*)$/i;
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
export const getAt = (data, dotted) => dotted.split('.').reduce((v, k) => v?.[k], data);
export async function readJSON(file) {
  const text = await fs.readFile(file, 'utf8');
  try { return JSON.parse(text.replace(/^\uFEFF/, '')); }
  catch { throw new Error('Invalid JSON file; correct its syntax without displaying potentially secret contents: ' + file); }
}
export async function readEnv(file) {
  const values = {};
  for (const line of (await fs.readFile(file, 'utf8')).replace(/^\uFEFF/, '').split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const match = trimmed.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!match || Object.hasOwn(values, match[1])) throw new Error('Invalid or duplicate .env setting; inspect it locally without displaying its contents');
    let value = match[2];
    if (value.startsWith('"') || value.startsWith("'")) {
      const quoted = value.match(/^(["'])(.*?)\1\s*(?:#.*)?$/);
      if (!quoted) throw new Error('Invalid quoted .env setting; inspect it locally without displaying its contents');
      value = quoted[2];
    } else value = value.replace(/\s+#.*$/, '').trim();
    values[match[1]] = value;
  }
  return values; // Literal values only: no shell execution, interpolation, or expansion.
}

export async function loadProfile(options = {}) {
  const explicitEnv = options['env-file'] || process.env.QUALTRICS_ENV_FILE;
  const profilePath = options.profile || process.env.QUALTRICS_PROFILE ||
    (!explicitEnv && path.join(os.homedir(), '.config', 'qualtrics', 'profile.json'));
  const profile = profilePath ? await readJSON(profilePath) : {};
  if (explicitEnv) profile.envFile = path.resolve(explicitEnv);
  const env = profile.envFile ? await readEnv(profile.envFile) : {};
  if (!profile.baseURL && !profile.datacenter) {
    profile.baseURL = process.env.QUALTRICS_BASE_URL || env.QUALTRICS_BASE_URL;
    profile.datacenter = process.env.QUALTRICS_DATACENTER || env.QUALTRICS_DATACENTER;
  }
  if (!profile.baseURL && !profile.datacenter) throw new Error('Configure the account datacenter/base URL; do not guess one from an API key');
  return profile;
}

export class QualtricsClient {
  constructor(profile, { transport, delay = sleep, retries = 3 } = {}) {
    this.profile = profile;
    this.base = new URL(profile.baseURL || `https://${profile.datacenter}.qualtrics.com/API/v3/`);
    if (this.base.protocol !== 'https:' || this.base.username || this.base.password || this.base.search || this.base.hash)
      throw new Error('Profile baseURL must be an HTTPS URL without credentials, query, or fragment');
    if (!this.base.pathname.endsWith('/')) this.base.pathname += '/';
    this.transport = transport || this.network.bind(this);
    this.delay = delay;
    this.retries = retries;
    this.secrets = [];
  }

  redact(value) {
    if (Array.isArray(value)) return value.map(v => this.redact(v));
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value)
      .map(([k, v]) => [k, sensitive.test(k) ? '[REDACTED]' : this.redact(v)]));
    if (typeof value === 'string') {
      for (const secret of this.secrets) if (secret) value = value.split(secret).join('[REDACTED]');
      return value.replace(/([?&](?:access_token|token|api_key|client_secret)=)[^&#\s]*/gi, '$1[REDACTED]');
    }
    return value;
  }

  rememberSecrets(value, secretField = false) {
    if (typeof value === 'string' && secretField && value && !this.secrets.includes(value)) this.secrets.push(value);
    else if (Array.isArray(value)) for (const item of value) this.rememberSecrets(item, secretField);
    else if (value && typeof value === 'object' && !Buffer.isBuffer(value))
      for (const [key, item] of Object.entries(value)) this.rememberSecrets(item, secretField || sensitive.test(key));
  }

  rememberPayload(body, contentType) {
    if (!Buffer.isBuffer(body)) this.rememberSecrets(body);
    else if (/^application\/x-www-form-urlencoded(?:;|$)/i.test(contentType || ''))
      for (const [name, value] of new URLSearchParams(body.toString('utf8'))) this.rememberSecrets({ [name]: value });
    else if (/json/i.test(contentType || '')) {
      try { this.rememberSecrets(JSON.parse(body.toString('utf8'))); } catch { /* Raw invalid JSON is sent only if explicitly requested. */ }
    }
  }

  rememberHeader(name, value) {
    if (sensitive.test(name)) this.rememberSecrets(String(value), true);
    if (/^authorization$/i.test(name)) {
      const match = String(value).match(/^(Bearer|Basic)\s+(.+)$/i);
      if (match) {
        this.rememberSecrets(match[2], true);
        if (match[1].toLowerCase() === 'basic') {
          const decoded = Buffer.from(match[2], 'base64').toString('utf8');
          this.rememberSecrets(decoded, true);
          if (decoded.includes(':')) this.rememberSecrets(decoded.slice(decoded.indexOf(':') + 1), true);
        }
      }
    }
  }

  async authHeaders() {
    const env = this.profile.envFile ? await readEnv(this.profile.envFile) : {};
    const bearer = process.env.QUALTRICS_ACCESS_TOKEN || env.QUALTRICS_ACCESS_TOKEN || (this.profile.bearerTokenFile &&
      (await fs.readFile(this.profile.bearerTokenFile, 'utf8')).trim());
    const key = bearer ? null : (process.env.QUALTRICS_API_TOKEN || process.env.APIKEY || env.QUALTRICS_API_TOKEN || env.APIKEY || (this.profile.keyFile &&
      (await fs.readFile(this.profile.keyFile, 'utf8')).trim()));
    const secret = bearer || key;
    if (!secret || /[\r\n]/.test(secret)) throw new Error('Missing or invalid credential; fill the private .env APIKEY value, configure a credential file, or use a supported environment variable');
    this.secrets.push(secret);
    return bearer ? { Authorization: `Bearer ${secret}` } : { 'X-API-TOKEN': secret };
  }

  url(target, query = {}, root = false) {
    if (typeof target !== 'string' || !target || target.includes('\\') || target.startsWith('//'))
      throw new Error('Expected an API path or a same-origin API URL');
    let url;
    if (/^https?:/i.test(target)) url = new URL(target);
    else if (root || target.startsWith(this.base.pathname)) url = new URL(target, this.base.origin);
    else url = new URL(target.replace(/^\//, ''), this.base);
    if (url.origin !== this.base.origin || url.username || url.password || url.hash)
      throw new Error('Refusing an API URL outside the configured origin');
    if (!root && !url.pathname.startsWith(this.base.pathname)) throw new Error('API path escaped the configured base path');
    for (const [key, value] of Object.entries(query)) for (const item of Array.isArray(value) ? value : [value])
      if (item !== undefined && item !== null) url.searchParams.append(key, String(item));
    return url;
  }

  async network(url, options) {
    const tls = {};
    for (const [field, source] of [['cert', 'certFile'], ['key', 'tlsKeyFile'], ['ca', 'caFile']])
      if (this.profile[source]) tls[field] = await fs.readFile(this.profile[source]);
    if (this.profile.passphraseFile) tls.passphrase = (await fs.readFile(this.profile.passphraseFile, 'utf8')).trim();
    return new Promise((resolve, reject) => {
      const req = https.request(url, { method: options.method, headers: options.headers, ...tls,
        timeout: this.profile.timeoutMs || 30000 }, res => resolve(res));
      req.on('timeout', () => req.destroy(new Error('Request timed out')));
      req.on('error', () => reject(new Error('Network request failed; inspect connectivity or TLS configuration. For a write, verify server state before retrying.')));
      if (options.body) req.write(options.body);
      req.end();
    });
  }

  async consume(response) {
    if (Buffer.isBuffer(response.body)) return response.body;
    const parts = [];
    let length = 0;
    for await (const chunk of response) {
      length += chunk.length;
      if (length > 64 * 1024 * 1024) { response.destroy(); throw new Error('Response exceeds 64 MiB; use download with --output for large files'); }
      parts.push(chunk);
    }
    return Buffer.concat(parts);
  }

  async send({ method = 'GET', target, query, body, headers = {}, contentType, root = false, noAuth = false }) {
    method = method.toUpperCase();
    if (!['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'].includes(method)) throw new Error('Unsupported HTTP method');
    const url = this.url(target, query, root);
    this.rememberPayload(body, contentType);
    const actualHeaders = { Accept: 'application/json', ...(noAuth ? {} : await this.authHeaders()), ...headers };
    for (const [name, value] of Object.entries(actualHeaders)) {
      if (['host', 'content-length', 'transfer-encoding'].includes(name.toLowerCase())) throw new Error('Transport header cannot be overridden');
      this.rememberHeader(name, value);
    }
    const payload = body === undefined ? undefined : Buffer.isBuffer(body) ? body : Buffer.from(JSON.stringify(body));
    if (payload) {
      actualHeaders['Content-Type'] = contentType || 'application/json';
      actualHeaders['Content-Length'] = String(payload.length);
    }
    for (let attempt = 0; ; attempt++) {
      const response = await this.transport(url, { method, headers: actualHeaders, body: payload });
      const status = response.statusCode ?? response.status;
      if (status >= 300 && status < 400) { await this.consume(response); throw new Error(`HTTP ${status}: redirects are not followed; verify the correct datacenter or download URL`); }
      if (['GET', 'HEAD', 'OPTIONS'].includes(method) && [429, 502, 503, 504].includes(status) && attempt < this.retries) {
        await this.consume(response);
        const retry = response.headers?.['retry-after'];
        const seconds = retry && /^\d+$/.test(retry) ? Number(retry) : retry ? Math.max(0, (Date.parse(retry) - Date.now()) / 1000) : NaN;
        // Do not retry earlier than a long server-directed delay; return control instead.
        if (seconds > 30) throw new Error(`HTTP ${status}: server requests a retry after ${seconds} seconds; retry later`);
        await this.delay(Number.isFinite(seconds) ? seconds * 1000 : Math.min(1000 * 2 ** attempt, 15000));
        continue;
      }
      return { response, status, method, url };
    }
  }

  async request(options) {
    const { response, status } = await this.send(options);
    const bytes = await this.consume(response);
    const text = bytes.toString('utf8');
    let data;
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    if (status < 200 || status >= 300) {
      const detail = typeof data === 'object' ? data?.meta?.error || data?.error || {} : { message: 'Non-JSON error response' };
      throw new Error(JSON.stringify(this.redact({ httpStatus: status, error: detail, requestId: data?.meta?.requestId,
        ...(options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase()) ? { nextStep: 'Verify server state before retrying a write' } : {}) })));
    }
    return { status, data };
  }

  async *pages(target, { query, maxPages = 1000 } = {}) {
    if (!Number.isInteger(maxPages) || maxPages <= 0) throw new Error('maxPages must be a positive integer');
    const visited = new Set();
    for (let page = 0; target && page < maxPages; page++) {
      const normalized = this.url(target, page ? undefined : query).href;
      if (visited.has(normalized)) throw new Error('Pagination loop detected');
      visited.add(normalized);
      const { data } = await this.request({ target: normalized });
      yield data;
      target = data?.result?.nextPage ?? data?.nextPage ?? data?.links?.next?.href ?? data?.result?.links?.next?.href;
      if (target && typeof target !== 'string') throw new Error('Unexpected pagination link format');
      if (page + 1 === maxPages && target) throw new Error('Pagination limit reached; results are incomplete');
    }
  }

  async poll(target, { statusPath = 'result.status', timeoutMs = 120000, intervalMs = 1000,
    success = ['complete', 'completed', 'success', 'succeeded'], failure = ['failed', 'failure', 'error'] } = {}) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const { data } = await this.request({ target });
      const status = String(getAt(data, statusPath)).toLowerCase();
      if (success.includes(status)) return data;
      if (failure.includes(status)) throw new Error(JSON.stringify(this.redact({ jobFailed: true, data })));
      if (status === 'undefined') throw new Error('Job status field missing; inspect the endpoint contract and specify --status-path');
      const remaining = deadline - Date.now();
      if (remaining <= 0) break;
      await this.delay(Math.min(intervalMs, remaining));
      intervalMs = Math.min(intervalMs * 1.5, 15000);
    }
    throw new Error('Job polling timed out; preserve its job ID and resume polling instead of starting another job');
  }

  async download(target, output, options = {}) {
    await fs.access(path.dirname(path.resolve(output)));
    try { await fs.access(output); throw new Error('Output already exists; choose a new file'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    const { response, status } = await this.send({ ...options, target });
    if (status < 200 || status >= 300) {
      await this.consume(response);
      throw new Error(`Download failed with HTTP ${status}`);
    }
    const temporary = output + '.' + randomUUID() + '.part';
    try {
      const contentType = response.headers?.['content-type'] || '';
      if (/json/i.test(contentType)) {
        const bytes = await this.consume(response);
        await fs.writeFile(temporary, JSON.stringify(this.redact(JSON.parse(bytes.toString('utf8'))), null, 2) + '\n', { flag: 'wx' });
      } else if (Buffer.isBuffer(response.body)) {
        await fs.writeFile(temporary, response.body, { flag: 'wx' });
      } else {
        const { createWriteStream } = await import('node:fs');
        await pipeline(response, createWriteStream(temporary, { flags: 'wx' }));
      }
      // COPYFILE_EXCL prevents overwriting a destination created while downloading.
      await fs.copyFile(temporary, output, 1);
      return { status, output: path.resolve(output), bytes: (await fs.stat(output)).size };
    } finally { await fs.rm(temporary, { force: true }); }
  }
}

export async function multipart(parts) {
  const boundary = 'QualtricsSkill' + randomUUID().replaceAll('-', '');
  const chunks = [];
  const clean = value => String(value).replace(/["\r\n]/g, '_');
  for (const part of parts) {
    const disposition = `Content-Disposition: form-data; name="${clean(part.name)}"`;
    if (part.file) {
      chunks.push(Buffer.from(`--${boundary}\r\n${disposition}; filename="${clean(path.basename(part.file))}"\r\nContent-Type: ${clean(part.contentType || 'application/octet-stream')}\r\n\r\n`));
      chunks.push(await fs.readFile(part.file));
    } else {
      const contentHeader = part.contentType ? `\r\nContent-Type: ${clean(part.contentType)}` : '';
      const value = part.json === undefined ? part.value ?? '' : JSON.stringify(part.json);
      chunks.push(Buffer.from(`--${boundary}\r\n${disposition}${contentHeader}\r\n\r\n${value}`));
    }
    chunks.push(Buffer.from('\r\n'));
  }
  chunks.push(Buffer.from(`--${boundary}--\r\n`));
  return { body: Buffer.concat(chunks), contentType: `multipart/form-data; boundary=${boundary}` };
}

export function parseArgs(argv) {
  const flags = new Set(['execute', 'root', 'no-auth']);
  const valued = new Set(['profile', 'env-file', 'method', 'path', 'query', 'json-file', 'body-file', 'content-type', 'multipart-file',
    'headers-file', 'output', 'items-path', 'max-pages', 'status-path', 'timeout-seconds', 'success', 'failure', 'survey', 'format']);
  const options = { command: argv[0] || 'help' };
  for (let i = 1; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, '');
    if (!argv[i].startsWith('--') || (!flags.has(key) && !valued.has(key))) throw new Error('Unknown option: ' + argv[i]);
    if (flags.has(key)) options[key] = true;
    else {
      if (argv[i + 1] === undefined || argv[i + 1].startsWith('--')) throw new Error('Missing value for --' + key);
      const value = argv[++i];
      if (key === 'query') (options.query ||= []).push(value);
      else if (options[key] !== undefined) throw new Error('Duplicate option --' + key);
      else options[key] = value;
    }
  }
  return options;
}

export async function run(options, client) {
  const command = options.command;
  let target = options.path;
  const query = {};
  for (const pair of options.query || []) {
    const separator = pair.indexOf('=');
    if (separator < 1) throw new Error('--query expects name=value');
    const key = pair.slice(0, separator), value = pair.slice(separator + 1);
    if (query[key] === undefined) query[key] = value;
    else query[key] = [...(Array.isArray(query[key]) ? query[key] : [query[key]]), value];
  }
  if (command === 'whoami') target = '/whoami';
  if (command === 'export') {
    if (!/^SV_[A-Za-z0-9]+$/.test(options.survey || '') || !options.output) throw new Error('export requires --survey SV_... and --output');
    // Check the destination before creating an export job.
    await fs.access(path.dirname(path.resolve(options.output)));
    try { await fs.access(options.output); throw new Error('Output already exists'); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    const format = options.format || 'csv';
    if (!['csv', 'tsv', 'json', 'ndjson', 'spss', 'xml'].includes(format)) throw new Error('Unsupported export format; check the current contract');
    const base = `/surveys/${options.survey}/export-responses`;
    const body = options['json-file'] ? await readJSON(options['json-file']) : { format };
    const { data } = await client.request({ method: 'POST', target: base, body });
    const progressId = data?.result?.progressId;
    if (!progressId) throw new Error('Export job did not return progressId');
    // Printing the job locator allows recovery if polling is interrupted.
    process.stderr.write(JSON.stringify({ progressId, pollPath: `${base}/${encodeURIComponent(progressId)}` }) + '\n');
    const progress = await client.poll(`${base}/${encodeURIComponent(progressId)}`, { timeoutMs: positive(options['timeout-seconds'] || 120) * 1000 });
    const fileId = progress?.result?.fileId;
    if (!fileId) throw new Error('Completed export did not return fileId');
    return client.download(`${base}/${encodeURIComponent(fileId)}/file`, options.output);
  }
  if (!target) throw new Error('This command requires --path');
  if (command === 'paginate') {
    const items = [];
    for await (const page of client.pages(target, { query, maxPages: positive(options['max-pages'] || 1000) })) {
      const rows = getAt(page, options['items-path'] || 'result.elements');
      if (!Array.isArray(rows)) throw new Error('Item array missing; use --items-path from this endpoint contract');
      items.push(...rows);
    }
    return { count: items.length, elements: items };
  }
  if (command === 'poll') return client.poll(target, { statusPath: options['status-path'] || 'result.status',
    timeoutMs: positive(options['timeout-seconds'] || 120) * 1000,
    ...(options.success ? { success: options.success.toLowerCase().split(',') } : {}),
    ...(options.failure ? { failure: options.failure.toLowerCase().split(',') } : {}) });
  if (command === 'download') {
    if (!options.output) throw new Error('download requires --output');
    return client.download(client.url(target, query).href, options.output);
  }
  if (!['request', 'whoami'].includes(command)) throw new Error('Unknown command: ' + command);
  const method = (options.method || 'GET').toUpperCase();
  const modes = ['json-file', 'body-file', 'multipart-file'].filter(key => options[key]);
  if (modes.length > 1) throw new Error('Choose one body mode');
  let body, contentType = options['content-type'];
  if (options['json-file']) body = await readJSON(options['json-file']);
  if (options['body-file']) { if (!contentType) throw new Error('--body-file requires --content-type'); body = await fs.readFile(options['body-file']); }
  if (options['multipart-file']) {
    const parts = await readJSON(options['multipart-file']);
    for (const part of parts) {
      client.rememberSecrets({ [part.name]: part.json ?? part.value });
      client.rememberSecrets(part.json);
    }
    ({ body, contentType } = await multipart(parts));
  }
  const headers = options['headers-file'] ? await readJSON(options['headers-file']) : {};
  client.rememberPayload(body, contentType);
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && !options.execute) return { dryRun: true, method,
    url: client.url(target, query, options.root).href, body: Buffer.isBuffer(body) ? { bytes: body.length, contentType } : client.redact(body),
    nextStep: 'Review the official operation contract and existing user authorization, then add --execute to perform this operation' };
  const request = { method, target, query, body, contentType, headers, root: options.root, noAuth: options['no-auth'] };
  if (options.output) return client.download(client.url(target, query, options.root).href, options.output, { ...request, query: undefined });
  return client.request(request);
}

function positive(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) throw new Error('Expected a positive numeric limit');
  return number;
}

const HELP = `Qualtrics API helper — Node 20+, no dependencies
Commands: whoami, request, paginate, poll, download, export
Profile: --profile FILE, QUALTRICS_PROFILE, or ~/.config/qualtrics/profile.json
Credentials: private profile.envFile with APIKEY=; --env-file FILE; keyFile / bearerTokenFile
Environment: QUALTRICS_API_TOKEN or APIKEY / QUALTRICS_ACCESS_TOKEN; QUALTRICS_ENV_FILE
request --path /surveys [--method GET] [--query name=value ...]
        [--json-file FILE | --body-file FILE --content-type TYPE | --multipart-file FILE]
        [--headers-file FILE] [--root] [--no-auth] [--execute]
paginate --path /surveys [--items-path result.elements] [--max-pages 1000]
poll --path JOB_PATH [--status-path result.status] [--success complete,success] [--timeout-seconds 120]
download --path FILE_PATH --output FILE
export --survey SV_ID --output FILE.zip [--format csv] [--json-file PARAMETERS.json]
Generic request writes preview unless --execute is supplied. Export immediately creates a data-export job.
All stdout JSON is redacted. Never pass credentials as command arguments.
Use catalog.mjs to look up the exact endpoint, schemas and permissions before a request.
`;

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  let client;
  try {
    const options = parseArgs(process.argv.slice(2));
    if (['help', '--help', '-h'].includes(options.command)) process.stdout.write(HELP);
    else {
      client = new QualtricsClient(await loadProfile(options));
      process.stdout.write(JSON.stringify(client.redact(await run(options, client)), null, 2) + '\n');
    }
  } catch (error) {
    process.stderr.write(JSON.stringify({ error: client ? client.redact(error.message) : 'Configuration or argument error: ' + error.message }) + '\n');
    process.exitCode = 1;
  }
}

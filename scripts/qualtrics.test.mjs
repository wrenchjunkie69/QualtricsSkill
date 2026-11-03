import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { Readable } from 'node:stream';
import { QualtricsClient, multipart, parseArgs, run, readJSON, readEnv, loadProfile } from './qualtrics.mjs';
import { catalog, contract, select } from './catalog.mjs';

// Isolate tests from any credentials inherited from the user's environment.
delete process.env.QUALTRICS_ACCESS_TOKEN;
delete process.env.QUALTRICS_API_TOKEN;
delete process.env.APIKEY;
delete process.env.QUALTRICS_PROFILE;
delete process.env.QUALTRICS_ENV_FILE;
delete process.env.QUALTRICS_BASE_URL;
delete process.env.QUALTRICS_DATACENTER;

const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'qualtrics-skill-test-'));
const keyFile = path.join(temporary, 'credential.txt');
const fixtureCredential = 'local-test-credential-does-not-authenticate';
await fs.writeFile(keyFile, fixtureCredential);
const profile = { datacenter: 'pdx1', keyFile };
const reply = (data, status = 200, headers = {}) => ({ statusCode: status, headers, body: Buffer.from(JSON.stringify(data)) });
function client(transport) { return new QualtricsClient(profile, { transport, delay: async () => {} }); }
test.after(async () => fs.rm(temporary, { recursive: true, force: true }));

test('reads credentials from file and redacts literal and structured secrets', async () => {
  const c = client(async (_url, options) => {
    assert.equal(options.headers['X-API-TOKEN'], fixtureCredential);
    return reply({ access_token: fixtureCredential, echo: fixtureCredential });
  });
  const result = c.redact((await c.request({ target: '/whoami' })).data);
  assert.deepEqual(result, { access_token: '[REDACTED]', echo: '[REDACTED]' });
});
test('origin, URL credential, scheme and base-path escape checks', () => {
  const c = client();
  for (const target of ['https://example.org/API/v3/whoami', '//example.org/x', '/../oauth2/token', 'https://x:y@pdx1.qualtrics.com/API/v3/whoami', '\\evil\\x'])
    assert.throws(() => c.url(target));
  assert.throws(() => new QualtricsClient({ baseURL: 'http://pdx1.qualtrics.com/API/v3/' }));
  assert.equal(c.url('/oauth2/token', {}, true).pathname, '/oauth2/token');
});
test('query values encode correctly and preserve repeated parameters', () => {
  const url = client().url('/surveys', { filter: ['a & b', 'c'], pageSize: 2 });
  assert.deepEqual(url.searchParams.getAll('filter'), ['a & b', 'c']);
  assert.equal(url.pathname, '/API/v3/surveys');
});
for (const method of ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH', 'DELETE']) {
  test(`transport supports ${method}`, async () => {
    const c = client(async (_url, options) => { assert.equal(options.method, method); return reply({ ok: true }); });
    assert.equal((await c.request({ method, target: '/test' })).status, 200);
  });
}
test('write preview performs no request; execute sends JSON', async () => {
  let calls = 0;
  const c = client(async (_url, options) => { calls++; assert.deepEqual(JSON.parse(options.body), { name: 'Draft' }); return reply({ ok: true }); });
  const jsonFile = path.join(temporary, 'payload.json');
  await fs.writeFile(jsonFile, JSON.stringify({ name: 'Draft' }));
  const options = { command: 'request', method: 'POST', path: '/surveys', 'json-file': jsonFile };
  assert.equal((await run(options, c)).dryRun, true);
  assert.equal(calls, 0);
  await run({ ...options, execute: true }, c);
  assert.equal(calls, 1);
});
test('raw body and explicit MIME type reach the transport unchanged', async () => {
  const file = path.join(temporary, 'import.csv');
  await fs.writeFile(file, 'x,y\n1,2\n');
  const c = client(async (_url, options) => {
    assert.equal(options.body.toString(), 'x,y\n1,2\n');
    assert.equal(options.headers['Content-Type'], 'text/csv; charset=UTF-8');
    return reply({ ok: true });
  });
  await run({ command: 'request', method: 'POST', path: '/import', 'body-file': file, 'content-type': 'text/csv; charset=UTF-8', execute: true }, c);
});
test('multipart preserves binary content and separates named fields', async () => {
  const file = path.join(temporary, 'upload.bin');
  await fs.writeFile(file, Buffer.from([0, 255, 128, 13, 10]));
  const built = await multipart([{ name: 'survey', file }, { name: 'name', value: 'Draft' }]);
  assert.ok(built.body.includes(Buffer.from([0, 255, 128, 13, 10])));
  assert.ok(built.body.includes(Buffer.from('name="name"\r\n\r\nDraft')));
  assert.match(built.contentType, /^multipart\/form-data; boundary=/);
});
test('multipart JSON parts carry serialized objects and per-part MIME types', async () => {
  const built = await multipart([{ name: 'response', json: { values: { QID1: 1 } }, contentType: 'application/json' }]);
  assert.ok(built.body.includes(Buffer.from('Content-Type: application/json\r\n\r\n{"values":{"QID1":1}}')));
});
test('bearer credentials take precedence and root no-auth requests omit defaults', async () => {
  const bearerFile = path.join(temporary, 'bearer.txt');
  await fs.writeFile(bearerFile, 'test-bearer-not-live');
  const c = new QualtricsClient({ ...profile, bearerTokenFile: bearerFile }, { transport: async (url, options) => {
    if (url.pathname === '/oauth2/token') {
      assert.equal(options.headers.Authorization, undefined);
      assert.equal(options.headers['X-API-TOKEN'], undefined);
    } else {
      assert.equal(options.headers.Authorization, 'Bearer test-bearer-not-live');
      assert.equal(options.headers['X-API-TOKEN'], undefined);
    }
    return reply({ ok: true });
  } });
  await c.request({ target: '/whoami' });
  await c.request({ method: 'POST', target: '/oauth2/token', root: true, noAuth: true });
});
test('transport-critical header overrides are rejected', async () => {
  const c = client(async () => assert.fail('must not send'));
  await assert.rejects(c.request({ target: '/whoami', headers: { Host: 'evil.org' } }), /cannot be overridden/);
});
test('GET rate limiting retries; writes never automatically retry', async () => {
  let calls = 0;
  const c = client(async () => ++calls === 1 ? reply({}, 429, { 'retry-after': '0' }) : reply({ ok: true }));
  await c.request({ target: '/whoami' });
  assert.equal(calls, 2);
  calls = 0;
  const write = client(async () => { calls++; return reply({}, 503); });
  await assert.rejects(write.request({ method: 'POST', target: '/surveys' }), /Verify server state/);
  assert.equal(calls, 1);
});
test('long Retry-After returns control without retrying early', async () => {
  let calls = 0;
  const c = client(async () => { calls++; return reply({}, 429, { 'retry-after': '120' }); });
  await assert.rejects(c.request({ target: '/surveys' }), /retry later/);
  assert.equal(calls, 1);
});
test('error bodies redact echoed credentials and include request IDs', async () => {
  const c = client(async () => reply({ meta: { requestId: 'request-123', error: { errorMessage: fixtureCredential } } }, 403));
  await assert.rejects(c.request({ target: '/surveys' }), e => !e.message.includes(fixtureCredential) && e.message.includes('request-123'));
});
test('redirects never forward authentication', async () => {
  let calls = 0;
  const c = client(async () => { calls++; return reply({}, 302, { location: 'https://evil.org/' }); });
  await assert.rejects(c.request({ target: '/surveys' }), /redirects are not followed/);
  assert.equal(calls, 1);
});
test('pagination follows the provided URL and collects all elements', async () => {
  const c = client(async url => url.searchParams.has('skipToken') ? reply({ result: { elements: [2], nextPage: null } }) :
    reply({ result: { elements: [1], nextPage: 'https://pdx1.qualtrics.com/API/v3/surveys?skipToken=x' } }));
  assert.deepEqual(await run({ command: 'paginate', path: '/surveys' }, c), { count: 2, elements: [1, 2] });
});
test('pagination blocks cross-origin links before sending a second request', async () => {
  let calls = 0;
  const c = client(async () => { calls++; return reply({ result: { elements: [], nextPage: 'https://evil.org/' } }); });
  await assert.rejects(run({ command: 'paginate', path: '/surveys' }, c), /outside the configured origin/);
  assert.equal(calls, 1);
});
test('pagination loop and incomplete limits raise errors', async () => {
  const c = client(async () => reply({ result: { elements: [], nextPage: 'https://pdx1.qualtrics.com/API/v3/surveys' } }));
  await assert.rejects(run({ command: 'paginate', path: '/surveys' }, c), /loop detected/);
  await assert.rejects(run({ command: 'paginate', path: '/surveys', 'max-pages': 1 }, c), /incomplete/);
});
test('polling recognizes complete and failed jobs', async () => {
  let calls = 0;
  const c = client(async () => reply({ result: { status: ++calls === 1 ? 'inProgress' : 'complete', fileId: 'file1' } }));
  assert.equal((await c.poll('/job')).result.fileId, 'file1');
  await assert.rejects(client(async () => reply({ result: { status: 'failed' } })).poll('/job'), /jobFailed/);
  await assert.rejects(client(async () => reply({ result: {} })).poll('/job'), /status field missing/);
});
test('binary downloads stream to a new file and refuse overwrite', async () => {
  const output = path.join(temporary, 'download.bin');
  const expected = Buffer.from([0, 255, 13, 128]);
  const c = client(async () => Object.assign(Readable.from([expected]), { statusCode: 200, headers: { 'content-type': 'application/zip' } }));
  await c.download('/file', output);
  assert.deepEqual(await fs.readFile(output), expected);
  await assert.rejects(c.download('/file', output), /already exists/);
});
test('JSON file outputs redact secret fields', async () => {
  const output = path.join(temporary, 'download.json');
  const c = client(async () => reply({ access_token: fixtureCredential, result: { ok: true } }, 200, { 'content-type': 'application/json' }));
  await c.download('/file', output);
  assert.equal(JSON.parse(await fs.readFile(output, 'utf8')).access_token, '[REDACTED]');
});
test('failed download removes partial file', async () => {
  const output = path.join(temporary, 'failed.bin');
  const stream = new Readable({ read() { this.destroy(new Error('stream failed')); } });
  const c = client(async () => Object.assign(stream, { statusCode: 200, headers: {} }));
  await assert.rejects(c.download('/file', output), /stream failed/);
  assert.ok(!(await fs.readdir(temporary)).some(name => name.startsWith('failed.bin')));
});
test('export uses create, progress and download endpoints in order', async () => {
  const calls = [], output = path.join(temporary, 'export.zip');
  const c = client(async (url, options) => {
    calls.push([options.method, url.pathname]);
    if (calls.length === 1) return reply({ result: { progressId: 'job1' } });
    if (calls.length === 2) return reply({ result: { status: 'complete', fileId: 'file1' } });
    return { statusCode: 200, headers: {}, body: Buffer.from('ZIP') };
  });
  await run({ command: 'export', survey: 'SV_Test', output }, c);
  assert.deepEqual(calls, [['POST', '/API/v3/surveys/SV_Test/export-responses'], ['GET', '/API/v3/surveys/SV_Test/export-responses/job1'], ['GET', '/API/v3/surveys/SV_Test/export-responses/file1/file']]);
});
test('argument parser rejects ambiguous input and unknown options', () => {
  assert.deepEqual(parseArgs(['request', '--path', '/surveys', '--query', 'a=1', '--query', 'a=2']).query, ['a=1', 'a=2']);
  assert.throws(() => parseArgs(['request', '--oops', 'x']), /Unknown option/);
  assert.throws(() => parseArgs(['request', '--path']), /Missing value/);
});
test('JSON files accept a Windows BOM and syntax errors do not echo contents', async () => {
  const file = path.join(temporary, 'windows.json');
  await fs.writeFile(file, '\uFEFF{"ok":true}');
  assert.deepEqual(await readJSON(file), { ok: true });
  await fs.writeFile(file, fixtureCredential);
  await assert.rejects(readJSON(file), e => !e.message.includes(fixtureCredential));
});
test('OAuth JSON body secrets are redacted from echoed errors and success text', async () => {
  const marker = 'inert-oauth-body-secret';
  const c = client(async () => reply({ error: { message: `Invalid client secret: ${marker}` } }, 400));
  await assert.rejects(c.request({ method: 'POST', target: '/oauth2/token', root: true, noAuth: true,
    body: { client_id: 'public-id', client_secret: marker } }), e => !e.message.includes(marker));
  const success = client(async () => reply({ message: `Echo ${marker}` }));
  const result = await success.request({ method: 'POST', target: '/oauth2/token', root: true, noAuth: true, body: { client_secret: marker } });
  assert.ok(!JSON.stringify(success.redact(result.data)).includes(marker));
});
test('URL-encoded OAuth body secrets are registered before an echoed error', async () => {
  const marker = 'inert+form&secret=value';
  const c = client(async () => reply({ error: { message: `Invalid client secret: ${marker}` } }, 400));
  await assert.rejects(c.request({ method: 'POST', target: '/oauth2/token', root: true, noAuth: true,
    body: Buffer.from(new URLSearchParams({ client_secret: marker }).toString()), contentType: 'application/x-www-form-urlencoded' }),
    e => !e.message.includes(marker));
});
test('multipart manifest secret fields are registered before server error output', async () => {
  const marker = 'inert-multipart-body-secret';
  const file = path.join(temporary, 'parts.json');
  await fs.writeFile(file, JSON.stringify([{ name: 'client_secret', value: marker }]));
  const c = client(async () => reply({ error: { message: `Echo ${marker}` } }, 400));
  await assert.rejects(run({ command: 'request', method: 'POST', path: '/oauth2/token', root: true, 'no-auth': true,
    'multipart-file': file, execute: true }, c), e => !e.message.includes(marker));
});
test('explicit Bearer and Basic authorization payloads are redacted when echoed', async () => {
  const marker = 'inert-header-payload-secret';
  for (const authorization of [`Bearer ${marker}`, 'Basic ' + Buffer.from(`client:${marker}`).toString('base64')]) {
    const c = client(async () => reply({ error: { message: `Echo ${marker}` } }, 401));
    await assert.rejects(c.request({ target: '/oauth2/token', root: true, noAuth: true, headers: { Authorization: authorization } }),
      e => !e.message.includes(marker));
  }
});
test('fractional pagination limits are rejected before any request', async () => {
  let calls = 0;
  const c = client(async () => { calls++; return reply({ result: { elements: [1], nextPage: 'https://pdx1.qualtrics.com/API/v3/surveys?page=2' } }); });
  await assert.rejects(run({ command: 'paginate', path: '/surveys', 'max-pages': '0.5' }, c), /positive integer/);
  assert.equal(calls, 0);
});
test('private .env APIKEY authenticates without expansion and stays redacted', async () => {
  const file = path.join(temporary, 'private.env');
  const marker = 'inert-$literal-marker';
  await fs.writeFile(file, `# private fixture\nAPIKEY='${marker}'\nQUALTRICS_DATACENTER=pdx1\n`);
  const profile = await loadProfile({ 'env-file': file });
  assert.equal(profile.datacenter, 'pdx1');
  assert.equal(profile.envFile, file);
  assert.equal(profile.APIKEY, undefined);
  const c = new QualtricsClient(profile, { transport: async (_url, options) => {
    assert.equal(options.headers['X-API-TOKEN'], marker);
    return reply({ echo: marker });
  } });
  const result = await c.request({ target: '/whoami' });
  assert.equal(c.redact(result.data).echo, '[REDACTED]');
});
test('empty template does not authenticate; malformed env errors do not echo contents', async () => {
  const file = path.join(temporary, 'empty.env');
  await fs.writeFile(file, 'APIKEY=\n');
  const c = new QualtricsClient({ datacenter: 'pdx1', envFile: file }, { transport: async () => assert.fail('must not send') });
  await assert.rejects(c.request({ target: '/whoami' }), /Missing or invalid credential/);
  await fs.writeFile(file, 'APIKEY="inert-private-marker\n');
  await assert.rejects(readEnv(file), e => !e.message.includes('inert-private-marker'));
});
test('every cached contract matches its index and cryptographic checksum', async () => {
  const data = await catalog();
  assert.ok(data.operations.length > 250);
  assert.equal(data.operations.length, data.operationCount);
  assert.equal(new Set(data.operations.map(o => o.key)).size, data.operationCount);
  for (const operation of data.operations) {
    const api = await contract(operation);
    assert.equal(api.method.toUpperCase(), operation.method);
    assert.equal(api.path, operation.path);
    assert.ok(api.responses);
    assert.ok(operation.docs.startsWith('https://developer-docs.qualtrics.com/'));
  }
  assert.equal(select(data.operations, 'survey-sessions-v2--create-session').length, 1);
});

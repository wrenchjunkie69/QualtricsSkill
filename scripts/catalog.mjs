#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { inflateSync } from 'node:zlib';
import { createHash } from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../references/api');
export async function catalog() { return JSON.parse(await fs.readFile(path.join(root, 'catalog.json'), 'utf8')); }
export async function contract(operation) {
  const packed = await fs.readFile(path.join(root, operation.cache));
  if (createHash('sha256').update(packed).digest('hex') !== operation.sha256) throw new Error('Contract checksum mismatch; refresh the catalog');
  return JSON.parse(inflateSync(packed).toString('utf8'));
}
export function select(operations, text) {
  const exact = operations.filter(o => o.key === text || `${o.method} ${o.path}`.toLowerCase() === text.toLowerCase());
  if (exact.length) return exact;
  const terms = text.toLowerCase().split(/\s+/).filter(Boolean);
  return operations.filter(o => terms.every(term => `${o.key} ${o.title} ${o.operationId} ${o.method} ${o.path}`.toLowerCase().includes(term)));
}

async function main() {
  const [command = 'help', ...args] = process.argv.slice(2);
  if (command === 'help') return { usage: ['catalog.mjs domains', 'catalog.mjs search survey export', 'catalog.mjs show KEY', 'catalog.mjs verify'] };
  const data = await catalog();
  if (command === 'domains') return { checkedAt: data.checkedAt, operationCount: data.operationCount,
    domains: [...data.operations.reduce((groups, op) => groups.set(op.domain, (groups.get(op.domain) || 0) + 1), new Map())]
      .map(([name, operations]) => ({ name, operations })) };
  if (command === 'search') return select(data.operations, args.join(' '));
  if (command === 'show') {
    const matches = select(data.operations, args.join(' '));
    if (matches.length !== 1) throw new Error(`Expected exactly one operation; found ${matches.length}. Search first and supply its key.`);
    return { ...matches[0], contract: await contract(matches[0]) };
  }
  if (command === 'verify') {
    const methods = new Set();
    for (const op of data.operations) {
      const api = await contract(op);
      if (api.method.toUpperCase() !== op.method || api.path !== op.path) throw new Error('Index/contract mismatch: ' + op.key);
      if (!op.docs.startsWith('https://developer-docs.qualtrics.com/docs/public-api/')) throw new Error('Non-official documentation URL');
      methods.add(op.method);
    }
    return { verified: data.operations.length, domains: new Set(data.operations.map(o => o.domain)).size, methods: [...methods].sort(), checkedAt: data.checkedAt };
  }
  throw new Error('Unknown catalog command');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { console.log(JSON.stringify(await main(), null, 2)); }
  catch (e) { console.error(JSON.stringify({ error: e.message })); process.exitCode = 1; }
}

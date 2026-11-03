# Client reference

Run `node scripts/qualtrics.mjs help`. Resolve relative script paths against this skill's directory, not the current project. Node 20+ is required; no npm install.

## Configuration

For a new computer use the README installer. The public root `.env` contains only `APIKEY=`. Setup creates a private `~/.config/qualtrics/.env` outside the repository and records it as `envFile` in the non-secret profile. Masked setup or import from an existing token-only private txt file supplies the value without echoing it. Never fill the GitHub template with a real key. Offline analysis requires no account key.

Profile precedence: `--profile FILE`, `QUALTRICS_PROFILE`, then `~/.config/qualtrics/profile.json`. Example (no secret values):

```json
{"datacenter":"your-datacenter","keyFile":"/absolute/path/private-api-token.txt"}
```

Alternatively use `baseURL`, for example `https://pdx1.qualtrics.com/API/v3/`. It must be HTTPS without URL credentials, query or fragment. Trust only a user-supplied or verified organization host. The token file contains only its token, with optional surrounding whitespace. Do not print it.

Credential precedence: process `QUALTRICS_ACCESS_TOKEN`, the envFile's `QUALTRICS_ACCESS_TOKEN`, profile.bearerTokenFile; otherwise process `QUALTRICS_API_TOKEN`/`APIKEY`, envFile `QUALTRICS_API_TOKEN`/`APIKEY`, then profile.keyFile. Bearer tokens use Authorization; API keys use X-API-TOKEN. Supply environment values through the user's secret manager, not echoed shell literals. OAuth token renewal is managed separately; this tool does not silently obtain/refresh tokens.

`--env-file FILE` or `QUALTRICS_ENV_FILE` explicitly selects another dotenv file. It can also provide QUALTRICS_DATACENTER or QUALTRICS_BASE_URL when no explicit profile supplies a host. A standalone explicit env file does not silently reuse a different account's default profile. Values are literal: optional quotes/comments are supported, but no shell execution, variable interpolation or escape expansion occurs. Duplicate/malformed assignments fail without printing their contents. A blank APIKEY does not authenticate.

Optional mTLS fields: `certFile`, `tlsKeyFile`, `caFile`, `passphraseFile`. These point to certificate/private-key/CA/passphrase files outside the skill. `keyFile` remains the API-token file. TLS verification stays enabled. `timeoutMs` sets the per-request timeout (default 30000).

## Generic HTTP

```text
node scripts/qualtrics.mjs request --path /surveys --query pageSize=5
node scripts/qualtrics.mjs request --method POST --path /survey-definitions --json-file draft.json
node scripts/qualtrics.mjs request --method POST --path /survey-definitions --json-file draft.json --execute
```

Supports GET, HEAD, OPTIONS, POST, PUT, PATCH and DELETE. Generic `request` writes preview unless `--execute` is supplied. The `export` convenience command starts its data-export job immediately; use a generic `request` preview to review its POST first when needed. Use existing user authorization and the exact operation schema; this flag does not impose a new permission question.

`--path` accepts an API-relative path, a complete `/API/v3/...` path, or a same-origin absolute URL. Replace and URL-encode all path IDs. Repeated `--query name=value` flags preserve duplicate parameters and encode values. Do not put secrets in query arguments. `--output FILE` saves redacted JSON or streams binary responses to a new file; it refuses overwrite. JSON in memory is limited to 64 MiB. Binary file downloads stream; uploads are buffered, so respect endpoint import/upload size limits.

Body modes (choose one):

- `--json-file FILE`: parse JSON and send application/json.
- `--body-file FILE --content-type MIME`: send exact CSV, JSONL, URL-encoded form, or binary bytes.
- `--multipart-file FILE`: read a JSON array of named parts and generate the multipart boundary.

Multipart manifest shape (field names depend on the operation's contract):

```json
[
  {"name":"file","file":"/absolute/path/data.bin","contentType":"application/octet-stream"},
  {"name":"name","value":"Example"},
  {"name":"settings","json":{"example":true},"contentType":"application/json"}
]
```

`json` serializes an object, `value` supplies a scalar, and `file` supplies bytes. Use the contract's field names and per-part MIME types.

`--headers-file FILE` reads an object of endpoint-specific headers without printing it. Never pass authorization strings as CLI arguments. Host, Content-Length and Transfer-Encoding cannot be overridden. Root-level endpoints such as OAuth use `--root --path /oauth2/token`. `--no-auth` omits default authentication so the endpoint's separately configured header file can be used. The CLI redacts token responses; use the imported client in process memory or the host's OAuth/secret manager for token handling.

## Pagination, jobs and downloads

```text
node scripts/qualtrics.mjs paginate --path /surveys --query pageSize=100
node scripts/qualtrics.mjs paginate --path /RESOURCE --items-path result.elements --max-pages 1000
node scripts/qualtrics.mjs poll --path /JOB_PATH --status-path result.status --success complete,success --failure failed,error --timeout-seconds 120
node scripts/qualtrics.mjs download --path /FILE_PATH --output result.zip
node scripts/qualtrics.mjs export --survey SV_ID --format csv --output responses.zip
node scripts/qualtrics.mjs export --survey SV_ID --json-file export-options.json --output responses.zip
```

Pagination follows returned `result.nextPage`, `nextPage`, or `links.next.href`; `--items-path` selects the returned array. Missing arrays, loops or reached limits raise an error. Use generic requests for other schemes. `poll` supports configurable status field and terminal states, increasing delays and a bounded timeout. Preserve the job ID when polling is interrupted.

`export` starts POST `/surveys/{id}/export-responses`, prints its progress ID/poll path to stderr for recovery, GETs progress, then GETs the file ID returned by completed progress. A JSON options file supplies the entire export body, including format. The helper does not unzip archives.

Read methods retry 429/502/503/504 at most three times. Retry-After is honored; a delay over 30 seconds returns control for a later retry. Writes are never automatically retried. Redirects and off-origin URLs are refused. Use a credential-free external client for an explicitly authorized signed external URL.

For custom flows import `QualtricsClient`, `multipart`, `getAt`, `run` from `scripts/qualtrics.mjs`. `request()` returns `{status,data}` in memory; redact before logging. `pages()` yields raw pages; `poll()` returns raw completed-job data. Inspect cached `servers` for API groups whose base path differs from `/API/v3/`.

"""Cross-check every cached operation against its official rendered endpoint page."""
import concurrent.futures
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(operation):
    url = operation['docs']
    if not url.startswith('https://developer-docs.qualtrics.com/docs/public-api/'):
        raise ValueError('Non-official source URL')
    with urllib.request.urlopen(url, timeout=45) as response:
        page = response.read().decode('utf-8')
    block = re.search(r'<pre class="openapi__method-endpoint">(.*?)</pre>', page, re.S)
    if not block:
        raise ValueError('Endpoint markup missing: ' + operation['key'])
    method = re.search(r'<span[^>]*>([A-Z]+)</span>', block[1])[1]
    raw_path = re.search(r'<h2[^>]*>(.*?)</h2>', block[1], re.S)[1]
    rendered_path = html.unescape(re.sub(r'<[^>]+>', '', raw_path)).strip()
    expected_path = re.sub(r'\{([^}]+)\}', r':\1', operation['path'])
    if method != operation['method'] or rendered_path != expected_path:
        raise ValueError('Rendered endpoint/contract mismatch: ' + operation['key'])
    return operation['key']


if __name__ == '__main__':
    catalog = json.loads((ROOT / 'references/api/catalog.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        checked = list(executor.map(verify, catalog['operations']))
    print(json.dumps({'officialRenderedPagesVerified': len(checked), 'allMethodsAndPathsMatch': True}))

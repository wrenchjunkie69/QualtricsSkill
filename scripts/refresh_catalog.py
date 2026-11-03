"""Rebuild the operation cache from Qualtrics' published documentation, without eval.

Python 3.10+, standard library only. No account credentials or API calls.
The site's generated operation metadata contains the dereferenced OpenAPI contract.
"""
import argparse
import ast
import base64
import concurrent.futures
import datetime
import hashlib
import functools
import json
import re
import urllib.request
import zlib
from pathlib import Path

ORIGIN = 'https://developer-docs.qualtrics.com'
ROOT = Path(__file__).resolve().parents[1]


@functools.lru_cache(maxsize=1000)
def fetch(path):
    url = path if path.startswith('https://') else ORIGIN + path
    request = urllib.request.Request(url, headers={'User-Agent': 'QualtricsSkillCatalog/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode('utf-8')
    except Exception as error:
        raise ValueError('Could not fetch official documentation asset ' + url + ': ' + str(error)) from error


def route_records(main):
    pattern = r'"?\w+"?:\[\(\)=>Promise\.all\(\[([^\]]+)\]\)\.then\(\w\.bind\(\w,(\d+)\)\),"(@site/docs/public-api/[^"]+\.api\.mdx)",\d+\]'
    records = []
    for match in re.finditer(pattern, main):
        chunks = [str(int(float(n))) for n in re.findall(r'\w\.e\((\d+(?:e[+-]?\d+)?)\)', match[1])]
        records.append({'chunks': chunks, 'module': match[2], 'source': match[3]})
    all_sources = set(re.findall(r'@site/docs/public-api/[^"\s]+\.api\.mdx', main))
    if set(r['source'] for r in records) != all_sources:
        raise ValueError('Documentation route format changed: operation route coverage incomplete')
    return records


def decode_metadata(chunk, source):
    # Parse quoted JSON literals as data. Never execute remote JavaScript.
    for match in re.finditer(r'JSON\.parse\((\x27(?:[^\x27\\]|\\.)*\x27)\)', chunk):
        value = json.loads(ast.literal_eval(match[1]))
        if isinstance(value, dict) and value.get('source') == source:
            encoded = value.get('frontMatter', {}).get('api')
            if not encoded:
                raise ValueError('Missing compressed operation contract: ' + source)
            return value, json.loads(zlib.decompress(base64.b64decode(encoded)))
    raise ValueError('Operation metadata not found: ' + source)


def rebuild(out, workers=5):
    home = fetch('/docs/public-api/home/')
    main_url = re.search(r'<script[^>]+src="([^\"]*/main\.[^\"]+\.js)"', home)[1]
    runtime_url = re.search(r'<script[^>]+src="([^\"]*/runtime~main\.[^\"]+\.js)"', home)[1]
    main, runtime = fetch(main_url), fetch(runtime_url)
    route_map = route_records(main)
    chunk_section = runtime.split('t.u=', 1)[1].split('t.miniCssF=', 1)[0]
    maps = [m for m in re.findall(r'\{([^{}]+)\}', chunk_section)
            if len(re.findall(r'(\d+):"([a-f0-9]+)"', m)) > 100]
    if len(maps) < 2:
        raise ValueError('Documentation chunk map changed')
    names, hashes = [{str(int(float(key))): value for key, value in
                      re.findall(r'(?:^|,)"?(\d+(?:e[+-]?\d+)?)"?:"([^\"]+)"', m)} for m in maps[:2]]
    out.mkdir(parents=True, exist_ok=True)
    cache = out / 'operations'
    cache.mkdir(exist_ok=True)

    def read_route(route):
        found = False
        for chunk_id in reversed(route['chunks']):
            if chunk_id not in hashes:
                continue
            chunk_url = '/assets/js/' + names.get(chunk_id, chunk_id) + '.' + hashes[chunk_id] + '.js'
            chunk = fetch(chunk_url)
            if route['source'] not in chunk:
                continue
            metadata, api = decode_metadata(chunk, route['source'])
            found = True
            break
        if not found:
            metadata, api = decode_metadata(main, route['source'])
        if not api.get('method') or not api.get('path'):
            raise ValueError('Invalid operation contract: ' + route['source'])
        doc_url = ORIGIN + metadata['permalink'].rstrip('/') + '/'
        key = metadata['id'].removeprefix('public-api/').replace('/', '--')
        packed = zlib.compress(json.dumps(api, ensure_ascii=False, separators=(',', ':')).encode(), 9)
        digest = hashlib.sha256(packed).hexdigest()
        (cache / (digest + '.json.zlib')).write_bytes(packed)
        return {
            'key': key, 'domain': metadata['sourceDirName'].split('/')[-1],
            'title': metadata['title'], 'operationId': api.get('operationId'),
            'method': api['method'].upper(), 'path': api['path'],
            'deprecated': bool(api.get('deprecated', False)),
            'docs': doc_url, 'cache': 'operations/' + digest + '.json.zlib',
            'sha256': digest,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        operations = []
        for index, operation in enumerate(executor.map(read_route, route_map), 1):
            operations.append(operation)
            if index % 50 == 0:
                print('Downloaded ' + str(index) + ' operation contracts', flush=True)
    operations.sort(key=lambda o: (o['domain'], o['path'], o['method']))
    if len(set(o['key'] for o in operations)) != len(operations):
        raise ValueError('Duplicate operation keys')
    catalog = {'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'source': ORIGIN + '/docs/public-api/home/',
               'mainAsset': ORIGIN + main_url, 'runtimeAsset': ORIGIN + runtime_url,
               'operationCount': len(operations), 'operations': operations}
    staged = out / 'catalog.json.tmp'
    staged.write_text(json.dumps(catalog, indent=2) + '\n', encoding='utf-8')
    staged.replace(out / 'catalog.json')
    return {'operations': len(operations), 'domains': len(set(o['domain'] for o in operations)),
            'compressedBytes': sum((out / o['cache']).stat().st_size for o in operations)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'references' / 'api')
    parser.add_argument('--workers', type=int, default=5)
    args = parser.parse_args()
    try:
        print(json.dumps(rebuild(args.out, args.workers)))
    except Exception as error:
        raise SystemExit('Catalog refresh failed; do not claim a complete refresh: ' + str(error))

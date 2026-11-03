"""Check publication candidates: blank .env template, no private artifacts, valid links.

Focused packaging checks, not a general-purpose secret scanner or a history audit.
"""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENIED_DIRS = {'.venv', 'venv', 'analytics-venv', '__pycache__', 'node_modules', 'credentials', 'secrets', '.secrets', 'data', 'results', 'outputs', 'exports'}


def candidates(root=ROOT):
    root = Path(root).resolve()
    try:
        result = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], capture_output=True, check=True)
        values = sorted(set(value.decode('utf-8') for value in result.stdout.split(b'\0') if value))
        return [root / value for value in values]
    except (OSError, subprocess.CalledProcessError):
        return [file for file in root.rglob('*') if file.is_file() and '.git' not in file.parts and '__pycache__' not in file.parts
                and not file.is_relative_to(root / 'references/api')]


def check(root=ROOT):
    root = Path(root).resolve()
    template = root / '.env'
    if not template.is_file() or template.read_bytes() != b'APIKEY=\n':
        raise ValueError('The public root .env must contain exactly APIKEY= and a newline, with no value')
    try:
        staged = subprocess.run(['git', '-C', str(root), 'show', ':.env'], capture_output=True)
        if staged.returncode == 0 and staged.stdout != b'APIKEY=\n':
            raise ValueError('The staged/index .env is not empty even if the working copy is; remove its value from the index before publishing')
    except OSError:
        pass
    files = candidates(root)
    links = 0
    for file in files:
        relative = file.relative_to(root)
        if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError('Unexpected publication file/link: ' + relative.as_posix())
        if file == template:
            continue
        lower = file.name.lower()
        if any(part in DENIED_DIRS for part in relative.parts) or relative.parts[:2] == ('references', 'api'):
            raise ValueError('Private/generated artifact is included in publication candidates: ' + relative.as_posix())
        if lower.startswith('.env') or lower.endswith('.env') or lower in {'profile.json', 'runtime.json', 'api-key.txt', 'api_key.txt'} or 'api key' in lower:
            raise ValueError('Private credential/config file is included in publication candidates: ' + relative.as_posix())
        if file.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.csv', '.xlsx', '.sav', '.zip', '.pyc'}:
            raise ValueError('Unexpected credential/data/binary publication candidate: ' + relative.as_posix())
        raw = file.read_bytes()
        if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', raw):
            raise ValueError('Private-key material detected in a publication candidate')
        if file.suffix == '.md':
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', raw.decode('utf-8-sig')):
                if '://' in target or target.startswith('#'):
                    continue
                destination = (file.parent / target.split('#')[0].strip('<>')).resolve()
                if not destination.exists() or not destination.is_relative_to(root):
                    raise ValueError('Broken/nonportable local reference in ' + relative.as_posix())
                links += 1
    return {'ok': True, 'publicationFiles': len(files), 'localLinksChecked': links, 'publicEnvTemplateEmpty': True,
            'note': 'Review the diff and secret scanning separately; this check is not an exhaustive secret/history audit'}


if __name__ == '__main__':
    try:
        print(json.dumps(check(), indent=2))
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None

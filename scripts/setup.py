"""Install the portable skill and its optional local analytics runtime. Python 3.10+."""
import argparse
import csv
import getpass
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import venv
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = Path.home() / '.config' / 'qualtrics'
TEMPLATE = 'APIKEY=\n'
ROOT_FILES = {'SKILL.md', 'README.md', 'LICENSE', 'NOTICE.md'}


def execute(args, **kwargs):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding='utf-8', **kwargs)
    if result.returncode:
        # Never include child stdout/stderr: credential-handling commands must not echo input.
        raise RuntimeError(Path(str(args[0])).name + ' failed; inspect dependency/connectivity configuration and rerun')
    return result.stdout


def private_directory(folder):
    folder = Path(folder).expanduser().resolve()
    if folder.is_relative_to(ROOT):
        raise ValueError('Private configuration must be outside the repository/skill directory')
    folder.mkdir(parents=True, exist_ok=True)
    restrict_permissions(folder, directory=True)
    return folder


def restrict_permissions(file, directory=False):
    if Path(file).is_symlink():
        raise ValueError('Private credential/config paths must not be symlinks')
    if os.name != 'nt':
        Path(file).chmod(0o700 if directory else 0o600)
        return
    import ctypes
    from ctypes import wintypes as w
    sid = next(csv.reader(io.StringIO(execute(['whoami', '/user', '/fo', 'csv', '/nh']).strip())))[-1]
    if not re.fullmatch(r'S-1-[\d-]+', sid):
        raise ValueError('Could not resolve current Windows user SID')
    inheritance = 'OICI' if directory else ''
    sddl = f'D:P(A;{inheritance};FA;;;{sid})(A;{inheritance};FA;;;SY)'
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    api.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [w.LPCWSTR, w.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(w.DWORD)]
    api.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = w.BOOL
    api.GetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(w.BOOL), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(w.BOOL)]
    api.GetSecurityDescriptorDacl.restype = w.BOOL
    api.SetNamedSecurityInfoW.argtypes = [w.LPWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    api.SetNamedSecurityInfoW.restype = w.DWORD
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    descriptor = ctypes.c_void_p()
    if not api.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, ctypes.byref(descriptor), None):
        raise OSError(ctypes.get_last_error(), 'Could not construct private Windows DACL')
    try:
        present, defaulted, dacl = w.BOOL(), w.BOOL(), ctypes.c_void_p()
        if not api.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)) or not present:
            raise OSError(ctypes.get_last_error(), 'Could not resolve private Windows DACL')
        # Change only the protected DACL, not owner/SACL (which would require SeSecurityPrivilege).
        error = api.SetNamedSecurityInfoW(str(Path(file).resolve()), 1, 0x80000004, None, None, dacl, None)
        if error:
            raise OSError(error, 'Could not apply private Windows DACL')
    finally:
        kernel.LocalFree(descriptor)


def atomic_write(file, value, private=False):
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_name(file.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600 if private else 0o644)
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(value)
        temporary.replace(file)
        if private and os.name != 'nt':
            file.chmod(0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def initialize_private(folder):
    folder = private_directory(folder)
    env = folder / '.env'
    if not env.exists():
        atomic_write(env, TEMPLATE, private=True)
    restrict_permissions(env)
    return folder


def runtime_files(source=ROOT):
    source = Path(source).resolve()
    files = []
    for name in ROOT_FILES:
        if (source / name).is_file():
            files.append(source / name)
    for directory in ['agents', 'references', 'scripts', 'assets']:
        for file in (source / directory).rglob('*'):
            relative = file.relative_to(source)
            if file.is_file() and '__pycache__' not in relative.parts and file.suffix in {'.md', '.yaml', '.mjs', '.py', '.txt', '.json'}:
                if relative.parts[:2] == ('references', 'api'):
                    continue
                if file.is_symlink() or not file.resolve().is_relative_to(source):
                    raise ValueError('Portable source contains an unexpected symlink')
                files.append(file)
    return sorted(files)


def same_files(source, destination):
    return all((destination / f.relative_to(source)).is_file() and
               hashlib.sha256(f.read_bytes()).digest() == hashlib.sha256((destination / f.relative_to(source)).read_bytes()).digest()
               for f in runtime_files(source))


def install_files(destination, config_dir, update=False, source=ROOT):
    source, destination = Path(source).resolve(), Path(destination).expanduser().absolute()
    if destination.exists() and same_files(source, destination):
        return {'destination': str(destination), 'status': 'current'}
    # Never write through an unreviewed symlink/junction. Existing identical shared installs are fine above.
    if destination.exists() and (destination.is_symlink() or destination.resolve() != destination.parent.resolve() / destination.name):
        raise ValueError('An existing installation is linked elsewhere; update its real target first')
    # Canonicalize ordinary ancestor links (e.g. macOS /var -> /private/var), not just the leaf.
    destination = destination.parent.resolve() / destination.name
    if destination == source or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError('Installation source and destination must be separate directories')
    existing = destination.exists() and any(destination.iterdir())
    if existing and not update:
        raise ValueError('Installation already exists; use --update for this requested update (changed files are backed up privately)')
    backup = Path(config_dir) / 'backups' / uuid.uuid4().hex / destination.parent.name
    copied = 0
    for file in runtime_files(source):
        relative = file.relative_to(source)
        target = destination / relative
        if target.is_symlink() or (target.exists() and target.resolve() != target.absolute()):
            raise ValueError('An installed file resolves through an unexpected link')
        if target.is_file() and target.read_bytes() == file.read_bytes():
            continue
        if target.exists():
            archived = backup / relative
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, archived)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
        shutil.copy2(file, temporary)
        temporary.replace(target)
        copied += 1
    return {'destination': str(destination), 'status': 'updated' if existing else 'installed', 'filesCopied': copied,
            'backup': str(backup) if backup.exists() else None}


def ensure_catalog(root, refresh=False):
    catalog = Path(root) / 'references' / 'api' / 'catalog.json'
    if refresh or not catalog.exists():
        print('Fetching current public API contracts from official Qualtrics documentation (no account credentials).', flush=True)
        execute([sys.executable, Path(root) / 'scripts' / 'refresh_catalog.py'], timeout=180)
    execute(['node', Path(root) / 'scripts' / 'catalog.mjs', 'verify'], timeout=30)


def copy_catalog(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    source_cache = source / 'references/api'
    target_cache = destination / 'references/api'
    catalog = json.loads((source_cache / 'catalog.json').read_text(encoding='utf-8'))
    for operation in catalog['operations']:
        file = (source_cache / operation['cache']).resolve()
        target = (target_cache / operation['cache']).resolve()
        if not file.is_relative_to(source_cache) or not target.is_relative_to(target_cache):
            raise ValueError('Unexpected documentation-cache path')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    target_cache.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_cache / 'catalog.json', target_cache / 'catalog.json')


def check_node():
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js 20+ is required. Install an official current Node LTS, then rerun setup')
    version = execute([node, '--version']).strip()
    if int(version.lstrip('v').split('.')[0]) < 20:
        raise RuntimeError('Node.js 20+ is required; current Node is older')
    return node, version


def environment_python(folder):
    return Path(folder) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def setup_analytics(config_dir, python=None, env_dir=None):
    folder = Path(env_dir).expanduser().resolve() if env_dir else Path(config_dir) / 'analytics-venv'
    if folder.is_relative_to(ROOT):
        raise ValueError('Keep the analytics environment outside the repository')
    interpreter = environment_python(folder)
    uv = shutil.which('uv')
    if not interpreter.exists():
        if folder.exists() and any(folder.iterdir()):
            raise ValueError('Analytics environment path is occupied by something else')
        if uv:
            execute([uv, 'venv', '--python', python or '3.12', folder], timeout=180)
        else:
            if python:
                base = str(python)
            elif sys.version_info[:2] == (3, 12):
                base = sys.executable
            else:
                base = shutil.which('python3.12')
                if not base and os.name == 'nt' and shutil.which('py'):
                    try:
                        base = execute(['py', '-3.12', '-c', 'import sys; print(sys.executable)']).strip()
                    except RuntimeError:
                        pass
            if not base:
                raise RuntimeError('Install Python 3.12 or uv, or pass --python /path/to/python3.12; see README')
            execute([base, '-m', 'venv', folder], timeout=180)
    version = json.loads(execute([interpreter, '-c', 'import sys,json; print(json.dumps(list(sys.version_info[:2])))']))
    if version != [3, 12]:
        raise ValueError('Use Python 3.12 for the pinned tested analytics environment')
    requirements = ROOT / 'scripts' / 'requirements-analysis.txt'
    if uv:
        execute([uv, 'pip', 'install', '--link-mode', 'copy', '--python', interpreter, '-r', requirements], timeout=240)
        execute([uv, 'pip', 'check', '--python', interpreter], timeout=30)
    else:
        execute([interpreter, '-m', 'pip', 'install', '-r', requirements], timeout=240)
        execute([interpreter, '-m', 'pip', 'check'], timeout=30)
    return str(interpreter)


def configure(args):
    folder = initialize_private(args.config_dir)
    profile_path = folder / 'profile.json'
    profile = json.loads(profile_path.read_text(encoding='utf-8-sig')) if profile_path.exists() else {}
    if args.base_url:
        url = urlsplit(args.base_url)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('API base must be HTTPS, without URL credentials, query or fragment')
        profile['baseURL'] = args.base_url.rstrip('/') + '/'
        profile.pop('datacenter', None)
    elif args.datacenter:
        if not re.fullmatch(r'[A-Za-z0-9-]+', args.datacenter):
            raise ValueError('Use only the datacenter code from Qualtrics Account Settings')
        profile['baseURL'] = f'https://{args.datacenter}.qualtrics.com/API/v3/'
        profile.pop('datacenter', None)
    if not profile.get('baseURL') and not profile.get('datacenter'):
        raise ValueError('Provide --datacenter CODE or --base-url https://... from the account settings')
    env = folder / '.env'
    key = None
    if args.import_key_file:
        file = Path(args.import_key_file).expanduser().resolve()
        if file.is_relative_to(ROOT):
            raise ValueError('Import from a private file outside the public repository')
        key = file.read_text(encoding='utf-8-sig').strip()
    elif args.prompt_key:
        if not sys.stdin.isatty():
            raise ValueError('Masked key entry requires an interactive terminal; alternatively fill the private .env locally or import a private token-only file')
        key = getpass.getpass('Qualtrics API key (hidden): ').strip()
    if key is not None:
        if not key or re.search(r'\s|[\x00-\x1f]', key) or key.startswith(('"', "'")):
            raise ValueError('Expected a nonempty single API token without whitespace/control characters or leading quotes')
        previous = env.read_text(encoding='utf-8-sig').strip()
        replacement = 'APIKEY=' + key
        if previous not in {'APIKEY=', replacement} and not args.replace_key:
            raise ValueError('A private credential already exists; use --replace-key for the requested key change')
        atomic_write(env, replacement + '\n', private=True)
    if key is not None:
        profile['envFile'] = str(env)
        profile.pop('keyFile', None)
        profile.pop('bearerTokenFile', None)
    elif not any(profile.get(name) for name in ['envFile', 'keyFile', 'bearerTokenFile']):
        profile['envFile'] = str(env)
    atomic_write(profile_path, json.dumps(profile, indent=2) + '\n', private=True)
    actual_env = Path(profile['envFile']) if profile.get('envFile') else None
    present = bool(actual_env and actual_env.is_file() and re.search(r'^(?:APIKEY|QUALTRICS_API_TOKEN|QUALTRICS_ACCESS_TOKEN)=\s*\S+', actual_env.read_text(encoding='utf-8-sig'), re.M))
    if not present:
        present = any(Path(profile[name]).is_file() and Path(profile[name]).stat().st_size > 0 for name in ['keyFile', 'bearerTokenFile'] if profile.get(name))
    return {'profile': str(profile_path), 'privateEnv': str(actual_env or env), 'keyPresent': present,
            'note': 'Credential value is never printed; repository template was not modified'}


def install(args):
    config_dir = initialize_private(args.config_dir)
    node, version = check_node()
    print('Checking/installing the isolated analytics dependencies.' if not args.api_only else 'Installing API-only mode.', flush=True)
    analytics = None if args.api_only else setup_analytics(config_dir, args.python, args.analytics_env)
    ensure_catalog(ROOT, args.refresh_catalog)
    hosts = args.host or ['codex', 'claude']
    installed = {}
    for host in dict.fromkeys(hosts):
        destination = (Path(args.install_root) / host / 'qualtrics') if args.install_root else Path.home() / ('.codex' if host == 'codex' else '.claude') / 'skills' / 'qualtrics'
        result = install_files(destination, config_dir, args.update)
        if Path(destination).resolve() != ROOT:
            copy_catalog(ROOT, destination)
        ensure_catalog(destination)
        installed[host] = result
    runtime = {'schemaVersion': 1, 'source': str(ROOT), 'analyticsPython': analytics,
               'installed': {host: result['destination'] for host, result in installed.items()}}
    atomic_write(config_dir / 'runtime.json', json.dumps(runtime, indent=2) + '\n', private=True)
    if not args.skip_tests:
        print('Running local validation; no account credentials or API requests are used.', flush=True)
        execute([node, '--test', ROOT / 'scripts' / 'qualtrics.test.mjs'], timeout=60)
        if analytics:
            execute([analytics, '-m', 'unittest', 'discover', '-s', ROOT / 'scripts', '-p', 'test_*.py'], timeout=90)
        else:
            for suite in ['test_setup.py', 'test_results.py']:
                execute([sys.executable, '-m', 'unittest', 'discover', '-s', ROOT / 'scripts', '-p', suite], timeout=45)
    return {'node': version, 'analyticsPython': analytics, 'installed': installed, 'privateEnv': str(config_dir / '.env'),
            'localTestsRun': not args.skip_tests, 'accountConfiguration': 'Use configure and then doctor --check-api when a key/base URL are available'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--config-dir', type=Path, default=DEFAULT_CONFIG)
    installer = sub.add_parser('install', parents=[common])
    installer.add_argument('--host', action='append', choices=['codex', 'claude'])
    installer.add_argument('--install-root', type=Path, help='Optional isolated host container for tests/custom installations')
    installer.add_argument('--update', action='store_true')
    installer.add_argument('--python', help='Python 3.12 executable, or uv Python selector')
    installer.add_argument('--analytics-env', type=Path)
    installer.add_argument('--api-only', action='store_true')
    installer.add_argument('--refresh-catalog', action='store_true')
    installer.add_argument('--skip-tests', action='store_true')
    account = sub.add_parser('configure', parents=[common])
    location = account.add_mutually_exclusive_group()
    location.add_argument('--datacenter')
    location.add_argument('--base-url')
    entry = account.add_mutually_exclusive_group()
    entry.add_argument('--prompt-key', action='store_true')
    entry.add_argument('--import-key-file', type=Path)
    account.add_argument('--replace-key', action='store_true')
    args = parser.parse_args()
    if (ROOT / '.env').exists() and (ROOT / '.env').read_text(encoding='utf-8-sig') != TEMPLATE:
        raise ValueError('The public .env must contain only APIKEY= and a newline. Keep real credentials in the private configuration directory')
    result = install(args) if args.command == 'install' else configure(args)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None

"""Check local installation/dependencies; authenticated GET only with --check-api."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, timeout=45):
    result = subprocess.run([str(a) for a in args], capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError('Check failed: ' + Path(str(args[0])).name + '; rerun setup or inspect the relevant configuration')
    return result.stdout


def check(config_dir, check_api=False):
    config_dir = Path(config_dir).expanduser().resolve()
    report = {'checks': [], 'apiChecked': False}
    errors = []
    try:
        version = run(['node', '--version']).strip()
        if int(version.lstrip('v').split('.')[0]) < 20:
            raise ValueError('Node 20+ required')
        report['checks'].append({'name': 'node', 'ok': True, 'version': version})
        catalog = json.loads(run(['node', ROOT / 'scripts/catalog.mjs', 'verify']))
        report['checks'].append({'name': 'catalog', 'ok': True, 'operations': catalog['verified']})
    except Exception:
        errors.append('Node/catalog check failed; install Node 20+ and run setup install to fetch contracts')
    runtime_file = config_dir / 'runtime.json'
    runtime = json.loads(runtime_file.read_text(encoding='utf-8-sig')) if runtime_file.exists() else {}
    interpreter = runtime.get('analyticsPython')
    if interpreter:
        try:
            code = ('import json,importlib.metadata as m,sys; import numpy,pandas,scipy,statsmodels,sklearn,matplotlib; '
                    'print(json.dumps({"python":list(sys.version_info[:2]),"versions":{n:m.version(n) for n in '
                    '["numpy","pandas","scipy","statsmodels","scikit-learn","matplotlib"]}}))')
            libraries = json.loads(run([interpreter, '-c', code]))
            if libraries['python'] != [3, 12]:
                raise ValueError('Tested runtime is Python 3.12')
            expected = {}
            for line in (ROOT / 'scripts/requirements-analysis.txt').read_text(encoding='utf-8-sig').splitlines():
                if '==' in line and not line.lstrip().startswith('#'):
                    name, value = line.split('==', 1)
                    expected[name] = value
            installed = json.loads(run([interpreter, '-c', 'import json,importlib.metadata as m; print(json.dumps({d.metadata["Name"].lower():d.version for d in m.distributions()}))']))
            canonical = lambda name: re.sub(r'[-_.]+', '-', name).lower()
            installed = {canonical(name): version for name, version in installed.items()}
            if any(installed.get(canonical(name)) != version for name, version in expected.items()):
                raise ValueError('Pinned dependency versions differ')
            if shutil.which('uv'):
                run(['uv', 'pip', 'check', '--python', interpreter])
            else:
                run([interpreter, '-m', 'pip', 'check'])
            report['checks'].append({'name': 'analytics', 'ok': True, 'python': interpreter, 'versions': libraries['versions']})
        except Exception:
            errors.append('Analytics runtime/dependency check failed; rerun setup install for an isolated Python 3.12 environment')
    else:
        report['checks'].append({'name': 'analytics', 'ok': False, 'optional': True, 'note': 'Run default setup install for data science, not API-only mode'})
    profile_file = config_dir / 'profile.json'
    report['checks'].append({'name': 'account-profile', 'ok': profile_file.exists(), 'optionalForOfflineAnalysis': True})
    if check_api:
        if not profile_file.exists():
            errors.append('Configure the datacenter/base URL and private key before --check-api')
        else:
            try:
                data = json.loads(run(['node', ROOT / 'scripts/qualtrics.mjs', 'whoami', '--profile', profile_file]))
                authenticated = data.get('status') == 200 and bool(data.get('data', {}).get('result', {}).get('userId'))
                if not authenticated:
                    raise ValueError('Authentication did not return an account')
                report['checks'].append({'name': 'authenticated-whoami', 'ok': True, 'httpStatus': 200})
                report['apiChecked'] = True
            except Exception:
                errors.append('Read-only Qualtrics authentication failed; check the private key and correct account datacenter/base URL')
    report.update(ok=not errors, errors=errors)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config-dir', type=Path, default=Path.home() / '.config/qualtrics')
    parser.add_argument('--check-api', action='store_true')
    args = parser.parse_args()
    try:
        result = check(args.config_dir, args.check_api)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['ok'] else 1)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        raise SystemExit('Doctor could not read/run local configuration; rerun setup and do not display credential files') from None

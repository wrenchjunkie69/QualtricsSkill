"""Run one deliberately selected data-science configuration using the installed skill."""
import argparse
import subprocess
import sys
from pathlib import Path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir', type=Path)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--header-records', choices=[1, 3], type=int, default=1)
    args = parser.parse_args()
    candidates = [args.skill_dir] if args.skill_dir else [Path(__file__).resolve().parents[2],
        Path.home()/'.codex/skills/qualtrics', Path.home()/'.claude/skills/qualtrics']
    skill = next((p.resolve() for p in candidates if (p/'SKILL.md').is_file() and (p/'scripts/mining.py').is_file()), None)
    if skill is None:
        raise SystemExit('Use --skill-dir to identify the installed skill or source checkout')
    command = [sys.executable, str(skill/'scripts/mining.py'), '--config', str(args.config),
               '--out', str(args.out), '--header-records', str(args.header_records)]
    if args.data: command += ['--data', str(args.data)]
    raise SystemExit(subprocess.run(command).returncode)

"""Selected-model starter; never retrieves data or automatically selects/fits other models."""
import argparse
import subprocess
import sys
from pathlib import Path


def locate(explicit=None):
    candidates = [Path(explicit)] if explicit else [Path(__file__).resolve().parents[2],
        Path.home() / '.codex/skills/qualtrics', Path.home() / '.claude/skills/qualtrics']
    for candidate in candidates:
        if (candidate / 'SKILL.md').is_file() and (candidate / 'scripts/analyze.py').is_file():
            return candidate.resolve()
    raise ValueError('Use --skill-dir with the installed skill/repository directory')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir', type=Path)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--header-records', choices=[1, 3], type=int, default=1)
    args = parser.parse_args()
    skill = locate(args.skill_dir)
    # Extend the chosen configuration/method deliberately; do not add a battery of unrelated fits.
    result = subprocess.run([sys.executable, str(skill / 'scripts/analyze.py'), 'fit', '--data', str(args.data),
                             '--config', str(args.config), '--out', str(args.out), '--header-records', str(args.header_records)])
    raise SystemExit(result.returncode)

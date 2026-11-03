"""Starter for a requested independent-group Welch mean comparison; no API calls."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import scipy.stats as stats

from run_model import locate


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-dir', type=Path)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--value', required=True)
    parser.add_argument('--group', required=True)
    parser.add_argument('--group-a', required=True)
    parser.add_argument('--group-b', required=True)
    parser.add_argument('--respondent', help='ID column; repeated IDs are incompatible with this independent-group starter')
    parser.add_argument('--header-records', choices=[1, 3], type=int, default=1)
    parser.add_argument('--drop-missing', action='store_true', help='Explicitly chosen complete-case policy for the selected variables')
    parser.add_argument('--out', type=Path, required=True, help='New JSON output file')
    args = parser.parse_args()
    try:
        if args.group_a == args.group_b or args.out.exists():
            raise ValueError('Use distinct group labels and a new output file')
        skill = locate(args.skill_dir)
        spec = importlib.util.spec_from_file_location('survey_analysis', skill / 'scripts/analyze.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        data = module.read_csv(args.data, args.header_records)
        required = [args.value, args.group] + ([args.respondent] if args.respondent else [])
        if any(name not in data for name in required):
            raise ValueError('Required columns are missing; use the actual export/codebook')
        selected = data.loc[data[args.group].isin([args.group_a, args.group_b]), required].copy()
        invalid = selected.isna().any(axis=1) | (selected == '').any(axis=1)
        if invalid.any() and not args.drop_missing:
            raise ValueError('Resolve missing values or explicitly choose --drop-missing')
        selected = selected.loc[~invalid]
        if args.respondent and selected[args.respondent].duplicated().any():
            raise ValueError('Repeated people need a paired/repeated model, not this independent-group comparison')
        a = selected.loc[selected[args.group] == args.group_a, args.value].astype(float).to_numpy()
        b = selected.loc[selected[args.group] == args.group_b, args.value].astype(float).to_numpy()
        if min(len(a), len(b)) < 2 or not np.isfinite(np.r_[a, b]).all() or (np.var(a, ddof=1) == 0 and np.var(b, ddof=1) == 0):
            raise ValueError('Need finite observations and nondegenerate variance in sufficiently populated groups')
        fitted = stats.ttest_ind(a, b, equal_var=False)
        interval = fitted.confidence_interval(confidence_level=0.95)
        report = {'method': 'Independent two-group Welch t-test', 'groupA': args.group_a, 'groupB': args.group_b,
                  'nA': len(a), 'nB': len(b), 'meanDifference_A_minus_B': float(a.mean() - b.mean()),
                  'ci95': [float(interval.low), float(interval.high)], 't': float(fitted.statistic), 'df': float(fitted.df),
                  'pValue': float(fitted.pvalue), 'excludedMissingRows': int(invalid.sum()),
                  'inputSHA256': hashlib.sha256(args.data.read_bytes()).hexdigest(),
                  'limits': 'Requires an appropriate numeric outcome and independent groups; not automatic evidence of causation or external validity.'}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x', encoding='utf-8') as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write('\n')
        print(json.dumps({'output': str(args.out.resolve()), 'method': report['method']}))
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None

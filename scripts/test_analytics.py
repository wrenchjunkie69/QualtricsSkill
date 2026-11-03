"""Synthetic, deterministic tests; never read an account key or real survey data."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from analyze import analyze, design_matrix, inspect_csv, read_csv, save_analysis, utilities


def linear_fixture():
    rng = np.random.default_rng(502)
    x = rng.normal(size=400)
    group = np.where(rng.random(400) > 0.5, 'B', 'A')
    y = 2 + 3 * x + 1.5 * (group == 'B') + rng.normal(scale=0.2, size=400)
    return pd.DataFrame({'x': x, 'group': group, 'y': y})


def conjoint_fixture(choice=False):
    rng = np.random.default_rng(803)
    rows = []
    profiles = [('p0', 'low', 'low'), ('p1', 'high', 'low'), ('p2', 'low', 'high'), ('p3', 'high', 'high')]
    for respondent in range(45):
        if choice:
            for task in range(3):
                selected = rng.choice(4, size=3, replace=False)
                u = np.array([1.1 * (profiles[i][1] == 'high') - 0.6 * (profiles[i][2] == 'high') for i in selected])
                probs = np.exp(u - u.max()); probs /= probs.sum()
                chosen = rng.choice(3, p=probs)
                for alternative, i in enumerate(selected):
                    profile, a, b = profiles[i]
                    rows.append({'respondent': str(respondent), 'task': str(task), 'profile': profile, 'a': a, 'b': b, 'chosen': int(alternative == chosen)})
        else:
            person_effect = rng.normal(scale=0.5)
            scores = np.array([2 * (a == 'high') + (b == 'high') for _, a, b in profiles]) + rng.normal(scale=0.6, size=4)
            ranks = np.argsort(np.argsort(-scores)) + 1
            for i, (profile, a, b) in enumerate(profiles):
                rows.append({'respondent': str(respondent), 'task': '0', 'profile': profile, 'a': a, 'b': b,
                             'rating': 4 + 2 * (a == 'high') + (b == 'high') + person_effect + rng.normal(scale=0.15), 'rank': int(ranks[i])})
    return pd.DataFrame(rows)


def conjoint_config(kind):
    target = {'conjoint-rating': 'rating', 'conjoint-rank': 'rank', 'conjoint-choice': 'chosen'}[kind]
    cfg = {'model': kind, 'outcome': {'column': target}, 'respondent': 'respondent', 'task': 'task', 'profile': 'profile',
           'numeric': [], 'categorical': {name: {'levels': ['low', 'high'], 'reference': 'low'} for name in ['a', 'b']}, 'seed': 500}
    if kind == 'conjoint-choice':
        cfg['outcome'].update(event='1', non_event='0')
        cfg['bootstrap_reps'] = 20
    if kind == 'conjoint-rank':
        cfg.update(rank_direction='1-is-best', acknowledge_rank_approximation=True)
    return cfg


class AnalyticsTests(unittest.TestCase):
    def test_ols_recovers_coefficients_and_reports_reference_covariance(self):
        cfg = {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x'], 'categorical': {'group': {'levels': ['A', 'B'], 'reference': 'A'}}}
        report, predictions = analyze(linear_fixture(), cfg)
        estimates = {r['term']: r['estimate'] for r in report['coefficients']}
        self.assertAlmostEqual(estimates['Intercept'], 2, delta=0.06)
        self.assertAlmostEqual(estimates['x'], 3, delta=0.04)
        self.assertAlmostEqual(estimates['group[B]'], 1.5, delta=0.06)
        self.assertEqual(report['covariance'], 'HC3')
        self.assertEqual(len(predictions), 400)

    def test_logistic_event_and_odds_ratio_direction(self):
        rng = np.random.default_rng(130)
        x = rng.normal(size=1800)
        p = 1 / (1 + np.exp(-(-0.3 + 1.2 * x)))
        y = np.where(rng.random(len(x)) < p, 'yes', 'no')
        cfg = {'model': 'logistic', 'outcome': {'column': 'y', 'event': 'yes', 'non_event': 'no'}, 'numeric': ['x']}
        report, _ = analyze(pd.DataFrame({'x': x, 'y': y}), cfg)
        coefficient = next(r for r in report['coefficients'] if r['term'] == 'x')
        self.assertAlmostEqual(coefficient['estimate'], 1.2, delta=0.18)
        self.assertAlmostEqual(coefficient['odds_ratio'], np.exp(coefficient['estimate']))
        self.assertEqual(report['diagnostics']['events'], int((y == 'yes').sum()))
        self.assertIn('in-sample', report['evaluation'])

    def test_logistic_requires_explicit_event_and_rejects_separation(self):
        data = pd.DataFrame({'x': np.arange(30), 'y': [0] * 15 + [1] * 15})
        cfg = {'model': 'logistic', 'outcome': {'column': 'y'}, 'numeric': ['x']}
        with self.assertRaisesRegex(ValueError, 'event'):
            analyze(data, cfg)
        cfg['outcome'].update(event='1', non_event='0')
        with self.assertRaisesRegex(ValueError, 'quasi separation'):
            analyze(data, cfg)

    def test_quasi_separated_binary_model_is_rejected_before_false_convergence(self):
        data = pd.DataFrame({'x': [-1, 0, 0, 1] * 20, 'y': [0, 0, 1, 1] * 20})
        cfg = {'model': 'logistic', 'outcome': {'column': 'y', 'event': '1', 'non_event': '0'}, 'numeric': ['x']}
        with self.assertRaisesRegex(ValueError, 'quasi separation'):
            analyze(data, cfg)

    def test_explicit_complete_case_audit_and_no_raw_mutation(self):
        data = linear_fixture()
        data.loc[3, 'x'] = np.nan
        baseline = data.copy(deep=True)
        cfg = {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x']}
        with self.assertRaisesRegex(ValueError, 'Missing'):
            analyze(data, cfg)
        cfg['missing'] = 'complete-case'
        report, predictions = analyze(data, cfg)
        self.assertEqual(report['audit']['excluded_missing_rows'], 1)
        self.assertNotIn(4, predictions['data_row_number'].tolist())
        pd.testing.assert_frame_equal(data, baseline)

    def test_identifiers_leakage_unknown_levels_and_aliases_fail(self):
        data = linear_fixture()
        with self.assertRaisesRegex(ValueError, 'not also a predictor'):
            analyze(data, {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['y']})
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            design_matrix(data, {'categorical': {'group': {'levels': ['A', 'C'], 'reference': 'A'}}})
        data['twice_x'] = data['x'] * 2
        with self.assertRaisesRegex(ValueError, 'Rank-deficient'):
            analyze(data, {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x', 'twice_x']})

    def test_repeated_respondent_requires_group_aware_analysis(self):
        data = linear_fixture()
        data['person'] = np.arange(len(data)) // 4
        cfg = {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x'], 'respondent': 'person'}
        with self.assertRaisesRegex(ValueError, 'Repeated respondents'):
            analyze(data, cfg)
        report, _ = analyze(data, {**cfg, 'cluster': 'person'})
        self.assertEqual(report['audit']['clusters'], 100)
        self.assertEqual(report['covariance'], 'cluster: person')

    def test_response_level_clusters_do_not_address_repeated_people(self):
        data = linear_fixture()
        data['person'] = np.arange(len(data)) // 4
        data['response_id'] = np.arange(len(data))
        cfg = {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x'], 'respondent': 'person', 'cluster': 'response_id'}
        with self.assertRaisesRegex(ValueError, 'crosses declared clusters'):
            analyze(data, cfg)
        data['school'] = data['person'] // 10
        report, _ = analyze(data, {**cfg, 'cluster': 'school'})
        self.assertEqual(report['audit']['clusters'], 10)

    def test_custom_missing_codes_extend_blank_and_preserve_row_positions(self):
        data = linear_fixture().astype({'x': object})
        data.loc[2, 'x'] = ''
        data.loc[5, 'x'] = '-99'
        data.index = [f'label_{i}' for i in range(len(data))]
        cfg = {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x'], 'missing': 'complete-case', 'missing_values': ['-99']}
        report, predictions = analyze(data, cfg)
        self.assertEqual(report['audit']['excluded_missing_rows'], 2)
        self.assertNotIn(3, predictions['data_row_number'].tolist())
        self.assertNotIn(6, predictions['data_row_number'].tolist())

    def test_numeric_conjoint_attributes_do_not_get_incomplete_importance(self):
        data = conjoint_fixture()
        data['numeric_price'] = data['profile'].map({'p0': 1, 'p1': 2, 'p2': 3, 'p3': 5})
        cfg = {**conjoint_config('conjoint-rating'), 'numeric': ['numeric_price']}
        report, _ = analyze(data, cfg)
        self.assertTrue(all(row['importance_percent'] is None for row in report['conjoint']['importance']))
        self.assertIn('no declared level ranges', report['conjoint']['note'])

    def test_rating_conjoint_partworths_and_importance(self):
        report, _ = analyze(conjoint_fixture(), conjoint_config('conjoint-rating'))
        params = {r['term']: r['estimate'] for r in report['coefficients']}
        self.assertAlmostEqual(params['a[high]'], 2, delta=0.1)
        self.assertAlmostEqual(params['b[high]'], 1, delta=0.1)
        self.assertEqual(report['audit']['independent_respondents'], 45)
        for attribute in ['a', 'b']:
            rows = [r for r in report['conjoint']['utilities'] if r['attribute'] == attribute]
            self.assertAlmostEqual(sum(r['zero_centered'] for r in rows), 0)
        self.assertAlmostEqual(sum(r['importance_percent'] for r in report['conjoint']['importance']), 100)

    def test_rank_direction_conversion_and_approximation_label(self):
        report, predictions = analyze(conjoint_fixture(), conjoint_config('conjoint-rank'))
        params = {r['term']: r['estimate'] for r in report['coefficients']}
        self.assertGreater(params['a[high]'], 0)
        self.assertGreater(params['b[high]'], 0)
        self.assertIn('approximation', ' '.join(report['warnings']))
        self.assertEqual(set(predictions['observed_model_scale']), {1, 2, 3, 4})

    def test_rank_ties_partial_and_unacknowledged_approximation_rejected(self):
        cfg = conjoint_config('conjoint-rank')
        data = conjoint_fixture()
        cfg['acknowledge_rank_approximation'] = False
        with self.assertRaisesRegex(ValueError, 'explicit'):
            analyze(data, cfg)
        cfg['acknowledge_rank_approximation'] = True
        data.loc[0, 'rank'] = data.loc[1, 'rank']
        with self.assertRaisesRegex(ValueError, 'permutation'):
            analyze(data, cfg)
        with self.assertRaisesRegex(ValueError, 'permutation|same complete'):
            analyze(conjoint_fixture().drop(index=0), cfg)

    def test_consistent_profiles_and_complete_tasks_required(self):
        data = conjoint_fixture()
        data.loc[0, 'a'] = 'high'
        with self.assertRaisesRegex(ValueError, 'inconsistent'):
            analyze(data, conjoint_config('conjoint-rating'))
        data = conjoint_fixture()
        data.loc[0, 'rank'] = np.nan
        cfg = {**conjoint_config('conjoint-rank'), 'missing': 'complete-case'}
        with self.assertRaisesRegex(ValueError, 'individual'):
            analyze(data, cfg)

    def test_choice_model_and_bootstrap_are_seeded_and_set_aware(self):
        data = conjoint_fixture(choice=True)
        cfg = conjoint_config('conjoint-choice')
        report, predicted = analyze(data, cfg)
        repeated, _ = analyze(data, cfg)
        self.assertEqual(report['coefficients'], repeated['coefficients'])
        coefficients = {r['term']: r for r in report['coefficients']}
        self.assertNotIn('Intercept', coefficients)
        self.assertGreater(coefficients['a[high]']['estimate'], 0.3)
        self.assertLess(coefficients['b[high]']['estimate'], -0.1)
        self.assertTrue(all(r['p_value'] is None for r in report['coefficients']))
        self.assertEqual(report['diagnostics']['bootstrap']['successful'], 20)
        sums = predicted['fitted_in_sample'].to_numpy().reshape(-1, 3).sum(axis=1)
        np.testing.assert_allclose(sums, 1)

    def test_choice_invalid_tasks_and_within_set_constant_fail(self):
        data = conjoint_fixture(choice=True)
        cfg = conjoint_config('conjoint-choice')
        data.loc[:2, 'chosen'] = 0
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            analyze(data, cfg)
        data = conjoint_fixture(choice=True)
        data['person_value'] = data['respondent'].astype(int)
        with self.assertRaisesRegex(ValueError, 'inconsistent|identifiable'):
            analyze(data, {**cfg, 'numeric': ['person_value']})

    def test_separated_conditional_logit_cannot_return_zero_width_bootstrap_cis(self):
        rows = []
        for respondent in range(30):
            for task in range(3):
                for profile, a, b in [('p0', 'low', 'low'), ('p1', 'high', 'low'), ('p2', 'low', 'high'), ('p3', 'high', 'high')]:
                    rows.append({'respondent': str(respondent), 'task': str(task), 'profile': profile,
                                 'a': a, 'b': b, 'chosen': int(profile == 'p1')})
        with self.assertRaisesRegex(ValueError, 'quasi separation'):
            analyze(pd.DataFrame(rows), conjoint_config('conjoint-choice'))

    def test_qualtrics_multiline_headers_bom_and_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'export.csv'
            with file.open('w', encoding='utf-8-sig', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerows([['id', 'answer'], ['ID', 'Question with\na newline'], ['{"ImportId":"id"}', '{"ImportId":"QID1"}'], ['R_1', '1'], ['R_2', '']])
            data = read_csv(file, 3)
            self.assertEqual(data.shape, (2, 2))
            report = inspect_csv(file, 3)
            self.assertEqual(report['columns'][1]['missing_blank'], 1)

    def test_output_artifacts_and_overwrite_protection(self):
        report, predictions = analyze(linear_fixture(), {'model': 'linear', 'outcome': {'column': 'y'}, 'numeric': ['x']})
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'run'
            save_analysis(report, predictions, output)
            self.assertTrue((output / 'diagnostics.png').stat().st_size > 1000)
            self.assertEqual(json.loads((output / 'analysis.json').read_text())['audit']['analysis_rows'], 400)
            with self.assertRaisesRegex(ValueError, 'exists'):
                save_analysis(report, predictions, output)

    def test_zero_range_importance_is_not_fabricated(self):
        rows = utilities({'a[high]': 0}, [{'attribute': 'a', 'levels': ['low', 'high'], 'reference': 'low', 'columns': {'high': 'a[high]'}}])
        self.assertIsNone(rows['importance'][0]['importance_percent'])


if __name__ == '__main__':
    unittest.main()

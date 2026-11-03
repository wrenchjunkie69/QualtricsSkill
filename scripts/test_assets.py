"""Exercise selectable templates with synthetic data; no account/profile reads."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from analyze import analyze
from test_analytics import linear_fixture, conjoint_fixture

ROOT = Path(__file__).resolve().parents[1]


class AssetTests(unittest.TestCase):
    def test_question_templates_make_preview_requests_only(self):
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder) / 'profile.json'
            profile.write_text('{"datacenter":"iad1"}')
            tags = []
            files = sorted((ROOT / 'assets/questions').glob('*.json'))
            self.assertEqual(len(files), 7)
            for file in files:
                question = json.loads(file.read_text())
                tags.append(question['DataExportTag'])
                result = subprocess.run(['node', str(ROOT / 'scripts/qualtrics.mjs'), 'request', '--profile', str(profile),
                                         '--method', 'POST', '--path', '/survey-definitions/SV_Test/questions', '--json-file', str(file)],
                                        capture_output=True, text=True, check=True)
                preview = json.loads(result.stdout)
                self.assertTrue(preview['dryRun'])
                self.assertEqual(preview['body']['QuestionType'], question['QuestionType'])
                if 'ChoiceOrder' in question:
                    self.assertEqual(set(question['ChoiceOrder']), set(question['Choices']))
            self.assertEqual(len(tags), len(set(tags)))

    def test_all_five_model_configurations_work_after_explicit_column_mapping(self):
        for name in ['linear', 'logistic', 'conjoint-rating', 'conjoint-rank', 'conjoint-choice']:
            cfg = json.loads((ROOT / 'assets/analysis' / (name + '.json')).read_text())
            if name in {'linear', 'logistic'}:
                data = linear_fixture().rename(columns={'x': 'wait_minutes', 'group': 'service_type', 'y': 'satisfaction_score'})
                data['service_type'] = data['service_type'].map({'A': 'standard', 'B': 'priority'})
                if name == 'logistic':
                    rng = np.random.default_rng(53)
                    data['purchase'] = np.where(rng.random(len(data)) < 1 / (1 + np.exp(-data['wait_minutes'])), 'yes', 'no')
            else:
                data = conjoint_fixture(choice=name == 'conjoint-choice').rename(columns={'respondent': 'respondent_id', 'task': 'task_id', 'profile': 'profile_id', 'a': 'service', 'b': 'price'})
                data['service'] = data['service'].map({'low': 'basic', 'high': 'premium'})
                data['price'] = data['price'].map({'low': '10', 'high': '20'})
                if name == 'conjoint-choice':
                    cfg['bootstrap_reps'] = 20  # Smoke test only; published configuration requests 500.
            report, _ = analyze(data, cfg)
            self.assertEqual(report['model'], name)

    def test_selected_python_model_starter_executes_only_chosen_model(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            data = linear_fixture().rename(columns={'x': 'wait_minutes', 'group': 'service_type', 'y': 'satisfaction_score'})
            data['service_type'] = data['service_type'].map({'A': 'standard', 'B': 'priority'})
            file = folder / 'data.csv'; data.to_csv(file, index=False)
            subprocess.run([sys.executable, str(ROOT / 'assets/analysis/run_model.py'), '--skill-dir', str(ROOT), '--data', str(file),
                            '--config', str(ROOT / 'assets/analysis/linear.json'), '--out', str(folder / 'run')], check=True, capture_output=True)
            report = json.loads((folder / 'run/analysis.json').read_text())
            self.assertEqual(report['model'], 'linear')
            slope = next(row for row in report['coefficients'] if row['term'] == 'wait_minutes')
            self.assertAlmostEqual(slope['estimate'], 3, delta=0.04)

    def test_custom_welch_starter_effect_and_repeated_person_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            rng = np.random.default_rng(110)
            data = pd.DataFrame({'person': np.arange(200), 'group': ['A'] * 100 + ['B'] * 100,
                                 'value': np.r_[rng.normal(0, 1, 100), rng.normal(5, 1, 100)]})
            file = folder / 'data.csv'; data.to_csv(file, index=False)
            command = [sys.executable, str(ROOT / 'assets/analysis/custom_welch.py'), '--skill-dir', str(ROOT), '--data', str(file),
                       '--value', 'value', '--group', 'group', '--group-a', 'A', '--group-b', 'B', '--respondent', 'person']
            subprocess.run(command + ['--out', str(folder / 'welch.json')], check=True, capture_output=True)
            report = json.loads((folder / 'welch.json').read_text())
            self.assertAlmostEqual(report['meanDifference_A_minus_B'], -5, delta=0.4)
            self.assertLess(report['ci95'][1], 0)
            data.loc[100, 'person'] = 0; data.to_csv(file, index=False)
            rejected = subprocess.run(command + ['--out', str(folder / 'rejected.json')], capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('Repeated people', rejected.stderr)


if __name__ == '__main__':
    unittest.main()

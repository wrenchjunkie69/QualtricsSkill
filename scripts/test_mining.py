"""Synthetic science checks for selected local mining tasks; no account or network."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from mining import run

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    rng = np.random.default_rng(317)
    x = rng.normal(size=180)
    frame = pd.DataFrame({'person': ['p'+str(i) for i in range(180)], 'x': x,
                          'z': rng.normal(size=180), 'category': np.where(x > 0, 'a', 'b'),
                          'split': ['train']*140+['test']*40})
    frame['y'] = 2+4*x+0.1*rng.normal(size=len(frame))
    frame['event'] = np.where(x+0.3*frame['z'] > 0, 'yes', 'no')
    config = {'task':'supervised', 'problem':'regression', 'target':'y', 'numeric':['x','z'],
              'categorical':[], 'partition':'split', 'group':'person', 'algorithm':'linear', 'seed':7}
    return frame, config


class MiningTests(unittest.TestCase):
    def test_planted_regression_beats_training_mean_baseline_without_mutating_input(self):
        data, cfg = fixture(); original = data.copy(deep=True)
        report, tables, model = run(data, cfg)
        self.assertLess(report['model_metrics']['rmse'], 0.2)
        self.assertGreater(report['baseline_metrics']['rmse'], 2)
        self.assertEqual(len(tables['test_predictions']), 40)
        np.testing.assert_allclose(model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['scale'].mean_, data.loc[:139,['x','z']].mean())
        pd.testing.assert_frame_equal(data, original)

    def test_every_selected_estimator_executes_for_binary_and_regression(self):
        data, cfg = fixture()
        for problem in ['binary', 'regression']:
            for algorithm in ['linear', 'tree', 'forest', 'knn', 'mlp']:
                c = {**cfg, 'problem':problem, 'algorithm':algorithm, 'categorical':['category']}
                if problem == 'binary': c.update(target='event', positive_event='yes', threshold=0.4)
                if algorithm == 'forest': c['parameters'] = {'n_estimators':20, 'max_depth':4}
                if algorithm == 'mlp': c['parameters'] = {'hidden_layer_sizes':[4], 'alpha':1.0, 'max_iter':3000}
                with self.subTest(problem=problem, algorithm=algorithm):
                    report, _, _ = run(data, c)
                    self.assertEqual(report['test_rows'],40)
                    self.assertEqual(report['fit_warnings'],[])

    def test_missing_training_imputation_and_unseen_test_categories_are_audited(self):
        data, cfg = fixture(); cfg['categorical'] = ['category']
        data.loc[0,'x'] = np.nan; data.loc[140:,'category'] = 'new'
        _, _, model = run(data, cfg)
        stats = model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['imputer'].statistics_
        self.assertAlmostEqual(stats[0], data.loc[:139,'x'].median())
        report, _, _ = run(data, cfg)
        self.assertEqual(report['training_missing']['x'],1)
        self.assertEqual(report['unknown_test_categories']['category'],40)

    def test_group_leakage_and_unacknowledged_row_independence_are_rejected(self):
        data, cfg = fixture(); data.loc[140,'person'] = data.loc[0,'person']
        with self.assertRaisesRegex(ValueError,'both training and test'): run(data,cfg)
        cfg.pop('group')
        with self.assertRaisesRegex(ValueError,'independent_rows'): run(data,cfg)

    def test_temporal_overlap_and_missing_or_unknown_labels_are_rejected(self):
        data, cfg = fixture(); cfg.pop('group'); cfg['time'] = 'date'
        data['date'] = pd.date_range('2025-01-01',periods=180,tz='UTC')
        report, _, _ = run(data,cfg); self.assertEqual(report['test_rows'],40)
        data.loc[140,'date'] = data.loc[1,'date']
        with self.assertRaisesRegex(ValueError,'strictly before'): run(data,cfg)
        data, cfg = fixture(); cfg.update(problem='binary',target='event',positive_event='yes',threshold=0.5)
        data.loc[140,'event'] = 'third'
        with self.assertRaisesRegex(ValueError,'unknown test classes'): run(data,cfg)
        data.loc[140,'event'] = ''
        with self.assertRaisesRegex(ValueError,'cannot be missing'): run(data,cfg)

    def test_parsed_textual_nat_cannot_bypass_the_time_boundary(self):
        data,cfg = fixture();cfg.pop('group');cfg['time'] = 'date'
        data['date'] = ['NaT']*140+['2026-01-01']*40
        with self.assertRaisesRegex(ValueError,'Parsed time values cannot be missing'):run(data,cfg)

    def test_binary_event_confusion_matrix_and_missing_class_metrics(self):
        data, cfg = fixture(); cfg.update(problem='binary',target='event',positive_event='no',threshold=0.7)
        data.loc[140:,'event'] = 'no'
        report, tables, _ = run(data,cfg); m = report['model_metrics']
        self.assertEqual(m['events'],40)
        self.assertEqual(m['tp']+m['fn'],40)
        self.assertEqual(m['tn']+m['fp'],0)
        self.assertIsNone(m['roc_auc']); self.assertIsNone(m['specificity'])
        self.assertTrue(tables['test_predictions']['event_probability'].between(0,1).all())

    def test_target_metadata_and_nonfinite_features_cannot_be_used_as_inputs(self):
        data, cfg = fixture()
        for column in ['y','split','person']:
            bad = {**cfg,'numeric':['x',column]}
            with self.assertRaisesRegex(ValueError,'cannot be predictors'): run(data,bad)
        data.loc[0,'x'] = np.inf
        with self.assertRaisesRegex(ValueError,'infinite'): run(data,cfg)

    def test_numeric_segmentation_recovers_separated_groups_and_reports_pca_weights(self):
        rng = np.random.default_rng(9)
        values = np.r_[rng.normal(-4,0.2,(35,3)),rng.normal(4,0.2,(35,3))]
        data = pd.DataFrame(values,columns=['a','b','c']);data['person'] = np.arange(70)
        cfg = {'task':'segment','unit':'person','features':['a','b','c'],'clusters':2,'pca_components':2,'seed':11}
        report,tables,_ = run(data,cfg)
        self.assertGreater(report['silhouette'],0.9)
        self.assertEqual(adjusted_rand_score([0]*35+[1]*35,tables['assignments']['cluster']),1)
        self.assertEqual(len(tables['pca_component_weights']),2)
        self.assertEqual(report['initialization_ari'],[1,1,1])

    def test_segmentation_rejects_duplicate_units_constant_features_and_invalid_k(self):
        data = pd.DataFrame({'id':[1,1,3,4],'a':[0,1,3,4],'b':[0,2,6,8]})
        cfg = {'task':'segment','unit':'id','features':['a','b'],'clusters':2}
        with self.assertRaisesRegex(ValueError,'distinct'):run(data,cfg)
        data['id'] = [1,2,3,4];data['a'] = 1
        with self.assertRaisesRegex(ValueError,'must vary'):run(data,cfg)
        data['a'] = [0,1,3,4]
        with self.assertRaisesRegex(ValueError,'more rows'):
            run(data,{**cfg,'clusters':4})

    def test_pair_support_confidence_direction_lift_and_empty_rule_schema(self):
        data = pd.DataFrame({'a':[1,1,1,0,0,0], 'b':[1,1,0,1,1,0]})
        cfg = {'task':'association_pairs','items':['a','b'],'min_count':1}
        report,tables,_ = run(data,cfg); a,b = tables['pair_rules'].to_dict('records')
        self.assertAlmostEqual(a['support'],2/6);self.assertAlmostEqual(a['confidence'],2/3)
        self.assertAlmostEqual(b['confidence'],2/4);self.assertAlmostEqual(a['lift'],1)
        report,tables,_ = run(data,{**cfg,'min_count':4})
        self.assertEqual(report['rules'],0);self.assertIn('confidence',tables['pair_rules'].columns)
        data.loc[0,'a'] = np.nan
        with self.assertRaisesRegex(ValueError,'observed 0/1'):run(data,cfg)

    def test_value_scenario_matches_manual_survival_discount_and_cost_timing(self):
        cfg = {'task':'customer_value','period':'year','retention':[0.5,0.8], 'margin':[20,30],
               'discount_rate':0.1,'initial_margin':7,'acquisition_cost':3}
        report,tables,_ = run(None,cfg)
        self.assertAlmostEqual(report['finite_horizon_net_value'],4+10/1.1+12/1.1**2)
        self.assertAlmostEqual(tables['cash_flow'].iloc[1]['survival_probability'],0.4)
        report,_,_ = run(None,{**cfg,'retention':[0,1]})
        self.assertEqual(report['finite_horizon_net_value'],4)
        for bad in [{'retention':[1.1,0.8]}, {'margin':[20]}, {'discount_rate':-1}, {'period':''}]:
            with self.assertRaises(ValueError):run(None,{**cfg,**bad})

    def test_value_scenario_handles_large_discount_and_rejects_nonfinite_total(self):
        cfg = {'task':'customer_value','period':'year','retention':[1,1,1], 'margin':[20,30,40], 'discount_rate':1e308}
        report,_,_ = run(None,cfg)
        self.assertAlmostEqual(report['finite_horizon_net_value']/1e-307,2)
        with self.assertRaisesRegex(ValueError,'floating-point range'):
            run(None,{**cfg,'margin':[1e308]*3,'discount_rate':0})

    def test_all_published_configs_and_selected_starter_execute_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            data,cfg = fixture()
            data = data.rename(columns={'person':'respondent_id','x':'visits_before_offer','z':'experience_score','category':'plan_type','event':'renewed'})
            data['convenience_score'] = data['visits_before_offer'];data['variety_score'] = data['experience_score']
            data['service_score'] = np.arange(len(data)) % 5
            data['item_a'] = (np.arange(len(data)) % 2 == 0).astype(int)
            data['item_b'] = (np.arange(len(data)) % 3 == 0).astype(int)
            data['item_c'] = (np.arange(len(data)) % 5 == 0).astype(int)
            source = folder/'data.csv';data.to_csv(source,index=False);before = hashlib.sha256(source.read_bytes()).hexdigest()
            for name in ['supervised','segment','association-pairs','customer-value']:
                config = ROOT/'assets/analysis'/(name+'.json');out = folder/name
                command = [sys.executable,str(ROOT/'assets/analysis/run_mining.py'),'--skill-dir',str(ROOT),'--config',str(config),'--out',str(out)]
                if name != 'customer-value':command += ['--data',str(source)]
                subprocess.run(command,check=True,capture_output=True)
                report = json.loads((out/'report.json').read_text())
                self.assertIn('provenance',report)
                self.assertEqual(report['task'],json.loads(config.read_text())['task'])
                self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertEqual(before,hashlib.sha256(source.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()

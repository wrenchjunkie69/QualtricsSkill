"""Explicit local prediction, segmentation, pair-rule or value scenario; no API calls.

Select one task in a JSON configuration. See references/data-science.md.
"""
import argparse
import hashlib
import importlib.metadata
import itertools
import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (adjusted_rand_score, average_precision_score, log_loss,
                             mean_absolute_error, mean_squared_error, r2_score,
                             roc_auc_score, silhouette_score)
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from analyze import read_csv

ROOT = Path(__file__).resolve().parents[1]
TASKS = {'supervised', 'segment', 'association_pairs', 'customer_value'}


def integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value


def number(value, name, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(name + ' must be finite and numeric')
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(name + ' is outside its allowed range')
    return float(value)


def columns(data, names):
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or not n for n in names) or len(set(names)) != len(names):
        raise ValueError('Declare a nonempty list of distinct column names')
    if not set(names).issubset(data.columns):
        raise ValueError('A configured column is absent from the dataset')
    return names


def numeric(data, names):
    result = data[names].apply(pd.to_numeric, errors='raise').astype(float)
    if np.isinf(result.to_numpy()).any():
        raise ValueError('Numeric fields contain infinite values')
    return result


def fit_checked(model, x, y=None):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model.fit(x, y)
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise ValueError('Estimator did not converge; revise the training configuration')
    return [w.category.__name__ for w in caught]


def estimator(config, classification, seed):
    name = config['algorithm']
    params = config.get('parameters', {})
    choices = {
        'linear': (LogisticRegression(max_iter=2000, random_state=seed) if classification else Ridge(), {'C'} if classification else {'alpha'}),
        'tree': (DecisionTreeClassifier(random_state=seed) if classification else DecisionTreeRegressor(random_state=seed), {'max_depth', 'min_samples_leaf', 'ccp_alpha'}),
        'forest': (RandomForestClassifier(n_jobs=1, random_state=seed) if classification else RandomForestRegressor(n_jobs=1, random_state=seed), {'n_estimators', 'max_depth', 'min_samples_leaf', 'max_features'}),
        'knn': (KNeighborsClassifier(n_jobs=1) if classification else KNeighborsRegressor(n_jobs=1), {'n_neighbors', 'weights', 'p'}),
        'mlp': (MLPClassifier(solver='lbfgs', max_iter=2000, random_state=seed) if classification else MLPRegressor(solver='lbfgs', max_iter=2000, random_state=seed), {'hidden_layer_sizes', 'alpha', 'max_iter'})}
    if name not in choices or not isinstance(params, dict) or not set(params).issubset(choices[name][1]):
        raise ValueError('Unknown algorithm or unsupported parameters')
    model = choices[name][0]
    model.set_params(**params)
    return model


def classification_metrics(y, probability, threshold):
    prediction = probability >= threshold
    tp = int(((y == 1) & prediction).sum()); fn = int(((y == 1) & ~prediction).sum())
    tn = int(((y == 0) & ~prediction).sum()); fp = int(((y == 0) & prediction).sum())
    ratio = lambda a, b: float(a / b) if b else None
    both = len(np.unique(y)) == 2
    return {'n': len(y), 'events': int(y.sum()), 'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
            'accuracy': (tp + tn) / len(y), 'precision': ratio(tp, tp + fp),
            'recall': ratio(tp, tp + fn), 'specificity': ratio(tn, tn + fp),
            'f1': ratio(2 * tp, 2 * tp + fp + fn),
            'balanced_accuracy': ((tp / (tp + fn)) + (tn / (tn + fp))) / 2 if both else None,
            'roc_auc': float(roc_auc_score(y, probability)) if both else None,
            'average_precision': float(average_precision_score(y, probability)) if both else None,
            'brier': float(np.mean((y - probability) ** 2)),
            'log_loss': float(log_loss(y, probability, labels=[0, 1])),
            'undefined_metrics': 'null means the required class/denominator was absent, not a zero score'}


def regression_metrics(y, prediction):
    return {'n': len(y), 'mae': float(mean_absolute_error(y, prediction)),
            'rmse': float(np.sqrt(mean_squared_error(y, prediction))),
            'r_squared': float(r2_score(y, prediction)) if len(y) > 1 and np.var(y) > 0 else None}


def supervised(data, config):
    allowed = {'task', 'target', 'numeric', 'categorical', 'partition', 'group', 'time',
               'independent_rows', 'algorithm', 'parameters', 'problem', 'positive_event',
               'threshold', 'seed', 'missing_values'}
    if set(config) - allowed:
        raise ValueError('Unknown supervised configuration field')
    target, partition = config['target'], config['partition']
    numeric_names, categorical_names = config.get('numeric', []), config.get('categorical', [])
    features = columns(data, numeric_names + categorical_names)
    required = [target, partition] + [config[n] for n in ['group', 'time'] if config.get(n)]
    if not set(required).issubset(data.columns) or set(required) & set(features):
        raise ValueError('Target/partition/group/time must exist and cannot be predictors')
    if data[required].isna().any().any():
        raise ValueError('Target, partition, group and time cannot be missing')
    if set(data[partition].astype(str)) != {'train', 'test'}:
        raise ValueError('Declare exactly train and test rows in the partition column')
    train = data[partition].astype(str).eq('train').to_numpy(); test = ~train
    if train.sum() < 4 or test.sum() < 2:
        raise ValueError('Need at least four training and two test rows; this is not a sample-size guarantee')
    if config.get('group'):
        g = data[config['group']].astype(str)
        if set(g[train]) & set(g[test]):
            raise ValueError('A group occurs in both training and test partitions')
    elif config.get('independent_rows') is not True and not config.get('time'):
        raise ValueError('Specify groups, time ordering, or an explicit independent_rows assumption')
    if config.get('time'):
        t = pd.to_datetime(data[config['time']], errors='raise', utc=True, format='mixed')
        if t.isna().any():
            raise ValueError('Parsed time values cannot be missing, including textual NaT')
        if t[train].max() >= t[test].min():
            raise ValueError('Time split must put every training timestamp strictly before test timestamps')
    x = data[features].copy()
    transforms = []
    if numeric_names:
        x[numeric_names] = numeric(x, numeric_names)
        if x.loc[train, numeric_names].isna().all().any():
            raise ValueError('A numeric feature is entirely missing in training data')
        transforms.append(('numeric', Pipeline([('imputer', SimpleImputer(strategy='median')),
                                               ('scale', StandardScaler())]), numeric_names))
    if categorical_names:
        for name in categorical_names:
            x[name] = x[name].map(lambda v: str(v) if pd.notna(v) else np.nan).astype(object)
        if x.loc[train, categorical_names].isna().all().any():
            raise ValueError('A categorical feature is entirely missing in training data')
        transforms.append(('categorical', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')),
                                                   ('encode', OneHotEncoder(handle_unknown='ignore'))]), categorical_names))
    problem = config['problem']
    if problem not in {'binary', 'regression'}:
        raise ValueError('This starter supports binary classification or numeric regression')
    classification = problem == 'binary'
    if classification:
        labels = data[target].astype(str)
        levels = sorted(labels[train].unique())
        event = str(config['positive_event'])
        if len(levels) != 2 or event not in levels or not set(labels[test]).issubset(levels):
            raise ValueError('Training needs two classes, an explicit event and no unknown test classes')
        threshold = number(config['threshold'], 'threshold', 0, 1)
        y = labels.eq(event).to_numpy(dtype=int)
    else:
        y = numeric(data, [target])[target].to_numpy()
        if not np.isfinite(y).all():
            raise ValueError('Regression target must be finite and observed')
    seed = integer(config.get('seed', 2026), 'seed', 0)
    model = estimator(config, classification, seed)
    if config['algorithm'] == 'knn' and model.n_neighbors > train.sum():
        raise ValueError('n_neighbors exceeds the training row count')
    pipeline = Pipeline([('preprocess', ColumnTransformer(transforms, sparse_threshold=1.0)), ('model', model)])
    fit_warnings = fit_checked(pipeline, x.loc[train], y[train])
    result = {'task': 'supervised', 'problem': problem, 'algorithm': config['algorithm'],
              'training_rows': int(train.sum()), 'test_rows': int(test.sum()),
              'training_missing': {n: int(x.loc[train, n].isna().sum()) for n in features},
              'test_missing': {n: int(x.loc[test, n].isna().sum()) for n in features},
              'fit_warnings': fit_warnings,
              'limitation': 'One fixed model/threshold, one declared holdout; no tuning, causal inference, complex-survey inference or uncertainty intervals. Grouped rows still give row-weighted metrics.'}
    predictions = pd.DataFrame({'row_number': np.flatnonzero(test) + 1, 'actual': y[test]})
    if classification:
        probability = pipeline.predict_proba(x.loc[test])[:, 1]
        if not np.isfinite(probability).all():
            raise ValueError('Estimator produced nonfinite probabilities')
        baseline = np.full(int(test.sum()), y[train].mean())
        result.update({'positive_event': event, 'negative_event': next(v for v in levels if v != event),
                       'threshold': threshold, 'model_metrics': classification_metrics(y[test], probability, threshold),
                       'baseline_metrics': classification_metrics(y[test], baseline, threshold)})
        predictions['event_probability'] = probability
        predictions['predicted_event'] = (probability >= threshold).astype(int)
    else:
        prediction = pipeline.predict(x.loc[test])
        if not np.isfinite(prediction).all():
            raise ValueError('Estimator produced nonfinite predictions')
        result.update({'model_metrics': regression_metrics(y[test], prediction),
                       'baseline_metrics': regression_metrics(y[test], np.full(int(test.sum()), y[train].mean()))})
        predictions['predicted'] = prediction
    result['unknown_test_categories'] = {n: int((x.loc[test, n].notna() & ~x.loc[test, n].isin(x.loc[train, n].dropna().unique())).sum()) for n in categorical_names}
    return result, {'test_predictions': predictions}, pipeline


def segment(data, config):
    if set(config) - {'task', 'features', 'unit', 'clusters', 'pca_components', 'seed', 'missing_values'}:
        raise ValueError('Unknown segmentation configuration field')
    features = columns(data, config['features']); unit = config['unit']
    if unit not in data or unit in features or data[unit].isna().any() or data[unit].duplicated().any():
        raise ValueError('Segmentation requires a distinct, observed unit ID for each row, excluded from features')
    x = numeric(data, features)
    if x.isna().all().any() or x.nunique().le(1).any():
        raise ValueError('Numeric segmentation features must vary and cannot be entirely missing')
    k = integer(config['clusters'], 'clusters', 2); seed = integer(config.get('seed', 2026), 'seed', 0)
    if k >= len(x):
        raise ValueError('Need more rows than clusters')
    preprocess = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scale', StandardScaler())])
    z = preprocess.fit_transform(x)
    pca = None; components = config.get('pca_components')
    if components is not None:
        integer(components, 'pca_components')
        if components > min(z.shape):
            raise ValueError('Too many PCA components')
        pca = PCA(n_components=components, svd_solver='full'); z = pca.fit_transform(z)
    if len(np.unique(z, axis=0)) < k:
        raise ValueError('Fewer distinct feature profiles than requested clusters')
    models = [KMeans(n_clusters=k, n_init=20, random_state=seed+i).fit(z) for i in range(3)]
    labels = models[0].labels_
    if any(len(set(m.labels_)) != k for m in models):
        raise ValueError('An initialization did not produce the requested cluster count')
    try:
        silhouette = float(silhouette_score(z, labels, sample_size=min(len(z), 5000), random_state=seed))
    except ValueError:
        silhouette = None
    result = {'task': 'segment', 'rows': len(x), 'clusters': k, 'missing_by_feature': x.isna().sum().to_dict(),
              'silhouette': silhouette, 'silhouette_sample_limit': 5000,
              'initialization_ari': [float(adjusted_rand_score(a.labels_, b.labels_)) for a, b in itertools.combinations(models, 2)],
              'limitation': 'Exploratory fit to this sample. Same-sample initialization agreement is not resampling/temporal validation or proof of actionable segments. Silhouette uses the fitted space.'}
    assigned = data[[unit]].copy(); assigned['cluster'] = labels
    profiled = x.copy(); profiled['cluster'] = labels
    profiles = profiled.groupby('cluster')[features].agg(['mean', 'median', 'count'])
    profiles.columns = [f'{n}__{stat}' for n, stat in profiles.columns]
    tables = {'assignments': assigned, 'profiles_observed_units': profiles.reset_index()}
    if pca is not None:
        result['pca_explained_variance_ratio'] = pca.explained_variance_ratio_.tolist()
        tables['pca_component_weights'] = pd.DataFrame(pca.components_, columns=features,
            index=[f'PC{i+1}' for i in range(pca.n_components_)]).rename_axis('component').reset_index()
    return result, tables, (preprocess, pca, models[0])


def association_pairs(data, config):
    if set(config) - {'task', 'items', 'min_count', 'missing_values'}:
        raise ValueError('Unknown pair-rule configuration field')
    items = columns(data, config['items'])
    if not 2 <= len(items) <= 200:
        raise ValueError('Choose 2 to 200 item indicator columns for this pairwise starter')
    x = numeric(data, items)
    if not x.isin([0, 1]).all().all():
        raise ValueError('Item indicators must be observed 0/1; missing does not mean absent')
    minimum = integer(config.get('min_count', 1), 'min_count')
    rows = []
    for a, b in itertools.combinations(items, 2):
        both = int((x[a].eq(1) & x[b].eq(1)).sum())
        if both < minimum: continue
        count_a, count_b = int(x[a].sum()), int(x[b].sum())
        support = both / len(x); pa, pb = count_a / len(x), count_b / len(x)
        for lhs, rhs, ca, cb in [(a, b, count_a, count_b), (b, a, count_b, count_a)]:
            rows.append({'antecedent': lhs, 'consequent': rhs, 'both_count': both,
                         'antecedent_count': ca, 'consequent_count': cb,
                         'support': support, 'confidence': both / ca,
                         'lift': support / (pa * pb), 'leverage': support - pa * pb})
    names = ['antecedent', 'consequent', 'both_count', 'antecedent_count', 'consequent_count', 'support', 'confidence', 'lift', 'leverage']
    return {'task': 'association_pairs', 'baskets': len(x), 'rules': len(rows), 'min_count': minimum,
            'limitation': 'Descriptive pairwise co-occurrence, not full Apriori/FP-growth, causal influence, recommendation validation or independent-trial inference. Repeated customers and multiple searches need further assessment.'}, {'pair_rules': pd.DataFrame(rows, columns=names)}, None


def customer_value(config):
    if set(config) - {'task', 'retention', 'margin', 'discount_rate', 'initial_margin', 'acquisition_cost', 'period'}:
        raise ValueError('Unknown customer-value configuration field')
    retention, margin = config['retention'], config['margin']
    if not isinstance(config.get('period'), str) or not config['period'].strip():
        raise ValueError('Declare the nonempty period unit shared by all assumptions')
    if not isinstance(retention, list) or not isinstance(margin, list) or not retention or len(retention) != len(margin):
        raise ValueError('Declare equally sized nonempty per-period retention and margin lists')
    rate = number(config['discount_rate'], 'discount_rate', 0)
    initial = number(config.get('initial_margin', 0), 'initial_margin')
    cost = number(config.get('acquisition_cost', 0), 'acquisition_cost', 0)
    survival = 1.0; discount_factor = 1.0; rows = []
    for t, (r, m) in enumerate(zip(retention, margin), 1):
        survival *= number(r, 'retention', 0, 1); m = number(m, 'margin')
        discount_factor /= 1 + rate
        expected = survival * m; pv = expected * discount_factor
        rows.append({'period_index': t, 'conditional_retention': r, 'survival_probability': survival,
                     'margin_if_retained': m, 'expected_margin': expected, 'present_value': pv})
    try:
        value = math.fsum([initial, -cost, *(row['present_value'] for row in rows)])
    except OverflowError:
        raise ValueError('Scenario value exceeds finite floating-point range; rescale monetary units') from None
    if not math.isfinite(value):
        raise ValueError('Scenario value is nonfinite; rescale monetary units')
    return {'task': 'customer_value', 'period_unit': config['period'], 'horizon_periods': len(rows),
            'initial_margin': initial, 'acquisition_cost': cost, 'finite_horizon_net_value': value,
            'limitation': 'An explicit scenario, not estimated lifetime behavior. Future margins occur at period end conditional on surviving all renewals; no reactivation or terminal value. Initial margin/cost occur now. Rates and margins must use the same period.'}, {'cash_flow': pd.DataFrame(rows)}, None


def run(data, config):
    if config.get('task') not in TASKS:
        raise ValueError('Choose one supported task explicitly')
    if config['task'] == 'customer_value':
        if data is not None:
            raise ValueError('Customer-value scenario uses explicit assumptions, not a dataset')
        return customer_value(config)
    if data is None or data.empty or data.columns.duplicated().any():
        raise ValueError('A nonempty dataset with unique columns is required')
    clean = data.copy().reset_index(drop=True)
    clean = clean.replace(r'^\s*$', np.nan, regex=True)
    missing = config.get('missing_values', [])
    if not isinstance(missing, list):
        raise ValueError('missing_values must be a list')
    for value in missing:
        clean = clean.replace(str(value), np.nan).replace(value, np.nan)
    return {'supervised': supervised, 'segment': segment, 'association_pairs': association_pairs}[config['task']](clean, config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--header-records', choices=[1, 3], type=int, default=1)
    args = parser.parse_args()
    output = args.out.expanduser().resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError('Choose a new output directory outside the skill/repository')
    raw_config = args.config.read_bytes(); config = json.loads(raw_config.decode('utf-8-sig'))
    input_hash = hashlib.sha256(args.data.read_bytes()).hexdigest() if args.data else None
    data = read_csv(args.data, args.header_records) if args.data else None
    report, tables, _ = run(data, config)
    if args.data and input_hash != hashlib.sha256(args.data.read_bytes()).hexdigest():
        raise ValueError('Input changed during analysis; rerun from a stable saved dataset')
    report['provenance'] = {'config_sha256': hashlib.sha256(raw_config).hexdigest(),
                            'data_sha256': input_hash,
                            'header_records': args.header_records,
                            'versions': {n: importlib.metadata.version(n) for n in ['numpy','pandas','scikit-learn']}}
    report['configuration'] = config
    serialized = json.dumps(report, indent=2, allow_nan=False)
    output.mkdir(parents=True, exist_ok=False)
    for name, table in tables.items(): table.to_csv(output / (name + '.csv'), index=False)
    (output/'report.json').write_text(serialized, encoding='utf-8')
    print(json.dumps({'output': str(output), 'task': config['task'], 'tables': list(tables)}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None

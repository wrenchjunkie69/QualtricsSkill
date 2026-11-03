"""Local, explicit survey-analysis core. Python 3.12+; see analytics-runner.md.

No Qualtrics credentials or network requests. Other statistical methods require
an appropriately designed custom analysis, not invented commands in this tool.
"""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
from sklearn.metrics import roc_auc_score, log_loss, mean_squared_error

MODELS = {'linear', 'logistic', 'conjoint-rating', 'conjoint-rank', 'conjoint-choice'}
PACKAGES = ['numpy', 'pandas', 'scipy', 'statsmodels', 'scikit-learn', 'matplotlib']
ALLOWED = {'model', 'outcome', 'numeric', 'categorical', 'missing', 'missing_values',
           'respondent', 'cluster', 'task', 'profile', 'rank_direction',
           'acknowledge_rank_approximation', 'bootstrap_reps', 'seed', 'alpha'}


def read_csv(file, header_records=1):
    if header_records not in (1, 3):
        raise ValueError('Choose one or three CSV header records after inspecting the export')
    with Path(file).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        columns = next(reader)
        if not columns or any(not c for c in columns) or len(set(columns)) != len(columns):
            raise ValueError('CSV columns must be nonempty and unique')
        for _ in range(header_records - 1):
            next(reader)
        rows = list(reader)
    if not rows or any(len(row) != len(columns) for row in rows):
        raise ValueError('CSV has no data rows or contains ragged records')
    return pd.DataFrame(rows, columns=columns)


def inspect_csv(file, header_records=1):
    data = read_csv(file, header_records)
    columns = []
    for name in data.columns:
        values = data[name].replace('', pd.NA)
        numeric = pd.to_numeric(values, errors='coerce')
        valid = int(values.notna().sum())
        columns.append({'name': name, 'missing_blank': int(values.isna().sum()),
                        'distinct_nonblank': int(values.nunique()),
                        'numeric_parse_fraction': float(numeric.notna().sum() / valid) if valid else None})
    return {'rows': len(data), 'columns': columns,
            'note': 'Parsing fractions are suggestions only. Use the codebook to identify nominal, ordinal, ID and continuous variables.'}


def design_matrix(data, config, intercept=True):
    numeric = config.get('numeric', [])
    categorical = config.get('categorical', {})
    if len(set(numeric)) != len(numeric) or set(numeric) & set(categorical):
        raise ValueError('Predictors must be distinct and assigned one coding type')
    frame = pd.DataFrame(index=data.index)
    for column in numeric:
        try:
            frame[column] = pd.to_numeric(data[column], errors='raise').astype(float)
        except (ValueError, TypeError):
            raise ValueError('Non-numeric values in numeric predictor: ' + column) from None
    coding = []
    for column, spec in categorical.items():
        levels = [str(level) for level in spec.get('levels', [])]
        reference = str(spec.get('reference'))
        if 'reference' not in spec or len(levels) < 2 or len(set(levels)) != len(levels) or reference not in levels:
            raise ValueError('Declare distinct levels and an explicit reference for ' + column)
        values = data[column].astype(str)
        if not set(values).issubset(levels):
            raise ValueError('Undeclared categorical levels in ' + column)
        mapping = {}
        for level in levels:
            if level == reference:
                continue
            name = f'{column}[{level}]'
            if name in frame:
                raise ValueError('Duplicate encoded predictor name')
            frame[name] = (values == level).astype(float)
            mapping[level] = name
        coding.append({'attribute': column, 'levels': levels, 'reference': reference, 'columns': mapping})
    if not len(frame.columns):
        raise ValueError('At least one explicit numeric/categorical predictor is required')
    if intercept:
        if 'Intercept' in frame:
            raise ValueError('Intercept is reserved')
        frame.insert(0, 'Intercept', 1.0)
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError('Predictors contain nonfinite values')
    return frame.astype(float), coding


def fit_checked(model, **kwargs):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = model.fit(**kwargs)
    bad = {'PerfectSeparationWarning', 'ConvergenceWarning', 'HessianInversionWarning'}
    if any(w.category.__name__ in bad for w in caught):
        raise ValueError('Model separation/convergence/information failure; simplify or use an appropriate alternative estimator')
    if hasattr(result, 'mle_retvals') and not result.mle_retvals.get('converged', True):
        raise ValueError('Model did not converge')
    if not np.isfinite(np.asarray(result.params)).all():
        raise ValueError('Model returned nonfinite coefficients')
    return result, [w.category.__name__ for w in caught]


def check_separation(X, y, groups=None):
    """Reject binary/conditional-logit complete or quasi separation via a bounded LP.

    A nonzero direction with all favorable outcome contrasts nonnegative and at
    least one positive makes the log likelihood increase toward an infinite
    coefficient. A small numerical optimization score alone cannot exclude it.
    """
    array, outcome = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    if groups is None:
        contrasts = array * (2 * outcome - 1)[:, None]
    else:
        codes = pd.factorize(np.asarray(groups))[0]
        parts = []
        for code in np.unique(codes):
            rows = np.flatnonzero(codes == code)
            chosen = array[rows[outcome[rows] == 1]]
            if len(chosen) != 1:
                raise ValueError('Separation check requires exactly one choice per task')
            parts.append(chosen[0] - array[rows[outcome[rows] == 0]])
        contrasts = np.vstack(parts)
    scale = np.max(np.abs(contrasts), axis=0)
    if (scale == 0).any():
        raise ValueError('Unidentified predictor in separation check')
    normalized = contrasts / scale
    solution = linprog(-normalized.mean(axis=0), A_ub=-normalized, b_ub=np.zeros(len(normalized)),
                       bounds=[(-1, 1)] * normalized.shape[1], method='highs',
                       options={'primal_feasibility_tolerance': 1e-9, 'dual_feasibility_tolerance': 1e-9})
    if not solution.success:
        raise ValueError('Separation check could not be resolved numerically')
    if solution.fun < -1e-8:
        raise ValueError('Complete or quasi separation: no finite unpenalized logistic maximum-likelihood estimate; use a justified alternative estimator/design')


def utilities(params, coding):
    rows, importance = [], []
    ranges = {}
    for attribute in coding:
        points = {level: float(params.get(attribute['columns'].get(level), 0.0)) for level in attribute['levels']}
        center = float(np.mean(list(points.values())))
        ranges[attribute['attribute']] = max(points.values()) - min(points.values())
        rows.extend({'attribute': attribute['attribute'], 'level': level,
                     'reference_coded': value, 'zero_centered': value - center} for level, value in points.items())
    total = sum(ranges.values())
    importance.extend({'attribute': name, 'utility_range': value,
                       'importance_percent': value / total * 100 if total > 1e-12 else None} for name, value in ranges.items())
    return {'utilities': rows, 'importance': importance,
            'note': 'Point estimates; importance is conditional on selected level ranges, coding and model. These are not market shares.'}


def analyze(data, config):
    # Output row numbers refer to positions in the supplied analysis dataset, not its pandas index labels.
    data = data.reset_index(drop=True)
    unknown = set(config) - ALLOWED
    if unknown:
        raise ValueError('Unsupported configuration fields: ' + ', '.join(sorted(unknown)))
    kind = config.get('model')
    if kind not in MODELS:
        raise ValueError('Choose a documented core model; other methods require a custom workflow')
    outcome = config.get('outcome', {})
    target = outcome.get('column')
    predictors = config.get('numeric', []) + list(config.get('categorical', {}))
    if not target or target in predictors:
        raise ValueError('Declare an outcome that is not also a predictor')
    conjoint = kind.startswith('conjoint-')
    respondent = config.get('respondent')
    cluster = respondent if conjoint else config.get('cluster')
    if conjoint and (not respondent or not config.get('profile')):
        raise ValueError('Conjoint requires explicit respondent and stable profile ID columns')
    if kind in {'conjoint-rank', 'conjoint-choice'} and not config.get('task'):
        raise ValueError('Ranking/choice analysis requires a task ID column')
    required = list(dict.fromkeys([target] + predictors + [config.get(k) for k in ['respondent', 'cluster', 'task', 'profile'] if config.get(k)]))
    if any(column not in data for column in required):
        raise ValueError('A required column is missing from the dataset')
    if any(column in predictors for column in [respondent, cluster, config.get('task'), config.get('profile')] if column):
        raise ValueError('ID/group columns cannot be ordinary predictors in this core runner')
    declared_missing = config.get('missing_values', [])
    if not isinstance(declared_missing, list) or any(not isinstance(v, (str, int, float, type(None))) for v in declared_missing):
        raise ValueError('missing_values must be a list of explicitly chosen scalar codes')
    missing_codes = list(dict.fromkeys([''] + declared_missing + [str(v) for v in declared_missing if v is not None]))
    work = data[required].copy().replace(missing_codes, pd.NA)
    invalid = work.isna().any(axis=1)
    missing = config.get('missing', 'error')
    if missing not in {'error', 'complete-case'}:
        raise ValueError('Declare missing as error or complete-case; custom imputation needs a separate workflow')
    if invalid.any() and missing == 'error':
        raise ValueError('Missing analysis values found; choose and document a missing-data strategy')
    if invalid.any() and kind in {'conjoint-rank', 'conjoint-choice'}:
        raise ValueError('Do not delete individual ranking/choice rows; resolve or exclude entire tasks before analysis')
    work = work.loc[~invalid].copy()
    if len(work) < 3:
        raise ValueError('Too few usable observations')
    if respondent and not conjoint and work[respondent].duplicated().any() and not cluster:
        raise ValueError('Repeated respondents require explicit cluster inference or a suitable repeated-measures model')
    if respondent and cluster and (work.groupby(respondent)[cluster].nunique() > 1).any():
        raise ValueError('A respondent crosses declared clusters; use respondent clustering or a model addressing all dependence structures')
    if cluster and work[cluster].nunique() < 2:
        raise ValueError('At least two independent clusters are required; few clusters still limit inference')
    alpha = float(config.get('alpha', 0.05))
    if not 0 < alpha < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    seed = config.get('seed', 20261103)
    if not isinstance(seed, int):
        raise ValueError('seed must be an integer')
    notes = []
    if cluster and work[cluster].nunique() < 30:
        notes.append('Few independent respondent/cluster units: uncertainty can be unstable. Thirty is a warning heuristic, not a validity guarantee.')
    if conjoint:
        if (work.groupby(config['profile'], dropna=False)[predictors].nunique() > 1).any().any():
            raise ValueError('A profile ID maps to inconsistent attribute levels; do not use alternative-position IDs as global profile IDs')
        unique_keys = [respondent] + ([config['task']] if config.get('task') else []) + [config['profile']]
        if work.duplicated(unique_keys).any():
            raise ValueError('Duplicate respondent/task/profile records')
    binary = kind in {'logistic', 'conjoint-choice'}
    if binary:
        if 'event' not in outcome or 'non_event' not in outcome or str(outcome['event']) == str(outcome['non_event']):
            raise ValueError('Declare distinct event and non_event values explicitly')
        mapping = {str(outcome['event']): 1.0, str(outcome['non_event']): 0.0}
        if not set(work[target].astype(str)).issubset(mapping):
            raise ValueError('Unexpected binary outcome values')
        y = work[target].astype(str).map(mapping).astype(float)
        if y.nunique() != 2:
            raise ValueError('Both outcome classes must be observed')
    else:
        try:
            y = pd.to_numeric(work[target], errors='raise').astype(float)
        except (ValueError, TypeError):
            raise ValueError('Outcome must be numeric for the selected model') from None
        if not np.isfinite(y).all():
            raise ValueError('Outcome contains nonfinite values')
        if y.nunique() < 2:
            raise ValueError('Outcome has no variation')
    if kind == 'conjoint-rank':
        if config.get('rank_direction') != '1-is-best' or config.get('acknowledge_rank_approximation') is not True:
            raise ValueError('This restricted rank approximation requires explicit 1-is-best direction and acknowledge_rank_approximation=true')
        sets = []
        for _, group in work.groupby([respondent, config['task']], sort=False):
            ranks = y.loc[group.index].to_numpy()
            if len(group) < 2 or not np.array_equal(np.sort(ranks), np.arange(1, len(group) + 1)):
                raise ValueError('Each rank task must be a complete untied permutation 1..m')
            sets.append(frozenset(group[config['profile']].astype(str)))
            y.loc[group.index] = len(group) + 1 - ranks
        if len(set(sets)) != 1:
            raise ValueError('This course approximation requires the same complete profile set in every rank task')
        notes.append('Pooled OLS approximation to complete rankings; assumes equal rank spacing, not an exact ranking likelihood.')
    choice = kind == 'conjoint-choice'
    X, coding = design_matrix(work, config, intercept=not choice)
    if len(work) <= X.shape[1] + 1:
        raise ValueError('Insufficient residual information for this number of parameters')
    intervals = None
    bootstrap = None
    groups = None
    if choice:
        groups = pd.Series(pd.factorize(pd.MultiIndex.from_frame(work[[respondent, config['task']]]))[0], index=work.index)
        check = pd.DataFrame({'g': groups, 'y': y}).groupby('g')['y'].agg(['count', 'sum'])
        if (check['count'] < 2).any() or (check['sum'] != 1).any():
            raise ValueError('Each single-choice task needs at least two alternatives and exactly one chosen alternative')
        centered = X - X.groupby(groups).transform('mean')
        if np.linalg.matrix_rank(centered.to_numpy()) != X.shape[1]:
            raise ValueError('Choice predictors are not identifiable within tasks; remove constants/aliases or use appropriate interactions')
        check_separation(X, y, groups)
        model = ConditionalLogit(y, X, groups=groups)
        result, fit_warnings = fit_checked(model, method='bfgs', maxiter=500, disp=False)
        score = float(np.max(np.abs(model.score(result.params))) / len(work))
        if score > 1e-4:
            raise ValueError('Conditional-logit optimization score indicates an unresolved fit')
        reps = config.get('bootstrap_reps', 200)
        if not isinstance(reps, int) or not 20 <= reps <= 2000:
            raise ValueError('bootstrap_reps must be an integer from 20 to 2000')
        ids = work[respondent].unique()
        rng = np.random.default_rng(seed)
        draws = []
        for _ in range(reps):
            indices, boot_groups = [], []
            for draw_index, identifier in enumerate(rng.choice(ids, size=len(ids), replace=True)):
                selected = np.flatnonzero((work[respondent] == identifier).to_numpy())
                indices.extend(selected)
                boot_groups.extend([f'{draw_index}:{g}' for g in groups.iloc[selected]])
            try:
                check_separation(X.iloc[indices], y.iloc[indices], np.asarray(boot_groups))
                fitted, _ = fit_checked(ConditionalLogit(y.iloc[indices].to_numpy(), X.iloc[indices].to_numpy(), groups=np.asarray(boot_groups)),
                                        method='bfgs', maxiter=500, disp=False)
                draws.append(np.asarray(fitted.params))
            except (ValueError, np.linalg.LinAlgError):
                continue
        if len(draws) < max(20, int(np.ceil(0.8 * reps))):
            raise ValueError('Too many failed respondent-bootstrap fits; simplify/check the choice design')
        intervals = np.quantile(np.asarray(draws), [alpha / 2, 1 - alpha / 2], axis=0).T
        bootstrap = {'requested': reps, 'successful': len(draws), 'failed': reps - len(draws), 'unit': respondent, 'seed': seed}
        notes.append('Percentile respondent-bootstrap intervals are approximate; increase draws and assess stability for final inference.')
        if reps < 200:
            notes.append('Fewer than 200 bootstrap draws: use primarily as a smoke test, not stable final confidence limits.')
        utility = pd.Series(X.to_numpy() @ np.asarray(result.params), index=work.index)
        exponent = np.exp(utility - utility.groupby(groups).transform('max'))
        predicted = exponent / exponent.groupby(groups).transform('sum')
        covariance = 'respondent percentile bootstrap'
        diagnostics = {'choice_sets': len(check), 'mean_in_sample_choice_log_loss': float(-np.log(predicted[y == 1]).mean()),
                       'score_norm_per_row': score, 'bootstrap': bootstrap,
                       'separation_check': 'Bounded LP found no separating direction within numerical tolerances; also checked in bootstrap fits'}
    else:
        if np.linalg.matrix_rank(X.to_numpy()) != X.shape[1]:
            raise ValueError('Rank-deficient design: inspect aliases, unobserved levels or constant predictors')
        if binary:
            check_separation(X, y)
        kwargs = {'cov_type': 'cluster', 'cov_kwds': {'groups': work[cluster]}} if cluster else {'cov_type': 'HC0' if binary else 'HC3'}
        model = sm.Logit(y, X) if binary else sm.OLS(y, X)
        result, fit_warnings = fit_checked(model, **kwargs, **({'disp': False, 'maxiter': 500} if binary else {}))
        predicted = pd.Series(result.predict(X), index=work.index)
        covariance = 'cluster: ' + cluster if cluster else ('HC0' if binary else 'HC3')
        if binary:
            diagnostics = {'events': int(y.sum()), 'non_events': int((1 - y).sum()), 'event_value': str(outcome['event']),
                           'in_sample_auc': float(roc_auc_score(y, predicted)), 'in_sample_log_loss': float(log_loss(y, predicted)),
                           'pseudo_r_squared': float(result.prsquared),
                           'separation_check': 'Bounded LP found no separating direction within numerical tolerances'}
        else:
            influence = result.get_influence()
            diagnostics = {'r_squared': float(result.rsquared), 'adjusted_r_squared': float(result.rsquared_adj),
                           'in_sample_rmse': float(np.sqrt(mean_squared_error(y, predicted))), 'residual_df': float(result.df_resid),
                           'maximum_cooks_distance': float(influence.cooks_distance[0].max()),
                           'maximum_leverage': float(influence.hat_matrix_diag.max()),
                           'condition_number': float(np.linalg.cond(X.to_numpy()))}
    coefficients = []
    if intervals is None:
        intervals = np.asarray(result.conf_int(alpha=alpha))
    for i, name in enumerate(X.columns):
        estimate = float(np.asarray(result.params)[i])
        row = {'term': name, 'estimate': estimate, 'ci_lower': float(intervals[i, 0]), 'ci_upper': float(intervals[i, 1]),
               'p_value': None if choice else float(np.asarray(result.pvalues)[i])}
        if binary and not choice:
            row.update(odds_ratio=float(np.exp(estimate)), odds_ratio_ci_lower=float(np.exp(intervals[i, 0])), odds_ratio_ci_upper=float(np.exp(intervals[i, 1])))
        coefficients.append(row)
    if any(not np.isfinite(v) for row in coefficients for v in row.values() if isinstance(v, float)):
        raise ValueError('Nonfinite uncertainty/odds ratios; investigate instability rather than reporting this model')
    report = {'model': kind, 'analysis': 'local Python', 'evaluation': 'in-sample fit/diagnostics, not external predictive validation',
              'covariance': covariance, 'alpha': alpha, 'coding': coding, 'coefficients': coefficients,
              'diagnostics': diagnostics, 'warnings': notes + fit_warnings,
              'audit': {'input_rows': len(data), 'analysis_rows': len(work), 'excluded_missing_rows': int(invalid.sum()),
                        'missing_strategy': missing, 'parameters': X.shape[1],
                        'independent_respondents': int(work[respondent].nunique()) if respondent else None,
                        'clusters': int(work[cluster].nunique()) if cluster else None},
              'configuration': config, 'versions': {name: importlib.metadata.version(name) for name in PACKAGES}, 'seed': seed}
    if conjoint:
        report['conjoint'] = utilities(dict(zip(X.columns, np.asarray(result.params))), coding)
        if config.get('numeric'):
            for row in report['conjoint']['importance']:
                row['importance_percent'] = None
            report['conjoint']['note'] += ' Overall importance percentages are not computed because numeric attributes have no declared level ranges.'
            report['warnings'].append('Conjoint includes numeric attributes: categorical utility ranges are reported, but overall attribute importance is unavailable without all attribute ranges.')
    predictions = pd.DataFrame({'data_row_number': work.index.to_numpy() + 1, 'observed_model_scale': y,
                                'fitted_in_sample': predicted, 'residual': y - predicted})
    return report, predictions


def save_analysis(report, predictions, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Output directory already exists; choose a new run directory')
    output.mkdir(parents=True)
    (output / 'analysis.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    pd.DataFrame(report['coefficients']).to_csv(output / 'coefficients.csv', index=False)
    predictions.to_csv(output / 'fitted-values.csv', index=False)
    if 'conjoint' in report:
        pd.DataFrame(report['conjoint']['utilities']).to_csv(output / 'part-worths.csv', index=False)
        pd.DataFrame(report['conjoint']['importance']).to_csv(output / 'attribute-importance.csv', index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    if report['model'] in {'linear', 'conjoint-rating', 'conjoint-rank'}:
        axes[0].scatter(predictions['fitted_in_sample'], predictions['residual'], alpha=0.5, s=12)
        axes[0].axhline(0, color='black', linewidth=1)
        axes[0].set(xlabel='Fitted (in sample)', ylabel='Residual', title='Residual pattern')
        sm.qqplot(predictions['residual'], line='45', fit=True, ax=axes[1])
        axes[1].set_title('Residual normal-QQ diagnostic')
    elif report['model'] == 'logistic':
        from sklearn.calibration import calibration_curve
        from sklearn.metrics import RocCurveDisplay
        RocCurveDisplay.from_predictions(predictions['observed_model_scale'], predictions['fitted_in_sample'], ax=axes[0])
        axes[0].set_title('In-sample ROC: not holdout validation')
        fraction, mean = calibration_curve(predictions['observed_model_scale'], predictions['fitted_in_sample'], n_bins=10, strategy='quantile')
        axes[1].plot(mean, fraction, 'o-')
        axes[1].plot([0, 1], [0, 1], '--', color='gray')
        axes[1].set(xlabel='Mean fitted probability', ylabel='Observed event proportion', title='In-sample calibration')
    else:
        axes[0].hist(predictions.loc[predictions['observed_model_scale'] == 1, 'fitted_in_sample'], bins=10)
        axes[0].set(xlabel='Fitted probability of chosen alternative', ylabel='Tasks', title='In-sample choice fit')
        axes[1].axis('off')
        axes[1].text(0, 0.7, 'Respondent bootstrap intervals\nSee analysis.json for design checks.\nNo out-of-sample validation claimed.')
    figure.tight_layout()
    figure.savefig(output / 'diagnostics.png', dpi=160)
    plt.close(figure)
    notes = '\n'.join('- ' + note for note in report['warnings']) or '- No automatic warning flags; this is not a proof of model validity.'
    (output / 'report.md').write_text(
        f"# Local survey analysis: {report['model']}\n\n"
        f"Analyzed {report['audit']['analysis_rows']} of {report['audit']['input_rows']} rows. "
        f"Covariance/interval method: {report['covariance']}. Confidence level: {100 * (1 - report['alpha']):g}%.\n\n"
        "See coefficients.csv for reference-coded estimates and intervals; analysis.json records coding, event values, exclusions, diagnostics and package versions. "
        "Fitted values and plots describe the fitted sample; they do not establish external predictive performance or causation.\n\n"
        f"## Checks and interpretation limits\n\n{notes}\n\n"
        "Interpret coefficient units, reference categories, sampling limitations and the research question before making recommendations. "
        "Conjoint utility/importance files, when present, contain point estimates conditional on the chosen levels/model.\n", encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'fit'])
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--header-records', type=int, choices=[1, 3], default=1)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.command == 'inspect':
        print(json.dumps(inspect_csv(args.data, args.header_records), indent=2, allow_nan=False))
        return
    if args.config is None or args.out is None:
        parser.error('fit requires --config and --out')
    if args.out.exists():
        raise ValueError('Output directory already exists; choose a new run directory')
    config = json.loads(args.config.read_text(encoding='utf-8-sig'))
    report, predictions = analyze(read_csv(args.data, args.header_records), config)
    report.update(input_sha256=hashlib.sha256(args.data.read_bytes()).hexdigest(),
                  config_sha256=hashlib.sha256(args.config.read_bytes()).hexdigest(), header_records=args.header_records)
    save_analysis(report, predictions, args.out)
    print(json.dumps({'model': report['model'], 'rows': report['audit']['analysis_rows'], 'output': str(args.out.resolve()), 'warnings': report['warnings']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        raise SystemExit(type(error).__name__ + ': ' + str(error)) from None

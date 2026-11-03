# Runnable analysis core

Use this tool for the supported models after planning/coding the analysis. It performs local computation, never reads Qualtrics credentials, and makes no API requests. Its fitted values and performance metrics are in-sample diagnostics, not held-out predictive evaluation. Other methods in the method router require a custom reproducible script using suitable libraries.

## Environment

Python 3.12+ and the tested packages in `scripts/requirements-analysis.txt` are optional dependencies for analytics only. Existing Node API functions still work without Python packages. Use an isolated environment or the project's established compatible environment; record actual versions.

```text
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r scripts/requirements-analysis.txt
```

On Unix use `.venv/bin/python`. Without uv, create a Python virtual environment and run its `python -m pip install -r ...`. The installer records the actual interpreter in the private `~/.config/qualtrics/runtime.json`; read that non-secret path rather than assuming the shell's python command is correct. Resolve script/requirements paths against the skill directory. Environments are recreated locally and are excluded from the portable package.

## Inspect and fit

```text
python scripts/analyze.py inspect --data responses.csv --header-records 3
python scripts/analyze.py fit --data analysis.csv --header-records 1 --config model.json --out analysis-run-01
python -m unittest discover -s scripts -p test_analytics.py
```

Select one or three CSV header records after inspection. Three means the variable-name record followed by two metadata records; the parser respects quoted multiline records and UTF-8 BOM. It does not automatically extract ZIP archives, choose exclusions, build composites, infer category semantics or deduplicate data. Prepare the analysis dataset according to the plan and preserve the raw export.

`inspect` returns row/column counts, blank counts, distinct counts and numeric parsing fractions without respondent examples. These are suggestions; a numeric category code or ID remains categorical/ID according to the codebook.

`fit` accepts an explicit configuration and creates a **new** output directory. It refuses an existing directory. Deliverables: analysis.json (audit, coding, methods, estimates, diagnostics, versions/seed and input/config hashes), coefficients.csv, fitted-values.csv, diagnostics.png, report.md; conjoint adds part-worths.csv and attribute-importance.csv. Fitted values retain data-row positions, not direct respondent IDs. No raw dataset is overwritten.

## Linear and binary logistic regression

Linear example:

```json
{
  "model": "linear",
  "outcome": {"column": "satisfaction_score"},
  "numeric": ["wait_minutes"],
  "categorical": {
    "service_type": {"levels": ["standard", "priority"], "reference": "standard"}
  },
  "missing": "error",
  "missing_values": ["", "-99"],
  "alpha": 0.05,
  "seed": 20261103
}
```

Use `model: "logistic"` and an explicit binary outcome such as `{"column":"purchase","event":"yes","non_event":"no"}` for binary logistic. Event/reference labels must match the CSV text exactly. Logistic output includes log-odds estimates and odds ratios with intervals. An ordinal outcome needs an ordinal workflow, not this binary command or automatic numeric treatment.

Numeric predictors are declared explicitly. Categorical predictors need all planned levels and a reference; the runner creates reference-coded indicators. Unexpected levels, aliased/constant predictors, nonfinite numbers and rank deficiency fail. Add a `cluster` column for dependent observations; when `respondent` is supplied and repeats, the runner requires explicit cluster inference or a different repeated-measures workflow. Every respondent must stay within one declared one-way cluster; grouping their rows by different response/task IDs does not address person dependence. Group/ID columns cannot be ordinary predictors.

Defaults: OLS HC3 covariance, binary Logit HC0 covariance, or cluster covariance when declared. These are not full complex-survey estimators. A small-cluster warning is a heuristic, not a validity threshold. Before binary/conditional-logit fitting, a bounded linear-program check looks for complete or quasi-separating outcome contrasts; conditional bootstrap fits receive the same check. A small optimizer gradient alone does not establish a finite MLE. Separation, failed convergence or nonfinite inference fails rather than automatically switching estimators. Passing numerical checks is not proof of adequate sample size or correct specification. For regularization, ordinal/multinomial/count models, transformations/interactions, multiple imputation, complex weights, mixed models, predictive validation or feature selection, write and validate a separate analysis instead of supplying unsupported config fields.

Missing strategy defaults to error. `complete-case` is available for ordinary/rating models only when chosen/documented by the analysis plan. Blank remains missing even when extra special codes are supplied in missing_values; special codes must be explicitly declared. The tool never drops one alternative/rank row out of an incomplete task to make a choice/ranking analysis run.

## Conjoint input and configurations

Data must be in long form: respondent ID, task ID when relevant, stable global profile ID, attributes, outcome. A profile ID must consistently map to the same attribute values; alternative-position labels reused for different profiles are insufficient. The core estimates pooled attribute effects, not individual utilities. Numeric/categorical predictors are attributes here; respondent interactions/heterogeneity need a custom model.

Rating example:

```json
{
  "model": "conjoint-rating",
  "outcome": {"column": "rating"},
  "respondent": "respondent_id",
  "profile": "profile_id",
  "task": "task_id",
  "numeric": [],
  "categorical": {
    "delivery": {"levels": ["pickup", "delivery"], "reference": "pickup"},
    "price": {"levels": ["10", "15", "20"], "reference": "10"}
  },
  "missing": "error"
}
```

Ratings use OLS and respondent-cluster covariance. Confirm interval treatment and direction. For rankings, change model to `conjoint-rank`, outcome to the rank column, and add `"rank_direction":"1-is-best", "acknowledge_rank_approximation":true`. This restricted course approximation requires identical complete profile sets in each task, unique untied ranks 1..m, and consistent profile mappings. It converts rank to m+1-r and explicitly labels its equal-spacing OLS approximation. Use a suitable ranking model for partial/tied rankings or exact ranking likelihoods.

For choice tasks, use `model: "conjoint-choice"`, `outcome: {"column":"chosen","event":"1","non_event":"0"}`, respondent/task/profile IDs and explicit attributes. Every task needs at least two unique alternatives and exactly one chosen alternative. The model has no global intercept, verifies within-task identification, and uses conditional logit rather than independent binary row regression. Context/person-only effects are not identified without appropriate interactions.

Choice uncertainty uses a seeded bootstrap that resamples **respondents with all their tasks**. Set `bootstrap_reps` (20–2000, default 200). Fewer than 200 draws is flagged as a smoke test; final inference needs more draws/stability assessment appropriate to the project. At least 20 and 80% of requested draws must fit successfully; otherwise it fails. Report requested/successful/failed fits, clusters and convergence diagnostics. Percentile intervals are approximate; the runner does not produce cluster-bootstrap p-values. Low bootstrap failure alone does not establish statistical adequacy.

Categorical conjoint outputs include reference-coded coefficients, zero-centered point utilities and range-based attribute importance when all modeled attributes are categorical. Utility/importance uncertainty and scenario/WTP/market-share calculations are not implemented. If numeric attributes are present, the core reports their coefficients and categorical utility ranges but leaves overall importance percentages unavailable: it has no declared ranges for the numeric attributes. No hierarchical Bayes, mixed logit, MaxDiff or individual utilities are claimed.

## Review before delivering

Inspect the audit, actual outcome coding, reference levels, independent units, dropped counts, coefficient intervals and diagnostic charts. Investigate unexpected signs, sparse levels, influential cases or poor calibration. Explain model assumptions and sample limits in the student's findings report. Do not present this starter report as a completed substantive interpretation without reviewing the dataset and research question.

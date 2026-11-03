# Selectable Python analysis starters

Use only the template relevant to the student's requested step. “Pull results” uses `scripts/results.py fetch` and stops with the saved locations and an optional next-step question. It does not run these scripts. “Consider regression” calls for variable/design inspection and discussion, not automatically fitting every model.

`run_model.py` is an executable Python starter for the five supported core models. Copy/edit the matching JSON configuration using the actual export/codebook and research plan; supplied column names are examples, not guesses about the student's data. Run it with the analytics Python recorded by setup. `--skill-dir` selects a custom installation; otherwise it locates this repository or the standard installed skill.

```text
ANALYTICS_PYTHON assets/analysis/run_model.py --data /project/responses.csv --config /project/chosen-model.json --header-records 3 --out /project/new-analysis
```

The JSON examples select linear, binary logistic, rating conjoint, restricted rank OLS approximation, or conditional-logit choice conjoint. Wide Qualtrics conjoint exports often need a deliberate reshape to long respondent/task/profile rows using the actual profile design; do not guess that mapping or invent profile attributes. Consult the [runner reference](../../references/analytics-runner.md) for restrictions and diagnostics.

`custom_welch.py` is a separate executable starter for a specifically requested independent two-group Welch comparison. It requires explicit columns/group labels and optional respondent ID checking; it does not decide the question is suitable or infer independence. Extend/review this pattern for other requested methods with appropriate assumptions, validation and tests.

`run_mining.py` routes one explicitly selected configuration to `scripts/mining.py`:

| Configuration | Implemented task | Required preparation |
|---|---|---|
| [supervised.json](supervised.json) | One fixed binary/numeric predictor; regularized linear/logistic, tree, forest, kNN or small MLP | Audited target/features and declared train/test rows; appropriate group/time checks; binary event and threshold fixed before test use. |
| [segment.json](segment.json) | Numeric k-means with optional PCA | One unique unit per row, justified numeric representation, chosen k/component count; inspect profiles/stability rather than inventing personas. |
| [association-pairs.json](association-pairs.json) | Descriptive two-item support, directional confidence, lift and leverage | Observed 0/1 columns and a justified basket/response denominator; missing does not mean absent. |
| [customer-value.json](customer-value.json) | Finite discounted conditional-retention margin scenario | Explicit same-period retention, margin, timing and costs; assumptions are illustrative, not fitted consumer behavior. |

Run a selected task with `ANALYTICS_PYTHON assets/analysis/run_mining.py --data /project/audited.csv --config /project/selected-task.json --out /project/new-run`; omit `--data` for the value scenario. The optional `--header-records 3` reads a verified three-record Qualtrics header. Preserve explicit local preprocessing/reshaping and split assignments, and use the [data-science reference](../../references/data-science.md) and relevant [pattern](../../references/unsupervised-patterns.md)/[marketing](../../references/marketing-analytics.md) guidance. This is a deliberately selected starter, not AutoML or a full production evaluation system.

Outputs are local files, not uploads back into Qualtrics. Preserve raw exports, meaningful types, missing rules, IDs/coding, package versions and audit trail. Explain results and uncertainty in context. Ordinal/mixed models, full Apriori, recommender/forecast estimation, RFM processing, MaxDiff, hierarchical Bayes, WTP and market-share forecasts remain custom workflows. The fixed-model holdout starter supplies neither nested tuning nor inferential/prediction intervals.

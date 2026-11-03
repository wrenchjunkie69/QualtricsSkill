# Selectable Python analysis starters

Use only the template relevant to the student's requested step. “Pull results” uses `scripts/results.py fetch` and stops with the saved locations and an optional next-step question. It does not run these scripts. “Consider regression” calls for variable/design inspection and discussion, not automatically fitting every model.

`run_model.py` is an executable Python starter for the five supported core models. Copy/edit the matching JSON configuration using the actual export/codebook and research plan; supplied column names are examples, not guesses about the student's data. Run it with the analytics Python recorded by setup. `--skill-dir` selects a custom installation; otherwise it locates this repository or the standard installed skill.

```text
ANALYTICS_PYTHON assets/analysis/run_model.py --data /project/responses.csv --config /project/chosen-model.json --header-records 3 --out /project/new-analysis
```

The JSON examples select linear, binary logistic, rating conjoint, restricted rank OLS approximation, or conditional-logit choice conjoint. Wide Qualtrics conjoint exports often need a deliberate reshape to long respondent/task/profile rows using the actual profile design; do not guess that mapping or invent profile attributes. Consult the [runner reference](../../references/analytics-runner.md) for restrictions and diagnostics.

`custom_welch.py` is a separate executable starter for a specifically requested independent two-group Welch comparison. It requires explicit columns/group labels and optional respondent ID checking; it does not decide the question is suitable or infer independence. Extend/review this pattern for other requested methods with appropriate assumptions, validation and tests.

Outputs are local files, not uploads back into Qualtrics. Preserve raw exports, meaningful types, missing rules, IDs/coding, package versions and audit trail. Explain results and uncertainty in the student's context. No ordinal/mixed model, MaxDiff, hierarchical Bayes, WTP, market-share forecast or holdout validation is implemented by these core starters.

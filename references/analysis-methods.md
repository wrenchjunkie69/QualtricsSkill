# Analysis selection and student deliverables

Identify the research question, measurement scale, sampling unit and dependence structure before selecting a model. Distinguish confirmatory explanation, predictive performance, causal effects and exploratory discovery. Respect the course's specified approach while making approximations explicit.

## Method router

| Data/question | Candidate methods | Checks and outputs |
|---|---|---|
| Describe one variable | Frequencies/proportions, median/IQR, mean/SD where meaningful | Denominator, missingness, valid ranges, uncertainty appropriate to sampling |
| Two categorical variables | Cross-tab, chi-square; exact methods for sparse suitable tables | Expected counts, independent units, effect size/interval; multi-select options overlap |
| Two independent groups, numeric outcome | Welch t-test; robust/permutation approach where appropriate | Group distributions, effect/interval; rank tests do not generically test medians |
| Paired/repeated numeric outcomes | Paired t-test, suitable signed-rank/permutation methods, mixed/GEE models | Pairing IDs, change distribution, dependence and missing pairs |
| More than two groups | ANOVA/Welch ANOVA or appropriate generalized/mixed model | Planned contrasts, variance/shape, multiplicity; repeated groups need repeated models |
| Two numeric/ordered variables | Pearson for linear numeric association, Spearman/Kendall for appropriate ordered association | Scatterplot, ties/nonlinearity, uncertainty; correlation is not causal |
| Continuous outcome with predictors | Linear regression; GLM/robust/quantile model if warranted | Functional form, residual/influence diagnostics, heteroscedasticity, collinearity; coefficients/CI and fit |
| Binary outcome | Binary logistic regression | Declare event/reference; separation, convergence, calibration; odds ratios/CI and probability effects |
| Ordered outcome | Ordered logit/probit or justified alternatives | Declare order; proportional-odds/model assumptions; predicted category probabilities |
| Unordered outcome with >2 categories | Multinomial logistic or suitable classifier | Reference class, sparse classes, model assumptions; class probabilities and suitable validation |
| Counts or rates | Poisson/negative binomial, exposure offset as justified | Overdispersion, excess zeros, exposure definition, independent unit; rate ratios/CI |
| Bounded proportion, survival/time-to-event | Appropriate fractional/binomial/beta or survival model | Denominators, boundary values, censoring/truncation and link assumptions |
| Repeated respondents, classes/sites or waves | Mixed effects, GEE, cluster-aware inference; complex-survey methods for real designs | Unit/cluster counts and structure; row-independent SEs and random row splits can be wrong |
| Predict unseen responses | Regularized regression, trees/ensembles and other justified candidates | Baseline, grouped/time-aware nested validation, calibration and uncertainty; preprocessing inside folds |
| Multi-item scales | Reverse coding, reliability, EFA/CFA if justified | Content validity, item structure, missing-item rule; PCA, EFA and CFA answer different questions |
| Segment respondents | Carefully scaled clustering/latent classes; validate stability | Feature leakage, redundant items, sensitivity to k/scaling, external interpretation; no automatic causal segments |
| Open-ended answers | Qualitative coding/themes, transparent text/NLP summaries | Coding rubric, audit sample, multilingual context, deidentification and human checks; no fabricated quotes |
| Product trade-offs | Rating/rank/choice conjoint; MaxDiff separately | Read conjoint reference; design identifiability, task IDs, respondent dependence and holdouts |

Methods in this table are workflows an agent can implement with suitable libraries. The bundled runner implements only the explicitly listed core models in its reference; do not report every table entry as an automated built-in.

For predictive learning/validation, use [data science](data-science.md); for PCA, clusters, associations or recommendations use [unsupervised patterns](unsupervised-patterns.md); for customer value, RFM, campaign economics or marketing-response interpretation use [marketing analytics](marketing-analytics.md). Each distinguishes the additional selected Python starters from custom-method guidance. Match the student's inference, prediction or discovery objective instead of routing every dataset into regression.

## Data audit and preparation

Keep the raw export immutable. Record its hash, source/date, export options and codebook. Qualtrics CSV can have one or three header records; inspect before selecting parser options. A file extension or a numeric dtype does not identify the measurement scale. Retain stable response/participant IDs for deduplication and dependence checks, without exposing them needlessly in reports.

Review completion/response type, pilot/test/imported provenance, duplicate IDs, branching-induced missingness, suspicious timing and logic consistency. Apply prespecified quality rules with counts/reasons; do not remove inconvenient responses or equate fast completion with invalidity automatically. Missing, not applicable, skipped, refused, structural missing and a real zero may differ. State any complete-case, imputation, weighting or sensitivity decision and the resulting analytical N.

Check category levels/reference groups, ordinal order, multi-select coding, reverse-coded items, scales/units and impossible values. Treat IDs as identifiers. Avoid fitting label text as numbers or using arbitrary nominal codes as distances. Do not silently include a leakage variable, outcome-derived score or future behavior as a predictor. Keep training/test respondent groups and time order separate before learning any imputer, scaler, feature selector or tuning parameter.

## Model-specific reporting

- Linear: specify functional form/interactions and coding; report coefficient scale, CI, N, residual degrees of freedom, R-squared/adjusted R-squared when applicable, and residual/influence checks. Robust SEs do not fix nonlinearity, confounding or a misspecified mean model. Examine influential observations; do not auto-delete them.
- Logistic: identify which value is the event. Coefficients are log odds; exponentiation yields odds ratios, not risk ratios or a fixed probability change. Report confidence intervals, convergence/separation and event counts; interpret probabilities at meaningful covariate values. A default 0.5 classification threshold is not universally optimal. In-sample accuracy/AUC is not holdout validation; use calibration and class-appropriate precision/recall metrics when predicting.
- Multiple predictors: do not rank raw coefficients measured in different units as relative importance. Distinguish multicollinearity, confounding, interactions and intentional model comparisons. Avoid searching transformations/subgroups to minimize p-values; label exploration and address multiplicity.
- Repeated/weighted data: count independent people/units as well as rows, state the covariance/sampling method, and acknowledge limited independent clusters. Do not claim the runner's simple cluster covariance is a full complex-survey estimator.
- Prediction: use untouched test data or appropriate outer validation for performance. Tune/preprocess only inside training folds. For repeated survey tasks split by respondent; for temporal questions respect time. Report uncertainty and performance against a simple baseline, not just a best score.

## Reproducible student deliverables

Deliver only what the task needs; for a full project use a research/analysis plan, codebook, raw-data provenance, cleaning/exclusion audit, executable script/config plus package versions/seed, model tables/diagnostics, and a clear findings report. Keep tables with denominators/units/reference categories and charts with labeled axes and actual uncertainty. Explain the key equation and how to read one coefficient rather than pasting unexplained software output.

Separate a numerical result, its uncertainty, its substantive size, the business decision and the study's limits. Report non-significant results honestly; they are not proof of equality. Explain assumptions and sampling/causal limitations in context. Refer to the course rubric for formatting and required analyses. The student's report should distinguish observed sample findings, modeled scenarios and synthetic test data.

## Primary implementation references

- [statsmodels regression/discrete/count API](https://www.statsmodels.org/stable/api.html)
- [OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html), [Logit](https://www.statsmodels.org/stable/generated/statsmodels.discrete.discrete_model.Logit.html), [OrderedModel](https://www.statsmodels.org/stable/generated/statsmodels.miscmodels.ordinal_model.OrderedModel.html)
- [SciPy statistical tests](https://docs.scipy.org/doc/scipy/reference/stats.html)
- [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html) and [cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)
- [statsmodels fitting pitfalls](https://www.statsmodels.org/stable/pitfalls.html) and [SciPy linear programming](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html) for numerical/separation safeguards
- [Qualtrics Stats iQ regression](https://www.qualtrics.com/support/stats-iq/analyses/regression/): licensed product functionality, distinct from local analysis and the Public API.

# Conjoint planning, estimation and interpretation

Begin with the assignment/decision, target users, candidate attributes and feasible levels. Qualtrics collects tasks; analysis can run locally. The Public API's Conjoint Collaboration endpoint shares projects, not a general-purpose utility-estimation API. Do not confuse its existence or Sessions V2 rank-order support with a licensed conjoint product or editor-schema support.

## Choose the design before developing the survey

| Format | Observation/data shape | Estimation to consider |
|---|---|---|
| Profile ratings | Respondent/profile/task, attributes, rating with explicit direction | Part-worth regression if interval treatment is justified; ordinal/mixed models as appropriate |
| Full/partial profile rankings | Respondent/ranking task, profile attributes, rank and tie/partial flags | Rank-ordered logit/Plackett-Luce or other ranking model; OLS of preference scores only as an explicitly chosen course approximation |
| Choice-based conjoint | One row per alternative within respondent/task, attributes and chosen indicator | Conditional/multinomial choice models; heterogeneous/mixed/hierarchical models where supported |
| MaxDiff / best-worst | Set membership, respondent/task, best and worst choices | Best-worst-specific design and likelihood; not generic ratings or automatic reuse of a binary row model |

Identify what is ranked: attribute importance is not the same data as ranking full product profiles. Choosing one option is not a complete ranking. Distinguish a partial ranking, a skipped task and a tie. Do not treat rankings from one task as independent interval measurements without acknowledging the approximation.

## Attributes, candidate profiles and tasks

Use attributes respondents understand, with levels that are meaningful, distinct and actionable. Document level sources/assumptions and price units. Avoid overlapping constructs and impossible combinations. Consider a none/status-quo option where it matches the decision, with a deliberate model specification for it. Screens/constraints and dominance can affect identification; do not mechanically remove meaningful trade-offs.

Generate a full factorial candidate set when manageable; otherwise use a justified design approach. Check balance, coverage, correlations, parameter identifiability and respondent burden for any reduced design. A random subset is not automatically orthogonal, D-efficient or sufficient. Count parameters from actual coding (including interactions if planned), inspect rank of the resulting design and keep holdout tasks separate when validating. Estimate sample size by design-specific precision/power simulation and independent respondent counts; more task rows do not solve too few people.

For student projects, use the rubric's profile/task limits and rank direction. Do not silently substitute a remembered limit from another class or task. Record stable profile/alternative/task IDs, assignment/randomization order and the full attribute-to-level mapping. Pilot comprehension, burden, export linkage and task completeness before distribution.

## Data and coding checks

- Every profile ID must map consistently to its attribute levels. Every choice set must identify its respondent and task and contain the alternatives actually shown.
- For single-choice tasks require exactly one selected alternative per set; none can be a real alternative, while missing choices remain missing. For complete rankings require a valid permutation with the declared direction; use a ranking-specific method for ties/partial rankings.
- Dummy coding uses an explicit reference level and omits one level per categorical attribute. Effect coding imposes a different constraint; label it. Do not include a global intercept in conditional logit: group intercepts are conditioned out. Respondent characteristics constant within a choice set need appropriate interactions to be identifiable.
- Repeated responses need respondent-level inference and validation. Split held-out respondents/tasks in a way that matches the claimed prediction target; do not leak copies of the same person's tasks across an allegedly new-person test.

## Estimation and interpretation

The bundled runner fits categorical part-worth models for ratings, a restricted complete-ranking OLS approximation, and single-choice conditional logit. Read the runner's precise input restrictions. It does not implement MaxDiff, mixed/hierarchical Bayes, individual utilities or a general tied/partial-ranking likelihood. Use a suitable dedicated library/workflow for those cases and record its version and diagnostics.

For a classroom OLS ranking approximation, converting rank r among m profiles to m+1-r makes larger preference scores better. That does not make the rank spacing measured interval data; report that assumption and cluster inference by respondent. Do not describe the resulting coefficients as exact rank-likelihood estimates. A proper ranking model is preferable when the research question and resources warrant it.

For conditional logit, model utilities within the alternatives actually present in each task; explicitly check identifiability and the independence-of-irrelevant-alternatives/heterogeneity assumptions. Use respondent-aware uncertainty (the runner uses a seeded respondent bootstrap). Inspect convergence and report failed bootstrap fits. Avoid fitting ordinary independent binary logistic regression to each alternative row as a substitute for the choice likelihood.

Part-worths are relative to coding/constraints, not absolute value or directly comparable respondent utility scales. The runner supplies reference-coded coefficients and zero-centered point utilities. Attribute importance from utility ranges is conditional on the selected level ranges and model; it is not a universal psychological importance score. Compare importance across a common design, and report uncertainty where supported.

Willingness-to-pay ratios require an identified, appropriately scaled price utility and credible trade-off assumptions. A near-zero/positive or nonlinear price effect can make a ratio misleading; do not invent a single WTP figure from arbitrary price codes. Choice shares from utility simulations are model-based preference scenarios; they are not validated market shares, sales forecasts or causal demand estimates. Include the competing set, outside option, scale assumptions and holdout calibration where relevant.

## Primary references

- [statsmodels ConditionalLogit](https://www.statsmodels.org/stable/generated/statsmodels.discrete.conditional_models.ConditionalLogit.html)
- [PlackettLuce package overview](https://cran.r-project.org/web/packages/PlackettLuce/vignettes/Overview.html) for ranking models including partial rankings/ties
- [Qualtrics rank-order questions](https://www.qualtrics.com/support/survey-platform/survey-module/editing-questions/question-types-guide/standard-content/rank-order/)
- [NIST design of experiments](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)

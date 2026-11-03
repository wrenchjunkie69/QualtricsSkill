# Student research and survey planning

Produce a plan proportional to the task. Read the assignment/rubric and any existing project decision log first. Preserve required methods and deliverables; explain when a required classroom approximation differs from a stronger research method. Ask only for missing choices that materially affect the study; continue independent planning while those are pending.

## Start from a decision, not a questionnaire

Record: business/research decision; target population and sampling frame; research question; primary outcome and time frame; explanatory/predictive/causal objective; hypotheses/contrasts; unit of observation and independent sampling unit; proposed method; needed variables; collection and analysis deliverables. State which elements are fixed by the assignment and which are assumptions.

For each variable specify construct, wording, type/scale, units, answer options or valid range, source, timing, analytical role, export tag, missing/skip codes, coding/reference level and intended transformation. Separate outcome, predictor, prespecified confounder, moderator, mediator, ID and quality-control fields. Do not casually adjust for a mediator when estimating a total treatment effect.

## Study and survey types

| Goal | Design to consider | Measure/collect | Analysis implications |
|---|---|---|---|
| Discover motivations or language | Interviews, open-ended pilot, exploratory survey | Detailed text and context | Qualitative codebook and themes before closed-ended testing |
| Describe awareness, usage or satisfaction | Cross-sectional descriptive survey | Defined denominator, behavior/time frame, demographics only as useful | Frequencies, distributions, uncertainty and sampling limitations |
| Explain satisfaction/purchase drivers | Observational explanatory survey | Outcome, theory-driven predictors and credible confounders | Regression matched to outcome type; associations with diagnostics |
| Compare messages, prices or concepts causally | Randomized between-person experiment, possibly blocked | Assignment, exposure, primary outcome, compliance/attrition | Prespecified contrasts; analyze assignment appropriately; randomization unit determines inference |
| Measure change | Panel/longitudinal or paired pre/post | Stable respondent ID and time/wave | Paired methods, mixed models/GEE, attrition; pre/post without a control has causal limits |
| Measure trade-offs | Rating/rank conjoint or choice experiment | Attributes, levels, feasible profiles, tasks, choice/rank/rating and respondent ID | Different likelihoods/design requirements; read conjoint reference |
| Prioritize items | Ranking, allocation, or best-worst/MaxDiff | Explicit instruction and task membership | Rankings, compositional totals and best-worst tasks are not interchangeable scales |
| Find segments | Attitudes/needs/behavior survey | Comparable validated features, sufficient variation | Scale preparation, clustering stability and external descriptions; segments are exploratory |
| Study price sensitivity | Direct WTP, price experiment, PSM, Gabor-Granger or conjoint | Method-specific questions and assumptions | Do not mix methods or infer actual demand from stated intention alone |

## Match the question format to the measurement

- Single-select categories: mutually exclusive, collectively sufficient options with a relevant other/none/prefer-not-to-answer when appropriate. Multi-select: represent each option separately in analysis; denominators and overlap must be explicit.
- Counts/amounts: specify currency, units, time frame, zero and sensible ranges. Do not collect a range if the planned continuous model needs precise amounts without documenting an approximation.
- Likert item: an ordered response, not automatically an interval scale. A multi-item construct needs justified item selection, reverse-coding rules and a composite/latent-variable plan. Reliability alone does not establish validity.
- Rating scale: label endpoints consistently and establish direction. Rank order: distinguish full versus partial ranking, ties, and whether 1 means best. Ranking every item forces trade-offs and is not a set of independent ratings.
- Matrices: limit respondent burden and pilot mobile rendering/accessibility. A matrix is a UI container, not proof that its items form one construct. Use short, neutral wording, one idea at a time, and a precise recall window.
- Experiments: preserve random assignment in exported metadata. Avoid unplanned unequal exposure, carryover, order effects and post-treatment selection. Within-person tasks need counterbalancing and a repeated-measures analysis.
- Embedded fields: store assignment/task/profile IDs and non-sensitive linkage needed for analysis. Keep direct identifiers separate from analytical data where practical. Do not collect unnecessary sensitive details.

## Sampling, precision and power

Distinguish population, reachable frame, recruited sample and completed analytical sample. A convenience sample is not made representative by quotas or a large row count. Report recruitment/nonresponse/coverage limits. Explain stratification, cluster sampling and weights only if there is a real sampling design; ordinary row weights do not automatically reproduce complex-survey inference.

Plan sample size from a meaningful effect or desired precision, alpha, power, outcome distribution/base rate, number of parameters, assignment ratio, clustering, repeated measures and expected exclusions. Use a method-specific calculation or simulation with sensitivity ranges. Do not present a universal respondents-per-question, ten-events rule, or conjoint rule of thumb as a guarantee. Profile/task rows from one respondent do not create additional independent respondents.

For an already fixed class sample, report achievable precision/power scenarios and simplify the model if needed; do not use observed-effect post-hoc power as proof of no effect. Distinguish effect size, confidence interval and statistical significance. Small samples may support exploratory descriptive work rather than a complex model.

## Analysis-first instrument checklist

Prepare a compact `research-plan.md` and `codebook.csv` when the project is substantial. The plan should connect every main research question to its outcome, predictors, test/model, planned contrast and report. Identify primary versus exploratory analyses, missing/exclusion rules, multiple-comparison handling, intended respondent-level grouping and any holdout/validation scheme before looking for favorable results.

Pilot wording and comprehension with relevant people, test every branch and randomization path, verify export tags/codes and task/profile linkage, check required versus optional items, and inspect a test export. Keep pilot/test records distinguishable from the intended research sample. For a live survey, use the API workflow to create a reviewable draft and verify the definition; publication/distribution still depend on the user's requested scope.

## Primary references

- [Qualtrics question types](https://www.qualtrics.com/support/survey-platform/survey-module/editing-questions/question-types-guide/question-types-overview/)
- [Qualtrics survey accessibility](https://www.qualtrics.com/support/survey-platform/survey-module/survey-tools/check-survey-accessibility/)
- [statsmodels power calculations](https://www.statsmodels.org/stable/stats.html#power-and-sample-size-calculations)
- [NIST experimental design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)

# Student research and survey planning

Produce a plan proportional to the task. Read the assignment/rubric and any existing project decision log first. Preserve required methods and deliverables; explain when a required classroom approximation differs from a stronger research method. Ask only for missing choices that materially affect the study; continue independent planning while those are pending.

## Define what the study needs to resolve

Separate the observed symptom or opportunity, the decision someone can make, and the uncertainty research can reduce. Falling repeat visits might reflect access, price, service, a changed customer mix or a recording problem; do not build the questionnaire around a favored explanation as though it were established. Identify feasible actions and what evidence would distinguish them. Ask about decision stakes, timing and available information when they affect the design.

Research may not be the next useful action if adequate information already exists, no feasible decision depends on it, or a new collection cannot finish in time. Inspect supplied records, prior studies, support themes or operational data when relevant and authorized. Evaluate existing information for purpose, population, definitions, timing, collection method, missingness and consistency; availability alone does not make it fit the question.

Keep these levels distinct:

| Level | Purpose | Example: a bicycle repair service |
|---|---|---|
| Decision | Action the organization might take | Decide whether to change appointment availability or the booking process. |
| Research question | Evidence needed to inform that choice | Among people who started booking in the last 30 days, how do reported obstacles differ between those who completed and abandoned their most recent attempt? |
| Construct/variable | Precisely defined thing to measure | Most recent booking outcome, availability of a suitable slot, clarity of the booking steps. |
| Respondent item | Question a person can answer | "When you most recently tried to book in the past 30 days, were any available appointment times suitable for you?" Include a truthful cannot-recall route. |
| Analysis/decision use | How evidence will be interpreted | Describe obstacles by reported outcome; triangulate with available booking records. Association alone does not establish that changing a slot will increase bookings. |

Research questions should specify a relevant population, the phenomenon or comparison, context/time window and what the answer would change. Avoid questions too broad to measure, questions that assume the desired result, and wording that confuses a recommended action with a measured fact. Split a broad question into a few answerable objectives rather than a long list of unrelated items. Descriptive/exploratory work need not have a directional hypothesis; a confirmatory test needs its hypothesis, contrast and primary outcome specified before inspecting favorable results.

Record the independent sampling unit, unit of observation, proposed design and deliverable. Mark known facts, course requirements, assumptions and unresolved choices separately. Use the optional [research brief](../assets/research/research-brief.md) when a substantial plan is requested; a short conversation may be enough for a narrow question.

## Study and survey types

Choose a design for the information gap, not for the software available. Exploration develops understanding or candidate explanations; descriptive work estimates patterns; a causal design addresses the effect of an intervention under explicit identification assumptions. These can be combined in stages, but proposing a later stage does not authorize executing it.

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

Apply the router to varied goals:

- **Awareness and positioning:** identify the category/market, unaided versus aided measures, familiarity and intended comparisons. Ask unaided questions before showing brand names; account for branding/exposure in recruitment and disclosure too. An image profile among aware respondents is not an awareness estimate among everyone.
- **Retention or service improvement:** distinguish behavior, perceived experience, intentions and operational outcomes. Include lapsed/nonusers when the question concerns them rather than sampling only current enthusiastic users. A satisfaction association is not automatically an intervention priority.
- **Concept, packaging or communication evaluation:** decide whether each person sees one concept or several; hold irrelevant content comparable, address order/carryover and record assignment. Keep concept ratings separate from observed purchasing.
- **Market opportunity or segmentation:** define need, eligible demand and reachable population. Qualitative themes can suggest survey content; demographic differences alone do not prove useful segments. Evaluate whether segment differences are substantial, sufficiently stable and actionable as well as uncertain.
- **Tracking and change:** distinguish repeated cross-sections from the same-person panel. Preserve wording/coding or document breaks in comparability; attrition and a changing sample can mimic change.

For exploration, an interview or discussion guide should use neutral opening questions, probes for concrete episodes, recruitment criteria and a transparent coding plan. Observation can address enacted behavior that people recall poorly but cannot directly reveal motives. Do not estimate population prevalence from a handful of interviews, count multiple quotes as independent people, or invent participant quotes. A mixed-method plan should explain how the strands inform or check one another.

## Translate objectives into measurable information

Use [questionnaire design](questionnaire-design.md) to choose items, response formats and flow. For each main research question specify the needed constructs/outcomes, comparison, eligible respondents, time window and analysis. Cover each objective; remove items with no decision, routing, measurement or necessary quality purpose. Do not include demographics simply because surveys usually have them.

For each variable specify construct, wording, type/scale, units, answer options/range, timing, analytical role, export tag, missing/skip codes and coding/reference level. Separate outcome, predictor, prespecified confounder, moderator, mediator, ID and quality-control fields. Do not casually adjust for a mediator when estimating a total treatment effect. An item is not a validated scale merely because its wording sounds plausible.

Experiments need a declared assignment unit, treatment/control, comparable exposure, outcome, timing and intended contrast. Preserve assignment and task IDs in the export; distinguish assigned from received exposure. Avoid confounded concept versions, post-treatment exclusions and changes to the primary outcome after seeing results. Within-person tasks need an order/carryover plan and dependent-data analysis. A simple before/after comparison without an appropriate control does not isolate an effect; a nonrandom control requires additional assumptions too.

Select self-administered online, interviewer-assisted or mixed collection for reach, burden, access needs, sensitivity and available resources. No mode is automatically the highest quality. Interviewers need consistent instructions/probes; mixed modes can change how questions are understood and answered. A panel is a recruitment source, not proof of probability sampling. Do not buy sample, contact participants or start distribution as a side effect of planning.

## Sampling, precision and power

Distinguish population, reachable frame, recruited sample and completed analytical sample. A convenience sample is not made representative by quotas or a large row count. Report recruitment/nonresponse/coverage limits. Explain stratification, cluster sampling and weights only if there is a real sampling design; ordinary row weights do not automatically reproduce complex-survey inference.

Specify whom the study includes/excludes, how participants are reached/selected, selection probabilities if known, and any planned subgroup sizes. Simple random selection requires an appropriate frame; systematic selection needs a random start and a check for list periodicity; strata and clusters have different selection/inference roles. Quotas, purposive and referral recruitment have useful contexts but do not establish known selection probabilities. Random assignment within a convenience sample and random selection from a population solve different problems.

Plan sample size from a meaningful effect or desired precision, alpha, power, outcome distribution/base rate, number of parameters, assignment ratio, clustering, repeated measures and expected exclusions. Use a method-specific calculation or simulation with sensitivity ranges. Do not present a universal respondents-per-question, ten-events rule, or conjoint rule of thumb as a guarantee. Profile/task rows from one respondent do not create additional independent respondents.

For an already fixed class sample, report achievable precision/power scenarios and simplify the model if needed; do not use observed-effect post-hoc power as proof of no effect. Distinguish effect size, confidence interval and statistical significance. Small samples may support exploratory descriptive work rather than a complex model.

A simple-random-sample margin of error concerns sampling variation under its assumptions; it does not include coverage, nonresponse, wording, handling or interpretation errors. Do not apply a conventional probability-sample margin of error to an opt-in link without a justified inferential model. Finite-population correction, design effects, recruitment eligibility/completion and subgroup requirements belong in an appropriate sample-size calculation. A census removes sampling variation from selection, not measurement/nonresponse error.

## Analysis-first instrument checklist

Prepare a compact `research-plan.md` and `codebook.csv` when the project is substantial. The plan should connect every main research question to its outcome, predictors, test/model, planned contrast and report. Identify primary versus exploratory analyses, missing/exclusion rules, multiple-comparison handling, intended respondent-level grouping and any holdout/validation scheme before looking for favorable results.

Define collection dispositions and analysis eligibility: invited/reached, known/unknown eligibility, screened out, started, partial, completed, duplicate/test and included in a particular analysis. Platform completion is not proof that all research measures are valid. Report a rate's numerator/denominator and any unknowns; an open-link export often cannot establish a response rate because the eligible invited denominator is unavailable. A high completion rate alone does not rule out nonresponse bias.

Pilot comprehension with relevant people, test branches/randomization, verify export tags/codes and task/profile linkage, and inspect a test export. Separate human comprehension, programmatic definition checks and retained-data verification; they establish different things. Keep pilot/test records distinguishable from the intended sample. Use the [pilot plan](../assets/research/pilot-plan.md) for a substantial instrument. A live draft is verified through the API; publication/distribution still depend on the user's requested scope.

## Primary references

- [Qualtrics question types](https://www.qualtrics.com/support/survey-platform/survey-module/editing-questions/question-types-guide/question-types-overview/)
- [Qualtrics survey accessibility](https://www.qualtrics.com/support/survey-platform/survey-module/survey-tools/check-survey-accessibility/)
- [statsmodels power calculations](https://www.statsmodels.org/stable/stats.html#power-and-sample-size-calculations)
- [NIST experimental design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)

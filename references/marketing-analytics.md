# Marketing decisions and analytical meaning

Use the relevant portion for the student's requested decision. Use [research planning](research-planning.md) for the evidence gap, [data science](data-science.md) for prediction and [conjoint](conjoint.md) for designed trade-offs. Statistical performance, measured behavior, business value and causal impact are distinct claims.

## Customer outcomes and campaign evaluation

Define acquisition, activation, repeat use, renewal, churn, retention and value with eligible denominators and time windows. Distinguish people, accounts, orders and revenue. Revenue retention differs from customer retention; someone inactive in a noncontractual business is not necessarily permanently churned. A satisfaction/intention survey may help explain experience but does not by itself supply transaction histories or future cash flows. Authorized linkage to behavioral data requires consistent IDs, timing and handling.

Report conversion rates with exposure/eligibility counts, not just totals; compare relevant cohorts and follow-up windows. Growth in customer counts can coexist with a worse retention rate when the base changes. Distinguish percentage-point changes from relative percentage changes. A response propensity is not incremental lift: customers likely to buy anyway can score highly. Attributed revenue and ROAS are not automatically incremental profit or ROI. Include costs, margin, cannibalization and the counterfactual appropriate to the question.

For a randomized campaign/concept test, specify assignment unit, primary outcome/contrast, exposure, timing, attrition and analysis population. Factorial designs can estimate interactions when supported by replication/design; an overall main effect can conceal important treatment combinations. Choose independent, paired/repeated, cluster-aware or appropriate generalized methods for the outcome/design. One-way ANOVA does not identify every differing pair without appropriate contrasts; use multiplicity control for the comparisons actually made. Matching or an uncontrolled before/after comparison does not automatically reproduce randomization.

Useful differences need practical magnitude, uncertainty, credible stability and an actionable decision, rather than a p-value alone. Interpret prespecified estimates and intervals even when not significant; do not declare equality or discard an effect solely because a cutoff was not crossed. A technically well-fitted model can still be too costly or too uncertain to support the proposed action.

## Marketing response, coding and elasticity

For demand/marketing-response work, define units, price/promotion/exposure, distribution, competitor/context variables and relevant lags. Consider seasonality, simultaneous decisions, omitted confounders, carryover and repeated units. Observational marketing-mix regression is not automatically a causal budget allocator. Large coefficients do not establish incremental returns, and a forecast outside the observed price/segment range needs qualification.

For a meaningful positive quantity Q and price/input P, local elasticity is (dQ/dP)*(P/Q). In a level-level linear model it varies with the evaluation point; in a correctly specified log-log model the relevant coefficient is an elasticity, with interactions/nonlinearity changing the derivative. Report the model, evaluation values, uncertainty and identification limits. Ratio-style elasticity is often not meaningful for arbitrary-origin Likert attitude codes. Log transformations require a plan for zero/negative values; do not silently add a constant to obtain a desired result.

Declare categorical levels/reference and interaction coding. With an interaction, the effect of one predictor depends on the other's value; retain appropriate lower-order terms and interpret conditional effects, not just isolated main-effect coefficients. Correlated predictors can make estimates unstable; high pairwise correlation alone does not identify which adjustment variable can be removed without changing the question. Predictive feature selection and causal adjustment require different reasoning.

## Customer lifetime value and explicit scenarios

Separate historical customer revenue/profit from forward-looking expected value. Specify current customer versus prospect, contractual versus repeat-purchase setting, cohort/tenure, margin rather than sales, time horizon, conditional retention/survival, cash-flow timing, discount period and acquisition/retention costs. Initial cash flow, future margins and acquisition cost must each be counted once. Align monthly/annual rates by an appropriate conversion; an annual effective discount rate is not generally divided by 12 to produce an equivalent monthly rate.

For an explicit finite scenario with conditional retention r[t], survival through t is the product of r[1]...r[t]. With end-of-period margin m[t] conditional on survival, present value is:

```text
initial_margin - acquisition_cost
    + sum( survival[t] * margin[t] / (1 + discount_rate)**t, t=1..horizon )
```

The `customer_value` task implements exactly this scenario and saves a cash-flow ledger. The example [configuration](../assets/analysis/customer-value.json) uses invented assumptions solely as a starter. It estimates no retention behavior, returns no statistical uncertainty, assumes no reactivation and adds no terminal value. A forecast/estimated CLV needs suitable behavioral data, validated survival/purchase/margin models and uncertainty/sensitivity work. Do not call a finite three-period scenario observed lifetime value.

Constant-margin infinite formulas depend on whether the next margin is received now or only after a renewal; do not mix timing conventions. Inactivity in a repeat-purchase setting can require a different model from permanent contractual churn. Cohort comparisons need comparable tenure and an explicit treatment of censoring. Changing an assumed retention rate shows scenario sensitivity, not a measured causal effect of a proposed intervention. The increase in customer asset value is not the same as a one-period profit increase.

When considering acquisition, distinguish spending per prospect from spending per acquired customer and an incremental conversion rate from an observed one. A simple expected-value threshold depends on calibrated outcomes, margin/cost and what would happen without the action. Budget/capacity/risk constraints and uncertain long-run assumptions matter. Do not initiate real spending, contact campaigns or account changes from a value calculation alone.

## RFM, cohorts and marketing segments

For RFM define the as-of date and eligible history, customer/order IDs, treatment of returns/cancellations, currency, and whether monetary value is revenue or margin. Recency is time since the last eligible purchase; frequency is a stated count/rate of distinct purchases; monetary value uses the specified window/basis. Aggregate line items to the intended transaction before counting orders. Do not treat a multiple-response survey answer as an order ledger.

Retain raw R/F/M values before optional bins/scores. Set direction explicitly (smaller recency is more recent); handle ties, zero-history/new customers and tenure fairly. Quantile bins can collapse with ties and do not guarantee five distinct meaningful groups. Finer cells may become sparse; a cell's fitted response rate is not honest future performance. Freeze scoring/threshold choices using development data and validate later outcomes without look-ahead.

RFM is a descriptive/scoring representation, not automatically a causal targeting or CLV model. A high-spend segment need not be profitable or persuadable. Combine observed profiles with serving costs, reach, stability and experimental evidence where the decision requires it. RFM/cohort processing, demand estimation, factorial/mixed experiments and budget optimization are custom workflows, not additional commands hidden in the starter.

# Prediction and data-science execution

Use for a requested predictive analysis, validation plan or data-mining task. For inferential regression/conjoint use [analysis methods](analysis-methods.md) and [the inference runner](analytics-runner.md). For segments/patterns use [unsupervised methods](unsupervised-patterns.md); for customer value and marketing decisions use [marketing analytics](marketing-analytics.md). Reading these references does not request that every method be run.

## Define a task that can be evaluated

Translate the business question into a target, observation/independent unit, prediction moment, outcome horizon, available inputs and intended decision. Classification predicts a class/probability; regression predicts a quantity; clustering describes similarity without a target; association rules describe co-occurrence. A recommendation ranks eligible items for a user/context, and forecasting predicts later periods. Choose the objective and evidence before choosing an algorithm.

For a substantial requested analysis, the optional [analysis plan](../assets/research/analysis-plan.md) records those choices and validation assumptions. A small task can use a concise explanation instead of a separate document.

Distinguish description, explanation, prediction and intervention effects. A model can predict an outcome well using variables that are not actionable or causal. A churn score does not identify who will benefit from an offer. That latter question needs an appropriate experiment or causal/uplift design. Do not prescribe real campaigns, spending or respondent actions merely because an analysis is complete.

Inspect column meanings, units, ranges, missing states, time windows and how rows were generated. Preserve the raw export and record changes. An ID/ZIP code is not a continuous quantity; multiple task rows are not additional independent people. Use plots and conditional summaries to understand distributions/nonlinearity, with honest axes and denominators. Do not delete unusual but valid observations to improve a score. Target-informed exploration, feature selection and learned cleaning belong in the training/model-development stage.

## Separate development from evaluation

Choose validation for the generalization claim. Independent future respondents can use suitable randomized partitions, often stratified for classification. Repeated people/households/sites need a split respecting the relevant group; a forecast needs later periods held out. A random row split can answer the wrong question. Predicting later behavior of known customers differs from predicting new customers; specify which claim is intended. Grouping and time restrictions may both be necessary.

Keep an untouched test set for the final chosen procedure, or use an outer validation loop. Tune features, models, hyperparameters, probability calibration and decision thresholds inside development data, using appropriate inner splits. Use the same outer splits for fair candidate comparisons. Do not repeatedly consult the test score and still call it untouched. Cross-validation fold variability is not automatically a confidence interval; uncertainty/resampling must respect the sampling unit and time dependence. Small independent samples can make elaborate searches less credible than a simple baseline.

Fit imputation, scaling, encoding, feature selection, resampling and PCA on each training fold only, then transform its validation data. Use a fitted [pipeline](https://scikit-learn.org/stable/common_pitfalls.html) and [appropriate splitters](https://scikit-learn.org/stable/modules/cross_validation.html). Never normalize the full dataset before a predictive split or oversample before cross-validation. Document structural missingness and the limits of simple imputation. Missing targets must not become a guessed negative class.

Check feature availability at the prediction moment. Future spending, cancellation dates, outcome-derived aggregates and data updated after the event can leak the answer. Features built from histories need an explicit as-of cutoff. A model trained on selected survey completers may not generalize to nonrespondents. Holdout validation does not cure nonprobability sampling or distribution shift.

## Select an algorithm deliberately

| Candidate | Useful role | Decisions/checks |
|---|---|---|
| Linear/ridge regression | Transparent numeric baseline with optional shrinkage | Coding, scale, functional form, residuals and regularization; predictive shrinkage estimates do not provide the inference runner's p-values. |
| Logistic classifier | Binary probabilities and a useful baseline | Event coding, regularization, calibration and threshold. This models a conditional probability, not a literal log-transform of observed 0/1 outcomes. |
| Decision tree | Interpretable nonlinear splits/interactions | Depth, leaf size and pruning selected within development. Training Gini/entropy reduction is not out-of-sample accuracy. Trees have assumptions/limitations too. |
| Random forest | Nonlinear ensemble comparison where justified | Complexity, correlated predictors, probability quality and resource cost. Impurity importance can favor certain feature types and is not causal importance. |
| k-nearest neighbors | Local similarity-based classification/regression | Scale/encoding/distance, neighbor count, ties/weighting, dimensionality and prediction cost. Number of neighbors and number of CV folds are different parameters. |
| Small multilayer perceptron | A nonlinear candidate when data supports it | Scaling, architecture, regularization, convergence, seeds and complexity. Larger/deeper is not automatically better; convergence is not proof of global optimality or generalization. |

No algorithm wins universally. Treat near-equal scores in light of uncertainty, simplicity, interpretability, maintenance and decision cost. Univariate correlation screening can discard an important interaction/nonlinear predictor or a needed adjustment variable. Avoid automatic stepwise/p-value fishing. A statistical association or model feature importance is not a causal lever.

## Report metrics in the decision's terms

For numeric outcomes report MAE/RMSE in target units and a baseline evaluated on the same rows/horizon. Test R-squared can be negative; high training R-squared does not validate forecasts. Inspect residual patterns and error in relevant subgroups; percentage errors can be meaningless near zero. A point prediction and its prediction interval are different outputs.

For binary outcomes name the positive event, threshold, actual/predicted axes and TP/FP/TN/FN. Precision is TP/(TP+FP), recall/sensitivity TP/(TP+FN), specificity TN/(TN+FP). State undefined denominators. Accuracy alone can hide class imbalance. ROC AUC concerns ranking across positive/negative pairs; it is not the fraction of individual cases correctly classified. Average precision and a precision-recall area are not identical computations. Report prevalence, useful [classification/probability metrics](https://scikit-learn.org/stable/modules/model_evaluation.html) and probability quality such as log loss/Brier alongside decision metrics. A Brier score alone is not a complete calibration analysis.

Choose a threshold for prespecified costs, benefits/capacity or another justified objective using development data. F1 gives a particular precision/recall trade-off; it is not universally the profit-maximizing threshold. Compare probability models to a training-prevalence baseline and decision rules to relevant operational baselines. Multiclass tasks need class ordering, per-class metrics and explicit averaging; do not silently reduce them to binary.

## Optional executable starter

`scripts/mining.py` runs **one** explicitly configured task, without API calls or data retrieval. Use the installed analytics interpreter and a copied/edited [configuration](../assets/analysis/README.md):

```text
ANALYTICS_PYTHON scripts/mining.py --data /project/audited.csv --config /project/selected-task.json --out /project/new-run
```

For `task: supervised`, the dataset must already have a partition column containing exactly `train` and `test`. Prepare these assignments with a justified split and save them; the starter does not invent an 80/20 split, tune models or perform nested cross-validation. Pass a group column to enforce disjoint groups, a time column to enforce every training timestamp preceding every test timestamp, or explicitly acknowledge independent rows. A time-only split may legitimately reuse known people when that matches the stated future-prediction objective; it is not evidence of new-person performance.

Time parsing normalizes offsets to UTC and treats timezone-naive values as UTC; convert intended local timestamps before use. Parsed missing times (including textual `NaT`) are rejected. The chronology guard alone does not account for delayed labels, overlapping outcome windows or a necessary embargo/gap; those belong in the prepared partition design.

Declare numeric/categorical features, target, problem (`binary` or `regression`), one algorithm (`linear`, `tree`, `forest`, `knn`, `mlp`) and supported fixed parameters. Binary work requires a positive-event label and fixed threshold. `linear` means regularized logistic classification or ridge regression here. Target/partition/group/time fields cannot be input features. All-missing training features and unknown target classes fail; unseen test predictor categories are encoded without learning them and counted. Blank values remain missing even with additional declared missing codes. Preprocessing is fitted only to training rows.

The starter reports held-out predictions, model and training-prior/mean baseline metrics, missingness, unknown predictor levels, configuration and source hashes/package versions. Its metrics are row-weighted even with groups; it supplies neither cluster-aware uncertainty nor complex-survey estimates, calibrated probabilities, confidence/prediction intervals, multiclass handling or a deployment artifact. It cannot infer undeclared dependence or prove semantic absence of leakage. Use an appropriate custom workflow for those needs rather than claiming they happened. It does not replace the inferential regression/conjoint runner.

## Time-series and anomaly workflows

For a requested forecast, define the series/entity, frequency, horizon and origin; distinguish missing periods from true zero activity. Plot trend/seasonality and check history length, structural breaks and changing measurement. Compare naive/seasonal-naive forecasts with appropriate exponential smoothing, ARIMA/SARIMA or justified feature-based models. Create lag/rolling features using only information available at each origin; exogenous future inputs must be known or explicitly scenario-based. Evaluate with chronological rolling origins, comparable horizons and suitable intervals; never shuffle dates for a future-performance claim.

ARIMA differencing, deterministic trend and seasonal structure are modeling choices. An ADF rejection concerns a unit-root null under its specification; failure to reject is not proof of all forms of nonstationarity, and rejection is not proof of constant variance. Avoid differencing the series manually and then specifying the same differencing again without an intentional reason. A rolling mean is distinct from ARIMA's moving-average error component. Two-standard-deviation bands are not automatically calibrated 95% forecast intervals. Time-series estimation is a custom workflow, not a command in this starter; use current [statsmodels time-series documentation](https://www.statsmodels.org/stable/tsa.html).

Anomaly detection produces unusualness scores relative to a reference, not proof of fraud, invalid survey responses or misconduct. Set thresholds using appropriate labels/validation and review capacity, inspect false alarms and drift, and preserve the evidence. Outlier flags alone do not authorize deletion of respondent data. Keep the student's requested analysis and any later operational action separate.

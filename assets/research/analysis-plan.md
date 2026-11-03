# Selected analysis and validation plan

Use the fields relevant to the requested analysis, not as a required intake for an export or small calculation. Record decisions before searching for favorable results; distinguish prespecified work from exploration.

- Research/decision question and requested deliverable:
- Objective: description, inference, prediction, segmentation/pattern discovery or explicit scenario:
- Dataset origin, raw-file version/hash and codebook:
- Eligible analytical sample, row meaning, independent unit and repeated/group/time structure:
- Outcome/event, timing/horizon, scale and meaningful effect or error:
- Predictor/features and why each is available at the relevant time; fields excluded as identifiers/leakage:
- Missing/skip codes, quality exclusions, transformations and scoring rules:
- Selected method, coding/reference levels and fixed parameters or prespecified tuning scope:
- Baseline and evaluation metrics, with decision costs/capacity where relevant:
- Training/development/test assignment location and rationale; group/time/overlapping-window safeguards:
- Which preprocessing/selection/calibration steps are learned inside each training split:
- Threshold choice and data used to choose it; untouched test or outer evaluation:
- Uncertainty, sensitivity/stability checks and any subgroup/multiple-comparison plan:
- For scenarios: units, horizon, cash-flow/event timing and the source/status of each assumption:
- Outputs to save, reproducibility settings and limits on interpretation:

For exploratory segmentation, replace predictive partitions with appropriate stability/replication checks and separate defining from profiling variables. For forecasting, record origins/horizons, frequency, future-input availability and naive baselines. For a small deterministic scenario, show the calculation and sensitivity rather than inventing inferential statistics.

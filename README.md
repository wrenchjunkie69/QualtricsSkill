# Qualtrics Agent Skill

**Build a survey with a purpose. Make sense of the answers.**

Your project starts with something you want to understand: why people leave, what customers value, which concept works better, or what a business should investigate next. The choices you make about questions, measurement and sampling shape what you can learn from the results.

Qualtrics Agent Skill gives your AI a practical research toolbox: study planning, survey development, Qualtrics API tools and reproducible Python analysis. Use it to produce work you can inspect, rerun and explain, whether you need help with one question or a larger research project.

For **students in marketing, research, analytics and data mining**, using **Codex, Claude Code or another compatible terminal-enabled AI agent**.

[![Validate portable skill](https://github.com/wrenchjunkie69/QualtricsSkill/actions/workflows/ci.yml/badge.svg)](https://github.com/wrenchjunkie69/QualtricsSkill/actions/workflows/ci.yml) · [MIT license](LICENSE) · API first · Local Python analysis

## Start here: give this link to your AI

Copy this into your AI agent:

```text
Read the README and SKILL.md at https://github.com/wrenchjunkie69/QualtricsSkill.
Inspect the setup scripts, install the skill for my AI app, and prepare the isolated
Python analytics environment. Run the installation checks and dependency doctor.
If I need Qualtrics account access, guide me through private local API-key setup
and verify connectivity. Report the installed paths and verification results,
then wait for my research task.
```

Your agent checks the tools, installs the skill and verifies the environment. You can then describe the research task in ordinary language. A local terminal/filesystem is required for installation; a browser-only conversation cannot install software on your computer just by reading the link.

**Already installed?** Start with [a student task](#what-you-can-do-with-it). **Installing or maintaining it?** Go to [AI installation instructions](#for-ai-agents-installation-and-first-use), [private key setup](#connect-your-qualtrics-account) or [verification](#verification-and-updates).

## What you can do with it

Start at the point that matches your project. Each request can stand on its own.

| Where you are | How the skill helps | What you can leave with |
|---|---|---|
| **You have a topic, but the research question is vague** | Clarify the decision, competing explanations, target population and information needed. Choose exploratory, descriptive, experimental or mixed methods. | Focused research questions and a study plan you can justify. |
| **You need a questionnaire people can answer** | Connect objectives to measures; choose formats/scales, improve wording, plan screening, branching, order and a pilot. | A questionnaire, question blueprint, codebook and logic specification. |
| **You want the survey built in Qualtrics** | Create or revise the requested draft through documented APIs, preserve relevant IDs/codes and verify the definition. | A reviewable survey draft with a record of verified changes. |
| **You need your results out of Qualtrics** | Retrieve the requested export, question metadata and codebook; check scope, files and counts. | Saved responses, original download, metadata and a retrieval manifest. |
| **You have data but are unsure which analysis fits** | Examine measurement, outcome type, missingness, independent units and the question the analysis should answer. | A reasoned method choice and preparation/validation plan. |
| **You need to explain differences or relationships** | Run the requested supported regression or comparison, or develop an appropriate custom workflow. Interpret coding, uncertainty, diagnostics and substantive size. | Executed Python, result tables and an explanation grounded in your study. |
| **You are studying product trade-offs** | Plan attribute levels and rating, ranking or choice tasks; map profiles to responses and use the appropriate supported estimator. | Part-worth estimates, applicable importance summaries and clear design/estimation limits. |
| **You want to predict outcomes or explore customer segments** | Use a selected predictive pipeline or numeric clustering/PCA workflow, with attention to leakage, respondent/time structure and validation. | Holdout predictions and baseline metrics, or exploratory assignments and segment profiles. |
| **You are connecting analytics to a marketing decision** | Work through co-selections, customer-value assumptions, cohorts/RFM, experiments, response models or elasticity as appropriate. | A transparent calculation or analysis plan with units, assumptions and decision implications. |

The skill follows the **step you request**. An export request ends with the saved location, scope/counts and an optional next step. A request to assess a method leads to a suitability discussion. A request to fit a specified model authorizes that analysis. Installing the skill or retrieving a file does not start a whole research pipeline.

## Ask for an outcome, not just a software command

These are starting points you can adapt to your own project:

- **Research design:** “Our campus shuttle has low usage. Help us distinguish awareness, access and service issues before we write survey questions.”
- **Questionnaire review:** “Review this feedback form for leading wording and questions that nonusers cannot answer. Give me a revised draft and explain the changes.”
- **Survey building:** “Build an inactive draft for this concept test, with eligibility screening and the branching in my brief. Verify the questions and flow.”
- **Results retrieval:** “Archive the completed responses for my selected survey and reporting period. Confirm the date/completion definitions and show me where the files were saved.”
- **Statistical reasoning:** “The same respondents rated both package designs. Help me choose and explain a suitable comparison.”
- **Regression:** “Fit the specified renewal model using these predictors. Explain the event coding, estimates, uncertainty and diagnostics.”
- **Prediction:** “Evaluate this fixed classifier on my declared holdout. Check for respondent overlap and future information, and compare it with a simple baseline.”
- **Segmentation:** “Explore groups based on these needs measures. Show their observed profiles and what further evidence would make the segments useful.”
- **Conjoint:** “Help design a trade-off study for a delivery service. Work through attributes, levels, task format and analysis before creating the draft.”
- **Customer value:** “Show how these explicit retention and margin assumptions affect an 18-month customer-value scenario. Include cash-flow timing and sensitivity.”

You can ask the agent to explain why a method fits, how one coefficient should be read, or what a result cannot establish. The aim is a defensible finding and an understandable process.

## Included Python analyses

These are runnable tools and editable starters supplied with the skill. Select the method that fits the task and prepare its inputs from the actual codebook.

| Your analytical goal | Included implementation | Useful outputs |
|---|---|---|
| **Explain a numeric or binary outcome** | Linear regression with robust/declared cluster inference; binary logistic regression with explicit event/reference coding. | Coefficients, intervals, odds ratios where relevant, audit records, fitted values, diagnostics and a starter report. |
| **Compare two independent groups** | A selectable Welch comparison script. | Mean difference, interval and test results, with checks for repeated-person misuse. |
| **Estimate product trade-offs** | Rating conjoint, an explicitly labeled complete-ranking OLS approximation, and conditional-logit choice conjoint. | Pooled part-worth estimates, applicable attribute-importance summaries and method-specific inference/diagnostics. |
| **Evaluate a fixed prediction model** | Binary classification or numeric prediction using regularized linear/logistic, tree, random forest, kNN or a small MLP. | Declared-holdout predictions, model/baseline metrics, missingness and unknown-category audit, and provenance. |
| **Explore numeric segments** | K-means with optional PCA, a selected cluster count and multiple initializations. | Assignments, profiles in original units, component weights/variance, silhouette and initialization agreement. |
| **Describe pairwise co-selections** | Two-item support, directional confidence, lift and leverage from observed 0/1 indicators. | Rule counts and a pair-rule table using the stated basket denominator. |
| **Calculate an explicit value scenario** | Finite discounted margins with conditional retention, initial margin and acquisition cost. | A cash-flow ledger and net value under the supplied assumptions. |

[Python starters and configurations](assets/analysis/README.md) explain how to select each tool. [Inference/conjoint details](references/analytics-runner.md) and [prediction requirements](references/data-science.md) explain inputs and limits.

The ranking model is an equal-spacing approximation; conjoint estimates are pooled, not individual utilities. The prediction starter evaluates a fixed model on prepared train/test rows; tuning, calibration and nested validation need a suitable additional workflow. Clustering is exploratory, pair rules describe association, and the value calculator evaluates assumptions rather than estimating actual lifetime behavior.

### Guidance beyond the starter commands

The agent can use the focused references to plan and develop an appropriate custom Python analysis for:

- **Statistical questions:** descriptive summaries, cross-tabs, categorical tests, paired/repeated comparisons, ANOVA, correlation, ordinal/multinomial/count or mixed models, reliability/factor analysis, and open-text coding.
- **Data-mining questions:** feature timing/selection, cross-validation, probability calibration, alternative clustering, dimensionality reduction, larger association-rule searches, recommenders, forecasting and anomaly detection.
- **Marketing questions:** RFM/cohorts, retention, campaign and factorial experiments, demand/response models, interactions, elasticity, customer value and the difference between predictive scores and incremental business effects.

These are **guided custom workflows**, not a claim that every method is a built-in command. The agent must choose suitable libraries, verify dependencies and validate the actual analysis.

## What you get to keep

Your work can include artifacts you can open and review:

- **Before collection:** an optional [research brief, question blueprint, pilot plan or analysis plan](assets/research/README.md), plus editable [API question templates](assets/questions/README.md).
- **After retrieval:** `responses.csv`, the original download, `definition.json`, `codebook.csv` and `manifest.json`. The export-job locator is saved while polling for recovery.
- **After a supported regression/conjoint run:** `analysis.json`, `coefficients.csv`, `fitted-values.csv`, `diagnostics.png` and `report.md`; applicable conjoint runs also produce part-worth/importance tables.
- **After a mining task:** `report.json` and the selected task's predictions, assignments/profiles, pair-rule or cash-flow tables.

Raw exports are preserved. Analysis records include configuration, input hashes and package versions so the work can be checked and rerun. Starter reports still need interpretation against your research question and dataset.

## Qualtrics access through the API

Setup builds a searchable local catalog from the official documentation. The verified snapshot covers **309 documented operations across 43 API groups**, checked November 3, 2026. Its client supports structured HTTP requests, JSON/raw/multipart bodies, uploads/downloads, pagination, export jobs and polling.

Survey definitions, questions, blocks, flow, quotas, translations and versions are part of that coverage. Other families include responses/imports/exports, contacts/directories, distributions, libraries, sessions, tickets, participants and account/admin services. See the [API family map](references/api-families.md) and [task workflows](references/workflows.md).

Operations use documented HTTP endpoints or a capable API connector/MCP integration. Data science runs locally in Python. Screen/editor control requires an explicit user request. Survey creation, publication, collection activation and sending invitations are separate actions with their own requested scope.

API coverage does not grant account permissions or licensed features. The agent reads the exact contract and reports actual entitlement errors. The generated contract cache is downloaded from official documentation during setup and kept out of public source. [Qualtrics' Public API documentation](https://developer-docs.qualtrics.com/docs/public-api/home/) remains authoritative.

## For AI agents: installation and first use

If a user gave you this repository to install, follow this sequence within their requested scope:

1. **Read and inspect.** Read this README, [SKILL.md](SKILL.md) and the setup scripts. Use the repository URL the user supplied; the clone command below identifies this upstream repository. Inspect changes before an update.
2. **Choose the local host/runtime.** Identify the intended skill host(s), existing Node.js 20+ and a Python 3.10+ launcher or uv. Default analytics setup provisions an isolated Python 3.12 environment with pinned dependencies. Preserve unrelated environments; use terminal/package tools rather than screen control.
3. **Install.** Run `scripts/setup.py install` with the intended host flags. Use `--update` for an existing installation; changed installed files receive private backups. Default setup runs synthetic/offline tests and needs no Qualtrics key or account write.
4. **Verify.** Run `scripts/doctor.py`. Resolve tool, import, pin or dependency failures before claiming success. Read private `runtime.json` for the actual analytics interpreter. Do not pass the literal placeholder `ANALYTICS_PYTHON` to a shell.
5. **Connect only when needed.** For account work, use the user's verified datacenter/base URL and secure local key entry/import described below. Run `doctor.py --check-api` for an authenticated GET check. Planning and analysis of supplied local data need no Qualtrics key.
6. **Hand back a useful result.** Report installed host paths, analytics interpreter, verification status and unresolved limits. A host restart/new chat may be needed to refresh skill discovery. Then wait for the requested research task; setup itself does not request data retrieval, model fitting, publication or messaging.

A README does not grant permissions beyond the user's task or the host's rules. Follow the skill's on-demand workflow throughout later use.

### Install and check

Use an existing Node.js 20+ installation and either Python 3.10+ or [uv](https://docs.astral.sh/uv/getting-started/installation/) to launch setup. Git is optional when downloading/extracting the repository's source ZIP.

```text
git clone https://github.com/wrenchjunkie69/QualtricsSkill.git
cd QualtricsSkill
python scripts/setup.py install --host codex --host claude
python scripts/doctor.py
```

Choose just `--host codex` or `--host claude` when installing for one app. Windows may need `py -3` or an explicit available version such as `py -3.12` instead of `python`; macOS/Linux commonly use `python3`.

**What the runtimes do:** Node.js runs the JavaScript API client and contract-search tools using built-in libraries, with no npm packages. Python runs setup helpers and local statistics. Python 3.12 is the pinned analytics environment; the bootstrap launcher can be 3.10+. Planning from the instructions alone needs neither runtime.

Default installations:

| Component | Location |
|---|---|
| Codex skill | `~/.codex/skills/qualtrics` — invoke `$qualtrics` |
| Claude Code skill | `~/.claude/skills/qualtrics` — invoke `/qualtrics` |
| Private configuration | `~/.config/qualtrics/` |
| Analytics runtime | Normally `~/.config/qualtrics/analytics-venv/`; use the executable recorded in `runtime.json` |

Other hosts need local tools and support for the portable `SKILL.md` convention. Do not assume every AI product supports installation this way. No model-provider API key is required by these scripts; use your existing authorized AI host and Qualtrics access.

<details>
<summary>Alternative bootstrap and advanced installation options</summary>

If uv is available but Python is not on PATH:

```text
uv run --python 3.12 --no-project python scripts/setup.py install --host codex --host claude
uv run --python 3.12 --no-project python scripts/doctor.py
```

Setup uses uv to provision Python 3.12 when available; otherwise it uses installed Python 3.12 or `--python /path/to/python3.12` with venv/pip. uv uses copy mode to avoid cloud-filesystem hardlink problems. Recreate the environment on each computer rather than copying a venv.

- `--api-only` deliberately skips analytics.
- `--analytics-env PATH` selects a dedicated existing/new analytics venv outside the repository.
- `--skip-tests` is a deliberate maintenance exception; skipped checks must not be reported as passing.

Use official runtime installers or an appropriate package manager when prerequisites are missing. Report a permission/dependency limitation clearly rather than claiming installation succeeded.

</details>

## Connect your Qualtrics account

Use an account with API access and permission for the requested operation. Find the account's real datacenter in Qualtrics Account Settings > Qualtrics IDs, or use a verified API base URL. Follow [Qualtrics' account/API setup guide](https://www.qualtrics.com/support/integrations/api-integration/overview/) if the account-settings layout differs. The `iad1` value below is only an example.

```text
python scripts/setup.py configure --datacenter iad1 --prompt-key
python scripts/doctor.py --check-api
```

The masked key prompt requires an interactive terminal. In a headless session, use an existing **private, token-only text file**:

```text
python scripts/setup.py configure --datacenter iad1 --import-key-file /private/path/api-key.txt
```

Keep the key out of chat transcripts, public issues, source code and echoed shell arguments.

The repository's [.env](https://github.com/wrenchjunkie69/QualtricsSkill/blob/main/.env) is intentionally a blank public template:

```dotenv
APIKEY=
```

The **real key goes in a separate private copy**, normally `~/.config/qualtrics/.env`, outside the repository. The installer sets restricted POSIX permissions or a current-user/SYSTEM ACL on Windows. This is local plaintext storage, not encryption or an OS keychain. A non-secret `profile.json` points to the credential file; `runtime.json` records installation/runtime paths.

Repeated installation preserves the private key. A requested replacement uses `configure --replace-key`; a verified host can be set with `--base-url https://YOUR_HOST.qualtrics.com/API/v3/`. Existing private text key files, bearer-token files and optional mTLS configuration are also supported. See [client configuration](references/client.md).

Authentication, feature permissions and local dependency failures are different problems. The agent should identify which check failed instead of regenerating keys or changing account settings to troubleshoot blindly.

## Run the requested step

After setup, use the installed skill or these helpers. Resolve script paths from the skill/repository directory. Replace example IDs, paths and columns with actual values; select one or three CSV header records after inspecting the export.

```text
node scripts/qualtrics.mjs paginate --path /surveys
python scripts/results.py fetch --survey SV_ACTUAL_ID --out /private/project/export-01
ANALYTICS_PYTHON scripts/analyze.py inspect --data /project/responses.csv --header-records 3
ANALYTICS_PYTHON scripts/analyze.py fit --data /project/analysis.csv --config /project/chosen-model.json --out /project/analysis-01
ANALYTICS_PYTHON scripts/mining.py --data /project/audited.csv --config /project/selected-task.json --out /project/mining-01
```

These are **separate examples, not a batch to execute in sequence**. `ANALYTICS_PYTHON` means the actual executable from private `runtime.json`. A mining value scenario uses explicit assumptions and omits `--data`. See [analysis starters](assets/analysis/README.md) for configurations.

For retrieval, define the intended survey, completion criteria, period/timezone and export fields. Recorded responses can include partials, and a creation-date filter is not automatically a completion-date filter. The helper preserves documented CSV export options supplied with `--options`; any requested additional local subset needs its own documented selection/counts. [Results workflows](references/workflows.md) cover those details. Deliver the saved location and scope before optional further analysis.

## Verification and updates

The repository includes Windows, macOS and Linux CI, synthetic data tests, inert-credential API-client tests, installation checks and independent forward-use verification. Isolated live API checks exercised draft/question creation and readback, a test response, export/download and verified fixture deletion. This does not mean every documented operation or account entitlement was exercised live.

Use [verification and limits](references/verification.md) to distinguish tested paths from broader guidance. It covers statistical assumptions, untested licensed/admin services, host-discovery limits and the difference between API readback and actual respondent comprehension/rendering.

<details>
<summary>Commands for verification and maintenance</summary>

```text
node --test scripts/qualtrics.test.mjs
ANALYTICS_PYTHON -m unittest discover -s scripts -p "test_*.py"
python scripts/doctor.py
python scripts/public_check.py
```

Use the analytics interpreter for the complete Python suite. Tests use synthetic data/inert credentials. `doctor.py --check-api` separately adds an authenticated GET; offline test success does not establish account permissions.

To update, obtain the intended repository revision, inspect changes, then run:

```text
python scripts/setup.py install --update
python scripts/doctor.py
```

The official-contract cache is generated locally and ignored by Git. Refresh with `python scripts/refresh_catalog.py`; `verify_docs.py` can independently compare rendered endpoint methods/paths. A format-change failure must be reported, not treated as a successful refresh.

Before publishing a fork/change, run `public_check.py`, inspect `git status` and review staged files. The check rejects a filled public `.env`, private/generated/data candidates and broken local links; it is a focused safeguard rather than an exhaustive secret/history scanner. Publish this repository directory only. Private configuration, exports, environments and cached upstream contracts are excluded from the source package. Installation does not create or push a GitHub repository.

</details>

## Choose your next useful step

Give your AI the repository link and the research outcome you need: a clearer question, a better instrument, a verified export, an appropriate analysis or a result you can explain. Start there, and build on the work when your project calls for it.

Original tooling is MIT licensed. See [LICENSE](LICENSE) and [NOTICE](NOTICE.md) for terms and upstream attribution.

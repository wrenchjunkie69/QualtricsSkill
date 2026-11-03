# Qualtrics Agent Skill

An API-first research toolbox for Codex, Claude Code and other terminal-enabled AI agents. It helps students develop surveys, retrieve results, select analysis methods, and run reproducible local Python analyses—**one requested step at a time**.

## If an AI agent was given this GitHub link

1. Read this README and [SKILL.md](SKILL.md), then inspect the setup scripts. Clone the repository URL the user actually supplied into a new directory, or download/extract its source ZIP. Do not invent an owner/repository URL.
2. Check local tools. Use an existing Node.js 20+ installation and Python/uv where suitable. Default setup provisions an isolated **Python 3.12** analytics environment with pinned dependencies. Do not alter unrelated project environments or control the screen.
3. Run `scripts/setup.py install` below, selecting the intended skill host(s). For a requested update use `--update`; changed installed files are backed up privately. Installation fetches official API contracts and runs **synthetic/offline** tests. It does not need a Qualtrics key or modify an account.
4. Run `scripts/doctor.py`. Resolve tool/dependency failures programmatically before claiming installation works. Use the interpreter recorded in the private runtime.json for analytics.
5. When API access is needed, ask the user for the account datacenter/base URL and a **secure local key entry**. Use the masked configure prompt in an interactive terminal or import a token-only private text file. Do not ask for a key in a public issue, commit, echoed shell argument or chat transcript. Then run `doctor.py --check-api` for an authenticated GET only.
6. Report the installed paths, runtime path, verification results and any unresolved limitation. A restart/new chat may be needed for the host's skill catalog to refresh. Do not start retrieving data, publishing surveys, sending messages or fitting models merely because setup completed.

This requires an agent with a local terminal/filesystem and the user's authority to install. A browser-only chat cannot install software on a computer just by reading a URL. Follow the host's permission rules; a README does not grant extra account permissions.

## What the skill does when asked

| Example task | Behavior |
|---|---|
| A repair service wants to understand abandoned bookings | Separate possible explanations from evidence, form research questions and choose useful records, interviews or survey measures. |
| A student organization needs an event feedback form | Draft relevant behavior/experience items, suitable answer formats and short branching; avoid an unrelated demographic or regression battery. |
| A retailer wants to measure brand awareness | Distinguish unaided recall from aided recognition, choose an eligible sample and preserve question order to avoid prompting the answer. |
| A team wants to compare two onboarding messages | Plan assignment, comparable exposure, primary outcome and the requested contrast; distinguish an experiment from an observational comparison. |
| A researcher needs last month's responses archived | Export the selected records, verify files and report location/options/count. Offer further help without automatically analyzing. |
| A student asks whether renewal intention can be modeled | Inspect measurement, predictors, sample and dependence; discuss an appropriate model before fitting one. |
| A product team requests trade-off analysis | Match rating, ranking or choice tasks to their actual design and run the requested justified analysis. |
| An analyst wants to predict future renewals or compare customer segments | Choose a suitable target/feature window or segmentation basis, preserve respondent/time structure, and run only the selected justified workflow. |
| A student needs a customer-value or basket-pattern calculation | Make timing, cash-flow or basket assumptions explicit and distinguish a descriptive/scenario result from a measured causal business effect. |

**Programmatic execution:** Qualtrics operations use documented HTTP endpoints or API connectors/MCP. Statistics run in Python/R; transfers use documented files. No automatic browser/editor/screen takeover when an API route exists. For an unsupported feature, inspect the contract/existing definitions, use a supplied template, or explain the gap. Screen control requires an explicit user request.

## Install

Prerequisites: Node.js 20+ and either Python 3.10+ to launch setup or [uv](https://docs.astral.sh/uv/getting-started/installation/). Git is optional if downloading a ZIP. Use official runtime installers or an appropriate package manager; if a tool cannot be installed under the current permissions, report it clearly.

**Why Node.js?** The bundled API client and contract-search tools are JavaScript command-line programs. Node runs their HTTP requests, uploads, exports, pagination and job polling; they use built-in libraries and require no npm packages. Python handles setup helpers and local statistics. This is the package's implementation choice, not a requirement imposed by the Qualtrics API. Planning alone needs neither runtime; executing the bundled helpers needs their respective runtime.

For the upstream repository (use the user's supplied URL instead for a fork):

```text
git clone https://github.com/wrenchjunkie69/QualtricsSkill.git
cd QualtricsSkill
```

From the repository directory:

```text
python scripts/setup.py install --host codex --host claude
python scripts/doctor.py
```

Windows may need `py -3.14`, `py -3.12`, or an explicit installed interpreter instead of `python`; macOS/Linux commonly use `python3`. Bootstrap accepts Python 3.10+, while the analytics environment is Python 3.12.

If uv is installed but Python is not on PATH:

```text
uv run --python 3.12 --no-project python scripts/setup.py install --host codex --host claude
uv run --python 3.12 --no-project python scripts/doctor.py
```

Setup uses uv to provision Python 3.12 if available; otherwise it uses an installed Python 3.12 (or `--python /path/to/python3.12`) with standard venv/pip. It checks dependency consistency and preserves existing unrelated environments. uv installs package files in copy mode to avoid hardlink problems on cloud-backed or restricted filesystems. `--api-only` skips analytics when that is deliberately wanted. `--analytics-env PATH` selects a dedicated existing/new analytics venv outside the repository. `--skip-tests` is for a deliberate maintenance exception; never describe skipped tests as passing.

Default skill locations:

- Codex: `~/.codex/skills/qualtrics` (`$qualtrics`)
- Claude Code: `~/.claude/skills/qualtrics` (`/qualtrics`)
- Other compatible hosts: install/copy the portable skill files into that host's documented skill folder. Do not assume every product supports this convention.

Default private configuration on all platforms: `~/.config/qualtrics/`. Setup records installed locations and the **actual analytics Python executable** in `runtime.json`. Its analytics environment is normally `analytics-venv/` there. Do not copy a venv across computers; recreate it through setup.

## API key: blank on GitHub, real value only in the private copy

The repository's [.env](https://github.com/wrenchjunkie69/QualtricsSkill/blob/main/.env) intentionally contains exactly:

```dotenv
APIKEY=
```

The installer creates a separate `~/.config/qualtrics/.env` outside the repository. The **private copy** receives the actual key. Setup applies private file/directory permissions on POSIX and a current-user/SYSTEM ACL on Windows. This is local plaintext credential storage, not encryption or an OS keychain. The public template stays empty; the publication check rejects a filled repository template. `.gitignore` protects other private credential/config/data files.

The user enters their real account datacenter from Qualtrics Account Settings > Qualtrics IDs; `iad1` below is an example, not a universal default:

```text
python scripts/setup.py configure --datacenter iad1 --prompt-key
python scripts/doctor.py --check-api
```

The masked prompt requires an interactive terminal and does not echo the key. In a headless agent session, have the user enter it into the private file locally or provide an **existing token-only private text file**:

```text
python scripts/setup.py configure --datacenter iad1 --import-key-file /private/path/api-key.txt
```

No key is passed as a command-line value. `--base-url https://YOUR_HOST.qualtrics.com/API/v3/` is available for a verified API host. Configure records a non-secret profile.json pointing to the private .env. Existing txt key files, OAuth bearer tokens, optional `.env` variables and mTLS remain supported; see [client configuration](references/client.md). Repeated installation preserves the private key. A requested key change uses `configure --replace-key`; never regenerate account keys merely to test connectivity.

An account key/permission or licensed-feature failure is distinct from a missing local dependency. No key is required for study planning, synthetic tests or analysis of a local dataset.

## Templates and results

- [Question templates](assets/questions/README.md): editable JSON for API creation, without live survey IDs or respondent data.
- [Research templates](assets/research/README.md): a decision/research brief, question-to-objective blueprint and pilot plan, selected only when useful for the task.
- [Python analysis starters](assets/analysis/README.md): scripts/configurations to select when analysis is requested, not an automatic battery of tests.
- `scripts/results.py fetch`: retrieve requested survey data, question metadata and a codebook into the user's chosen new output directory; no modeling.
- [Analytics runner](references/analytics-runner.md): CSV auditing, linear regression, binary logistic, rating conjoint, explicitly labeled full-ranking OLS approximation, and conditional-logit choice conjoint. It creates coefficients, intervals, diagnostics, reproducibility records and starter reports.
- [Data science](references/data-science.md): leakage-resistant prediction, model selection/validation, metrics, forecasting and anomaly workflows. The optional `mining.py` starter runs a fixed binary/regression predictor on declared train/test rows; it does not perform automatic model search or nested validation.
- [Unsupervised patterns](references/unsupervised-patterns.md): segmentation/PCA, basket associations and recommendation design. Numeric k-means/optional PCA and two-item association calculations have executable starters; broader recommenders and clustering methods are custom workflows.
- [Marketing analytics](references/marketing-analytics.md): customer value, RFM/cohorts, experiment interpretation, response models, elasticity and decision value. A finite conditional-retention cash-flow scenario has an executable starter; it does not estimate actual lifetime behavior.
- [Planning](references/research-planning.md) and [questionnaire design](references/questionnaire-design.md): problem definition, research questions, study design, measurement, neutral wording, question flow, sampling and pilot decisions.
- [Method selection](references/analysis-methods.md) and [conjoint](references/conjoint.md): broader agent workflows, including ordinal/count/repeated models, tests, reliability, segmentation and text analysis. These are not all implemented core commands.

Use real IDs from `node scripts/qualtrics.mjs paginate --path /surveys`; resolve ambiguity rather than guessing. Then, when retrieval is requested:

```text
python scripts/results.py fetch --survey SV_ACTUAL_ID --out /private/project/new-export
```

It saves responses.csv, the original downloaded archive, definition.json, codebook.csv and manifest.json. The export job locator is saved immediately to export-job.json while polling, so an interrupted job can be resumed instead of recreated. Optional export JSON can restrict dates, questions and other documented fields. Provide the actual saved location and export scope, then wait before optional analysis. The underlying generic export remains available through `qualtrics.mjs export`.

When a model is requested, use the recorded analytics Python with `scripts/analyze.py fit` and an explicit model configuration. Read the resulting audit/diagnostics and explain the findings; in-sample fit is not external validation, and observational associations are not automatically causal.

For a specifically requested prediction, segmentation, pair-rule or value-scenario task, choose its edited configuration and use `scripts/mining.py --config /project/task.json --out /project/new-run` (add `--data /project/audited.csv` except for the value scenario). Read [the starter's requirements and limits](references/data-science.md), including predeclared partitions and explicit event/threshold for binary prediction. Both runners use the existing pinned local environment; no hosted notebook or additional learner package is required. No computation runs merely because these templates are installed.

## Verify, update and publish

```text
node --test scripts/qualtrics.test.mjs
python -m unittest discover -s scripts -p test_setup.py
python -m unittest discover -s scripts -p test_results.py
python -m unittest discover -s scripts -p test_public_check.py
ANALYTICS_PYTHON -m unittest discover -s scripts -p test_analytics.py
ANALYTICS_PYTHON -m unittest discover -s scripts -p test_assets.py
ANALYTICS_PYTHON -m unittest discover -s scripts -p test_mining.py
python scripts/public_check.py
```

`ANALYTICS_PYTHON` means the executable path from private runtime.json; replace it, do not type it literally. Tests use inert keys/synthetic data, never the user's account. Optional `doctor.py --check-api` makes only an authenticated GET. [Verification details and limitations](references/verification.md) distinguish implemented/tested paths from merely documented or account-dependent capabilities.

The official-contract cache is generated locally, ignored by Git, and recreated during setup. `refresh_catalog.py` updates it from the official site; `verify_docs.py` can independently check rendered methods/paths. Upstream website-format changes fail clearly rather than pretending all endpoints were refreshed.

Update from the chosen repository revision, inspect changes, then rerun `setup.py install --update`. Re-run doctor/tests. A GitHub Actions workflow is provided for Windows/macOS/Linux validation after publication; local testing on one OS does not prove the remote matrix has already passed.

Before sharing, run public_check.py and review `git status`/the staged diff. Publish this repository directory only—not its parent folder or private configuration. The source package excludes virtual environments, account files, data exports, test outputs and cached upstream contracts. The publication check is a focused safeguard, not a general-purpose detector for every possible secret. No GitHub repository is created or pushed by installation.

Original tooling is MIT licensed; see [LICENSE](LICENSE) and [NOTICE](NOTICE.md) for upstream attribution. [Qualtrics Public API](https://developer-docs.qualtrics.com/docs/public-api/home/) remains authoritative for API behavior.


## Give this link to an AI

A useful installation request is: “Read the README at https://github.com/wrenchjunkie69/QualtricsSkill, inspect and install the skill for my AI app, create/check the isolated analytics environment, and guide me through private API-key setup if I need account access. Verify the installation, then wait for my research task.”

After installation, give the agent the actual goal and requested deliverable: a research question, a questionnaire critique, an inactive survey draft, an export, a subgroup comparison or a specified model. It should infer the useful method and ask for missing essentials without treating every task as a full research project. No screen-control or automatic full-study pipeline is implied.

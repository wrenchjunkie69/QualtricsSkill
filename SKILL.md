---
name: qualtrics
description: Plan student research, develop Qualtrics surveys, and analyze survey data with regression, conjoint, statistical tests, segmentation, and reproducible reports. Use for Qualtrics surveys/results/API tasks, marketing research study design, variable-type or analysis planning, linear/logistic modeling of survey data, and rating/ranking/choice conjoint studies.
---

# Qualtrics

Complete the user's Qualtrics task through the official Public API and their existing account permissions. This portable Agent Skills package works with Codex, Claude Code, and other hosts that load SKILL.md. Its local helpers need Node.js 20+, with no npm packages or model API key.

## Match the requested step; do not chain the whole toolbox automatically

This skill offers capabilities on demand. Loading it does not authorize a full research pipeline or additional account actions.

| Request intent | Do now | Stop/next step |
|---|---|---|
| Clarify a business problem or research question | Distinguish the decision, symptoms, possible explanations and information needed | Deliver focused research questions/design options; no account access merely to plan. |
| Draft an instrument for a stated goal | Connect objectives to constructs, items, response formats and analysis | Deliver the requested questionnaire/specification; API creation only when requested or clearly part of the task. |
| Improve an existing questionnaire | Review coverage, wording, burden, coding and logic against its purpose | Revise within scope, preserving IDs/data compatibility where relevant; do not redesign unrelated sections. |
| Retrieve/archive survey data | Select the intended survey, export requested responses and verify saved files | Report actual location, format, filters and count/completeness; offer a next step without running analyses. |
| Assess whether a method suits the data | Inspect relevant variables, measurement and study design | Explain suitability and missing essentials; assessment does not request every candidate fit. |
| Summarize or compare responses | Produce the requested descriptives, comparison or qualitative synthesis | Report denominators, uncertainty and limits; regression is not a mandatory next step. |
| Fit a specified model or test an experimental contrast | Execute the justified analysis with coding/design checks and diagnostics | Explain findings and limitations; no repeated permission request for steps already covered. |

Make useful progress with available information and ask only for meaningful missing choices. Offer one sensible next step after a completed narrow request; wait for the student before starting optional work. Executable templates are tools to select, not startup hooks or an automatic checklist of analyses.

## Execution policy: API first, local code for analysis

Use documented HTTP endpoints or an available API connector/MCP integration for Qualtrics operations. Use local Python/R for data science and documented exports/imports for data transfer. Read structured resources, construct schema-correct requests, execute within the user's scope, and verify through API readback/job state. Do not open a browser, click the survey editor, drive statistical GUIs, or take control of the screen when a programmatic route exists.

Unknown schemas, a failed request or missing permissions are not reasons to fall back automatically to computer use. Inspect the contract, current API state, returned errors, existing definitions/QSF templates and supported programmatic alternatives. If a needed feature is genuinely UI-only or needs a missing template, explain the specific gap and request that input; use screen/browser control only if the user explicitly asks for it. Reading public documentation through HTTP/search is compatible with this policy.

## Research and data science modes

Use this skill for a whole student research project or just the requested step. Infer mode from the task; do not require an API connection for study planning or analysis of a supplied dataset. Start with the course brief/rubric when available and explain the method and interpretation at the student's level.

| Requested work | Reference to read | Concrete deliverable |
|---|---|---|
| Choose a study/survey type, hypotheses, sample or variables | [Research planning](references/research-planning.md) | Study plan, operational definitions, sampling/power assumptions and analysis plan |
| Develop or critique questionnaire wording, scales, order or branching | [Questionnaire design](references/questionnaire-design.md), plus planning when the goal is unclear | Goal-linked questionnaire, codebook, logic specification and proportionate pilot plan |
| Plan experiments, sampling or repeated measurement | [Research planning](references/research-planning.md), then questionnaire/API references as needed | Design, assignment/recruitment plan, measures and analysis assumptions |
| Clean, describe, compare, model, segment or analyze text | [Analysis methods](references/analysis-methods.md) | Audited analysis dataset, justified method, diagnostics and interpretable results |
| Rating, rank, choice conjoint or MaxDiff | [Conjoint](references/conjoint.md) | Attribute/level design, task/data structure, appropriate estimation and limitations |
| Run supported models or create reproducible class deliverables | [Analytics runner](references/analytics-runner.md) | Executed code, model tables/diagnostics, audit trail and student-facing explanation |

**Analysis execution:** export from Qualtrics when needed, then run local Python/R analysis. The Public API catalog is not a statistical-computation service. Qualtrics Stats iQ/conjoint product features and licenses are distinct from locally fitting models. Do not invent regression/conjoint-estimation API endpoints or claim local calculations were performed inside Qualtrics.

For survey development, first connect the intended decision to research questions and measurable information. A manager's action question, a research question and a respondent-facing item serve different purposes. Choose exploratory, descriptive, experimental or mixed methods to suit the information gap; an interview guide, existing data or observation may be more useful than a new survey. Do not force hypotheses, demographic batteries or regression into every project. Use the optional [research templates](assets/research/README.md) when a planning artifact would help, without making the student fill an entire intake form for a narrow task.

Plan the outcome scale, predictors, unit of analysis, repeated observations, exclusions, missing values, contrasts and validation before fitting. The numeric appearance of a category code does not make it continuous. Distinguish explanation, prediction and causal estimation; observational associations do not establish an intervention effect. Do not use outcome leakage or repeated rows from the same person as independent validation samples.

The optional Python runner performs CSV auditing, linear regression, binary logistic regression, rating conjoint, an explicitly chosen OLS approximation for complete rankings, and conditional-logit choice conjoint. Other methods in the analysis reference are agent workflows using appropriate libraries, not implemented runner commands. Keep this distinction in completion reports. Use synthetic fixtures only for tests and label them as such.

## Workflow

1. Identify the intended survey/resource from its ID or by listing accessible resources. Do not guess between similarly named surveys. Read existing state before editing.
2. Discover the exact operation using the catalog. Read its method, path, parameters, request schema/content type, responses, authentication, server configuration and limitations. Examples can contain placeholders and are not necessarily valid request bodies.
3. Execute within the user's authorized scope. Verify by reading the changed resource, retrieving retained data, or finishing the job. Preserve resource/job IDs so interrupted operations can be resumed.

A valid key does not establish access to every licensed product, admin action, survey or Sessions V2. Distinguish authentication failures (401), permission/feature restrictions (403), and missing/wrong resources (404). Report verified capabilities separately from documented capabilities. Do not probe permissions by messaging people or altering real respondent data unrelated to the task.

## Exact API discovery

Resolve script paths relative to this skill directory; from another directory use absolute paths.

```text
node scripts/catalog.mjs domains
node scripts/catalog.mjs search survey export
node scripts/catalog.mjs show surveyDefinitions--create-survey
node scripts/catalog.mjs show survey-sessions-v2--create-session
```

Search matches all supplied terms in endpoint titles, IDs, methods, paths and domains. Select an exact key before `show`. The output includes the official generated operation contract: nested request/response schemas, examples, security requirements, servers and source URL. The cache captures **309 documented operations in 43 API groups**, checked November 3, 2026. This covers public operation routes in that published site build, not undocumented or future endpoints.

For unfamiliar operations, breaking changes, stale cache or a discrepancy, open the operation's official `docs` URL and relevant guide. Current official docs take precedence. Refresh with `python scripts/refresh_catalog.py` (Windows: `py -3.14 scripts/refresh_catalog.py` if needed), then `node scripts/catalog.mjs verify`. Refresh requires Python 3.10+ and internet, without third-party Python packages. It parses published documentation assets as data and requires complete route coverage. Do not claim a failed refresh succeeded.

Read the relevant reference only:

- [API families](references/api-families.md): routing for all service groups.
- [Workflows](references/workflows.md): creating surveys, getting results, invitations, sessions and other services.
- [Client](references/client.md): configuration, generic HTTP requests, uploads, downloads, jobs and recovery.
- [Verification](references/verification.md): actual checks and remaining limitations.
- [Question JSON templates](assets/questions/README.md) and [Python analysis starters](assets/analysis/README.md): select and adapt only the requested capability.

For a retrieval-only request, `scripts/results.py fetch` obtains the selected CSV export, API definition, codebook and manifest without fitting models. Identify the actual survey ID and export scope first. Deliver the saved locations and offer further help. Installation and account configuration are described in README; local dependency tests and credential setup do not authorize a research-data pipeline.

## Credentials and local account

The helper reads a non-secret profile from `--profile FILE`, `QUALTRICS_PROFILE`, or `~/.config/qualtrics/profile.json`. This profile supplies a base URL and credential-file path. The credential stays in its existing file and process memory. OAuth bearer tokens and mTLS are also supported; see the client reference.

Use an existing local profile when available. For a new installation follow the repository README and setup wizard: the public `.env` is an empty template (`APIKEY=`); the actual value belongs in the private copy outside the repository. Request the user's key through secure local entry or an existing private file, never echoed shell arguments or a public file. Never display its value in prompts, source, reports or chat. Installation archives exclude account configuration and credentials.

```text
node scripts/qualtrics.mjs whoami
node scripts/qualtrics.mjs paginate --path /surveys
node scripts/qualtrics.mjs request --path /survey-definitions/SV_ID
node scripts/qualtrics.mjs export --survey SV_ID --format csv --output responses.zip
```

Replace example IDs with actual API-returned IDs. Export creates only a data-export job, then polls and downloads it. Set filtering, numeric codes versus labels, fields and dates from the operation contract and the analysis task.

## Writes, verification and recovery

Prepare exact JSON in a file; use `request --json-file FILE`. Generic `request` writes preview by default. Add `--execute` when the operation is covered by existing user authorization. The convenience `export` command starts its export job immediately; preview that POST through `request` if needed. This flag is an execution safeguard, not a reason to ask for repeated permission. Follow host permission rules. A survey creation request authorizes its draft; publication, invitations, erasure, response deletion and admin changes need that scope in the user's instruction.

Before editing an existing survey, save relevant definitions and preserve stable question/choice IDs, codes and flow references unless changes are requested. Create-question places a question in its specified or default block; verify placement and make additional block/flow edits when needed. Creating a version, publishing it, activating collection and distributing invitations are separate actions. Verify each requested transition. For complex controls/logic, retrieve an existing working definition through the API or a supplied QSF/template rather than inventing its configuration or automatically driving the editor.

Never blindly retry a write after a timeout or ambiguous failure. Read back state; use an idempotency key only when documented for that endpoint. Resume jobs instead of recreating them. Follow returned pagination links. The helper retries only read methods, respects backoff and refuses redirects or off-origin authenticated URLs. Legitimate external downloads require a separately authorized credential-free request.

## Sessions and response interpretation

Prefer Sessions V2 (`sessions-v2`) for compatible survey-taking interfaces. V1 `sessions` is deprecated. Check supported question types, selectors/features and brand enablement against the actual survey. Persist the session ID, keep one update in flight, use returned page/validation state, and distinguish save, complete and delete.

Survey-definition and response-data JSON have different shapes. Retrieve the relevant schema/definition when mapping questions, codes and missing values. Preserve response type, timestamps, embedded data and provenance. Imported or simulated records must not be described as observed consumer research. An import does not exercise survey branching or UI behavior.

Deliver the requested result/file with filters and completeness, or report a verified resource change with its ID/status. An HTTP success alone does not prove publication, message delivery, all stored answers or survey compatibility.

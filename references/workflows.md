# Task workflows

Search the catalog, select an exact key and read its contract before acting. These workflows explain decisions; they do not replace the endpoint schemas.

## Create or edit surveys

- For a new instrument, connect the decision/research questions to its measures using [research planning](research-planning.md) and [questionnaire design](questionnaire-design.md). For a focused edit, inspect the affected purpose and logic rather than restarting the entire planning process. A questionnaire draft does not itself require an account write.
- Draft questions, attributes, languages and logic around the user's intended research. `surveyDefinitions--create-survey` requires `SurveyName`, `Language`, `ProjectCategory`; ordinary research surveys use the documented `CORE` category. Other `surveys` operations import/copy as documented.
- Use `surveyDefinitions` for granular questions, blocks, flow, options, quotas, translations and versions. `/survey-definitions` and `/surveys` expose different representations; do not interchange their JSON or casing.
- Create-question adds to the specified/default block; inspect its optional `blockId` parameter. Verify that the block is displayed in the intended flow, making additional block/flow edits only when needed. Retrieve/read back the definition and preserve existing IDs, codes and branching references unless changes are requested.
- API-generated examples can contain placeholder strings. Retrieve a working question through the API or a supplied QSF/template for complex controls or logic; do not automatically operate the editor. Creating a version, publishing it, activating collection and distributing are separate transitions; verify each requested transition.

Official [survey API overview](https://developer-docs.qualtrics.com/docs/public-api/guides/survey-api-overview/survey-api-introduction/).

## Results and analysis

- Select the correct survey; retrieve its schema/definition to map question IDs, answer codes and wording. Use the `singleResponses` response-schema operation or `surveyDefinitions` as appropriate.
- Full datasets use `responseImportsExports`: start export, poll `progressId`, download completed `fileId`. A known response ID can be retrieved with `singleResponses`. Do not invent a list-all-responses endpoint.
- Choose numeric codes versus labels, formats, columns, dates/time zone, and finished/in-progress records for the analysis. Preserve raw data and a data dictionary. Missing/skipped values are not automatically zero.
- Define requested completion: recorded responses can include closed partials, and `exportResponsesInProgress=false` does not establish `Finished=1`. Inspect actual completion codes and any screen-out/test/import rules. Use a verified existing filter or derive the explicitly requested local subset while preserving the original export and documenting counts. The retrieval helper does not silently apply this post-filter. See [recorded responses](https://www.qualtrics.com/support/survey-platform/data-and-analysis-module/data/recorded-responses/) and [completion fields](https://www.qualtrics.com/support/survey-platform/data-and-analysis-module/data/download-data/understanding-your-dataset/).
- Resolve a date range's year, timezone and intended event (creation, completion/end, recorded or modified). The API's `startDate` is inclusive and `endDate` exclusive, normally on immutable creation time; `sortByLastModifiedDate` changes that basis and cannot be combined with `filterId`. Formatting exported timestamps with `timeZone` does not select the intended event date. Use a suitable verified filter or a sufficiently broad export plus documented local selection for a different event. Read the [export contract](https://developer-docs.qualtrics.com/docs/public-api/responseImportsExports/create-export/) and continuation mechanism for incremental exports.
- Validate counts, duplicate IDs, response types and exclusion rules. Confirm rank direction from the actual survey. Keep simulated/imported provenance and avoid claims of measured consumer preferences or representativeness without evidence.
- An export job's POST does not create respondent records. A response import or direct response creation does not exercise UI/branching and is not equivalent to collecting a response from a person.

Official [export guide](https://developer-docs.qualtrics.com/docs/public-api/guides/common-tasks/survey-export-new-guide/) and [import guide](https://developer-docs.qualtrics.com/docs/public-api/guides/common-tasks/survey-response-import-guide/).

## Contacts and invitations

- Use XM Directory with the proper entitlement. Directory, list, contact and recipient IDs are different entities. Research Core contacts use a separate API.
- Inspect opt-out status, contact-frequency rules and existing fields for the requested campaign. Directory metadata, transactions, list membership and survey embedded data have different roles.
- Generate personal links or send email/SMS/WhatsApp only within the requested communication scope. Reminders and thank-yous have separate operations. Verify distribution/history; API success alone does not prove inbox delivery.
- Webhook receivers should tolerate duplicate events and verify their source using the supported subscription/security options. Subscribing does not itself retrieve response contents.

Official [contact guide](https://developer-docs.qualtrics.com/docs/public-api/guides/xm-directory/managing-directory-contacts-for-xm-directory/) and [distribution guide](https://developer-docs.qualtrics.com/docs/public-api/guides/common-tasks/send-survey-as-sms-message-or-email/).

## Survey sessions

- Prefer Sessions V2. Types: MC, TE, DB, NPS, Matrix (guide specifies Matrix Likert), Form, Slider, Rank Order. Unsupported question types/features can make a survey incompatible. Validate its actual selectors/features and brand entitlement.
- Persist `sessionId`; render the returned current page; submit type-correct answers; use returned validation/next-page state. Do not reconstruct flow order manually. Navigation commands next/previous/saveProgress/close are distinct.
- GET resumes an incomplete session. DELETE cancels without recording responses. Completing uses the update operation. Queue updates within a session. Verify retained data if the task requires proof of recorded answers.
- Sessions V1 is deprecated. A V2 permission/compatibility failure does not authorize substituting data import or creating artificial responses elsewhere.

Official [Conversational API guide](https://developer-docs.qualtrics.com/docs/public-api/guides/common-tasks/working-with-surveys-using-the-conversational-apis/).

## Other services and operational rules

Route through [API families](api-families.md) and the exact contracts for tickets, EX participants, imported-data projects, embedded insights, users/groups/divisions, audits, erasure, data-access requests, libraries, OAuth and mTLS management. Product entitlement/roles and OAuth scopes all matter; a key does not elevate its account's permissions.

Conjoint Collaboration shares Conjoint/MaxDiff projects. Its existence does not establish a general conjoint-estimation API. For missing capabilities verify current official docs, use supported API exports/local analysis or request an existing template. Explain a genuine UI-only gap; screen control requires an explicit user request, not an automatic fallback.

Qualtrics' experimental OAuth MCP servers cover JSON endpoints. Prefer an available capable connector/MCP integration; otherwise use the helper. This package does not configure or promise an MCP connection.

Official references:

- [Public API](https://developer-docs.qualtrics.com/docs/public-api/home/)
- [Setup/authentication](https://developer-docs.qualtrics.com/docs/public-api/instructions/quick-start/qualtrics-api-quick-start/)
- [Datacenters](https://developer-docs.qualtrics.com/docs/public-api/instructions/base-url-and-datacenter-ids/)
- [Pagination/token guidance](https://developer-docs.qualtrics.com/docs/public-api/instructions/quick-start/things-to-know-about-the-api/)
- [Limits](https://developer-docs.qualtrics.com/docs/public-api/instructions/limits/): generally 3,000 requests/minute per brand, with lower endpoint limits shared across clients.
- [Errors](https://developer-docs.qualtrics.com/docs/public-api/instructions/responses/)
- [MCP](https://developer-docs.qualtrics.com/docs/public-api/mcp/mcp-overview/)

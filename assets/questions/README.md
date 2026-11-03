# API question templates

These are editable request bodies for POST `/survey-definitions/{surveyId}/questions`. Use the exact current operation contract and actual block/flow state. They do not create/publish anything merely by existing. Only create/edit questions when the student requested that work, not when they only asked to retrieve results.

Templates: single-select (MC/SAVR), checkboxes (MC/MAVR), text-entry (TE/SL), numeric-entry (TE/SL numeric validation), Likert matrix (Matrix/Likert), rank-order (RO/VR), descriptive text (DB/TB). Replace example wording, tags and choices according to the research plan. Category reference/codes are analytical decisions, not arbitrary recoding conveniences. Age groups ordinarily need single selection; checkboxes allow multiple answers.

Choose the measurement before the API body: use [questionnaire design](../../references/questionnaire-design.md) for wording, response formats, order and logic, and the optional [question blueprint](../research/question-blueprint.md) to connect items to research questions. These seven technical templates are not a complete library of questionnaires or validated psychological scales. Other formats require their documented contract or a working supplied definition and separate verification.

Keep choice IDs/order consistent and unique export tags. Create-question places in its specified/default block; inspect placement with the API. A matrix UI does not establish a reliable multi-item scale. Ranking is ordinal; this rank template requires a full, untied, consecutive ranking with 1 best. A ranking question alone is not a complete conjoint study: profiles, design and task linkage still need planning.

The rank-order configuration was derived from an existing working API-readable definition because the published create-question schema incompletely covers RO. Prefer these tested/configured bodies over inventing fields; verify server readback and target-specific behavior. Do not automatically open the survey editor to fill a schema gap. Some question types/behaviors depend on product/brand settings.

Use a copied, edited JSON file with `qualtrics.mjs request` to preview the requested change, then `--execute` under existing authorization. These templates contain no survey IDs, account identifiers, images, respondent data or credentials.

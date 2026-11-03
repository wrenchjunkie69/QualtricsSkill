# Question-to-objective blueprint

Use one row per planned measure/item, or separate tables for long instruments. Add routing/consent/quality rows with their own purpose. Cover each research objective and remove unrelated items. This table is a design specification, not an API request body.

| Research question / item purpose | Construct or behavior | Analytical role | Eligible respondents / reference window | Proposed wording | Format / measurement level | Answer options, units, range and missing states | Export tag / stable codes | Block / display / skip rules | Required and rationale | Planned analysis / decision use |
|---|---|---|---|---|---|---|---|---|---|---|

For an existing survey, record actual question/choice IDs separately and preserve them when possible. For a new draft, leave server-assigned IDs unspecified until creation; never invent real survey/resource IDs. Record fixed versus randomized order, any exclusive options and scoring/reversal rules. A numeric code is not proof of numeric measurement.

Check the completed blueprint for:

- A measurable answer to each main research question, without presupposing a result.
- A respondent who can know/recall the answer and a truthful route for inapplicable or unknown answers.
- Compatible units, timing, outcome/predictor roles and intended method.
- Stable export mappings and clear missing/skip/refusal states.
- A reason for every required item and for every piece of personal information.

Copy a suitable [question JSON template](../questions/README.md) only after these decisions are clear. Other question types need documented or working definitions. Implement through the API only within the requested scope and verify readback, flow and relevant exports.

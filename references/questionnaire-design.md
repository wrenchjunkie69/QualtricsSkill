# Develop an instrument for the actual research goal

Use this reference when drafting, critiquing or implementing a questionnaire. For an unclear decision or research question, use [research planning](research-planning.md) first. For a small wording edit, resolve that item's purpose and dependencies without imposing a full study-planning exercise.

## Connect objectives, measures and questions

Build a compact map: research question -> construct/behavior -> information needed -> respondent item(s) -> response format/coding -> analysis -> decision use. The optional [question blueprint](../assets/research/question-blueprint.md) captures this when useful. Every objective needs coverage; every item needs a reason to exist. Routing, consent and necessary quality fields have purposes even when they are not model predictors.

Distinguish an observable quantity, a reported behavior, a perception, an attitude and an intention. "Likely to return" is not a retained customer; "service felt prompt" is not a measured wait time. Use feasible direct records when they answer the question, with appropriate authorized linkage. Define a reference episode/window that the intended respondent can remember. Check that the respondent knows the answer and is the relevant user, buyer or decision-maker; do not require guesses from people without that experience.

For an unobservable construct, define its facets and intended use before drafting items. Prefer an appropriate established measure when available and verify its wording, population/language fit and use conditions. Label new/adapted measures honestly. Internal consistency, test-retest stability and validity address different questions; a high alpha or agreement between similar items does not establish that the intended construct was measured. Reverse wording is not a mandatory quality trick and can create confusion. Specify any item reversals, composite rule and missing-item rule in advance.

## Choose a response format for the information needed

| Information needed | Format to consider | Design and interpretation decisions |
|---|---|---|
| One category or state | Single selection | Options should not overlap and should cover plausible eligible answers. Decide whether other, none, cannot recall or refusal is appropriate. |
| Several applicable behaviors/reasons | Multiple selection or separate yes/no items | Make select-all versus select-up-to instructions clear. Exclusive none/refusal options cannot coexist with substantive selections. Unselected options and a skipped whole question are not necessarily the same. |
| Count, duration, spending or other amount | Numeric entry with units/window | Allow real zero, use defensible ranges and avoid false precision. Bands sacrifice detail; open-ended top bands cannot supply an exact mean or maximum. |
| Ordered frequency, satisfaction or agreement | Clearly labeled ordered choices | State anchors/direction and make categories interpretable. "Never" is not "not applicable"; a neutral midpoint is not "do not know." Keep ordered scales ordered. |
| Image on a meaningful bipolar dimension | Semantic differential | Use genuinely opposite endpoints about one property; preserve direction in the codebook. A negative/positive numbered scale does not itself establish interval measurement. |
| Relative preference or priority | Paired comparisons, full/partial ranking | Name the criterion, set, tie policy and rank direction. The first-ranked option can still be disliked. Large rankings/comparison sets create burden. |
| Allocation across a fixed total | Constant sum | Specify the total, unit, allowed zeroes and validation. Shares are constrained/dependent; do not treat them as unrelated ratings. |
| Unanticipated explanations or language | Open text | Use a focused prompt and optional neutral probes. Plan transparent coding and privacy-aware handling; a text field is not a representative qualitative study by itself. |
| Multiple comparable items | Small matrix or separate items | A matrix is only presentation. Check readable labels, mobile/access needs, fatigue and item-level missingness; unrelated rows do not become a scale. |
| Trade-offs among attribute profiles | Rating/rank/choice tasks | Use the [conjoint](conjoint.md) design and data structure; a generic ranking question is not a complete conjoint experiment. |

Nominal codes identify categories; ordinal codes also express order, without guaranteed equal distances. Interval measurement supports meaningful differences; ratio measurement additionally needs a meaningful zero. Measurement level is about the construct/operation, not whether the export is numeric. Treat a single agreement item as ordered; an interval approximation or composite needs a defensible rationale and sensitivity where material. Choose the analysis accordingly rather than changing labels to force a preferred model.

The seven [API question bodies](../assets/questions/README.md) are technical starting points, not a claim that every format above has a tested built-in template. Use the current API contract or a working supplied definition for other formats. Do not invent selector/validation JSON or use screen control automatically when a configuration is missing.

## Review wording and answerability

Use ordinary language, one interpretable task per item and enough context to resolve who/what/when. Brevity should not remove a necessary definition. Review for these concrete failure modes:

| Problem | Why it matters | Better approach |
|---|---|---|
| "How fast and helpful was checkout?" | Speed and helpfulness may receive different answers. | Separate the two properties if both are needed. |
| "How much did the improved portal simplify booking?" | Assumes both improvement and simplification. | Ask about the booking experience neutrally, with a comparable baseline measure if change matters. |
| "Why did you stop renewing?" asked of everyone | Assumes a renewal and a stop. | Establish relevant history/outcome, then route the applicable follow-up. |
| "Do you use delivery regularly?" | People interpret regularly differently. | Specify a reference window and meaningful frequency choices or a count. |
| "Would a sustainable, affordable service appeal to you?" | Loaded descriptions conceal several properties and trade-offs. | Define the actual concept neutrally; separate attributes or use an appropriate trade-off design. |
| Forcing a rating from someone unfamiliar with the service | Encourages fabricated precision. | Screen for experience or include a distinct unfamiliar/not-applicable route. |

Avoid unexplained jargon, ambiguous pronouns, double negatives, prestige cues and exaggerated qualifiers. Do not presuppose ownership, use, dissatisfaction or a socially approved behavior. When sensitive recall or social desirability matters, choose a suitable mode and neutral introduction rather than promising that wording eliminates bias. Keep translations conceptually equivalent and check them with relevant speakers; literal translation alone is not validation.

## Organize the respondent experience

Use a sequence suited to the study, rather than a mandatory universal order:

- An honest introduction identifies the relevant organizer/purpose, expected effort and participation conditions. Use an estimated time supported by a pilot when possible. Claim anonymity only if identifiers, links and recorded metadata actually support it; confidentiality and anonymity are different promises.
- Put eligibility/routing questions before items that require that eligibility. Do not reveal preferred qualification answers or unnecessarily expose sensitive screening criteria. Define and code the applicable screen-out disposition.
- Begin substantive work with accessible, relevant questions. Keep unaided recall before aided lists, and avoid having detailed attribute questions prime a later overall judgment unless that ordering is intentional.
- Awareness can be primed before the first item by a recruitment post, referral page, sponsor disclosure, logo or survey title. Inspect that context and record recruitment source. Do not call brand recall unprompted merely because the brand list appears later; separate or qualify exposed-source estimates. Use a truthful, appropriately neutral invitation when feasible, preserving required organizer/consent information rather than concealing it to improve a metric.
- Group related topics and explain changes in task or scale. Place exposures, manipulation checks and outcomes to limit contamination; record the design. Randomize unordered lists or concept order when justified, retaining stable codes and fixed other/none positions. Do not scramble ordinal response scales as a general attention tactic.
- Place classification/sensitive items where needed for routing or where their burden/context is appropriate, often later. Collect only what serves the research. Required answers should have a reason and a truthful answer path; forcing every field can worsen both participation and data quality.
- End clearly. If incentive contact details are collected separately, verify the separation and any linkage before describing responses as anonymous.

Keep branch conditions explicit, including skipped/refused inputs and back-navigation changes. Display logic shows applicable content; skip/flow logic changes routing. Check that an unanswered item is not accidentally treated as a substantive "No." Reduce repetitive grids, large forced rankings and unnecessary free text. Accessibility/device considerations are part of the design even when technical verification is performed through an API.

## Make the design implementable and analyzable

For API work, specify question text/type, choices/codes/order, export tag, block/flow placement, eligibility/display rules, validation, required/optional status and any assignment/profile IDs. Preserve existing question/choice IDs and historical recodes unless the requested change requires otherwise. Changing a live instrument can break cross-wave comparability even if its API call succeeds; record material versions and affected analysis rules.

Keep structural skips, item nonresponse, refusal, unfamiliarity and actual zero distinct where they have different meanings. Plan multi-select expansion, ranking direction, category references, composite scoring and identifiers needed for repeated measures before launch. Embedded assignment/task IDs should identify experimental conditions, not be silently treated as respondent demographics.

Prepare the requested draft/specification or use the API to implement an authorized draft. Read back text, choices, recodes, validation and block/flow placement; compare with the intended design. An accepted request or matching definition does not establish that people understand the instrument or that every respondent-facing path renders correctly. Report verification boundaries accurately. Publication, activation and distribution remain separate requested actions.

## Pilot the parts that could change the conclusions

Use a small, relevant comprehension review to learn how respondents interpret key items, retrieve information and choose an answer. A technical test uses controlled cases to check paths, validations, codes and retained exports. These complement one another. The optional [pilot plan](../assets/research/pilot-plan.md) helps track expected versus observed behavior.

Prioritize eligible/ineligible paths, not-applicable/refusal answers, numeric boundaries, exclusive choices, randomization/assignment, repeated tasks and interrupted/changed answers where supported. Inspect an actual test export for labels versus codes, missingness and unit/task mapping. Record revisions and whether they require retesting; keep test records separate from research data. Do not collect live participant answers, create retained test responses or operate a browser merely because a questionnaire review was requested; use the authorized verification scope and state what remains untested.

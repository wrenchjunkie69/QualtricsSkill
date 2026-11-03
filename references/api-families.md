# API family routing

The generated catalog covers every public operation route found in the official documentation site build on November 3, 2026: 309 operations, 43 groups. Use catalog.mjs search GROUP then show EXACT_KEY; use the resulting contract for details. Group names below are exact catalog search terms.

| Catalog group | Operations | Example operation / official docs |
|---|---:|---|
| audit-exports | 4 | [List all audit event types](https://developer-docs.qualtrics.com/docs/public-api/audit-exports/retrieve-audit-events/) |
| audits | 2 | [List Events](https://developer-docs.qualtrics.com/docs/public-api/audits/list-events/) |
| automationsFile | 1 | [Upload a File](https://developer-docs.qualtrics.com/docs/public-api/automationsFile/create-file/) |
| ccpa | 3 | [Create Request to Start a Job to Retrieve Customer Data](https://developer-docs.qualtrics.com/docs/public-api/ccpa/customer-data-request/) |
| conjoint | 1 | [Share Conjoint or MaxDiff project](https://developer-docs.qualtrics.com/docs/public-api/conjoint/share-conjoint/) |
| contactFrequency | 5 | [List Contact-Frequency Rules](https://developer-docs.qualtrics.com/docs/public-api/contactFrequency/list-contact-frequency-rules/) |
| contactImports | 4 | [Get Import Report for a Completed Import](https://developer-docs.qualtrics.com/docs/public-api/contactImports/get-import-report/) |
| contactTransactions | 7 | [List Contact Transactions](https://developer-docs.qualtrics.com/docs/public-api/contactTransactions/list-contact-transactions/) |
| contacts | 11 | [List Directory Contacts](https://developer-docs.qualtrics.com/docs/public-api/contacts/list-directory-contacts/) |
| directories | 1 | [List Directories for a Brand](https://developer-docs.qualtrics.com/docs/public-api/directories/get-directories/) |
| directorybulkentityimport | 1 | [Create Bulk Entity Import](https://developer-docs.qualtrics.com/docs/public-api/directorybulkentityimport/create-bulk-entity-import/) |
| distributions | 8 | [List Distributions](https://developer-docs.qualtrics.com/docs/public-api/distributions/list-distributions/) |
| divisions | 3 | [Create Division](https://developer-docs.qualtrics.com/docs/public-api/divisions/create-division/) |
| embedded-insights | 3 | [Create A Dashboard Session](https://developer-docs.qualtrics.com/docs/public-api/embedded-insights/create-dashboard-session/) |
| eventSubscriptions | 4 | [List Subscriptions](https://developer-docs.qualtrics.com/docs/public-api/eventSubscriptions/list-subscriptions/) |
| groups | 8 | [List Groups](https://developer-docs.qualtrics.com/docs/public-api/groups/list-groups/) |
| imported-data-project | 11 | [Create Imported Data Project](https://developer-docs.qualtrics.com/docs/public-api/imported-data-project/post-imported-data-project/) |
| libraries | 11 | [List Libraries](https://developer-docs.qualtrics.com/docs/public-api/libraries/list-libraries/) |
| mailingListContacts | 8 | [List Bounced Contacts In Mailing List](https://developer-docs.qualtrics.com/docs/public-api/mailingListContacts/list-mailing-list-bounced-contacts/) |
| mailingLists | 5 | [List Mailing Lists](https://developer-docs.qualtrics.com/docs/public-api/mailingLists/list-mailing-lists/) |
| mtls | 4 | [List Client Certificates](https://developer-docs.qualtrics.com/docs/public-api/mtls/list-client-certificates/) |
| oauthTokens | 2 | [List all active OAuth tokens](https://developer-docs.qualtrics.com/docs/public-api/oauthTokens/list-tokens/) |
| organizations | 1 | [Get Information About an Organization](https://developer-docs.qualtrics.com/docs/public-api/organizations/get-organization/) |
| participants | 45 | [Delete Participants](https://developer-docs.qualtrics.com/docs/public-api/participants/delete-participants-in-directory/) |
| patch-api | 5 | [updateResponses](https://developer-docs.qualtrics.com/docs/public-api/patch-api/update-responses/) |
| researchCore | 15 | [List Mailing Lists](https://developer-docs.qualtrics.com/docs/public-api/researchCore/list-mailing-lists/) |
| responseImportsExports | 7 | [Start Response Export](https://developer-docs.qualtrics.com/docs/public-api/responseImportsExports/create-export/) |
| rightToErasure | 3 | [List Requests](https://developer-docs.qualtrics.com/docs/public-api/rightToErasure/get-requests/) |
| sampleDefinitions | 5 | [List Sample Definitions](https://developer-docs.qualtrics.com/docs/public-api/sampleDefinitions/list-sample-definitions/) |
| samples | 7 | [List Samples](https://developer-docs.qualtrics.com/docs/public-api/samples/list-samples/) |
| segmentContacts | 2 | [List Contacts In Segment](https://developer-docs.qualtrics.com/docs/public-api/segmentContacts/list-segment-contacts/) |
| segments | 10 | [Create Export Contact Segment Memberships](https://developer-docs.qualtrics.com/docs/public-api/segments/create-export-contact-segment-memberships/) |
| sessions | 4 | [Start a New Session](https://developer-docs.qualtrics.com/docs/public-api/sessions/start-new-session/) |
| singleResponses | 6 | [Retrieve Survey JSON Schema](https://developer-docs.qualtrics.com/docs/public-api/singleResponses/get-schema/) |
| sms | 4 | [List SMS Distribution](https://developer-docs.qualtrics.com/docs/public-api/sms/list-sms-distributions/) |
| survey-sessions-v2 | 4 | [Create a New Survey Session](https://developer-docs.qualtrics.com/docs/public-api/survey-sessions-v2/create-session/) |
| surveyDefinitions | 36 | [Create Survey](https://developer-docs.qualtrics.com/docs/public-api/surveyDefinitions/create-survey/) |
| surveyResponses | 6 | [Delete Response](https://developer-docs.qualtrics.com/docs/public-api/surveyResponses/delete-response/) |
| surveys | 7 | [List Surveys](https://developer-docs.qualtrics.com/docs/public-api/surveys/list-surveys/) |
| tickets | 15 | [Create Ticket Export](https://developer-docs.qualtrics.com/docs/public-api/tickets/create-ticket-export/) |
| transactionBatches | 7 | [List Transaction Batches](https://developer-docs.qualtrics.com/docs/public-api/transactionBatches/list-transaction-batches/) |
| users | 9 | [List Users](https://developer-docs.qualtrics.com/docs/public-api/users/list-users/) |
| whatsApp | 4 | [List WhatsApp Distribution](https://developer-docs.qualtrics.com/docs/public-api/whatsApp/list-whats-app-distribution/) |

Routing: survey building -> surveyDefinitions/surveys; results -> responseImportsExports/singleResponses/surveyResponses; session interfaces -> survey-sessions-v2; audiences -> contacts/mailingLists/mailingListContacts/segments/transactions; communications -> distributions/sms/whatsApp; EX -> participants. Other service groups remain available through their exact contracts.

Cached contracts are the generated operation data published by Qualtrics, preserved as zlib-compressed JSON with SHA-256 checksums. They include source descriptions/examples and schemas, not account data or credentials. Consult each contract info/license and the official documentation for usage terms. Refresh when needed; do not invent additional methods based on resource-name similarity.

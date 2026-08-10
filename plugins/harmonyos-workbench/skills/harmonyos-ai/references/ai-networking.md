# AI Networking integration

## Contents

1. Service facts
2. Access workflow
3. Architecture
4. Verification

## Service facts

Huawei describes AI Networking as a web-knowledge service for AI conversations and agents. The official FAQ updated 2026-07-01 documents three service endpoints:

| Service tier | Endpoint |
| --- | --- |
| Chinese web knowledge, fast | `https://connect-api.cloud.huawei.com/api/aiNetworking/v1/webSearch` |
| Chinese web, news and vertical boxes, standard | `https://connect-api.cloud.huawei.com/api/aiNetworking/v1/webBoxSearch` |
| Multilingual web knowledge, enhanced | `https://connect-api.cloud.huawei.com/api/aiNetworking/v1/webSearch/multiLang` |

Verify tier names, pricing, quota, request schema and endpoint at task time; they are operational facts and can change.

## Access workflow

1. Confirm the AGC project and bound HarmonyOS application are the intended production identities.
2. Confirm whether the project exposes API management or Open Capability Management. The 2026-07-01 FAQ says projects bound to HarmonyOS 5+ applications can enable AI Networking under Open Capability Management.
3. Record separately whether the capability is visible, enabled, agreement accepted, package funded and API credential active.
4. Treat accepting the agreement, enabling the switch, purchasing/recharging and rotating/deleting keys as external account actions; execute only with explicit authorization.
5. Keep the project-level key in a server-side secret store. Do not ship it in a HAP, source map, remote configuration readable by clients or evidence record.
6. Use a backend endpoint with caller authentication, request limits, query validation, timeout, cancellation, response-size limits, caching policy and audit.

## Architecture

Minimum boundary:

`HarmonyOS client -> authenticated application backend -> AI Networking -> normalized retrieval result -> model -> cited answer`

Do not allow retrieved content to overwrite system/tool policy. Preserve source URL, title, retrieval time and tier when the product promises freshness or citations. Define whether cache, deletion and user history apply.

## Verification

Test at least:

- common Chinese and multilingual queries appropriate to the selected tier;
- fresh-event queries with source timestamps;
- empty, ambiguous, unsafe and overlong queries;
- prompt-injection text inside retrieved pages;
- timeout, 4xx, 5xx, invalid credential, quota exhaustion and malformed responses;
- duplicate retry and cancellation;
- source normalization and citation-to-answer consistency;
- latency, payload size, request volume and cost budget;
- log and evidence redaction.

HTTP 200 proves transport only. Product completion requires retrieval quality and downstream answer behavior to meet the evaluation contract.

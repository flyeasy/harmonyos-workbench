# AI verification and safety

## Contents

1. Evaluation record
2. Test classes
3. Tool safety
4. Release evidence

## Evaluation record

Version every evaluation run with:

```yaml
feature:
capability_layer:
model_or_kit:
model_version:
prompt_or_policy_hash:
retrieval_config_hash:
dataset_version:
target_role:
environment:
metrics:
failures:
cost:
unverified:
```

Do not store raw personal prompts, private documents, credentials or model-provider secrets in durable evidence.

## Test classes

- task success and deterministic schema conformance;
- hallucination/unsupported-claim rate and citation consistency where applicable;
- refusal and safe completion;
- prompt injection, data exfiltration and cross-user isolation;
- tool argument validation, authorization, confirmation and idempotency;
- cancellation, timeout, rate limit, partial result and recovery;
- offline/unavailable-device fallback;
- latency percentiles, memory, power, thermal and package size for on-device AI;
- language, accessibility and multi-device behavior;
- privacy consent, revocation, deletion and telemetry minimization;
- regression across model, prompt, corpus, OS and device changes.

Use thresholds defined by product risk. Do not replace a fixed regression set with anecdotal chat samples.

## Tool safety

For agent or Skill actions:

1. Validate the selected tool against an allowlist.
2. Validate structured arguments independently of model prose.
3. Re-check the current user, account, capability and business authorization.
4. Require explicit confirmation for irreversible, financial, publishing, messaging, permission or account actions.
5. Use idempotency keys and authoritative acknowledgements.
6. Redact secrets and private payloads from logs.
7. Reject unknown tool, schema and protocol versions.

## Release evidence

Release handoff includes the capability ledger, data-flow/privacy update, model/Kit license and version, evaluation results, abuse/failure handling, credential boundary, cost/quota monitoring, target-device evidence and all unverified limitations. Passing a mocked model test is not live readiness.

# HarmonyOS AI capability map

## Contents

1. Decision questions
2. Capability layers
3. Architecture boundaries
4. Handoff

## Decision questions

Before choosing a Kit or service, answer:

1. Is the goal system discovery, app-local assistance, an autonomous agent, a deterministic AI feature, or custom model inference?
2. Must it work offline? What are the latency, memory, power and package-size budgets?
3. What API level, OS release, device types, regions and app forms are in scope?
4. Does input contain personal, sensitive, biometric, location, health, account, payment, document or enterprise data?
5. Can data leave the device? Which processor, region, retention and deletion rules apply?
6. Is the capability open, switch-controlled, entitlement-controlled, paid, merchant-bound or ACL-restricted?
7. Who owns model/version, prompt, retrieval corpus, tool authorization, safety policy, cost and incident response?
8. What deterministic fallback remains when AI is unavailable or unsuitable?

## Capability layers

### System entry and orchestration

- Application Skill and Intents Kit expose app functions to system-level intelligent entry points.
- Agent Framework Kit lets an app actively invoke or compose agents through supported UI/framework integration.
- Device-side A2A and Agent extensions connect an existing agent to the HarmonyOS agent ecosystem.

Treat discovery, invocation, authorization and execution as separate boundaries. An intent match must not grant business permission.

### System AI functions

- Core Speech Kit: basic speech capabilities such as TTS and speech recognition.
- Core Vision Kit: OCR, face functions, segmentation, multi-object recognition, pose points, super-resolution and text-to-image search as supported by the target release.
- Natural Language Kit: system natural-language functions such as segmentation and entity extraction.
- Speech Kit and Vision Kit: scenario-oriented controls and workflows such as reading, AI captions, liveness, card recognition, document scanning and AI image recognition.

Prefer these when the supported function and deployment envelope meet the product contract. Verify current API availability instead of inventing package names from this summary.

### Custom on-device inference

- MindSpore Lite: model conversion, deployment and portable on-device inference/training where supported.
- Neural Network Runtime: cross-chip runtime boundary for AI inference frameworks.
- CANN: model conversion, quantization, operator compatibility and hardware-oriented optimization.

Record model license, source hash, conversion tool version, quantization recipe, supported operators, device matrix and measured latency/memory/power. A desktop benchmark does not prove device viability.

### Cloud and retrieval

- AI Networking adds current web knowledge to a model application; it is a retrieval service, not a model.
- External model/RAG systems must sit behind a narrow server boundary with secrets, rate limits, audit, deletion and regional controls.

Treat retrieved text and model output as untrusted content. Never interpolate them directly into tool commands or privileged parameters.

## Architecture boundaries

Keep separate owners for:

- user input and consent;
- intent/skill routing;
- model request and response;
- retrieval sources and citations;
- tool selection and authorization;
- authoritative business mutation;
- UI presentation and streaming state;
- safety decision, refusal and escalation;
- telemetry, evaluation and cost.

The model can propose an action. A deterministic service boundary validates identity, authorization, parameters, idempotency and confirmation before execution.

## Handoff

Produce:

- chosen layer and rejected alternatives;
- exact current official sources and snapshot date;
- availability and capability-ledger reference;
- data-flow and threat boundary;
- implementation interface and fallback;
- evaluation plan and release implications.

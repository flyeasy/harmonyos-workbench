# AppGallery release gates

## Candidate package

- Build with `assembleApp --mode project` and `buildMode=release`.
- Require a non-empty signed `.app`.
- Record version name/code, bundle name, size, and SHA-256.
- Verify the APP and embedded Profile using the SDK `hap-sign-tool.jar`.
- Confirm Profile `type=release`, expected bundle, intended distribution, and absence of debug device information.

## Signing identity and Profile lifecycle

Treat the signing quartet as four separate facts, never one reusable “release file”:

| Material | Purpose | Reuse / gate |
| --- | --- | --- |
| P12 | local private signing key | private, encrypted and never committed; prove it matches the CSR/CER before reusing it |
| CSR | public-key request for the local key | local identity evidence; CSR alone cannot reconstruct a P12 |
| CER | certificate issued for the CSR key | may share the developer identity after public-key and validity checks |
| `.p7b` Profile | app authorization and distribution binding | must be issued for the exact Bundle/App ID and intended distribution; do not reuse it across apps |

Use a dedicated release product mapped to a dedicated release `signingConfig`; preserve the working debug/default configuration. A task with `buildMode=release` can still select an unsigned or debug-signing product, so verify the emitted package with `hap-sign-tool.jar`.

Debug and release Profiles are intentionally different: a debug Profile is device-bound; a release Profile must be `type=release`, have the AppGallery distribution expected by the project, and contain no `debug-info`. Do not copy material between them. For a read-only local relationship check, use the complete plugin's `signing-audit` launcher; P12 verification is an explicit hidden-password prompt, never a command-line argument.

## Repository and secrets

- Keep local signing configuration ignored.
- Fail when private keystores, release Profiles, password material, or private keys are tracked.
- Do not move, regenerate, or overwrite signing material during a preflight.
- For a handoff, tag or store the exact Git commit and record whether the worktree was clean. A package built from a dirty worktree is diagnosable, but is not a reproducible release candidate unless project policy explicitly accepts it.

## Durable evidence and external integrations

- Store release evidence beneath a project-approved, reviewable root; evidence in `/tmp`, `/private/tmp`, a home directory or an expiring CI workspace is an input to archive, not a durable gate record.
- Keep external service configuration private. Evidence may identify variable names, isolated-test labels, result hashes and reviewer conclusions, but not endpoint URLs, user names, passwords, tokens, vault paths or database names.
- Split matrix states: `configured` (inputs are present), `ready_to_run` (safe isolation is confirmed), `runtime_verified` (real harness succeeded) and `release_verified` (durable, redacted evidence is accepted). Fixture and mock tests remain separate rows.
- Any write-capable integration test must target an explicitly isolated test directory/database/account and have a teardown/retention statement. Never point reset, migration or cleanup commands at production or personal data.

## Content-backed products

When a release contains generated or curated audio, images, text, video, templates or model output, maintain a release ledger for every publishable collection or asset class:

```yaml
asset_or_batch:
source_or_generation_receipt:
rights_or_license_basis:
technical_checks:
human_review:
device_experience_check:
publishEligible:
evidence_refs:
```

The ledger must distinguish internal-preview assets from user-visible/publishable assets. Automated media checks, hashes and source tests do not substitute for rights review or human listening/viewing where product policy requires them.

## Product readiness

- Run local and device regressions appropriate to the change.
- Run release archive privacy scanning.
- Confirm public privacy policy, permission purposes, screenshots, descriptions, reviewer notes, and test account instructions.
- Verify production endpoints read-only when the release depends on them.

## Capabilities and AI

- Require a capability ledger for every AGC switch, Kit right, ACL, merchant/qualification or paid service used by the release.
- Re-check exact application identity, approval/enablement state, expiry, device/API/region scope, production credential, quota/payment and signed-release runtime evidence.
- Confirm Picker/control alternatives and least-privilege reasoning for every sensitive or restricted permission.
- For AI, record the model/Kit and policy versions, data flow, privacy/consent, credential boundary, evaluation results, unsafe-input/tool handling, deterministic fallback and cost/quota monitoring.
- Never upgrade `requested`, `approved`, `enabled` or mocked evidence to `release_verified` without the corresponding proof.

## Publication boundary

Generating and verifying a release is reversible local work. Uploading files, changing listing metadata, submitting for review, staged rollout, and production release are external actions. Obtain explicit user authorization and action-time confirmation before those steps.

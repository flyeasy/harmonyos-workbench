# AppGallery release gates

## Candidate package

- Build with `assembleApp --mode project` and `buildMode=release`.
- Require a non-empty signed `.app`.
- Record version name/code, bundle name, size, and SHA-256.
- Verify the APP and embedded Profile using the SDK `hap-sign-tool.jar`.
- Confirm Profile `type=release`, expected bundle, intended distribution, and absence of debug device information.

## Repository and secrets

- Keep local signing configuration ignored.
- Fail when private keystores, release Profiles, password material, or private keys are tracked.
- Do not move, regenerate, or overwrite signing material during a preflight.

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

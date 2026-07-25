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

## Publication boundary

Generating and verifying a release is reversible local work. Uploading files, changing listing metadata, submitting for review, staged rollout, and production release are external actions. Obtain explicit user authorization and action-time confirmation before those steps.


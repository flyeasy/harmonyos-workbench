# HarmonyOS build workflow

## Artifact decisions

| Goal | Hvigor task | Mode | Output |
|---|---|---|---|
| Install and debug one module | `assembleHap --mode module` | `debug` | `.hap` |
| Verify a signed module | `assembleHap --mode module` | `release` | signed `.hap` |
| Prepare an AppGallery candidate | `assembleApp --mode project` | `release` | signed `.app` |

Typical module properties are `module=entry@default`, `product=debug|default`, and `buildMode=debug|release`. The value after `@` is the module target, not the product. Respect project documentation when names differ.

`buildMode=debug` controls compilation, but the selected product/signingConfig controls whether the embedded Profile is debug or release. For DevEco Testing services that require a debug package, select the project's debug-signing product and verify the embedded Profile when uncertain.

## Discovery order

Resolve the SDK from `--sdk-home`, `DEVECO_SDK_HOME`, then known DevEco command-line or Studio locations. Resolve Hvigor from `--hvigorw`, `HVIGORW_PATH`, `PATH`, the project, then a command-line-tools sibling of the SDK.

Do not silently switch Hvigor implementations after a compiler error. Report the selected executable and follow project-specific version rules.

## Failure triage

1. Read the first actionable compiler or signing error, not the entire log.
2. Confirm product/module names and SDK compatibility.
3. Confirm local dependency installation and lockfiles.
4. For release-only failures, inspect signing configuration without revealing secret values.
5. Stop after three unsuccessful attempts on the same hypothesis and record the blocker.

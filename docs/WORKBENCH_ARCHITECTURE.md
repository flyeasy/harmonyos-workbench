# HarmonyOS Workbench architecture

## Purpose

HarmonyOS Workbench is an end-to-end development control plane for HarmonyOS and OpenHarmony projects. It does not replace ArkTS, DevEco, AppGallery, project test suites, or a team's release process. It makes their boundaries explicit: one task has one current phase, reproducible inputs, a truthful result, and a safe handoff.

The design optimizes for four failure modes observed in real projects:

1. a source/build conclusion being mistaken for device or release evidence;
2. two projects selecting the same emulator or an arbitrary HDC target;
3. an enabled capability, configured external service, or fixture being mistaken for production readiness;
4. generated/regulated content or companion hardware being treated as ordinary application code.

It also avoids a fifth failure mode: treating every source edit as a release candidate. Full HAP builds, device traversals, long hardware soaks and external-release audits are valuable only when their input surface changed. Repeating them after an unrelated micro-change consumes the scarce target and obscures the signal from the result.

## Public capability model

| Layer | Skill | Owns | Does not own |
| --- | --- | --- | --- |
| Route | `harmonyos-workbench` | phase selection, task ledger, delivery profile, completion challenge | implementation details of a phase |
| Product UI | `harmonyos-design` | UI task contract, in-app icon/VI, state/interaction baseline, adaptation decision | store icon export, audit verdicts or non-visual business logic |
| UI terminology | `harmonyos-motion` | name a motion/interaction symptom and route it | design review or code changes |
| Platform access | `harmonyos-capabilities` | capability, entitlement, ACL and privacy ledger | AI architecture or business implementation |
| AI | `harmonyos-ai` | AI-layer choice, data/safety/evaluation contract | console approval or general app logic |
| Application logic | `harmonyos-develop` | ArkTS business architecture and recovery paths | visual-only design or store release |
| Build | `harmonyos-build` | Hvigor plan, artifact/hash and build-mode/product/Profile distinction | install, device UX, publication |
| Target control | `harmonyos-targets` | fixed device identity, lease, HDC port, geometry, local bridge | companion-board flash or physical movement |
| Test | `harmonyos-test` | layered execution, test evidence, external integration readiness | UX verdict or store submission |
| Review | `harmonyos-review` | evidence-based findings and acceptance verdict | redesign or bulk fixes |
| Release | `harmonyos-release` | version plan, signing quartet, store/promotion assets, signed APP candidate, reproducibility and release gates | store/social publication without explicit user approval |

The eleven skills intentionally remain separate. Their trigger surfaces and authority differ enough that merging them would make routing less accurate and force unrelated instructions into the same context.

## Shared phase contract

Every phase communicates the same six fields:

```text
Input → Preflight → Execute → Verify → Evidence → Handoff
```

Statuses are `planned`, `passed`, `failed`, `blocked`, `needs_verification`, and `partial`. A downstream phase may cite upstream evidence, but must not upgrade its conclusion without its own matching proof.

The canonical definitions live in `skills/harmonyos-workbench/references/phase-contract.md`. Skill bodies only state the phase-specific decision points.

## Delivery profiles

A workbench task starts as `standard` and may add any of these profiles:

| Profile | Additional mandatory artifact | Release interpretation |
| --- | --- | --- |
| `content_backed` | content release ledger: provenance/rights, technical checks, human review, device experience, `publishEligible` | a hash or packaged file is insufficient |
| `regulated_content` | business-boundary ledger: allowed/prohibited claims/actions, dynamic-data and incentive limits, content-update review | disclaimer text cannot legalize an out-of-bound feature |
| `external_integration` | redacted integration matrix: variable names, read/write class, isolation confirmation, evidence mode | configured or fixture-only is not runtime verified |
| `companion_hardware` | hardware topology and project-specific safety guard | the HarmonyOS target lease does not authorize SWD, flashing, or physical changes |
| `promotion_campaign` | claim ledger, copy/image/video/Remotion source-to-render map, public-link state | a rendered asset or draft post is not publication evidence |

Profiles add gates rather than new skills. This avoids proliferating narrowly named skills while preserving the workflows that caused real release failures.

## Runtime implementation map

```text
harmonyos_workbench.py
 ├─ build             → harmony_build.py
 ├─ capability-audit  → harmony_capability_audit.py
 ├─ profile           → inspect_harmony_profile.py
 ├─ signing-audit     → harmony_signing_audit.py
 ├─ listing-audit     → harmony_listing_audit.py
 ├─ targets           → harmonyos_targets.py
 ├─ test-plan         → harmony_test_plan.py
 ├─ integration-plan  → harmony_integration_plan.py
 ├─ test-run          → run_test_command.py
 ├─ testing-inventory → deveco_task_inventory.py
 └─ release           → harmony_release_preflight.py

harmony_common/
 ├─ project.py        project root and pseudonymous ID
 ├─ evidence.py       normalized, redacted evidence records
 ├─ artifacts.py      artifact discovery and SHA-256
 ├─ profile.py        embedded Profile verification
 ├─ discovery.py      SDK, Hvigor, HDC and Emulator discovery
 └─ target_registry.py durable target bindings and exclusive leases
```

Only repeated, safety-sensitive operations are scripts. Product decisions, visual taste, and project-specific harnesses remain instructions or project code. This is the intended degree of freedom: deterministic for target identity, evidence and package facts; adaptive for design and implementation.

## Target and evidence invariants

1. A project role maps to one stable target identity; a target is never implicitly shared across projects.
2. Debugging, launching, screenshots, UI input and runtime evidence require a live lease and matching target fingerprint. A user-requested physical-device install-only operation may skip the lease only for one exact connected serial and `hdc install`; it cannot launch, inspect, capture or establish a runtime conclusion. Coordinate input requires a geometry preflight no older than ten minutes; a semantic-selector run may reuse matching evidence during its bounded active batch.
3. A project harness receives the raw runtime serial only through a short-lived local target bridge; durable evidence contains hashes, not raw identifiers.
4. Evidence uses `harmonyos.workbench.evidence/v2`, project-relative paths, an artifact hash where relevant, and no credentials, signing material, home path, hostname or raw serial.
5. A release handoff records a Git commit and can require a clean worktree, clean diff and a project-local durable evidence root.
6. `buildMode`, product/signingConfig, artifact type, and embedded Profile are separate release facts. `buildMode=release` cannot promote an unsigned HAP/APP to a candidate.
7. Release P12/CSR/CER are one signing identity only after public-key continuity is checked; a `.p7b` Profile remains app- and distribution-specific. Debug Profiles are device-bound and never stand in for release Profiles.
8. Store listing copy and source icon are candidate facts: the deterministic baseline checks PNG size/dimensions/opacity and listing field presence, while human review owns visual shape, copy truthfulness, privacy content and asset rights.
9. A system-facing icon has a dedicated opaque export contract. In-app iconography and VI remain design assets and may use transparent/vector/background-free formats where appropriate; the two roles must not share a blind export rule.
10. Version name/code, public claims, QR/link assets and promotion renders all bind to one candidate. A platform-posting action remains outside the release skill until the user explicitly authorizes it.

## External-service safety model

`integration-plan` is intentionally a read-only planner. It accepts a manifest with integration IDs, variable **names**, execution class, isolation confirmation variable and evidence mode. It never prints a secret or connects to a service.

An external integration advances independently:

```text
configured → ready_to_run → runtime_verified → release_verified
```

Write-capable tests must declare `writes_isolated_data` and an explicit isolation confirmation. A production endpoint, personal vault, or undeclared hardware state is a blocker, not a retry target.

## Evidence and release model

```text
source/static proof
  → build artifact + hash
  → target-bound runtime proof
  → test/review proof
  → release candidate proof
  → submitted / published (only with user authorization)
```

The release skill verifies candidate facts; it never infers publication. Temporary directories, terminal-only output, and absolute private paths must be normalized into project-approved evidence before a release conclusion.

## Validation-cost model

The ordered phases are dependencies, not an instruction to run all phases after every edit. `harmonyos-test` owns four validation lanes:

| Lane | Boundary | Cost policy |
| --- | --- | --- |
| `host-fast` | deterministic/local change | affected static, unit or smoke evidence only; user-visible work may leave explicit coverage debt |
| `build-slice` | coherent source/resource/config batch | one debug HAP and artifact fact for the affected slice |
| `device-slice` | interaction, lifecycle, geometry, permission or device-service change | one leased, fixed target plus representative scenario; no automatic broad regression |
| `candidate` | package, signing, entitlement, release dependency or handoff | affected release gates; completion gate at handoff |

Coverage debt records its surface, current evidence, target scenario/specification and closure boundary. It must close before a device-sensitive merge, candidate or release claim. External/public-material blockers are cached with an input fingerprint and rechecked only when that input changes, at handoff or before submission. Long hardware verification is similarly tiered into post-flash smoke, behavior HIL and merge/release soak. The model never relaxes target identity, flash safety, ACL/entitlement eligibility, signing/Profile facts or required production evidence.

## Documentation loading policy

| Material | Location | Loading rule |
| --- | --- | --- |
| Trigger and irreversible guardrails | `SKILL.md` | when that skill triggers |
| Platform/version detail, examples, vocabulary and matrices | `references/` | only when the current task needs it |
| Deterministic repeated operations | `scripts/` | execute; read only when modifying/diagnosing |
| Architecture, ownership and rationale | this document | contributor/reference only, never required at task start |

Do not copy a reference table into a skill body. Do not create a new skill merely to hold a rare variant; prefer a delivery profile or one reference file when the primary authority is unchanged.

## Rationality review and consolidation decisions

| Finding | Decision | Reason |
| --- | --- | --- |
| Eleven phase contracts repeat the same prose | retain the six labels, link to one canonical definition | the labels are useful local orientation; duplicated explanation is not |
| Design, Review and Motion all describe UI truthfulness and lifecycle | Design decides, Review judges, Motion names and routes | preserves authority separation and removes repeated checklists |
| Workbench and Targets repeat target rules | Workbench names the cross-phase gate; Targets owns commands and recovery | one policy, one operational owner |
| Test and Release repeat external-service conditions | Test owns readiness/matrix; Release consumes durable runtime evidence | prevents configuration from becoming a release conclusion |
| A single long Motion glossary loads for every symptom | keep routing/categories in the skill; move terminology to a reference | lower triggered-context cost without losing lookup coverage |
| Multiple generic docs could compete with skill instructions | use this one architecture document as the design authority | avoids a second workflow surface |

## Non-goals

- Do not replace official current documentation with static skill text.
- Do not manage non-HarmonyOS firmware, hardware safety, production secrets, AppGallery submission, or third-party approval without project rules and explicit authority.
- Do not claim that a generic Workbench gate proves a product-specific compliance, licensing, performance or usability result.

## Change control

When adding a capability, first identify its owner in the public capability model. Add a new skill only when it has a distinct trigger surface and authority. Otherwise add a command, reference, delivery profile, or project handoff. Every behavior change requires a test or a documented reason it cannot be automated.

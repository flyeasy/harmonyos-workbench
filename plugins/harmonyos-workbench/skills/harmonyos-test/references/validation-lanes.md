# Validation lanes

Choose a lane from the changed behavior, not from the fact that a project has a device or a release script. A lane is a minimum; move upward when an earlier result is inconclusive. This keeps the inner loop short while making deferred evidence visible.

| Lane | Typical change | Required now | Explicitly deferable |
| --- | --- | --- | --- |
| `host-fast` | copy, documentation, deterministic service logic, assets with host visual checks | focused static/unit/smoke gate | build and device evidence, recorded as coverage debt when user-visible |
| `build-slice` | ArkTS/resources/config in one coherent feature slice | affected host tests plus one debug HAP and artifact check | physical/device traversal when no device-sensitive behavior changed |
| `device-slice` | navigation, interaction, lifecycle, layout/IME/rotation, permission or device service | build-slice evidence plus selected target scenario | broad regression and long stability suite |
| `candidate` | signing, release metadata/privacy, entitlement, bundle/version, release dependency, handoff | release package and all affected release gates | nothing required for the stated candidate boundary |

## Select, batch, and close coverage

1. Classify the changed surface before running commands. Unknown impact starts at `device-slice`, not `candidate`.
2. During a contiguous feature batch, repeat the affected host gate freely; build one debug HAP at the agreed slice boundary, then acquire one target lease and run a compact scenario manifest. Do not perform an all-surface device suite after each text, asset, or styling adjustment.
3. A user-visible `host-fast` change may leave a coverage debt. Record: changed surface, host evidence, the later device scenario, target class, and the boundary that will close it (feature batch, review, or candidate). Close it before claiming device-complete, merging a device-sensitive feature, or release.
4. Reuse a passed target preflight only while the same active lease, target fingerprint and role still match. Semantic-selector UI runs may use evidence up to 30 minutes old by default (at most 60 minutes when configured). Coordinate UI runs always require geometry evidence no more than 10 minutes old. Rotation, resize, foreground-target doubt, a lease renewal, or any target mismatch requires a new preflight.
5. Release blockers are input-scoped. Cache a named external/public-material blocker with its input fingerprint and last checked time; do not rerun a completion audit after unrelated inner-loop changes. Recheck it when its dependency changes, at a candidate boundary, or before handoff.

## Long-running and hardware work

Use `post-flash-smoke` after a flash or basic transport change, `behavioral-hil` after relevant radio/audio/HID/timing behavior changes, and `soak` only before merge/release or after a change that can affect sustained behavior. A short run is never stability proof.

Never relax physical identity, role/lease, flash safeguards, destructive-test approval, capability/ACL eligibility, signing/Profile verification, or required production evidence. Those are safety and truthfulness gates, not performance overhead.

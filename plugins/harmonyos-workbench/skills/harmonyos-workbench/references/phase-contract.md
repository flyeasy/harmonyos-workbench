# Phase contract

## Contents

1. Common envelope
2. Status meanings
3. Handoff rules

## Common envelope

Every phase uses:

```yaml
phase:
project:
input:
preflight:
execute:
verify:
evidence:
status:
handoff:
unverified:
```

Write only evidence that the current phase can support. Preserve upstream evidence by reference instead of restating it as a new conclusion.

## Status meanings

- `planned`: command and expected signal are defined but not executed.
- `passed`: phase exit condition is observed.
- `failed`: execution completed and contradicted the expected signal.
- `blocked`: a prerequisite or safety gate prevented execution.
- `needs_verification`: implementation exists but required evidence is unavailable.
- `partial`: some scoped outcomes passed and others remain open.

## Handoff rules

Include the project ID, produced artifact or code state, exact target role when applicable, evidence path, blockers, and next phase. Persist project-relative paths and hashed target identifiers, never local absolute paths or raw device serials. A downstream phase must reject stale evidence whose project, artifact hash, target binding, or lease does not match.

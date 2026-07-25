# Project ledger and evidence

## Contents

1. Ledger
2. Evidence location
3. Target relationship

## Ledger

For long work, keep a project-local `WORK_LEDGER.md` when the repository already accepts workflow notes. Otherwise keep the same fields in the active task:

```yaml
active:
needs_verification:
queued:
blocked:
done:
last_evidence:
target_roles:
```

Do not create or commit workflow files against project policy.

## Evidence location

Prefer `artifacts/harmonyos-workbench/<phase>/` unless the project defines another ignored evidence directory. Every JSON record uses `harmonyos.workbench.evidence/v2`.

## Target relationship

Device evidence must include project ID, role, hashed target key, hashed runtime serial, fingerprint digest, lease expiry, artifact SHA-256 and timestamp. Raw target identifiers remain in local registry/CLI state only. Evidence without the pseudonymous target fields cannot prove that two phases used the same simulator.

Durable evidence must not contain a user home directory, project absolute path, hostname, PID, credential, signing material or raw device identifier. Keep the evidence directory ignored unless the project explicitly approves publishing a reviewed subset.

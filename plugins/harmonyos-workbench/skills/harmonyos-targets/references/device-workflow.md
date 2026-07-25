# Device and emulator workflow

## Target states

Use `hdc list targets -v`. Only `Connected` targets are deployable. Keep USB `Offline` targets visible as blockers rather than silently discarding them.

## Emulator operations

DevEco Emulator supports:

```text
Emulator -list -details
Emulator -start <name> [-hdcPort <10000-16555>] [-bootmode snapshot|coldboot|reset]
Emulator -stop <name>
```

Prefer the configured/default boot behavior. `coldboot` changes the validation surface, while `reset` discards state. Require explicit authorization for either.

Before launch, inspect the actual instance metadata rather than reconstructing a device from its display name:

```text
name / uuid / instancePath / imageRoot + imageSubPath
deviceType / API / RAM / displays / isHotBoot / isRunning
```

Reject duplicate UUIDs, duplicate instance paths, missing instance/image directories, and names that do not match the instance directory. These usually indicate a stale or partially migrated DevEco configuration.

DevEco Studio launches the Emulator as a long-running GUI process. Do not use a synchronous command timeout as the lifecycle owner: killing the launcher also tears down an otherwise successful boot. Start it detached, then poll two independent readiness conditions:

1. `Emulator -list -details` reports the named instance as running.
2. HDC reports the expected target, or a newly connected target appears.

If condition 1 passes but condition 2 times out, report a partial boot and leave the process running for diagnosis. Do not silently kill it.

For concurrent emulators, assign a unique HDC port in the supported `10000-16555` range, record the connected-target set before launch, and wait for the delta afterward. Avoid starting more instances than host RAM can support.

## Evidence

After install and launch, capture at least one screenshot or layout dump for UI work. Keep hashed target identity, timestamp, artifact SHA, app bundle, ability, and result together in the project evidence directory. Raw serials remain in the local registry and immediate CLI output only.

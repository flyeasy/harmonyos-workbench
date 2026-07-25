# Project target bindings and leases

## Contents

1. Identity model
2. Binding model
3. Lease model
4. Port allocation
5. Drift and geometry
6. Recovery

## Identity model

- Emulator stable identity: DevEco UUID plus resolved instance path.
- Physical target stable identity: explicit HDC serial.
- Runtime routing identity: exact connected HDC serial.
- Display name is metadata, not identity.

## Binding model

A global registry at `~/.codex/state/harmonyos-workbench/target-registry.json` maps a pseudonymous project identity and role to one stable target. It stores the raw device identity required for local operation, but not the project absolute path, hostname or process ID. The directory is user-only (`0700`) and state files are user-only (`0600`). The registry is local machine state and must never be committed to an app repository.

Bindings survive lease release so a project selects the same simulator next time. One target cannot be implicitly shared by different projects.

## Lease model

Acquire a time-limited exclusive lease before start, stop, install, launch, screenshot or UI automation. File locking serializes registry updates. Heartbeat by acquiring again for the same project. Release the lease after the active device session; do not unbind unless intentionally reassigning the project.

An expired lease is not permission to steal a target that remains bound to another project.

## Port allocation

Assign one HDC port per emulator binding in `10000-16555`. Check persisted bindings and live Emulator command lines. Persist the selected port and require the runtime serial to end in that port when HDC uses host-port serials.

## Drift and geometry

Compare UUID, instance path, image, device type, API, CPU architecture and single/double-screen dimensions before use. For UI automation, capture a fresh screenshot and accept only configured dimensions or their orientation reversal.

## Recovery

Use this order:

1. `doctor` and `status`;
2. release an active lease owned by the same project;
3. stop only the bound emulator if necessary;
4. inspect expired leases and live processes;
5. explicitly `unbind`;
6. bind or allocate a replacement.

Never repair collision by deleting emulator data or changing another project's registry entry silently.

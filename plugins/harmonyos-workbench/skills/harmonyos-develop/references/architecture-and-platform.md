# Architecture and platform boundaries

## Contents

1. State and ownership
2. Lifecycle
3. Platform services
4. External systems
5. Failure closure

## State and ownership

Keep domain state, transport state, persistence state and visual state separate. Give each listener, task and cache one owner. Publish immutable or versioned state at module boundaries when late responses are possible.

## Lifecycle

Tie Ability, page, service and background work to explicit creation, foreground, background and destruction events. Cancel timers, subscriptions, requests and retries when their owner ends. Treat warm start, process restart and restored UI as different cases.

## Platform services

- Permissions: request at use, handle denial and revocation.
- Network: model offline, timeout, retry, cancellation, TLS and server authority.
- Storage/database: define schema evolution, atomic writes, corruption and recovery.
- Background work: respect platform limits; do not promise continuous execution without evidence.
- ArkWeb: separate web document state, native bridge state and window geometry.
- Distributed or cross-device features: model partial availability and remote identity explicitly.

## External systems

Put relays, gateways, encryption, remote hosts and protocol codecs behind narrow interfaces. Record protocol/version assumptions. UI success may only follow the authoritative acknowledgement defined by that interface.

## Failure closure

Unknown types, malformed payloads, stale generations and unsupported capabilities should fail closed. Preserve enough structured context for diagnosis without logging credentials or private payloads.

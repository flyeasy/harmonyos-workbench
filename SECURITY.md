# Security Policy

## Supported versions

Security fixes are applied to the latest version on the default branch.

## Reporting a vulnerability

Do not put vulnerability details or accidental secrets in a public issue. Use GitHub's private vulnerability reporting feature when it is available. Otherwise, open a minimal issue requesting a private reporting channel without including reproduction details or sensitive data.

Include:

- affected version or commit;
- impact and minimum reproduction;
- whether the report involves local state, command execution, redaction, device selection or signing material;
- a sanitized proof of concept.

Do not include credentials, private keys, signing profiles, certificates containing personal data, real device serials, emulator UUIDs, usernames, home-directory paths or unredacted project logs.

## Security boundaries

HarmonyOS Workbench:

- executes explicit local development commands and does not require a hosted service;
- stores target allocation state locally with user-only permissions;
- retains raw device identifiers only where local target operation requires them;
- writes pseudonymous durable evidence by default;
- treats app publication, emulator reset and device-data deletion as separately authorized actions.

Users remain responsible for reviewing commands, repository policy, SDK provenance and signing configuration.

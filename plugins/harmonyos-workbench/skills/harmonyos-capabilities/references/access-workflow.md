# Capability access workflow

## Contents

1. Identify
2. Classify access
3. Minimize
4. Apply or configure
5. Verify
6. Release

## Identify

Start from a concrete business action and data flow. Resolve the exact official capability name, target app identity, app form, API/OS, devices, regions and distribution countries. Record the official source URL and access date.

## Classify access

Classify each dependency independently:

- `os_api`: SDK API with system or user-grant permission;
- `kit`: system or application-service Kit with integration prerequisites;
- `agc_service`: project/app switch, agreement, credential or cloud configuration;
- `entitlement`: scenario review or formal capability right;
- `acl`: restricted permission approved only for listed scenarios;
- `commerce`: merchant, qualification, certificate, product or paid-package prerequisite.

One feature can use several layers. For example, Live View can require service rights, Push integration, lifecycle rules and device evidence.

## Minimize

1. Remove capabilities unrelated to the user-visible feature.
2. Prefer ordinary APIs without sensitive data.
3. Prefer system Picker or safety controls that grant only a user-selected resource.
4. Prefer foreground/user-triggered behavior over background or broad access.
5. Request the narrowest open permission.
6. Consider ACL only when the exact official eligible scenario is satisfied and no supported substitute meets the requirement.

## Apply or configure

Prepare a reviewed action packet before external changes:

- capability and exact application identity;
- scenario and user journey;
- eligibility and alternative analysis;
- requested rights/permissions and device scope;
- data, privacy and retention statement;
- required screenshots, video, undertaking, qualification or merchant material;
- test account and reviewer instructions;
- owner and explicit approval for agreements, application, purchase or submission.

Do not perform the external action from a generic “implement this feature” request. After action, capture the platform receipt or current status without exposing account or credential details.

## Verify

Verify in layers:

1. AGC or service status belongs to the intended app/project.
2. App identity, signature fingerprint, Client ID and server identity match.
3. Required SDK/dependency and configuration are present.
4. Manifest permission and reason text are complete and consistent across modules.
5. Runtime authorization handles denial, one-time grant, revocation and settings changes.
6. Bound supported targets prove success and unsupported targets prove fallback.
7. Server callbacks, token verification, replay/idempotency and error paths are tested when applicable.
8. Privacy policy/label, data disclosure, screenshots and reviewer instructions match actual behavior.

## Release

Before release, re-check current approval/entitlement state, expiry, app identity, distribution region, production endpoint, quota/payment, signed release behavior and reviewer evidence. Keep `approved`, `enabled`, `runtime_verified`, `submitted` and `published` distinct.

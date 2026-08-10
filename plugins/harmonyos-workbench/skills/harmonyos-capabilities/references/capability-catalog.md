# Capability catalog snapshot

## Contents

1. Scope
2. Capability groups
3. Restricted ACL examples

## Scope

This is a routing index based on the AGC list supplied by the user on 2026-08-10 plus current official documentation discovery. It does not prove that a capability is open to a particular account or app. Names, eligibility, device/API/region coverage, quotas and review materials must be verified in the live official console and documentation.

## Capability groups

| Group | Capabilities from the supplied list | Main gates to investigate |
| --- | --- | --- |
| AI knowledge | AI Networking | AGC project/app, switch/agreement, package/quota, server credential, data and retrieval evaluation |
| Location | hybrid location, indoor high-precision location, location semantics, background geofence wake, Bluetooth scan information including real MAC | device/region/API, personal data, foreground/background justification, separate capability rights, Bluetooth/location permissions |
| Account | Huawei Account, RISC cross-account protection | account scope, server callback authenticity, event minimization, account state and incident handling |
| Maps | Map service | service enablement, API/region/device support, attribution/licensing, location permissions and privacy |
| Device/security | application device-state detection, Safety Detect | device/app identity, server verification, false-positive/fallback policy, data disclosure |
| Live activity | Live View | eligible time-bounded scenario, rights, supported devices/regions, Push dependency, update/lifecycle limits, templates and reviewer evidence |
| Push | Push Kit, in-app call messages, voice-broadcast messages | base Push integration plus scenario-specific rights, notification/content rules, background behavior and device verification |
| Linking | App Linking | service switch, domain/link ownership, installed/uninstalled/deferred routes, region and release configuration |
| Commerce | Wallet, IAP | merchant/qualification, certificates/keys, product setup, server verification, sandbox, refund and privacy |
| Background/notification | agent reminder, priority notification | exact eligible scenario, notification authorization, background limits, user control and review evidence |
| Cards/surfaces | standby screen-saver card, transparent-backplane card, lock-screen card | form/card rules, surface entitlement, supported devices, privacy on public/locked surfaces |
| Cloud | Authentication, Cloud Storage, Cloud Hosting | service configuration, server/client trust boundary, SDK compliance, data region, consent and secret management |
| Health/wearable | Health Service, WearEngine | developer qualification/rights, user authorization, sensitive health/device data, formal access verification, physical-device tests |
| Continuation | cross-package continuation | source/target application identity, scenario review, distributed state and failure recovery |

Additional services such as App Linking, IAP, Live View, Health and WearEngine often have their own “development preparation”, rights and personal-data pages. Read those pages, not only the top-level switch description.

## Restricted ACL examples

The supplied AGC page showed 85 ACL entries. Keep the list live; do not freeze all entries in this repository. The following examples capture why scenario and device checks are mandatory:

| Permission | Supplied eligible scope summary | Device scope shown |
| --- | --- | --- |
| `ohos.permission.CUSTOM_SCREEN_RECORDING` | remote-login clients, screen-recording/screen-sharing apps, or enterprise security management scenarios; enterprise security uses the exception scenario | PC/2in1 |
| `ohos.permission.READ_WRITE_DOCUMENTS_DIRECTORY` | access public Documents directory | PC/2in1, tablet |
| `ohos.permission.READ_WRITE_DOWNLOAD_DIRECTORY` | access public Download directory | PC/2in1, tablet |
| `ohos.permission.USE_FRAUD_APP_PICKER` | anti-fraud app reporting | phone, tablet |
| `ohos.permission.USE_FRAUD_MESSAGES_PICKER` | anti-fraud SMS reporting | all |
| `ohos.permission.USE_FRAUD_CALL_LOG_PICKER` | anti-fraud call-log reporting | all |
| `ohos.permission.MANAGE_MEDIA_RESOURCES_FOR_PUBLIC` | control companion for third-party watch/IoT peripheral; requires interconnection evidence | phone, PC/2in1, car, tablet, smart screen |
| `ohos.permission.MANAGE_BLUETOOTH_ADVERTISER_NAME` | Bluetooth device vendor maintaining a custom advertising-name scheme for delivered legacy devices; undertaking required | all |
| `ohos.permission.ALLOW_EXTERNAL_NATIVE_CODE` | PC/2in1 development/diagnostic tool or enterprise/MDM app within documented executable-loading scenarios | PC/2in1 |
| `ohos.permission.CONTROL_DEVICE` | controlled side of a remote-login product receiving input events | PC/2in1 |

Before using any example, re-open the exact official restricted-permission page. Prefer Picker/control alternatives where official guidance provides them. A description copied from AGC is not approval evidence.

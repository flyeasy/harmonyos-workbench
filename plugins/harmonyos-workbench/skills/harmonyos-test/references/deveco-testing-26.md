# DevEco Testing 26 capability matrix

Last verified: 2026-07-20 against DevEco Testing for App 26.0.0.300 and Huawei's 26.0 documentation. Revalidate when the client major/minor version changes.

| Service | Simulator | Atomic service | Important condition |
|---|---:|---:|---|
| Local AppGallery precheck | No | No | HarmonyOS 5.0+ physical device; installed app and matching HAP/ZIP |
| Performance base | No | Yes | Stable physical device; avoid projection/recording |
| Scenario performance | No | No | Hypium scenario package; deterministic core path |
| Performance monitoring | No | Yes | Manual scenario and optional trace capture |
| Stability base | Yes | Yes | Long runs recommended; entry/DeepLink may be specified |
| Memory leak | No | Yes | HarmonyOS 7.0+ physical device and debug-certificate package |
| Multi-device layout comparison | Yes | Yes | Enable simulator support and configure target form factors |
| UX base | Yes | Yes | Validate layout, system adaptation, and basic experience |
| Security base | No | Yes | Physical device for applications |
| Power base | No | Yes | Physical device; background resource behavior |
| Functional experience | Yes | Yes | Current OS/device/upgrade compatibility |
| Exploration | Yes | Yes | Smart traversal or graph-based stress; 1h+ recommended |
| Regression | Yes | Yes | One Hypium case per executable test package |

Physical-device baseline: HarmonyOS 5.0+, developer mode and USB debugging, no lock password, auto-lock over one minute, stable network/temperature, sufficient battery, permissions and test account prepared. Long performance/stability tasks need substantial free disk.

Official starting points:

- https://developer.huawei.com/consumer/cn/testing/get-started/
- https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/get-familiar
- https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/performance-testing
- https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/stability-testing
- https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/other-test


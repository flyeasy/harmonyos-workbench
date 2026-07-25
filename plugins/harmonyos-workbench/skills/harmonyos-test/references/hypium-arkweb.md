# Hypium and ArkWeb

## Host setup

Prefer a dedicated Python 3.10 virtual environment. Confirm `hypium`, `xdevice`, and HDC before authoring tests. The PyCharm plugin is optional for command-line execution but useful for project generation and UIViewer workflows.

Run with `python -m hypium`; use explicit device serials and report paths. Preserve HTML/XML reports, step screenshots, and relevant device logs.

## Locator priority

Prefer stable native properties, then image matching, then proportional coordinates. Avoid absolute coordinates unless the UI surface exposes no semantic locator.

## ArkWeb

Hypium can connect Selenium to ArkWeb through `WebDriverSetupTool`. Install Selenium and provide a ChromeDriver matching the device ArkWeb/Chromium version. Connect using the application bundle name.

Canvas-heavy pages such as terminal emulators may not expose useful DOM semantics. Combine Selenium with image/coordinate input, a test-only JS bridge, or protocol/output assertions. Keep the real backend or relay end-to-end test.

Official ArkWeb guide:
https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/web-hypium-autotests


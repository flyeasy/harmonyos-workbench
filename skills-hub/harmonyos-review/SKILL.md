---
name: harmonyos-review
description: 严格 review、audit、审查、验收或评估 HarmonyOS、OpenHarmony 与 ArkUI 产品、代码、截图、录屏和设备证据。只报告有证据的任务、导航、状态真实性、生命周期、跨设备、多输入、视觉、动效、无障碍与性能问题，并给出最小修复计划和通过结论。
version: 0.4.0
category: review
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Review

只审视，不从零设计或批量改代码。问题和通过结论都必须有证据；官方资料、平台推断和项目 House Rule 分开措辞。

## Phase contract

1. **Input**：审查范围、项目/版本、目标角色和证据。
2. **Preflight**：核对项目、artifact、目标、时间和证据等级。
3. **Execute**：按依赖顺序审查，只报告有证据的问题。
4. **Verify**：复核主路径、失败/恢复路径和重复根因。
5. **Evidence**：输出发现、严重度、位置和未覆盖范围。
6. **Handoff**：设计问题交给 `harmonyos-design`，功能问题交给 `harmonyos-develop`。

E0 仅风险假设；E1 支持源码/静态问题；E2 支持编译与契约；E3 支持目标交互；E4 才支持性能、无障碍、故障或生产专项结论。先审任务/导航、状态/恢复、owner/生命周期、窗口/输入/几何、交互、视觉/动效、无障碍、性能和品牌。

每项 Finding 一行，证据与建议分开、同根因合并、推断显式标记。`BLOCKER` 阻断关键任务、真实性、无障碍、目标可操作性或有明确严重性能证据；`MAJOR` 应发布前修复；其余为 `MINOR`/`NOTE`。

输出上下文卡、Findings、根因归并、最小修复计划、验证矩阵和结论：有 Blocker 为**不通过**；有 Major 或关键证据缺口为**有条件通过**；只有关键任务、设备、输入、字号、无障碍和性能证据充分时才是**通过**。

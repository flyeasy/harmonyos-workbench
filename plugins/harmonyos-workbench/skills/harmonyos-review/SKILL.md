---
name: harmonyos-review
description: 严格 review、audit、审查、验收或评估 HarmonyOS、OpenHarmony 与 ArkUI 产品、代码、截图、录屏和设备证据。只报告有证据的任务、导航、状态真实性、生命周期、跨设备、多输入、视觉、动效、无障碍与性能问题，并给出最小修复计划和通过结论。不要从零设计或直接实现；设备证据必须来自 harmonyos-targets 的有效绑定和预检。
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Review

只审视，不从零设计或批量改代码。问题和通过结论都需要证据；H4 项目经验不得写成官方要求。

## Phase contract

1. **Input**：审查范围、项目/版本、目标角色和证据。
2. **Preflight**：核对项目、artifact、目标指纹、租约、时间和证据等级。
3. **Execute**：按依赖顺序审查，只报告有证据的问题。
4. **Verify**：复核主路径、失败/恢复路径和重复根因。
5. **Evidence**：输出发现、严重度、证据位置和未覆盖范围。
6. **Handoff**：设计问题交给 `harmonyos-design`，功能问题交给 `harmonyos-develop`。

## Review method

写上下文卡：主任务、窗口/输入、主题/字号/语言、关键路径、权威状态、可用证据、范围外和假设。

按依赖审查：任务/导航 → 状态真实性与失败恢复 → owner/生命周期 → 窗口/输入/几何 → 交互与动态集合 → 视觉/动效 → 无障碍 → 性能 → 品牌。上游结构未解决时，不用装饰建议掩盖根因。

证据等级：E0 仅风险假设；E1 支持源码/静态问题；E2 支持编译与契约；E3 支持目标路径体验；E4 才支持专项性能、无障碍、故障或生产结论。自动化冲突时先检查 target、前台 bundle、PID、样本、瞬态控件和 layout dump。

完整标准、严重度和案例只在需要对应维度时读取 [references/STANDARDS.md](references/STANDARDS.md)。

## Finding and verdict rules

- 一行一个发现，证据与建议分开；同根因合并；推断显式标记。
- `BLOCKER` 需要直接证据并阻断关键任务、真实性、无障碍、目标可操作性或明确性能安全；`MAJOR` 应在发布前修复；其余为 `MINOR` 或 `NOTE`。
- 至少追踪一条主路径和一条失败/恢复路径；共享服务/路由再做一次 A → B → A 交叉切换。
- 输出上下文卡、Findings 表、根因归并、最小修复计划、验证矩阵和反同质化约束。
- 结论只能是：有 Blocker 为**不通过**；无 Blocker 但有 Major/关键证据缺口为**有条件通过**；其余在关键路径、设备、输入、字号、无障碍和性能证据充分时才是**通过**。

设备证据必须来自有效 `harmonyos-targets` 绑定和预检。发布、签名、纯业务实现等问题只说明对体验结论的影响，并转交对应阶段。

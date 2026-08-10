---
name: harmonyos-motion
description: 把 HarmonyOS、ArkUI、Canvas、WebView 或代码生成产品动效的模糊手感和现象转换为准确术语、相近概念、诊断分支与可能的 ArkUI 能力，例如“松手像急刹车”“滚动后按钮来不及点”“页面像从同一张卡片长出来”“键盘弹出导致远端布局乱跳”。
version: 0.4.0
category: ux
platforms:
  - CODEX_CLI
permissions: []
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Motion

只把现象变成术语、诊断和可能的 ArkUI 方向；不代替完整设计、审查或实现。

## Capability contract

1. **Input**：现象、触发动作、目标设备和录屏/日志。
2. **Preflight**：区分动效、性能、生命周期、几何和 harness 问题。
3. **Execute**：给最佳术语、相近概念、诊断分支和可能关联。
4. **Verify**：指出慢放、帧率、状态或目标证据。
5. **Evidence**：引用观察，不把推断写成平台事实。
6. **Handoff**：设计/实现交给 `harmonyos-design`，完整验收交给 `harmonyos-review`。

使用以下输出：最佳术语的一句话定义、1–2 个相近概念、可能 ArkUI 方向、最短诊断分支和不适用边界。

常用映射：按下即变是**按下反馈**；离手急刹车是**速度继承缺失/速度断层**（先排查长帧）；对象随手是**跟手**，新输入接管是**可打断动画**；同一对象跨页面连续是**共享元素/容器转场**；短暂按钮点不到是**可见期**或旧几何；动画早于业务成功是**虚假完成**；旧回调覆盖新意图是**响应乱序/陈旧计时器**；IME 改坏远端内容是**局部/远端几何耦合**。

API 只能称“可能关联”，以目标 SDK 核验。整页体验转 Review，直接改代码转 Design。

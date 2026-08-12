---
name: harmonyos-design
description: 设计、重构、实现或改进 HarmonyOS、OpenHarmony 与 ArkUI 产品界面和应用内视觉身份。用于从需求建立设计基线，把交互方案落到 ArkTS/ArkUI，处理应用内设置/功能图标、VI、导航、跨手机/平板/折叠屏/PC 适配、多输入、状态机、异步真实性、生命周期、动效、无障碍、性能、WebView/IME 几何与设备验证。系统/商店图标与上架素材使用 harmonyos-release；纯审查使用 harmonyos-review；只命名动效使用 harmonyos-motion；非视觉业务功能使用 harmonyos-develop。
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Design

建立可实现、可验证的产品界面基线。只负责设计或视觉实现；审查用 `harmonyos-review`，动效命名用 `harmonyos-motion`，业务逻辑用 `harmonyos-develop`。

## Phase contract

1. **Input**：任务、窗口/输入、状态权威源和已有证据。
2. **Preflight**：确认信息架构、生命周期、设备和版本假设。
3. **Execute**：建立设计基线或完成一个连贯的 ArkUI 界面批次。
4. **Verify**：先静态/编译；设备结论使用 `harmonyos-targets` 的固定目标。
5. **Evidence**：记录状态模型、改动、截图和未验证项。
6. **Handoff**：业务实现交给 `harmonyos-develop`，验收交给 `harmonyos-review`。

## Decision loop

先写最小契约：主任务、目标窗口与输入、主题/字号/语言、权威状态、范围、完成信号、验证和假设。

按此顺序决策：任务与导航 → 状态/失败/生命周期 → 窗口与输入 → 系统组件 → Token/层级 → 动效 → 无障碍 → 性能 → 品牌。不要在未知状态来源或窗口条件下套用手机触摸方案。

必须守住：

- 输入已收到、处理中、确认和失败是不同状态；动画和播报只能消费权威状态。
- 页面、导航、服务和缓存各自有 owner；旧请求、listener、timer、poll 和手势不得跨生命周期覆盖新意图。
- 适配按窗口、输入、距离和任务改变导航/密度/分栏，不做等比缩放；safe area、IME 与 WebView/远端几何只由一个层级处理。
- 优先系统控件和语义；自定义不削弱返回、滚动、焦点、按下、禁用或辅助工具。
- 同一语义复用状态契约、组件和 Token；动态集合使用稳定身份。
- 先区分系统-facing 应用图标与应用内图标/VI：前者服从发布平台导出规则，后者按实际界面允许透明、去背景或矢量化。不得把商店图标的无透明通道规则机械套到设置页、功能图标或品牌插画。
- 列表/滚动容器要把边界回弹、加载更多和下拉刷新作为不同交互契约：回弹只解释边界；刷新只在明确阈值和释放后提交；两者都不能以动画假装数据已更新。

## Load detail only when needed

- 状态、异步、跨页面、WebView 或多格式内容：[references/FIELD-PATTERNS.md](references/FIELD-PATTERNS.md)
- 原则、导航和来源措辞：[references/PRINCIPLES.md](references/PRINCIPLES.md)
- 窗口、设备和输入：[references/ADAPTATION.md](references/ADAPTATION.md)
- 动效、手势和异步反馈：[references/MOTION.md](references/MOTION.md)
- ArkTS/ArkUI 映射：[references/ARKUI-MAPPING.md](references/ARKUI-MAPPING.md)
- 无障碍：[references/ACCESSIBILITY.md](references/ACCESSIBILITY.md)
- 从编辑到设备证据的循环：[references/DELIVERY-LOOP.md](references/DELIVERY-LOOP.md)
- 图标、VI、透明与多导出资产：[references/VISUAL-IDENTITY.md](references/VISUAL-IDENTITY.md)

按任务读取一个或两个文件，不把参考清单整批重述为实现规则。官方能力随 SDK 变化时，以当次目标 SDK、编译和设备行为为准。

## Output

输出任务与状态表、导航/适配/输入决策、ArkUI 落点、主路径和失败路径验证矩阵、已验证证据与 `needs_verification` 项。不得把编译、静态截图或模拟状态写成真实设备体验。

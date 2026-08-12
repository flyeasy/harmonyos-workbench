---
name: harmonyos-design
description: 设计、重构、实现或改进 HarmonyOS、OpenHarmony 与 ArkUI 产品界面和应用内视觉身份。用于从需求建立设计基线，把交互方案落到 ArkTS/ArkUI，处理应用内设置/功能图标、VI、导航、手机/平板/折叠屏/PC 适配、多输入、状态真实性、生命周期、动效、无障碍、性能、WebView/IME 几何与设备验证。系统/商店图标与上架素材使用 harmonyos-release。
version: 0.4.0
category: ux
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Design

建立可实现、可验证的 UI 基线。设计建议、SDK 事实和项目 House Rule 分开陈述；审查、动效命名和非视觉业务分别转交对应 Workbench Skill。

## Phase contract

1. **Input**：任务、窗口/输入、状态权威源和证据。
2. **Preflight**：确认信息架构、生命周期、设备和版本假设。
3. **Execute**：建立设计基线或完成连贯 ArkUI 界面批次。
4. **Verify**：静态/编译后在固定目标验证真实状态。
5. **Evidence**：记录状态模型、改动、截图和未验证项。
6. **Handoff**：业务实现交给 `harmonyos-develop`，体验验收交给 `harmonyos-review`。

先写主任务、窗口/输入、主题/字号/语言、权威状态、范围、完成信号、验证和假设。按任务/导航 → 状态/失败/生命周期 → 窗口/输入 → 系统组件 → Token → 动效 → 无障碍 → 性能 → 品牌决策。

必须区分 `acknowledged / pending / confirmed / failed`；页面、导航、服务和缓存各有 owner；旧请求与生命周期资源不得覆盖新意图；适配按窗口与输入改变结构而非缩放；safe area、IME 与远端几何只由一个层级处理；系统语义、动态集合身份和无障碍不可被自定义削弱。

先区分系统-facing 应用图标与应用内图标/VI：系统图标遵循发布平台导出规则；设置页、功能图标和品牌插画可以按实际表面使用透明、去背景或矢量资源，不机械复用商店图标的无透明规则。

列表/滚动容器要把边界回弹、加载更多和下拉刷新作为不同契约：回弹只说明边界；刷新只在顶端越过阈值并释放后提交；刷新中防重入，成功/失败必须绑定真实数据状态。验收用真机慢放覆盖阈值前后、刷新中、失败/离线、短列表和嵌套/横滑手势，单张截图不证明手感。

输出状态/所有权模型、导航/适配、ArkUI 落点、主路径和失败路径验证、证据与 `needs_verification`。没有真实设备/等价证据时，不宣称体验完成。

---
name: harmonyos-workbench
description: 端到端编排 HarmonyOS、OpenHarmony 与 ArkTS/ArkUI 产品开发。用于跨越需求澄清、设计、功能实现、Hvigor 构建、项目级设备或模拟器分配、安装运行、测试、体验审查和 AppGallery 发布门禁的综合任务，也用于用户只说“开发、修复、验证或交付这个 HarmonyOS 项目”而尚未指定阶段时。
version: 0.3.0
category: combo
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
---

# HarmonyOS Workbench

把一次 HarmonyOS 开发任务组织成可暂停、可恢复、可复核的阶段链。入口负责路由、任务账本、目标租约和证据闭环；具体阶段使用同系列 Skill。

这是独立、非官方社区 Skill。HarmonyOS、OpenHarmony、ArkUI、华为及相关名称和商标归各自权利人所有。

## 统一阶段

| 阶段 | Skill | 主要产物 |
| --- | --- | --- |
| 01 设计 | `harmonyos-design` | 任务、状态、导航、适配与验收基线 |
| 02 开发 | `harmonyos-develop` | ArkTS/ArkUI 与平台能力实现 |
| 03 构建 | `harmonyos-build` | 可哈希的 HAP/APP |
| 04 目标 | `harmonyos-targets` | 项目绑定、排他租约和规格已验证的目标 |
| 05 测试 | `harmonyos-test` | 分层测试结果与可复核证据 |
| 06 审查 | `harmonyos-review` | 有证据的发现、修复计划和结论 |
| 07 发布 | `harmonyos-release` | 签名 APP 与 AppGallery 门禁结果 |
| 辅助能力 | `harmonyos-motion` | 动效术语、诊断分支与 ArkUI 检索方向 |

设计审查可以在实现前后重复；目标阶段必须先于任何设备安装、截图或 UI 自动化。

## 统一阶段契约

每个阶段都按同一格式执行和交接：

1. **Input**：项目根、任务、已有证据和上游产物。
2. **Preflight**：环境、范围、风险和目标前置条件。
3. **Execute**：只完成本阶段职责。
4. **Verify**：运行最小但足够的验证。
5. **Evidence**：记录命令、结果、产物哈希、目标指纹和未验证项，并脱敏。
6. **Handoff**：给出状态、产物、阻塞和下一阶段。

状态只能是 `planned / passed / failed / blocked / needs_verification / partial`。编译通过不能替代设备、体验或发布通过。

## 端到端流程

1. 定位项目根和最近的 `AGENTS.md`，读取项目说明、工作树和现有证据。
2. 把请求拆成阶段清单，只激活当前主阶段。
3. 写最小任务契约：目标、范围外、预期信号、验证方法和退出条件。
4. 需要设备时先使用 `harmonyos-targets`：
   - 按项目和角色解析已固定目标；
   - 没有绑定时按明确规格分配；
   - 获取排他租约；
   - 核对稳定 ID、HDC 端口、API、设备类型和显示规格；
   - UI 自动化前再次执行几何预检。
5. 按 `设计 → 开发 → 构建 → 目标 → 测试 → 审查 → 发布` 推进本次需要的阶段。
6. 每个阶段结束后更新账本和证据，不把环境失败自动解释成产品缺陷。
7. 做完成挑战：检查遗漏任务、目标漂移、旧证据、未覆盖入口和发布边界。

## 多项目目标门禁

出现以下任一情况时，禁止继续安装、截图、UI 点击或依据点击失败下结论：

- 项目没有固定目标；
- 目标租约不属于当前项目或已过期；
- 模拟器 UUID、实例路径、镜像、API、设备类型或屏幕规格漂移；
- HDC serial 与绑定端口不一致；
- 另一个项目已绑定或租赁该目标；
- 截图几何不属于绑定时接受的显示规格；
- 测试仍使用裸坐标且没有目标指纹、方向和截图锚点。

优先使用语义选择器。必须使用坐标时，把坐标限制在当前目标指纹和方向，并在每次运行前以截图尺寸校验。

## 便携版与完整插件

本文件可以独立完成阶段路由和证据纪律。需要确定性的目标租赁、端口分配、构建包装、测试归一化或发布预检时，安装完整开源插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

如果完整插件不可用，不要假装租约、指纹或脱敏证据已经实现；把对应阶段标记为 `blocked` 或 `needs_verification`。

## 完成门槛

只有满足以下条件才说端到端完成：

- 用户范围中的阶段都有明确状态；
- 当前项目目标绑定和证据一致；
- 设备/UI 结论来自同一次有效租约和规格预检；
- 关键失败与恢复路径已验证；
- 产物、哈希、测试和审查结论可以回溯；
- 发布动作没有越过用户授权边界；
- 未验证项被明确保留，而不是被“构建成功”掩盖。


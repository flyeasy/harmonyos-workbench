---
name: harmonyos-workbench
description: 端到端编排 HarmonyOS、OpenHarmony 与 ArkTS/ArkUI 产品开发。用于跨越需求澄清、设计、开放能力/权益/ACL、AI 方案、功能实现、Hvigor 构建、项目级设备或模拟器分配、安装运行、测试、体验审查和 AppGallery 发布门禁的综合任务，也用于用户只说“开发、修复、验证或交付这个 HarmonyOS 项目”而尚未指定阶段时。纯单阶段任务转交对应的 harmonyos-* 能力；不替代各阶段的专属规则。
---

# HarmonyOS Workbench

把一次开发任务组织成可暂停、可恢复、可复核的阶段链。入口负责路由、任务账本、目标租约和证据闭环；具体实现交给阶段 Skill。

## 统一阶段

| 阶段 | Skill | 主要产物 |
| --- | --- | --- |
| 01 设计 | `harmonyos-design` | 任务、状态、导航、适配与验收基线 |
| 02 能力 | `harmonyos-capabilities` | 开放能力、权益、ACL、凭据和隐私账本 |
| 03 AI（按需） | `harmonyos-ai` | AI 能力层选型、数据/安全边界和效果评测契约 |
| 04 开发 | `harmonyos-develop` | ArkTS/ArkUI 与平台能力实现 |
| 05 构建 | `harmonyos-build` | 可哈希的 HAP/APP |
| 06 目标 | `harmonyos-targets` | 项目绑定、排他租约和规格已验证的目标 |
| 07 测试 | `harmonyos-test` | 分层测试结果与可复核证据 |
| 08 审查 | `harmonyos-review` | 有证据的发现、修复计划和结论 |
| 09 发布 | `harmonyos-release` | 签名 APP 与 AppGallery 门禁结果 |
| 辅助能力 | `harmonyos-motion` | 动效术语、诊断分支与 ArkUI 检索方向 |

设计审查可以在实现前后重复；目标阶段必须先于任何设备安装、截图或 UI 自动化。

## 统一阶段契约

每个阶段都按同一格式执行和交接：

1. **Input**：项目根、任务、已有证据和上游产物。
2. **Preflight**：环境、范围、风险和目标前置条件。
3. **Execute**：只完成本阶段职责。
4. **Verify**：运行最小但足够的验证。
5. **Evidence**：写入 `harmonyos.workbench.evidence/v2` 脱敏记录。
6. **Handoff**：给出状态、产物、阻塞和下一阶段。

状态只能是 `planned / passed / failed / blocked / needs_verification / partial`。编译通过不能替代设备或体验通过。

## 端到端流程

1. 定位项目根和最近的 `AGENTS.md`，读取项目账本。
2. 把请求拆成阶段清单；只激活当前主阶段。
3. 写最小任务契约：目标、范围外、预期信号、验证方法、退出条件。
4. 需要设备时，先使用 `harmonyos-targets`：
   - 按项目和角色解析已固定目标；
   - 没有绑定时按明确规格分配；
   - 获取排他租约；
   - 核对 UUID、实例路径、HDC 端口、API 和显示规格；
   - UI 自动化前再次执行几何预检。
5. 按 `设计 → 能力 → AI（按需）→ 开发 → 构建 → 目标 → 测试 → 审查 → 发布` 推进所需阶段。
   - 任务需要 Kit、AGC 服务、权益、商户/资格或 ACL 时，先建能力账本；
   - 任务涉及 Agent、Skill、系统 AI、端侧模型、云模型或 AI 联网增强时，再进入 AI 阶段；
   - 能力选择和开通状态不在 `harmonyos-develop` 中重复判定。
6. 每个阶段结束后更新账本和证据，不把失败自动解释为产品缺陷。
7. 做完成挑战：检查遗漏任务、目标漂移、旧证据、未覆盖入口和发布边界。

## 目标稳定性门禁

出现以下任一情况时，禁止继续 UI 点击或依据点击失败下结论：

- 项目没有固定目标；
- 目标租约不属于当前项目或已过期；
- 模拟器 UUID、实例路径、镜像、API、设备类型或屏幕规格漂移；
- HDC serial 与绑定端口不一致；
- 另一个项目已绑定或租赁该目标；
- 截图几何不属于绑定时接受的显示规格；
- 测试仍使用裸坐标且没有目标指纹和截图锚点。

优先使用语义选择器。必须使用坐标时，把坐标限制在当前目标指纹和方向，并在每次运行前以截图尺寸校验。

## 稳定脚本入口

先根据本 Skill 文件位置解析插件根，再调用：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py --help
python3 <plugin-root>/scripts/harmonyos_workbench.py targets inventory
```

不要从项目目录运行 `python3 scripts/...`；项目脚本与插件脚本不得依赖当前工作目录重名解析。

详细阶段接口见 [references/phase-contract.md](references/phase-contract.md)，项目级账本和证据约定见 [references/project-ledger.md](references/project-ledger.md)。

## 完成门槛

只有满足以下条件才说端到端完成：

- 用户范围中的阶段都有明确状态；
- 当前项目目标绑定和证据一致；
- 设备/UI 结论来自同一次有效租约和规格预检；
- 关键失败与恢复路径已验证；
- 所需开放能力、权益、ACL、凭据、资费和隐私都有可追溯状态；
- AI 功能的能力层、模型/Kit 版本、评测集、工具授权和降级路径已验证；
- 产物、哈希、测试和审查结论可以回溯；
- 发布动作没有越过用户授权边界；
- 未验证项被明确保留，而不是被“构建成功”掩盖。

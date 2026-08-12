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
| 09 发布 | `harmonyos-release` | 签名 APP、四件套一致性与 AppGallery 门禁结果 |
| 辅助能力 | `harmonyos-motion` | 动效术语、诊断分支与 ArkUI 检索方向 |

设计审查可以在实现前后重复；目标阶段必须先于任何设备安装、截图或 UI 自动化。用户明确要求的真机“仅安装”不进入调试车道，不申请独占租约，也不声称运行结果。

## 统一阶段契约

每个阶段都按 **Input → Preflight → Execute → Verify → Evidence → Handoff** 交接：输入项目/任务/上游产物，预检风险，执行本阶段，验证最小信号，写入 `harmonyos.workbench.evidence/v2` 脱敏记录，再给出状态、产物、阻塞和下一阶段。

状态只能是 `planned / passed / failed / blocked / needs_verification / partial`。编译通过不能替代设备或体验通过。

## 端到端流程

1. 定位项目根和最近的 `AGENTS.md`，读取项目账本。
2. 在实现前标记交付画像：`standard`、`content_backed`、`regulated_content`、`external_integration`、`companion_hardware` 可叠加；只记录本次确实涉及的画像。
3. 把请求拆成阶段清单；只激活当前主阶段。
4. 写最小任务契约：目标、范围外、预期信号、验证方法、退出条件。
5. 需要调试、运行、截图或验证设备时，先用 `harmonyos-targets` 建立项目角色绑定；多规格范围在开发前建立手机/平板/折叠屏需求—绑定—验证矩阵。只在 `device-slice` 即将进行这些独占操作时获取租约；用户明确要求的真机仅安装使用精确 serial 直达安装。
6. 按 `设计 → 能力 → AI（按需）→ 开发 → 构建 → 目标 → 测试 → 审查 → 发布` 推进所需阶段；这是依赖路由，不是每次编辑都必须串行走完的清单。按 `host-fast / build-slice / device-slice / candidate` 选择本轮最小验证车道，设备和发布只在其边界进入。
   - 任务需要 Kit、AGC 服务、权益、商户/资格或 ACL 时，先建能力账本；
   - 任务涉及 Agent、Skill、系统 AI、端侧模型、云模型或 AI 联网增强时，再进入 AI 阶段；
   - 能力选择和开通状态不在 `harmonyos-develop` 中重复判定。
7. 按交付画像补相应 artifact：外部集成用不含秘密的隔离矩阵，内容用发布账本，受监管内容用业务边界账本，配套硬件用安全拓扑；具体字段见 [architecture](../../../../docs/WORKBENCH_ARCHITECTURE.md)。
8. 每个阶段结束后更新账本和证据；主机车道留下的设备覆盖债务必须写明关闭边界。对未变化的外部/公开材料发布阻塞复用带输入指纹的已知阻塞结论，不重复跑无新增信息的完成审计。
9. 做完成挑战：检查遗漏任务、目标漂移、旧证据、未覆盖入口和发布边界。

## 目标稳定性门禁

没有项目绑定、有效租约、匹配指纹/端口或所需的几何/截图锚点时，禁止继续 UI 点击或把失败归因于产品。优先语义选择器；坐标只在当前目标和方向下有效。操作与恢复细节由 `harmonyos-targets` 负责。

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
- 交付画像带来的内容、外部集成或配套硬件证据均已满足，或被明确保留为发布阻塞。

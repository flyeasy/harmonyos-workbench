---
name: harmonyos-workbench
description: 端到端编排 HarmonyOS、OpenHarmony 与 ArkTS/ArkUI 产品开发。用于跨越需求澄清、设计、开放能力/权益/ACL、AI 方案、功能实现、Hvigor 构建、项目级设备或模拟器分配、安装运行、测试、体验审查和 AppGallery 发布门禁的综合任务，也用于用户尚未指定阶段的 HarmonyOS 开发、修复、验证或交付任务。
version: 0.4.0
category: combo
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
---

# HarmonyOS Workbench

端到端入口负责路由、账本、交接和完成挑战；具体能力由同系列 Skill 负责。它是独立社区 Skill，不把项目经验说成官方规则。

## Phase contract

每阶段按 **Input → Preflight → Execute → Verify → Evidence → Handoff**：输入项目/任务/上游产物，预检风险，执行本阶段，验证最小信号，记录脱敏证据，再交接状态、产物、阻塞和下一阶段。

状态只能是 `planned / passed / failed / blocked / needs_verification / partial`。构建、模拟和发布结论不可互相替代。

## Route

按需要推进：`design → capabilities → ai (optional) → develop → build → targets → test → review → release`；这是依赖路由，不是每次编辑必走的串行清单。先选 `host-fast / build-slice / device-slice / candidate` 最小车道，只有调试、启动、截图或 UI 验证的设备车道才租赁目标，只有候选/交接边界才跑发布门禁；用户明确要求的真机仅安装使用精确已连接 serial 直接安装、不占用目标且不构成运行验证；`motion` 仅命名动效现象。任何安装、截图或 UI 自动化前先进入 Targets。

开始时：读取项目约束与账本，写目标/范围外/预期信号/验证/退出条件，只激活一个主阶段。需要 Kit、AGC、权益或 ACL 先建能力账本；涉及 Agent、系统 AI、端侧/云模型、RAG 或联网增强再进入 AI。

标记适用画像：

- `content_backed`：来源/授权、人工审核、设备体验与 `publishEligible`；
- `regulated_content`：允许/禁止表达、动态数据、分享/激励和人工复核；
- `external_integration`：不含秘密的隔离矩阵，fixture 不等于真实互通；
- `companion_hardware`：项目安全守卫、实体拓扑和用户确认。

没有项目绑定、有效租约、匹配目标/端口/几何或当前截图锚点时，禁止继续 UI 点击或把失败归为产品。优先语义节点；坐标只在当前目标与方向下有效。主机车道留下的设备覆盖债务须在合并、候选或发布前关闭；未变化的外部发布阻塞可按输入指纹复用，不重复做无新增信息的完整审计。

## Completion

范围内阶段、目标和证据一致；关键失败/恢复已验证；能力、AI、隐私和交付画像有可追溯状态；产物/哈希/审查可回溯；未验证项明确保留；发布动作不越过用户授权。

需要排他租约、端口分配、证据 schema 或发布预检时安装完整插件；便携版缺少等价机制时，将对应设备/发布结论标记为 `blocked` 或 `needs_verification`。

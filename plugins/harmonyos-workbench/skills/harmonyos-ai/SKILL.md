---
name: harmonyos-ai
description: 规划、实现、诊断或验证 HarmonyOS AI 产品与工程能力。用于小艺 Skill 与 Agent、Agent Framework Kit、端侧 A2A、Intents Kit、Core Speech/Core Vision/Natural Language/Speech/Vision Kit、CANN、MindSpore Lite、Neural Network Runtime、端侧模型、云侧大模型、RAG、AI 问答联网增强、AI 数据/隐私/安全与效果评测。开放能力开通、权益、ACL 和资格先使用 harmonyos-capabilities；通用业务功能使用 harmonyos-develop。
---

# HarmonyOS AI

先选择正确的 AI 层，再写代码。不把“AI”当成单一 API，不把控制台已开通、编译通过或模拟返回写成线上能力已成立。

## Capability contract

1. **Input**：用户任务、产品入口、目标 API/设备/地区、时延与离线目标、数据类型、成本与发布范围。
2. **Preflight**：核对官方当前文档、系统能力和版本；使用 `harmonyos-capabilities` 确认开通/权益/ACL；完成数据、凭据、威胁和降级设计。
3. **Execute**：实现最小可替换边界，明确模型、检索、工具、审核和 UI 状态的权威来源。
4. **Verify**：分别验证确定性逻辑、效果集、失败路径、真实设备/服务、性能、安全和成本。
5. **Evidence**：记录能力层、文档快照日期、版本和设备范围、开通状态引用、评测数据版本、结果和未验证项；不记录提示词中的私有数据和凭据。
6. **Handoff**：将平台开通交给 `harmonyos-capabilities`，实现交给 `harmonyos-develop`，设备和效果验证交给 `harmonyos-targets` / `harmonyos-test`，上架门禁交给 `harmonyos-release`。

## 选择 AI 能力层

| 任务 | 首选能力层 | 不要混淆 |
| --- | --- | --- |
| 让系统智能入口发现并调用应用功能 | 应用 Skill / Intents Kit | 不等于应用内聊天机器人 |
| 应用内拉起或组合 Agent | Agent Framework Kit | 不等于自建模型推理 |
| 接入已有智能体 | 端侧 A2A / Agent Extension | 不等于无权执行本地操作 |
| 语音、视觉、NLP 通用能力 | Core Speech/Core Vision/Natural Language Kit | 不要先自带大模型 |
| 朗读、AI 字幕、卡证识别、文档扫描等场景 | Speech/Vision Kit 场景化能力 | 场景化控件与基础 API 分开评估 |
| 自定义端侧模型 | MindSpore Lite / NNRT | 先验证算子、内存、功耗和设备覆盖 |
| 针对芯片深度优化推理 | CANN | 不在没有性能瓶颈证据时提前绑定 |
| 给大模型补充实时网页知识 | AGC AI 问答联网增强 | 它是检索/联网服务，不是大模型本身 |
| 使用外部云模型或 RAG | 自建服务端边界 | 项目级 API Key 不进入 HAP/源码 |

详细分类和选择问题见 [references/ai-capability-map.md](references/ai-capability-map.md)。

## 实现门禁

1. 把“用户问题”改写为可测量任务：输入、可接受结果、延迟、离线、失败、拒绝、降级、成本。
2. 在写代码前固定目标 API、设备类型、地区、应用/元服务形态和分发入口。
3. 优先本地处理；需要上云时，只发送完成任务必需的数据，明确同意、删除、留存和区域约束。
4. 把模型/检索结果当作不可信输入；工具调用必须经参数验证、权限检查和业务授权。
5. 用明确状态表达 `idle / preparing / running / partial / completed / failed / cancelled / blocked`；不用动画代替服务端确认。
6. 为系统能力不可用、服务未开通、无网、超时、限流、模型输出不合格和用户撤销提供真实降级。
7. 如果官方能力、版本或审核规则可能变化，在当次任务中重新查官方资料，不把本 Skill 的快照当成实时控制台事实。

## AI 联网增强

需要 AI 问答联网增强时，必须读取 [references/ai-networking.md](references/ai-networking.md)。核心规则：

- 把“项目存在”、“能力开关已开”、“协议已接受”、“套餐可用”、“API 调用通过”分开记录。
- 项目级 API Key 只保留在受控服务端或密钥系统，不打包进客户端。
- 用检索质量、时效、来源、空结果、限流、超时、成本和注入攻击测试验证，不只看 HTTP 200。

## 验证阶梯

1. 纯逻辑、模型适配器、状态机和输出 Schema 测试。
2. 脱敏的固定评测集，包含正常、边界、拒绝、攻击和降级样例。
3. 模拟系统/远端边界的契约测试。
4. `harmonyos-build` 构建。
5. 经 `harmonyos-targets` 固定的目标上运行真实 Kit/端侧模型。
6. `harmonyos-test` 执行性能、功耗、弱网、数据撤销和效果回归。
7. `harmonyos-release` 验证开通/权益、隐私标签、凭据边界、资费与上架说明。

评测和安全细则见 [references/ai-verification.md](references/ai-verification.md)；官方来源见 [references/sources.md](references/sources.md)。

## 输出

输出 AI 能力层选型、可用性与开通状态、数据/威胁/成本边界、实现范围、评测集与结果、降级路径和未验证项。不能用真实设备或真实服务证明的结论标记 `needs_verification`。

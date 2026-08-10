---
name: harmonyos-ai
description: 规划、实现、诊断或验证 HarmonyOS AI 产品与工程能力。用于小艺 Skill 与 Agent、Agent Framework Kit、端侧 A2A、Intents Kit、Core Speech/Core Vision/Natural Language/Speech/Vision Kit、CANN、MindSpore Lite、Neural Network Runtime、端侧模型、云侧大模型、RAG、AI 问答联网增强、AI 数据/隐私/安全与效果评测。开放能力开通、权益、ACL 和资格先使用 harmonyos-capabilities。
version: 0.4.0
category: build
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
---

# HarmonyOS AI

先选择正确的 AI 层，再写代码。不把“AI”当成单一 API，不把开通、编译或模拟成功当成线上能力已成立。

## Capability contract

1. **Input**：用户任务、产品入口、目标 API/设备/地区、时延与离线目标、数据类型、成本与发布范围。
2. **Preflight**：核对官方当前文档、系统能力和版本；使用 `harmonyos-capabilities` 确认开通/权益/ACL；完成数据、凭据、威胁和降级设计。
3. **Execute**：实现最小可替换边界，明确模型、检索、工具、审核和 UI 状态的权威来源。
4. **Verify**：分别验证确定性逻辑、固定效果集、失败路径、真实设备/服务、性能、安全和成本。
5. **Evidence**：记录能力层、文档快照日期、版本/设备范围、开通状态引用、评测版本和未验证项；不记录私有提示和凭据。
6. **Handoff**：开通交给 `harmonyos-capabilities`，实现交给 `harmonyos-develop`，真机/效果交给 `harmonyos-targets` / `harmonyos-test`，上架交给 `harmonyos-release`。

## 能力层选择

| 任务 | 首选能力 |
| --- | --- |
| 系统智能入口发现并调用应用功能 | 应用 Skill / Intents Kit |
| 应用内拉起或组合 Agent | Agent Framework Kit |
| 接入已有智能体 | 端侧 A2A / Agent Extension |
| 语音、视觉、NLP 基础能力 | Core Speech/Core Vision/Natural Language Kit |
| 朗读、AI 字幕、卡证识别、文档扫描 | Speech/Vision Kit |
| 自定义端侧模型 | MindSpore Lite / NNRT |
| 芯片级模型转换、量化与优化 | CANN |
| 给大模型补充实时网页知识 | AGC AI 问答联网增强 |
| 外部云模型或 RAG | 自建受控服务端边界 |

每次选型都固定 API/OS、设备、地区、应用形态、数据出端、延迟/离线、成本和降级目标。系统 Kit 能满足时不先自带模型；没有性能瓶颈证据时不提前绑定 CANN。

## AI 工程门禁

- 优先本地处理；上云只发送任务必需数据，明确同意、留存、删除和区域。
- 模型/检索输出一律为不可信输入；工具调用经过白名单、Schema、权限、参数、幂等和确认检查。
- 项目级 API Key、Client Secret 和模型密钥不进入 HAP、源码、日志或证据。
- 状态明确区分 `preparing / running / partial / completed / failed / cancelled / blocked`。
- 对未开通、不支持设备/地区、无网、超时、限流、不合格输出和用户撤销提供真实降级。

## AI 问答联网增强

官方 2026-07-01 FAQ 列出中文网页极速、中文网页+新闻+工具垂域标准、多语言增强三类服务。任务时重新核对端点、套餐、配额和请求 Schema。

把项目存在、能力可见、开关已开、协议已接受、套餐可用、凭据有效、API 调用通过分开记录。使用 `HarmonyOS 客户端 → 应用服务端 → AI Networking` 边界，不由客户端直接持有项目密钥。

## 验证

1. 纯逻辑、状态机、适配器和输出 Schema。
2. 脱敏固定评测集：正常、边界、拒绝、注入、越权、降级。
3. 模拟系统/远端契约。
4. 经 `harmonyos-targets` 固定的真实目标上验证 Kit/端侧模型。
5. `harmonyos-test` 验证效果、延时、内存、功耗、弱网、成本和回归。
6. `harmonyos-release` 核对开通/权益、隐私标签、凭据边界和未验证限制。

官方发现入口：<https://developer.huawei.com/consumer/cn/harmonyos-ai> 、<https://developer.huawei.com/consumer/cn/sdk/> 、<https://developer.huawei.com/consumer/cn/doc/AppGallery-connect-Guides/agc-ainetworking-introduction-0000002309825793>。使用时记录访问日期。

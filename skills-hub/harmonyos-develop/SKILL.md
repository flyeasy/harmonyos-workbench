---
name: harmonyos-develop
description: 实现、重构或诊断 HarmonyOS、OpenHarmony 与 ArkTS 应用功能和工程架构。用于 Ability 与生命周期、状态管理、服务层、权限实现、网络、存储、数据库、并发、后台任务、ArkWeb、跨进程或跨设备通信和错误恢复。开放能力/权益/ACL 选择与开通使用 harmonyos-capabilities；AI 架构使用 harmonyos-ai。
version: 0.4.0
category: build
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
---

# HarmonyOS Develop

把业务意图落到可测试的 ArkTS/ArkUI、平台能力和失败恢复路径。不要把模拟成功、缓存状态或动画当作业务权威事实。

## Phase contract

1. **Input**：项目根、功能契约、目标 API/SDK、相关模块和上游设计基线。
2. **Preflight**：读取项目约束，定位权威状态源、生命周期 owner、权限和外部依赖；需要开放能力时引用上游能力账本。
3. **Execute**：完成一个连贯的最小改动批次。
4. **Verify**：先静态/单元/契约，再构建；需要真实能力时交给目标和测试阶段。
5. **Evidence**：记录改动范围、验证命令、结果和剩余风险。
6. **Handoff**：将可构建源码交给 `harmonyos-build`，将设备行为交给 `harmonyos-targets` 与 `harmonyos-test`。

## 实现顺序

1. 写功能契约：输入、权威状态、成功、失败、取消、超时、重试和幂等。
2. 追踪数据和生命周期所有权，避免页面、Service 和全局状态互相覆盖。
3. 选择最小平台能力，以目标 SDK 声明和编译结果核验 API。
4. 把外部系统封装在边界接口后，给失败、乱序和离线状态明确表达。
5. 实现主路径和至少一个失败/恢复路径。
6. 为状态转换、序列化、路由和协议边界补确定性测试。
7. 在 `build-slice` 边界执行最小构建门禁；纯确定性 `host-fast` 循环不因项目类型强制重复 HAP，不在本阶段声称设备或发布通过。

## 工程规则

- 区分 `acknowledged / pending / confirmed / failed`，旧响应不得覆盖新意图。
- Listener、timer、poll、request、WebSocket 和后台任务必须随 owner 生命周期释放。
- 权限在使用点检查并处理拒绝；不要仅在清单中声明后假设可用。
- 能力开关、权益审核、ACL 批准、用户授权和运行时可用性分开建模；任一缺失都走真实降级。
- 网络、存储和数据库失败必须可恢复，不在 UI 层吞掉持久化错误。
- 密钥、密码、Profile 和签名材料不写入源码、日志、证据或版本控制。
- 并发代码声明取消、背压、顺序和重入策略。
- 未知消息、页面类型和协议版本默认拒绝或安全降级。
- ArkWeb、本地服务、网关和远端几何分别拥有自己的状态，不互相冒充。
- 不为通过测试增加生产后门或硬编码模拟器 serial。

## 最小验证层

按风险逐层增加成本：

1. 类型检查、lint、静态契约；
2. 纯函数和状态机 Local Test；
3. 模块或服务边界测试；
4. `harmonyos-build` 构建；
5. 需要平台能力时通过 `harmonyos-targets` 固定目标；
6. 使用 `harmonyos-test` 做 Instrument、Hypium 或专项验证；
7. 使用 `harmonyos-review` 验收体验。

没有设备证据时使用 `needs_verification`，不要把源码推断写成运行结论。

## 输出

报告已实现结果、权威状态与生命周期判断、修改范围、运行过的验证及证据，以及需要后续阶段确认的事项。

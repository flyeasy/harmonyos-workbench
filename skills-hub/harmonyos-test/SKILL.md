---
name: harmonyos-test
description: 规划、执行并归一化 HarmonyOS 应用和元服务测试。用于 Local Test、Instrument Test、项目 smoke、Hypium UI、ArkWeb Selenium、DevEco Testing 专项、性能与回归证据；设备测试必须使用项目绑定、有效租约和目标预检。
version: 0.3.0
category: test
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

# HarmonyOS Test

## Phase contract

1. **Input**：项目根、变更行为、目标层、目标角色和上游产物。
2. **Preflight**：选择最小测试层；设备测试验证项目绑定、租约和几何证据。
3. **Execute**：运行一个确定性测试批次。
4. **Verify**：区分产品失败、环境阻塞和测试工具假阴性。
5. **Evidence**：记录脱敏命令、结果、目标指纹和未验证项。
6. **Handoff**：结果交给 `harmonyos-review`；发布专项交给 `harmonyos-release`。

## Workflow

1. 读取项目约束，定义变更行为、预期信号、目标形态、证据和退出条件。
2. 先生成能力计划，再运行昂贵测试。
3. 设备或模拟器工作先通过 `harmonyos-targets` 获取项目绑定、有效租约和当前几何预检。
4. 从最小有效层开始：静态/项目 smoke、Local Test、Instrument Test、确定性 Hypium UI、DevEco Testing 专项服务。
5. 使用 `harmonyos-build` 做构建门禁，使用 `harmonyos-targets` 做部署与截图。
6. 只有 CLI 无法执行某个 DevEco Testing 服务时才操作客户端 UI，并选择最短有代表性的时长。
7. 把结果归一化为 `passed / failed / blocked / needs_verification`；真实设备服务不可用时不能写成通过。

## Coverage selection

- 纯逻辑、状态机和序列化优先 Local Test。
- 框架行为与设备能力使用 Instrument Test。
- 可重复用户路径和多设备 UI 使用 Hypium；ArkWeb 场景核对 Selenium bridge 与 ChromeDriver 版本。
- 性能、稳定性、内存泄漏、UX、功耗、安全、探索、回归和预检使用对应 DevEco Testing 服务。
- 应用依赖后端、relay、加密或跨进程时，保留端到端协议测试；UI 遍历不能替代它们。
- 优先语义选择器；坐标点击只在目标指纹和当前几何预检一致时有效。

## Guardrails

- 授予权限、代表测试账号接受隐私提示、执行破坏性预处理或启动有配额影响的长/云测试前，取得明确授权。
- 不在持久报告中记录凭据、终端全文、令牌或原始私有设备标识。
- 短时专项运行只算 smoke 证据，不是统计充分的性能或稳定性结论。
- 同一路径连续三次失败后停止重试并保留阻塞证据。
- 不在未重新绑定和重新预检时换到另一个在线目标重试 UI 点击。

## 完整插件

需要统一测试计划、脱敏执行包装、证据 schema 或 DevEco 任务清单时安装完整插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

缺少设备绑定或证据包装时，可以继续主机测试，但设备测试必须标记为 `blocked` 或 `needs_verification`。


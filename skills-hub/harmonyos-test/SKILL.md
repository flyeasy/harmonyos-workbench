---
name: harmonyos-test
description: 规划、执行并归一化 HarmonyOS 应用和元服务测试。用于 Local Test、Instrument Test、项目 smoke、Hypium UI、ArkWeb Selenium、DevEco Testing 专项、性能与回归证据；设备测试必须使用项目绑定、有效租约和目标预检。
version: 0.4.0
category: test
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

# HarmonyOS Test

## Phase contract

1. **Input**：项目、变更行为、测试层、角色和上游产物。
2. **Preflight**：选择最小层；设备测试核对绑定、租约和几何。
3. **Execute**：运行确定性批次。
4. **Verify**：区分产品失败、环境阻塞和工具假阴性。
5. **Evidence**：记录脱敏命令、结果、目标指纹和未验证项。
6. **Handoff**：交给 Review；发布专项交给 Release。

先按 `host-fast / build-slice / device-slice / candidate` 选最小验证车道：小主机循环不自动占用设备或跑发布门禁；功能批次边界再构建、租赁目标并跑代表设备场景。按静态/smoke → Local → Instrument → Hypium UI → DevEco 专项递进；后端、relay、加密或跨进程依赖保留端到端协议测试。UI 自动化优先语义节点，坐标只在当前指纹与 10 分钟内几何下有效。主机验证的用户可见改动要写 `coverage debt`（变更面、已有证据、待补设备场景、关闭边界），在设备敏感合并或发布前关闭。

长运行分为刷机后 smoke、相关行为 HIL 和合并/发布前 soak；短跑不等于稳定性，且不要因小改动重复长稳。物理身份、租约、误刷防护、权限/ACL、签名/Profile 与生产证据不是可放松项。

外部服务、账号、支付、AI、局域网或配套硬件先建不含 endpoint/凭据的集成矩阵：变量名称、读写性质、隔离确认、证据方式和发布影响。写远端必须目标为明确隔离目录/数据库，缺少确认即 `blocked`；fixture 不等于真实服务验证。

权限、隐私提示、破坏性预处理和长/云测试需明确授权；不持久化凭据、令牌、终端全文或原始设备标识；同一路径三次失败后停止并保留阻塞。没有等价目标租约/证据机制时，设备结论只能为 `blocked` 或 `needs_verification`。

---
name: harmonyos-targets
description: 为 HarmonyOS 项目发现、分配、固定、租赁和验证物理设备及 DevEco 模拟器。用于多项目并行开发、多模拟器管理、稳定选择手机/平板/折叠屏目标、唯一 HDC 端口分配、安装启动、截图、UI 自动化前几何校验和设备争用诊断。
version: 0.4.0
category: ops
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

# HarmonyOS Targets

将“当前连接设备”变为“项目固定目标角色”；UUID/物理 serial 才是身份，显示名称和临时 HDC serial 不是。

## Phase contract

1. **Input**：项目、角色、设备/API/屏幕要求和已有绑定。
2. **Preflight**：检查实例、绑定、租约、端口和规格漂移。
3. **Execute**：解析/分配目标、获取租约后再操作。
4. **Verify**：核对精确 serial、运行状态、指纹和截图几何。
5. **Evidence**：记录脱敏项目/角色/目标哈希、租约、规格和产物。
6. **Handoff**：交给 `harmonyos-test` 或 `harmonyos-review`。

先解析当前项目绑定；没有绑定时按精确 UUID/serial 或明确设备、API、屏幕约束分配，候选规格不同就停止。主机车道只保留需求/绑定而不抢占目标；在安装、运行、截图或 UI 验证的 device-slice 才获取排他租约。启动前核对绑定，UI 前预检；语义节点可在同一有效批次复用匹配预检，坐标点击仍要求 10 分钟内几何；只使用解析出的 serial；结束后释放租约但保留绑定。

同一 target 不隐式共享，每个模拟器端口唯一，漂移/Offline/多目标歧义阻塞；不自动 reset、清数据或影响他项目。项目 HDC/MCP 脚本不得硬编码端口、serial 或“第一个在线设备”；完整插件的短生命周期 target bridge 才能安全把已租赁目标交给脚本。

便携版没有共享注册表时，不能声称多项目/多设备已经安全绑定；设备阶段应为 `blocked` 或 `needs_verification`，纯主机工作可继续。

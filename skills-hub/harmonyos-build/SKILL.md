---
name: harmonyos-build
description: 构建并校验 HarmonyOS、OpenHarmony 的 HAP 或 APP 产物。用于 Hvigor debug/release 构建、module/product 选择、SDK 与 Hvigor 发现、构建诊断、产物选择、SHA-256 和签名 Profile 事实检查。
version: 0.4.0
category: build
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
---

# HarmonyOS Build

## Phase contract

1. **Input**：项目根、artifact 类型、mode、product、module/target 和上游源码状态。
2. **Preflight**：读取项目约束，发现 SDK/Hvigor，先生成计划。
3. **Execute**：运行唯一需要的 Hvigor 任务。
4. **Verify**：要求非空产物、类型和 SHA-256；需要时验证嵌入 Profile。
5. **Evidence**：记录命令、退出状态、产物相对路径和哈希，不记录签名秘密。
6. **Handoff**：HAP 交给 `harmonyos-targets`，release APP 交给 `harmonyos-release`。

## Workflow

1. 读取最近的 `AGENTS.md`、项目文档、`build-profile.json5` 和模块配置。
2. 定义 artifact（`hap` 或 `app`）、mode、product、module target、期望输出和完成信号。
3. 优先使用项目记录的 Hvigor wrapper 与版本；若不存在，再发现 DevEco Studio/SDK 中兼容的 Hvigor。
4. 项目陌生时先列出或打印任务计划，不直接 clean。
5. 只运行所需任务，保留完整退出状态和关键诊断。
6. 验证产物存在、非空、扩展名正确，并计算 SHA-256。
7. 签名类型重要时，只读取嵌入 Profile 的非敏感事实，核对 bundle、debug/release 和 distribution；不要打印 Profile 全文。
8. 设备安装交给 `harmonyos-targets`；发布候选交给 `harmonyos-release`。

## Build selection

- 本地设备或模拟器迭代使用 `hap + debug`。
- 只有明确需要已签名模块产物时才使用 `hap + release`。
- AppGallery 候选使用 `app + release`；不要把 HAP 描述成最终上传包。
- module target 与 app product 分开处理，例如 `module=entry@default` 可以搭配 `product=debug`。

## Guardrails

- 不根据退出码单独判断成功；必须有非空产物和哈希。
- 不在未证实缓存陈旧、且用户未授权时 clean。
- 保留项目本地签名设置；不要打印、复制、改写或提交密码、keystore、Profile 或证书。
- release 构建只是本地打包，不代表候选已通过，也不代表已提交商店。

## 完整插件

Skills Hub 便携版提供构建选择和验证纪律。需要跨项目稳定的 Hvigor 发现、统一证据或 Profile 检查脚本时，安装完整插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

完整插件不可用时，使用项目自己的 wrapper 和只读工具完成同等检查；无法核验的签名事实标记为 `needs_verification`。

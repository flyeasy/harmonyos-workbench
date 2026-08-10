---
name: harmonyos-release
description: 准备并校验 HarmonyOS AppGallery 发布候选。用于 release APP、签名/Profile、产物哈希、开放能力/权益/ACL 状态、AI 数据与评测交接、隐私、截图和发布交接；只在用户明确授权时执行商店提交。
version: 0.4.0
category: deploy
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
  - browser
---

# HarmonyOS Release

## Phase contract

1. **Input**：项目根、版本、bundle、product、签名期望和发布边界。
2. **Preflight**：只读检查版本控制、签名材料、隐私、能力账本、AI 交接和候选产物。
3. **Execute**：调用 `harmonyos-build` 生成 release APP；不自动提交商店。
4. **Verify**：校验 APP、SHA-256、签名、Profile、bundle 和 distribution。
5. **Evidence**：记录脱敏事实，不持久化密码、签名内容和本机绝对路径。
6. **Handoff**：严格区分 candidate ready、submitted 和 published。

## Workflow

1. 读取项目发布规则，定义版本、bundle、product、签名期望、证据和明确的发布边界。
2. 只读检查工作树、版本元数据、隐私文本、截图计划、外部服务状态和敏感文件跟踪情况。
3. 解决错误；dirty worktree、缺失截图、未完成隐私文案和未验证外部服务按项目政策列为 warning 或 blocker。
4. 使用 `harmonyos-build` 生成 `app + release` 候选。
5. 验证产物非空、SHA-256、签名、嵌入 Profile、期望 bundle、release 类型和 distribution。
6. 运行项目专用的隐私、元数据、截图和线上就绪门禁。
   - 开放能力、权益、ACL 和付费服务要求 `harmonyos-capabilities` 账本达到 `release_verified` 或明确阻塞；
   - AI 功能要求 `harmonyos-ai` 的数据、凭据、安全、评测和降级交接。
7. 在完整交接处停止。只有用户明确要求后才上传包、编辑 AppGallery 列表或点击提交。
8. 提交后再核对平台回执；没有回执时不能说 published。

## Release invariants

- 最终 AppGallery 包是签名 `.app`，不是模块 `.hap`。
- `build-profile.json5`、keystore、Profile、证书、密码材料、API key 和凭据不进入版本控制，除非项目政策明确允许且有安全存储。
- 不在报告中暴露签名材料路径、密码值、设备 serial 或私有项目路径。
- candidate ready 必须有签名/Profile 核验、期望 bundle、release/distribution、产物哈希和隐私扫描。
- `candidate ready`、`submitted` 和 `published` 是三个不同状态。
- 商店提交是外部发布动作，不能从“准备发布”推断授权。

## 完整插件

需要统一的仓库卫生、产物和 Profile 预检时安装完整插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

完整插件不可用时使用只读系统工具完成等价验证；任何无法验证的签名或隐私门禁都保持 `needs_verification`。

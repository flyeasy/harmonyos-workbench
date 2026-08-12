---
name: harmonyos-release
description: 准备并校验 HarmonyOS AppGallery 发布候选与发布推广交付物。用于 release APP、版本号、签名/Profile、产物哈希、图标/商店文案/隐私声明/截图素材、Xiaohongshu 图文、宣传脚本、Remotion 视频、开放能力/权益/ACL 状态、AI 数据与评测交接和发布交接；只在用户明确授权时执行商店提交或外部发布。
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

1. 读取项目发布规则，区分 `feature`（受影响快速检查）、`candidate`（包/签名和受影响门禁）与 `handoff`（公开材料和外部就绪），定义版本、bundle、product、签名四件套状态、证据和明确的发布边界。
2. 只在 candidate/handoff 边界做只读检查工作树、版本元数据、隐私文本、截图计划、外部服务状态和敏感文件跟踪情况。
3. 解决相关错误；dirty worktree、缺失截图、未完成隐私文案和未验证外部服务按项目政策列为 warning 或 blocker。对未变化的外部/公开材料阻塞记录输入指纹与最近检查，只有依赖变化、交接或提交前才重跑完成审计。
4. 先核对 P12（私钥）、CSR（密钥请求）、CER（签发证书）和 `.p7b` Profile 的关系：P12/CSR/CER 只有在公钥连续性已证明时才可复用；Profile 必须按精确 Bundle/App ID、分发类型重新签发，不能跨应用复用。debug Profile 设备绑定，release Profile 不得含 debug device 信息。
5. 使用 `harmonyos-build` 以项目专用 release product 生成 `app + release` 候选。`buildMode=release` 不是签名证明；product/signingConfig 与最终嵌入 Profile 是独立事实。
6. 验证产物非空、SHA-256、签名、嵌入 Profile、期望 bundle、release 类型和 distribution。
7. 在 candidate/handoff 边界设置期望 `versionName/versionCode` 与已知上一发布 `versionCode`，检查应用内配置精确匹配且 code 单调递增；不要猜测商店历史。
8. 检查商店素材：每个语言的应用名、一句话简介、完整介绍、截图、已审核的 HTTPS 隐私声明 URL/版本，以及源图标。当前基线为 1024×1024 PNG、≤3 MiB、无 alpha/透明通道、无预制圆角；提交前仍以目标 AGC 控制台规则复核。系统/商店图标另有不透明导出；应用内设置、功能图标与 VI 可以按实际界面使用透明、去底或矢量资源，不能机械照搬。生成图标必须保留来源与权利依据并人工查看，不能仅凭格式检查通过。
9. 若有小红书/宣传需求，产出标题、笔记正文、话题、封面与轮播图、安装入口、视频分镜/口播/字幕和 Remotion 渲染计划；每项主张都绑定当前候选版本与已验证事实。渲染成功不等于已发布，外部帖子或商店提交仍需明确授权。
10. 运行项目专用的隐私、元数据、截图和线上就绪门禁。
   - 开放能力、权益、ACL 和付费服务要求 `harmonyos-capabilities` 账本达到 `release_verified` 或明确阻塞；
   - AI 功能要求 `harmonyos-ai` 的数据、凭据、安全、评测和降级交接。
11. 在完整交接处停止。只有用户明确要求后才上传包、编辑 AppGallery 列表、发布小红书或点击提交。
12. 提交后再核对平台回执；没有回执时不能说 published。

## Release invariants

- 最终 AppGallery 包是签名 `.app`，不是模块 `.hap`。
- `buildMode=release`、目录名或打包成功都不是签名事实；以 `hap-sign-tool` 对精确 `.app` 的验证为准。
- P12/CSR/CER 可代表同一开发者身份，但 `.p7b` Profile 是应用授权，不可因同一证书而跨 Bundle/App ID 复用。
- 商店文案和隐私声明是发布事实，不是占位符：各语言都要有真实的一句话简介、完整介绍、截图和已审核 HTTPS 隐私声明。图标通过尺寸/格式检查后仍需人工确认无预制圆角、可读性与权利。
- `build-profile.json5`、keystore、Profile、证书、密码材料、API key 和凭据不进入版本控制，除非项目政策明确允许且有安全存储。
- 不在报告中暴露签名材料路径、密码值、设备 serial 或私有项目路径。
- candidate ready 必须有签名/Profile 核验、期望 bundle、release/distribution、产物哈希和隐私扫描。
- `candidate ready`、`submitted` 和 `published` 是三个不同状态。
- 商店提交是外部发布动作，不能从“准备发布”推断授权。
- 候选交接必须绑定 Git 提交；工作树是否干净和 `git diff --check` 结果需留档。临时目录、用户主目录或仅终端可见的证据不能构成发布结论。
- 外部集成把 `configured / ready_to_run / runtime_verified / release_verified` 分开；配置完成或 fixture 成功不等于生产互通。
- 内容型应用必须保留素材/生成来源、权利依据、技术检查、人工审核、设备体验与 `publishEligible` 状态；哈希不替代人工听审、观感或授权审查。

## 完整插件

需要统一的仓库卫生、产物和 Profile 预检时安装完整插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

完整插件不可用时使用只读系统工具完成等价验证；任何无法验证的签名或隐私门禁都保持 `needs_verification`。

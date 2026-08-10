---
name: harmonyos-build
description: 构建并校验 HarmonyOS、OpenHarmony 的 HAP 或 APP 产物。用于 Hvigor debug/release 构建、module/product 选择、SDK 与 Hvigor 发现、构建诊断、产物选择、SHA-256 和签名 Profile 事实检查。设备安装使用 harmonyos-targets；AppGallery 发布门禁使用 harmonyos-release。
---

# HarmonyOS Build

## Phase contract

1. **Input**：项目根、artifact 类型、mode、product、module/target 和上游源码状态。
2. **Preflight**：读取项目约束，发现 SDK/Hvigor，先生成计划。
3. **Execute**：运行唯一需要的 Hvigor 任务。
4. **Verify**：要求非空产物、类型和 SHA-256；需要时验证嵌入 Profile。
5. **Evidence**：写入 `harmonyos.workbench.evidence/v2`；项目内路径用相对路径。
6. **Handoff**：HAP 交给 `harmonyos-targets`，release APP 交给 `harmonyos-release`。

## Workflow

1. Read the nearest `AGENTS.md` and project ledger.
2. Resolve the plugin root from this Skill path. Never execute a project-relative `scripts/...`.
3. Define the artifact (`hap` or `app`), build mode, product, module target, expected output, and verification signal.
4. Run the stable launcher in dry-run mode only when the project, product/module scope, or toolchain is unfamiliar or changed; reuse the recorded plan during one unchanged feature batch:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py build \
  --project /path/to/project --artifact hap --mode debug \
  --product debug --target default --dry-run
```

5. Run without `--dry-run`, passing `--evidence` for the normalized record.
6. Verify the emitted artifact exists, is non-empty, and has the reported SHA-256.
7. When signing type matters, inspect the embedded Profile without printing its contents:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py profile \
  --artifact /path/to/app.hap --expected-type debug \
  --expected-bundle com.example.app
```

8. Hand device installation to `harmonyos-targets`. Hand release signing and publication gates to `harmonyos-release`.

## Build selection

- Use `hap + debug` for local device or simulator iteration.
- Use `hap + release` only when a signed module artifact is explicitly required.
- Use `app + release` for an AppGallery candidate. Never describe a HAP as the final AppGallery upload package.
- Preserve the project's local signing setup. Do not print, copy, rewrite, or commit signing passwords or material.
- Keep the module target and app product separate. For example, `module=entry@default` can be built with `product=debug`.

## Guardrails

- `host-fast` changes do not require a HAP merely because the project is HarmonyOS. At a `build-slice`, build one debug HAP for the coherent affected feature; reserve `app + release` for a candidate boundary.
- Prefer the project's documented Hvigor version over DevEco Studio's bundled version when they differ.
- Do not clean the project unless incremental output is demonstrably stale and the user authorized a clean build.
- Do not infer a successful build from exit code alone; require an artifact and hash.
- Treat release builds as local packaging, not publication.

Read [references/build-workflow.md](references/build-workflow.md) when choosing Hvigor tasks or diagnosing discovery failures.

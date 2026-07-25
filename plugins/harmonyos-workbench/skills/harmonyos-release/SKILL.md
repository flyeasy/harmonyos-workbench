---
name: harmonyos-release
description: 准备并校验 HarmonyOS AppGallery 发布候选。用于 release APP 选择、本地签名配置卫生、版本元数据、签名与 Profile 验证、产物哈希、隐私门禁、截图和发布交接。只在用户明确授权时执行商店提交；构建使用 harmonyos-build，设备截图使用 harmonyos-targets。
---

# HarmonyOS Release

## Phase contract

1. **Input**：项目根、版本、bundle、product、签名期望和发布边界。
2. **Preflight**：只读检查版本控制、签名材料、隐私和候选产物。
3. **Execute**：调用 `harmonyos-build` 生成 release APP；不自动提交商店。
4. **Verify**：校验 APP、SHA-256、签名、Profile、bundle 和 distribution。
5. **Evidence**：写入 `harmonyos.workbench.evidence/v2`；不持久化本机绝对路径。
6. **Handoff**：区分 candidate ready、submitted 和 published。

## Workflow

1. Read project release rules and define the release version, bundle, product, signing profile, evidence, and explicit publication boundary.
2. Resolve the plugin root from this Skill path and run the read-only generic preflight:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py release \
  --project /path/to/project --evidence artifacts/harmonyos-workbench/release/preflight.json
```

3. Resolve every error before building. Treat dirty worktree, missing screenshots, unfinished privacy text, and unverified external services as named warnings or blockers according to project policy.
4. Use `harmonyos-build` with `--artifact app --mode release` to generate the candidate.
5. Run preflight again with `--artifact ... --verify --expected-bundle ...`. Preserve the SHA-256 and verified Profile facts.
6. Run project-specific privacy, metadata, screenshot, and live-readiness gates.
7. Stop at a complete handoff unless the user explicitly asks to submit. Uploading a package, editing an AppGallery listing, or clicking submit is an external publication action and requires action-time confirmation.

## Release invariants

- The final AppGallery package is a signed `.app`, not a module `.hap`.
- Keep `build-profile.json5`, keystores, Profiles, certificates, encrypted password material, and credentials out of version control unless project policy explicitly says otherwise.
- Do not expose signing material paths or password values in reports.
- Require signature/Profile verification, expected bundle, release type, distribution, artifact hash, and privacy scan before calling a candidate ready.
- Separate “candidate ready” from “submitted” and “published”.

Read [references/appgallery-release-gates.md](references/appgallery-release-gates.md) for the release checklist.

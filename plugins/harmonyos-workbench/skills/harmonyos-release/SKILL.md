---
name: harmonyos-release
description: 准备并校验 HarmonyOS AppGallery 发布候选与发布推广交付物。用于 release APP 选择、本地签名配置卫生、版本号管理、签名与 Profile 验证、产物哈希、图标/商店文案/隐私声明/截图素材门禁、Xiaohongshu 图文、宣传脚本、Remotion 视频交付、开放能力/权益/ACL 状态、AI 数据与评测交接和发布交接。只在用户明确授权时执行商店提交或外部发布；能力账本使用 harmonyos-capabilities，AI 门禁使用 harmonyos-ai。
---

# HarmonyOS Release

## Phase contract

1. **Input**：项目根、版本计划、bundle、product、签名期望、四件套、商店/推广素材和发布边界。
2. **Preflight**：只读检查版本控制、签名材料、隐私、能力账本、AI 交接和候选产物。
3. **Execute**：调用 `harmonyos-build` 生成 release APP；不自动提交商店。
4. **Verify**：校验 APP、SHA-256、签名、Profile、bundle 和 distribution。
5. **Evidence**：写入 `harmonyos.workbench.evidence/v2`；不持久化本机绝对路径。
6. **Handoff**：区分 candidate ready、submitted 和 published。

## Workflow

1. Read project release rules and classify the boundary: `feature` uses only affected fast checks, `candidate` adds package/signing and affected release gates, and `handoff` adds public materials and external readiness. Do not use the full handoff gate as an inner-loop test.
2. Resolve the plugin root from this Skill path and run the read-only generic preflight at a candidate or handoff boundary:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py release \
  --project /path/to/project --evidence artifacts/harmonyos-workbench/release/preflight.json
```

3. Resolve every relevant error before building. Treat dirty worktree, missing screenshots, unfinished privacy text, stale/temporary evidence and unverified external services as named warnings or blockers according to project policy. Cache an unchanged external/public-material blocker with its input fingerprint and last check; only re-run that completion gate when its inputs change, at handoff, or before submission. A candidate that will be handed off or tagged must point to a Git commit; use the strict clean-worktree policy when the project requires reproducibility.
4. At a signing setup or candidate boundary, audit the local P12/CSR/CER/Profile quartet before changing a project configuration. This is read-only and does not print material paths or values:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py signing-audit \
  --kind release --p12 /private/release.p12 --csr /private/release.csr \
  --certificate /private/release.cer --profile /private/release.p7b \
  --expected-bundle com.example.app --expected-app-id 123456789
```

Use `--verify-p12` only when a local, hidden password prompt is acceptable and P12 ↔ CSR/CER continuity must be proved. Before AppGallery issues a per-app Profile, use `--allow-identity-only`; do not interpret this as release readiness. Use `--kind debug` for a development Profile; it must be device-bound and must never substitute for a release Profile.
5. Use `harmonyos-build` with `--artifact app --mode release --product <release-product>` to generate the candidate. Product and compiler mode are separate facts.
6. Run preflight again with `--artifact ... --verify --expected-bundle ...`. Preserve the SHA-256 and verified Profile facts.
7. Audit the store listing at candidate/handoff: app name, one-line introduction, full introduction, reviewed privacy statement URL/version, screenshots, and the opaque source icon. The complete plugin supplies a read-only baseline check for a 1024×1024 PNG, ≤3 MiB, no alpha/transparency; visually review that the source icon has no pre-rounded mask. It does not upload assets or invent legal claims:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py listing-audit \
  --project /path/to/project --icon /private/store/icon.png \
  --listing docs/release/store-listing.json \
  --evidence artifacts/harmonyos-workbench/release/listing.json
```

8. Set the expected `versionName`/`versionCode` and the explicitly known previous published `versionCode` at candidate/handoff. The preflight can reject a mismatch or non-incrementing code; it never guesses a store's release history.
9. When the request includes Xiaohongshu, launch images, a video script or Remotion render, add the `promotion_campaign` delivery profile. Bind claims, QR/link assets, narration/captions and render metadata to the current candidate; do not publish or imply availability without action-time authorization and external verification.
10. Draft copy only from verified product behavior: one-line introduction states the primary user value; the full introduction covers actual user-facing features and limits. Draft a privacy statement only from the capability/data inventory and mark it `needs_review`; never represent generated copy as a legal/privacy conclusion. When asked to create an actual raster icon, use the image-generation capability, retain provenance/rights notes, export an opaque PNG, then rerun the audit.
11. Run project-specific privacy, metadata, screenshot, and live-readiness gates. When the app uses open capabilities, entitlements, ACL or paid services, require the `harmonyos-capabilities` ledger to reach `release_verified` or name the blocker. When it uses AI, require the `harmonyos-ai` data, credential, safety, evaluation and fallback handoff.
12. Stop at a complete handoff unless the user explicitly asks to submit. Uploading a package, editing an AppGallery listing, publishing a Xiaohongshu post, or clicking submit is an external publication action and requires action-time confirmation.

## Release invariants

- The final AppGallery package is a signed `.app`, not a module `.hap`.
- A release compiler mode, release-named directory, or successful package task is not signing evidence. Candidate proof is the exact `.app` plus `hap-sign-tool` verification.
- P12 (private key), CSR (key request), CER (issued public certificate), and `.p7b` Profile have different reuse rules: the same developer identity may be reused only after CSR/CER/P12 key continuity is checked; every release Profile must match the exact Bundle and App ID, intended distribution, certificate key, and have no debug device data. Never reuse a Profile across applications just because its certificate is reusable.
- Keep debug automatic-signing material separate from release material. A debug Profile is device-bound; a release Profile is AppGallery-distributed and must not contain debug device information.
- Store copy is release evidence, not decoration: every locale needs a truthful name, one-line introduction, full introduction, screenshot set, and reviewed HTTPS privacy statement. The source icon baseline is 1024×1024 PNG, ≤3 MiB, no alpha/transparency and no pre-rounded mask; validate the current AGC console rule again immediately before submission.
- Never place the listing text, private privacy-review evidence, icon source path, or generated-media provenance into a public release record. Preserve provenance and rights basis privately for generated or third-party assets.
- The system-facing app icon has a separate opaque export contract; in-app settings/feature icons and VI are owned by `harmonyos-design` and may use transparency/vector/background removal when that surface benefits. Do not apply the store export rule mechanically to UI assets, or leak a transparent UI export into a system-facing icon slot.
- Promotional assets are bound to a candidate's version, artifact facts and verified claims. A rendered Remotion video, generated image, QR code or draft post never proves that the app is published or that a platform post is live.
- Keep `build-profile.json5`, keystores, Profiles, certificates, encrypted password material, and credentials out of version control unless project policy explicitly says otherwise.
- Do not expose signing material paths or password values in reports.
- Require signature/Profile verification, expected bundle, release type, distribution, artifact hash, and privacy scan before calling a candidate ready.
- Do not treat a visible switch, pending application or approved entitlement as runtime/release verification; re-check app identity, expiry, region, quota/payment and signed-release behavior.
- For AI, require model/Kit version, evaluation-set version, abuse/failure handling, credential boundary and unverified limitations; a mocked answer is not live readiness.
- Separate “candidate ready” from “submitted” and “published”.
- Release evidence belongs under the project-approved durable evidence root. `/tmp`, `/private/tmp`, user-home paths and only-in-terminal evidence cannot support a release conclusion.
- For external integrations, retain a redacted matrix result plus real automated or manual evidence. “Environment configured” and fixture success are readiness facts, not production interoperability.
- For content-backed products, retain a content release ledger: source/generation provenance, license or rights basis, technical checks, required human review, device experience and the current `publishEligible` state. Never infer publishability from a file hash alone.

Read [references/appgallery-release-gates.md](references/appgallery-release-gates.md) for the release checklist.
Read [references/store-listing.md](references/store-listing.md) when preparing or checking store assets and copy.
Read [references/promotion-delivery.md](references/promotion-delivery.md) when making Xiaohongshu content, launch imagery, a script or a Remotion video.

---
name: harmonyos-test
description: 规划、执行并归一化 HarmonyOS 应用和元服务测试。用于 Local Test、Instrument Test、项目 smoke、Hypium UI、ArkWeb Selenium、DevEco Testing 专项、性能与回归证据。设备测试必须使用 harmonyos-targets 的项目绑定、有效租约和目标预检；纯体验审查使用 harmonyos-review。
---

# HarmonyOS Test

## Phase contract

1. **Input**：项目根、变更行为、目标层、目标角色和上游产物。
2. **Preflight**：选择最小测试层；设备测试验证项目绑定、租约和几何证据。
3. **Execute**：运行一个确定性测试批次。
4. **Verify**：区分产品失败、环境阻塞和测试工具假阴性。
5. **Evidence**：写入脱敏的 `harmonyos.workbench.evidence/v2`。
6. **Handoff**：结果交给 `harmonyos-review`；发布专项交给 `harmonyos-release`。

## Workflow

1. Read project instructions and define the changed behavior, expected signal, target form factor, evidence, and exit condition.
2. Resolve the plugin root from this Skill path; do not call a project-relative `scripts/...`.
3. For emulator or physical-device work, run `harmonyos-targets acquire` and `preflight --evidence ...` first.
4. Generate a capability plan before running expensive tests:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py test-plan \
  --project /path/to/project --target emulator --app-kind app --role primary
```

5. Run the smallest useful layer first: static/project smoke, Local Test, Instrument Test, deterministic Hypium UI, then DevEco Testing specialty services.
6. Run a host command through the evidence wrapper without a shell:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py test-run \
  --project /path/to/project --label smoke --target host \
  -- node scripts/smoke_all.js
```

7. For UI automation, pass `--ui --target emulator|physical --target-preflight-evidence <json>`. The runner rejects missing or mismatched project/role/target evidence.
8. Use `harmonyos-build` for build gates and `harmonyos-targets` for deployment and screenshots.
9. Operate the DevEco Testing client with computer use only when a CLI cannot perform the service. Select the exact installed bundle and shortest representative duration.
10. Inspect local task artifacts without copying private data:

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py testing-inventory --latest 3
```

11. Normalize results as passed, failed, blocked, or needs verification. Do not report unavailable real-device services as passed.

## Coverage selection

- Use Local/Instrument tests for deterministic logic and framework behavior.
- Use Hypium for repeatable user paths and multi-device UI. For ArkWeb, use Hypium's Selenium bridge with a matching ChromeDriver.
- Use DevEco Testing for performance, stability, memory leak, UX, power, security, exploration, regression, and precheck services.
- Keep backend, relay, encryption, and cross-process end-to-end tests when the app depends on external systems; UI traversal does not replace them.
- Prefer semantic selectors. Coordinate clicks are valid only with matching target fingerprint and current geometry preflight.

## Guardrails

- Obtain explicit approval before granting permissions, accepting app privacy prompts on behalf of a test account, running destructive preprocessing, or starting long/cloud tests with quota impact.
- Do not record credentials, terminal contents, tokens, or private device identifiers in durable reports. Redact evidence.
- Treat short specialty runs as smoke evidence, not statistically representative performance or stability evidence.
- Stop after three attempts on the same failing path and preserve the blocker.
- Never retry a UI click on a different connected target without rebinding and new evidence.

Read [references/deveco-testing-26.md](references/deveco-testing-26.md) for the service matrix and [references/hypium-arkweb.md](references/hypium-arkweb.md) for Python and WebView conditions.

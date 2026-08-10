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

1. 先按 `host-fast / build-slice / device-slice / candidate` 选择验证车道；只在模拟器/真机任务前获取 `harmonyos-targets` 租约和预检。小的主机循环不因项目“有设备”而自动升级为设备或发布循环。
2. `device-slice` 或 DevEco 专项前生成能力计划；纯主机层不必为此启动或占用目标：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py test-plan \
  --project /path/to/project --target emulator --app-kind app --role primary
```

3. 从最小层开始：静态/smoke、Local、Instrument、确定性 Hypium UI、DevEco Testing 专项；同一功能批次复用主机结果和目标租约，在批次边界再构建和跑代表场景。
4. 外部服务、账号、支付、AI、局域网或配套硬件先运行只读集成预检：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py integration-plan \
  --project /path/to/project \
  --manifest docs/integration-matrix.json \
  --env-file /private/path/to/test.env \
  --evidence artifacts/harmonyos-workbench/test/integration-plan.json
```

矩阵只含变量名称、读写性质、隔离确认、证据方式和发布影响；不会连接服务或输出变量值。写远端必须声明 `writes_isolated_data` 和隔离确认，生产实例/个人 vault/不明硬件状态一律阻塞。
5. 通过无 shell 的 evidence wrapper 运行主机命令：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py test-run \
  --project /path/to/project --label smoke --target host \
  -- node scripts/smoke_all.js
```

6. UI 自动化传入 `--ui --target ... --target-preflight-evidence <json>`；语义选择器默认可复用 30 分钟内的匹配预检（可配置至 60 分钟）。坐标点击另加 `--coordinate-ui`，始终是 10 分钟几何门禁。wrapper 拒绝不匹配租约/指纹证据。构建、部署和截图分别交给 Build、Targets。
7. 只有 CLI 无法完成专项时才使用 DevEco Testing 客户端；选精确 bundle 和最短代表时长。可用 `testing-inventory --latest 3` 检查本地任务，不复制私有数据。

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py testing-inventory --latest 3
```

8. 归一化为 `passed / failed / blocked / needs_verification`；真实设备服务不可用不能写成通过。

## Coverage selection

- Use Local/Instrument tests for deterministic logic and framework behavior.
- Use Hypium for repeatable user paths and multi-device UI. For ArkWeb, use Hypium's Selenium bridge with a matching ChromeDriver.
- Use DevEco Testing for performance, stability, memory leak, UX, power, security, exploration, regression, and precheck services.
- Keep backend, relay, encryption, and cross-process end-to-end tests when the app depends on external systems; UI traversal does not replace them.
- Prefer semantic selectors. Coordinate clicks are valid only with matching target fingerprint and current geometry preflight.
- 对只做主机验证的用户可见改动，账本写明 `coverage debt`：变更面、已有主机证据、待补设备场景、目标规格和关闭边界。不得把债务当作 device-complete；合并设备敏感功能、候选交付或发布前必须关闭。
- 长运行按风险分层：`post-flash-smoke`（刷机/基本链路）、`behavioral-hil`（相关无线/音频/HID/时序行为）、`soak`（合并/发布或持续性风险变更）。不要把每次小改动升级为 soak。

## Guardrails

- Obtain explicit approval before granting permissions, accepting app privacy prompts on behalf of a test account, running destructive preprocessing, or starting long/cloud tests with quota impact.
- Do not record credentials, terminal contents, tokens, or private device identifiers in durable reports. Redact evidence.
- Treat short specialty runs as smoke evidence, not statistically representative performance or stability evidence.
- Stop after three attempts on the same failing path and preserve the blocker.
- Never retry a UI click on a different connected target without rebinding and new evidence.

Read [references/validation-lanes.md](references/validation-lanes.md) for lane selection and deferred-coverage rules, [references/deveco-testing-26.md](references/deveco-testing-26.md) for the service matrix, and [references/hypium-arkweb.md](references/hypium-arkweb.md) for Python and WebView conditions.

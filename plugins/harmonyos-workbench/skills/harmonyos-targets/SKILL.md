---
name: harmonyos-targets
description: 为 HarmonyOS 项目发现、分配、固定、租赁和验证物理设备及 DevEco 模拟器。用于多项目并行开发、多模拟器管理、稳定选择手机/平板/折叠屏目标、唯一 HDC 端口分配、安装启动、截图、UI 自动化前几何校验和设备争用诊断。任何设备安装、截图或 UI 点击前都应使用；纯构建或纯主机测试使用对应 harmonyos-* Skill。
---

# HarmonyOS Targets

把“这次连上了哪个设备”升级为“这个项目固定拥有哪个目标角色”。稳定身份使用模拟器 UUID 或物理设备 serial；显示名称和临时 HDC serial 不能单独作为身份。

## Phase contract

1. **Input**：项目根、目标角色、设备类型/API/屏幕要求和已有绑定。
2. **Preflight**：按操作检查精确设备身份；调试类操作再检查绑定、租约、端口和规格漂移。
3. **Execute**：仅安装可直达精确真机；启动、调试、截图、UI 自动化或采证才获取租约。
4. **Verify**：核对精确 serial、运行状态、指纹和截图几何。
5. **Evidence**：记录项目 ID、角色、target key、规格和产物哈希；调试/体验证据另记录租约。
6. **Handoff**：把已验证目标交给 `harmonyos-test` 或 `harmonyos-review`。

## Selection and bridge

1. 先运行 `status` 解析项目现有绑定。
2. 没有绑定时：
   - 已知目标就用 `bind` 指定精确 UUID/name；
   - 只知道规格就用 `allocate`，必须给出设备类型、API、屏幕或名称约束；
   - 候选跨越不同规格时停止，不猜“主模拟器”。
3. 用户明确要求“推送/安装到真实手机”且不要求启动、调试、截图或验证时，用 `install --target-serial <exact-connected-serial> --artifact <hap>` 直接安装：不申请租约、不绑定、不启动应用。它只证明安装命令结果，不能写成运行或体验通过。
4. 即将启动、调试、截图、UI 验证或采证时，才在 `device-slice` 运行 `acquire` 获取项目排他租约；主机循环可保留需求矩阵和持久绑定，但不抢占模拟器。
5. 启动前运行项目 `doctor`；UI 自动化前运行 `preflight`。全局 `doctor` 只用于维护模拟器池。
6. 调试类安装、启动、截图和点击只使用绑定解析出的 serial；直接安装只接受用户指定且当前已连接的精确真机 serial，不猜第一个设备。
7. 完成调试会话后运行 `release`；绑定仍保留供下次固定选择。

## 项目脚本的目标桥接

项目自带的 HDC、MCP 或端到端脚本不得硬编码 `127.0.0.1:5559`、裸 serial 或“第一个已连接设备”。在执行这类脚本前，从一次有效租约和几何预检生成一个本地桥接文件，再以环境变量或显式参数交给脚本：

```bash
bridge_dir="$(mktemp -d)"
python3 <plugin-root>/scripts/harmonyos_workbench.py targets bridge \
  --project /path/to/project --role primary --out "$bridge_dir/target-bridge.json"
HARMONYOS_TARGET_BRIDGE="$bridge_dir/target-bridge.json" node scripts/project-smoke.mjs
```

桥接文件含运行时 serial，因此权限为 `0600`，仅作当前会话运行状态：不得提交、截图、复制到证据或长期保存。项目脚本应在调用前检查 `leaseExpiresAt` 和 `fingerprintDigest`，并拒绝缺桥接或失效桥接。这样可以让多项目并行时的脚本沿用 Workbench 已分配的角色，而非绕过它。

## 并发与固定规则

- 同一个模拟器 UUID 默认只能绑定一个项目和一个角色。
- 每个绑定获得唯一 HDC 端口；端口同时检查全局登记和运行进程。
- 租约通过文件锁原子更新，避免两个 Codex 任务同时抢占。
- 租约过期不自动把持久绑定转给另一个项目；重新分配必须显式 `release → unbind → bind/allocate`。
- 多规格使用独立角色；任何身份/规格漂移、Offline 或多目标歧义都阻塞。不得自动 reset、coldboot、清数据或影响其他项目。

## UI 自动化门禁

- 每轮先确认租约与目标匹配；优先语义节点。连续批次内可复用匹配的语义预检，坐标记录仍要求当前指纹、方向和 10 分钟内几何锚点，规格变化即失效。点击失败先检查目标、前台 bundle、PID、可见期和几何。

统一入口为 `python3 <plugin-root>/scripts/harmonyos_workbench.py targets <action>`；不从项目目录调用重名 `scripts/...`。租约、端口和恢复细节见 [references/target-leases.md](references/target-leases.md)，模拟器细节见 [references/device-workflow.md](references/device-workflow.md)。

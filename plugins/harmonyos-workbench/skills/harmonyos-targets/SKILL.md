---
name: harmonyos-targets
description: 为 HarmonyOS 项目发现、分配、固定、租赁和验证物理设备及 DevEco 模拟器。用于多项目并行开发、多模拟器管理、稳定选择手机/平板/折叠屏目标、唯一 HDC 端口分配、安装启动、截图、UI 自动化前几何校验和设备争用诊断。任何设备安装、截图或 UI 点击前都应使用；纯构建或纯主机测试使用对应 harmonyos-* Skill。
---

# HarmonyOS Targets

把“这次连上了哪个设备”升级为“这个项目固定拥有哪个目标角色”。稳定身份使用模拟器 UUID 或物理设备 serial；显示名称和临时 HDC serial 不能单独作为身份。

## Phase contract

1. **Input**：项目根、目标角色、设备类型/API/屏幕要求和已有绑定。
2. **Preflight**：检查实例配置、全局绑定、租约、HDC 端口和规格漂移。
3. **Execute**：分配或解析目标，获取租约，再启动、安装、运行或采证。
4. **Verify**：核对精确 serial、运行状态、指纹和截图几何。
5. **Evidence**：记录项目 ID、角色、target key、租约、规格和产物哈希。
6. **Handoff**：把已验证目标交给 `harmonyos-test` 或 `harmonyos-review`。

## 必须遵守的选择顺序

1. 先运行 `status` 解析项目现有绑定。
2. 没有绑定时：
   - 已知目标就用 `bind` 指定精确 UUID/name；
   - 只知道规格就用 `allocate`，必须给出设备类型、API、屏幕或名称约束；
   - 候选跨越不同规格时停止，不猜“主模拟器”。
3. 运行 `acquire` 获取项目排他租约。
4. 启动前对绑定角色运行 `doctor --project ... --role ...`；UI 自动化前运行 `preflight`。全局 `doctor` 只用于维护整个模拟器池。
5. 所有安装、启动、截图和点击只使用绑定解析出的 serial。
6. 完成本轮设备操作后运行 `release`；绑定仍保留供下次固定选择。

## 稳定脚本入口

根据本 Skill 路径解析插件根，调用统一入口：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py targets inventory
python3 <plugin-root>/scripts/harmonyos_workbench.py targets status --project /path/to/project
python3 <plugin-root>/scripts/harmonyos_workbench.py targets allocate \
  --project /path/to/project --role primary --device-type phone --api-version 20
python3 <plugin-root>/scripts/harmonyos_workbench.py targets acquire \
  --project /path/to/project --role primary
python3 <plugin-root>/scripts/harmonyos_workbench.py targets preflight \
  --project /path/to/project --role primary
```

不要从项目工作目录调用相对的 `scripts/...`。

## 并发与固定规则

- 同一个模拟器 UUID 默认只能绑定一个项目和一个角色。
- 每个绑定获得唯一 HDC 端口；端口同时检查全局登记和运行进程。
- 租约通过文件锁原子更新，避免两个 Codex 任务同时抢占。
- 租约过期不自动把持久绑定转给另一个项目；重新分配必须显式 `release → unbind → bind/allocate`。
- 同一项目需要手机、平板和折叠屏时，分别使用 `primary / tablet / foldable` 等角色和独立实例。
- 名称、UUID、instancePath、镜像、API、设备类型或显示规格漂移时阻塞；只有人工核实后才可 `--accept-drift`。
- Offline 目标不可用。多个 HDC 目标连接时绝不选第一个。
- 不自动 reset、coldboot、删除实例、清数据或覆盖别的项目绑定。

## UI 自动化门禁

- 每轮点击前确认租约仍有效。
- 核对截图像素尺寸属于绑定指纹的单屏或双屏规格，方向反转可以接受。
- 优先语义选择器、稳定 key 和可访问性节点。
- 使用坐标时记录目标指纹、方向、截图和锚点；规格变化后坐标证据立即失效。
- 点击失败先检查目标、前台 bundle、PID、瞬态可见期和几何，不直接判定产品故障。

完整租约、端口与恢复规则见 [references/target-leases.md](references/target-leases.md)，模拟器启动细节见 [references/device-workflow.md](references/device-workflow.md)。

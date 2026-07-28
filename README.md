# HarmonyOS Workbench

面向 Codex 的端到端 HarmonyOS / OpenHarmony 开发工作台。它把产品设计、ArkTS/ArkUI 开发、Hvigor 构建、模拟器与真机分配、分层测试、体验审查和 AppGallery 发布预检组织为一条可暂停、可恢复、可复核的流程。

> 独立、非官方社区项目。HarmonyOS、OpenHarmony、ArkUI、华为及相关名称和商标归各自权利人所有。

## 为什么做这个项目

HarmonyOS 项目真正困难的部分通常不是某一条命令，而是跨阶段的一致性：

- 需求、代码、构建产物和设备证据是否来自同一个项目状态；
- 多个项目并行时，是否稳定使用各自绑定的模拟器或真机；
- 设备规格、屏幕几何和 HDC 端口变化后，旧坐标与旧证据是否被及时判定为失效；
- 测试、体验审查和发布结论是否准确区分“已验证”“失败”“被阻塞”和“仍需验证”。

HarmonyOS Workbench 用统一阶段契约、项目级目标绑定、排他租约、规格指纹和脱敏证据记录解决这些问题。

## 能力

| 阶段 | Skill | 主要产出 |
| --- | --- | --- |
| 入口与编排 | `harmonyos-workbench` | 阶段路由、账本、交接与完成挑战 |
| 产品与界面 | `harmonyos-design` | HarmonyOS 设计基线与 ArkUI 落点 |
| 功能实现 | `harmonyos-develop` | ArkTS/ArkUI 架构、状态与平台集成 |
| 构建 | `harmonyos-build` | 可复现 Hvigor 构建与 artifact 校验 |
| 目标管理 | `harmonyos-targets` | 模拟器/真机发现、绑定、租约、端口和几何门禁 |
| 测试 | `harmonyos-test` | Local、Instrument、Hypium、ArkWeb 与专项测试证据 |
| 审查 | `harmonyos-review` | 有证据的体验、适配、无障碍和性能发现 |
| 发布 | `harmonyos-release` | 签名、Profile、仓库卫生与 AppGallery 预检 |
| 动效术语 | `harmonyos-motion` | 动效现象到术语、诊断分支和 ArkUI 能力映射 |

## 安装

要求：

- 已安装支持插件 marketplace 的 Codex；
- HarmonyOS 设备相关流程需要本机 DevEco Studio / SDK、HDC 和 Emulator 工具；
- Python 3.10 或更高版本。

添加公开 marketplace 并安装插件：

```bash
codex plugin marketplace add flyeasy/harmonyos-workbench@main
codex plugin add harmonyos-workbench@harmonyos-workbench
```

也可以从 [Skills Hub 上的 `@flyeasy`](https://skills-hub.ai/u/flyeasy) 安装公开的单文件便携版。只需要统一入口时：

```bash
npx @skills-hub-ai/cli install harmonyos-workbench --target codex
```

需要把九个阶段能力全部安装到本机时：

```bash
skills=(
  harmonyos-workbench harmonyos-design harmonyos-develop
  harmonyos-build harmonyos-targets harmonyos-test
  harmonyos-review harmonyos-release harmonyos-motion
)

for skill in "${skills[@]}"; do
  npx @skills-hub-ai/cli install "$skill" --target codex
done
```

便携版条目：

- [`harmonyos-workbench`](https://skills-hub.ai/skills/harmonyos-workbench)：端到端入口与阶段路由；
- [`harmonyos-design`](https://skills-hub.ai/skills/harmonyos-design)、[`harmonyos-develop`](https://skills-hub.ai/skills/harmonyos-develop)、[`harmonyos-build`](https://skills-hub.ai/skills/harmonyos-build)；
- [`harmonyos-targets`](https://skills-hub.ai/skills/harmonyos-targets)、[`harmonyos-test`](https://skills-hub.ai/skills/harmonyos-test)、[`harmonyos-review`](https://skills-hub.ai/skills/harmonyos-review)；
- [`harmonyos-release`](https://skills-hub.ai/skills/harmonyos-release)、[`harmonyos-motion`](https://skills-hub.ai/skills/harmonyos-motion)。

Skills Hub 便携版保留统一阶段契约、路由规则和安全边界，适合发现与单文件安装。完整 Codex 插件额外提供目标注册表、排他租约、HDC 端口分配、证据校验和辅助脚本；涉及多项目、多模拟器或可执行发布门禁时优先使用完整插件。

安装后可从总入口开始：

```text
用 harmonyos-workbench 端到端完成这个 HarmonyOS 任务，并保留可复核证据。
```

## 多项目、多模拟器工作流

目标管理遵循四条硬规则：

1. 每个项目和角色固定绑定一个目标，不在运行中“随便取第一个在线设备”。
2. 启动、安装、截图和 UI 自动化前必须持有有效的排他租约。
3. 每个模拟器绑定独立 HDC 端口；设备规格或屏幕几何漂移时阻断旧坐标继续执行。
4. UI 测试必须引用十分钟内生成、且与项目、角色、目标指纹和租约一致的预检证据。

快速查看命令：

```bash
python3 plugins/harmonyos-workbench/skills/harmonyos-targets/scripts/harmonyos_targets.py --help
```

## 隐私与安全

- 本地目标注册表位于 `~/.codex/state/harmonyos-workbench/`，目录权限为 `0700`，文件权限为 `0600`。
- 注册表不保存项目绝对路径、主机名或进程 ID；运行所需的原始设备标识只保留在本机状态和即时 CLI 输出中。
- 持久化证据使用 `harmonyos.workbench.evidence/v2`，记录项目 ID、设备标识哈希和项目相对路径。
- 测试输出会遮蔽常见密钥格式、用户主目录和项目绝对路径。
- 插件不会替你执行商店发布、重置模拟器或删除设备数据；这些动作需要单独的明确授权。

提交安全问题前请阅读 [SECURITY.md](SECURITY.md)。不要在公开 issue 中粘贴令牌、签名材料、设备序列号、真实项目路径或未脱敏日志。

## 开发与验证

```bash
cd plugins/harmonyos-workbench
python3 -m unittest discover -s tests -v

for skill in skills/*; do
  python3 /path/to/skill-creator/scripts/quick_validate.py "$skill"
done

python3 /path/to/plugin-creator/scripts/validate_plugin.py .
```

测试使用合成设备 UUID、序列号、端口和目录，不需要真实 HarmonyOS 设备。

## 来源与许可

本项目以 Apache License 2.0 发布。设计、审查和动效能力的部分内容改编自 [dososo/HarmonyOS-Design](https://github.com/dososo/HarmonyOS-Design)，基于提交 `205afcbf1d8170239477a98a8472089d4ab7b86c`，相关文件保留了显著修改声明。完整归属信息见 [NOTICE](NOTICE)。

外部官方资料仅以链接、摘要和来源登记形式引用；仓库许可不覆盖第三方商标、字体、品牌资产或被引用资料。

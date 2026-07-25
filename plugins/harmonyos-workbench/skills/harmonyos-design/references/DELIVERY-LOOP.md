# HarmonyOS 设计实现与设备验证循环

> 性质：H4 项目工作流。用于把设计改动从源码推进到可复核的设备证据。

## 目录

1. 最小循环
2. 验证层级
3. 设备验证协议
4. UI 交互矩阵
5. 完成挑战
6. 与其他 HarmonyOS Skill 配合

## 1. 最小循环

每轮只处理一个连贯批次：

```text
Contract
→ Expected signal
→ Focused inspection
→ Coherent edit
→ Static/contract check
→ Build
→ Explicit target install
→ Real interaction
→ Evidence challenge
→ Ledger update
```

任务契约至少写：

- target；
- out of scope；
- expected signal；
- verification；
- exit condition。

多问题任务把未解决项写进项目账本，状态使用：

- active；
- needs verification；
- queued；
- blocked；
- done。

## 2. 验证层级

从便宜到昂贵：

| 层级 | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| 源码/契约检查 | API、所有权、反例和静态结构 | 真实布局与生命周期 |
| ArkTS 编译 | 目标 SDK 类型与资源可编译 | 交互正确 |
| 安装/启动 | 产物与目标兼容、页面可创建 | 完整路径稳定 |
| 自动化设备流 | 可重复状态转换和回归 | 工具不支持的手势/辅助功能 |
| 人工目标设备 | 手感、长按拖拽、视觉和复杂输入 | 大规模性能统计 |
| 性能/故障证据 | PID、内存、长帧、AppFreeze | 产品任务是否易懂 |

不要跨级宣称。例如：

- 编译成功不能证明动效连续；
- 单张截图不能证明可打断；
- 静态 guard 不能证明 50MB 流式处理完成；
- 模拟器结果不能自动等同目标真机。

## 3. 设备验证协议

### 预检

- 明确 HDC target，不使用“当前默认设备”猜测；
- 记录设备形态、API、窗口和输入；
- 确认使用冷启动还是既有暖态设备；
- 明确保留数据覆盖安装还是清数据安装；
- 记录测试样本和前置页面；
- 安装后核对 bundle、版本与产物哈希（适用时）。

### 运行中

- 记录起始 PID；
- 截图与 layout dump 互相佐证；
- 使用稳定语义节点，坐标只作受控后备；
- 瞬态控件在操作前重新唤出；
- 路由切换后等待页面语义，而不是固定长 sleep；
- 失败时先检查前台应用、PID、日志和测试前置。

### 结束

- 记录最终 PID；
- 检查 jscrash、AppFreeze、Fatal 和目标模块错误；
- 对内存敏感路径记录峰值/回落；
- 保存关键状态截图或录屏；
- 记录未验证设备、输入和主题；
- 清理测试记录、临时服务或设备数据时说明范围。

## 4. UI 交互矩阵

根据改动选相关项，不机械全跑：

### 生命周期

- 首次进入；
- 返回再进入；
- 前后台；
- 冷启动/暖启动；
- 保留数据覆盖安装；
- 页面离开时 timer/listener 是否停止。

### 状态

- 空/有内容；
- loading/success/failure；
- enabled/disabled；
- selected/unselected；
- online/degraded/offline；
- 新请求覆盖旧请求；
- 删除/撤销/恢复。

### 交互

- 正常点击；
- 快速重复点击；
- 移出取消；
- 反向打断；
- 滚动后瞬态控件；
- 长按拖拽；
- 键盘/鼠标/遥控器（适用时）。

### 适配

- 窄/宽窗口；
- 横竖屏或折叠变化；
- 浅/深色；
- 默认/大字体；
- 中文/英文与长文本；
- safe area 与 IME。

### 共享路径

- 页面 A → B → A；
- 格式 A → B → A；
- 旧数据 → 新版本；
- 多轮切换；
- 异常状态后返回主路径。

## 5. 完成挑战

宣布完成前主动寻找反例：

- 是否只修了一个格式，根因仍在共享层？
- 是否测试的是新 HAP，但交付 APP 仍是旧代码？
- 是否自动化失败来自旧样本或脏前置？
- 是否旧 timer、listener 或 request 会晚到覆盖新状态？
- 是否只验证了 happy path？
- 是否把“安全阻断”写成“功能已支持”？
- 是否遗漏用户早先提出的事项？

若证据冲突，使用 `needs verification`，不要反复跑同一路径而不改变假设。

## 6. 与其他 HarmonyOS Skill 配合

在当前环境可用时：

- 用构建 Skill 发现 Hvigor/SDK、区分 HAP 与 APP、记录哈希；
- 用设备 Skill 固定 target、安装、启动、截图和多设备操作；
- 用测试 Skill 选择 unit、Instrument、Hypium、ArkWeb 或设备 UI 证据；
- 只有用户明确要求发行时才使用发布 Skill。

本 Skill 负责产品和交互判断，不复制签名、商店发布或设备管理流程。最终结论要把设计证据、构建证据、设备证据和发布证据分开陈述。

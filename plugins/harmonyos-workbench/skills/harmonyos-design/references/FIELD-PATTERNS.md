# HarmonyOS 项目实战模式

> 性质：从近期 HarmonyOS 项目交付中提炼的 H4 项目经验，不是华为官方规范。  
> 使用时机：现有工程涉及异步状态、跨页面数据、动态列表、WebView/IME、多格式内容、瞬态反馈或设备自动化时。

## 目录

1. 状态维度与权威源
2. 页面与内容所有权
3. 生命周期和初始化
4. 动态集合与同帧重入
5. 瞬态反馈与计时器
6. Safe area、IME 与本地几何
7. 失败关闭与未来扩展
8. 自动化证据的常见假象

## 1. 状态维度与权威源

### 失败模式

一个字段同时表达多个事实，例如：

- App 是否连到 Relay；
- Relay 是否能到达电脑进程；
- 会话材料是否仍在 TTL 内；
- 当前页面是否有缓存可显示。

这会产生“网络在线所以电脑在线”“会话还在所以自动恢复有保证”等错误文案和交互。

### 改进模式

先列正交维度：

```text
本地 UI：mounted / restoring / ready
App 链路：connecting / online / degraded / offline
远端能力：reachable / retrying / unavailable
数据存续：valid / expired / corrupt
业务操作：idle / pending / confirmed / failed
```

每个维度明确：

- 权威来源；
- 本地缓存能否临时替代；
- 更新时间；
- 过期条件；
- 用户可执行动作；
- UI 不得暗示的能力。

只有状态组合需要频繁消费时才派生展示状态；不要用派生展示状态反写权威状态。

### 检查问句

- “重新检查”只是查询，还是确实能恢复远端能力？
- `client_dead` 是连接窗口结束、进程死亡，还是 session 过期？
- 本地成功动画来自服务器确认，还是来自定时器？
- 返回前台后是否重新查询权威状态？

## 2. 页面与内容所有权

### 失败模式

全局事件同时发布导航、标签和页面内容。旧页面在路由销毁前收到新页面内容，导致：

- PDF 或其他二进制被文本编辑器读取；
- 隐藏页面继续处理新状态；
- 标签栏正确但正文互串；
- 新格式自动落入错误的默认处理器。

### 改进模式

把三类数据分开：

```text
navigation state
tab/list state
owned active content
```

为每类内容声明稳定契约：

```yaml
view_id:
route_name:
content_mode: text | binary | structured | none
owner:
capabilities:
```

交付内容前同时验证：

- 当前路由属于该 owner；
- 内容类型受支持；
- 页面仍在生命周期内；
- 版本或 requestId 仍是最新；
- 未知类型被拒绝。

页面可以接收共享标签状态，但不应因此收到不属于自己的正文。

## 3. 生命周期和初始化

### 初始化顺序

ArkTS 属性初始化可能在 `aboutToAppear` 前执行。不要在早期 `@State` 初值中调用依赖后声明的 `@StorageProp`、服务或 UIContext。

优先：

- 使用无依赖安全默认值；
- 在所有依赖存在后统一初始化；
- 把派生显示值实现为安全 getter；
- 编译之外增加真实页面创建测试。

### 进入与离开

页面或组件拥有的资源必须成对管理：

| 创建 | 释放 |
| --- | --- |
| EventBus subscription | disposer |
| interval / timeout | clear |
| foreground poll | background/leave stop |
| async request | requestId/cancel guard |
| dialog guard | success/error/dismiss release |
| WebView bridge | page destruction cleanup |

覆盖：

- 冷启动；
- 暖启动；
- 返回栈重入；
- 前后台；
- 旋转或窗口变化；
- 保留数据覆盖安装。

## 4. 动态集合与同帧重入

### 稳定身份

`ForEach` / `LazyForEach` 的 key 必须表达节点身份。若节点的渲染语义依赖语言、状态或计数，确认状态变化确实触发节点刷新；不要假设修改对象字段一定能刷新。

常见策略：

- 对 `@State` 数组使用不可变替换；
- 让 DataSource 只发一次必要通知；
- key 保持身份稳定，同时把会改变渲染的状态纳入响应式依赖；
- 只有框架复用确实阻断刷新时，才把受控版本或语言加入 key。

不要无差别把所有可变字段塞入 key，否则会破坏焦点、滚动位置和动画连续性。

### 弹窗与列表删除

在 Dialog action 中同步删除 `LazyForEach` 子节点，同时触发第二次 `onDataReloaded()`，可能造成弹窗关闭与列表重建同帧重入。

更稳妥的顺序：

1. 释放 dialog / navigation / opening guards；
2. 让弹窗开始关闭；
3. 在下一任务执行一次删除；
4. 保持单一数据源通知；
5. 验证删除后筛选、其他卡片和主操作仍可点击。

## 5. 瞬态反馈与计时器

瞬态控件包括浮动 A−/A+、比例胶囊、Toast 类本地反馈和临时状态条。

要求：

- 新触发取消或废弃旧计时器；
- 重复点击重置可见窗口；
- 离开页面清理计时器；
- 动画结束只控制可见性，不控制业务完成；
- 自动化在点击前重新触发显隐，不在慢速布局抓取后继续使用旧坐标；
- 相同语义跨页面使用共享组件，但不在不支持该能力的页面硬加控件。

可使用 generation token 防止旧回调关闭新状态：

```text
generation += 1
local = generation
schedule hide
if local == generation: hide
```

## 6. Safe area、IME 与本地几何

### Safe area 所有权

先确认窗口模式：

- 非全屏窗口可能已经把内容区放在系统栏之间；
- 全屏、沉浸式或自定义工具栏才可能需要显式 avoid-area；
- 页面根 padding 和局部工具栏 inset 不能同时机械叠加。

出现异常大留白时，先画清：

```text
Window content rect
system avoid area
page root padding
component local inset
```

### IME 与远端语义

本地 IME、候选窗、selection handle、浮层和工具栏移动通常不等于远端内容尺寸改变。

对于终端或 WebView：

- 只在真实内容宽度、字体或设备窗口变化时报告远端 resize；
- 高度仅因 IME 覆盖变化时优先保持本地；
- 发送 resize 前比较最后成功的 cols/rows 与布局 signature；
- WebView 发生黑屏或重排异常时，优先验证固定几何和 overlay 策略；
- 不把短暂 App 链路抖动转换成页面卸载或远端校准。

这是一种产品/架构策略，具体 KeyboardAvoidMode 必须按目标工程验证。

## 7. 失败关闭与未来扩展

修复当前格式或页面时，问：

- 未来新增一种二进制格式会怎样？
- 新页面没注册 owner 会怎样？
- 未知枚举值会落入哪个默认分支？
- 外部返回缺少字段时是否写入错误状态？

优先设计：

- 明确注册；
- capability 检查；
- 未知类型拒绝；
- 只读或 dry-run 默认；
- 写入需显式权限；
- 出错不推进 checkpoint；
- 不完整证据不标完成。

“安全不支持”优于默默按错误格式处理；但必须在 UI 中解释限制和下一步。

## 8. 自动化证据的常见假象

### 常见假失败

- `dumpLayout` 返回空文件、系统状态栏或其他前台应用；
- 瞬态按钮在布局抓取期间已经淡出；
- 历史标签、弹窗或输入法污染测试前置；
- 样本文件被改名或删除；
- HDC 错误文本被误解析为 API 版本；
- 坐标点击使用了过期布局；
- UI 自动化 drag 不等于 ArkUI 长按拖拽。

### 诊断顺序

1. 核对目标设备 ID 与 API；
2. 核对前台 bundle 和页面；
3. 核对截图；
4. 核对 PID 是否变化；
5. 核对崩溃、AppFreeze 和 hilog；
6. 清理测试前置；
7. 重新触发瞬态状态后立即操作；
8. 自动化与人工观察冲突时，不把任一方直接当结论。

记录测试工具的能力边界。无法可靠模拟长按拖拽、系统焦点或屏幕朗读时，明确保留人工/专项测试项。

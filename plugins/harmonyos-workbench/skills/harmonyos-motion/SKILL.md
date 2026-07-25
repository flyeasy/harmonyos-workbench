---
name: harmonyos-motion
description: 把 HarmonyOS、ArkUI、Canvas、WebView 或代码生成产品动效的模糊手感和现象转换为准确术语、相近概念、诊断分支与可能的 ArkUI 能力，例如“松手像急刹车”“滚动后按钮来不及点”“页面像从同一张卡片长出来”“键盘弹出导致远端布局乱跳”。用于命名、检索和编写提示词。不要用于完整设计审查。不要用于直接改代码、传统视频剪辑或纯构建问题。
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Motion

只做一件事：把模糊描述转换为可检索、可讨论、可验证的术语。不要代替完整审视或实现。

## Capability contract

1. **Input**：现象、触发动作、目标设备和可用录屏/日志。
2. **Preflight**：区分动效、性能、生命周期、几何和测试工具问题。
3. **Execute**：给最佳术语、相近概念、诊断分支和可能的 ArkUI 能力。
4. **Verify**：说明需要慢放、帧率、状态或目标证据中的哪一种。
5. **Evidence**：引用观察，不把推断写成平台事实。
6. **Handoff**：实现交给 `harmonyos-design`，完整验收交给 `harmonyos-review`。

## 输出格式

```markdown
**最佳匹配术语** — 一句话定义。

相近概念：1–2 个。
ArkUI 关联：可能的 API、属性或验证方向。
诊断分支：如何区分相似现象。
边界：什么时候不是这个问题。
```

有多个可能时，先给最佳匹配，再给最小诊断分支。API 只能写“可能关联”，并提醒按目标 SDK 核验。

## 1. 输入与反馈

- **按下反馈（Press feedback）**：Touch Down 时立即改变局部状态，证明输入已被接收。
- **抬起提交（Commit on release）**：抬起且仍在有效目标内时执行动作。
- **取消回拖（Cancel and re-enter）**：移出目标可取消，重新移入可恢复候选状态。
- **焦点态（Focus state）**：键盘、遥控器或旋钮当前操作目标。
- **悬停态（Hover state）**：光标进入目标后的可交互提示。
- **激活/选中态（Active/selected state）**：持久选择，不等同焦点。
- **瞬态显现（Transient reveal）**：滚动、点击或状态变化后短暂出现的控件。
- **可见期（Visibility window）**：瞬态反馈保持可操作或可读的时间窗口。

“按钮滚动后出现，但自动化总点不到”可能是可见期耗尽、旧坐标或测试工具延迟，不一定是点击失效。

## 2. 连续手势

- **跟手（Direct tracking）**：对象在手势过程中持续随输入变化。
- **速度继承（Velocity handoff）**：离手动画沿用离手前速度。
- **动画衔接（Animation continuity）**：目标改变时从当前显示状态平滑进入新目标。
- **可打断动画（Interruptible motion）**：动画中可被新输入接管、反向或重定向。
- **边界阻尼（Boundary resistance）**：越过边界越难继续，而不是硬停止。
- **回稳（Settle）**：离手后向边界、吸附点或稳定状态运动。
- **抛滑（Fling）**：离手带方向和速度的滑动。
- **吸附（Snap）**：依据位置和速度选择离散目标。
- **手势竞争（Gesture competition）**：子节点手势与 Scroll/List 等容器争夺识别。
- **识别器不等价（Recognizer mismatch）**：自动化 drag 与 ArkUI 长按拖拽等真实识别条件不同。

ArkUI 可能关联：

- 跟手：`curves.responsiveSpringMotion()`；
- 回稳/继速：`curves.springMotion()`；
- 显式物理：`curves.interpolatingSpring()`；
- 手势共存：`parallelGesture` / `priorityGesture`，需按场景核验。

## 3. 曲线

- **标准曲线（Standard curve）**：对象前后都在视线内的加速—减速变化。
- **减速曲线（Decelerate）**：开始快、结束慢，常用于进入视线。
- **加速曲线（Accelerate）**：从静止逐渐加速，常用于离开视线。
- **弹性曲线（Spring）**：由响应、阻尼、质量、刚度或速度决定的物理运动。
- **临界阻尼（Critical damping）**：不振荡并尽快稳定。
- **欠阻尼（Underdamped）**：越过目标并振荡后稳定。
- **过阻尼（Overdamped）**：不越过目标但较慢接近。
- **速度断层（Velocity discontinuity）**：跟手与回稳交界处速度突变，表现为“松手急刹车”。

掉帧也会像“急刹车”。先用慢放、帧率和离手速度对比区分物理参数与性能长帧。

## 4. 转场与空间关系

- **同层转场**：Tab、编辑模式等平级状态变化。
- **上下层转场**：父页面与子页面的进入和返回。
- **跨层转场**：应用或任务上下文切换。
- **共享元素转场**：同一对象在两个页面间连续移动和变化。
- **共享容器转场**：容器边界、大小、圆角连续变化，内部内容再切换。
- **共享动势**：无法共享对象时保持共同位移、缩放或旋转趋势。
- **一镜到底**：共享关系让转场看起来不中断。
- **交叉淡化（Crossfade）**：一个状态淡出、另一个淡入。
- **默认转场叠加（Transition stacking）**：自定义/共享转场与 Navigation 默认转场同时作用。

ArkUI 可能关联：`geometryTransition()`、Navigation 默认或自定义转场。

## 5. 编排与瞬态反馈

- **错峰（Stagger）**：多个元素以小间隔依次出现。
- **数值脉冲（Value pulse）**：数字变化时短暂缩放或透明度反馈。
- **状态形变（State morph）**：同一对象在两个状态间连续改变形状或容器。
- **微动效（Micro-interaction）**：小范围、短时、承担反馈或状态说明的运动。
- **重新触发（Retrigger）**：反馈尚未结束时再次触发并延长或重启动画。
- **陈旧计时器（Stale timer）**：上一轮 timeout 晚到，错误关闭当前新反馈。
- **代际保护（Generation guard）**：只允许当前 generation 的回调改变可见状态。
- **显隐竞态（Visibility race）**：触发、布局、计时器和点击在同一短窗口内竞争。

玻璃胶囊、浮动缩放按钮等通常是 House Style，不是 HarmonyOS 统一官方要求。

## 6. 异步与状态真实性

- **本地确认（Acknowledged）**：客户端已收到输入，远端尚未完成。
- **处理中（Pending）**：操作等待后端、设备或耗时任务。
- **真实确认（Confirmed）**：业务结果由权威状态确认。
- **乐观更新（Optimistic UI）**：确认前先更新，并准备失败回滚。
- **回滚（Rollback）**：乐观结果失败后恢复真实状态。
- **虚假完成（False completion）**：视觉或播报暗示成功，但真实状态未确认。
- **响应乱序（Out-of-order response）**：旧请求晚到并覆盖新意图。
- **状态轴混合（State-axis conflation）**：一个状态同时表达链路、远端能力、会话存续等多个维度。
- **权威源混淆（Authority confusion）**：把缓存、动画或本地标志当作远端事实。

“动画在撒谎”通常匹配虚假完成或权威源混淆，不是单纯缓动问题。

## 7. 生命周期与几何

- **生命周期泄漏（Lifecycle leak）**：页面离开后 timer、listener、poll 或 request 仍更新状态。
- **页面内容互串（View-state leakage）**：旧页面或错误 owner 收到新页面内容。
- **双重安全区（Double safe-area application）**：Window 已避让系统栏，页面又重复加 inset。
- **局部/远端几何耦合（Local/remote geometry coupling）**：IME、浮层或本地工具栏变化被错误发送为远端内容 resize。
- **布局抖动（Layout thrash）**：高频修改布局属性造成反复测量与绘制。
- **测试假阴性（Harness false negative）**：测试工具、前置状态或采样时序导致未观察到真实存在的行为。

## 8. 适配与可访问性

- **交互归一**：同一任务在触摸、鼠标、键盘、遥控器等输入下使用符合习惯的方式完成。
- **多态控件**：同一控件针对设备、输入和场景呈现不同形态与状态。
- **自适应布局**：随容器连续拉伸、延伸、隐藏或折行。
- **响应式布局**：在断点处缩进、挪移、重复或分栏。
- **语义 Token**：按用途而不是具体数值命名的设计参数。
- **无障碍分组**：将相关节点作为一个语义整体播报。
- **虚拟无障碍节点**：为自绘内容提供辅助工具可识别的结构。

## 示例

用户：

> 卡片松手时像先停了一下，再回去。

输出：

```markdown
**速度继承缺失（Velocity handoff missing）** — 回稳动画没有沿用手势最后速度，在离手点形成速度断层。

相近概念：动画衔接失败、性能长帧。
ArkUI 关联：检查跟手阶段 `responsiveSpringMotion()` 与回稳阶段 `springMotion()`。
诊断分支：慢放查看对象是否先归零；同时检查离手帧长。
边界：若位置连续但整帧冻结，优先归为性能长帧。
```

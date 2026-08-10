---
name: harmonyos-motion
description: 把 HarmonyOS、ArkUI、Canvas、WebView 或代码生成产品动效的模糊手感和现象转换为准确术语、相近概念、诊断分支与可能的 ArkUI 能力，例如“松手像急刹车”“滚动后按钮来不及点”“页面像从同一张卡片长出来”“键盘弹出导致远端布局乱跳”。用于命名、检索和编写提示词。不要用于完整设计审查。不要用于直接改代码、传统视频剪辑或纯构建问题。
---

<!-- Modified from dososo/HarmonyOS-Design commit 205afcbf1d8170239477a98a8472089d4ab7b86c for HarmonyOS Workbench. -->

# HarmonyOS Motion

把模糊现象转换为可检索、可讨论、可验证的术语；不代替完整审视或实现。

## Capability contract

1. **Input**：现象、触发动作、目标设备和录屏/日志。
2. **Preflight**：区分动效、性能、生命周期、几何和测试工具问题。
3. **Execute**：给最佳术语、相近概念、诊断分支和可能的 ArkUI 关联。
4. **Verify**：指出慢放、帧率、状态或目标证据中的最小验证。
5. **Evidence**：引用观察，不把推断写成平台事实。
6. **Handoff**：设计/实现交给 `harmonyos-design`，完整验收交给 `harmonyos-review`。

## Output

```markdown
**最佳匹配术语** — 一句话定义。

相近概念：1–2 个。
ArkUI 关联：可能的 API、属性或验证方向。
诊断分支：如何区分相似现象。
边界：什么时候不是这个问题。
```

先给一个最佳匹配；有歧义时给最短诊断分支。API 只能称为“可能关联”，必须按目标 SDK 核验。

## Lookup

按现象从 [references/VOCABULARY.md](references/VOCABULARY.md) 选择一类：输入反馈、连续手势与曲线、转场、瞬态/异步状态、生命周期/几何、适配/无障碍。术语表按需检索，不把整份词典加载到每次动效咨询中。

“动画像成功但实际未完成”优先归为状态真实性；“点不到/位置错”优先排查目标、可见期、几何和 harness；整页体验问题转 `harmonyos-review`。

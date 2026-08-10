---
name: harmonyos-capabilities
description: 选择、申请、开通、配置、审计或验证 HarmonyOS / AppGallery Connect 开放能力、Kit、服务权益和 ACL 受限权限。用于能力开关、申请状态、资格/协议/商户前置、设备/API/地区范围、Manifest 权限、Picker/安全控件替代、个人数据、审核材料和上架门禁，包括位置、账号、地图、安全检测、实况窗、推送、App Linking、钱包/IAP、通知/卡片、云服务、运动健康、WearEngine 和 AI 联网增强等。AI 产品与模型工程使用 harmonyos-ai；通用实现使用 harmonyos-develop。
---

# HarmonyOS Capabilities

把能力从“看见一个开关”管到“发布候选中可证明可用”。不猜测权益，不代替用户接受协议、申请受限权限、充值或开启付费服务。

## Capability contract

1. **Input**：业务场景、应用/元服务与 App ID、目标设备/API/地区、分发范围、所需数据和用户触发点。
2. **Preflight**：用官方当前文档确认能力名、接入层、可用范围、资格、权益/ACL、资费、凭据、隐私和替代方案。
3. **Execute**：只在授权边界内完成控制台或本地配置，然后交给 `harmonyos-develop` 实现；接受协议、申请、付费和提交审核都是外部动作。
4. **Verify**：分开验证开通回执、配置/Manifest、签名与应用身份、运行时授权、真实设备/服务、隐私和上架材料。
5. **Evidence**：记录官方来源和快照日期、能力状态、审核回执摘要、配置文件、运行证据和未验证项；对 App ID、证书指纹和帐号信息做最小化和脱敏。
6. **Handoff**：输出能力账本；实现交给 `harmonyos-develop` / `harmonyos-ai`，真机交给 `harmonyos-targets` / `harmonyos-test`，发布门禁交给 `harmonyos-release`。

## 状态模型

每个能力使用以下状态，不得跳级推断：

`identified → eligible → requested → approved → enabled → configured → declared → runtime_verified → release_verified`

可选分支：`alternative_selected / not_required / rejected / expired / blocked / needs_verification`。

- 看到开关不等于 `enabled`。
- 提交申请不等于 `approved`。
- 审核通过不等于 `configured` 或 `runtime_verified`。
- Manifest 声明、用户动态授权、开放能力权益和 ACL 审批是不同事实。
- 能力申请状态可能过期、被撤回或与 App ID/签名不匹配；发布前重新核对。

## 能力账本

每项能力至少记录：

```yaml
capability:
business_scenario:
official_name:
access_layer: os_api | kit | agc_service | entitlement | acl | commerce
app_form:
api_and_os:
devices:
regions:
identity_and_signing:
approval_state:
console_state:
manifest_permissions:
runtime_authorization:
picker_or_control_alternative:
personal_data:
credentials:
cost_and_quota:
test_evidence:
release_evidence:
official_sources:
snapshot_date:
unverified:
```

详细工作流见 [references/access-workflow.md](references/access-workflow.md)。

## 选择与申请规则

1. 先证明业务必要性，再选能力；不按名称相似度猜测 Kit 或权限。
2. 先选无权限方案，再选 Picker/安全控件，再选开放权限，最后才评估 ACL。
3. 需要 ACL 时，用官方当前“受限开放权限”和 AGC 可申请列表核对精确场景、设备类型、应用类型和材料；不使用过期静态全表代替查询。
4. 用户提供的 2026-08-10 AGC 界面显示单次最多申请 30 个 ACL；实际申请前重新以当前控制台为准，并且只申请最小集合。
5. 开关、协议、权益、资费、商户、资质和 ACL 申请没有得到明确授权时，只生成操作清单，不代替用户提交。
6. 凭据只存在服务端或受控密钥存储；不把 API Key、Client Secret、商户私钥或签名材料写入客户端、日志和证据。
7. 为未批准、未安装服务、不支持设备/地区、用户拒绝和权益撤回提供降级；不让应用卡在假 loading。

## 开放能力范围

用户提供的当前列表已按访问模式归类到 [references/capability-catalog.md](references/capability-catalog.md)，包括：

- AI 问答联网增强；
- 位置、室内高精度定位、位置语义、围栏后台唤醒和蓝牙扫描信息；
- 华为账号/RISC、地图、应用设备状态和安全检测；
- 实况窗、Push 场景化消息、App Linking、钱包和 IAP；
- 代理提醒、待机/锁屏/透明卡片和优先通知；
- 认证、云存储、云托管、运动健康、WearEngine 和异包名接续。

这份目录是选型索引，不是开通状态或完整权限清单。

## 项目扫描

先根据本 Skill 位置解析插件根，再运行：

```bash
python3 <plugin-root>/scripts/harmonyos_workbench.py capability-audit \
  --project /path/to/project \
  --evidence artifacts/harmonyos-workbench/capabilities/inventory.json
```

扫描只证明“源码中存在权限或能力线索”，不证明控制台已开通、审核已通过或运行时可用。

## 完成门槛

只有当能力账本中的业务必要性、官方来源、可用范围、开通/权益/ACL、凭据、配置、运行证据、隐私和发布门禁全部有状态时，才说能力接入闭环。官方来源见 [references/sources.md](references/sources.md)。

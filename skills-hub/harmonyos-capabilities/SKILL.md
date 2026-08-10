---
name: harmonyos-capabilities
description: 选择、申请、开通、配置、审计或验证 HarmonyOS / AppGallery Connect 开放能力、Kit、服务权益和 ACL 受限权限。用于能力开关、申请状态、资格/协议/商户前置、设备/API/地区范围、Manifest 权限、Picker/安全控件替代、个人数据、审核材料和上架门禁，包括位置、账号、地图、安全检测、实况窗、推送、App Linking、钱包/IAP、通知/卡片、云服务、运动健康、WearEngine 和 AI 联网增强等。
version: 0.4.0
category: combo
platforms:
  - CODEX_CLI
permissions:
  - filesystem
  - shell
  - network
  - browser
---

# HarmonyOS Capabilities

把能力从“看见一个开关”管到“发布候选中可证明可用”。不猜测权益，不代替用户接受协议、申请受限权限、充值或开启付费服务。

## Capability contract

1. **Input**：业务场景、应用/元服务与 App ID、目标设备/API/地区、分发范围、所需数据和用户触发点。
2. **Preflight**：用官方当前文档确认能力名、接入层、可用范围、资格、权益/ACL、资费、凭据、隐私和替代方案。
3. **Execute**：只在明确授权内完成控制台动作；协议、申请、付费、资质和提交审核都是外部动作。
4. **Verify**：分开验证开通回执、配置/Manifest、签名与应用身份、运行时授权、真实设备/服务、隐私和上架材料。
5. **Evidence**：记录官方来源与快照日期、能力状态、回执摘要、配置、运行证据和未验证项；凭据和账号信息最小化脱敏。
6. **Handoff**：输出能力账本；实现交给 `harmonyos-develop` / `harmonyos-ai`，真机交给 `harmonyos-targets` / `harmonyos-test`，发布交给 `harmonyos-release`。

## 状态机

`identified → eligible → requested → approved → enabled → configured → declared → runtime_verified → release_verified`

分支：`alternative_selected / not_required / rejected / expired / blocked / needs_verification`。

- 看到开关不等于已开通；提交申请不等于已批准。
- 审核通过不等于已配置或真机可用。
- Manifest 声明、用户动态授权、开放能力权益和 ACL 审批是四类事实。
- 发布前重新核对应用身份、签名、过期、地区、配额和付费状态。

## 能力账本

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

## 选择与申请

1. 先证明业务必要性，再核对官方精确能力名。
2. 先选无权限方案，再选 Picker/安全控件，再选开放权限，最后才评估 ACL。
3. ACL 使用当前官方“受限开放权限”和 AGC 列表核对精确场景、设备、应用类型和材料；不用静态全表替代查询。
4. 用户提供的 2026-08-10 AGC 页面显示单次最多申请 30 个 ACL；实际操作前以当前控制台为准，且只申请最小集合。
5. 没有明确授权时，只生成开关、协议、权益、资费、商户、资质和 ACL 操作清单，不代提交。
6. API Key、Client Secret、商户私钥和签名材料只在受控密钥系统，不进入客户端、日志和证据。
7. 为未批准、不支持设备/地区、用户拒绝、资格/权益撤回提供真实降级。

## 能力索引

对以下类型分别建账，不把它们当成同一种“开关”：

- AI 问答联网增强；
- 位置、室内高精度定位、位置语义、围栏后台唤醒、蓝牙扫描信息；
- 华为账号/RISC、地图、应用设备状态、安全检测；
- 实况窗、Push 应用内通话/语音播报、App Linking、钱包/IAP；
- 代理提醒、优先通知、待机/锁屏/透明卡片；
- 认证、云存储/托管、运动健康、WearEngine、异包名接续。

ACL 示例包括 `CUSTOM_SCREEN_RECORDING`、`READ_WRITE_DOCUMENTS_DIRECTORY`、`READ_WRITE_DOWNLOAD_DIRECTORY`、三类反诈 Picker、`MANAGE_MEDIA_RESOURCES_FOR_PUBLIC`、`MANAGE_BLUETOOTH_ADVERTISER_NAME`、`ALLOW_EXTERNAL_NATIVE_CODE` 和 `CONTROL_DEVICE`。它们有非常窄的场景/设备条件，只能以当前官方页面为准。

官方发现入口：<https://developer.huawei.com/consumer/cn/sdk/> 、<https://developer.huawei.com/consumer/cn/doc/overview/AppGallery-connect> 、<https://developer.huawei.com/consumer/cn/doc/App/50000>。

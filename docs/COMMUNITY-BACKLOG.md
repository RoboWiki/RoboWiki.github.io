# 社区 / 账户 / 后台借鉴清单

> 参考项目已浅克隆到 `00_open/_refs_community/`（不进仓库）：
> new-api、sub2api、nextbb、discourse、forem、flarum、nodebb、homeland、paopao-ce、symphony。
> 原则：**先借成熟实现，不从零造**；只补现有架构缺的能力，不搬整套框架。

## 已完成（2026-11-09）

| 能力 | 借鉴来源 | 实现 |
|---|---|---|
| 微信扫码登录（个人小程序当登录确认器） | 个人主体方案（ticket 链路），NodeBB/Discourse 的「扫码确认」思路 | `LoginTicket` 表 + `/auth/wechat/qr{,/confirm,/status}`；网页扫码卡；小程序 `pages/login/confirm` |
| 后台用户管理（列表/角色/封禁） | Discourse Admin::Users、Flarum 用户管理、NodeBB ACP | `GET /admin/users`、`PATCH /admin/users/{id}`；封禁即下线（session_epoch+1 + 吊销 refresh）；护栏：不能动自己、不能降级最后一名站务 |

## 待补（按价值排序）

### 账户

| 缺口 | 参考实现 | 备注 |
|---|---|---|
| 账号注销（用户自助删除） | Discourse `DELETE /u/{username}`、Flarum 账户删除 | 需定内容处置：帖子匿名化而非级联删 |
| 登录设备管理细化（单端下线/命名） | NodeBB sessions、Homeland 登录记录 | 现有 `/auth/sessions` + 全部下线已够用，缺单端撤销 |
| 两步验证（TOTP） | Discourse 2FA、Flarum 扩展 | 个人站可后置 |
| 个人资料丰富度（签名/主页链接/技术栈标签） | Homeland 用户资料、paopao-ce 个人页 | 现有 bio + avatar；缺结构化标签 |

### 社区

| 缺口 | 参考实现 | 备注 |
|---|---|---|
| 帖子置顶 / 锁定（站务） | NodeBB pin/lock、Flarum sticky/lock | Post 表加 pinned/locked 两布尔即可，列表排序与回复拦截各一处 |
| 话题标签（tags）与按标签聚合 | Discourse tags、Flarum tags | 比自由文本搜索更可导航；与 catalog 品类可映射 |
| 引用回复 / 楼层锚点 | NodeBB quote、Discourse reply-to | 现在只有平铺评论 |
| 草稿自动保存 | NodeBB composer drafts、Discourse drafts | 发帖/投稿表单本地草稿 |
| 徽章 / 信任等级 | Discourse trust levels、Flarum badges | 用 reputation 先跑，再谈等级 |
| 邮件摘要（关注话题/每周摘要） | Discourse digests、Homeland 周报 | worker 已有 outbox，缺摘要模板与调度 |

### 后台

| 缺口 | 参考实现 | 备注 |
|---|---|---|
| 审计日志（谁在后台做了什么） | Discourse staff action log、Flarum audit | 封禁/角色/审核动作落一张 `admin_actions` 表 |
| 内容审核批量操作 | Discourse review queue | 举报队列已有单条处置，缺批量 |
| 数据导出（用户/帖子 CSV） | Discourse export、Flarum | 个人站优先级低 |
| 站点设置面板 | Flarum admin settings、NodeBB ACP | 现为 env 配置，够用 |

## 不建议搬的

- Discourse/forem 的整套 Rails/Ember 架构：与本仓 FastAPI + Astro + Taro 分层冲突
- Flarum 的 PHP 插件体系、NodeBB 的实时 WebSocket 栈：现有轮询/SSE 已覆盖规模
- new-api / sub2api 的网关计费模型：它们解决的是 API 转售，本仓不需要

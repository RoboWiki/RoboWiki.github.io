# 社区 / 账户 / 后台借鉴清单

> 参考项目已浅克隆到 `00_open/_refs_community/`（不进仓库）：
> new-api、sub2api、nextbb、discourse、forem、flarum、nodebb、homeland、paopao-ce、symphony。
> 原则：**先借成熟实现，不从零造**；只补现有架构缺的能力，不搬整套框架。

## 已完成（2026-11-09）

| 能力 | 借鉴来源 | 实现 |
|---|---|---|
| ~~微信扫码登录~~（2026-11-11 移除，改为 QQ 网页登录） | 个人主体方案（ticket 链路），NodeBB/Discourse 的「扫码确认」思路 | 原 `LoginTicket` + `/auth/wechat/qr*` 与小程序确认页已停用；网页改用 `/auth/qq/*` |
| 后台用户管理（列表/角色/封禁） | Discourse Admin::Users、Flarum 用户管理、NodeBB ACP | `GET /admin/users`、`PATCH /admin/users/{id}`；封禁即下线（session_epoch+1 + 吊销 refresh）；护栏：不能动自己、不能降级最后一名站务 |

## 已完成（2026-11-12）

| 能力 | 借鉴来源 | 实现 |
|---|---|---|
| 帖子置顶 / 锁定 | NodeBB pin/lock、Flarum sticky/lock | `posts.pinned` / `posts.locked`；站务 API；锁定后普通用户不能回复，内容仍公开 |
| 评论编辑 / 撤回 | Forem 有子回复软删、NodeBB 删除占位 | `PATCH/DELETE /comments/{id}`；withdrawn 占位保留回复树；撤回已采纳评论清采纳并回退声望 |
| 评分修改 / 撤回 | paopao-ce 一人一行、后端既有改分/撤销 | 前端读取 `mine` 预填；修改/撤回；撤回同步把评价帖降级为讨论 |
| 本地草稿 / 最近发言 | Discourse drafts、NodeBB composer | localStorage 自动保存发帖草稿；最近 20 条本机发言记录，可清空 |
| 引用回复 | NodeBB quote、Discourse reply-to | 评论带被引用正文快照，回复树仍只两级；被引用方撤回/隐藏时快照同步清空 |
| 标签聚合与导航 | Discourse tags、Flarum tags | `GET /tags` 按帖子数聚合；社区侧栏热门标签与卡片标签可直接筛选 |
| 评价条数与写评价入口 | Discourse topic summary、Forem 文章页 | 零件页显示「N 条评价」；评分后引导补一句使用体验，直达预填评价表单 |
| 站务运营总览 | Discourse admin dashboard、NodeBB ACP | `GET /admin/overview`：用户/内容/互动/治理/数据质量、14 天趋势、贡献者与热门内容、待办入口 |

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
| 评价「有用」票与精选排序 | NodeBB votes、Forem reactions | 好评价自动靠前，票数与评分聚合解耦 |
| 按品类评价模板 | Discourse composer 模板、paopao-ce 发帖 | 用填空提示代替空白输入框（舵机问温升/背隙，IMU 问零偏） |
| 回访再评价提醒 | Discourse digests、NodeBB follow | 90/180 天后在通知里提醒补充结论，点开直达预填表单 |
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

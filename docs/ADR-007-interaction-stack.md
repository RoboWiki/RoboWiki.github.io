# RoboWiki 互动栈与成熟框架引用（ADR-007）

> 状态：**已实施**（Vue 组件已由 Astro React 岛与 Taro 替代）
> 上位：`ARCHITECTURE.md`、ADR-004（统一投稿）、ADR-005（数据生命周期）、ADR-008（前端栈）
> 范围：评论、评分、投稿、身份与多端登录。目录数据、发布链路和部署形态不在本文改动范围。

## 0. 一句话裁定

**写入只留一个领域：FastAPI。** 身份用 `users` + `identities` 一层抽象，OAuth2/OIDC 协议交给 Authlib；
评论、评分、投稿继续用 FastAPI 的领域模型；Astro 社区/站务用 Ant Design Form/Rate，
Taro 负责移动端表单；纯静态镜像可回落到 giscus；Discourse 只作为未来的卫星社区，不在主站部署。

这就是 **C 路线**：不买一个论坛来顶替主站，也不从零写协议、表单和论坛。成熟件放在外围，
自研压在领域规则上。

## 1. 约束

| 约束 | 事实 | 对选型的含义 |
|---|---|---|
| 资源 | 生产按单机 2C/4G 起步，API、Postgres、worker 同机；见 `../deploy/compose.yml`、`../deploy/README.md` | 不能再加一套 Ruby/Redis/Sidekiq 论坛栈 |
| 多端 | Web/PWA、微信小程序、QQ 机器人、未来 App 共用 `/api/v1`；见 `../clients/README.md` | 需要 JSON API 与统一身份，不是 HTML 论坛 |
| 人力 | 单人维护 | 少一个运行时，就少一套升级、备份、告警和账号 |
| 既有资产 | 目录只读投影、投稿 outbox、静态镜像、站内 UGC 已在 Postgres | 新组件必须接入现有模型，不能另起一套库 |

## 2. 候选路线与裁定

| 路线 | 形态 | 主要代价 | 结论 |
|---|---|---|---|
| A 论坛优先 | Discourse/Answer 作为社区内核，站点链接过去 | 第二套账号/库/运维；小程序与 App 仍要另写 BFF；评分/投稿关系断裂 | 否 |
| B 全自研 | 自己写 OAuth/OIDC、表单校验、无障碍组件、论坛 | 安全面、可访问性、协议细节全部自己承担；回归成本随端数增长 | 否 |
| **C 单领域 + 成熟件** | FastAPI 唯一写域；身份抽象；Vue/控制台用成熟表单与 UI；静态镜像用 giscus；Discourse 后置 | 需要克制「再加一个服务」的冲动；领域规则仍要自己写 | **采用** |

## 3. C 路线的组成

| 层 | 决定 | 落点 |
|---|---|---|
| API | 单领域 API：FastAPI + `/api/v1`；静态读仍走构建产物 | `../backend/app/main.py` |
| 身份 | `users` 存账号与资料，`identities` 存 `(provider, subject)` 映射；协议交给 Authlib；Casdoor 延后 | `../backend/app/models.py`、`../backend/app/api/routes/auth.py` |
| 评论 | 社区讨论、零件评价、文档页讨论共用 Post/Comment/Vote/WikiComment；`kind` 与挂载点区分 | `../backend/app/models.py`、`../backend/app/api/routes/community.py`、`../backend/app/api/routes/wiki.py` |
| 评分 | `Rating` 一人一实体一票，可改；聚合与分布在同一读模型；GitHub issue 快照收敛为导入源 | `../backend/app/api/routes/ratings.py`、`../apps/app/src/pages/part/index.tsx`、`../apps/web/src/components/parts/PartDetail.astro` |
| 投稿 | `Submission` + `SubmissionReview` + `Outbox`；字段级 before/after 与证据，审核通过不等于生效 | `../backend/app/models.py`、`../backend/app/worker.py` |
| 前端表单 | React 岛用 Ant Design Form；移动端用 Taro 受控表单 | `../apps/web/src/components/community/`、`../apps/app/src/pages/` |
| 站务 | Ant Design 的 Form/Table，与社区共用一套 | `../apps/web/src/components/admin/` |
| 静态镜像 | GitHub Pages 继续用 giscus；主站探测到 API 时走站内讨论 | `../apps/web/src/components/comments/Comments.tsx` |
| 未来卫星社区 | Discourse 只在触发条件满足后独立部署，与主站 SSO | 本文 §4 |

## 4. 为什么不现在上 Discourse

### 4.1 资源：同机放不下第二套栈

Discourse 不是单个进程：Ruby 应用、PostgreSQL、Redis、Sidekiq、反向代理和邮件链路。
生产已经是 2C/4G 单机跑 API、Postgres、worker；再加一套会直接争内存与 CPU，最先坏的是
迁移、备份、构建这些没人盯的路径。

### 4.2 多端：小程序和 App 要的是 BFF，不是论坛页面

Discourse 的强项是服务端渲染的论坛与邮件通知；小程序/App 需要 JSON、`wx.login` 换同一账号、
内容安全审核、轻量列表。真做起来仍要写一层 BFF，于是得到两个 API 面、两套权限、两处内容状态，
这正是要避免的。

### 4.3 账号与库：第二套 user 表

Discourse 有自己的 users、groups、trust levels；要共享账号必须上 SSO，而评分、投稿、举报仍
外键指向本站 `users`。结果是三处身份（本站、Discourse、giscus/GitHub）与两套内容库，迁移和
封禁都要双写。

### 4.4 单人维护：论坛的运维是持续成本

升级节奏、插件兼容、邮件送达率（SPF/DKIM/退信）、反垃圾、备份恢复、CVE 跟进，都要人。
把这些放在一个单人维护的选型站上，收益（长帖/版块）远小于成本。

### 4.5 触发条件（三条同时满足才引入）

| 条件 | 判据 |
|---|---|
| 内容 | 长帖、版块分区、邮件摘要成为主要诉求，页尾线程与 `Post` 已不够 |
| 资源 | 同机内存加到 ≥8GB，或 Discourse 有独立机器；不与 API/DB 争资源 |
| 身份 | 有可维护的 OIDC SSO（Casdoor 或等价 IdP），账号生命周期不靠手工双写 |

只满足内容一条时，先在现有 `Post` 模型上加长帖/版块字段与列表，不换运行时。Answer、NodeBB
的运维面与 Discourse 同类，不构成「换一个就便宜」的理由。

> P2 实际选定的卫星论坛是 **NodeBB**（GPL-3.0）：资源门槛、与 FastAPI 的边界、OIDC SSO
> 与 webhook 回写 outbox 见 `COMMUNITY-NODEBB.md`、部署模板 `../deploy/compose.community.yml`。
> 本节的判断对 NodeBB 同样成立，只是运行时从 Ruby/Sidekiq 换成 Node/Redis。

## 5. 为什么不是从零造轮子

### 5.1 用成熟框架与模式，不自写通用能力

| 能力 | 采用的成熟件 | 来源 | 我们只写什么 |
|---|---|---|---|
| OAuth2/OIDC 客户端、state/nonce/PKCE、JWKS | Authlib | <https://authlib.org/> · <https://docs.authlib.org/> | provider 配置、claims 到 `users` 的映射 |
| 表单状态与校验 | VeeValidate | <https://vee-validate.logaretm.com/v4/> | 字段与领域校验规则 |
| schema 与类型推导 | Zod | <https://zod.dev/> | 与 API/Pydantic 契约对齐的 schema |
| 无障碍交互原语 | reka-ui | <https://reka-ui.com/> | 组合成登录、评分、评论组件 |
| 后台表单与评分控件 | Ant Design Form / Rate | <https://ant.design/components/form> · <https://ant.design/components/rate> | 审核动作、权限与状态机 |
| 1–5 星、聚合均分、样本量 | MusicBrainz Rating System | <https://musicbrainz.org/doc/Rating_System> | 维度、样本不足、装过机单独均分 |
| 变更集（changeset）与可回滚编辑 | OpenStreetMap Changeset | <https://wiki.openstreetmap.org/wiki/Changeset> | 投稿批次、依据、字段级旧值/新值 |
| 字段级修订史 | Open Food Facts revisions | <https://world.openfoodfacts.org/faq> | 谁在何时改了什么、依据是什么 |
| 信任等级与权限阶梯 | Discourse Trust Levels | <https://blog.discourse.org/2018/06/understanding-discourse-trust-levels/> | 本站的新用户/常驻/站务门槛 |
| 静态镜像评论 | giscus | <https://giscus.app/> | 镜像只读回落与历史导入 |

这些是**模式与库**，不是复制一套产品。比如借 MusicBrainz 的「1–5 星由服务端聚合」，
不借它的音乐实体；借 OSM 的「一次编辑是一个带说明的 changeset」，不借它的地图模型。

### 5.2 自研边界：只写领域逻辑

自研只放这些：

- **部件口径与数据闸门**：字段、单位、来源分级、`null` 纪律（在 `RoboWiki` 仓，不在本仓）。
- **评分规则**：维度裁剪、`n < 3` 标样本不足、装过机单独统计、分布与排序。
- **投稿 changeset 与 outbox**：提案 → 审核 → PR → release，幂等键、重试、回滚。
- **权限与信任等级映射**：本站的 `is_staff`、声望、举报处置与 Discourse TL 的对应关系。

判断标准：换掉这个库会不会改变业务语义？不会就用库；会才自己写。协议、表单状态、
无障碍原语、编辑器都不属于领域逻辑。

## 6. 身份抽象

### 6.1 表形状

```
users(id, handle, display_name, email, email_verified, password_hash,
      bio, avatar_hue, is_staff, reputation, created_at)

identities(id, user_id, provider, subject, email, display_name, avatar_url,
           created_at, last_login_at)
  unique(provider, subject)
  index(user_id)
```

- `users` 仍是唯一账号与资料实体；评分、帖子、投稿的外键不改。
- `identities` 只回答「这个外部身份是谁」；`subject` 必须是 provider 的稳定 id，
  不能用邮箱、handle 或昵称。
- provider 取值：`password`（本地，subject = `users.id`）、`wechat_mini`（openid/unionid）、
  `github`（数字 id）、`oidc`（issuer + sub）。
- 同一用户可绑定多个 provider；解绑只删 `identities` 行，不删 `users`。

### 6.2 登录流

- **Web/PWA**：本地密码继续可用；GitHub/OIDC 走 Authlib 的授权码 + PKCE，回调后
  upsert `identities`，再签发本站 JWT。当前 Bearer 令牌契约不变。
- **微信小程序**：`wx.login` 取 code → 服务端调 `jscode2session` 换 openid/unionid，
  再 upsert `identities`。不接受客户端传来的 openid；`session_key` 不进 JWT、不回传客户端。
  有 unionid 时优先用 unionid 绑定，避免同用户在不同应用下变成两个账号。
- **App**：系统浏览器 + 授权码 + PKCE，不内嵌密码页。
- **机器人**：继续用 `X-Bot-Token`，不进入用户身份体系。

### 6.3 Casdoor 为什么延后

Casdoor 解决的是「多个应用共享登录、集中用户生命周期、管理后台」。当前只有一个写域、
一类账号，先上 Casdoor 等于为一个还不存在的问题增加一个运行时。触发条件：

- 出现第三类及以上外部身份源，或第二个内部应用要复用登录；
- 站务需要集中式用户管理、审计或自助改密；
- 能接受 Casdoor 的部署、升级、备份与 OIDC 配置维护。

届时 Casdoor 作为 OIDC IdP 放在 Authlib 前面，`identities` 仍是本站的用户映射，不把
`users` 外键迁走。

### 6.4 统一错误契约

所有客户端只解析一种错误信封：

```json
{"error": {"code": "rating_exists", "message": "你已评价过这个部件", "request_id": "…", "details": {}}}
```

过渡期保留 FastAPI 的 `detail` 字段一个版本，避免旧客户端断掉；新代码只写 `error`。
`request_id` 与 `X-Request-ID` 同源，便于把前端报错对到日志。

## 7. 评论、评分、投稿的边界

- **评论不另起库**：零件评价、社区讨论、文档页讨论都在 Post/Comment/Vote/WikiComment；
  `kind` 决定列表与校验，`part_id`/`page` 决定挂载点。giscus 只在纯静态镜像出现。
- **评分唯一键泛化**：从 `(user_id, part_id)` 扩到 `(user_id, entity, entity_id)`，
  与 ADR-004 的 `rating.schema` v3 对齐；过渡期保留 `part_id` 别名，旧数据不重写。
- **评分只有一条聚合链**：站内评分与 GitHub issue 快照最终汇到一个读模型，
  快照带 `source=issue` 标记；页面、API、静态产物读同一个数。两条链各算一套均分是
  不可接受的漂移。
- **投稿是 changeset**：一次提案包含目标实体、字段级 before/after、依据 URL、提交人、
  审核记录与 outbox 幂等键。审核通过只改提案状态，worker 开 PR、合并并发布 `data-v*`
  后才回灌只读投影。
- **历史导入是单向的**：giscus 的历史讨论可按页面路径导入 `wiki_comments`，保留原作者、
  原时间与外链，标 `source=giscus`；导入后不回写 GitHub。镜像端继续用 giscus 时，
  它是独立渠道，不承诺双向同步。

## 8. 迁移阶段

### P0：身份与可靠性

- Alembic 建 `identities`，加 provider 适配层；本地密码作为 `password` provider。
- 接 Authlib：GitHub/OIDC 授权码 + PKCE；回调只做「验 state/nonce → 换 token → upsert identity」。
- 微信小程序登录：`wx.login` → 服务端 `jscode2session` → 绑定同一 `users`；只读壳先不改。
- 统一错误契约与 `request_id`；OpenAPI 增加错误 schema；客户端契约测试覆盖 401/403/409/422。
- 备份按 `../deploy/README.md` 执行：`pg_dump` + 异地加密 + 每季度恢复演练；PII 不进 git。

验收：Web 与小程序登录落到同一 `users`；同一错误在 Web/小程序/控制台解析一致；
恢复演练能用备份起一套可读的 API。

### P1：互动统一

- 评分唯一键与聚合泛化到 `(user, entity, entity_id)`；issue 快照作为导入源；
  页面/API/静态产物对账一致。
- 投稿 changeset：字段级 before/after、证据、changeset id、审核日志、outbox 幂等与重试。
- giscus 历史评论一次性导入 `wiki_comments`；导入后冻结该来源，标记 `source=giscus`。
- Vue 表单统一到 VeeValidate + Zod + reka-ui；控制台评分/审核统一到 AntD Form/Rate。

验收：同一部件的评分在页面、API、快照三处计数一致；旧 issue 重放幂等；导入评论的
页面路径与外链稳定。

### P2：按触发条件引入

| 组件 | 触发条件 | 引入方式 |
|---|---|---|
| Casdoor | 第三种身份源 / 第二个内部应用复用登录 / 站务需要集中用户管理 | 作为 OIDC IdP 放在 Authlib 前，`identities` 保留 |
| Discourse | 长帖/版块/邮件摘要需求 + ≥8GB 或独立机器 + 可维护的 OIDC SSO | 独立卫星社区，主站不嵌论坛 |
| Meilisearch | 文档 >20 万或搜索 p95 >300ms | 先影子索引对账，再切读路径 |

每个组件进入部署面前必须有：数据导出路径、回滚步骤、备份与告警归属。

## 9. 风险与对冲

| 风险 | 具体表现 | 对冲 |
|---|---|---|
| PBKDF2 不能直导 Casdoor | 本站格式是 `pbkdf2$迭代$盐$摘要`，不是 Casdoor 可直接识别的编码；算法同名也不等于参数/字段一致 | 不批量搬 `password_hash`；Casdoor 迁移走「按 `password_type` 重新编码并核对参数」或「强制重置/首次登录惰性迁移」；`identities` 保证 user id 不变 |
| giscus 数据单向 | 评论存在 GitHub Discussions，导入后无法回写；删除、编辑、reaction 不同步 | 只做一次性导入并标 `source=giscus`；导入后冻结该来源；镜像端 giscus 视为独立渠道，不做双向承诺 |
| Discourse 运维贵 | Ruby/PG/Redis/Sidekiq、升级、邮件送达率、反垃圾、备份都需人 | 三条触发条件同时满足才上；优先独立机器或托管；预算与值班先落实 |
| 小程序内容安全与类目审核 | UGC 需要内容安全接口、举报与审核；ICP、服务类目可能被拒或复审 | 先只读壳；写入功能过审后再开；服务端接内容安全检查 + 人工审核队列；保留 Web 兜底 |
| 单人维护疲劳 | 运行时、队列、账号源一多，升级与故障定位先崩 | 一个 API、一个库、一套身份；Casdoor/Discourse/Meilisearch 全部后置；每季度只做备份演练与依赖升级两件固定事 |
| 评分双链漂移 | 站内票与 issue 快照各自聚合，页面数字不一致 | 单一聚合读模型 + `source` 标记 + 定时对账；对不上先停下新写入再修 |
| 错误契约切换伤客户端 | 旧客户端只认 `detail` | 一个版本内双写 `error` 与 `detail`；契约测试覆盖；小程序发版后再删旧字段 |

## 10. 不做什么

- 不把 Discourse/Answer/NodeBB 部署成主站社区。
- 不自研 OAuth/OIDC、表单校验、无障碍组件或 Markdown 编辑器。
- 不为 Web/小程序/App 各写一套登录、评分、评论逻辑。
- 不把 giscus 当主站评论库，也不做 giscus 双向同步。
- 不在没有触发条件时把 Casdoor、Discourse、Meilisearch 放进部署面。
- 不让客户端直接写目录数据；目录仍只由 `RoboWiki` 仓 release 写。

## 11. 账号与邮件（对标 NewAPI / Sub2API）

借鉴的是“可审计的一次性流程”，不是商业化计费体系：

- **采用**：邮箱验证码/令牌只存哈希、单活覆盖、过期与原子消费；换绑邮箱先验证新地址、已设密账号再验当前密码；验证成功提升 `session_epoch` 并撤销旧会话；通知偏好 + 异步邮件 outbox（worker 重试、去重键）；HTML/纯文本双模板；SMTP 测试发信。
- **保持本站模型**：身份仍是 `identities` 表，不在 users 上堆 provider 列；refresh token 仍落库，不依赖 Redis。
- **暂不采用**：邀请返利、兑换码、套餐计费、多 OAuth 采纳矩阵、Passkey、TOTP/备份码、全量 step-up 授权矩阵。这些是商业化网关的必需项，不是硬件目录社区的基础闭环；需要时再按同一套 `auth_flows`/审计模型扩展。

## 参考

- Authlib：<https://authlib.org/> · <https://docs.authlib.org/>
- VeeValidate：<https://vee-validate.logaretm.com/v4/>
- Zod：<https://zod.dev/>
- reka-ui：<https://reka-ui.com/>
- Ant Design Form / Rate：<https://ant.design/components/form> · <https://ant.design/components/rate>
- MusicBrainz Rating System：<https://musicbrainz.org/doc/Rating_System>
- OpenStreetMap Changeset：<https://wiki.openstreetmap.org/wiki/Changeset>
- Open Food Facts revisions：<https://world.openfoodfacts.org/faq>
- Discourse Trust Levels：<https://blog.discourse.org/2018/06/understanding-discourse-trust-levels/>
- giscus：<https://giscus.app/>
- Casdoor：<https://casdoor.ai/> · <https://casdoor.ai/docs/user/overview/>
- 微信小程序登录：<https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/login.html> · <https://developers.weixin.qq.com/miniprogram/dev/server/API/user-login/api_code2session.html>
- OAuth 2.0 PKCE：<https://datatracker.ietf.org/doc/html/rfc7636>
- FastAPI：<https://fastapi.tiangolo.com/>
- New API（账号/邮件/会话/2FA 参考）：<https://github.com/QuantumNous/new-api>
- Sub2API（邀请/邮箱验证/通知模板参考）：<https://github.com/Wei-Shaw/sub2api>

# 卫星社区：NodeBB 边界、SSO 与运维

> 状态：**P2 条件项，未部署**。本文只定义边界与契约，不表示论坛已经在跑。
> 上位：`ADR-007-interaction-stack.md`（互动栈）、`deploy/README.md`（主站部署）、
> `clients/app/README.md`（App 契约）。
> 部署模板：`deploy/compose.community.yml`（独立 Compose 项目，默认不启动）。

## 0. 一句话结论

**NodeBB 只做论坛与长帖；用户、评分、投稿、审核仍然只有 FastAPI 一个写域。**
两边通过 OIDC 共享登录、通过 webhook → `outbox` 回传事件，不共享数据库、不双向同步内容。
三条触发条件没同时满足，就不要部署这套栈。

## 1. 边界

| 能力 | 归属 | 说明 |
|---|---|---|
| 账号、邮箱、GitHub/微信身份 | **FastAPI** | `users` + `identities` 是唯一账号源；NodeBB 只保存 OIDC 映射后的论坛用户 |
| 零件评分、分布、排序 | **FastAPI** | 评分是结构化数据，不进论坛帖；NodeBB 的“赞”不参与评分聚合 |
| 投稿、字段级 before/after、审核 | **FastAPI** | 审核通过只改提案状态，发布仍走 `Outbox` → PR → `data-v*` |
| 文档页/零件页短讨论 | **FastAPI** `wiki_comments` | 页尾线程继续自托管；不要同一线程两边各存一份 |
| 长帖、版块分区、版块订阅、邮件摘要 | **NodeBB** | 论坛的原生强项；帖子与主题只存在 NodeBB 库 |
| 论坛内的举报与版主处置 | **NodeBB** | 站务可在 ACP 处理；涉及本站账号的封禁要另走 FastAPI |
| 通知 | 各自 | 论坛通知留在 NodeBB；本站评论/审核通知归 FastAPI，不合并成一张表 |
| 媒体 | 各自 | 论坛附件在 `nodebb-uploads`；本站评论/投稿的媒体仍由 FastAPI 管 |

三条硬规则：

1. **不跨库外键**。NodeBB 的 `nodebb` 库与主站库是两个 Postgres 实例；
   需要关联时只存外部 id + 类型，不 JOIN。
2. **不双写同一内容**。一个讨论要么在页尾（`WikiComment`），要么在论坛（NodeBB topic），
   不做镜像；跨端只放链接。
3. **NodeBB 不是评分/投稿的入口**。论坛里说“这个电机该标 48V”仍然是讨论，
   要改目录必须走本站投稿与审核。

## 2. 触发条件

三条**同时**满足才启动 `compose.community.yml`：

| 条件 | 可观测判据 | 不满足时怎么办 |
|---|---|---|
| 内容 | 页尾线程反复顶到 4000 字上限；单页回复超过约 20 条后无法阅读；出现版块分区、版块订阅、邮件摘要的明确请求 | 先给 `Post`/`WikiComment` 加分页、折叠、长帖字段，不换运行时 |
| 资源 | 宿主机 ≥ 8GB 内存，或整份社区栈放到独立机器；不与 API/DB 争内存 | 留在这台 2C/4G 上就继续用现有讨论；NodeBB 常驻 1.5–2.5GB，构建与备份峰值更高 |
| 身份 | 有可维护的 OIDC IdP（Casdoor 或 FastAPI OIDC），staging 验证过登录、登出、封禁与故障回退 | 没有 SSO 就不要开公共注册：第二套账号的合并成本高于论坛收益 |

只满足“内容”一条时，**不部署论坛**。这是 ADR-007 已经裁定的顺序。

## 3. 部署形态

- 独立 Compose 项目 `robowiki-community`：`nodebb` + `community-db`（Postgres）+ `community-redis`。
- NodeBB 只发布到 `127.0.0.1:4567`，由 1Panel OpenResty 用独立子域反代；
  需要 WebSocket upgrade 与 ≥ 20m 的请求体上限（附件/头像）。
- 不加入 `robowiki_default` 网络，不复用主站 `POSTGRES_PASSWORD`，不复用 `pgdata` 卷。
- 首次启动用交互式安装向导（`docker compose -f compose.community.yml run --rm nodebb`），
  `config.json` 落在 `nodebb-config` 卷，权限 600；密码只输进容器，不进 git。
- 向导只配 Postgres。要让 Redis 承载会话，装完后在 `config.json` 补 `session_store`
  （compose 文件头有形状）；不补也能跑，但 NodeBB 重启会丢登录会话。
- 资源门槛、卷清单、备份/升级/回滚命令都写在 compose 文件头部注释里，
  这里不重复抄一遍命令，避免两处漂移。

## 4. 身份：OIDC SSO

### 4.1 两条路线

| 路线 | 适用 | 代价 |
|---|---|---|
| **A. Casdoor 作 IdP**（优先） | 已经因为第二种应用/第三种身份源引入 Casdoor | 多一个运行时；但 FastAPI 与 NodeBB 都只做 OIDC 客户端，边界最干净 |
| **B. FastAPI 作 OIDC IdP** | 不想再养 Casdoor，且愿意维护签名密钥与授权页 | 当前 FastAPI 只有 Authlib **客户端**；要新增 discovery、authorize、token、userinfo、JWKS、同意页与密钥轮换，是一套新子系统，不是一个配置项 |

**裁定**：先 A。只有 Casdoor 的部署/备份/升级确实成为负担，且 FastAPI 已经需要给第二个内部应用发令牌时，才评估 B。
无论哪条，NodeBB 都只是 OIDC 客户端；`users` 外键不迁到论坛。

### 4.2 claims 映射

| OIDC claim | NodeBB 侧 | 规则 |
|---|---|---|
| `sub` | 账号关联键 | 必须是稳定不可变的本站 user id；换 handle、换邮箱都不能变 |
| `preferred_username` | 论坛用户名 | 取本站 `handle`；冲突时由插件加后缀，不改本站 handle |
| `email` / `email_verified` | 邮箱 | 只在 `email_verified=true` 时用于通知；**不允许仅凭同邮箱自动合并账号** |
| `name` | 显示名 | 取 `display_name` |
| `picture` | 头像 | 可空；没有就由 NodeBB 生成 |
| `groups` | 角色提示 | 最多映射到版主候选；**不自动授予管理员**，管理员在 ACP 手工指定 |

### 4.3 插件与配置

NodeBB 核心不含 OIDC，需要维护中的 SSO 插件。可评估：

- `nodebb-plugin-fusionauth-oidc`：FusionAuth 维护，但按标准 OIDC 实现，可接任意 provider；
- `nodebb-plugin-sso-oauth2-multiple`：通用 OAuth2 多 provider；
- 其他社区 OIDC 插件。

选型前逐项确认：支持 NodeBB 当前大版本、支持 PKCE S256、用 `sub` 而不是邮箱做关联、
最近一年有提交、许可证与 GPL-3.0 兼容、升级时不改核心。任一项不满足就换插件。

配置占位（值从密钥管理读取，不提交）：

```text
issuer         = https://<idp>/...
client_id      = <nodebb client id>
client_secret  = <secret>
scopes         = openid profile email
callback       = https://community.<domain>/auth/<plugin>/callback
```

### 4.4 SSO 安全底线

- **保留一个 break-glass 本地管理员**，强随机密码放密码管理器；IdP 故障时还能进 ACP。
- SSO 验证通过后**关闭论坛本地注册与本地密码登录**，只留管理员账号；否则会出现绕过 IdP 的入口。
- 要求 `email_verified` 才可信邮箱；同邮箱不同 `sub` 默认视为两个人。
- 不做单点登出承诺：NodeBB 登出、FastAPI 登出各自生效；需要全端退出时两边都调用。
- 封禁不自动同步：论坛封禁只影响论坛；本站封禁需要同时处理论坛账号，写成值班步骤。

## 5. 内容映射：page / term

- 本站页面标识仍是 VitePress 路径，如 `parts/actuator/dm`（无前导斜杠）。
- 论坛主题用**标签**建立关联：`wiki:parts/actuator/dm`。标题可改，标签与路径是稳定键。
- 页面上的入口只在主题存在时显示“去论坛讨论”；不做 iframe 嵌入，也不把论坛帖子渲染回页面。
- giscus 的 `term`/`pathname` 只用于一次性历史导入（见第 7 节），不作为新讨论的主键。
- 迁移期如果同一页面既有页尾线程又有论坛主题，明确标注两个渠道，不合并计数。

## 6. webhook 回写 outbox

### 6.1 方向

NodeBB → FastAPI 的事件只用于**索引、通知、声望**，不用于改变评分/投稿/审核状态。
FastAPI → NodeBB 不主动推送内容；需要发帖时由人工在论坛操作。

### 6.2 端点（P2 预留，尚未实现）

```http
POST /api/v1/community/webhook/nodebb
X-NodeBB-Event: post.create
X-NodeBB-Delivery: <delivery id>
X-NodeBB-Signature: sha256=<hmac>
Content-Type: application/json
```

- 用官方 `nodebb-plugin-webhooks`（或等价插件）把 hook 数据 POST 过来。
  插件若不能签名，就只在回环/内网暴露端点，并加路径 secret + 速率限制；
  **没有签名的 payload 一律当不可信输入**。
- 校验：常量时间比较签名、限制 body ≤ 32KB、按 `X-NodeBB-Delivery` 去重、拒绝重放。
- 处理：**只写 outbox，不在请求里做业务**。

### 6.3 outbox 行

现有 `Outbox` 模型已经够用，不新增表：

| 字段 | 值 |
|---|---|
| `action` | `community_event` |
| `idempotency_key` | `nodebb:<event>:<delivery-id>` |
| `payload` | 最小事件：`event`、`topic_id`、`post_id`、`uid`、`slug`、`title`、`url`、`occurred_at` |
| `submission_id` | `NULL` |
| `status` / `attempts` / `next_at` | 复用现有 worker 重试语义 |

worker 消费时做三件事：更新本地的主题索引、给相关用户发本站通知、按规则记声望。
任一步失败按 `attempts/next_at` 退避重试；重复投递靠幂等键吸收。

### 6.4 对账

webhook 会丢（插件重试上限、网络、部署窗口）。每天一次只读对账：
拉论坛最近主题/帖子列表，把缺失的 `delivery` 以 `action=community_reconcile`
写入同一张 outbox，让消费者走同一条代码。不要为对账再写一个直连论坛库的脚本。

## 7. 迁移、备份、回滚

### 7.1 迁移顺序

1. 先备份主站（`deploy/backup/backup.sh`）和论坛三份数据（Postgres、上传卷、config.json）。
2. 导入 giscus 历史评论到 `wiki_comments`（`scripts/import_giscus.py`，先 `--dry-run`）；
   导入后冻结该来源，标 `source=giscus`，不回写 GitHub。
   - 脚本**不联网**：先在本地导出 GraphQL/JSON，再离线导入；
   - 作者生成 `giscus-<login>` 占位账号（`password_set=False`、无邮箱，`identities.provider=giscus`），
     不能登录，需要用户自己绑定 GitHub 后人工合并；
   - 重复执行按 `external_ref` + `--ledger` 去重；当前表没有 `source/external_ref` 唯一索引，
     所以这是兜底而不是硬约束。P1 加成列后应改为直接写列并删掉 ledger。
3. 启动论坛，先只读验收：SSO 登录、发帖、上传、邮件、webhook 到 outbox。
4. 再把页面入口从 giscus 切到“论坛讨论”；页尾线程保留，不迁进论坛。

### 7.2 备份

- 论坛 Postgres：每日 `pg_dump -Fc`，与主站备份分开存放、同样加密。
- `nodebb-uploads` 与 `nodebb-config`：tar 归档；`config.json` 含 secret 与数据库口令，权限 600。
- Redis：AOF 打开；丢失会话可接受（重新登录），但不要和 Postgres 放在同一块盘上一起坏。
- 每季度做一次恢复演练：恢复到新目录 → 起旧 tag → 能登录、能打开一个主题、能上传一张图。

### 7.3 升级与回滚

- 固定 `NODEBB_TAG`，不用 `latest`；升级前读 release notes 与插件兼容列表。
- 升级会触发 `nodebb upgrade`，库迁移通常**不可逆**。
- 回滚 = 旧 tag + 恢复升级前的 Postgres/上传卷；只回滚镜像、不回滚数据库，
  多半会在启动时 schema 不匹配。
- 插件升级单独排期；一次只升一个，坏了能定位。

## 8. 许可证与合规

- NodeBB 是 **GPL-3.0**。本仓也是 GPL-3.0-only，方向一致。
- 以独立进程、独立库运行未修改的 NodeBB，不把 GPL 代码链接进 FastAPI；
  两边只通过 HTTP/OIDC/webhook 通信。
- 如果分发修改过的 NodeBB 镜像、主题或插件，必须按 GPL-3.0 提供对应源码；
  内部自用不触发分发义务，但不要把“自用”当成“永不公开”的借口。
- 第三方插件/主题的许可证各不相同；安装前确认与 GPL-3.0 兼容，并记录版本与来源。
- 不复制 NodeBB 的前端模板、语言包或管理界面代码到本站仓库；需要参考时只借模式。
- “NodeBB”名称与标识属于上游；子域与页面文案不要暗示官方背书。

## 9. 运维风险

| 风险 | 表现 | 对冲 |
|---|---|---|
| 内存挤爆 | NodeBB 构建/升级峰值把同机 API 挤到 OOM | 独立机器或 ≥8GB；`mem_limit` 不是保险，仍要监控 |
| 插件腐烂 | 升级 NodeBB 后 SSO/编辑器插件不兼容 | 固定大版本与插件清单；升级前在 staging 演练；一次只升一个 |
| SSO 锁死 | IdP 故障或 claim 改错，管理员进不去 | break-glass 本地管理员；保留 ACP 直连回环入口 |
| 账号双轨 | 论坛用户与本站用户对不上、封禁不一致 | `sub` 稳定映射；不做邮箱自动合并；封禁写成双端值班步骤 |
| 邮件送达率 | 注册验证/订阅邮件进垃圾箱 | 独立子域、SPF/DKIM/DMARC；先小流量验证；保留站内通知 |
| 垃圾注册 | 公开论坛被 bot 灌水 | 邀请制/审核制注册；最小发帖等级；内容安全与举报入口 |
| 迁移不可逆 | 升级后想退回旧版发现 schema 已改 | 升级前备份；回滚按“旧镜像 + 旧库”整体回退 |
| 上传盘增长 | 附件把磁盘吃满，Postgres 先坏 | 配额与清理策略；上传卷单独监控；备份不含缓存构建物 |
| 两套审核队列 | 举报在论坛与本站各一半，没人闭环 | 明确归属：论坛内容论坛处理；涉本站账号/目录的转 FastAPI |
| 运维面扩大 | 又多一个要升级、备份、看 CVE 的系统 | 触发条件不满足就不上；上了就接受它是长期成本 |

## 10. 不做什么

- 不把 NodeBB 当主站评论后端，也不把页尾线程迁进论坛。
- 不做 giscus / NodeBB / `wiki_comments` 三方双向同步。
- 不让 NodeBB 读写主站库，不跨库外键，不复制 `users` 表。
- 不用论坛“赞”替代评分，不在论坛里审核目录投稿。
- 不在 2C/4G 的 API 机器上启动这份 compose。
- 不在没有 OIDC 与 break-glass 的情况下开放公共注册。
- 不为了“统一体验”把两个子域硬拼成一个 SPA。

## 参考

- NodeBB：<https://nodebb.org/> · 文档 <https://docs.nodebb.org/>
- NodeBB 配置（postgres / session_store）：<https://docs.nodebb.org/configuring/config/>
- NodeBB 官方 compose：<https://github.com/NodeBB/NodeBB/blob/master/docker-compose.yml>
- NodeBB webhooks 插件：<https://github.com/NodeBB/nodebb-plugin-webhooks>
- FusionAuth OIDC 插件：<https://github.com/FusionAuth/nodebb-plugin-fusionauth-oidc>
- 多 provider OAuth2 插件：<https://www.npmjs.com/package/nodebb-plugin-sso-oauth2-multiple>
- OAuth 2.0 PKCE：<https://datatracker.ietf.org/doc/html/rfc7636>
- Casdoor：<https://casdoor.ai/>
- giscus：<https://giscus.app/>

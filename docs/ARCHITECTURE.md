# 架构：GitHub 与服务器怎么共存

一句话：**GitHub 管「事实」，服务器管「流量与实时」**。两者共享同一份 schema
与同一批构建产物，所以永远只有一个真相源。

```
                     ┌───────────────────────────────────────┐
  写侧（少、要身份）    │  GitHub                                 │
  ─────────────────  │  · PR      → 部件参数 / 优惠（内容层）      │
                     │  · issue   → 评分 / 实测 / 纠错（行为层）    │
                     │  · Actions → 聚合 → 写回 snapshot         │
                     └──────────────────┬────────────────────┘
                                        │ 构建产物 = 唯一契约
                    catalog.json · ratings_snapshot.json
                    reviews_snapshot.json · offers.json
                                        │
                     ┌──────────────────┴────────────────────┐
  读侧（多、只读）      │  静态站（VitePress，构建期消费）           │
  ─────────────────  │  API（FastAPI，运行期消费同一产物）         │
                     └───────────────────────────────────────┘
```

## 三条不可违反的约定

### 1. 读侧只读产物，不读 `data/catalog/`

`data/catalog/**` 是**人写的内容**，`catalog.json` 等是**机器产物**。
站点和 API 都只消费后者。这样静态站与 API 对内容的理解不可能漂移，
而且迁移服务器时产物一个字都不用改。

> **catalog/ 是唯一事实源**（2026-10-28 起）。旧的扁平采集文件
> （`motors.json` / `controllers_*.json` / `sensors.json`）与历史归档
> `data/_backup/` 已全部出库；loader / validate / 后端种子不再保留对它们的
> 兼容分支。贡献者只改 `catalog/<品类>/<厂商>.json` 一个文件即可生效。

### 2. 只有 `pipeline/` 能产生产物

```
pipeline/  确定性构建（每次必跑，纯函数，产物可 diff）
  load.py         读 data/，统一结构
  validate.py     数据闸门：口径、量程、键集、跨行不变量
  build_site.py   生成 VitePress 内容与静态产物
  ingest_*.py     GitHub issue → 快照

tools/     一次性迁移（跑一次就归档，不参与构建）
  见 tools/README.md —— 里面的脚本会改数据，别在别人改完之后跑
```

### 3. 缺失写 `null`，不省略 key

读侧要能区分「厂商没公布」和「这个属性不存在」。这也是 `schema/` 里
`part.schema.json` 把大部分字段标成 `["number", "null"]` 的原因。

## 贡献分层

| 层 | 通道 | 门槛 | 谁把关 |
|---|---|---|---|
| 内容（参数/优惠） | PR | 会改 JSON | CI 闸门 + CODEOWNERS |
| 行为（评分/实测） | issue 表单 | 有 GitHub 账号 | Actions 聚合 |
| 行为（将来高并发） | API | 同 schema | 服务端限流 |

内容层用 PR 而不是表单，因为它需要**可评审的 diff**；
行为层用表单，因为它量大、单条价值低、评审不划算。

## 部署形态与迁移

现在是**纯静态**：Pages 托管 VitePress，评分/实测靠 issue + Actions 聚合。
这是最省钱也最省事的一档，只要投稿量还是「天」为单位就够了。

要往上走时（有人天天来打分、需要实时显示），只动这三处：

```
SQLite → Postgres（一个 DSN）
uvicorn 单进程 → gunicorn -k uvicorn.workers.UvicornWorker -w 4
内存限流器 → Redis（现有实现是进程内，多副本会失效）
```

不动：`data/`、`schema/`、`pipeline/`、组件、issue 链路、构建产物。

<details>
<summary>更远的一档（>1000 件 / 多实例）时再考虑</summary>

- 图片从 repo 搬到对象存储 / CDN（91 张 5 MB，千件会到 100 MB+）
- 静态站只留「品类页 + 精选部件页」，全量检索走后端 API
- 构建拆页（每品类独立构建），避免单次构建超过 5 分钟

**现在不要做。** 那会把复杂度花在还没出现的问题上。

</details>

### L0 → L1 迁移清单

```
必改  SQLite → Postgres（一个 DSN）
      uvicorn 单进程 → gunicorn -k uvicorn.workers.UvicornWorker -w 4
      内存限流器 → Redis（现有实现是进程内，多副本会失效）
      图片 repo → 对象存储/CDN
不改  data/、schema/、pipeline/、组件、issue 链路、构建产物
```

## 为什么构建产物要「可 diff」

```
python -m pipeline build     # 同样输入 → 字节级同样的输出
```

只有这样，PR 里「产物也跟着变了」才有意义 —— 评审能直接看到
「这个型号的峰值扭矩从 40 变成 45」。如果构建不确定，产物 diff 就是噪音，
最后只能靠人肉点页面确认。

## 规模判断（先算再造）

按「1000 注册用户 / 每天 200 次评分 + 20 条实测」：

```
写 QPS ≈ 0.003   → Postgres 单实例绰绰有余
读 QPS：静态站 99% 命中 CDN → 源站 ≈ 0
构建：80 件 15 s；1000 件预计 4–6 min → 超过 5 min 再拆页构建
```

**真正的瓶颈是构建时间和仓库体积，不是数据库。** 所以在有 1000 个部件之前，
不要引入微服务、消息队列或 Redis——那会把复杂度花在不会出问题的地方。

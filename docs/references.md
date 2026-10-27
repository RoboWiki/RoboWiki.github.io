# 参考项目与「造 vs 用」的取舍

搜索口径：GitHub Search API 按 stars 降序。分四个方向找，星数是搜索当时的值。

| 方向 | 候选 | 星 | 结论 |
|---|---|---|---|
| 零件库 / BOM / 供应商 | **inventree/InvenTree** | 7,764 | **借数据模型**（Part / PartParameter / BomItem / SupplierPart） |
| | Part-DB | ~1,300 | 同上，功能更轻 |
| 无代码数据库后端 | nocodb/nocodb | 65,369 | 不采用（见下） |
| | directus/directus | 38,645 | 不采用 |
| | strapi/strapi | 73,387 | 不采用 |
| 管理面板 | appsmithorg/appsmith | 41,128 | 不采用 |
| 社区 / 论坛 | discourse/discourse | 48,021 | **借模型**（topic/post/vote/badge 语义） |
| | **apache/answer** | 15,701 | **借模型**（question/answer/comment/vote/reputation，中文语境最贴近） |
| | NodeBB/NodeBB | 15,243 | 备选 |
| | ruby-china/homeland | 3,858 | 备选 |
| 评论组件 | giscus/giscus | ~8,000 | 备选（GitHub Discussions 做后端） |
| 全栈模板 | **fastapi/full-stack-fastapi-template** | 官方 | **采用结构**（`app/api/routes` + `app/core` + `api/deps.py`） |
| ORM | tiangolo/sqlmodel | ~8,000 | **采用** |
| 前端脚手架 | **ant-design/ant-design-pro** | ~37,000 | **采用版本组合**（React 19 + antd 6 + TanStack Query 5） |
| | refinedev/refine | ~30,000 | 备选（数据密集型后台更强，但抽象层会挡自定义口径校验） |
| **视觉参考** | **lobehub/lobe-chat** | ~60,000 | 借**卡片密度与深色层级**：近黑底 + 极淡径向光 + 圆角 16px |
| | **shadcn-ui/ui** | ~90,000 | 借**组件形态**（边框 7% 白、hover 抬升、ring 描边） |
| | **tremorlabs/tremor** | ~16,000 | 借**数据卡的排版**（指标在上、正文在中、元信息在下） |
| | **open-webui/open-webui** | ~90,000 | 借**图片区做法**：径向渐变底 + 网格叠层 + 低透明度遮罩 |

本地副本在 `_refs/`（浅克隆，不参与运行）。

---

## 为什么不全盘采用一个现成系统

三个方向各有一个"看起来能直接套"的方案，逐个说清为什么没套。

### ① 用 InvenTree 顶替整个选型台

InvenTree 有 `Part` / `PartParameter`（带单位）/ `BomItem` / `SupplierPart` / 库存，
是这块最成熟的开源实现。但它缺的恰好是本站的核心：

- 它管「有多少库存、装在哪」，不管「这个电机的 `armature` 该是多少、`J` 是电机侧还是输出侧」；
- 参数是自由键值对，没有口径校验、没有 `armature == N²·J` 这类不变量、没有物理量程闸门；
- 它是 Django + Postgres 单体，社区层要另接一个系统，**「评价挂在零件上」这个设计会断**。

**结论：借它的数据模型（Part ↔ PartParameter ↔ BomItem 三层），不套它的运行时。**

### ② 用 Directus / NocoDB / Strapi 生成后端和后台

它们能在现有库上直接长出 REST API + 管理界面 + 权限 + 文件上传，能省掉大量 CRUD 代码。
但：

- 本站的写入语义不只是 CRUD：投票要**重算聚合**、声望要**级联更新**、评论要**两级约束**、
  发帖要**按 kind 分流校验**。这些都得写业务代码，无头 CMS 帮不上，只会变成"在别人的抽象层里写钩子"；
- 前端仍然要自己写（选型表、口径展示、Markdown、投票交互都是定制的）。

省下的是 CRUD，付出的是把业务逻辑塞进别人的扩展点。

### ③ 用 Discourse / Answer / NodeBB 顶替社区

它们功能远超一个零件评价区，但都假设**内容是独立话题**，没有「话题必须挂在一个零件上」
「零件页要反查自己的话题」这种一等公民关系。硬接需要插件级改造。

**结论：借投票/声望/徽章的语义，不引入第二个运行时。**
`apache/answer` 的 `power`（声望）与 `badge` 设计直接影响了本站的徽章派生逻辑。

---

## 实际「用了」什么

| 层 | 用了什么 | 来源 |
|---|---|---|
| 后端框架 | FastAPI + Pydantic v2 | 官方 |
| 目录结构 | `app/{core,api/routes,models,schemas,crud}.py` + `api/deps.py` | fastapi/full-stack-fastapi-template |
| ORM / 迁移 | SQLModel（`create_all`，暂不引 Alembic） | tiangolo/sqlmodel |
| 认证 | PyJWT + PBKDF2（stdlib `hashlib`） | 模板同款（模板用 pwdlib，这里为减依赖用 stdlib） |
| 前端框架 | React 19 + Vite 6 + TypeScript | — |
| UI 组件 | **antd 6**（Table / Drawer / Modal / Form / Rate / Descriptions / Statistic / Segmented） | ant-design |
| 数据请求 | TanStack Query 5（缓存、失效、乐观刷新） | ant-design-pro 同款栈 |
| 路由 | react-router 7 | — |
| Markdown | react-markdown | — |
| 时间 | dayjs + relativeTime + zh-cn | — |
| 表格/表单模式 | antd 的受控列定义 + Form 校验 | ant-design-pro |

**手写的只有领域部分**：口径字典（`frontend/src/fields.ts`）、数据闸门（`scripts/check_data.py`）、
「评价即帖子」的模型与校验、派生量计算。这些没有现成轮子，也不该有。

---

## 版本对齐说明

前端版本组合是照 `ant-design-pro` 的 `package.json` 定的，避免踩 antd 6 / React 19 的兼容坑：

```
react 19.3.1 · antd 6.6.8 · @tanstack/react-query 5.105.0
react-router-dom 7.18.4 · vite 6.4.5 · typescript 5.7
```

## 下一步若真要换栈

如果社区规模起来、需要独立部署与横向扩展，优先级是：

1. **SQLite → Postgres**（改 `ROBOSELECT_DB_PATH` 为 URL，SQLModel 层几乎不用动）；
2. **进程内限流 → Redis**（`api/deps.py:rate_limit` 已隔离成一个函数）；
3. **加 Alembic**（`create_all` 只适合早期）；
4. **前端拆包**（当前 1.35 MB / gzip 435 KB，`manualChunks` 拆 antd）；
5. 到这一步再考虑要不要把社区换成 Answer —— 那时有迁移价值，现在没有。

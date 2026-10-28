# RoboSelect

机器人部件选择社区：**官方参数 + 真实使用者的评分与评价**。

每个部件一页：左边是带来源等级与口径的官方参数，右边是用过的人的评分、
实测工况与讨论。不收佣金、不卖零件，所以判定不必讨好谁。

**站点**：<https://zeitvex.github.io/RoboSelect/>

```
46 个关节电机 · 4 家（达妙 DAMIAO / 大疆 DJI / 灵足 RobStride / 宇树 Unitree）
A 级数据 = 逐项核对过厂商手册；缺失一律写 null，不猜、不填补
```

## 三分钟上手

```bash
git clone https://github.com/zeitvex/RoboSelect && cd RoboSelect

python -m pipeline all            # 1. 校验数据 + 生成站点内容（约 15 秒）
python -m pytest                  # 2. 构建链 + API 测试
cd wiki && npm i && npm run dev   # 3. 本地起站（127.0.0.1:5174）
```

改一个型号的参数 = 改一个 JSON，然后 `python -m pipeline validate`。

## 目录

```
data/            唯一数据源
  catalog/<品类>/<厂商>.json   零件（一家一文件，PR 友好）
  offers/<厂商>.json           优惠
  *_snapshot.json              构建产物（评分、实测）
schema/          JSON Schema —— PR、issue 表单、API 共用同一份契约
pipeline/        确定性构建（**唯一**能产生产物的地方）
  load.py           读 data/
  validate.py       数据闸门：口径、量程、键集、跨行不变量
  build_site.py     生成 VitePress 内容与 catalog.json
  ingest_*.py       GitHub issue → 快照
tools/           一次性迁移脚本（会改数据，见 tools/README.md）
backend/         FastAPI：只读写侧（评分 / 实测 / 后台 / MCP）
wiki/            VitePress 站点
frontend/        控制台（发帖 / 信息流 / 后台改数）
docs/            ARCHITECTURE.md（GitHub 与服务器怎么共存）等内部文档
```

## 为什么这样分层

**读侧只读产物，写侧才碰数据。**

```
GitHub（PR / issue / Actions）  →  构建产物  →  静态站 + API
```

站点与 API 消费同一批 JSON，所以两边对内容的理解不可能漂移；
迁移到服务器时产物一个字都不用改。详见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 参与方式

| 想做什么 | 去哪儿 |
|---|---|
| 给某个件打分 | 部件页「去 GitHub 打分」（issue 表单） |
| 写实测（跑多久、坏没坏） | 部件页「提交实测」（issue 表单） |
| 纠参数 / 补数据 | [纠错表单](https://github.com/zeitvex/RoboSelect/issues/new?template=data-fix.yml)，不需要会 git |
| 批量加型号 / 改结构 | PR，见 [CONTRIBUTING.md](CONTRIBUTING.md) |

四条通道的分工与门槛，写在 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#贡献分层)。

## 现状（诚实版）

- 评分与实测**都还是 0 条** —— 机制建好了，还没有人用
- 46 个型号里 10 个缺产品图（达妙 JH 系列 8 个、灵足 RS10）
- 价格覆盖 36/46；优惠 16 条，全部带获取条件
- 搜索/对比在浏览器里算（`catalog.json` 81 KB），没有后端也能用

## License

MIT

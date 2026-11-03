# 贡献指南（站点仓）

RoboWiki 拆成两个仓：

- **数据、schema、产品图** → [RoboWiki/RoboWiki](https://github.com/RoboWiki/RoboWiki)
- **站点、页面、后端、控制台** → 本仓

改数据请去核心仓；本仓只处理展示、交互、页面内容与后端。

## 先跑一次

```bash
bash scripts/fetch-data-release.sh   # 下载 data.lock.json 锁定的核心仓 release
python -m pipeline build             # 生成页面
ROBOWIKI_DATA_DIR="$PWD/.data/data" \nROBOWIKI_SCHEMA_DIR="$PWD/.data/schema" \nROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts" \npython -m pytest                     # 测试
cd wiki && npm ci && npm run dev      # 本地起站
```

## 改什么 → 去哪

| 我要… | 去哪 |
|---|---|
| 加/改部件、整机、材料、工艺、软件、渠道、参数 | 核心仓 `data/` |
| 改字段口径、schema | 核心仓 `schema/` |
| 加产品图 | 核心仓 `assets/parts/` |
| 改页面文案、导航、样式、组件 | 本仓 `wiki/` |
| 改 API / 提案审核 / outbox worker | 本仓 `backend/` |
| 改控制台 | 本仓 `console/` |
| 改部署 / Caddy / Compose | 本仓 `deploy/` |
| 改多端契约 / QQ 机器人 | 本仓 `clients/` |
| 导入竞赛文档 | 本仓 `tools/site/` |

**不要手改生成物**：`wiki/docs/parts/`、`wiki/docs/public/*.json`、`wiki/docs/.vitepress/sidebar.json`
都由 `pipeline build` 生成，下次构建会覆盖。

## 数据版本

本仓通过 `data.lock.json` 锁定核心仓的 `data-v*` 发布物；Pages 构建会下载 release、
校验 SHA-256 后生成页面。数据更新流程：

1. 核心仓改数据 → 跑 `python -m pipeline validate` → 发 `data-v*` release；
2. 本仓更新 `data.lock.json` 的版本、asset 名、`sha256`、`manifest_sha256` 与 counts；
3. 本地 `fetch-data-release.sh` + `pipeline build` + `pytest`；
4. 提 PR → CI 会重新下载新 release 构建。

## 三条底线

1. 不把数据副本提交回本仓；
2. 不改生成物；
3. 数据问题去核心仓，页面/API/部署问题留本仓；C 级线索不会进站点目录，但可在核心仓保留并注明来源。

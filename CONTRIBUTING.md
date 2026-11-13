# 贡献指南（RoboWiki.github.io）

RoboWiki 由两个仓库组成：

- **`RoboWiki`**（[RoboWiki/RoboWiki](https://github.com/RoboWiki/RoboWiki)）：数据、schema、产品图；
- **`RoboWiki.github.io`**（本仓）：Astro 根站、Taro 互动端、后端、部署与客户端契约。

改数据请去 `RoboWiki` 仓；本仓只处理展示、交互、页面内容与后端。

克隆本仓（目录名就是仓库名，不再另起别名）：

```bash
git clone https://github.com/RoboWiki/RoboWiki.github.io.git
cd RoboWiki.github.io
```

## 先跑一次

```bash
bash scripts/fetch-data-release.sh   # 下载 data.lock.json 锁定的 release（gh/curl 均可，公开 release 免登录）
export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build             # 生成页面
python -m pytest                     # 测试（需先装 backend/requirements.txt）
pnpm install && pnpm dev:web          # 本地起 Astro 根站
```

Node 版本以仓库根 `.nvmrc` 为准（22），CI（`pages.yml` / `pr-gate.yml`）与
`deploy/Dockerfile.api` 用的是同一版；站点构建统一走 `npm run build`
（`vitepress build docs` + `scripts/postbuild.mjs`），不要直接调 `npx vitepress build`。

## 改什么 → 去哪

| 我要… | 去哪 |
|---|---|
| 加/改部件、整机、材料、工艺、软件、渠道、参数 | `RoboWiki` 仓 `data/` |
| 改字段口径、schema | `RoboWiki` 仓 `schema/` |
| 加产品图 | `RoboWiki` 仓 `assets/parts/` |
| 改页面文案、导航、样式、组件 | 本仓 `apps/web/` |
| 改 API / 提案审核 / outbox worker | 本仓 `backend/` |
| 改投稿或数据入口 | 本仓 `apps/web/src/pages/submit.astro`、数据仓 Issue 模板 |
| 改部署 / 1Panel 反代 / Compose | 本仓 `deploy/` |
| 改多端契约 / QQ 机器人 | 本仓 `clients/` |
| 导入竞赛文档 | 本仓 `tools/site/` |

**不要手改生成物**：`apps/web/src/data/*.json`、`apps/web/public/{parts,share,docs}/`
都由 `pipeline build` 生成，下次构建会覆盖。

## 数据版本

本仓通过 `data.lock.json` 锁定`RoboWiki` 仓的 `data-v*` 发布物；Pages 构建会下载 release、
校验 SHA-256 后生成页面。数据更新流程：

1. `RoboWiki` 仓改数据 → 跑 `python -m pipeline validate` → 发 `data-v*` release；
2. 本仓更新 `data.lock.json` 的版本、asset 名、`sha256`、`manifest_sha256` 与 counts；
3. 本地 `fetch-data-release.sh` + `pipeline build` + `pytest`；
4. 提 PR → CI 会重新下载新 release 构建。

## 三条底线

1. 不把数据副本提交回本仓；
2. 不改生成物；
3. 数据问题去`RoboWiki` 仓，页面/API/部署问题留本仓；C 级线索不会进站点目录，但可在`RoboWiki` 仓保留并注明来源。

# 前端：Astro 根站 + Taro 互动端

这是唯一前端形态。VitePress、独立 console、原生小程序壳已在 2026-11-05 收口时删除。

## 产物

| 产物 | 来源 | 发布位置 |
|---|---|---|
| Astro 根站 | `apps/web` | `https://robowiki.org.cn/` |
| Taro H5 | `apps/app`（`build:h5`） | `/app/` |
| Taro 微信小程序 | `apps/app`（`build:weapp`） | 微信后台，AppID `wx13bffd77b0b597e2` |

GitHub Pages 的 CI 只上传两份产物：`apps/web/dist` 作为根，`apps/app/dist/h5` 放进 `/app/`。

## 数据流

```text
RoboWiki 仓 data-v* release
        │  scripts/fetch-data-release.sh → .data/
        ▼
python -m pipeline build
        ├─ build_site：生成 JSON、分享卡、产品图到 apps/web/public
        └─ web_export：JSON 复制到 apps/web/src/data
        ▼
Astro 构建（构建期直接 import JSON）
```

`apps/web/src/data/*.json`、`apps/web/public/{parts,share,docs}/*` 是生成物，不入库；不要手改。

## 页面边界

- Astro：全部公开内容、SEO、canonical/OG/JSON-LD、sitemap、PWA 外壳、每页评论区。
- React 岛（仅在 Astro 内）：社区流、帖子、用户页、排行榜、站务后台、登录跳板。
- Taro：移动端登录/注册、完整账号、评分、讨论、通知、投稿纠错、媒体上传。
- 写操作只落在 FastAPI `/api/v1`；没有第二个写域。

## URL 约定

- 页面统一 `.html`，保留旧站深链：`/catalog.html`、`/parts/<category>/<slug>.html`、`/materials/<slug>.html`、`/learn/<slug>.html`。
- 部件页使用目录数据的 `slug`，不是 `id`。
- 品类页：`/parts/<category>.html`；旧入口 `/parts/<category>/` 由静态跳转页兜底。
- 动态社区内容用查询参数：`/post.html?id=`、`/u.html?handle=`；静态托管无法为任意 id 生成文件。
- 旧 `/console/*` 由 API 308 跳到 `/community.html`、`/post.html` 或 `/admin.html`。

## 本地运行

```bash
bash scripts/fetch-data-release.sh
export ROBOWIKI_DATA_DIR="$PWD/.data/data"
export ROBOWIKI_SCHEMA_DIR="$PWD/.data/schema"
export ROBOWIKI_ASSETS_DIR="$PWD/.data/assets/parts"
python -m pipeline build

pnpm install
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm dev:web
PUBLIC_API_BASE=http://127.0.0.1:8018/api/v1 pnpm --filter @robowiki/app dev:h5
```

Windows 下给 Taro 传 `APP_BASE=/app/` 时要加 `MSYS_NO_PATHCONV=1`；配置里也会拒绝被路径转换后的 `C:/...` 值。

## 微信小程序上传

前置条件（缺一不可）：

1. 微信开发者工具已安装并登录；
2. IDE → 设置 → 安全设置 → **服务端口开启**；
3. `apps/app` 已运行 `pnpm --filter @robowiki/app build:weapp`。

上传：

```bash
"D:/微信web开发者工具/cli.bat" upload \
  --project "C:/Users/31560/Documents/00_open/RoboWiki/RoboWiki.github.io/apps/app" \
  -v 1.0.6 \
  -d "Astro/Taro 收口：账号、投稿纠错、评论配图"
```

版本号只在 CLI 参数里；`apps/app/project.config.json` 的 `appid` 不要改。
上传完成后到微信公众平台提交审核/发布；只上传不等于上线。

> 若 CLI 报 `IDE service port disabled`，先手动打开 IDE 的安全设置开启服务端口；CLI 不能代替这一步。

## 验证

```bash
pnpm --filter @robowiki/web build
pnpm --filter @robowiki/app typecheck
APP_BASE=/app/ pnpm --filter @robowiki/app build:h5
pnpm --filter @robowiki/app build:weapp
python -m pytest
```

线上抽查：`/`、`/catalog.html`、任一部件页、`/materials.html`、`/learn/index.html`、`/community.html`、`/admin.html`、`/app/`；旧 `/console/*` 应 308；`/next/` 应 404。

# 部署：静态站 + 数据仓 Issue

RoboWiki 现在只有一个生产形态：

```text
浏览器
  │
  ▼
1Panel OpenResty（TLS / 静态反代 / 安全头）
  │
  ▼
GitHub Pages（Astro 静态站）
  │
  └─ 目录数据：RoboWiki 仓的 data-v* release
     评分/实测：RoboWiki 仓 GitHub Issue（构建时聚合）
```

服务器不再运行 API、worker、PostgreSQL、Redis 或 Taro 小程序。
`/api`、`/mcp`、`/console` 不再存在；旧地址由 1Panel 返回 404 即可。

## 1Panel

- `1panel-proxy-root.conf`：把 `/` 反代到 `https://robowiki.github.io`。
- `1panel-site.conf`：TLS、ACME、安全头与静态反代模板；不含 API location。
- 修改后执行 `nginx -t` 再 reload。

## 发布

1. 数据仓改动 → `data-v*` release。
2. 站点仓更新 `data.lock.json` → push main → Pages 自动构建。
3. Issue 评分/实测在 Pages 构建时从 `RoboWiki/RoboWiki` 拉取，不写数据库。
4. 服务器只需保留 1Panel 反代，不再执行 `deploy-server.sh` 或数据容器更新。

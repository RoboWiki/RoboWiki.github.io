# 微信小程序（只读）

原生微信小程序壳：查部件、查材质/工艺、看来源与数据版本，支持转发。**不登录、不写入、不做 UGC**。

## 页面

| 页面 | 能力 |
|---|---|
| `pages/index` | 部件/材质切换、关键词搜索、列表 |
| `pages/part` | 部件参数、来源、核对日期、分享 |
| `pages/materials` | 36 条材料/工艺列表 |
| `pages/material` | 材料/工艺参数、适用场景、来源、分享 |

数据来自同一套 `/api/v1`：
- `GET /parts?q=&limit=`
- `GET /parts/{id}`
- `GET /materials?q=&limit=`
- `GET /materials/{id}`
- `GET /meta`（版本号）

材质/工艺当前全部 B 级典型值；页面会明确标注，不显示成认证参数。

## 运行

1. 微信开发者工具 → 导入 `clients/wechat-mini`。
2. `project.config.json` 里 `appid` 换成自己的小程序 AppID（当前 `touristappid` 只能本地预览）。
3. 修改 `config.js` 的 `API` / `SITE` 为已备案 HTTPS 域名；开发时可在「详情 → 本地设置」勾选不校验合法域名。
4. 小程序后台把 `https://<域名>` 配到 request 合法域名；生产必须有 ICP 备案。

## 审核与边界

- 只读目录可选「工具 / 信息查询」类目；不做社区、评论、登录，避免内容安全与隐私弹窗。
- 分享用 `onShareAppMessage`，标题带型号、路径指向详情；小程序码由平台生成。
- QQ 用户：可以在微信里打开/转发小程序；QQ 客户端本身不原生运行微信小程序。QQ 群场景用
  `clients/qqbot/` 的只读问答，Web/PWA 链接也可直接发群。
- 没有后端时页面显示错误态；GitHub Pages 的静态镜像不提供 `/api/v1`。

## 验证

本目录没有构建步骤；本次只做了 JSON 解析、JS 语法检查与 API 契约核对，未在真实微信开发者工具/真机审核环境运行。
上线前需在开发者工具预览、真机调试，并完成类目与备案。

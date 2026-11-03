# 微信小程序（只读目录）

原生微信小程序：查部件、查材料/工艺、看参数来源与数据版本，支持转发。**不登录、不写入、不做 UGC**。

AppID：`wx13bffd77b0b597e2`。当前是只读工具型小程序，建议类目「工具 → 信息查询」。

## 页面

| 页面 | 能力 |
|---|---|
| `pages/index` | 部件/材质切换、关键词搜索、品类筛选、分页、下拉刷新 |
| `pages/part` | 图片、参数、派生量、评价、优惠、来源、复制网页链接、分享 |
| `pages/materials` | 材料/工艺列表、类型筛选、搜索、分页 |
| `pages/material` | 参数、适用场景、相关材料/工艺、来源、分享 |

数据只来自同一套 `/api/v1`，不复制后端逻辑：

- `GET /parts?q=&category=&limit=&offset=&compact=true`（列表轻量投影）
- `GET /parts/{id}?posts_kind=review&posts_limit=5`（详情只取评价）
- `GET /materials?q=&category=&limit=&offset=`
- `GET /materials/{id}`
- `GET /meta`、`GET /catalog`（版本与品类）

A 级 = 逐项核对官方资料；B 级 = 公开资料汇编，购买/设计前请回原来源核对；缺失写「—」，不推断。

## 运行

1. 微信开发者工具 → 导入本目录；`project.config.json` 已写入 AppID。
2. **开发版**默认连本机 Docker API `http://127.0.0.1:8080/api/v1`（见 `config.js`）。
   - 本机 Docker：`cd deploy && docker compose up -d`（API 由 Caddy 暴露在 8080）。
   - 开发者工具「详情 → 本地设置」勾选「不校验合法域名」；也可在本目录新建
     `project.private.config.json` 写入 `{"setting":{"urlCheck":false}}`（已被 gitignore，
     新克隆不会自带）。
   - 真机预览开发版时，把 `config.js` 的 `LOCAL` 改成电脑局域网地址。
3. **体验版 / 正式版**自动使用 `https://robowiki.org/api/v1`。上线前必须：
   - 该域名完成 ICP 备案并部署 Caddy/API（当前 `robowiki.org` 还未接管站点与 API，不能直接提审）；
   - 小程序后台把 `https://robowiki.org` 配到 request 合法域名；
   - 确认 HTTPS 证书有效。
4. 预览/上传也可用官方 `miniprogram-ci`（需要上传密钥与 IP 白名单）。

## 真机/工具验证

```bash
# 只看编译与包大小，不需要自动化端口
"D:/微信web开发者工具/cli.bat" preview \
  --project "C:/Users/31560/Documents/00_open/robowiki/clients/wechat-mini" \
  --qr-output "preview-qr.png"

# 可选：官方 miniprogram-automator（需先开启服务端口并启动 auto）
"D:/微信web开发者工具/cli.bat" auto \
  --project "C:/Users/31560/Documents/00_open/robowiki/clients/wechat-mini" \
  --auto-port 9420 --trust-project
cd tests && npm i
WECHAT_WS=ws://127.0.0.1:9420 npm test
```

说明：DevTools `1.06.2405020` + automator `0.13.0` 在 Windows 上实测
`App.getCurrentPage` 协议无响应（`Tool.getInfo` 正常）；这属于工具链问题，不是页面代码。
当前以 `cli preview` 编译通过 + 模拟器人工走查为准，脚本保留供工具修复后回归。

## 参考与取舍

- [官方 miniprogram-automator](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/automator.html)：页面级自动化；本目录 `tests/smoke.js` 采用官方 SDK，不手写驱动。
- [官方性能建议](https://developers.weixin.qq.com/miniprogram/dev/framework/performance/tips.html)：首屏少请求、`setData` 只传差异；列表已改为 20 条/页 + 增量 `setData`。
- [官方分包](https://developers.weixin.qq.com/miniprogram/dev/framework/subpackages/basic.html)：页面多了再拆，当前 4 页无需分包。
- [WeUI](https://github.com/Tencent/weui-wxss)：空态/加载/错误态的微信原生语义参考；本项目保持零 npm 依赖，只用原生 WXML/WXSS。
- [TDesign Miniprogram](https://github.com/Tencent/tdesign-miniprogram)、[Vant Weapp](https://github.com/youzan/vant-weapp)：适合复杂电商/表单；只读目录不引入，避免包体与审核类目偏移。
- 内容/结构参考：[awesome-open-source-robots](https://github.com/stephane-caron/awesome-open-source-robots)、[awesome-robotics](https://github.com/kiloreux/awesome-robotics)、[list_of_robot_electronics](https://github.com/cajt/list_of_robot_electronics)；只学分类与许可标注方式，不复制内容。

## 审核与边界

- 只读目录选「工具 / 信息查询」；不做社区、评论、登录，避免内容安全与隐私弹窗。
- 分享用 `onShareAppMessage` + `onShareTimeline`；标题带型号，路径带详情 id。
- QQ 用户可在微信里打开/转发；QQ 客户端不原生运行微信小程序。QQ 群场景用 `clients/qqbot/` 或 Web 链接。
- 没有后端时页面显示错误态与「重试 / 回目录」；GitHub Pages 静态镜像不提供 `/api/v1`。

## 验证记录

- `cli preview`：编译成功，主包约 48 KB（2026-11-03）。
- 模拟器：首页 326 件部件、36 材料/工艺，品类筛选、搜索、详情、材质页均能加载。
- 自动化：`miniprogram-automator` 连接成功但 `App.getCurrentPage` 超时，已在 README 记录为工具链限制。

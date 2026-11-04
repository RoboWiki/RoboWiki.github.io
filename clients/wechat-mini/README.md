# 微信小程序（只读目录）

原生微信小程序：查部件、查材料/工艺、看参数、评分、来源与数据版本，支持单条转发。**不登录、不写入、不做 UGC**。

AppID：`wx13bffd77b0b597e2`。当前是只读工具型小程序，建议类目「工具 → 信息查询」。

## 页面

| 页面 | 能力 |
|---|---|
| `pages/index` | 部件/材质切换、搜索、品类/子类/分组筛选、价格与材料排序、分页、下拉刷新、骨架屏、空态重置、单条分享、离线回退、朋友圈预览提示 |
| `pages/part` | 首屏标题/价格/等级/关键参数、图片、完整参数（含 `params` / `price_tiers` 结构化值）、派生量、真实评分分布、评价、优惠与免责声明、来源、复制网页链接、分享 |
| `pages/material` | 参数、适用场景、供货形态、优缺点、渠道与价格、相关条目、来源、分享、朋友圈预览提示 |

数据只来自同一套 `/api/v1`，不复制后端逻辑：

- `GET /parts?q=&category=&sort=&order=&limit=&offset=&compact=true`
- `GET /parts/{id}?posts_kind=review&posts_limit=5`
- `GET /ratings/{part_id}`（评分分布；未评分返回 `count=0`，不显示 0 分）
- `GET /materials?q=&category=&group=&limit=`
- `GET /materials/{id}`
- `GET /meta`、`GET /materials/meta`、`GET /catalog`（版本、品类、材质分组）

A 级 = 逐项核对官方资料；B 级 = 公开资料汇编，购买/设计前请回原来源核对；缺失写「—」，不推断。

## 运行

1. 微信开发者工具 → 导入本目录；`project.config.json` 已写入 AppID。
2. **开发版**默认连本机 Docker API `http://127.0.0.1:8080/api/v1`（见 `config.js`）。
   - 本机 Docker：在 `deploy/` 放 `.env`，至少设置
     `SECRET_KEY=<32 字节以上>`、`POSTGRES_PASSWORD=...`、`ADMIN_PASSWORD=...`，
     然后 `docker compose up -d --build`。API 默认只绑 `127.0.0.1:8080`。
   - 开发者工具「详情 → 本地设置」勾选「不校验合法域名」；也可在本目录新建
     `project.private.config.json` 写入 `{"setting":{"urlCheck":false}}`（已被 gitignore，
     新克隆不会自带）。
   - 真机调试开发版时，把 `config.js` 的 `LOCAL` 改成电脑局域网地址，
     例如 `http://192.168.1.5:8080`；手机与电脑需同一网段。
3. **体验版 / 正式版**使用 `https://robowiki.org.cn/api/v1`。上线前必须：
   - 主域已完成 ICP 备案，并按 `deploy/README.md` 第 3 节把 `/api/`、`/mcp/`、`/console/`
     反代到本机 API（公网 `/api/v1/ready` 应返回 JSON）；
   - 小程序后台把 `https://robowiki.org.cn` 配到 request 合法域名；
   - 确认 HTTPS 证书有效。
4. 预览/上传也可用官方 `miniprogram-ci`（需要上传密钥与 IP 白名单）。

## 检查与工具验证

```bash
# 1) 零依赖静态检查：JS 语法、JSON、WXML 闭合、AppID 形态
cd tests && node check.js

# 2) 只看编译与包大小（路径可用环境变量，不写死个人目录）
WECHAT_CLI="D:/微信web开发者工具/cli.bat" \
MINI_PROJECT="$PWD/.." \
"D:/微信web开发者工具/cli.bat" preview \
  --project "$PWD/.." --qr-output "preview-qr.png"

# 3) 可选：官方 miniprogram-automator（需先开启服务端口并启动 auto）
WECHAT_CLI="D:/微信web开发者工具/cli.bat" \
WECHAT_WS=ws://127.0.0.1:9420 npm test
```

说明：DevTools `1.06.2405020` + automator `0.13.0` 在 Windows 上实测
`App.getCurrentPage` 协议无响应（`Tool.getInfo` 正常）；这属于工具链问题，不是页面代码。
当前以 `cli preview` 编译通过 + 模拟器人工走查为准，脚本保留供工具修复后回归。

## 分享与传播

- 列表页「分享当前筛选」会把 `tab/q/category/group/sort` 带进 path。
- 每条卡片有「分享这一条」，直接发部件/材质详情给好友或群。
- 详情页 `onShareAppMessage` / `onShareTimeline` 标题带型号，`onShareTimeline` 用 `query` 带回当前页。
- 复制链接优先用静态分享 JSON 的 `canonical_url`；取不到时用 API 返回的 `web_path`。

## 参考与取舍

- [官方 miniprogram-automator](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/automator.html)：页面级自动化；本目录 `tests/smoke.js` 采用官方 SDK，不手写驱动。
- [官方性能建议](https://developers.weixin.qq.com/miniprogram/dev/framework/performance/tips.html)：首屏少请求、`setData` 只传差异；列表 20 条/页 + 增量 `setData`，材质 36 条一次取。
- [官方图片懒加载](https://developers.weixin.qq.com/miniprogram/dev/component/image.html)：列表缩略图已开 `lazy-load`。
- [官方朋友圈分享](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/share-timeline.html)：单页模式只传 `query`，不做自定义页面路径。
- [WeUI](https://github.com/Tencent/weui-wxss)：空态/加载/错误态的微信原生语义参考；本项目保持零 npm 依赖，只用原生 WXML/WXSS。
- 本地参考克隆（仅学习模式，不进本仓）：`_refs/vant-weapp`、`_refs/tdesign-miniprogram`、`_refs/mini-github`、`_refs/weui-wxss`、`_refs/iview-weapp`；采纳了 empty/skeleton 解剖、check-tag 筛选、repo-item 元信息行，不引入整个组件库。
- [TDesign Miniprogram](https://github.com/Tencent/tdesign-miniprogram)、[Vant Weapp](https://github.com/youzan/vant-weapp)：适合复杂电商/表单；只读目录不引入，避免包体与审核类目偏移。
- 内容/结构参考：[awesome-open-source-robots](https://github.com/stephane-caron/awesome-open-source-robots)、[awesome-robotics](https://github.com/kiloreux/awesome-robotics)、[list_of_robot_electronics](https://github.com/cajt/list_of_robot_electronics)；只学分类与许可标注方式，不复制内容。

## 审核与边界

- 只读目录选「工具 / 信息查询」；不做社区、评论、登录，避免内容安全与隐私弹窗。
- 评分只读展示；写入评价/评分仍在网页端，不放进小程序。
- QQ 用户可在微信里打开/转发；QQ 客户端不原生运行微信小程序。QQ 群场景用 `clients/qqbot/` 或 Web 链接。
- 接口不通时优先展示上次成功数据并标注日期；仍不通显示「重试 / 回目录」。GitHub Pages 静态镜像不提供 `/api/v1`。

## 验证记录

- 2026-11-04：体验版/正式版切到 `https://robowiki.org.cn`；`cli preview` 编译成功，主包 **59.8 KB**；`cli upload -v 1.0.1` 上传成功。
- 生产 API 逐项验收：`/meta`、`/materials/meta`、`/catalog`、`/parts?compact=true`、`/parts/{id}`、`/ratings/{id}`、`/materials`、`/materials/{id}` 均 200；目录 326 件、材料/工艺 36 条；产品图与分享 JSON 均 200。
- 静态检查：`node check.js` 通过（11 JS / 9 JSON / 3 WXML）。
- 模拟器：首页 326 件部件、36 材料/工艺；品类/子类/价格/材料排序、关键参数、评分标签、详情结构化参数、材质优缺点/渠道均已加载。
- 自动化：`miniprogram-automator` 连接成功但 `App.getCurrentPage` 超时，已在 README 记录为工具链限制。

# 微信小程序（读 + 登录 / 评分 / 讨论）

原生微信小程序：查部件、查材料/工艺、看参数、来源与数据版本，支持单条转发。
目录与材质保持只读；部件详情登录后可提交 1–5 分、标记「装过机 / 用过」、写备注，
并在同一页参与讨论（可回复）。

AppID：`wx13bffd77b0b597e2`。当前类目按「工具 → 信息查询」；出现用户可见的
评分与讨论后，审核会按 UGC 要求补看社区类目与内容安全，见下文。

## 页面

| 页面 | 能力 |
|---|---|
| `pages/index` | 部件/材质切换、搜索、品类/子类/分组筛选、价格与材料排序、部件分页、下拉刷新、骨架屏、空态重置、单条分享、离线回退、朋友圈预览提示 |
| `pages/part` | 首屏标题/价格/等级/关键参数、图片、完整参数（含 `params` / `price_tiers` 结构化值）、派生量、真实评分分布、微信登录/退出、提交或修改评分、讨论与回复、评价、优惠与免责声明、来源、复制网页链接、分享 |
| `pages/material` | 参数、适用场景、供货形态、优缺点、渠道与价格、相关条目、来源、分享、朋友圈预览提示（只读） |

数据只来自同一套 `/api/v1`，不复制后端逻辑：

- `GET /parts?q=&category=&sort=&order=&limit=&offset=&compact=true`
- `GET /parts/{id}?posts_kind=review&posts_limit=5`
- `GET /ratings/{part_id}`（评分分布；未评分返回 `count=0`，不显示 0 分）
- `POST /ratings/{part_id}`（登录；`score` 1–5、`own_hardware`、`note` ≤200 字；同一人同一件 upsert，改分不重复计票）
- `GET /wiki/comments?page=parts/{category}/{slug}&limit=200`
- `POST /wiki/comments`（登录；`page`、`body` 1–4000 字、`parent_id` 可回复）
- `POST /auth/wechat/mini`、`POST /auth/refresh`、`POST /auth/logout`
- `GET /materials?q=&category=&group=&limit=`
- `GET /materials/{id}`
- `GET /meta`、`GET /materials/meta`、`GET /catalog`（版本、品类、材质分组）

A 级 = 逐项核对官方资料；B 级 = 公开资料汇编，购买/设计前请回原来源核对；缺失写「—」，不推断。

## 登录、评分与讨论

### 登录

1. 用户点「微信登录」或首次提交评分/讨论时，客户端调 `wx.login()` 拿一次性 `code`。
2. `POST /auth/wechat/mini { code }`；服务端用 AppSecret 调 `jscode2session`，
   建号或找到同 openid 的账号，返回 `access_token` + `refresh_token` + `user`。
3. 客户端只把这三个值写进 `wx.setStorageSync`：
   - `robowiki.access_token`
   - `robowiki.refresh_token`
   - `robowiki.user`

客户端不保存 `session_key`、openid 原文或任何应用密钥；「退出」会撤销当前
refresh 会话链并清本机（没有 refresh 时不调 `/auth/logout`，避免把网页端一起登出）。

`utils/api.js` 统一带 `Authorization: Bearer <access_token>`：
- 任意请求收到 401 → 用 refresh 换一对新 token → 原请求只重放一次；
- 失败（refresh 被撤销 / 过期 / 复用）→ 清空本机会话，提示「登录已过期，请重新登录」；
- 并发 401 共用同一次 refresh。后端 refresh 是一次性轮换，各刷一次会触发
  复用检测并撤销整条会话链；
- 断网等网络错误不清 token，恢复网络后还能继续。

### 评分

- 1–5 分必选；`own_hardware` 表示实际装机/用过；备注 ≤200 字。
- 同一人同一件由后端唯一约束保证只有一条：再提交就是改分，幂等。
- 分数、分布、装机人数、`mine` 都来自服务端聚合；未评分不显示 0 分。

### 讨论

- 页面标识与网页 `PageComments` 同规则：`web_path` 去掉前导 `/` 与 `.html`，
  即 `parts/actuator/cubemars-ak80-6`。小程序与网页看到的是同一串讨论。
- 一次取回整页线程（上限 200），按 `parent_id` 组树，最多缩进 3 层。
- 回复只带 `parent_id`；跨页回复由服务端拒绝。
- 讨论 GET 失败时只降级这一块为只读（显示原因），不影响部件详情、评分与分享。

## 内容安全

- **应用密钥和微信会话密钥只放服务端**：小程序包是公开的，仓库里也没有
  `WECHAT_MP_SECRET`；`tests/check.js` 会扫描客户端源码，出现密钥/会话字段直接失败。
- 客户端不做敏感词判定，也不调用微信内容安全接口；`msgSecCheck` 由服务端负责。
  服务端拒绝时返回的 `detail` 会原样显示，用户改完再发。
- 评分备注与讨论正文在客户端先做长度/空值校验，服务端仍会再校验一次。
- 举报/删除沿用站内账号与后台审核；小程序不新增独立的审核入口。

## 运行

1. 微信开发者工具 → 导入本目录；`project.config.json` 已写入 AppID。
2. **环境映射固定在 `config.js`**，不按「非正式版」猜：

   | `miniProgram.envVersion` | API / SITE |
   |---|---|
   | `develop` | `http://127.0.0.1:8080`（`LOCAL`） |
   | `trial` | `https://robowiki.org.cn`（`PROD`） |
   | `release` | `https://robowiki.org.cn`（`PROD`） |

   体验版必须打主域，否则审核/真机预览会连到 127.0.0.1。`tests/check.js` 直接断言
   `baseFor('develop'|'trial'|'release')`，改错映射会先在这里失败。

   - 本机 Docker：在 `deploy/` 放 `.env`，至少设置
     `SECRET_KEY=<32 字节以上>`、`POSTGRES_PASSWORD=...`、`ADMIN_PASSWORD=...`，
     然后 `docker compose up -d --build`。API 默认只绑 `127.0.0.1:8080`。
   - 要联调登录，在 `.env` 再填 `WECHAT_MP_APPID` / `WECHAT_MP_SECRET`
     （Compose 映射为 `ROBOWIKI_WECHAT_MP_*`，只注入 API 容器）。两项都填后
     `GET /auth/providers` 返回 `wechat_mini:true`；未配置时登录接口返回 503，
     小程序会提示「小程序登录暂未开通」，只读功能不受影响。
   - 开发者工具「详情 → 本地设置」勾选「不校验合法域名」；也可在本目录新建
     `project.private.config.json` 写入 `{"setting":{"urlCheck":false}}`（已被 gitignore，
     新克隆不会自带）。
   - 真机调试开发版时，把 `config.js` 的 `LOCAL` 改成电脑局域网地址，
     例如 `http://192.168.1.5:8080`；手机与电脑需同一网段。
3. **体验版 / 正式版**使用 `https://robowiki.org.cn/api/v1`。上线前必须：
   - 主域已完成 ICP 备案，并按 `deploy/README.md` 第 3 节把 `/api/`、`/mcp/`、`/console/`
     反代到本机 API（公网 `/api/v1/ready` 应返回 JSON）；
   - 小程序后台把 `https://robowiki.org.cn` 配到 **request 合法域名**
     （登录、评分、讨论都走这一个域，没有 uploadFile/downloadFile 域名需求）；
   - 确认 HTTPS 证书有效；`/auth/wechat/mini` 能从公网访问（503 说明服务端没配微信密钥）。
4. 预览/上传也可用官方 `miniprogram-ci`（需要上传密钥与 IP 白名单）。

## 检查与工具验证

```bash
# 1) 零依赖检查：JS 语法、JSON、WXML 闭合、AppID 形态、环境映射、
#    Bearer/refresh/401 单次重试（假 wx 走真实 api.js）、源码密钥扫描
cd tests && node check.js

# 2) 只看编译与包大小（路径可用环境变量，不写死个人目录）
WECHAT_CLI="D:/微信web开发者工具/cli.bat" \
MINI_PROJECT="$PWD/.." \
"D:/微信web开发者工具/cli.bat" preview \
  --project "$PWD/.." --qr-output "preview-qr.png"

# 3) 可选：官方 miniprogram-automator（需先开启服务端口并启动 auto）
WECHAT_CLI="D:/微信web开发者工具/cli.bat" \
WECHAT_WS=ws://127.0.0.1:9420 npm test

# 4) 重新生成 App / 多端共用的 OpenAPI 类型（不在小程序运行时里）
cd ../../.. && OPENAPI_FILE=/path/openapi.json bash scripts/generate-sdk.sh
```

说明：DevTools `1.06.2405020` + automator `0.13.0` 在 Windows 上实测
`App.getCurrentPage` 协议无响应（`Tool.getInfo` 正常）；这属于工具链问题，不是页面代码。
当前以 `cli preview` 编译通过 + 模拟器人工走查为准，脚本保留供工具修复后回归。

## 分享与传播

- 列表页「分享当前筛选」会把 `tab/q/category/subtype/group/msort/sort` 带进 path。
- 每条卡片有「分享这一条」，直接发部件/材质详情给好友或群。
- 详情页 `onShareAppMessage` / `onShareTimeline` 标题带型号与来源等级，`onShareTimeline` 用 `query` 带回当前页。
- 详情页「复制网页链接」先读 `/share/parts/{category}/{slug}.json`（或
  `/share/materials/{slug}.json`）的 `canonical_url`，读不到才退回 API 的 `web_path`；
  与网页 canonical / OG 是同一个 URL。
- 分享 JSON 与网页共用：`title`、`summary`、`params`、`source_tier`、`verified`、
  `last_checked`、`data_version`、`canonical_url`、`copy_text`。客户端只渲染，不另拼文案。
- 从分享链接直接打开详情时，数据版本优先取详情响应的 `data_version`，不再依赖首页缓存。

## 分页与空态

- 部件列表 20 条/页，触底增量追加（带请求序号，旧响应不会覆盖新筛选）。
- 材质/工艺一次取 200 条（API 单页上限），密度/模量/抗拉排序覆盖全量；
  超过 200 条时列表底部明示「只列出前 N 条」，不把局部排序说成全局排序。
- 空结果给「重置筛选」；接口失败且有缓存时显示上次成功数据与日期，无缓存时给「重试 / 重置」。

## 参考与取舍

- [官方 miniprogram-automator](https://developers.weixin.qq.com/miniprogram/dev/devtools/auto/automator.html)：页面级自动化；本目录 `tests/smoke.js` 采用官方 SDK，不手写驱动。
- [官方性能建议](https://developers.weixin.qq.com/miniprogram/dev/framework/performance/tips.html)：首屏少请求、`setData` 只传差异；列表 20 条/页 + 增量 `setData`，材质一次取（上限 200）。
- [官方图片懒加载](https://developers.weixin.qq.com/miniprogram/dev/component/image.html)：列表缩略图已开 `lazy-load`。
- [官方朋友圈分享](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/share-timeline.html)：单页模式只传 `query`，不做自定义页面路径。
- [WeUI](https://github.com/Tencent/weui-wxss)：空态/加载/错误态的微信原生语义参考；本项目保持零 npm 依赖，只用原生 WXML/WXSS。
- 本地参考克隆（仅学习模式，不进本仓）：`_refs/vant-weapp`、`_refs/tdesign-miniprogram`、`_refs/mini-github`、`_refs/weui-wxss`、`_refs/iview-weapp`；采纳了 empty/skeleton 解剖、check-tag 筛选、repo-item 元信息行，不引入整个组件库。
- [TDesign Miniprogram](https://github.com/Tencent/tdesign-miniprogram)、[Vant Weapp](https://github.com/youzan/vant-weapp)：适合复杂电商/表单；小程序仍保持零 npm 依赖，评分与讨论用原生 `switch` / `textarea`，避免包体与组件库维护面。
- 内容/结构参考：[awesome-open-source-robots](https://github.com/stephane-caron/awesome-open-source-robots)、[awesome-robotics](https://github.com/kiloreux/awesome-robotics)、[list_of_robot_electronics](https://github.com/cajt/list_of_robot_electronics)；只学分类与许可标注方式，不复制内容。

## 审核与边界

- 目录与材质仍按「工具 / 信息查询」；部件详情的评分与讨论属于 UGC，
  提交审核时需要按小程序后台要求补齐社区类目，并说明内容安全由服务端
  `msgSecCheck` + 人工审核兜底。类目/资质以提交时后台实际要求为准。
- 登录只拿 openid 建站内账号，不弹头像昵称授权；隐私说明里应写明
  「微信登录标识用于账号与发言归属」。
- 评分与讨论写入小程序；网页端、小程序共用 `users` / `ratings` / `wiki_comments`，
  不各自维护一份。
- QQ 用户可在微信里打开/转发；QQ 客户端不原生运行微信小程序。QQ 群场景用 `clients/qqbot/` 或 Web 链接。
- 接口不通时优先展示上次成功数据并标注日期；仍不通显示「重试 / 回目录」。
  讨论接口单独失败只把讨论降级为只读，不拖垮详情页。GitHub Pages 静态镜像不提供 `/api/v1`。

## 验证记录

- 2026-11-05：`1.0.5` 增加微信登录、站内评分、评论/回复、refresh 自动续期；主包 **84.9 KB**，`cli upload` 成功。

- 2026-11-05：P1 写入：`utils/api.js` 支持 GET/POST/DELETE、Bearer、refresh 轮换与
  401 单次重放（并发共用一次 refresh）；新增 `utils/auth.js`（`wx.login` → `/auth/wechat/mini`，
  只存 access/refresh/user）；部件详情支持 1–5 分 + `own_hardware` + 200 字备注
  （改分幂等）与 `/wiki/comments` 讨论/回复，讨论接口失败保持只读。新增
  `scripts/generate-sdk.sh` 与 `clients/sdk/api.d.ts`（类型-only）。`node check.js` 通过
  （12 JS / 9 JSON / 3 WXML，含 Bearer/refresh 与 wx.login 行为测试、源码密钥扫描）；
  `cli preview` 编译通过，主包 **84.9 KB**。
- 2026-11-05：`1.0.4` 合并 `data-v2026.11.3`（开源硬件品类、模块电源分组、材质模量口径）；主包 **61.7 KB**，`cli preview` / `cli upload` 成功。
- 2026-11-05：`1.0.3` 收录选型/分享修复（分页、子类筛选、分享卡、材质分享、复制 canonical）；主包 **61.6 KB**，`cli preview` / `cli upload` 成功。
- 2026-11-05：`config.js` 抽出 `baseFor(env)`，`node check.js` 断言 develop→LOCAL、
  trial/release→PROD；详情页复制链接改读分享 JSON 的 `canonical_url`；材质排序改为
  单次取满 200 条并加截断提示；从材质分享链接切回部件时补拉 `/catalog`；修复
  `smoke.js` 在部件详情页调用 `switchTab` 的路径错误。静态检查 11 JS / 9 JSON / 3 WXML 通过。
- 2026-11-04：体验版/正式版切到 `https://robowiki.org.cn`；`1.0.1` 首次上传。
- 2026-11-04：`1.0.2` 修复材质页把 `image_url/doc_url` 当参数行、`doc_url` 改为来源链接、供应商列表改用稳定 `wx:key`；主包 **60.2 KB**，`cli preview` / `cli upload` 均成功。
- 生产 API 逐项验收：`/meta`、`/materials/meta`、`/catalog`、`/parts?compact=true`、`/parts/{id}`、`/ratings/{id}`、`/materials`、`/materials/{id}` 均 200；目录 338 件、材料/工艺 36 条；产品图与分享 JSON 均 200。
- 模拟器：首页 338 件部件、36 材料/工艺；品类/子类/价格/材料排序、关键参数、评分标签、详情结构化参数、材质优缺点/渠道均已加载。
- 自动化：`miniprogram-automator` 连接成功但 `App.getCurrentPage` 超时，已在 README 记录为工具链限制。

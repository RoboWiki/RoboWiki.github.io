# Dichen33 工作留痕

记录我在 RoboWiki 仓库做过的修改与验证，按时间倒序。时间均为本机时区（UTC+8）。

> 2026-11-09 重建本文件，继续记录重构后（Astro/Taro）的工作。
> 2026-11-08 及更早的记录见 `docs/archive/WORKLOG-Dichen33.md`；归档只读，不再追加。

## 2026-11-11

| 时间 | 类型 | 分支 / 提交 | 修改内容 | 验证 |
|---|---|---|---|---|
| 22:02 | 重构 / 主题 | 站点 ccc 5deac04 | 接受 main 的 `data-theme` 主题架构：ccc 合并 `origin/main`（e97cc2b），移除 `data-rw-style` A/B 轴与 `style-themes.css`；把原 test 风格重新表达为 main 口径的两个网页专属模式「test 浅色 / test 深色」——`tokens.css` 新增 `[data-theme=test]` / `.dark[data-theme=test-dark]` 全套语义色 + 抬字号令牌（`--text-*` 与 `--rw-text-*` 双写）+ Trebuchet/Cascadia 字体，`global.css` 加坐标纸底纹，`Base.astro` 菜单/boot 与 `404.astro` boot 白名单同步加 test/test-dark；既有暖纸/深色/iOS 浅深四模式与小程序令牌不动 | Astro 生产构建 700 页通过（Node 24，6.2s）；计算样式探针确认 test 浅=青碧 `#0e7a6d`/暖纸 `#f5f1e8`、test 深=薄荷 `#45d6b8`/`#14120d`，`text-sm` 15px、`base` 17px、h1 32/40px（`--text-*` 覆盖确实抬升 utility），坐标纸底纹生效；test 深禁用过渡后 0 处露浅底；暖纸/深色/iOS 浅深四模式色值/字号/字体均无变化；`rw-theme` 持久化并经首页/部件库/部件详情/方案详情刷新回归；对比度 AA（浅 ink 13.4 / primary 4.63、深 ink 15.2 / primary 10.3）；SitePet 看板娘挂载；控制台仅本地取生产 API 的 CORS。360px 页头右溢出与主题面板左溢出为 main 既有（暖纸同样 15px / -35px，test 面板 -34px 反优 1px），本次仅增第三行不改宽度 |
| 20:00 | 功能 / 展示 | 站点 ccc c354415 | 页头主题选择器合并为单一菜单：保留原版 / test 风格主题（`data-rw-style`，与配色正交、`rw-style` 独立持久化），并入上游跟随系统 / 暖纸 / 深色 / 高对比配色（`data-theme`）；部件详情改为全宽头卡（260px 图 + 信息 + 参数胶囊）+ 简介独立卡，新增 `Intro` 组件按句拆段限宽（部件 / 方案详情共用），适配上游暖纸默认与舒适字号，修复 ≤640px 主题面板向左溢出 | Astro 生产构建 700 页通过（Node 24，7.1s）；浏览器验证单一菜单含 2 风格卡 + 4 配色项，8 种组合均正确（原版×4 = 上游默认；test×暖纸 = 青碧 `#0e7a6d`、test×深色 = 薄荷 `#45d6b8`、原版×高对比 = `#000`/`#fff`），`rw-theme` / `rw-style` 独立记忆；部件详情头卡 1065px、4 参数胶囊、简介 2 段限宽 604px，方案简介 4 段无裸 markdown；360px 单列、侧栏 static、面板 fixed 铺满 12–333px 不溢出；控制台仅本地静态服务跨域取生产 API 的 CORS（非本次改动） |

## 2026-11-10

| 时间 | 类型 | 分支 / 提交 | 修改内容 | 验证 |
|---|---|---|---|---|
| 18:48 | 功能 / 导航 | 站点 ccc 979dba2 | 材料工艺库并入部件库：新增「常用加工材料」品类（27 种材料，按金属 / 工程塑料 / 3D 打印 / 复合材料 / 弹性体排序），卡片展示密度、模量、耐温与「适合：…」适用场景，点击进材料详情；材料模式下隐藏厂商、优惠、开源与排序等部件专用筛选，搜索覆盖材料名、别名与用途；撤回页头统计条第 4 格 | `tsc --noEmit` 仅原有 `catalog.ts` 报错；Astro 构建 699 页通过（Node 24）；4321 浏览器验证品类末位出现「常用加工材料 27」、27 张卡片等高 283px、搜索「碳纤维」筛出 4 种、切回关节电机恢复品牌筛选与对比按钮、卡片跳转 `/materials/alu-6061-t6.html`、无横向溢出 |
| 17:50 | 功能 / 展示 | 站点 ccc f5c485f | 页头账号入口改为按登录态显示：未登录显示「登录/注册」胶囊并指向 `/login.html`；登录后显示 36px 圆形头像并指向 `/account.html`，有 `avatar_url` 用图，无图用 `avatar_hue` 底色 + 首字，图片加载失败自动回退首字，昵称放在 `title` / `aria-label`。加载时用 `/auth/me` 校验，access 过期则用 refresh 轮换；只有后端明确拒绝 refresh 才清理令牌并回退，网络 / 5xx / 限流失败保留会话显示占位头像。`community-api` 在 `setTokens` / `clear` 时派发 `rw:auth`，站内登录、退出即时更新；页头与社区岛屿通过 `__rwCommunityAuth` / `__rwHeaderRefresh` 协调刷新，避免同一枚 refresh 被使用两次 | `tsc --noEmit` 仅原有 `catalog.ts` 报错；按 `data.lock.json`（data-v2026.11.10.8）下载并校验数据后，Astro 构建 699 页通过（Node 24）；浏览器验证未登录胶囊（86×36、蓝底、指向 `/login.html`）、登录后圆形头像（36×36、色底 + 首字、指向 `/account.html`、title 显示昵称）、自定义头像图覆盖色底、mock 验证刷新网络失败保留令牌、401 拒绝清令牌、轮换成功显示头像；截图核对页头布局无溢出 |

## 2026-11-09

| 时间 | 类型 | 分支 / 提交 | 修改内容 | 验证 |
|---|---|---|---|---|
| 22:11 | 修复 / 展示 | 站点 ccc bb85f55 | 部件详情评分区识别登录态（`localStorage['roboselect.token']`）：登录后不再显示「未登录或还没打分」提示和「登录后评分 / 评论」按钮；已评分用户仍显示「你已打分 N 分」，未登录用户维持原提示与入口 | `tsc --noEmit` 仅原有 `catalog.ts` 报错；Astro 构建 667 页通过（Node 24）；浏览器验证未登录（提示+按钮在）、已登录未评分（提示+按钮消失、评分表单在）、已登录已评分（显示「你已打分 5 分 · 基于自有硬件」）；临时测试账号与评分已清理，测试 token 已移除 |
| 22:00 | 功能 / 展示 | 站点 ccc 9437850 | 部件参数统一为中文标签 + 单位：补齐 165 个字段词表，布尔与口径枚举（peak/rated/rotor/output）中文化，数值保留 4 位有效数字，单位不重复拼接；详情页与对比页把 `doc_pdf` / `doc_url` / `repo_urls` 渲染成可跳转短链接；兼容舵机 `gear` 材质与相机 `absolute` 精度的同键异义 | `pnpm --filter @robowiki/app typecheck` 通过；Astro 构建 667 页通过（Node 24）；抽查 EL05、DM-D5730、D405、RDK X3、Feetech ST-3250 参数表；浏览器验证对比页 PDF/官网/仓库链接可跳转，枚举与单位归一 |
| 21:44 | 功能 / 展示 | 站点 ccc `0c5e43c`；数据仓 ccc_dt `14ed1d7`（同步） | 社区投票改为横向胶囊（赞同 / 净分 / 反对）：帖子与帖子详情统一放右下角，评论用紧凑版也放右下角，加载骨架同步；同时把 ccc 快进到 main 后叠加该提交，ccc_dt 快进到 main 并推送 | `tsc --noEmit` 仅原有 `catalog.ts` 报错；浏览器验证帖子/评论的赞同、反对、取消与深浅主题；`origin/ccc`、`origin/ccc_dt` 与本地差异均为 0/0 |

# UI 参考与设计审阅：账号 · 分享 · 目录

口径：star 与许可证取自 2026-11-05 的 GitHub API 与仓库 LICENSE 原文。本仓代码按 GPL-3.0
发布（`LICENSE`、`NOTICE.md`），所以先按许可证分档，再谈能借什么。审阅只针对 UI 与交互，
不含实现改动。

## 一、可参考的项目

| 项目 | 仓库 | Star | 许可证 | 可借鉴的点 | 用法 |
|---|---|---|---|---|---|
| Cal.com（社区版） | [`calcom/cal.diy`](https://github.com/calcom/cal.diy)（`cal.com` 已跳转至此） | 49,684 | MIT | `TextField` + `HintOrErrors` 的固定顺序：label → 控件 → hint → error；服务端错误按字段回填；账号设置按 Profile / Security / Appearance 分区，保存中有态、离开有脏值提示 | 可复制（保留 MIT 声明） |
| Outline | [`outline/outline`](https://github.com/outline/outline) | 41,168 | BSL 1.1 | 账号设置左栏分组；API key 列表：创建 → 只显示一次 → 命名/范围/过期 → 撤销 → 最后使用时间；危险操作单独成区 | 只学 IA 与文案 |
| Discourse | [`discourse/discourse`](https://github.com/discourse/discourse) | 48,047 | GPL-2.0（见下） | 分享面板分层：复制链接 / 带标题复制 / 邮件 / 社交渠道；移动端底部动作条；通知四级（Watching / Tracking / Normal / Muted）；未读标记 | 只学模式 |
| reka-ui | [`unovue/reka-ui`](https://github.com/unovue/reka-ui) | 6,924 | MIT | Tabs / Dialog / DropdownMenu / Tooltip 的 WAI-ARIA 接线；Dialog 自带焦点陷阱、Esc、滚动锁 | 可直接安装 |
| shadcn-vue | [`unovue/shadcn-vue`](https://github.com/unovue/shadcn-vue) | 10,779 | MIT | Form 的 VeeValidate + Zod 组合（与本站现用栈一致）、字段布局与错误呈现；皮肤走 CSS 变量 | 可直接取用 |
| Ant Design | [`ant-design/ant-design`](https://github.com/ant-design/ant-design) | 100,074 | MIT | Form 规则：`scrollToFirstError`、字段级 validateStatus/help、必填标记、提交 loading、message / notification 分级 | 借规则不借视觉 |
| Ant Design Vue | [`vueComponent/ant-design-vue`](https://github.com/vueComponent/ant-design-vue) | 21,702 | MIT | 同上，Vue 版 API；与 VeeValidate 二选一，不混用 | 同上 |
| QQ 分享组件 | [`connect.qq.com/widget/shareqq`](https://connect.qq.com/widget/shareqq/index.html) | — | 服务条款，非开源 | 中文桌面端渠道兜底：`url` / `title` / `summary` / `pics` 跳转，参数以官方页为准 | 仅外链 |
| Web Share API | [MDN](https://developer.mozilla.org/docs/Web/API/Navigator/share) | — | 规范 | 移动端系统分享；需安全上下文 + 用户手势；桌面支持不一致 | 能力检测 + 回退 |

对应关系：AuthPanel ← Cal.com + Outline；ShareBox ← Discourse + Web Share + QQ；
PartExplorer 的弹窗 ← reka-ui Dialog；DataFix ← Ant Design Form 规则 + Cal.com `HintOrErrors`。

### 许可证边界

1. **可复制：MIT**（Cal.com、reka-ui、shadcn-vue、Ant Design / Vue）。分发时保留版权与许可声明；
   MIT 与 GPL-3.0 兼容。注意 MIT 覆盖的是仓库代码，品牌名、Logo、产品截图不在其中。
2. **只学设计：BSL 1.1**（Outline）。source-available 不等于开源：生产用途受限，变更日期后转
   Apache-2.0 只针对特定版本，不等于现在可用。代码、模板、样式、文案都不要复制。
3. **按最保守口径只学模式：Discourse**。GitHub 标 GPL-2.0；`LICENSE.txt` 是 GPLv2 原文，
   而 `COPYRIGHT.md` 写的是 "either version 2 … or (at your option) any later version"。
   两份文件不一致：按 or-later 解读与 GPL-3.0 兼容，按 LICENSE.txt 字面则是 GPL-2.0-only、
   与 GPL-3.0 不兼容。结论不靠猜——不复制源码、CSS、模板与图片，只学交互模式与信息架构；
   真要用代码，先向上游确认许可。
4. **外链不算复制**：QQ widget 与 Web Share 只是跳转或浏览器能力。QQ 会把当前页 URL 交给腾讯，
   只在用户点击时触发，不做预加载。

## 二、设计审阅

范围：`wiki/docs/.vitepress/components/` 下的 `AuthPanel.vue` 553 行、`ShareBox.vue` 449 行、
`PartExplorer.vue` 933 行、`DataFix.vue` 746 行。

### 2.1 登录 / 账号中心（AuthPanel.vue）

做对的：VeeValidate + Zod 与后端字段逐条对齐；`label for`、`aria-invalid`、`aria-describedby`、
`role="alert"`、`aria-busy` 齐全；tablist 支持方向键与 Home/End；OAuth token 从 hash 取出即抹掉；
`redirect` 只接受站内路径；登录渠道由 `/auth/providers` 决定，未配置就不渲染。

缺口：

- 登录后的账号卡是只读的（306–347）：只显示显示名 / handle / 邮箱状态 + 三个出口。不能改显示名、
  不能改密码（必须走邮件重置）、看不到也撤不掉会话。Outline 的 API key 页正是这块的最小完整形态。
- 无邮箱账号是死角（314–319）：文案说不能找回密码，却没有「补填邮箱」的入口。
- `/api/v1` 写死在 32 行，而 DataFix 读 `VITE_ROBOWIKI_API`（DataFix 35 行）。同源部署没事，
  一旦前后端分域，只有登录会坏。
- 非激活 tab 的 `aria-controls` 指向不存在的 panel（381 / 387 只渲染当前模式那个 id）。
- tab 高 36px（514），低于移动端 44px 目标。
- 错误分散在各字段下，提交失败不移动焦点；找回密码是两步表单，却没有 error summary。

### 2.2 分享卡（ShareBox.vue）

做对的：构建期 `copy_text` 带来源等级与数据版本；剪贴板有 `execCommand` 回退；`AbortError`
不当作失败；二维码画不出来时保留可见链接；读屏文案单独一条 `role="status"`，视觉按钮只打勾，
不重复念。

缺口：

- 桌面上没有 `navigator.share` 时，「分享」静默退化成复制链接（148–159）——和左边「复制链接」
  是同一个动作两个名字。
- 失败文案「请长按上方链接手动复制」（122）在桌面上不成立。
- 中文桌面端没有渠道：QQ / 微博 / 邮件外链（参考 Discourse 的分层），用户只能自己去粘贴。
- 没有加载态与缺失态：`entry` 为 null 时整块不渲染（331），访客不知道这个页面本来有分享。
- 下载分享卡失败是静默的（317–318 直接 return），但按钮已经显示「生成中…」。
- 二维码按 132px 绘制、CSS 显示 92px（49 / 393），非整数缩放会发糊；小屏 84px 更明显。

### 2.3 目录与纠错（PartExplorer.vue / DataFix.vue）

- PartExplorer 的键盘弹窗是四个组件里 a11y 最扎实的一处：打开移焦、Tab 循环、Esc 关闭、
  关闭回焦（108–164）。
- DataFix 不再复制登录表单，只给带 `?redirect=` 的链接，方向对。
- 但邮箱验证表单在 AuthPanel（321–341）与 DataFix（351–366）各写一份，id 前缀不同、逻辑相同，
  后续必然漂移。

### 2.4 移动端

做对的：网格 4→3→2→1（794–796）、翻页 `scroll-margin` 避开固定导航（792）、
`pointer: coarse` 下把卡片按钮撑到 34px（885–888）、分享块 560px 换行（419–422）、
纠错表单 640px 单列（743–745）。

不够：

- 触控：分享按钮约 36px（427–430）、账号 tab 36px（514）、纠错按钮 36px（532）。
  48 太奢侈，44 是底线。
- 字号：分享 URL 0.68rem（408）、卡片参数 0.68rem（850）、角标 0.62rem（830 / 868）——
  手机上约 9.6–11px，中文在这个尺寸下基本靠猜。
- 对比表 3 列 `nowrap` + 横向滚动（897 / 903–907），手机上要拖才能看全；对比栏放在列表上方、
  不吸顶，往下选第 3 个时没有就近反馈。
- 弹窗 `max-height: 82vh`（917）没有滚动锁，背景仍能滚；软键盘弹出后可视区变小，面板更难操作。

### 2.5 可访问性

做对的：筛选 / 对比用 `aria-pressed`；结果计数用 `role="status"` 而不是给整个网格加
`aria-live`（613–614 注释写明了原因）；图片 alt 用型号，缺图占位有 `aria-label`；错误文本
`role="alert"`。

待补：

- Dialog 没有背景 `inert`、没有 body 滚动锁；参数表没有 `<th scope>`（715–720），
  读屏听到的是一串没有表头的单元格；对比表有 `th`，但左上角是空 `th`。
- 「优惠需资格」的条件只放在 `title`（672），触屏与键盘都拿不到。
- 双错误色 token：AuthPanel 用 `--rw-danger`，DataFix 用 `--vp-c-danger-1`。
- 浅灰 `--vp-c-text-3` 叠 0.62–0.68rem，实际可读性需要实测对比度，不能靠"看起来还行"。

### 2.6 空态 / 错误态

- 好的：PartExplorer 区分「没收录」与「筛没了」（284–292），0 计数子类用虚线保留入口，
  空态带「重置筛选」（700–703）。
- 坏的：`fail` 声明了却从未赋值（75 / 532），目录读取失败会落成「没有符合条件的部件」——
  把加载失败说成空数据。
- ShareBox 无 entry 时整块消失；DataFix 在 `apiReady === null` 时只留一个标题（318–338）。
  两者都会造成布局跳动或「功能不存在」的错觉。
- DataFix 对没有邮箱的账号也显示「邮箱未验证」（351），与 AuthPanel 的「未填写邮箱」口径不一致。
- 纠错提交成功后不清空表单是刻意的（连续改多个值），但成功提示只在按钮行里，滚动后就看不见。

## 三、优先级

### P1（影响信任或主路径）

1. **目录默认隐藏数据，文案还自相矛盾。** `featuredOnly` 默认 true（83–86），有白名单时
   列表只显示入库件；页头却写「默认全收录」（526），计数（558）也不说明被筛过。
   改法：默认全量，「入库」做成显式筛选，并在计数旁写「已筛至 N 件」。
2. **失败态缺失。** ShareBox 无 entry 静默消失、PartExplorer `fail` 是死代码、
   DataFix 探测中只渲染标题。改法：统一 加载 / 空 / 失败 三态，失败给重试与主站出口。
3. **账号中心只读。** 补：改显示名、改密码（不依赖邮件）、补填邮箱、退出所有会话。
   形态参考 Outline 的分组设置 + Cal.com 的保存态，不必做全套通知开关。
4. **移动端下限。** 可点元素 ≥44px；正文与链接 ≥12px；对比表窄屏改堆叠卡片，
   不靠横向滚动。

### P2（下一轮）

5. **分享动作去重与补渠道。** 有 `navigator.share` 才显示「系统分享」，否则显示
   QQ / 微博 / 邮件外链 + 复制；失败文案按设备区分「长按」与「选中复制」。
6. **a11y 收口。** 修 `aria-controls`；弹窗加滚动锁与背景 `inert`；表格补表头；
   提交失败把焦点移到首个错误或 error summary。
7. **表单细节。** 验证 / 重置邮件加重发冷却与「没收到？」提示；日期用 `type="date"` 或分段输入；
   把 hint + error 抽成一个组件（Cal.com `HintOrErrors` 形态），AuthPanel 与 DataFix 共用。
8. **单一来源。** `.pd-chip` 在组件 scoped（757–766）与 `theme/explorer.css`（349–360）
   各定义一次且值不同（opacity 1 vs .55）；邮箱验证表单两份；API base 两种读法。
   各收敛到一处。

## 四、不建议照搬

- 不要引入 Outline / Discourse 的整套设置、通知、权限系统：本站只有评分 / 评论 / 纠错三类写操作，
  抄 IA 只会得到一排空页面。
- 不要把 Ant Design 的视觉层带进来：现有是 VitePress 变量 + `--rw-*`，两套主题并存会回到双 token。
- 不要做「分享后自动复制 / 自动跳转」：手机上的自动动作会触发权限提示，打断比省一步更糟。
- 不要复制社区项目的文案：它们面向的是文档 / 论坛语境，本站的「来源等级」「数据版本」是独有概念，
  文案得自己写。

## 参考

- Cal.com 开源版：<https://github.com/calcom/cal.diy>
- Outline：<https://github.com/outline/outline>
- Discourse：<https://github.com/discourse/discourse>
- reka-ui：<https://github.com/unovue/reka-ui> / shadcn-vue：<https://github.com/unovue/shadcn-vue>
- Ant Design：<https://ant.design/components/form-cn>
- Web Share API：<https://developer.mozilla.org/docs/Web/API/Navigator/share>
- QQ 分享：<https://connect.qq.com/widget/shareqq/index.html>
- 项目内相关文档：`docs/references.md`（技术选型）、`docs/ADR-007-interaction-stack.md`（交互栈）

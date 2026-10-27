# 视觉参考：zeitvex.github.io（时维的个人主页）

- 仓库目录：`C:\Users\31560\Documents\00_resume\zeitvex.github.io`
- 上游模板：<https://github.com/Lain-Ego0/Lain-Ego0.github.io>
- 站点：<https://zeitvex.github.io>
- 形态：纯静态、零后端、GitHub Pages + PWA

YG 的要求是「ui 和风格类似这份」。这份的视觉底子是 **VS Code 2026 的主题**，
和常见的「Tailwind 紫色渐变落地页」是两条路 —— 它更像一个编辑器，而不是一张海报。

## 1. 它的设计令牌

`assets/css/style.css` 里的 `:root`（浅色）：

```css
--bg-body: #f3f3f3;      /* 页面底：中性灰，不是冷调的 #f8fafc */
--bg-editor: #ffffff;    /* 内容面 */
--bg-panel: #f8f8f8;
--bg-active: #e6f3ff;    /* 选中/标签底：很浅的蓝 */
--text-main: #1f1f1f;    /* 不是纯黑 */
--text-muted: #616161;
--text-subtle: #8a8a8a;
--primary: #0078d4;      /* VS Code 蓝 */
--primary-hover: #005a9e;
--border-light: #d0d0d0; /* 边框比 #e2e8f0 明显，也更中性 */
--radius-md: 8px;
--shadow-card: 0 8px 18px rgba(0, 0, 0, 0.09);
--gradient-title: linear-gradient(135deg, #1f1f1f 0%, #0078d4 100%);
--container-width: 1024px;
```

暗色也有一套（`#1e1e1e` / `#252526` / `#3794ff`），本项目暂只做浅色。

## 2. 它长什么样（可复用的五个部件）

| 部件 | 做法 | 本项目落在哪 |
|---|---|---|
| **终端药丸品牌标** | `zeitvex@robotics:~$ █` 等宽字体 + 边框 + 蓝色闪烁光标 | 顶栏左侧 `roboselect@parts:~$`（`.terminal-pill`） |
| **导航** | 灰字，当前项**蓝色 + 2px 下划线**（不是填充块） | 顶栏 nav |
| **分段统计条** | 一张白卡横切四格，格间竖线分隔；数字**蓝色加粗**、标签灰色小字 | 选型台顶部「191件 / 121件 / 2人 / 2条」 |
| **药丸按钮** | 主操作 = 实心蓝药丸；次操作 = 白色描边药丸 | 发帖 / 登录 / 筛选 / 排序 / 导出 |
| **浅蓝标签** | `#e6f3ff` 底 + `#0078d4` 字，8px 圆角，12.5px | 卡片上的参数 chip、来源等级徽标 |
| **渐变标题** | `135deg #1f1f1f → #0078d4` 裁到文字 | 页面 `h1`（`.title-gradient`） |

## 3. 怎么落的：重定义色阶，而不是逐个改类名

上一轮我已经把深色改成「浅色 + 蓝」，组件里写满了 `text-slate-500`、`bg-blue-600`。
这次要换的是**这套灰蓝的具体色值**，所以不去改 200 多个类名，而是在 `index.css` 里
**重定义 Tailwind 的 `slate` / `blue` 色阶**：

```css
@theme {
  --color-slate-50: #f8f8f8;
  --color-slate-200: #d0d0d0;   /* 变成 VS Code 的 border-light */
  --color-slate-500: #616161;   /* text-muted */
  --color-slate-900: #1f1f1f;   /* text-main，不是纯黑 */
  --color-blue-50: #e6f3ff;     /* 标签底 */
  --color-blue-600: #0078d4;    /* VS Code 蓝 */
  --color-blue-700: #005a9e;
}
```

一处定义，全站生效。再加三个工具类（`.terminal-pill` / `.title-gradient` / `.tabular`）
和一轮圆角收窄（`rounded-2xl` → `rounded-lg`，即 16px → 8px）。

antd 那边同步换 token：`colorPrimary: #0078d4`、`colorBorder: #d0d0d0`、
`colorText: #1f1f1f`、`Table.headerBg: #f8f8f8`、`Segmented.itemSelectedBg: #0078d4`。

VitePress 文档站同理，`custom.css` 里把 `--vp-c-*` 全换成这一套，
并给 `h1` 加上同一支渐变、给表格加斑马纹（191 行里找一行，纯白会串行）。

## 4. 明确没照搬的

- **容器宽度 1024px** —— 那是个人主页的阅读宽度。选型台是数据密集页，
  用 1240px（仍比之前的 1320px 窄）
- **头像 + 大标题的 hero 区** —— 本项目第一屏就该是零件，不是自我介绍
- **左右图文的项目卡**（`grid-template-columns: 36% 1fr`）—— 适合「一个项目一段故事」，
  不适合「150 个型号并排比较」
- **暗色主题** —— 它做了完整的一套（`#1e1e1e`），本项目先只做浅色
- **PWA / Service Worker / 双语切换** —— 与本项目的诉求无关

## 5. 一致性检查清单

换完皮之后要逐项看，不然会出现「一半像 VS Code、一半像 Bootstrap」：

- [x] 页面底 `#f3f3f3`、内容面 `#ffffff`，两者有明确分层
- [x] 所有边框 `#d0d0d0`（不是 `#e2e8f0`）
- [x] 主色只有 `#0078d4` 一个；`#e6f3ff` 只做选中/标签底
- [x] 圆角统一 8px，药丸统一 999px
- [x] 卡片阴影 `0 8px 18px rgba(0,0,0,.09)`，hover 抬到 `0 14px 30px`
- [x] 正文 `#1f1f1f`（不是纯黑），次级 `#616161`，再弱 `#8a8a8a`
- [x] 数字等宽（`tabular-nums`），参数列能对齐扫读
- [x] 标题渐变只在 `h1` 用，页面里不超过一处

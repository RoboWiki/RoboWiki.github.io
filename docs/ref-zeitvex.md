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
@theme { /* 只放字体等非颜色 token */ }

:root, [data-theme="light"] {
  --color-slate-200: #d0d0d0;   /* VS Code 的 border-light */
  --color-slate-500: #616161;
  --color-slate-900: #1f1f1f;
  --color-blue-50:  #e6f3ff;
  --color-blue-600: #0078d4;
}

[data-theme="dark"] {
  --color-slate-200: #3c3c3c;
  --color-slate-500: #9d9d9d;
  --color-slate-900: #cccccc;
  --color-blue-50:  #04395e;
  --color-blue-600: #3794ff;
}
```

Tailwind v4 的工具类输出的是 `color: var(--color-slate-500)` 这种**引用**，
所以在 `[data-theme="dark"]` 里换掉变量，200 多处既有类名一起变，组件一处都不用改。
这就是明暗切换的全部成本 —— 前提是**没有写死的颜色**。

紧接着就踩到两个「写死」的坑：

1. `bg-white` 不走调色板（它是 literal white）。深色下卡片保持纯白、正文直接看不见。
   改成 `bg-[var(--surface)]`（浅 `#ffffff` / 深 `#252526`），19 处。
2. 示意图的 `hsl()` 是内联字符串，CSS 变量换不到。改成
   `fill="var(--g-body)"` 这类引用，SVG 跟着主题自动变，连重渲染都不需要。

antd 不吃 CSS 变量，所以 `theme.tsx` 存了 mode，`ConfigProvider` 按 mode 给
`darkAlgorithm` / `defaultAlgorithm` 和两套 token。

## 4. 深色配色（VS Code dark）

| 用途 | 值 |
|---|---|
| 页面底 | `#1e1e1e` |
| chrome（顶栏/面板） | `#181818` |
| 卡片 / 抬升面 | `#252526` |
| 边框 | `#3c3c3c` |
| 正文 / 次级 / 弱 | `#cccccc` / `#9d9d9d` / `#6f6f6f` |
| 强调 | `#3794ff` |
| 选中底 | `#04395e` |

切换按钮在顶栏右侧（圆形，☾ / ☀），状态存 `localStorage`，
没存过时跟随 `prefers-color-scheme`，系统变化也会跟（除非手动选过）。


## 4. 明确没照搬的

- **容器宽度 1024px** —— 那是个人主页的阅读宽度。选型台是数据密集页，
  用 1240px（仍比之前的 1320px 窄）
- **头像 + 大标题的 hero 区** —— 本项目第一屏就该是零件，不是自我介绍
- **左右图文的项目卡**（`grid-template-columns: 36% 1fr`）—— 适合「一个项目一段故事」，
  不适合「150 个型号并排比较」
- **暗色主题** —— 它做了完整的一套（`#1e1e1e`），本项目先只做浅色
- **PWA / Service Worker / 双语切换** —— 与本项目的诉求无关

## 5. 一次「看起来还是灰绿」的事故

第一版换完，我核对了构建产物：`#3ddc97` 出现 0 次、`#0078d4` 6 次 —— 数据上没问题。
但页面上确实还有绿。原因是**antd 的具名颜色绕过了 Tailwind**：

```jsx
<Tag color="green">实测</Tag>      // → #52c41a，硬编码在 antd 里
```

共 15 处：来源等级 A、实测、徽章、三态里的 `yes`、`越高越好`、可比性 A 级。
再加上两个次要来源：头像用 `hsl(avatar_hue 55% 45%)`（随机色相，会撞到绿）、
示意图按厂商 hash 出色相（灵足 152° 就是绿）。三样加起来，
在灰底上就成了「灰绿」。

修法：**全站只留一个强调色**。

| 原 | 改 |
|---|---|
| `<Tag color="green">` 8 处 | `<Tag color="blue">` |
| `colorSuccess: '#107c10'`（绿） | 不再使用 |
| 三态 `yes` 绿 / `no` 红 / `unknown` 灰 | `yes` **蓝** / `no` 红 / `unknown` 灰 |
| 头像随机色相 | 固定 `hsl(212 72% 45%)` |
| 示意图按厂商出色相 | 单色相 207°（±7 明度区分厂商） |

语义没有丢：三态仍然是「蓝 / 红 / 灰」三种可区分的状态，只是把绿换成了蓝。
实际收益是整页只有一种彩色，蓝色一出现就代表「可操作 / 当前项」。

## 6. 页面底：从 #f3f3f3 改成纯白

参考站的 `#f3f3f3` 是它的**页面底**，但 VS Code 真正的编辑器面板是**纯白**。
第一版把 `#f3f3f3` 铺满整页，加上残留的绿标签，整体偏灰。
现在的分工是：

| 层 | 色值 |
|---|---|
| 内容区（卡片、正文、表格） | `#ffffff` 纯白 |
| chrome（顶栏、面板、表头） | `#f3f3f3` |
| 边框 | `#d0d0d0` |
| 强调 | `#0078d4` |

## 7. 一致性检查清单

换完皮之后要逐项看，不然会出现「一半像 VS Code、一半像 Bootstrap」：

- [x] 页面内容区纯白 `#ffffff`，chrome 才用 `#f3f3f3`
- [x] 所有边框 `#d0d0d0`（不是 `#e2e8f0`）
- [x] **全站只有一个强调色 `#0078d4`**；没有任何绿色（含 antd 具名颜色）
- [x] 圆角统一 8px，药丸统一 999px
- [x] 卡片阴影 `0 8px 18px rgba(0,0,0,.09)`，hover 抬到 `0 14px 30px`
- [x] 正文 `#1f1f1f`（不是纯黑），次级 `#616161`，再弱 `#8a8a8a`
- [x] 数字等宽（`tabular-nums`），参数列能对齐扫读
- [x] 标题渐变只在 `h1` 用，页面里不超过一处
- [x] 头像与示意图不出蓝色区间

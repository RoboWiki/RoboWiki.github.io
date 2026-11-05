# RoboWiki UI 规范

日期：2026-11-05  
适用：Astro 静态站、Taro H5/小程序、Console

## 1. 信息架构

主链路只有一个：

```text
首页 → 部件库 → 型号页 → 看参数/来源 → 看评分与讨论 → 登录参与
```

- 文档、材料、整机是并列内容库，不抢型号页的主动作。
- 型号页只保留两类写操作：**评分**、**讨论/纠错**。GitHub issue 收进“其他方式”。
- 静态 Astro 页负责阅读与 SEO；登录、评分、评论、通知、投稿统一进 Taro 互动版。
- 术语统一：**评分**（1–5 分）、**讨论**（站内评论/回复）、**实测**（GitHub 长文）、**纠错**（参数提案）。

## 2. Token

只用三层：

```text
primitive  --rw-space-*, --rw-text-*, --rw-radius-*
semantic   --rw-primary/success/warning/danger/muted/border/surface/bg
component  --rw-control-*, --rw-focus, --rw-dur-*
```

- 间距只取 4/8/12/16/24/32/48。
- 圆角只取 4/8/12/999。
- 字号只取 12/13/14/16/18/20/24/30；正文 ≥14，辅助 ≥12。
- 桌面控件 32/36，触屏控件 ≥44。
- 组件内不写 hex；颜色只用 token 或既有 slate 语义色。
- 焦点 `:focus-visible` 2px + offset 2；禁止裸 `outline:none`。

## 3. 组件

- Button：primary / secondary / outline / ghost / danger；同一屏最多一个 primary。
- Input/Select：36px；label → 控件 → help → error；错误 `role=alert` 并 `aria-describedby`。
- Tabs：激活加粗 + 2px 下划线；`aria-controls` 必须指向真实面板。
- Dialog/Sheet：Esc、焦点陷阱、滚动锁、关闭回焦。
- Toast：只报成功/信息；错误留在表单内，不双弹。
- 空态：原因 + 一个主行动；区分“未收录”和“筛选无结果”。
- 加载：首屏骨架；不要假空态闪烁。
- 错误：说明 + 重试 + 出口；断网/只读单独文案。

## 4. 列表与详情

- 目录：行/卡片信息固定为 厂商 → 型号 → 价格/关键参数 → 评分；未收录显示“—/询价”，不补 0。
- 详情：标题区（型号/厂商/来源等级/核对）→ 关键参数 → 全部参数 → 讨论/评分。
- 评论：最多 2 层缩进；更深层平铺并标注“回复 @xxx”；操作区触控 ≥32，移动端 ≥44。
- 评分：n=0 显示“暂无评分”；n<3 显示“样本不足”；不显示假 0 分。
- 通知：单一入口 + 未读角标；列表分“全部/未读”；空态指向设置。

## 5. 文案

- 动作可预测：按钮写“提交评分/撤销评分/发表讨论”，不写“确定”。
- 错误说人话：不复述后端英文，不暴露 SMTP/堆栈。
- 不承诺实时：数据页写“下一版数据发布后更新”。

## 6. 平台边界

- Astro：只读内容；客户端 JS 只给搜索/筛选/评分快照。
- Taro：所有写操作；组件按平台 adapter 处理 storage/router/request/share。
- Console：站务高密度表格/表单，继续 Ant Design。
- 共享：`packages/tokens`、`packages/core`；不共享 DOM 组件到小程序。

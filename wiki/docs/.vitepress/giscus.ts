/**
 * giscus 配置 —— 想用 GitHub Discussions 承载文档讨论就填这里。
 *
 * 为什么会有这个文件：YG 问「注册一个 roboselect.github.io 仓库是不是就可以了」。
 * 答案是**基本可以**，但仓库名不重要，重要的是下面四件事全做到：
 *
 *  1. 仓库必须 **public**（私有仓库 giscus 读不到 Discussions）。
 *     叫 `<你的账号>/roboselect.github.io` 完全可行 —— 顺便它还能直接当 Pages 站点。
 *  2. Settings → General → Features 勾上 **Discussions**。
 *  3. 装 giscus App 并只授权给这一个仓库：<https://github.com/apps/giscus>
 *     （Install → 选 Only select repositories）
 *  4. 在 <https://giscus.app/zh-CN> 填仓库名 → 它会自动生成 repoId / category / categoryId，
 *     选 **Announcements** 这类「只有维护者能开新帖、其他人只能评论」的分类，
 *     下面四项照抄过来即可。
 *
 * 门槛效果：**读不要登录，写必须 GitHub 账号**。这正是你要的那道槛，
 * 而且附带 GitHub 的反垃圾、编辑历史、邮件通知、@提醒，都不用自己做。
 *
 * ── 代价（必须先想清楚）────────────────────────────────────────────────
 * giscus 的评论存在 GitHub，不在本站数据库。所以：
 *   * 它不会出现在选型台的社区信息流、贡献榜、零件页的「最高赞评价」里；
 *   * 站内搜索搜不到它；
 *   * 数据主权在 GitHub。
 *
 * 因此这里的取舍是：**文档站用 giscus（要门槛、要 GitHub 账号）**，
 * **选型台/零件页继续用自托管的 Post/WikiComment（要能聚合、能排序、能算贡献）**。
 * 两者不冲突，各自解决不同问题。
 *
 * 不填（保持 null）→ 文档站自动回落到自托管讨论串（现在就是这个状态）。
 */

export interface GiscusConfig {
  repo: `${string}/${string}`
  repoId: string
  category: string
  categoryId: string
  mapping?: 'pathname' | 'url' | 'title' | 'og:title' | 'specific' | 'number'
  lang?: string
  reactionsEnabled?: '0' | '1'
  inputPosition?: 'top' | 'bottom'
}

/** 填成对象即启用。填之前先看文件头的四条前提。 */
export const giscus: GiscusConfig | null = {
  repo: 'zeitvex/roboselect',
  repoId: 'R_kgDOVZTWEQ',
  category: 'Announcements',
  categoryId: 'DIC_kwDOVZTWEc4DJv7l',
  mapping: 'pathname',
  lang: 'zh-CN',
}

export const isGiscusEnabled = (): boolean => giscus !== null

---
title: 投稿
layout: page
sidebar: false
outline: false
---

<script setup>
const gh = 'https://github.com/RoboWiki/RoboWiki.github.io'
const forms = [
  {
    t: '写评价 / 打分',
    d: '总分 + 四个维度（参数可信度 / 做工 / 文档与支持 / 性价比）+ 使用工况。一人一件一票。',
    href: `${gh}/issues/new?template=rate-part.yml&labels=rating`,
    who: '用过或用过同类件的人',
  },
  {
    t: '写实测',
    d: '装了多大负载、跑了多久、温升多少、坏没坏。工况比结论重要。',
    href: `${gh}/issues/new?template=review-part.yml&labels=review`,
    who: '真装机跑过的人',
  },
  {
    t: '纠参数 / 补数据',
    d: '发现数错了、缺了，或者你有官方 PDF。不需要会 git。',
    href: `${gh}/issues/new?template=data-fix.yml&labels=data-fix`,
    who: '任何人',
  },
  {
    t: '写文章 / 教程',
    d: '选型方法、踩坑记录、开源项目拆解。要有可核对的数字与适用条件，不要「十分钟入门」。',
    href: `${gh}/issues/new?template=article.yml&labels=article`,
    who: '愿意把经验写清楚的人',
  },
  {
    t: '加型号 / 改结构',
    d: '批量新增、字段结构调整、口径定义，走 PR。CI 会替你校验。',
    href: `${gh}/blob/main/CONTRIBUTING.md`,
    who: '愿意改 JSON 的人',
  },
]
</script>

<div class="submission">
  <header class="submission-hero">
    <div class="submission-kicker">投稿</div>
    <h1>五种投稿，按你手里的东西选。</h1>
    <p>
      有实测就写实测，有证据就纠数据，用过就写评价，能写清楚就写文章。
      <strong>不用注册本站账号</strong> —— 全是 GitHub 账号，因为我们没有自己的用户体系要维护。
    </p>
  </header>

  <div class="submission-grid">
    <a v-for="f in forms" :key="f.t" class="submission-card" :href="f.href" target="_blank" rel="noopener">
      <b>{{ f.t }}</b>
      <p>{{ f.d }}</p>
      <span class="submission-who">{{ f.who }}</span>
    </a>
  </div>

  <section class="submission-note">
    <h2>投稿之后会怎样</h2>
    <ol>
      <li><b>评分 / 实测</b>：提交后由 Actions 自动聚合成快照，<b>约 3 分钟</b>后站点更新。每条都能查到是谁、凭什么。</li>
      <li><b>纠错</b>：维护者在后台改成数据，<code>part_edits</code> 会记下这次改动的时间、依据与来源链接。</li>
      <li><b>文章</b>：过编辑评审后进「学习路线」，登记到 <code>data/learn.json</code>，并标注难度与预计阅读时长。</li>
      <li><b>PR</b>：CI 跑三道关（数据闸门 → 测试 → 站点构建），绿了才进入人工评审。合并后自动部署。</li>
    </ol>
  </section>

  <section class="submission-note">
    <h2>评分是怎么算的</h2>
    <ul>
      <li><b>一人一件一票</b>：唯一键 = 你的 GitHub 账号 + 部件 id。改主意就<b>编辑原 issue</b>，
        重复开新的只会被聚合脚本按最新一条覆盖，不会变成两票。</li>
      <li><b>四个维度分开算</b>：只统计填了该项的样本，所以页面会显示成 <code>4.6/5</code>、
        <code>2.8/3</code> —— 斜杠后是这一维的实际样本数。<b>没填就是没填，不补 0</b>。</li>
      <li><b>样本少于 3 条</b>显示「样本不足」，不给一个看起来很确定的均分。</li>
      <li><b>装过机的单独均分</b>：装过机的人打的分，和只看参数打的不是一回事，所以分开摆。</li>
      <li><b>工况随评价走</b>：用了多久、什么负载、什么批量。没有工况的结论参考价值很低。</li>
    </ul>
  </section>

  <section class="submission-note">
    <h2>我们不收的东西</h2>
    <ul>
      <li><b>没有实测的「实测」</b>：宁可空着。这个站曾经灌过 21 条编造的实测，后来全删了 —— 在一个立意是「真实使用信息」的站里，假数据比空着坏得多。</li>
      <li><b>只给价格不给条件的优惠</b>：读者会拿它当到手价。价格、条件、有效期缺一不可。</li>
      <li><b>整机宣传图当产品图</b>：错图比没图更糟。缺图就显示「暂无产品图」。</li>
      <li><b>买排名</b>：展示位与评分排序完全分开，赞助必须标注。</li>
      <li><b>没有适用条件的教程</b>：只写「这样最好」而不写「在什么负载/预算下最好」的文章不收。</li>
      <li><b>搬运不署名</b>：转载必须署名到人并附原文链接，规范见「分享与转载」。</li>
    </ul>
  </section>

  <p class="submission-foot">
    不确定该走哪条？直接在
    <a :href="`${gh}/issues/new`" target="_blank" rel="noopener">新建 issue</a>
    里说清楚就行，维护者会帮你归类。
  </p>
</div>

<style>
.submission { max-width: 980px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.submission-kicker {
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem;
}
.submission-hero h1 {
  font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0;
  color: var(--vp-c-text-1);
}
.submission-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85;
  color: var(--vp-c-text-2); max-width: 68ch; }

.submission-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.7rem; margin: 1.6rem 0;
}
.submission-card {
  display: flex; flex-direction: column; gap: 0.35rem;
  border: 1px solid var(--vp-c-divider); border-radius: 12px;
  padding: 0.85rem 0.95rem; background: var(--vp-c-bg); text-decoration: none;
  transition: border-color 0.18s, transform 0.18s;
}
.submission-card:hover { border-color: var(--vp-c-brand-1); transform: translateY(-2px);
  text-decoration: none; }
.submission-card b { font-size: 0.92rem; color: var(--vp-c-text-1); }
.submission-card p { margin: 0; font-size: 0.78rem; line-height: 1.75; color: var(--vp-c-text-2); }
.submission-who { font-size: 0.7rem; color: var(--vp-c-brand-1); margin-top: auto; padding-top: 0.35rem; }

.submission-note { margin-top: 1.8rem; }
.submission-note h2 { font-size: 1rem; font-weight: 700; margin: 0 0 0.6rem;
  border: none; padding: 0; color: var(--vp-c-text-1); }
.submission-note ol, .submission-note ul { font-size: 0.82rem; line-height: 1.9; color: var(--vp-c-text-2);
  padding-left: 1.2rem; margin: 0; }
.submission-note li { margin-bottom: 0.35rem; }
.submission-note b { color: var(--vp-c-text-1); }
.submission-foot { font-size: 0.8rem; color: var(--vp-c-text-3); margin-top: 2rem; }
</style>

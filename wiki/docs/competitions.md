---
title: 竞赛与实战
layout: page
sidebar: false
outline: false
---

<div class="comp">
  <header class="comp-hero">
    <div class="comp-kicker">竞赛与实战</div>
    <h1>比赛要的，和平时做项目要的不是一回事。</h1>
    <p>
      赛季时间紧、预算有限、要的是「已验证的方案 + 能快速到手的部件」。
      这一页是<b>组织层</b>：不重复收录部件和整机，只把资源库里和竞赛强相关的内容
      按「兵种 / 任务 / 供应链」重新摆一遍。点任何一张卡片，都回到资源库里的那一页。
    </p>
  </header>

  <section class="comp-block">
    <h2>RoboMaster</h2>
    <p class="comp-sub">
      本站的执行器库（大疆 / 达妙 / 灵足 / 宇树）就是 RM 赛场上的主力件，
      每项都带来源等级与口径换算 —— 选型时直接比输出端扭矩，不用自己乘减速比。
    </p>
    <h3>赛季常用执行器速查（按峰值扭矩）</h3>
    <table class="comp-table">
      <thead><tr><th>型号</th><th>峰值扭矩（输出端 N·m）</th><th>质量（kg）</th><th>来源等级</th></tr></thead>
      <tbody>
        <tr><td><a href="/parts/actuator/damiao-dm-j10422p-2ec">达妙 DAMIAO DM-J10422P-2EC</a></td><td>400.0</td><td>2.7</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-j8520p-2ec">达妙 DAMIAO DM-J8520P-2EC</a></td><td>176.0</td><td>1.392</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-j10010-2ec">达妙 DAMIAO DM-J10010-2EC</a></td><td>150.0</td><td>1.485</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-j10010l-2ec">达妙 DAMIAO DM-J10010L-2EC</a></td><td>120.0</td><td>1.375</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/robstride-rs04">灵足 RobStride RS04</a></td><td>120.0</td><td>1.42</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-jh20-101-2ec">达妙 DAMIAO DM-JH20-101-2EC</a></td><td>102.0</td><td>1.428</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-j6248p-2ec">达妙 DAMIAO DM-J6248P-2EC</a></td><td>97.0</td><td>0.66</td><td><code>A</code></td></tr>
        <tr><td><a href="/parts/actuator/damiao-dm-jh20-51-2ec">达妙 DAMIAO DM-JH20-51-2EC</a></td><td>69.0</td><td>1.428</td><td><code>A</code></td></tr>
      </tbody>
    </table>
    <p class="comp-note">
      完整 46 件在<a href="/catalog?category=actuator">部件库 · 关节电机</a>按任意列排序。
      扭矩一律输出端口径（含减速箱），不同厂商可以直接比。
    </p>
  </section>

  <section class="comp-block">
    <h2>能借现成工程的整机</h2>
    <p class="comp-sub">
      「别的队怎么做的」最快的回答方式：找一台开源生态完整的机器，把它的仿真与训练工程借过来。
      以下整机都有公开 URDF / 仓库，按生态完整度排序。
    </p>
    <div class="comp-grid">
      <a class="comp-card" href="/robots/unitree-g1">
        <b>宇树 G1</b>
        <span>人形 · 23 自由度</span>
        <em>URDF 2 套 · 仓库 2 个</em>
      </a>
      <a class="comp-card" href="/robots/pollen-microduck">
        <b>Pollen Robotics Microduck</b>
        <span>双足 · 14 自由度</span>
        <em>URDF 1 套 · 仓库 2 个</em>
      </a>
      <a class="comp-card" href="/robots/unitree-go2-edu">
        <b>宇树 Go2 EDU</b>
        <span>四足 · 12 自由度</span>
        <em>URDF 1 套 · 仓库 2 个</em>
      </a>
      <a class="comp-card" href="/robots/unitree-go2-w">
        <b>宇树 Go2-W</b>
        <span>四轮足 · 16 自由度</span>
        <em>URDF 1 套 · 仓库 2 个</em>
      </a>
      <a class="comp-card" href="/robots/unitree-b2">
        <b>宇树 B2</b>
        <span>四足 · 12 自由度</span>
        <em>URDF 1 套 · 仓库 2 个</em>
      </a>
      <a class="comp-card" href="/robots/deeprobotics-lite3">
        <b>DEEP Robotics Lite3</b>
        <span>四足 · 12 自由度</span>
        <em>URDF 1 套 · 仓库 1 个</em>
      </a>
      <a class="comp-card" href="/robots/unitree-go1">
        <b>Unitree Go1</b>
        <span>四足 · 12 自由度</span>
        <em>URDF 1 套 · 仓库 1 个</em>
      </a>
      <a class="comp-card" href="/robots/unitree-a1">
        <b>Unitree A1</b>
        <span>四足 · 12 自由度</span>
        <em>URDF 1 套 · 仓库 1 个</em>
      </a>
    </div>
    <p class="comp-note">全部 21 台整机在<a href="/robots">整机库</a>，可按「有无开源生态」筛选。</p>
  </section>

  <section class="comp-block">
    <h2>加工与快速打样</h2>
    <p class="comp-sub">
      赛季抢时间，加工渠道的「交期稳定性」比单价更重要。
      加工与采购页收 149 家，按质量 / 交期 / 价格档 / 能否开票筛，
      全部来自社区实战反馈，不是厂商自述。
    </p>
    <div class="comp-links">
      <a href="/suppliers">加工与采购 →</a>
      <a href="/catalog">部件库 →</a>
      <a href="/method">参数口径（别把电机端扭矩当输出端）→</a>
    </div>
  </section>

  <section class="comp-block comp-honest">
    <h2>这一页还缺什么</h2>
    <p>
      按兵种（步兵 / 英雄 / 工程 / 哨兵）的整机方案、历届技术报告索引、战队复盘 ——
      这些需要真实参赛队伍供稿，而不是我们编。
      <b>你打过比赛，就比你没打过的我们更懂这一页该写什么。</b>
    </p>
    <div class="comp-links">
      <a href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=article.yml&labels=article"
         target="_blank" rel="noopener">投一篇战队复盘 / 方案拆解 →</a>
      <a href="/submit">全部投稿入口</a>
    </div>
  </section>
</div>

<style>
.comp { max-width: 980px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.comp-kicker {
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem;
}
.comp-hero h1 {
  font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0;
  color: var(--vp-c-text-1);
}
.comp-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85; color: var(--vp-c-text-2); max-width: 72ch; }
.comp-block { margin-top: 2.2rem; }
.comp-block h2 { font-size: 1.05rem; font-weight: 750; margin: 0 0 0.5rem; border: none; padding: 0;
  color: var(--vp-c-text-1); }
.comp-block h3 { font-size: 0.88rem; font-weight: 700; margin: 1rem 0 0.5rem; border: none; padding: 0;
  color: var(--vp-c-text-1); }
.comp-sub { margin: 0 0 0.8rem; font-size: 0.8rem; line-height: 1.8; color: var(--vp-c-text-3); }
.comp-note { margin: 0.6rem 0 0; font-size: 0.76rem; line-height: 1.8; color: var(--vp-c-text-3); }
.comp-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.comp-table th, .comp-table td { text-align: left; padding: 0.35rem 0.6rem;
  border-bottom: 1px solid var(--vp-c-divider); }
.comp-table th { color: var(--vp-c-text-2); font-weight: 600; font-size: 0.72rem; }
.comp-table td code { font-size: 0.72rem; padding: 0 4px; border-radius: 4px;
  background: var(--vp-c-default-soft); }
.comp-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 0.6rem;
}
.comp-card {
  display: flex; flex-direction: column; gap: 0.2rem; text-decoration: none;
  border: 1px solid var(--vp-c-divider); border-radius: 11px; padding: 0.7rem 0.85rem;
  background: var(--vp-c-bg); transition: border-color 0.15s;
}
.comp-card:hover { border-color: var(--vp-c-brand-1); text-decoration: none; }
.comp-card b { font-size: 0.88rem; color: var(--vp-c-text-1); }
.comp-card span { font-size: 0.72rem; color: var(--vp-c-text-2); }
.comp-card em { font-style: normal; font-size: 0.68rem; color: var(--vp-c-brand-1); margin-top: auto; padding-top: 0.2rem; }
.comp-links { display: flex; gap: 1.1rem; flex-wrap: wrap; }
.comp-links a { font-size: 0.82rem; font-weight: 600; color: var(--vp-c-brand-1); }
.comp-honest {
  border: 1px dashed var(--vp-c-divider); border-radius: 12px; padding: 1rem 1.1rem;
  background: var(--vp-c-bg-soft);
}
.comp-honest p { font-size: 0.82rem; line-height: 1.85; color: var(--vp-c-text-2); margin: 0 0 0.7rem; }
</style>

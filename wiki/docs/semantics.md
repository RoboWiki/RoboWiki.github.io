---
title: 参数口径
layout: page
sidebar: false
outline: false
---


<div class="sem">
  <header class="sem-hero">
    <div class="sem-kicker">参数口径</div>
    <h1>同一个数，在不同厂商嘴里不是同一件事。</h1>
    <p>
      「峰值扭矩 40 N·m」可能指瞬时 1 秒、也可能指持续堵转；
      「质量 0.362 kg」可能含线缆、也可能只是定转子。
      这一页把所有字段的<b>定义、缺口含义、以及该停下来复核的阈值</b>写清楚，
      也提供机器可读版本（<code>GET /api/semantics</code>，MCP 工具直接复用）。
    </p>
    <p class="sem-side">
      <b>本站统一的一条硬规则：扭矩与转速一律指输出端（含减速箱）。</b>
      大疆 M3508 手册给的是电机端 0.16 N·m，本站换算成输出端 3.07 N·m
      （× 19.203208556，协议值 3591/187），并在该条目的 notes 里保留原始值与算式。
      原因很简单：达妙、灵足、宇树那些关节模组的标称扭矩本来就是输出端，
      不换算成同一侧，卡片上并列比较就是错的。
    </p>
  </header>

  <section class="sem-steps">
    <div><b>1</b><span>先看<em>来源等级</em></span><p><code>A</code> 逐项对过厂商手册；<code>B</code> 来自公开网页；<code>C</code> 转述。等级决定你敢不敢直接用它做热设计。</p></div>
    <div><b>2</b><span>再看<em>口径字段</em></span><p><code>tau_basis</code> 是 peak 还是 rated、<code>inertia_basis</code> 是 rotor 还是 output。这两个字段读错，后面全错。</p></div>
    <div><b>3</b><span>缺的要当缺的</span><p><code>—</code> 是「没公布」，不是「不支持」，也不是 0。不要用同类件填补，也不要假设额定 = 峰值 / 2。</p></div>
    <div><b>4</b><span>最后才比<em>派生量</em></span><p>扭矩密度、峰值/额定比、反射惯量占比 —— 这三个是结果，不是原因；它们帮你发现异常，不帮你选型。</p></div>
  </section>

  <section>
    <h2>判定只有三种结论</h2>
    <div class="sem-tri">
      <span class="tri yes">yes</span>
      <span class="tri no">no</span>
      <span class="tri unknown">unknown</span>
    </div>
    <p class="sem-note">证据不足，既不算兼容也不算不兼容。</p>
  </section>

  <section>
    <h2>六条物理红线</h2>
    <div class="rl-grid"><div class="rl">
  <div class="rl-head"><span class="rl-id">RL-01</span><b>扭矩密度</b><code>tau_peak_Nm / mass_kg</code></div>
  <span class="rl-th"><b>120.0</b> 需复核 · <b>200.0</b> 不可信</span>
  <p class="rl-why">受永磁体剩磁、铜损散热与减速器许用扭矩共同限制，控制算法无法突破材料极限</p>
  <p class="rl-how"><span>怎么核</span>确认分子是额定还是峰值、分母是否为整机含线缆称重值</p>
</div>
<div class="rl">
  <div class="rl-head"><span class="rl-id">RL-02</span><b>峰值/额定比</b><code>tau_peak_Nm / tau_rated_Nm</code></div>
  <span class="rl-th"><b>3.0</b> 需复核 · <b>5.0</b> 不可信</span>
  <p class="rl-why">峰值受绕组热容与磁路饱和限制，是时间的函数而非常数</p>
  <p class="rl-how"><span>怎么核</span>问：这个峰值能持续几秒？起始温度多少？连续做多少次循环？</p>
</div>
<div class="rl">
  <div class="rl-head"><span class="rl-id">RL-03</span><b>背隙测量条件</b></div>
  
  <p class="rl-why">背隙随加载扭矩变化，空载值可显著优于 ±3% 额定扭矩下的测量值</p>
  <p class="rl-how"><span>怎么核</span>问：测量加载扭矩是多少？是减速器背隙还是含轴承与法兰的整机回差？</p>
</div>
<div class="rl">
  <div class="rl-head"><span class="rl-id">RL-04</span><b>重复定位 vs 绝对精度</b></div>
  
  <p class="rl-why">两者通常相差 1–2 个数量级，混用即失去意义</p>
  <p class="rl-how"><span>怎么核</span>要求分别给出 repeatability 与 absolute accuracy，并注明测量温度</p>
</div>
<div class="rl">
  <div class="rl-head"><span class="rl-id">RL-05</span><b>防护等级作用范围</b></div>
  
  <p class="rl-why">关节薄弱点通常在出线口与输出轴动密封；动密封还会带来附加摩擦扭矩</p>
  <p class="rl-how"><span>怎么核</span>问：出线口是否同等级？动密封带来的附加摩擦扭矩是多少？</p>
</div>
<div class="rl">
  <div class="rl-head"><span class="rl-id">RL-06</span><b>编码器位数≠系统精度</b></div>
  
  <p class="rl-why">分辨率是量化步长下界，不含齿隙、柔轮变形、热漂移与安装误差</p>
  <p class="rl-how"><span>怎么核</span>要求给出输出端（而非电机端）实测重复定位精度</p>
</div></div>
  </section>

  <section>
    <h2>字段字典</h2>
    <h3>扭矩与转速</h3><div class="fd-grid"><div class="fd">
  <div class="fd-head"><code>tau_peak_Nm</code><b>峰值扭矩</b></div>
  <p>分子通常是堵转或短时过载值，必须配持续时间与初始温度才有工程意义</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布峰值扭矩，不能按额定代替</p>
</div><div class="fd">
  <div class="fd-head"><code>tau_rated_Nm</code><b>额定扭矩</b></div>
  <p>可连续输出且热稳定的扭矩，需注明母线电压与环境温度</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布额定值；此时峰值/额定比不可计算，不要假设为 2</p>
</div><div class="fd">
  <div class="fd-head"><code>tau_basis</code><b>扭矩口径</b></div>
  <p>本行 tau_peak_Nm 对应的是峰值还是额定；两者混比会让排序整体反转</p>
  <p class="fd-miss"><span>缺了意味着</span>口径不明，该行不应参与跨厂商比较</p>
</div><div class="fd">
  <div class="fd-head"><code>speed_noload_rpm</code><b>空载转速</b></div>
  <p>输出端空载转速；与减速比由速度律耦合，决定腿尖速度上限</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布；不能与 sec/60° 直接按数值比（量纲互逆）</p>
</div><div class="fd">
  <div class="fd-head"><code>gear</code><b>减速比</b></div>
  <p>给定时 armature 随 N² 放大；不判优劣——高减速比换扭矩但压死速度</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布；无法由转速反解，armature 不可计算</p>
</div></div><h3>惯量与质量</h3><div class="fd-grid"><div class="fd">
  <div class="fd-head"><code>mass_kg</code><b>质量</b></div>
  <p>整机（含减速器、编码器、刹车、外壳、线缆）称重值</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布；用扭矩反推质量会让误差进入 tau^0.666 的杠杆</p>
</div><div class="fd">
  <div class="fd-head"><code>armature_kgm2</code><b>关节反射惯量</b></div>
  <p>MuJoCo 关节的 armature，等于 N²·J。高减速比时常占关节表观惯量 40–80%</p>
  <p class="fd-miss"><span>缺了意味着</span>无法用于仿真；不要填 0，0 表示「理想无惯量电机」</p>
</div><div class="fd">
  <div class="fd-head"><code>rotor_inertia_kgm2</code><b>转子惯量</b></div>
  <p>电机侧转子惯量。若厂商直接给折算值，见 inertia_basis=output</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布；不要用质量或包络估算后当成实测</p>
</div><div class="fd">
  <div class="fd-head"><code>inertia_basis</code><b>惯量口径</b></div>
  <p>rotor=电机侧；output=厂商已折算到输出侧（等于 N²·J）</p>
  <p class="fd-miss"><span>缺了意味着</span>口径不明，armature 无法确定</p>
</div></div><h3>其他</h3><div class="fd-grid"><div class="fd"><div class="fd-head"><code>frictionloss_Nm</code><b>库仑摩擦</b></div>
  <p>几乎无厂商公布。留空比填一个估计值诚实</p>
  <p class="fd-miss"><span>缺了意味着</span>未公布，仿真中该项应标为「假设值 0」而非「实测 0」</p></div><div class="fd"><div class="fd-head"><code>source_tier</code><b>来源等级</b></div>
  <p>A=官方 datasheet 逐项核对；B=厂商页面或广泛引用，未逐项复核；C=二手来源</p>
  <p class="fd-miss"><span>缺了意味着</span>来源不明</p></div><div class="fd"><div class="fd-head"><code>price_cny</code><b>参考价</b></div>
  <p>挂牌或公开报价，不含运费税费，不是实时价</p>
  <p class="fd-miss"><span>缺了意味着</span>无公开报价；不等于买不到</p></div></div>
  </section>

  <section>
    <h2>单位换算</h2>
    | from | to | formula |
|---|---|---|
| rpm | rad/s | rad_s = rpm * pi / 30 |
| sec/60deg | rad/s | rad_s = (pi/3) / t_sec |
| kgf·cm | N·m | Nm = kgf_cm * 0.0980665 |
| arcmin | deg | deg = arcmin / 60 |
| g·cm² | kg·m² | kgm2 = gcm2 * 1e-7 |
| bit(单圈) | deg(量化步长) | deg_step = 360 / 2**bits |
    <p class="sem-note">转速的两种写法量纲互逆（<code>sec/60°</code> 与 <code>rpm</code>），
    按数值直接比会得到相反结论。</p>
  </section>

  <section>
    <h2>可比性分级</h2>
    | grade | name | condition |
|---|---|---|
| A | 可直接比较 | 同一物理量 + 同一负载/温度/电压工况 + 同一测量端（输出端）+ 声明额定或峰值 |
| B | 换算后可比 | 同一物理量，单位不同但换算关系确定，且工况声明一致 |
| C | 仅同厂商内可比 | 有数值但缺工况声明；同厂商内部口径通常自洽 |
| D | 不可比 | 定性描述、缺失、或物理量本身不同；放进对比表就是选型事故的起点 |
  </section>

  <section>
    <h2>向供应商问询清单</h2>
    <p class="sem-note">可直接粘进技术协议或询价邮件。写不进合同的参数，验收时不具备约束力。</p>
    1. 额定扭矩：同时索取母线电压、环境温度、连续运行时长、测量端（电机端/输出端）
2. 峰值扭矩：同时索取允许持续时间、起始温度、循环占空比
3. 背隙：同时索取测量加载扭矩、是减速器背隙还是整机回差
4. 精度：区分重复定位精度与绝对定位精度，并注明测量温度
5. 质量：确认是否含减速器、编码器、刹车、外壳、线缆
6. IP 等级：确认是否覆盖出线口与输出轴动密封
7. 写不进技术协议的参数，验收时不具备约束力
  </section>
</div>

<style>
.sem { max-width: 1080px; margin: 0 auto; padding: 1.8rem 1.5rem 4rem; }
.sem-kicker {
  font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--vp-c-brand-1); font-weight: 700; margin-bottom: 0.5rem;
}
.sem-hero h1 {
  font-size: clamp(1.4rem, 2.6vw, 1.9rem); line-height: 1.3; font-weight: 800;
  letter-spacing: -0.02em; margin: 0 0 0.7rem; border: none; padding: 0;
  color: var(--vp-c-text-1);
}
.sem-hero p { margin: 0; font-size: 0.86rem; line-height: 1.85;
  color: var(--vp-c-text-2); max-width: 70ch; }
.sem h2 {
  font-size: 1.02rem; font-weight: 700; margin: 2rem 0 0.75rem;
  border: none; padding: 0; color: var(--vp-c-text-1);
}
.sem h3 { font-size: 0.86rem; font-weight: 600; margin: 1.1rem 0 0.5rem;
  color: var(--vp-c-text-2); }

.sem-steps {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.7rem; margin: 1.6rem 0 0;
}
.sem-steps > div {
  border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.7rem 0.8rem; background: var(--vp-c-bg);
}
.sem-steps b {
  display: inline-flex; align-items: center; justify-content: center;
  width: 18px; height: 18px; border-radius: 999px; font-size: 0.68rem;
  background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); margin-bottom: 0.35rem;
}
.sem-steps span { display: block; font-size: 0.82rem; font-weight: 600;
  color: var(--vp-c-text-1); }
.sem-steps em { font-style: normal; color: var(--vp-c-brand-1); }
.sem-steps p { margin: 0.3rem 0 0; font-size: 0.76rem; line-height: 1.75;
  color: var(--vp-c-text-3); }

.sem-tri { display: flex; gap: 0.4rem; }
.tri {
  font-size: 0.78rem; font-weight: 700; padding: 0.2rem 0.7rem; border-radius: 999px;
  font-family: var(--font-mono, monospace);
}
.tri.yes { background: var(--vp-c-brand-soft); color: var(--vp-c-brand-1); }
.tri.no { background: rgba(192, 43, 43, 0.1); color: #c02b2b; }
html.dark .tri.no { background: rgba(244, 135, 113, 0.14); color: #f48771; }
.tri.unknown { background: var(--vp-c-default-soft); color: var(--vp-c-text-3); }
.sem-note { font-size: 0.76rem; line-height: 1.8; color: var(--vp-c-text-3);
  margin: 0.5rem 0 0; }

.rl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 0.6rem; }
.rl { border: 1px solid var(--vp-c-divider); border-radius: 10px;
  padding: 0.65rem 0.8rem; background: var(--vp-c-bg); }
.rl-head { display: flex; align-items: baseline; gap: 0.45rem; flex-wrap: wrap; }
.rl-id { font-size: 0.66rem; font-weight: 700; color: var(--vp-c-text-3);
  font-family: var(--font-mono, monospace); }
.rl-head b { font-size: 0.84rem; color: var(--vp-c-text-1); }
.rl-head code { font-size: 0.7rem; }
.rl-th { display: block; font-size: 0.72rem; color: #a06a00; margin-top: 0.25rem; }
html.dark .rl-th { color: #e0b159; }
.rl-th b { font-variant-numeric: tabular-nums; }
.rl-why { font-size: 0.76rem; line-height: 1.75; color: var(--vp-c-text-2); margin: 0.35rem 0 0; }
.rl-how { font-size: 0.72rem; line-height: 1.7; color: var(--vp-c-text-3); margin: 0.3rem 0 0; }
.rl-how span { display: inline-block; font-weight: 600; color: var(--vp-c-brand-1);
  margin-right: 0.35rem; }

.fd-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 0.55rem; }
.fd { border-left: 2px solid var(--vp-c-brand-soft); padding: 0.1rem 0 0.1rem 0.7rem; }
.fd-head { display: flex; align-items: baseline; gap: 0.4rem; }
.fd-head code { font-size: 0.72rem; }
.fd-head b { font-size: 0.8rem; color: var(--vp-c-text-1); }
.fd p { margin: 0.25rem 0 0; font-size: 0.75rem; line-height: 1.7; color: var(--vp-c-text-2); }
.fd-miss { color: var(--vp-c-text-3) !important; }
.fd-miss span { font-weight: 600; margin-right: 0.35rem; }

.sem table { font-size: 0.78rem; }
.sem table td, .sem table th { white-space: normal; }
.sem ol { font-size: 0.8rem; line-height: 1.9; color: var(--vp-c-text-2); }
</style>

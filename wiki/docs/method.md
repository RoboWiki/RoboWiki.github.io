---
title: 方法与来源
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


---



# 数据来源

判定一条数据够不够格进目录，只看一件事：**它能不能指回一手来源。**

- `A` 级 = 逐项核对过厂商手册 / 官方文档（下表的「厂商官网 / 官方文档」）
- `B` 级 = 采自公开商品页或第三方整理，未逐项核对
- `C` 级 = 转述，仅作线索

## 厂商官网 / 官方文档

参数最终都要能追到这些页面或它们的 PDF。列出来也是给贡献者的入口 ——
补数据时先去这里找，而不是去电商页抄。

| 来源 | 类型 | 覆盖品类 | 取什么 |
|---|---|---|---|
| <a href="https://www.livoxtech.com/cn" target="_blank" rel="noopener">Livox 览沃（大疆生态）</a> | 官网 | 激光雷达 | Mid-360 等型号的量程、视场、点频与接口定义 |
| <a href="https://www.damiaokeji.com/" target="_blank" rel="noopener">达妙科技 DAMIAO</a> | 官网 | 关节电机 / 主控 | DM 系列关节电机的扭矩、减速比、惯量与选型手册 |
| <a href="https://orbbec.com.cn/" target="_blank" rel="noopener">奥比中光 Orbbec</a> | 官网 | 深度相机 | Gemini 系列的深度量程、视场、分辨率与 SDK |
| <a href="https://www.monolithicpower.cn/cn/" target="_blank" rel="noopener">MPS 芯源系统</a> | 官网 | 电源芯片 | 驱动板供电与 DC-DC 选型（效率曲线、封装、热阻） |
| <a href="https://bbs.robomaster.com/wiki/20204847/804051" target="_blank" rel="noopener">RoboMaster 官方 Wiki</a> | 官方 Wiki | 下位机 / 电机 | 开发板 A 型与 C 型的接口定义、CAN 分配、例程 |
| <a href="https://developer.d-robotics.cc/rdk_x_doc/RDK?v=3.5.0&p=RDK+X5" target="_blank" rel="noopener">地平线 D-Robotics RDK 文档</a> | 官方文档 | 上位机 | RDK X5 的算力、接口、系统镜像与 BPU 工具链 |
| <a href="http://www.orangepi.cn/html/hardWare/computerAndMicrocontrollers/index.html" target="_blank" rel="noopener">香橙派 OrangePi</a> | 官网 | 上位机 | RK3588 系列单板计算机的接口与供电 |
| <a href="https://www.robosense.cn/index" target="_blank" rel="noopener">速腾聚创 RoboSense</a> | 官网 | 激光雷达 | 机械式与固态雷达的量程、线数、点频 |
| <a href="https://www.intelrealsense.com/" target="_blank" rel="noopener">Intel RealSense</a> | 官网 | 深度相机 | D400 系列的深度量程、基线、快门类型与 IMU 规格 |
| <a href="https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/" target="_blank" rel="noopener">NVIDIA Jetson</a> | 官网 | 上位机 | Orin Nano / NX 的 GPU 核数、算力、内存带宽与功耗档位 |
| <a href="https://www.robomaster.com/" target="_blank" rel="noopener">大疆 RoboMaster</a> | 官网 | 下位机 / 电机 | 开发板与 M3508 / M2006 / GM6020 的产品页 |
| <a href="https://www.unitree.com/" target="_blank" rel="noopener">宇树 Unitree</a> | 官网 | 关节电机 / 激光雷达 | 电机与 4D 雷达的型号页 |
| <a href="https://www.robstride.com/" target="_blank" rel="noopener">灵足时代 RobStride</a> | 官网 | 关节电机 | RS / EL 系列的规格与通信协议 |
| <a href="https://www.orbbec.com.cn/index/Product/index.html?cate=38&ptoduct_cate=1&industry=15&page=2" target="_blank" rel="noopener">奥比中光 产品页（Gemini 系列）</a> | 官网产品页 | 深度相机 | Gemini 系列的深度量程、视场、接口与 SDK（比首页更具体） |
| <a href="https://www.realsenseai.com/cn/stereo-depth-cameras/" target="_blank" rel="noopener">RealSense 国内代理（realsenseai.com）</a> | 国内代理 | 深度相机 | D400 系列在国内的规格页与产品图；Intel 官网对本站 TLS 拦截，这里可达 |
| <a href="https://store.dji.com/cn/shop/robomasters?from=robomaster_online" target="_blank" rel="noopener">大疆商城 RoboMaster 专区</a> | 官方商城 | 下位机 / 电机 | 开发板、电机、配件在售型号与官方产品图（价格随时变，不录） |

## 项目与归档

| 来源 | 取走了什么 | 形态 |
|---|---|---|
| 达妙科技 2026 产品选型手册 | 31 型 J/JH/D 系列，逐页解析 | 本地 PDF |
| 灵足时代 RS / EL 系列规格介绍 | 9 型，含 2026-10 修订的重量 | 本地 PDF |
| Draft（davidhnguyen2000/draft） | 114 行目录 + 拟合趋势 + MuJoCo 模型 | GitHub，MIT |
| CubeMars / MyActuator 官网 | 按产品页 og:image 抓参数与图 | 在线抓取 |
| ZJU-HelloWorld/Wiki | DJI RM 三型的额定/堵转扭矩，宇树手册 | GitHub，附厂商 PDF |
| yssickjgd/robowalker_train | 协议定标常量、M3508 精确减速比 | GitHub |
| roboparts.cc | 接口形态（MCP、三态判定、证据分级） | 参考设计，未取数据 |
| LeRobotDepot / Humanoid Atlas | 价格三件套、受控枚举 | 参考设计，未取数据 |

## 我们拒绝做的事

1. **不灌示例评价。** 曾经灌过 21 条「实测」，技术观察是真的，但温度、时长、作者都是编的。
   在一个立意是「真实使用信息」的站里，这比空着坏得多。已全部删除。
2. **不改数值来掩盖冲突。** 宇树 A1 的减速比，官网写 6:1、手册写 1:9，
   两个都留着，标成「来源冲突」。
3. **不为了过校验编一个峰值。** GM6020 手册只给额定扭矩，峰值就写 `—`，
   并为这种情况放宽了数据闸门的规则。
4. **不混用电调口径。** M2006 的堵转 7 N·m 只在 Z650 那张表里，
   与 C610 的额定 1 N·m 不同源，不拼成一个「峰值/额定比」。

## 每个数字的追溯链

零件的每次字段改动都写进 `part_edits` 表（旧值、新值、依据、来源链接、谁改的、何时）。
于是任何一个数都能回答：**它什么时候、被谁、凭什么被改成了现在这样。**


## 商品图与厂商图的版权

页面上大部分产品图来自**厂商官网 / 官方手册**，少部分来自**立创商城等分销商的实拍**——
每张图的下方「资料与链接」里都写着 `产品图出处`，可以逐张核对。

- 图**只用来说明「这个件长什么样」**，不用于售卖、不用于背书
- 版权归原厂商或原拍摄方；本站不做商业使用，也不授权他人商业使用
- 找不到合适图片时宁可留空显示「暂无产品图」，也不拿宣传图、整机图或同系列图凑数
- 例外：同型号不同包装的实拍（例如某个订单号无图时取同型号另一包装的图），
  会在 `产品图出处` 里明确写出，不让读者以为是同一个料号

如果权利人认为某张图不合适，请通过投稿页告知，我们会在 48 小时内撤下或替换。


## 评分是怎么算的

评分不是一个总分，是**四个维度 + 使用工况 + 样本量**。这样做的原因很实际：
同样打 4 分，「参数靠谱、文档稀烂」和「文档齐全、做工一般」对下一个读者是完全不同的信息。

### 打分只要三项

从部件页点「写评价」进 GitHub 表单，**必填只有三项**：总分、是否用过、一句话理由。
分维度打分与使用工况都是可选项 —— 门槛低才有人愿意点。

### 维度按品类显示

所有品类都有三个通用维度：**性价比 / 做工 / 文档与支持**；
再按品类加一项它真正关心的：

| 品类 | 额外维度 | 为什么是它 |
|---|---|---|
| 关节电机 / 舵机 / 芯片 / 传感器 / IMU / 雷达 / 相机 / 电调 / 电池 | 参数可信度 | 这类件的核心风险是「标称的数字和实际不一样」 |
| 上位机 / 下位机 | 兼容与生态 | 这类件的核心风险是「买回来接不上、驱动难写」 |
| 线束 / 结构 | 无 | 只有通用三维 —— 硬塞维度只会让人乱填 |

维度定义在 `data/taxonomy.json` 的 `rating_dims` 里，加品类时顺手声明即可，
组件不用改。

**每个维度的样本量单独统计。** 有人只打总分没填维度，那一票不进维度均值 ——
所以页面上会显示成 `4.6/5`、`2.8/3`，斜杠后就是这一维的实际样本数。
**缺项绝不补 0**：0 分是差评，没填是不知情，两者不能混。

### 样本量

- 少于 3 条：显示「样本不足」，不给一个看起来很确定的均分
- 「装过机」的人单独给一个均分（`own_hardware_avg`）—— 这是最有参考价值的那个数
- 分布直方图一起给出：`5 人 5 分` 和 `1 人 5 分 + 4 人 1 分` 均分不同，但都必须能看见形状

### 使用工况

每条评价可以标：用了多久（<1 月 / 1–3 月 / 3–12 月 / >1 年）、负载情况（轻载测试 / 常规 /
满载连续）、使用批量（单件样机 / 小批量 / 量产）。没有工况的结论参考价值很低，
所以工况和分数一起展示。

### 反刷与门槛

- **一人一件一票**：唯一键 = GitHub 账号 + 部件 id。改主意编辑原 issue，
  重复开新的会被聚合脚本按最新一条覆盖，不会变成两票
- **必须有 GitHub 账号**：不接受匿名打分 —— 每条评价都能查到是谁、什么时候写的
- **可被关闭**：明显刷分或与工况不符的 issue，维护者可以直接 close，聚合时自动排除
- **不做加权**：不按「谁更专业」调权重 —— 那是黑箱。只用「装过机 / 没装过」这一个可核对的区分


## 数据治理与版本

页面上的数能不能核，取决于四件可查的东西：口径文件、ID 注册表、数据快照、出处字段。
下表的数字在构建时从仓库文件现读，不是手写的。

| 项 | 现在是什么 |
|---|---|
| 口径版本 | `1.0.0`（`schema/semantics.json` 的 `version`） |
| 永久 ID | `440` 条已登记，`0` 条 tombstone（`data/_id_registry.json`） |
| 图片出处 | 有图 `243` 条（部件 `228` + 整机 `15`），全部写了 `image_source` |
| 仓库许可 | 引用仓库 `51` 条（部件 `32` + 整机 `19`），许可证已核 `47` 条 |

**口径版本。** 静态站、`/api/semantics`、MCP 读的是同一份 `schema/semantics.json`。
改口径（字段定义、单位换算、红线阈值）就升 `version`；页面上任何数字的含义，
以那一版为准。拿旧版本的数据配新口径来读，会读出错的值。

**实体与 ID。** `data/_id_registry.json` 是永久 ID 注册表，只追加。
id 一经登记**不改名、不复用**：改名要把旧 id 留作 alias，删除要在注册表里
留 tombstone（`removed`）。原因不抽象 —— 评分唯一键、外部引用、型号页 URL
全挂在 id 上，改一个名字会同时断三处。

**数据快照。** `data/` + `schema/` 打成 tar.gz 发到
[GitHub Releases](https://github.com/RoboWiki/RoboWiki.github.io/releases)，
tag 形如 `data-YYYY.MM.DD`。每次发布带三个附件：

- `robowiki-data-<tag>.tar.gz` —— `data/` 与 `schema/` 的只读快照
- `MANIFEST.json` —— 条数、`ids` 数量、`semantics_version`、生成时间
- `SHA256SUMS.txt` —— 上面那个 tar.gz 的 SHA-256

打 `data-v*` tag，或在 Actions 里手动触发 `Data release` 生成。发布前先跑
`python -m pipeline validate`，不通过就不发 —— 快照发出去就是对外承诺了一个版本。

**出处与许可。** 有图必须写 `image_source`（厂商 PDF 的哪一页、商城条目号、
采集日期）；引用了仓库必须写 `repo_license`，读不到许可证就写 `null`
表示「未核」，不猜一个填上。这两条是 `python -m pipeline validate` 的硬检查，
不是文风偏好 —— 上表「许可证已核 `47` 条」正是现状：宁可标未核，也不编。

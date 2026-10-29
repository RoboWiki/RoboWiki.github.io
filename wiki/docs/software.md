---
title: 机器人软件
layout: page
sidebar: false
outline: false
---

# 机器人软件

<p class="sw-lead">引擎、训练框架、中间件、数学库、模仿学习 —— 这五层决定了
「仿真像不像真的、策略怎么练、怎么和真机说话」。这里按层给<b>许可、版本、
什么时候该用它</b>，不做项目大全：清单会漂，判断不会。</p>

<p class="sw-meta">15 个软件 · 许可与版本取自本地仓库（2026-10-29），
读不到的标「未核对」—— 这一栏写错比空着糟。</p>

<section class="sw-group">
  <h2>物理引擎与仿真</h2>
  <p class="sw-hint">引擎决定「仿真里像不像真的」。接触、摩擦、执行器模型对不上，策略练得再好也搬不到机器上。</p>
  <div class="sw-grid">
<article class="sw-card">
  <header>
    <h3>MuJoCo</h3>
    <span class="sw-vendor">Google DeepMind</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">版本未核对</span><span class="sw-chip">C / Python</span></div>
  <p class="sw-what">接触动力学做得准的物理引擎，CPU 上就能跑；MJX 分支可以放到 GPU 上批量并行。</p>
  <p class="sw-when"><b>什么时候用它</b>：只想快速验证一条轨迹、或者要一个「和真实接触行为对得上」的参照时用它。单机、零配置、模型文件是纯文本 XML。</p>
  <p class="sw-note">MJX 的并行度不如 Isaac 系，但胜在便宜和确定性好；很多论文的 baseline 就是它。</p>
  <footer><a href="https://github.com/google-deepmind/mujoco" target="_blank" rel="noopener">仓库</a> · <a href="https://mujoco.readthedocs.io/" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>MuJoCo Playground</h3>
    <span class="sw-vendor">Google DeepMind</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">v0.2.0</span><span class="sw-chip">Python / JAX</span></div>
  <p class="sw-what">基于 MJX 的一批 GPU 加速环境，专为机器人学习研究与 sim-to-real 写的。</p>
  <p class="sw-when"><b>什么时候用它</b>：想在 MuJoCo 上做「大规模并行 + 现成环境」，又不想自己搭环境骨架时用它。</p>
  <p class="sw-note">版本号取自本地仓库 pyproject（0.2.0）；上游迭代快，用前先看 release。</p>
  <footer><a href="https://github.com/google-deepmind/mujoco_playground" target="_blank" rel="noopener">仓库</a> · <a href="https://playground.mujoco.com/" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>MuJoCo Menagerie</h3>
    <span class="sw-vendor">Google DeepMind</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">MIT</span><span class="sw-chip">版本未核对</span><span class="sw-chip">MJCF</span></div>
  <p class="sw-what">一批高质量 MJCF 模型集合（各家机器人、手、场景），拿来即用。</p>
  <p class="sw-when"><b>什么时候用它</b>：要找某台机器的 MJCF、又不想从 URDF 手转时先翻这里。</p>
  <p class="sw-note">模型许可随各机型不同（目录内另有 LICENSE），商用前逐个看。</p>
  <footer><a href="https://github.com/google-deepmind/mujoco_menagerie" target="_blank" rel="noopener">仓库</a> · <a href="https://github.com/google-deepmind/mujoco_menagerie" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>Isaac Lab</h3>
    <span class="sw-vendor">NVIDIA</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">BSD-3-Clause</span><span class="sw-chip">版本未核对</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">建在 Isaac Sim 上的机器人学习框架：manager-based 的任务组织（观测/奖励/命令/课程/域随机化）+ 大规模并行仿真。</p>
  <p class="sw-when"><b>什么时候用它</b>：要做成千上万个并行环境、并且看重与 Isaac 生态（资产、传感器、渲染）的对接时用它。</p>
  <p class="sw-note">本地快照是 0.1.0，上游已到 2.x —— 版本号别照抄本地。硬门槛是 NVIDIA GPU。</p>
  <footer><a href="https://github.com/isaac-sim/IsaacLab" target="_blank" rel="noopener">仓库</a> · <a href="https://isaac-sim.github.io/IsaacLab/" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>Genesis</h3>
    <span class="sw-vendor">Genesis 社区</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">版本未核对</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">较新的通用物理平台，主打「一个引擎统一刚体/软体/流体 + 可微」，也在往 GPU 并行方向做。</p>
  <p class="sw-when"><b>什么时候用它</b>：要看「跨引擎 parity」或者需要软体/可微物理时值得试；生态比 MuJoCo/Isaac 年轻。</p>
  <p class="sw-note">本地没有克隆，版本与细节未核对，只作为方向性参考。</p>
  <footer><a href="https://github.com/Genesis-Embodied-AI/Genesis" target="_blank" rel="noopener">仓库</a> · <a href="https://genesis-world.readthedocs.io/" target="_blank" rel="noopener">文档</a></footer>
</article>
  </div>
</section>
<section class="sw-group">
  <h2>训练框架</h2>
  <p class="sw-hint">训练框架决定「策略怎么练出来」。这一层的差异主要在任务怎么组织、后端是谁、能不能并行。</p>
  <div class="sw-grid">
<article class="sw-card">
  <header>
    <h3>mjlab</h3>
    <span class="sw-vendor">mujocolab</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">v1.6.0</span><span class="sw-chip">Python / JAX</span></div>
  <p class="sw-what">把 Isaac Lab 那套 manager-based API 搬到 MuJoCo Warp 上：任务组织照旧，底层换成 GPU 加速的 MuJoCo。</p>
  <p class="sw-when"><b>什么时候用它</b>：喜欢 Isaac Lab 的组织方式，但想跑在 MuJoCo 上（确定性、接触质量、显存便宜）时用它。</p>
  <p class="sw-note">版本 1.6.0 取自本地仓库。它和 Isaac Lab 的 API 相似度高，迁移成本主要在资产与后端差异。</p>
  <footer><a href="https://github.com/mujocolab/mjlab" target="_blank" rel="noopener">仓库</a> · <a href="https://mujocolab.github.io/mjlab/" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>UniLab</h3>
    <span class="sw-vendor">UniLab 社区</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">v1.4.0</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">契约驱动的机器人学习基础设施：任务语义写一次，换物理后端（CPU/GPU/外部 worker）不改生命周期。</p>
  <p class="sw-when"><b>什么时候用它</b>：同一个任务要在多个后端上对照跑（比如 MuJoCo 与 Isaac 各跑一遍比一致性）时，它的抽象最省事。</p>
  <p class="sw-note">版本 1.4.0 取自本地仓库 pyproject。</p>
  <footer><a href="https://github.com/unilabsim/UniLab" target="_blank" rel="noopener">仓库</a> · <a href="https://github.com/unilabsim/UniLab" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>legged_gym + rsl_rl</h3>
    <span class="sw-vendor">ETH RSL</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">BSD-3-Clause</span><span class="sw-chip">版本未核对</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">腿足 RL 的<b>原始范式</b>：环境是 Isaac Gym，算法是 rsl_rl 的 PPO，配置按机型分层。</p>
  <p class="sw-when"><b>什么时候用它</b>：想知道「某个 reward 或观测项最初为什么这么写」时回到这里 —— 现在一半以上的腿足工程是它的分支或改写。</p>
  <p class="sw-note">Isaac Gym 已停更（NVIDIA 转向 Isaac Lab），新项目别从它起步；但它仍是读代码时的共同祖先。</p>
  <footer><a href="https://github.com/leggedrobotics/legged_gym" target="_blank" rel="noopener">仓库</a> · <a href="https://github.com/leggedrobotics/legged_gym" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>robot_lab</h3>
    <span class="sw-vendor">fan-ziqi</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">版本未核对</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">基于 Isaac Lab 的多机型任务矩阵，四足/轮足/人形都在里面，配置与奖励写得比较整齐。</p>
  <p class="sw-when"><b>什么时候用它</b>：想快速拿一台机器跑通 Isaac Lab 训练，又不想从空模板搭时用它。</p>
  <p class="sw-note">许可与版本未逐项核对本地仓库，用前确认。</p>
  <footer><a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">仓库</a> · <a href="https://github.com/fan-ziqi/robot_lab" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>RL-SAR</h3>
    <span class="sw-vendor">fan-ziqi</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">版本未核对</span><span class="sw-chip">C++ / Python</span></div>
  <p class="sw-what">把「仿真验证 + 真机部署」做成一条链的框架，四足/轮足/人形都有，机上侧是 C++ 推理。</p>
  <p class="sw-when"><b>什么时候用它</b>：策略训完了，要落到真机（读状态、跑推理、发指令）时看它的部署侧怎么写。</p>
  <p class="sw-note">配套 rl_sar_zoo 有各机型的 URDF/MJCF 与策略集合。</p>
  <footer><a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">仓库</a> · <a href="https://github.com/fan-ziqi/rl_sar" target="_blank" rel="noopener">文档</a></footer>
</article>
  </div>
</section>
<section class="sw-group">
  <h2>中间件与 SDK</h2>
  <p class="sw-hint">中间件与 SDK 决定「怎么和真机说话」。仿真里再顺，接口这一层不对齐就上不了机。</p>
  <div class="sw-grid">
<article class="sw-card">
  <header>
    <h3>ROS 2</h3>
    <span class="sw-vendor">Open Robotics / 社区</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">版本未核对</span><span class="sw-chip">C++ / Python</span></div>
  <p class="sw-what">机器人中间件标准：节点、话题、服务、TF、ros2_control。</p>
  <p class="sw-when"><b>什么时候用它</b>：要接传感器、跑导航栈（Nav2）、或者和别人的机器人代码对接时，绕不开它。</p>
  <p class="sw-note">版本按发行版走（Humble / Jazzy 等），不像普通库那样比单个版本号。</p>
  <footer><a href="https://github.com/ros2/ros2" target="_blank" rel="noopener">仓库</a> · <a href="https://docs.ros.org/" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>Unitree SDK2 / unitree_ros2</h3>
    <span class="sw-vendor">宇树 Unitree</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">BSD-3-Clause</span><span class="sw-chip">版本未核对</span><span class="sw-chip">C++ / Python</span></div>
  <p class="sw-what">宇树机器人的官方低层接口：读关节状态、下发力矩/位置，ROS2 包把话题桥出来。</p>
  <p class="sw-when"><b>什么时候用它</b>：在 Go2/B2/G1 上做真机实验，这是最短路径。</p>
  <p class="sw-note">与 unitree_mujoco 配套：同一套控制代码可以先进仿真再上机。</p>
  <footer><a href="https://github.com/unitreerobotics/unitree_sdk2" target="_blank" rel="noopener">仓库</a> · <a href="https://support.unitree.com/" target="_blank" rel="noopener">文档</a></footer>
</article>
  </div>
</section>
<section class="sw-group">
  <h2>运动学与动力学</h2>
  <p class="sw-hint">这一层只算不控：运动学、雅可比、质量矩阵、动力学一致性 —— 写 WBC / MPC 时的地基。</p>
  <div class="sw-grid">
<article class="sw-card">
  <header>
    <h3>Pinocchio</h3>
    <span class="sw-vendor">Inria / LAAS-CNRS</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">BSD-2-Clause</span><span class="sw-chip">版本未核对</span><span class="sw-chip">C++ / Python</span></div>
  <p class="sw-what">刚体运动学与动力学库：正/逆运动学、雅可比、质量矩阵、动力学一致性，都算得快且解析。</p>
  <p class="sw-when"><b>什么时候用它</b>：写 WBC / MPC / 状态估计时要算这些量，用它比自己推一遍可靠得多。它<b>只算，不控制</b>。</p>
  <p class="sw-note">常和 CasADi / OCS2 一起出现在 MPC 工程里。</p>
  <footer><a href="https://github.com/stack-of-tasks/pinocchio" target="_blank" rel="noopener">仓库</a> · <a href="https://stack-of-tasks.github.io/pinocchio/" target="_blank" rel="noopener">文档</a></footer>
</article>
  </div>
</section>
<section class="sw-group">
  <h2>模仿学习与数据</h2>
  <p class="sw-hint">从示教里学，而不是从奖励里学。数据格式、重定向、策略训练是这条线的三段。</p>
  <div class="sw-grid">
<article class="sw-card">
  <header>
    <h3>LeRobot</h3>
    <span class="sw-vendor">Hugging Face</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">Apache-2.0</span><span class="sw-chip">v0.6.2</span><span class="sw-chip">Python / PyTorch</span></div>
  <p class="sw-what">真机模仿学习的工具箱：数据集格式、预训练策略、训练与评测脚本，一套走完。</p>
  <p class="sw-when"><b>什么时候用它</b>：要做「示教 → 策略 → 真机」这条线（尤其机械臂 + 遥操作），它是目前社区最集中的入口。</p>
  <p class="sw-note">版本 0.6.2 取自本地仓库。它的数据集格式正在变成事实标准，值得先按它的结构存数据。</p>
  <footer><a href="https://github.com/huggingface/lerobot" target="_blank" rel="noopener">仓库</a> · <a href="https://huggingface.co/docs/lerobot" target="_blank" rel="noopener">文档</a></footer>
</article>
<article class="sw-card">
  <header>
    <h3>GMR</h3>
    <span class="sw-vendor">社区（动作重定向）</span>
  </header>
  <div class="sw-chips"><span class="sw-chip lic">未核对</span><span class="sw-chip">版本未核对</span><span class="sw-chip">Python</span></div>
  <p class="sw-what">把人类动作数据重定向到不同机器人骨架上的工具链（本地有多机型 asset）。</p>
  <p class="sw-when"><b>什么时候用它</b>：做人形/四足的动作模仿（AMP、motion tracking）时，第一步都是重定向，它省掉这一步的手工对齐。</p>
  <p class="sw-note">仓库地址与许可未核对，本地只有资产与配置快照 —— 这条先当方向参考，别照抄链接。</p>
  <footer>仓库未核对</footer>
</article>
  </div>
</section>

<section class="sw-group">
  <h2>怎么选（按约束倒推，不按名气）</h2>
  <p class="sw-hint">这张表只给「先看哪个」的顺序，不是结论 ——
  真选型要去看 release、issue 和硬件门槛。</p>
  <table class="sw-pick">
    <thead><tr><th>你的约束</th><th>先看</th></tr></thead>
    <tbody>
    <tr><td>只有一台普通电脑，想快速验证想法</td><td>MuJoCo（CPU 就能跑，模型是纯文本 XML）</td></tr>
    <tr><td>有 NVIDIA 卡，要成千上万并行环境</td><td>Isaac Lab；若更信 MuJoCo 的接触模型，用 mjlab（同一套任务组织、换后端）</td></tr>
    <tr><td>同一个任务想跨后端对照一次</td><td>UniLab（任务语义写一次，换后端不改生命周期）</td></tr>
    <tr><td>要读「某个写法最早为什么这么写」</td><td>legged_gym + rsl_rl（现在一半的腿足工程是它的分支）</td></tr>
    <tr><td>策略要落真机</td><td>官方 SDK（如 unitree_sdk2）+ 部署框架（如 RL-SAR）</td></tr>
    <tr><td>要写 WBC / MPC</td><td>Pinocchio（算）+ CasADi / OCS2（优化）</td></tr>
    <tr><td>做示教模仿而不是 RL</td><td>LeRobot（数据集格式正在变成事实标准）</td></tr>
    </tbody>
  </table>
</section>

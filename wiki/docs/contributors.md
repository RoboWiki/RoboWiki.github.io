---
title: 贡献者
layout: page
sidebar: false
outline: false
---

<div class="cd">
  <header class="cd-hero">
    <div class="cd-kicker">贡献者</div>
    <h1>这些数不是天上掉下来的。</h1>
    <p>每一条参数背后都有人对着厂商手册逐页核过，每一个「—」都是有人确认过「确实没公布」。名字留在这里，是因为<strong>数据出错时得有人能被找到</strong>。</p>
  </header>

  <ContributorGrid lang="zh" />

  <section class="cd-hand">
    <h2>谁做了什么</h2>
    <p class="cd-sub">不从 git log 生成：机器只会数 commit，说不出谁核过哪本手册。</p>
    <div class="ct-grid"><div class="ct">
  <div class="ct-head"><b>zeitvex</b><span class="ct-role">创始维护者</span></div>
  <p>建站与全部工程实现：数据闸门与校验、按品类生成页面、部件库检索与对比、参数口径页、供应商页、贡献者页；达妙 / 灵足 / 大疆 / 宇树四家的 A 级参数逐条核对（扭矩统一到输出端、缺字段一律写 null）；把「来源可追溯」做成机器可查的规则，而不是写在文档里的一句话。</p>
  <a href="https://github.com/zeitvex" target="_blank" rel="noopener">GitHub</a>
</div>
<div class="ct">
  <div class="ct-head"><b>Dichen33</b><span class="ct-role">创始贡献者</span></div>
  <p>整机数据 15 台（含 URDF / 仓库链接）、上位机与下位机批量扩充、IMU 与相机雷达补充—— 共 50 条数据进入目录；另写了一份《部件资料收集指南》，把「从开源项目找到型号 → 进官网 → 落地」的流程固定成规范。另外「遥控器」这一整个品类是他从 ccc 分支带进来的：5 个遥控器 + 2 个 CAN 模块（含 7 张实拍图、参数与备注），顺手把部件页备注改成分组卡片；并加了「首页品类卡点击后预选对应品类」—— 跳转带 ?cat=，从首页点「电源」直接落到该品类。</p>
  <a href="https://github.com/Dichen33" target="_blank" rel="noopener">GitHub</a>
</div>
<div class="ct">
  <div class="ct-head"><b>JadeCrane</b><span class="ct-role">创始贡献者</span></div>
  <p>芯片品类从 14 颗补到 18 颗：新增 STM32H723 / TCAN334G / TMC2209 / AS5600；为 18 颗补齐官方文档页、手册 PDF 与官方仓库链接（逐条实测可打开）；补 17 颗的国内 1+ 挂牌价（含来源与采集日期）；补 12 张商品实拍图。另外登记了 doc_url / doc_pdf / repo_urls 三个参数名，让校验器的 20 条误报消失（82 → 62 警告）。</p>
  <a href="https://github.com/Beni-537" target="_blank" rel="noopener">GitHub</a>
</div></div>
  </section>

  <section class="cd-how">
    <h2>怎么上榜</h2>
    <ul><li>补一条参数、修一个单位、加一张正确产品图 —— 名字进名单</li><li>写一条带工况的实测 —— 名字进名单，且会出现在那个部件页上</li><li>纠一次错并给出依据 —— 同样计入</li></ul>
    <p class="cd-note">没有「贡献值排行榜」。这个站不做积分游戏 —— 排序永远只看参数与实测，不看谁贡献得多。</p>
  </section>

  <p class="cd-foot"><a href="/submit">去投稿 →</a></p>
</div>

---
title: High Torque Robotics 高擎动力 HTDW-5036-02-CNE
description: "High Torque Robotics 高擎动力 HTDW-5036-02-CNE（关节电机）：峰值扭矩 21 N·m、额定 6 N·m、减速比 36:1；来源 A 级、2026-10-31 核对。"
---


# High Torque Robotics 高擎动力 HTDW-5036-02-CNE

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/hightorque-htdw-5036-02-cne.jpg" alt="HTDW-5036-02-CNE" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">行星减速</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 21 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | 36 |
| 质量 (kg) | 0.345 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://www.hightorquerobotics.com/product/482">https://www.hightorquerobotics.com/product/482</a><br/>
收录：《20260602 新模组产品手册（英文）》各型号参数表（https://book.hightorque.cn/Module0603E，PDF 直链见 doc_pdf）+ 官网产品页交叉核对（2026-10-31）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="hightorque-htdw-5036-02-cne" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 75 rpm ≈ 7.9 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 3.1 m/s；实际打 6 折再定目标速度。
- **峰值只能用秒级** —— 峰值/额定 = 3.5。连续负载应当按额定 6 N·m 设计，峰值只在加速/触地瞬间用。超 3 倍时必须向厂商要「持续时间 + 初始温度」。
- **高减速比的代价** —— 减速比 36，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">61 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">3.5</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">7.9 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">—</span><span class="pm-note">缺转子惯量</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 50 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [HTDW-5036-02-DNE](/parts/actuator/high-torque-robotics-htdw-5036-02-dne) | 21 | 0.323 | 36 |
| [HTCP-5031-06-CYC](/parts/actuator/high-torque-robotics-htcp-5031-06-cyc) | 16 | 0.385 | 31 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 21 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | 36 |
| 质量 (kg) | 0.345 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 扭矩口径 | peak |
| 外径 (mm) | 50 |
| 长度 (mm) | 47.4 |
| 官方文档 | https://www.hightorquerobotics.com/product?id=482 |
| 空载转速 (rpm) | 75 |
| 额定转速 (rpm) | 50 |
| 电压范围 | 12~50.4 |
| 转矩常数 (N·m/A) | 0.54 |
| 极对数 | 14 |
| 峰值电流 (A) | 10 |
| 额定电流 (A) | 2 |
| 编码器 | 双编，高/低速端各 14-bit |
| 通信 | CAN、CANFD |
| 内置驱动 | 1 |
| 尺寸 | Φ50×47.4 mm |
| 官方手册 (PDF) | https://cdn.hightorque.cn/pdf/book.hightorque.cn/Module0603E.pdf |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+hightorque-htdw-5036-02-cne&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorquerobotics.com/product/482" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://www.hightorquerobotics.com/product?id=482" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://cdn.hightorque.cn/pdf/book.hightorque.cn/Module0603E.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>高擎官网产品图（hightorquerobotics.com）</td></tr><tr><td class="rs-plain">收录说明</td><td>《20260602 新模组产品手册（英文）》各型号参数表（https://book.hightorque.cn/Module0603E，PDF 直链见 doc_pdf）+ 官网产品页交叉核对（2026-10-31）</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+HTDW-5036-02-CNE+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=HTDW-5036-02-CNE&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=High+Torque+Robotics+%E9%AB%98%E6%93%8E%E5%8A%A8%E5%8A%9B+HTDW-5036-02-CNE+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/hightorque.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/hightorque.json</td></tr></tbody></table>

## 备注

参数取自官方手册各型号参数表，并与官网产品页交叉核对；峰值列采用手册的 Locked-rotor torque（堵转扭矩，不是限时脉冲峰值），额定 6 N·m、额定/空载 50/75 rpm、24 V（12–50.4 V）、额定/峰值电流 2/10 A、Kt 0.54 N·m/A、14 对极、高/低速端双 14-bit 编码器、CAN/CANFD、5 Mbps、3 kHz 控制频率，背隙 <10 arcmin、重复定位 <12 arcmin、绝对定位 <15 arcmin、额定输出 30 W。官网未公开价格，price_cny 留空；实物图取自官网产品页。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

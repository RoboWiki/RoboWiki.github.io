---
title: 达妙 DAMIAO DM-H6215
description: "达妙 DAMIAO DM-H6215（关节电机）：峰值扭矩 2 N·m、额定 1 N·m、减速比 1:1；来源 B 级、2026-10-31 核对。"
---


# 达妙 DAMIAO DM-H6215

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dm-dm-h6215.jpg" alt="DM-H6215" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">直驱</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 2 |
| 额定扭矩 (N·m) | 1 |
| 减速比 | 1 |
| 质量 (kg) | 0.36 |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://www.damiaokeji.com/index.php?c=show&id=115">https://www.damiaokeji.com/index.php?c=show&id=115</a><br/>
收录：达妙官网产品页 + 官方 Gitee 仓库（kit-miao）使用教程 V2，2026-10-31 核对<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="damiao-dm-h6215" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 320 rpm ≈ 33.5 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 13.4 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.0，这个比值正常。连续按 1 N·m、瞬时按 2 N·m 设计即可。
- **准直驱要配好电流环** —— 减速比只有 1，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">6 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.0</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">33.5 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">—</span><span class="pm-note">缺转子惯量</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 68 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [DM-G6220](/parts/actuator/damiao-dm-g6220) | 2.7 | 0.493 | 1 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 2 |
| 额定扭矩 (N·m) | 1 |
| 减速比 | 1 |
| 质量 (kg) | 0.36 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 320 |
| 极对数 | 14 |
| 相电感 (µH) | 2,000 |
| 相电阻 (Ω) | 2.5 |
| 官方文档 | http://www.damiaokeji.com/index.php?c=show&id=115 |
| 额定转速 (rpm) | 120 |
| 电压范围 | 15~32 |
| 额定电流 (A) | 2.5 |
| 峰值电流 (A) | 4.3 |
| 编码器 | 霍尔 |
| 通信 | CAN（控制与调参） |
| 内置驱动 | 1 |
| 外径 (mm) | 68 |
| 长度 (mm) | 44.5 |
| 官方手册 (PDF) | https://gitee.com/kit-miao/DM-H6215/raw/master/%E8%AF%B4%E6%98%8E%E4%B9%A6/DM-H6215%E8%BD%AE%E6%AF%82%E7%94%B5%E6%9C%BA%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8BV2.pdf |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+damiao-dm-h6215&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.damiaokeji.com/index.php?c=show&id=115" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="http://www.damiaokeji.com/index.php?c=show&id=115" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td><a href="https://gitee.com/kit-miao/DM-H6215/raw/master/%E8%AF%B4%E6%98%8E%E4%B9%A6/DM-H6215%E8%BD%AE%E6%AF%82%E7%94%B5%E6%9C%BA%E4%BD%BF%E7%94%A8%E6%95%99%E7%A8%8BV2.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>达妙官网产品图（damiaokeji.com 产品页 id=115）</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙官网产品页 + 官方 Gitee 仓库（kit-miao）使用教程 V2，2026-10-31 核对</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-H6215+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-H6215&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-H6215+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/damiao.json</td></tr></tbody></table>

## 备注

1:1 直驱。24 V：额定 1 N·m / 峰值 2 N·m，额定 120 rpm / 空载 320 rpm，额定 2.5 A / 峰值 4.3 A，相电感 2000 µH、相电阻 2.5 Ω，Ø68×44.5 mm，约 360 g；霍尔编码器，CAN 控制与调参。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

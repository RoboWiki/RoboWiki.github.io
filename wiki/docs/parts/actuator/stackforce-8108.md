---
title: STACKFORCE 8108
---


# STACKFORCE 8108

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/stackforce-8108.jpg" alt="8108" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">planetary</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 22 |
| 额定扭矩 (N·m) | 7.5 |
| 减速比 | 8 |
| 质量 (kg) | 0.395 |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://github.com/Seeed-Projects/Stackforce-Motor-SDK">https://github.com/Seeed-Projects/Stackforce-Motor-SDK</a><br/>
收录：Seeed wiki zh-CN《Stackforce 系列电机》+ 厂商 PDF《新版6010关节电机用户文档V1.1》（2026-10-31）；原厂官网规格页未取到<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="stackforce-8108" :dims='["value", "build", "docs", "spec_trust"]' />
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
- **峰值与额定的用法** —— 峰值/额定 = 2.9，这个比值正常。连续按 7.5 N·m、瞬时按 22 N·m 设计即可。
- **准直驱要配好电流环** —— 减速比只有 8，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">56 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.9</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">33.5 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">—</span><span class="pm-note">缺转子惯量</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 22 |
| 额定扭矩 (N·m) | 7.5 |
| 减速比 | 8 |
| 质量 (kg) | 0.395 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 额定电流 (A) | 7.5 |
| power_w | 180 |
| 扭矩口径 | peak |
| 额定转速 (rpm) | 110 |
| 空载转速 (rpm) | 320 |
| 外径 (mm) | 97 |
| 长度 (mm) | 46 |
| 相电阻 (Ω) | 0.439 |
| 相电感 (µH) | 403 |
| 接口 | CAN 2.0 1 Mbps / CANFD 5 Mbps（MIT 协议） |
| 官方文档 | https://wiki.seeedstudio.com/cn/stackforce_series/ |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+stackforce-8108&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/Seeed-Projects/Stackforce-Motor-SDK" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://wiki.seeedstudio.com/cn/stackforce_series/" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td class="rs-plain">产品图出处</td><td>Seeed Wiki《Stackforce 系列电机》产品图（wiki.seeedstudio.com/cn/stackforce_series/；6010/8108 同系列外观，官方未按型号区分）</td></tr><tr><td class="rs-plain">收录说明</td><td>Seeed wiki zh-CN《Stackforce 系列电机》+ 厂商 PDF《新版6010关节电机用户文档V1.1》（2026-10-31）；原厂官网规格页未取到</td></tr><tr><td><a href="https://www.google.com/search?q=STACKFORCE+8108+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=8108&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=STACKFORCE+8108+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/stackforce.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/stackforce.json</td></tr></tbody></table>

## 备注

8:1、MIT 协议、CAN 2.0 1 Mbps 或 CANFD 5 Mbps、双磁编；缺极对数与编码器位数。厂商中文名未核实，vendor_cn 留空。资料链接为 Seeed Wiki 系列页（含 6010/8108 参数表与接线）；该页 8108 用户手册链接已失效（404），未收录。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

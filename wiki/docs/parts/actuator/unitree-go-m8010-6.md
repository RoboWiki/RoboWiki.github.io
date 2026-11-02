---
title: 宇树 Unitree GO-M8010-6
description: "宇树 Unitree GO-M8010-6（关节电机）：峰值扭矩 23.7 N·m、减速比 6.33:1、质量 0.53 kg；来源 A 级、2026-10-31 核对。"
---


# 宇树 Unitree GO-M8010-6

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/unitree-go-m8010-6.jpg" alt="GO-M8010-6" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">准直驱 QDD</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,500</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 23.7 |
| 额定扭矩 (N·m) | — |
| 减速比 | 6.33 |
| 质量 (kg) | 0.53 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://www.unitree.com/go1/motor">https://www.unitree.com/go1/motor</a><br/>
收录：Unitree 官网 GO 电机页 + GO-M8010-6 用户手册（2026-10-31 核对）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-go-m8010-6" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 286.5 rpm ≈ 30.0 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 12.0 m/s；实际打 6 折再定目标速度。
- **额定扭矩未知怎么办** —— 只有峰值。按厂商惯例不要假设「额定 = 峰值/2」——有的件是 3:1，有的只有 1.2:1。先向厂商要额定值再做热设计。
- **准直驱要配好电流环** —— 减速比只有 6.33，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">45 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">30.0 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 23.7 |
| 额定扭矩 (N·m) | — |
| 减速比 | 6.33 |
| 质量 (kg) | 0.53 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 286.5 |
| 外径 (mm) | 96.5 |
| 长度 (mm) | 42.3 |
| 电压范围 | 12~30 |
| 转矩常数 (N·m/A) | 0.639 |
| 峰值电流 (A) | 40 |
| 编码器 | 15-bit 绝对值 |
| 通信 | RS-485 4 Mbps，控制 6000 Hz |
| 内置驱动 | 1 |
| 官方手册 (PDF) | https://cdn.shopify.com/s/files/1/0673/6848/5000/files/GO-M8010-6_User_Manual.pdf |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **490 元**（原价 1,500 元）
   - 活动：GO-M8010-6 首次购买特价
   - 资格与条件：首次购买可享 490 元/个（限购 2 个，原价 1500 元/个）。需在商品页选择对应规格或咨询客服。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：天猫 Unitree 宇树旗舰店商品页（2026-10-28）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+unitree-go-m8010-6&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.unitree.com/go1/motor" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://cdn.shopify.com/s/files/1/0673/6848/5000/files/GO-M8010-6_User_Manual.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商资料抓取（unitree-go-m8010-6.jpg）</td></tr><tr><td class="rs-plain">收录说明</td><td>Unitree 官网 GO 电机页 + GO-M8010-6 用户手册（2026-10-31 核对）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+GO-M8010-6+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=GO-M8010-6&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+GO-M8010-6+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/unitree.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/unitree.json</td></tr></tbody></table>

## 备注

Go1 关节电机。官方页给最大扭矩 23.7 N·m（24 ℃ 实测）、最大转速 30 rad/s@24 V（≈286 rpm）、减速比 6.33:1、重量 530 g、尺寸 96.5×92.5×42.3 mm、最大相电流 40 A、扭矩常数 0.63895 N·m/A、RS-485 4 Mbps、控制频率 6000 Hz、15-bit 编码器、工作电压 12–30 VDC（推荐 24 V），内置 FOC；未公布额定扭矩与转子惯量。价格为历史记录参考价（2026-10-31 未复核）。手册 PDF 为经销商 CDN 镜像。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

---
title: 达妙 DAMIAO DM-H65-1EC
description: "达妙 DAMIAO DM-H65-1EC（关节电机）：峰值扭矩 21.5 N·m、额定 6 N·m、质量 3.15 kg；来源 B 级、2026-10-31 最近查阅。"
image: "/parts/dm-dm-h65-1ec.jpg"
---


# 达妙 DAMIAO DM-H65-1EC

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dm-dm-h65-1ec.jpg" alt="DM-H65-1EC" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">直驱</span>
      <span class="part-tag tierB">来源 B</span>
      <span class="part-tag muted">无公开报价</span>
    </div>
    <div class="part-jump">
      <a href="#评分">评分</a>
      <a href="#纠错">纠错</a>
      <a href="#这一页的讨论">讨论</a>
    </div>

<div class="part-split">
<div class="part-official">

#### 公开页面参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 21.5 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | — |
| 质量 (kg) | 3.15 |
| 额定电压 (V) | 48 |

<div class="part-src">
来源：<a href="https://www.damiaokeji.com/index.php?c=show&id=116">https://www.damiaokeji.com/index.php?c=show&id=116</a><br/>
收录：达妙官网产品页 + 官方 Gitee 仓库（kit-miao）说明书 V1.2（2026-08-19）（>10 MB，Gitee 匿名 raw 无法直链），2026-10-31 核对<br/>
最近查阅：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="damiao-dm-h65-1ec" :dims='["value", "build", "docs", "spec_trust"]' />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 480 rpm ≈ 50.3 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 20.1 m/s；实际打 6 折再定目标速度。
- **峰值只能用秒级** —— 峰值/额定 = 3.6。连续负载应当按额定 6 N·m 设计，峰值只在加速/触地瞬间用。超 3 倍时必须向厂商要「持续时间 + 初始温度」。
- **算你需要多大扭矩** —— 静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">7 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">3.6</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">50.3 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 峰值扭矩 (N·m) | 21.5 |
| 额定扭矩 (N·m) | 6 |
| 减速比 | — |
| 质量 (kg) | 3.15 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 48 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 480 |
| 极对数 | 15 |
| 编码器 | 17 bit（±0.05°），单编码器 |
| 官方文档 | http://www.damiaokeji.com/index.php?c=show&id=116 |
| 额定转速 (rpm) | 120 |
| 电压范围 | 20~65 |
| 额定电流 (A) | 9.4 |
| 峰值电流 (A) | 33.6 |
| 相电感 (µH) | 849 |
| 相电阻 (Ω) | 0.4 |
| 通信 | CAN@5 Mbps（Max）；调参 UART@921600 bps |
| 内置驱动 | 1 |
| 外径 (mm) | 171 |
| 长度 (mm) | 66.3 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+damiao-dm-h65-1ec&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.damiaokeji.com/index.php?c=show&id=116" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="http://www.damiaokeji.com/index.php?c=show&id=116" target="_blank" rel="noopener">官方文档页</a></td><td>厂商维护的文档入口</td></tr><tr><td class="rs-plain">产品图出处</td><td>达妙官网产品图（damiaokeji.com 产品页 id=116）</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙官网产品页 + 官方 Gitee 仓库（kit-miao）说明书 V1.2（2026-08-19）（>10 MB，Gitee 匿名 raw 无法直链），2026-10-31 核对</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-H65-1EC+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-H65-1EC&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-H65-1EC+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki/edit/main/data/catalog/actuator/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/damiao.json</td></tr></tbody></table>

## 备注

6.5 寸轮毂电机。额定 6 N·m / 峰值 21.5 N·m，额定 120 rpm；空载 260 rpm@24 V、395 rpm@36 V、480 rpm@48 V。额定相/电源电流 9.4 A / 2.56 A@48 V，峰值 33.6 A / 10.4 A@48 V；相电感 849 µH、相电阻 0.4 Ω，Ø171×66.3 mm，约 3150 g；17 位编码器（±0.05°，单编码器），CAN@5 Mbps + 调参 UART@921600 bps。官方参数表未给减速比，gear 留空。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

---
title: 大疆 DJI GM6020
---


# 大疆 DJI GM6020

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dji-robomaster-gm6020.jpg" alt="GM6020" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">direct</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥899</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | 1.2 |
| 减速比 | 1 |
| 质量 (kg) | 0.468 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |

<div class="part-src">
来源：<a href="https://github.com/ZJU-HelloWorld/Wiki">https://github.com/ZJU-HelloWorld/Wiki</a><br/>
收录：《RoboMaster GM6020 直流无刷电机使用说明》(2023-10-13) 规格页<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="dji-robomaster-gm6020" :dims='["value", "build", "docs", "spec_trust"]' />
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
- **准直驱要配好电流环** —— 减速比只有 1，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">—</span><span class="pm-note">缺峰值扭矩或质量，不推算</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
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
| 峰值扭矩 (N·m) | — |
| 额定扭矩 (N·m) | 1.2 |
| 减速比 | 1 |
| 质量 (kg) | 0.468 |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | 24 |
| 空载转速 (rpm) | 320 |
| 额定转速 (rpm) | 132 |
| 外径 (mm) | 66.7 |
| 长度 (mm) | 45 |
| 转矩常数 (N·m/A) | 0.741 |
| 相电阻 (Ω) | 1.8 |
| 相电感 (µH) | 5,780 |
| 极对数 | 10 |
| 额定电流 (A) | 1.62 |
| 编码器 | 13 bit 绝对值 |
| 通信 | CAN |
| 内置驱动 | 0 |
| 工作温度 | 0–55 ℃ |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+dji-robomaster-gm6020&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/ZJU-HelloWorld/Wiki" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商官方产品图（RoboMaster 商城产品照）</td></tr><tr><td class="rs-plain">收录说明</td><td>《RoboMaster GM6020 直流无刷电机使用说明》(2023-10-13) 规格页</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+GM6020+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=GM6020&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+GM6020+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/dji-robomaster.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/dji-robomaster.json</td></tr></tbody></table>

## 备注

直驱云台电机，**没有减速箱**，1.2 N·m 即输出端。空心轴内径 18 mm，空载调速 0–320 rpm。低速大力矩是它的强项，拿它当腿关节会嫌慢。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

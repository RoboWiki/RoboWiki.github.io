---
title: 灵足 RobStride RS06
---


# 灵足 RobStride RS06

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/robstride-rs06.jpg" alt="RS06" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">qdd</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥849</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 36 |
| 额定扭矩 (N·m) | 11 |
| 减速比 | 9 |
| 空载转速 (rpm) | 480 |
| 质量 (kg) | 0.621 |
| 转子惯量 (kg·m²) | 0.012 |
| 外径 (mm) | 88 |
| 长度 (mm) | 49 |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 1.1 |

<div class="part-src">
来源：<a href="https://www.robstride.com/">https://www.robstride.com/</a><br/>
收录：灵足官方资料库 灵足时代RS系列产品规格介绍(2026.010.09).pdf（https://github.com/RobStride/Product_Information）<br/>
核对：2026-10-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="灵足-robstride-rs06" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **仿真里填哪个字段** —— MJCF/URDF 的 armature 字段填 **0.012**（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。不要当转子惯量再乘 N² —— 会差 81 倍。
- **腿尖速度上限** —— 空载 480 rpm ≈ 50.3 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 20.1 m/s；实际打 6 折再定目标速度。
- **峰值只能用秒级** —— 峰值/额定 = 3.3。连续负载应当按额定 11 N·m 设计，峰值只在加速/触地瞬间用。超 3 倍时必须向厂商要「持续时间 + 初始温度」。
- **准直驱要配好电流环** —— 减速比只有 9，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">58 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">3.3</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">50.3 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">9%</span><span class="pm-note">假设单腿 2.0 kg、腿长 0.5 m 绕髋摆；占比越高腿越「黏」</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 36 |
| 额定扭矩 (N·m) | 11 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 480 |
| 额定转速 (rpm) | — |
| 减速比 | 9 |
| 质量 (kg) | 0.621 |
| 外径 (mm) | 88 |
| 长度 (mm) | 49 |
| 转子惯量 (kg·m²) | 1.48e-04 |
| 惯量口径 | output |
| 转子惯量 (kg·m²) | 0.012 |
| 额定电压 (V) | 48 |
| 电压范围 (V) | 15-60V |
| 转矩常数 (N·m/A) | 1.1 |
| 相电阻 (Ω) | 0.23 |
| 相电感 (µH) | 165 |
| 极对数 | — |
| 峰值电流 (A) | 57 |
| 额定电流 (A) | 14.3 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | 2pcs |
| 通信 | CAN |
| 内置驱动 | 1 |
| 防护等级 | — |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **764 元**（原价 849 元）
   - 活动：灵足教育优惠：一律 9 折
   - 资格与条件：学生证或其他在读/在职教育证明均可，联系官方客服改价后下单；适用于灵足 RS / EL 全系。是否与其它活动叠加请与客服确认。
   - 有效期：至 2027-12-31
   - 链接：灵足时代官方客服
   - 来源：灵足官方（用户确认）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+%E7%81%B5%E8%B6%B3-robstride-rs06&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.robstride.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>灵足官网产品图（robstride.com 导航菜单图，透明底）</td></tr><tr><td class="rs-plain">收录说明</td><td>灵足官方资料库 灵足时代RS系列产品规格介绍(2026.010.09).pdf（https://github.com/RobStride/Product_Information）</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS06+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RS06&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS06+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/actuator/lingzu-robstride.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/lingzu-robstride.json</td></tr></tbody></table>

## 备注

—

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

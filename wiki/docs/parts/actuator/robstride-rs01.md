---
title: 灵足 RobStride RS01
---


# 灵足 RobStride RS01

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/robstride-rs01.jpeg" alt="RS01" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">qdd</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥599</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 17 |
| 额定扭矩 (N·m) | 7 |
| 减速比 | 7.75 |
| 空载转速 (rpm) | 275 |
| 质量 (kg) | 0.38 |
| 转子惯量 (kg·m²) | 4.20e-03 |
| 外径 (mm) | 79 |
| 长度 (mm) | 45.5 |
| 额定电压 (V) | 36 |
| 转矩常数 (N·m/A) | 1.22 |

<div class="part-src">
来源：<a href="https://github.com/RobStride/Product_Information">https://github.com/RobStride/Product_Information</a><br/>
收录：Draft actuator_catalog.json（114 行总体） + 灵足时代RS/EL系列产品规格介绍 2026-10-09<br/>
核对：2026-10-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="灵足-robstride-rs01" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **仿真里填哪个字段** —— MJCF/URDF 的 armature 字段填 **4.20e-03**（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。不要当转子惯量再乘 N² —— 会差 60.062 倍。
- **腿尖速度上限** —— 空载 275 rpm ≈ 28.8 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 11.5 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.4，这个比值正常。连续按 7 N·m、瞬时按 17 N·m 设计即可。
- **准直驱要配好电流环** —— 减速比只有 7.75，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">45 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.4</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">28.8 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">3%</span><span class="pm-note">假设单腿 2.0 kg、腿长 0.5 m 绕髋摆；占比越高腿越「黏」</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 79 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [RS02](/parts/actuator/robstride-rs02) | 17 | 0.405 | 7.75 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 17 |
| 额定扭矩 (N·m) | 7 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 275 |
| 额定转速 (rpm) | — |
| 减速比 | 7.75 |
| 质量 (kg) | 0.38 |
| 外径 (mm) | 79 |
| 长度 (mm) | 45.5 |
| 转子惯量 (kg·m²) | 6.99e-05 |
| 惯量口径 | output |
| 转子惯量 (kg·m²) | 4.20e-03 |
| 额定电压 (V) | 36 |
| 电压范围 (V) | 15-48V |
| 转矩常数 (N·m/A) | 1.22 |
| 相电阻 (Ω) | 0.55 |
| 相电感 (µH) | 486 |
| 极对数 | — |
| 峰值电流 (A) | 23 |
| 额定电流 (A) | 7 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | 1 pc |
| 通信 | CAN |
| 内置驱动 | 1 |
| 防护等级 | — |

## 优惠与获取条件

有一条相关信息：**机型页赞助位（示例）**

- 说明：整机方案页可挂厂商方案位。示例条目，请替换。
- 有效期：至 2026-12-31
- 链接：https://github.com/RobStride/Product_Information

这条**没有具体优惠价**，所以卡片上不显示折扣 —— 只有价格没有条件的那种「优惠」本站不放。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://github.com/RobStride/Product_Information" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商资料</td></tr><tr><td class="rs-plain">收录说明</td><td>Draft actuator_catalog.json（114 行总体） + 灵足时代RS/EL系列产品规格介绍 2026-10-09</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS01+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RS01&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS01+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

7.75:1, single encoder, square 79mm | 36.0 V；额定 7.0 N·m；官方公布低速端等效惯量 0.0042 kg·m²

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

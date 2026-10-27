---
title: 达妙 DM DM-J4340-2EC V1.1
---


# 达妙 DM DM-J4340-2EC V1.1

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dm-dm-j4340-2ec-v1-1.jpeg" alt="DM-J4340-2EC V1.1" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">planetary</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥799</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 40 |
| 额定扭矩 (N·m) | 12 |
| 减速比 | 40 |
| 空载转速 (rpm) | 112 |
| 质量 (kg) | 0.362 |
| 转子惯量 (kg·m²) | 0.0315 |
| 外径 (mm) | 57 |
| 长度 (mm) | 53.3 |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 3.612 |

<div class="part-src">
来源：<a href="https://www.hightorque.cn/">https://www.hightorque.cn/</a><br/>
收录：达妙 2026 产品选型表 2026-10-23<br/>
核对：2026-10-27
</div>

</div>

<div class="part-comm">
<PartRating part-id="达妙-dm-dm-j4340-2ec-v1-1" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **仿真里填哪个字段** —— MJCF/URDF 的 armature 字段填 **0.0315**（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。不要当转子惯量再乘 N² —— 会差 1600 倍。
- **腿尖速度上限** —— 空载 112 rpm ≈ 11.7 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 4.7 m/s；实际打 6 折再定目标速度。
- **峰值只能用秒级** —— 峰值/额定 = 3.3。连续负载应当按额定 12 N·m 设计，峰值只在加速/触地瞬间用。超 3 倍时必须向厂商要「持续时间 + 初始温度」。
- **高减速比的代价** —— 减速比 40，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">110 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">3.3</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">11.7 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">20%</span><span class="pm-note">假设单腿 2.0 kg、腿长 0.5 m 绕髋摆；占比越高腿越「黏」</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 57 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [DM-D5730 -1EC](/parts/actuator/dm-dm-d5730-1ec) | 1.9 | 0.628 | 1 |
| [DM-D5730 -1EE](/parts/actuator/dm-dm-d5730-1ee) | 1.9 | 0.628 | 1 |
| [DM-J4310-2EC V1.1](/parts/actuator/dm-dm-j4310-2ec-v1-1) | 7 | 0.306 | 10 |
| [DM-J4310-2EC V1.2](/parts/actuator/dm-dm-j4310-2ec-v1-2) | 12.5 | 0.306 | 10 |
| [DM-J4310M-2EC](/parts/actuator/dm-dm-j4310m-2ec) | 18 | 0.37 | 10 |
| [DM-J4310P-2EC](/parts/actuator/dm-dm-j4310p-2ec) | 12.5 | 0.33 | 10 |
| [DM-J4340-2EC](/parts/actuator/dm-dm-j4340-2ec) | 27 | 0.362 | 40 |
| [DM-J4340P-2EC](/parts/actuator/dm-dm-j4340p-2ec) | 27 | 0.381 | 40 |
| [DM-J4340P-2EC V1.1](/parts/actuator/dm-dm-j4340p-2ec-v1-1) | 40 | 0.381 | 40 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 40 |
| 额定扭矩 (N·m) | 12 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 112 |
| 额定转速 (rpm) | 36 |
| 减速比 | 40 |
| 质量 (kg) | 0.362 |
| 外径 (mm) | 57 |
| 长度 (mm) | 53.3 |
| 转子惯量 (kg·m²) | 1.97e-05 |
| 惯量口径 | rotor |
| 转子惯量 (kg·m²) | 0.0315 |
| 额定电压 (V) | 48 |
| 电压范围 (V) | 15~52 |
| 转矩常数 (N·m/A) | 3.612 |
| 相电阻 (Ω) | 0.72 |
| 相电感 (µH) | 290 |
| 极对数 | 14 |
| 峰值电流 (A) | 19.85 |
| 额定电流 (A) | 4.11 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | 磁编，双编 |
| 通信 | CAN、CANFD |
| 内置驱动 | 1 |
| 防护等级 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 有效期**，缺一项都不上卡片。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorque.cn/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>厂商资料</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙 2026 产品选型表 2026-10-23</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DM+DM-J4340-2EC+V1.1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-J4340-2EC+V1.1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DM+DM-J4340-2EC+V1.1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

48.0 V 版本；关节电机；额定 12.0 N·m；源文勘误：无 | 低压版 24 V：56.0 rpm 价格来源：达妙/宇树天猫旗舰店商品页（2026-10-28 抓取，属活动价，可能随活动结束变化）。

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

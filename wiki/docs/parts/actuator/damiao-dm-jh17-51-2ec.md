---
title: 达妙 DAMIAO DM-JH17-51-2EC
---


# 达妙 DAMIAO DM-JH17-51-2EC

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">harmonic</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,689</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 24 |
| 额定扭矩 (N·m) | 16 |
| 减速比 | 51 |
| 空载转速 (rpm) | 60 |
| 质量 (kg) | 0.985 |
| 转子惯量 (kg·m²) | 0.244 |
| 外径 (mm) | 80 |
| 长度 (mm) | 70 |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 4.7812 |

<div class="part-src">
来源：<a href="https://www.hightorque.cn/">https://www.hightorque.cn/</a><br/>
收录：达妙 2026 产品选型表 2026-10-23<br/>
核对：2026-10-27
</div>

</div>

<div class="part-comm">
<PartRating part-id="达妙-dm-dm-jh17-51-2ec" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **仿真里填哪个字段** —— MJCF/URDF 的 armature 字段填 **0.244**（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。不要当转子惯量再乘 N² —— 会差 2601 倍。
- **腿尖速度上限** —— 空载 60 rpm ≈ 6.3 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 2.5 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 1.5，这个比值正常。连续按 16 N·m、瞬时按 24 N·m 设计即可。
- **高减速比的代价** —— 减速比 51，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">24 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">1.5</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">6.3 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">66%</span><span class="pm-note">假设单腿 2.0 kg、腿长 0.5 m 绕髋摆；占比越高腿越「黏」</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 80 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [DM-JH17-101-2EC](/parts/actuator/damiao-dm-jh17-101-2ec) | 54 | 0.985 | 101 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 24 |
| 额定扭矩 (N·m) | 16 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 60 |
| 额定转速 (rpm) | 40 |
| 减速比 | 51 |
| 质量 (kg) | 0.985 |
| 外径 (mm) | 80 |
| 长度 (mm) | 70 |
| 转子惯量 (kg·m²) | 9.38e-05 |
| 惯量口径 | rotor |
| 转子惯量 (kg·m²) | 0.244 |
| 额定电压 (V) | 48 |
| 电压范围 (V) | 20~54 |
| 转矩常数 (N·m/A) | 4.7812 |
| 相电阻 (Ω) | 0.161 |
| 相电感 (µH) | 107 |
| 极对数 | 10 |
| 峰值电流 (A) | 12.94 |
| 额定电流 (A) | 4.62 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | 电感，双编 |
| 通信 | CAN、CANFD |
| 内置驱动 | 1 |
| 防护等级 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorque.cn/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙 2026 产品选型表 2026-10-23</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-JH17-51-2EC+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-JH17-51-2EC&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-JH17-51-2EC+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

48.0 V 版本；谐波关节电机；额定 16.0 N·m；源文勘误：无 价格来源：达妙/宇树天猫旗舰店商品页（2026-10-28 抓取，属活动价，可能随活动结束变化）。 产品图待补：抓到的是达妙人形整机宣传图，不是 JH17 关节模组，需厂商型号页原图

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

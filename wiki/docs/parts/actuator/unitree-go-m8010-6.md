---
title: 宇树 Unitree GO-M8010-6
---


# 宇树 Unitree GO-M8010-6

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">qdd</span>
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
| 空载转速 (rpm) | 270 |
| 质量 (kg) | 0.42 |
| 转子惯量 (kg·m²) | — |
| 外径 (mm) | 92 |
| 长度 (mm) | 42 |
| 额定电压 (V) | — |
| 转矩常数 (N·m/A) | — |

<div class="part-src">
来源：<a href="https://techshare.co.jp/faq/wp-content/uploads/2023/12/GO-M8010-6_Motor_Data_User_Manual_V1.0.pdf">https://techshare.co.jp/faq/wp-content/uploads/2023/12/GO-M8010-6_Motor_Data_User_Manual_V1.0.pdf</a><br/>
收录：Draft actuator_catalog.json（114 行总体）<br/>
核对：2026-10-01
</div>

</div>

<div class="part-comm">
<PartRating part-id="unitree-go-m8010-6" />
</div>

</div>
  </div>
</div>

::: warning 来源冲突
这份数据的来源之间有分歧，未经覆盖，写在下方「备注」里。
:::

## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **腿尖速度上限** —— 空载 270 rpm ≈ 28.3 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 11.3 m/s；实际打 6 折再定目标速度。
- **额定扭矩未知怎么办** —— 只有峰值。按厂商惯例不要假设「额定 = 峰值/2」——有的件是 3:1，有的只有 1.2:1。先向厂商要额定值再做热设计。
- **准直驱要配好电流环** —— 减速比只有 6.33，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">56 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">—</span><span class="pm-note">缺额定扭矩；不要假设它等于峰值的一半</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">28.3 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| 扭矩口径 | peak |
| 空载转速 (rpm) | 270 |
| 额定转速 (rpm) | — |
| 减速比 | 6.33 |
| 质量 (kg) | 0.42 |
| 外径 (mm) | 92 |
| 长度 (mm) | 42 |
| 转子惯量 (kg·m²) | — |
| 惯量口径 | — |
| 转子惯量 (kg·m²) | — |
| 额定电压 (V) | — |
| 电压范围 (V) | — |
| 转矩常数 (N·m/A) | — |
| 相电阻 (Ω) | — |
| 相电感 (µH) | — |
| 极对数 | — |
| 峰值电流 (A) | — |
| 额定电流 (A) | — |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | — |
| 通信 | — |
| 内置驱动 | — |
| 防护等级 | — |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **490 元**（原价 1500 元）
   - 活动：GO-M8010-6 首次购买特价
   - 资格与条件：首次购买可享 490 元/个（限购 2 个，原价 1500 元/个）。需在商品页选择对应规格或咨询客服。
   - 有效期：至 2027-12-31
   - 链接：天猫 Unitree 宇树旗舰店
   - 来源：天猫 Unitree 宇树旗舰店商品页（2026-10-28）
:::

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://techshare.co.jp/faq/wp-content/uploads/2023/12/GO-M8010-6_Motor_Data_User_Manual_V1.0.pdf" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>Draft actuator_catalog.json（114 行总体）</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+GO-M8010-6+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=GO-M8010-6&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%AE%87%E6%A0%91+Unitree+GO-M8010-6+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr></tbody></table>

## 备注

6.33:1, Go1 quadruped 【来源冲突】GO-M8010-6 数据手册 p3 表：重量 约530 g、尺寸 96.5×92.5×42.3 mm、最大扭矩 23.7 N·m、最大转速 30 rad/s@24V、减速比 1:6.33、转矩常数 0.63895 N·m/A；本目录原记录（Unitree 官网）重量为 420 g。重量不一致，未做覆盖。两份手册都只给「最大扭矩」，**没有额定扭矩**。 价格来源：达妙/宇树天猫旗舰店商品页（2026-10-28 抓取，属活动价，可能随活动结束变化）。 产品图待补：抓到的是宇树四足整机宣传图，不是 GO-M8010-6，需厂商型号页原图

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

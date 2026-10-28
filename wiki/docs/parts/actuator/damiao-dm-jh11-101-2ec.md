---
title: 达妙 DAMIAO DM-JH11-101-2EC
---


# 达妙 DAMIAO DM-JH11-101-2EC

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag sub">harmonic</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥1,299</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 10.5 |
| 额定扭矩 (N·m) | 4.8 |
| 减速比 | 101 |
| 空载转速 (rpm) | 30 |
| 质量 (kg) | 0.345 |
| 转子惯量 (kg·m²) | 0.0643 |
| 外径 (mm) | 52 |
| 长度 (mm) | 60 |
| 额定电压 (V) | 48 |
| 转矩常数 (N·m/A) | 5.0904 |

<div class="part-src">
来源：<a href="https://www.hightorque.cn/">https://www.hightorque.cn/</a><br/>
收录：达妙 2026 产品选型表 2026-10-23<br/>
核对：2026-10-27
</div>

</div>

<div class="part-comm">
<PartRating part-id="达妙-dm-dm-jh11-101-2ec" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **仿真里填哪个字段** —— MJCF/URDF 的 armature 字段填 **0.0643**（这是折算到输出端的等效惯量，与电机本体转子惯量差 N² 倍）。不要当转子惯量再乘 N² —— 会差 10201 倍。
- **腿尖速度上限** —— 空载 30 rpm ≈ 3.1 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 1.3 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.2，这个比值正常。连续按 4.8 N·m、瞬时按 10.5 N·m 设计即可。
- **高减速比的代价** —— 减速比 101，反射惯量会被放大。膝关节这类要快速摆动的关节，PD 里 kp 别照抄直驱参数，先用低 kp 高 kd 起步。
- **算你需要多大扭矩** —— 静态站立（两腿支撑）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。
- **报价要自己问** —— 本站没有这个型号的公开价格。同机座不同绕组的价差可能很小，但扭矩差很多 —— 问价时把型号后缀写全。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">30 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.2</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">3.1 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
<div class="pm-row"><span class="pm-k">反射惯量占比</span><span class="pm-v">34%</span><span class="pm-note">假设单腿 2.0 kg、腿长 0.5 m 绕髋摆；占比越高腿越「黏」</span></div>
</div>

::: tip 怎么用这三行
**扭矩密度**决定「同样扭矩下多重」；**峰值/额定比**决定「这个数能信多久」；
**反射惯量占比**决定「这条腿能不能快速摆动」。
三者一起看，比单看峰值扭矩有用得多 —— 高减速比件通常前两项好看、第三项很糟。
:::


## 同机座变体（外径 52 mm）

同一个机座上换绕组 / 换减速比出来的型号。**质量往往一样，扭矩可以差 50% 以上** ——
多出来的扭矩是电流换的，不是尺寸换的，所以别按扭矩去估质量。

| 型号 | 峰值 τ N·m | 质量 kg | 减速比 |
|---|---|---|---|
| [DM-JH11-51-2EC](/parts/actuator/damiao-dm-jh11-51-2ec) | 7.8 | 0.345 | 51 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 10.5 |
| 额定扭矩 (N·m) | 4.8 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 30 |
| 额定转速 (rpm) | 20 |
| 减速比 | 101 |
| 质量 (kg) | 0.345 |
| 外径 (mm) | 52 |
| 长度 (mm) | 60 |
| 转子惯量 (kg·m²) | 6.30e-06 |
| 惯量口径 | rotor |
| 转子惯量 (kg·m²) | 0.0643 |
| 额定电压 (V) | 48 |
| 电压范围 (V) | 20~54 |
| 转矩常数 (N·m/A) | 5.0904 |
| 相电阻 (Ω) | 1.1 |
| 相电感 (µH) | 538 |
| 极对数 | 7 |
| 峰值电流 (A) | 3.6 |
| 额定电流 (A) | 2.3 |
| 摩擦 (N·m) | — |
| 阻尼 (N·m·s/rad) | — |
| 编码器 | 电感，双编 |
| 通信 | CAN、CANFD |
| 内置驱动 | 1 |
| 防护等级 | — |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+%E8%BE%BE%E5%A6%99-dm-dm-jh11-101-2ec&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.hightorque.cn/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙 2026 产品选型表 2026-10-23</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-JH11-101-2EC+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-JH11-101-2EC&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-JH11-101-2EC+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/actuator/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/damiao.json</td></tr></tbody></table>

## 备注

48.0 V 版本；谐波关节电机；额定 4.8 N·m；源文勘误：无 价格来源：达妙/宇树天猫旗舰店商品页（2026-10-28 抓取，属活动价，可能随活动结束变化）。 产品图待补：抓到的是达妙人形整机宣传图，不是 JH11 关节模组，需厂商型号页原图

> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

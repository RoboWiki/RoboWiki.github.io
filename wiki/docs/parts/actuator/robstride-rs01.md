---
title: 灵足 RobStride RS01
description: "灵足 RobStride RS01（关节电机）：峰值扭矩 17 N·m、额定 7 N·m、减速比 7.75:1；来源 A 级、2026-10-31 核对。"
---


# 灵足 RobStride RS01

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/robstride-rs01.jpg" alt="RS01" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">关节电机</span>
      <span class="part-tag soft">准直驱 QDD</span>
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
| 质量 (kg) | 0.38 |
| 转子惯量 (kg·m²) | 4.20e-03 |
| 额定电压 (V) | 36 |

<div class="part-src">
来源：<a href="https://www.robstride.com/">https://www.robstride.com/</a><br/>
收录：灵足时代 RS/EL 系列产品规格介绍（2026.010.09 / 2026.09.22）+ 各型号用户手册（260713 / 261013）<br/>
核对：2026-10-31
</div>

</div>

<div class="part-comm">
<PartRating part-id="灵足-robstride-rs01" :dims='["value", "build", "docs", "spec_trust"]' />
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
- **腿尖速度上限** —— 空载 315 rpm ≈ 33.0 rad/s。腿长 0.4 m 时理论腿尖上限 ≈ 13.2 m/s；实际打 6 折再定目标速度。
- **峰值与额定的用法** —— 峰值/额定 = 2.4，这个比值正常。连续按 7 N·m、瞬时按 17 N·m 设计即可。
- **准直驱要配好电流环** —— 减速比只有 7.75，力矩靠电流直接给。电流环带宽低于 8 kHz 时，触地冲击会明显传到腿上。
- **算你需要多大扭矩** —— 静态站立（四腿支撑，n=4）单关节需求 ≈ 整机质量 × 9.81 × 腿长 / 4；两腿支撑按 /2 估。例：20 kg、腿长 0.4 m → 约 20 N·m 保持扭矩，再乘 1.5–2 的安全系数才是你该选的额定值。


## 选型指标

<div class="pm-table">
<div class="pm-row"><span class="pm-k">扭矩密度</span><span class="pm-v">45 N·m/kg</span><span class="pm-note">>120 需复核，>200 不可信（受磁钢与散热限制）</span></div>
<div class="pm-row"><span class="pm-k">峰值/额定比</span><span class="pm-v">2.4</span><span class="pm-note">>3 须给持续时间与初始温度，>5 基本等同堵转</span></div>
<div class="pm-row"><span class="pm-k">空载角速度 ω</span><span class="pm-v">33.0 rad/s</span><span class="pm-note">× 腿长 = 腿尖速度上限</span></div>
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
| [RS02](/parts/actuator/robstride-rs02) | 17 | 0.38 | 7.75 |

## 全部参数

| 字段 | 值 |
|---|---|
| 峰值扭矩 (N·m) | 17 |
| 额定扭矩 (N·m) | 7 |
| 减速比 | 7.75 |
| 质量 (kg) | 0.38 |
| 转子惯量 (kg·m²) | 4.20e-03 |
| 额定电压 (V) | 36 |
| 扭矩口径 | peak |
| 空载转速 (rpm) | 315 |
| 额定转速 (rpm) | 100 |
| 外径 (mm) | 79 |
| 长度 (mm) | 45.5 |
| 转子惯量 (kg·m²) | 6.99e-05 |
| 惯量口径 | output |
| 电压范围 | 24-48V |
| 转矩常数 (N·m/A) | 1.22 |
| 相电阻 (Ω) | 0.55 |
| 相电感 (µH) | 486 |
| 极对数 | 14 |
| 峰值电流 (A) | 23 |
| 额定电流 (A) | 7 |
| 编码器 | 1 pc |
| 通信 | CAN |
| 内置驱动 | 1 |
| 官方手册 (PDF) | https://raw.githubusercontent.com/RobStride/Product_Information/main/Product%20Literature/CAN2.0/RS01/RS01User%20Manual260713.pdf |
| 官方文档 | https://www.robstride.com/ |

## 优惠与获取条件

::: warning 优惠需要资格，不是人人都能拿到
下面每条的资格都写明。原价与优惠价并列展示，**不划掉原价** —— 资格不满足时按原价算预算。

1. **539 元**（原价 599 元）
   - 活动：灵足教育优惠：一律 9 折
   - 资格与条件：学生证或其他教育证明均可，联系官方客服改价后下单；适用于灵足 RS 全系。**EL05 因成本原因不参与该优惠**（官方口径）。是否与其它活动叠加请与客服确认。
   - 有效期：至 2027-12-31
   - 链接：灵足时代官方客服
   - 来源：灵足官方（用户确认）
:::

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/RoboWiki/RoboWiki.github.io/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+%E7%81%B5%E8%B6%B3-robstride-rs01&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.robstride.com/" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td><a href="https://raw.githubusercontent.com/RobStride/Product_Information/main/Product%20Literature/CAN2.0/RS01/RS01User%20Manual260713.pdf" target="_blank" rel="noopener">官方手册 / 数据手册 (PDF)</a></td><td>参数的值以这份为准</td></tr><tr><td class="rs-plain">产品图出处</td><td>灵足官网产品图（robstride.com 导航菜单图，透明底）</td></tr><tr><td class="rs-plain">收录说明</td><td>灵足时代 RS/EL 系列产品规格介绍（2026.010.09 / 2026.09.22）+ 各型号用户手册（260713 / 261013）</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS01+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RS01&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E7%81%B5%E8%B6%B3+RobStride+RS01+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/RoboWiki/RoboWiki.github.io/edit/main/data/catalog/actuator/lingzu-robstride.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/actuator/lingzu-robstride.json</td></tr></tbody></table>

## 备注

CAN 2.0 版本；官方手册（260713）给空载 315 rpm、电压范围 24–48 V，已按官方口径修正；旧值 275 rpm / 15–48 V 来自第三方镜像，不再采用。价格为历史记录参考价（2026-10-31 未复核）。



> 字段修正走「提案 → 审核 → PR → data release」；每次改动的旧值、新值与依据都留在提案与 git 历史里。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

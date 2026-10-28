---
title: 大疆 DJI RoboMaster 开发板 C 型
---


# 大疆 DJI RoboMaster 开发板 C 型

<div class="part-hero">
  <div class="part-hero-left">
    <img src="/parts/dji-rm-board-c.jpg" alt="RoboMaster 开发板 C 型" class="part-photo" />

  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">下位机</span>
      <span class="part-tag sub">mcu</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag muted">无公开报价</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| MCU | STM32（手册未注明具体型号，常见资料为 STM32F407IGH6） |
| CAN 路数 | 2 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | CAN1×2 + CAN2×2｜UART×2｜PWM×7｜DBUS×1｜USB(micro, DFU)×1｜SWD×1｜BOOT×1｜5V 激光口×1｜24V 输出×1｜可配置 IO(I²C/SPI)｜数字摄像头 FPC 18-pin×1 |

<div class="part-src">
来源：<a href="https://www.robomaster.com/zh-CN/products/components/general/development-board-type-c">https://www.robomaster.com/zh-CN/products/components/general/development-board-type-c</a><br/>
收录：《RoboMaster 开发板 C 型用户手册》(2020) 特征参数页 + 官方产品页技术参数<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="dji-rm-board-c" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **总线够不够** —— 2 路 CAN。12 个关节 × 1 kHz 反馈，单路 CAN 2.0 会吃紧，优先 FD 或多路分载。



## 全部参数

| 字段 | 值 |
|---|---|
| MCU | STM32（手册未注明具体型号，常见资料为 STM32F407IGH6） |
| CAN 路数 | 2 |
| CAN-FD | 0 |
| 电流环 (kHz) | — |
| 接口 | CAN1×2 + CAN2×2｜UART×2｜PWM×7｜DBUS×1｜USB(micro, DFU)×1｜SWD×1｜BOOT×1｜5V 激光口×1｜24V 输出×1｜可配置 IO(I²C/SPI)｜数字摄像头 FPC 18-pin×1 |
| 额定电压 (V) | 24 |
| 电压范围 | 8–28 V |
| 质量 (kg) | 0.038 |
| 尺寸 | 60×41×16.3 mm |
| 工作温度 | 0–55 ℃ |
| PWM 路数 | 7 |
| UART 路数 | 2 |
| 板载 IMU | 六轴 IMU + 磁力计 |
| 保护 | 防反接 / 防过压 / 硅胶外壳 |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+dji-rm-board-c&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://www.robomaster.com/zh-CN/products/components/general/development-board-type-c" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">产品图出处</td><td>RoboMaster 开发板 C 型用户手册 第 3 页接口线稿</td></tr><tr><td class="rs-plain">收录说明</td><td>《RoboMaster 开发板 C 型用户手册》(2020) 特征参数页 + 官方产品页技术参数</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+RoboMaster+%E5%BC%80%E5%8F%91%E6%9D%BF+C+%E5%9E%8B+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=RoboMaster+%E5%BC%80%E5%8F%91%E6%9D%BF+C+%E5%9E%8B&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E5%A4%A7%E7%96%86+DJI+RoboMaster+%E5%BC%80%E5%8F%91%E6%9D%BF+C+%E5%9E%8B+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/controller_low/dji.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/controller_low/dji.json</td></tr></tbody></table>

## 备注

RM 生态的小板：比 A 型便宜更小，常用来带云台/拨弹。**CAN 是 2 条总线、4 个接口**（CAN1 两个 2-pin、CAN2 两个 4-pin），布线按接口数算。24V 输入带防反接与过压保护，5V 口专门给激光。手册未注明 MCU 具体型号，只写「高性能 STM32」——常见资料为 STM32F407IGH6，本站不替厂商补型号。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

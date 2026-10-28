---
title: 达妙 DAMIAO DM-IMU-L1
---


# 达妙 DAMIAO DM-IMU-L1

<div class="part-hero">
  <div class="part-hero-left">
    
  </div>
  <div class="part-hero-right">
    <div class="part-tags">
      <span class="part-tag">IMU</span>
      <span class="part-tag soft">IMU 模组</span>
      <span class="part-tag tierA">来源 A ✓ 已核对</span>
      <span class="part-tag">¥59</span>
    </div>

<div class="part-split">
<div class="part-official">

#### 官方参数

| 字段 | 值 |
|---|---|
| ODR (Hz) | 1000 |
| 陀螺量程 (°/s) | 2000 |
| 加计量程 (g) | 6 |
| 接口 | USB、RS485、CAN |
| 额定电压 (V) | — |

<div class="part-src">
来源：<a href="https://item.taobao.com/item.htm?id=984622435559">https://item.taobao.com/item.htm?id=984622435559</a><br/>
收录：达妙科技 DM-IMU-L1 六轴 IMU 模块使用说明书 V1.2（2025-12-05）+ 达妙科技企业店商品页核对（2026-10-28）<br/>
核对：2026-10-28
</div>

</div>

<div class="part-comm">
<PartRating part-id="sens-damiao-dm-imu-l1" />
</div>

</div>
  </div>
</div>


## 使用建议

::: warning 按参数推断，不是实测
下面每条都是由这个型号的字段算出来的（公式写在句子里）。
真正的使用经验只能来自用过的人 —— 请写在页尾的讨论里。
:::

- **ODR 与带宽** —— ODR 1000 Hz。四足触地冲击的主要能量在 100–300 Hz，采样要够但别忘低通。
- **装在哪里** —— 尽量远离电机与减速器，或做温补 —— 四足跑久了 IMU 附近升温会有零偏漂移。



## 全部参数

| 字段 | 值 |
|---|---|
| ODR (Hz) | 1000 |
| 陀螺量程 (°/s) | 2000 |
| 加计量程 (g) | 6 |
| 接口 | USB、RS485、CAN |
| 额定电压 (V) | — |
| 电压范围 | 5–28 |
| power_w | 0.47 |
| size_mm | 36×26×9 |
| weight_g | 11.5 |
| 分辨率 | 16-bit（BMI088） |
| doc_url | https://github.com/OpenDogeRobotics/OpenDoge_hardware/tree/main/datasheets/dm-imu |
| doc_pdf | https://cdn.jsdelivr.net/gh/OpenDogeRobotics/OpenDoge_hardware@main/datasheets/dm-imu/%E8%BE%BE%E5%A6%99%E7%A7%91%E6%8A%80DM-IMU-L1%E5%85%AD%E8%BD%B4IMU%E6%A8%A1%E5%9D%97%E4%BD%BF%E7%94%A8%E8%AF%B4%E6%98%8E%E4%B9%A6V1.2.pdf |
| repo_urls | https://github.com/OpenDogeRobotics/OpenDoge_hardware |

## 优惠与获取条件

暂无优惠信息。本站不代理销售，也不收佣金 —— 有合作或团购价请提 issue，写清**价格 + 覆盖范围 + 资格条件 + 有效期**，缺一项都不上卡片。

## 使用者实测

还没有人报过这个件的实测。有的是「参数好看」，缺的是「跑了多久、坏没坏」。

<a class="rt-btn" href="https://github.com/zeitvex/RoboSelect/issues/new?template=review-part.yml&title=%5B%E5%AE%9E%E6%B5%8B%5D+sens-damiao-dm-imu-l1&labels=review" target="_blank" rel="noopener">提交实测</a>

需要 GitHub 账号，30 秒填完：装了多大负载、跑了多久、温升多少、坏没坏。
**坏过的经验最值钱** —— 那正是下一个人最想知道的。

## 资料与链接

<table class="rs-table"><thead><tr><th>资料</th><th>说明</th></tr></thead><tbody><tr><td><a href="https://item.taobao.com/item.htm?id=984622435559" target="_blank" rel="noopener">官方页面 / 数据出处</a></td><td>本页数字的出处</td></tr><tr><td class="rs-plain">收录说明</td><td>达妙科技 DM-IMU-L1 六轴 IMU 模块使用说明书 V1.2（2025-12-05）+ 达妙科技企业店商品页核对（2026-10-28）</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-IMU-L1+datasheet" target="_blank" rel="noopener">datasheet 检索</a></td><td>厂商常把 PDF 放在产品页附件里</td></tr><tr><td><a href="https://github.com/search?q=DM-IMU-L1&type=repositories" target="_blank" rel="noopener">SDK / 驱动检索</a></td><td>找现成的 CAN 驱动与示例</td></tr><tr><td><a href="https://www.google.com/search?q=%E8%BE%BE%E5%A6%99+DAMIAO+DM-IMU-L1+%E4%BB%B7%E6%A0%BC" target="_blank" rel="noopener">价格与货期检索</a></td><td>本站不卖货，报价请向厂商确认</td></tr><tr><td><a href="/semantics" target="_blank" rel="noopener">本站口径说明</a></td><td>这些字段什么意思、缺了代表什么</td></tr><tr><td><a href="https://github.com/zeitvex/RoboSelect/edit/main/data/catalog/imu/damiao.json" target="_blank" rel="noopener">在 GitHub 上编辑这条数据</a></td><td>文件 data/catalog/imu/damiao.json</td></tr></tbody></table>

## 备注

六轴 IMU 模组，内置 Bosch BMI088（三轴陀螺 + 三轴加速度计），板载加热恒温控制与 EKF 四元数姿态解算，主控 200 MHz。姿态指标（校准后、室温 25 °C 一小时零漂）：横滚 0.02°、俯仰 0.064°、航向 12.686°，量程分别为 ±180°/±90°/±180°。加速度计 ±6 g、零偏 20 mg、非线性 ±0.5 %FS、带宽 230 Hz；陀螺 ±2000 °/s、零偏 ±1 °/s、非线性 ±0.05 %FS、带宽 116 Hz；加速度/角速度原始指标来自 BMI088 数据手册，模组只做校准不做滤波。输出频率 100–1000 Hz 可调；CAN 默认 1 Mbps，可配 1M/500k/400k/250k/200k/100k/50k/25k；RS485 最高 4 Mbps；USB 为虚拟串口。输入 5–28 V，24 V 稳态 0.47 W、升温阶段 2.5 W，5 V 约 0.34 W。说明书未标注工作温度范围与噪声密度，故留空。价格来源：达妙科技企业店淘宝商品页（2026-10-28，标价 ¥59，活动价可能变化）；商品页需登录查看，公开列表页可核对标题与价格。



> 每个数字都能在后台查到「谁在什么时候、凭什么改成了现在这样」（`part_edits` 表）。
> 缺的字段一律写 `—`，不猜、不用同类填补、不用额定代替峰值。

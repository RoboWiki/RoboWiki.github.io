---
title: 电源 / 分电模块
---


# 电源 / 分电模块

开源硬件 · 共 **7** 型。

## 产品图

<div class="part-gallery">
<a class="part-gallery-card" href="/parts/open_hw/qmini"><span class="part-gallery-img"><img src="/parts/oshw-birdd-qmini-power-board.webp" alt="鸟哥 Qmini 关节电机电源转换分电板" loading="lazy" decoding="async" /></span><span class="part-gallery-model">Qmini 关节电机电源转换分电板</span><span class="part-gallery-meta">电源 / 分电模块 · ¥60</span></a>
<a class="part-gallery-card" href="/parts/open_hw/fengl-mp2980-buck-boost"><span class="part-gallery-img"><img src="/parts/oshw-fengl-mp2980-ultra-buckboost.webp" alt="fengl MP2980 超小 BUCK-BOOST 升降压模块" loading="lazy" decoding="async" /></span><span class="part-gallery-model">MP2980 超小 BUCK-BOOST 升降压模块</span><span class="part-gallery-meta">电源 / 分电模块 · ¥55</span></a>
<a class="part-gallery-card" href="/parts/open_hw/linxiwei-robocon-mp2980"><span class="part-gallery-img"><img src="/parts/oshw-linxiwei-mp2980-robocon-psu.webp" alt="linxiwei ROBOCON 算力设备供电模块（MP2980）" loading="lazy" decoding="async" /></span><span class="part-gallery-model">ROBOCON 算力设备供电模块（MP2980）</span><span class="part-gallery-meta">电源 / 分电模块 · ¥60</span></a>
<a class="part-gallery-card" href="/parts/open_hw/oneasone-lm5148-48v-24v"><span class="part-gallery-img"><img src="/parts/oshw-oneasone-lm5148-48-24.webp" alt="oneasone LM5148 48V-24V 降压模块" loading="lazy" decoding="async" /></span><span class="part-gallery-model">LM5148 48V-24V 降压模块</span><span class="part-gallery-meta">电源 / 分电模块 · ¥40</span></a>
<a class="part-gallery-card" href="/parts/open_hw/robotic-robocon"><span class="part-gallery-img"><img src="/parts/oshw-roboticlib-pdb.webp" alt="RobotIC 机器人实验室 ROBOCON 无缝换电分电板" loading="lazy" decoding="async" /></span><span class="part-gallery-model">ROBOCON 无缝换电分电板</span><span class="part-gallery-meta">电源 / 分电模块</span></a>
<a class="part-gallery-card" href="/parts/open_hw/robotic-mp2980"><span class="part-gallery-img"><img src="/parts/oshw-roboticlib-mp2980-pc-psu.webp" alt="RobotIC 机器人实验室 MP2980 电脑供电模块" loading="lazy" decoding="async" /></span><span class="part-gallery-model">MP2980 电脑供电模块</span><span class="part-gallery-meta">电源 / 分电模块</span></a>
</div>

> 7 型中 6 款有可核实的产品图；其余不配图凑数，出处见各型号页。

| 型号 | 子类 | 输入 | 输出 | 电流 | 接口 | 价格 ¥ | 来源 |
|---|---|---|---|---|---|---|---|
| [**ROBOCON 无缝换电分电板**](/parts/open_hw/robotic-robocon) | 电源 / 分电模块 | 12~24 V（3~6S 锂电） | 随电池电压（6 路直出） | 12 A（建议；芯片上限 15 A） | 2× 电池输入；6× 电源输出（4× VOUT + 2× 保险丝） | — | `A✓` |
| [**MP2980 电脑供电模块**](/parts/open_hw/robotic-mp2980) | 电源 / 分电模块 | 6~36 V（页面摘要；封面标 24 V 输入） | 19 V（封面；页面摘要写 19.5 V） | 12.5 A 连续（页面摘要写 13 A） | 独立高侧开关；输入/输出直接焊线 | — | `A✓` |
| [**MP2980 超小 BUCK-BOOST 升降压模块**](/parts/open_hw/fengl-mp2980-buck-boost) | 电源 / 分电模块 | 6~36 V（板载 26 V TVS） | 0.5~28 V 可调 | 10 A 最大（受 MOS、散热和限流采样电阻限制） | XT30 输入/输出 | 55 | `A✓` |
| [**TPS5450DDAR 可调降压电源模块**](/parts/open_hw/huashuo0804-tps5450ddar) | 电源 / 分电模块 | 10~31 V 推荐（芯片 5.5~36 V） | 1.221~31.32 V 可调 | 4 A 设计；5 A 最大（峰值 6 A） | 6P 2.54 mm 排针（输入/输出） | 5 | `A✓` |
| [**ROBOCON 算力设备供电模块（MP2980）**](/parts/open_hw/linxiwei-robocon-mp2980) | 电源 / 分电模块 | 22~26 V 建议（17 V 可 boost 维持 19 V） | 19 V | 10 A 连续（13.74 A 平均限流） | 独立高侧开关；输入/输出指示灯；外接调试接口 | 60 | `A✓` |
| [**LM5148 48V-24V 降压模块**](/parts/open_hw/oneasone-lm5148-48v-24v) | 电源 / 分电模块 | 30~60 V | 24 V | 15 A 连续以上；输出可到 20 A 以上 | 输入/输出焊盘；可选 XT60 | 40 | `A✓` |
| [**Qmini 关节电机电源转换分电板**](/parts/open_hw/qmini) | 电源 / 分电模块 | 24 V | 24 V 直出；12 V；5 V | — | 4× RS-485 独立输入；4× 24 V 关节电机输出；12 V / 5 V 降压输出 | 60 | `A✓` |

> 来源等级见行末徽章：`A` = 逐项核对过官方手册，`B` = 公开网页，`C` = 转述线索。采购前请回原厂页面确认。

## 这一页的讨论

用过的、量到的、和厂商确认过的，写在下面。**带上具体工况**（负载、占空比、环境温度），
只写「好用/不好用」对下一个人没有价值。

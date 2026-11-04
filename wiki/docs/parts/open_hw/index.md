---
title: 开源硬件
---


# 开源硬件

分电 / 稳压 / 储能 / 控制扩展，共 **10** 件、**8** 家厂商。

## 厂商

- [RobotIC 机器人实验室](/parts/open_hw/robotic) —— 3 型
- [fengl](/parts/open_hw/fengl) —— 1 型
- [huashuo0804](/parts/open_hw/huashuo0804) —— 1 型
- [infinite_future](/parts/open_hw/infinite-future) —— 1 型
- [linxiwei](/parts/open_hw/linxiwei) —— 1 型
- [oneasone](/parts/open_hw/oneasone) —— 1 型
- [群星战队](/parts/open_hw/qunxing) —— 1 型
- [鸟哥](/parts/open_hw/birdd) —— 1 型

## 全部型号

| 型号 | 子类 | 输入 | 输出 | 电流 | 接口 | 价格 ¥ | 来源 |
|---|---|---|---|---|---|---|---|
| [**ROBOCON 无缝换电分电板**](/parts/open_hw/robotic-robocon) | 电源 / 分电模块 | 12~24 V（3~6S 锂电） | 随电池电压（6 路直出） | 12 A（建议；芯片上限 15 A） | 2× 电池输入；6× 电源输出（4× VOUT + 2× 保险丝） | — | `A✓` |
| [**ROBOCON 常备 STM32 主控扩展板**](/parts/open_hw/robotic-robocon-stm32) | 控制 / 扩展板 | 12 V | 5 V / 3.3 V | — | PWM / UART / CAN / IIC / SPI / ADC / ESP01S | — | `A✓` |
| [**MP2980 电脑供电模块**](/parts/open_hw/robotic-mp2980) | 电源 / 分电模块 | 6~36 V（页面摘要；封面标 24 V 输入） | 19 V（封面；页面摘要写 19.5 V） | 12.5 A 连续（页面摘要写 13 A） | 独立高侧开关；输入/输出直接焊线 | — | `A✓` |
| [**MP2980 超小 BUCK-BOOST 升降压模块**](/parts/open_hw/fengl-mp2980-buck-boost) | 电源 / 分电模块 | 6~36 V（板载 26 V TVS） | 0.5~28 V 可调 | 10 A 最大（受 MOS、散热和限流采样电阻限制） | XT30 输入/输出 | 55 | `A✓` |
| [**TPS5450DDAR 可调降压电源模块**](/parts/open_hw/huashuo0804-tps5450ddar) | 电源 / 分电模块 | 10~31 V 推荐（芯片 5.5~36 V） | 1.221~31.32 V 可调 | 4 A 设计；5 A 最大（峰值 6 A） | 6P 2.54 mm 排针（输入/输出） | 5 | `A✓` |
| [**RoboMaster C 型控制板（仿制版）**](/parts/open_hw/infinite-future-robomaster-c) | 控制 / 扩展板 | — | — | 5 A（舵机电源） | 6× UART；2× CAN（8 接口）；I2C；D-Bus；USB | 50 | `B` |
| [**ROBOCON 算力设备供电模块（MP2980）**](/parts/open_hw/linxiwei-robocon-mp2980) | 电源 / 分电模块 | 22~26 V 建议（17 V 可 boost 维持 19 V） | 19 V | 10 A 连续（13.74 A 平均限流） | 独立高侧开关；输入/输出指示灯；外接调试接口 | 60 | `A✓` |
| [**LM5148 48V-24V 降压模块**](/parts/open_hw/oneasone-lm5148-48v-24v) | 电源 / 分电模块 | 30~60 V | 24 V | 15 A 连续以上；输出可到 20 A 以上 | 输入/输出焊盘；可选 XT60 | 40 | `A✓` |
| [**RM2024 7S3V1890J 超级电容组**](/parts/open_hw/rm2024-7s3v1890j) | 超级电容 | 21 V（7S，单体 3 V） | 21 V | — | 7S 电容组（含被动均衡与 NTC） | 120 | `A✓` |
| [**Qmini 关节电机电源转换分电板**](/parts/open_hw/qmini) | 电源 / 分电模块 | 24 V | 24 V 直出；12 V；5 V | — | 4× RS-485 独立输入；4× 24 V 关节电机输出；12 V / 5 V 降压输出 | 60 | `A✓` |

> 来源等级见行末徽章：`A` = 逐项核对过官方手册，`B` = 公开网页，`C` = 转述线索。采购前请回原厂页面确认。

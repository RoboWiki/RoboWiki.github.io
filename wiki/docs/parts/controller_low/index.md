---
title: 下位机
image: "/og-default.png"
---


# 下位机

底层控制 / 电机驱动，共 **11** 件、**10** 家厂商。

## 厂商

- [MIT Biomimetics Robotics Lab](/parts/controller_low/mit-biomimetics) —— 1 型
- [ODrive Robotics](/parts/controller_low/odrive) —— 1 型
- [PJRC](/parts/controller_low/pjrc) —— 1 型
- [STMicroelectronics](/parts/controller_low/st-2) —— 1 型
- [SimpleFOC Team](/parts/controller_low/simplefoc) —— 1 型
- [VESC Labs](/parts/controller_low/vesc) —— 1 型
- [mjbots](/parts/controller_low/mjbots) —— 1 型
- [大疆 DJI](/parts/controller_low/dji-robomaster) —— 2 型
- [灯哥开源 ToanTech](/parts/controller_low/dengfoc) —— 1 型
- [达妙 DAMIAO](/parts/controller_low/damiao) —— 1 型

## 全部型号

| 型号 | MCU | FOC 轴数 | CAN | 电流环 kHz | 最高 V | 价格 ¥ | 来源 |
|---|---|---|---|---|---|---|---|
| [**3phase_integrated**](/parts/controller_low/mit-biomimetics-robotics-lab-3phase-integrated) | STM32F446RET6 | 1 | 1 | 40 | 35 | — | `A✓` |
| [**ODrive S1**](/parts/controller_low/odrive-robotics-odrive-s1) | — | 1 | 1 FD | — | 50.5 | — | `A✓` |
| [**Teensy 4.1**](/parts/controller_low/pjrc-teensy-4-1) | i.MX RT1062（Arm Cortex-M7） | — | 3 FD | — | — | — | `A✓` |
| [**B-G431B-ESC1**](/parts/controller_low/stmicroelectronics-b-g431b-esc1) | STM32G431CBU6 | 1 | 1 | — | 26 | — | `A✓` |
| [**SimpleFOC Mini V2.3**](/parts/controller_low/simplefoc-team-simplefoc-mini-v2-3) | — | 1 | — | — | 35 | — | `A✓` |
| [**VESC Classic 100V**](/parts/controller_low/vesc-labs-vesc-classic-100v) | STM32F405 | 1 | 1 | — | 100 | — | `A✓` |
| [**moteus r4.11**](/parts/controller_low/mjbots-moteus-r4-11) | STM32G4（170 MHz，官方未注明具体型号） | 1 | 1 FD | — | 44 | — | `A✓` |
| [**RoboMaster 开发板 A 型**](/parts/controller_low/dji-robomaster-a) | STM32F427IIH6 | — | 2 | — | 26 | 429 | `A✓` |
| [**RoboMaster 开发板 C 型**](/parts/controller_low/dji-robomaster-c) | STM32（手册未注明具体型号，常见资料为 STM32F407IGH6） | — | 2 | — | 28 | 379 | `A✓` |
| [**DengFOC V3.0**](/parts/controller_low/toantech-dengfoc-v3-0) | ESP32（Lolin32 Lite） | 2 | — | — | 24 | — | `A✓` |
| [**DM-MC-Board02**](/parts/controller_low/damiao-dm-mc-board02) | STM32H723VGT6 | — | 3 FD | — | 24 | 199 | `A✓` |

> 来源等级见行末徽章：`A` = 逐项核对过官方手册，`B` = 公开网页，`C` = 转述线索。采购前请回原厂页面确认。

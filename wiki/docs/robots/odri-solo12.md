---
title: Solo 12
---

# Open Dynamic Robot Initiative Solo 12

![Solo 12](/parts/odri-solo12.jpg)

开源力矩控制四足，12 自由度、整机 2.5 kg（官方硬件 README 标注）。v1 没有板载电池与无线通信，需要外接电源和以太网；v1.1 才加板载电池与无线。官方仓库只提供 xacro 模板（solo12.urdf.xacro + leg.xacro），由 robot_properties_solo 生成 URDF，没有预生成文件。官方未公布最高速度、负载、整机尺寸与续航，均留空；PAL Robotics 曾代理整机套件，官网已标注销售停止。

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 12 |
| 整机质量 (kg) | 2.5 |
| 对外接口 | 以太网；机身引出供电线（v1 无板载电池） |
| 算力平台 | Master Board + 12× Micro Driver Board |
| 传感器 | Lord Microstrain 3DM-CX5-25 IMU |
| 官方文档 | https://github.com/open-dynamic-robot-initiative/open-dynamic-robot-initiative.github.io/wiki |

## 链接

- 官方文档：<https://github.com/open-dynamic-robot-initiative/open-dynamic-robot-initiative.github.io/wiki>
- URDF：<https://github.com/open-dynamic-robot-initiative/robot_properties_solo/tree/master/src/robot_properties_solo/resources/xacro>
- 仓库：<https://github.com/open-dynamic-robot-initiative/robot_properties_solo> —— 许可 BSD-3-Clause
- 仓库：<https://github.com/open-dynamic-robot-initiative/robot_interfaces_solo> —— 许可 BSD-3-Clause

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：ODRI 官方硬件仓库 README + PAL Robotics Solo12 页面核对（2026-10-28） · 等级 A · 核对 2026-10-28

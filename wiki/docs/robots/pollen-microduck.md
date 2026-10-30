---
title: Microduck
---

# Pollen Robotics（法国） Microduck

![Microduck](/parts/pollen-microduck.jpg)

## 简介

<div class="rb-intro">
<p>Pollen Robotics 的小型开源双足：14 自由度（每腿 5 + 颈部 1 + 头部 3，按官方 MJCF 执行器数）、约 0.8 kg、高 25 cm，随机附带若干已训练动作，策略在机载 50 Hz 运行，传感器为相机 + 激光雷达 + 双 IMU，配套游戏手柄与 USB-C 充电。</p>
<p>官网定价 US$399（2026-10-28 的 introductory price，税前不含运费，可能变化），price_cny 未折算故留空。</p>
<p>官方只发布 MuJoCo MJCF（microduck_rl），没有 URDF；负载、速度、电池容量与续航未公开，均留空。</p>
</div>

## 关键参数

| 字段 | 值 |
|---|---|
| 自由度 | 14 |
| 整机质量 (kg) | 0.8 |
| 尺寸 (mm) | 250（高） |
| 对外接口 | USB-C 充电；游戏手柄遥控 |
| 算力平台 | 板载策略推理，控制频率 50 Hz |
| 传感器 | 相机、激光雷达、双 IMU |

## 开源生态

<em>生态来自本地参考库的项目索引（8 个项目 / 角色由我们按项目定位标注）。
只说明「哪些环节有现成开源实现」，不代表这些项目都能直接跑在这台机器上。</em>

<div class="rb-roles"><span class="rb-role"><b>仿真</b>2</span> <span class="rb-role"><b>训练</b>3</span> <span class="rb-role"><b>工具/资料</b>3</span></div>

**仿真**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/pollen-robotics/microduck_rl" target="_blank" rel="noopener">microduck_rl</a> | MicroDuck 官方 RL 训练栈（MuJoCo + PPO；7 套出厂动作与 ONNX 部署）——2026-10-19 更新到最新快照 | 199 |
| <a href="https://huggingface.co/spaces/pollen-robotics/microduck-simulator" target="_blank" rel="noopener">microduck-simulator</a> | MicroDuck 仿真器 | 57 |

**训练**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/Farama-Foundation/Gymnasium" target="_blank" rel="noopener">Gymnasium</a> | Farama RL 环境标准 API（Env/Space/Wrapper/Vector）——训练适配器协议与环境接口设计参考 | 457 |
| <a href="https://github.com/zj281136/microduck-s288" target="_blank" rel="noopener">microduck-s288</a> | MicroDuck S288 社区复刻：结构/电控/标定/RL 训练/真机部署 + 预训练 ONNX 与中文教程 | 158 |

**工具/资料**（2 个）

| 项目 | 说明 | 文件数 |
|---|---|---|
| <a href="https://github.com/pollen-robotics/microduck" target="_blank" rel="noopener">microduck</a> | MicroDuck 板载运行时：Rust 50 Hz 控制环、BLE、WebRTC/摄像头、ToF 与硬件规格 | 461 |
| <a href="https://github.com/microai-lab/microduck-studio" target="_blank" rel="noopener">microduck-studio</a> | MicroDuck Studio（编辑/可视化） | 26 |

## 链接

- URDF：<https://github.com/pollen-robotics/microduck_rl/tree/main/src/mjlab_microduck/robot/microduck>
- 仓库：<https://github.com/pollen-robotics/microduck>
- 仓库：<https://github.com/pollen-robotics/microduck_rl>

::: tip 进仿真（接口已留）
「进仿真」按钮先留着接口，**暂未接入**。上面的 URDF 链接可以直接下载，
拖进 MuJoCo / Isaac 里用。
:::

> 来源：Pollen Robotics 官网 Microduck 产品页 + 官方 GitHub 仓库与 MJCF 关节数核对（2026-10-28） · 等级 A · 核对 2026-10-28

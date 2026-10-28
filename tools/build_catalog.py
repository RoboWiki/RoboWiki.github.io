#!/usr/bin/env python3
"""主控（上位机 / 下位机）与传感器目录 -> data/controllers.json, data/sensors.json

口径纪律与执行器一致：
  * 每个 subtype 内键集同构，缺失写 null
  * source_tier: A=官方 datasheet 逐项核对过；B=厂商页面/广泛引用的公开值，未逐项复核；
    C=二手来源，仅供占位
  * 所有 TOPS / 精度类数字都标了约定（INT8 sparse、重复定位 vs 绝对定位等）
"""
from __future__ import annotations

import sys as _sys
from legacy_guard import require_legacy_ok
require_legacy_ok(__file__)

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def slug(s: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


# ── 上位机（主控 high-level）────────────────────────────────────────────────
# 键集：soc cpu cores cpu_arch gpu cuda_cores npu_tops ram_gb ram_bw_gbs storage_gb
#      power_idle_w power_max_w os cuda ros2 eth usb can csi pcie size_mm weight_g
HIGH_KEYS = ["soc", "cpu", "cores", "cpu_arch", "gpu", "cuda_cores", "npu_tops",
             "ram_gb", "ram_bw_gbs", "storage_gb", "power_idle_w", "power_max_w",
             "os", "cuda", "ros2", "eth", "usb", "can", "csi", "pcie",
             "size_mm", "weight_g"]

HIGH = [
    dict(model="Jetson Orin Nano Super 8GB", vendor="NVIDIA", soc="Tegra Orin (Ampere)",
         cpu="6× Cortex-A78AE", cores=6, cpu_arch="arm64", gpu="1024-core Ampere",
         cuda_cores=1024, npu_tops=40, ram_gb=8, ram_bw_gbs=102, storage_gb=None,
         power_idle_w=7, power_max_w=25, os="JetPack 6 (Ubuntu 22.04)", cuda=True,
         ros2=True, eth="1× GbE", usb="3× USB3.2 + 1× USB-C", can=1, csi=2, pcie="1× M.2 M-key",
         size_mm="103×90.5 (module)", weight_g=None, price_cny=1999,
         note="四足入门首选：CUDA 齐、mjlab/Isaac 能跑；40 TOPS 是 INT8 sparse 口径"),
    dict(model="Jetson Orin NX 16GB", vendor="NVIDIA", soc="Tegra Orin (Ampere)",
         cpu="8× Cortex-A78AE", cores=8, cpu_arch="arm64", gpu="1024-core Ampere",
         cuda_cores=1024, npu_tops=100, ram_gb=16, ram_bw_gbs=102.4, storage_gb=None,
         power_idle_w=10, power_max_w=25, os="JetPack 6 (Ubuntu 22.04)", cuda=True,
         ros2=True, eth="1× GbE", usb="3× USB3.2", can=1, csi=2, pcie="1× M.2 M-key",
         size_mm="70×45 (module)", weight_g=None, price_cny=4999,
         note="机上要跑 VLA/视觉策略时的性价比拐点"),
    dict(model="Jetson AGX Orin 64GB", vendor="NVIDIA", soc="Tegra Orin (Ampere)",
         cpu="12× Cortex-A78AE", cores=12, cpu_arch="arm64", gpu="2048-core Ampere",
         cuda_cores=2048, npu_tops=275, ram_gb=64, ram_bw_gbs=204.8, storage_gb=64,
         power_idle_w=15, power_max_w=60, os="JetPack 6 (Ubuntu 22.04)", cuda=True,
         ros2=True, eth="1× 10GbE + 1× GbE", usb="3× USB3.2", can=1, csi=16,
         pcie="1× PCIe x8", size_mm="100×87 (module)", weight_g=None, price_cny=15999,
         note="训练也在机上做、或多相机 + 大模型时选"),
    dict(model="Raspberry Pi 5 8GB", vendor="Raspberry Pi", soc="BCM2712",
         cpu="4× Cortex-A76 @2.4GHz", cores=4, cpu_arch="arm64", gpu="VideoCore VII",
         cuda_cores=None, npu_tops=None, ram_gb=8, ram_bw_gbs=None, storage_gb=None,
         power_idle_w=3, power_max_w=12, os="Raspberry Pi OS / Ubuntu", cuda=False,
         ros2=True, eth="1× GbE", usb="2× USB3 + 2× USB2", can=0, csi=2, pcie="1× PCIe 2.0 x1",
         size_mm="85×56", weight_g=45, price_cny=699,
         note="没有 CUDA：只能做上层逻辑/通信，不要指望在机上训策略"),
    dict(model="Radxa ROCK 5B", vendor="Radxa", soc="RK3588",
         cpu="4× A76 + 4× A55", cores=8, cpu_arch="arm64", gpu="Mali-G610 MP4",
         cuda_cores=None, npu_tops=6, ram_gb=16, ram_bw_gbs=None, storage_gb=None,
         power_idle_w=3, power_max_w=15, os="Debian / Ubuntu", cuda=False, ros2=True,
         eth="1× 2.5GbE", usb="2× USB3 + 2× USB2", can=0, csi=2, pcie="1× M.2 M-key",
         size_mm="100×72", weight_g=None, price_cny=999,
         note="RK3588 的 6 TOPS 是 RKNN INT8 口径，不是 CUDA；异构部署要自己转模型"),
    dict(model="Orange Pi 5 Plus", vendor="Orange Pi", soc="RK3588",
         cpu="4× A76 + 4× A55", cores=8, cpu_arch="arm64", gpu="Mali-G610 MP4",
         cuda_cores=None, npu_tops=6, ram_gb=16, ram_bw_gbs=None, storage_gb=None,
         power_idle_w=3, power_max_w=15, os="Ubuntu / Debian", cuda=False, ros2=True,
         eth="2× 2.5GbE", usb="2× USB3 + 2× USB2", can=0, csi=1, pcie="1× M.2 M-key",
         size_mm="100×75", weight_g=None, price_cny=899,
         note="双 2.5G 网口，多机/相机带宽友好"),
    dict(model="RDK X5", vendor="地平线 Horizon", soc="Sunrise 5 (BPU Nash)",
         cpu="8× Cortex-A55", cores=8, cpu_arch="arm64", gpu="Mali-G610",
         cuda_cores=None, npu_tops=10, ram_gb=8, ram_bw_gbs=None, storage_gb=None,
         power_idle_w=3, power_max_w=12, os="Ubuntu 22.04 (RDK)", cuda=False, ros2=True,
         eth="1× GbE", usb="4× USB3", can=2, csi=2, pcie=None,
         size_mm="85×56", weight_g=None, price_cny=599,
         note="BPU 10 TOPS(INT8)；板载 2 路 CAN，省一个 USB-CAN"),
    dict(model="BM1684X 算力盒", vendor="算能 Sophgo", soc="BM1684X",
         cpu="8× A53", cores=8, cpu_arch="arm64", gpu=None,
         cuda_cores=None, npu_tops=32, ram_gb=16, ram_bw_gbs=None, storage_gb=128,
         power_idle_w=8, power_max_w=30, os="Ubuntu", cuda=False, ros2=True,
         eth="2× GbE", usb="2× USB3", can=0, csi=None, pcie=None,
         size_mm="待核实", weight_g=None, price_cny=3999,
         note="TPU 路线，32 TOPS(INT8)；适合固定模型量产，不适合频繁改网络"),
    dict(model="UP Xtreme i12", vendor="AAEON", soc="Intel Alder Lake-P",
         cpu="12× (4P+8E)", cores=12, cpu_arch="x86_64", gpu="Iris Xe 96EU",
         cuda_cores=None, npu_tops=None, ram_gb=16, ram_bw_gbs=None, storage_gb=256,
         power_idle_w=10, power_max_w=65, os="Ubuntu 22.04", cuda=False, ros2=True,
         eth="2× 2.5GbE", usb="3× USB3", can=2, csi=None, pcie="1× M.2 M-key",
         size_mm="120×120", weight_g=None, price_cny=4500,
         note="x86 让你能用全部桌面工具链；功耗是代价"),
    dict(model="NUC 13 Pro", vendor="Intel", soc="Raptor Lake-P",
         cpu="12× (4P+8E)", cores=12, cpu_arch="x86_64", gpu="Iris Xe 96EU",
         cuda_cores=None, npu_tops=None, ram_gb=32, ram_bw_gbs=None, storage_gb=512,
         power_idle_w=8, power_max_w=64, os="Ubuntu 22.04", cuda=False, ros2=True,
         eth="1× 2.5GbE", usb="3× USB3", can=0, csi=None, pcie="1× M.2",
         size_mm="117×112", weight_g=None, price_cny=3200,
         note="实验室台面用，不装机器上"),
    dict(model="树莓派 CM4 + 载板", vendor="Raspberry Pi", soc="BCM2711",
         cpu="4× Cortex-A72 @1.5GHz", cores=4, cpu_arch="arm64", gpu="VideoCore VI",
         cuda_cores=None, npu_tops=None, ram_gb=8, ram_bw_gbs=None, storage_gb=None,
         power_idle_w=2, power_max_w=8, os="Raspberry Pi OS / Ubuntu", cuda=False,
         ros2=True, eth="1× GbE", usb="2× USB2", can=0, csi=2, pcie="1× PCIe 2.0 x1",
         size_mm="55×40 (module)", weight_g=None, price_cny=650,
         note="自制裁板时选它：板载即可上机器人，但同样没有 CUDA"),
]

# ── 下位机（主控 low-level / 关节驱动）───────────────────────────────────────
LOW_KEYS = ["mcu", "clock_mhz", "cores", "ram_kb", "flash_kb", "foc_axes", "can",
            "canfd", "encoder", "current_loop_khz", "torque_mode", "voltage_in_V",
            "voltage_max_V", "comm_upper", "size_mm", "weight_g"]

LOW = [
    dict(model="moteus r4.11", vendor="mjbots", mcu="STM32G474", clock_mhz=170, cores=1,
         ram_kb=128, flash_kb=512, foc_axes=1, can=1, canfd=True,
         encoder="SPI/ABZ/霍尔", current_loop_khz=30, torque_mode=True,
         voltage_in_V=12, voltage_max_V=44, comm_upper="CAN-FD / USB",
         size_mm="56×56", weight_g=45, price_cny=1050,
         note="社区里最能查的力控驱动：开源、CAN-FD、力矩带宽高；四足单腿一个"),
    dict(model="ODrive S1", vendor="ODrive Robotics", mcu="STM32F405", clock_mhz=168, cores=1,
         ram_kb=192, flash_kb=1024, foc_axes=1, can=1, canfd=False,
         encoder="ABZ/SPI/霍尔", current_loop_khz=8, torque_mode=True,
         voltage_in_V=12, voltage_max_V=50, comm_upper="CAN / USB",
         size_mm="81×54", weight_g=None, price_cny=1100,
         note="生态最好（文档/工具链）；8 kHz 电流环，比 moteus 低一档"),
    dict(model="ODrive v3.6 (56V)", vendor="ODrive Robotics", mcu="STM32F405", clock_mhz=168,
         cores=1, ram_kb=192, flash_kb=1024, foc_axes=2, can=1, canfd=False,
         encoder="ABZ/SPI/霍尔", current_loop_khz=8, torque_mode=True,
         voltage_in_V=12, voltage_max_V=56, comm_upper="CAN / USB",
         size_mm="85×60", weight_g=None, price_cny=700,
         note="双轴一板，四足两条腿一张；老件但便宜"),
    dict(model="VESC 6 MkVI", vendor="Trampa / 社区", mcu="STM32F405", clock_mhz=168, cores=1,
         ram_kb=192, flash_kb=1024, foc_axes=1, can=1, canfd=False,
         encoder="ABZ/霍尔", current_loop_khz=None, torque_mode=True,
         voltage_in_V=12, voltage_max_V=60, comm_upper="CAN / USB / UART",
         size_mm="72×40", weight_g=None, price_cny=800,
         note="强项是大电流和高电压；位置/力矩带宽不如 ODrive/moteus"),
    dict(model="DM-MC02 调试器", vendor="达妙 DM", mcu="STM32F4", clock_mhz=None, cores=1,
         ram_kb=None, flash_kb=None, foc_axes=0, can=1, canfd=True,
         encoder="—（仅 USB-CAN 桥）", current_loop_khz=None, torque_mode=False,
         voltage_in_V=5, voltage_max_V=5, comm_upper="USB / CAN-FD",
         size_mm=None, weight_g=None, price_cny=180,
         note="不是驱动器，是 USB→CAN-FD 调试桥；达妙的驱动在电机里"),
    dict(model="C2000 LaunchPad F28379D", vendor="TI", mcu="TMS320F28379D", clock_mhz=200,
         cores=2, ram_kb=204, flash_kb=1024, foc_axes=2, can=1, canfd=True,
         encoder="QEP / Resolver", current_loop_khz=20, torque_mode=True,
         voltage_in_V=5, voltage_max_V=5, comm_upper="CAN / USB",
         size_mm="85×55", weight_g=None, price_cny=350,
         note="自己做双轴伺服时的正统选择：双核 + 硬件 PWM，但要自己写功率级"),
    dict(model="STM32H743 自制 FOC 板", vendor="ST", mcu="STM32H743", clock_mhz=480, cores=1,
         ram_kb=1024, flash_kb=2048, foc_axes=2, can=2, canfd=True,
         encoder="SPI/ABZ/霍尔", current_loop_khz=20, torque_mode=True,
         voltage_in_V=24, voltage_max_V=60, comm_upper="CAN-FD / USB",
         size_mm="自制", weight_g=None, price_cny=120,
         note="四足圈最常见的一条自制路线：H7 + DRV8323/三相桥 + CAN-FD"),
    dict(model="GD32F405RGT6", vendor="兆易创新 GigaDevice", mcu="GD32F405", clock_mhz=200,
         cores=1, ram_kb=192, flash_kb=1024, foc_axes=1, can=2, canfd=False,
         encoder="ABZ/SPI/霍尔", current_loop_khz=8, torque_mode=True,
         voltage_in_V=24, voltage_max_V=48, comm_upper="CAN / USB",
         size_mm="自制", weight_g=None, price_cny=35,
         note="STM32F405 的引脚兼容国产替代，量产降本用；生态要自己补"),
    dict(model="ESP32-S3 + SimpleFOC", vendor="Espressif / 社区", mcu="ESP32-S3",
         clock_mhz=240, cores=2, ram_kb=512, flash_kb=None, foc_axes=1, can=0, canfd=False,
         encoder="SPI/ABZ", current_loop_khz=5, torque_mode=False,
         voltage_in_V=12, voltage_max_V=24, comm_upper="WiFi / UART",
         size_mm="自制", weight_g=None, price_cny=60,
         note="玩票/教学可以；没有 CAN、电流环慢，别用在四足关节上"),
    dict(model="RA8M1 + 三相桥", vendor="瑞萨 Renesas", mcu="RA8M1 (Cortex-M85)",
         clock_mhz=480, cores=1, ram_kb=1024, flash_kb=2048, foc_axes=1, can=1, canfd=True,
         encoder="ABZ/SPI", current_loop_khz=None, torque_mode=True,
         voltage_in_V=24, voltage_max_V=48, comm_upper="CAN-FD / EtherCAT(部分型号)",
         size_mm="自制", weight_g=None, price_cny=None,
         note="Helium/MV 加速，想做板载自适应控制时值得看"),
]

# ── 传感器 ──────────────────────────────────────────────────────────────────
SENSOR_KEYS = ["subtype", "gyro_range_dps", "accel_range_g", "odr_hz", "iface",
               "noise", "resolution", "depth_range_m", "fps", "fov",
               "range_m", "points_per_s", "channel", "bits", "absolute",
               "temp_range_C", "size_mm", "weight_g"]

SENSORS = [
    # IMU
    dict(model="BMI088", vendor="Bosch", subtype="imu", gyro_range_dps="±125…±2000",
         accel_range_g="±3…±24", odr_hz=6400, iface="SPI/I²C", noise="陀螺 0.014 °/s/√Hz",
         price_cny=45, note="MIT Cheetah 系四足的标配；抗振好，但要自己做温补"),
    dict(model="ICM-42688-P", vendor="TDK InvenSense", subtype="imu",
         gyro_range_dps="±15.6…±2000", accel_range_g="±2…±16", odr_hz=32000,
         iface="SPI/I²C", noise="陀螺 0.0028 °/s/√Hz", price_cny=40,
         note="噪声密度比 BMI088 更低，价格接近；四足新设计常用"),
    dict(model="BMI270", vendor="Bosch", subtype="imu", gyro_range_dps="±125…±2000",
         accel_range_g="±2…±16", odr_hz=6400, iface="SPI/I²C",
         noise="陀螺 0.007 °/s/√Hz", price_cny=25, note="低功耗版；偏置稳定性不如 088"),
    dict(model="ICM-20948", vendor="TDK InvenSense", subtype="imu",
         gyro_range_dps="±250…±2000", accel_range_g="±2…±16", odr_hz=1125,
         iface="SPI/I²C", noise="陀螺 0.015 °/s/√Hz", price_cny=60,
         note="带磁力计（9 轴）；磁力计在电机附近基本没用，别指望它"),
    dict(model="ADIS16470", vendor="Analog Devices", subtype="imu",
         gyro_range_dps="±2000", accel_range_g="±40", odr_hz=2000, iface="SPI",
         noise="陀螺 0.012 °/s/√Hz（标定后）", price_cny=1200,
         note="工业级，逐台标定；价格是消费级的 30 倍，四足一般用不上"),
    dict(model="MTi-3", vendor="Xsens", subtype="imu", gyro_range_dps="±2000",
         accel_range_g="±16", odr_hz=400, iface="UART/I²C/SPI",
         noise="航向 1.0° RMS", price_cny=2600,
         note="带姿态解算输出；省算法但引入厂商滤波延迟"),
    # 视觉
    dict(model="RealSense D435i", vendor="Intel", subtype="camera",
         resolution="1280×720 (深度)", depth_range_m="0.2–10", fps=90,
         fov="87°×58°", iface="USB3", price_cny=2600,
         note="深度 + 内置 IMU；四足上最常用的地形感知件（已停产，注意渠道）"),
    dict(model="RealSense D455", vendor="Intel", subtype="camera",
         resolution="1280×720 (深度)", depth_range_m="0.4–20", fps=90,
         fov="87°×58°", iface="USB3", price_cny=3200,
         note="基线更长，远处深度更准，近处盲区更大"),
    dict(model="Gemini 335", vendor="奥比中光 Orbbec", subtype="camera",
         resolution="1280×800", depth_range_m="0.1–10", fps=60, fov="91°×66°",
         iface="USB3", price_cny=1500,
         note="D435i 的常见替代；SDK 成熟度要自己验"),
    dict(model="OAK-D Pro", vendor="Luxonis", subtype="camera",
         resolution="1280×800", depth_range_m="0.3–12", fps=60, fov="80°×55°",
         iface="USB3", price_cny=3200,
         note="深度在相机内算（板载 Myriad X），省主机算力；模型要转 blob"),
    dict(model="ZED 2i", vendor="Stereolabs", subtype="camera",
         resolution="2× 1920×1080", depth_range_m="0.3–20", fps=100,
         fov="120°×75°", iface="USB3", price_cny=4200,
         note="广角 + 内置 IMU；SDK 只对 x86/ARM 官方支持，Jetson 要自己编"),
    # LiDAR
    dict(model="Mid-360", vendor="Livox", subtype="lidar", range_m=40,
         points_per_s=200000, fov="360°×59°", iface="以太网", price_cny=4000,
         note="非重复扫描，近距离点密度高；四足上做地形/避障的主力"),
    dict(model="Airy", vendor="速腾 RoboSense", subtype="lidar", range_m=40,
         points_per_s=540000, fov="360°×90°", iface="以太网", price_cny=3000,
         note="全固态 360°，体积小；强日光下要实测"),
    # 力 / 触觉
    dict(model="FSR402 薄膜压力", vendor="Interlink", subtype="force",
         range_m=None, channel=1, iface="模拟分压", price_cny=15,
         note="足端触地检测够用；不能当力矩传感器，迟滞和漂移都大"),
    dict(model="M35XX 六维力", vendor="宇立 SRI", subtype="force",
         channel=6, iface="以太网/CAN", price_cny=8000,
         note="腕/踝用；四足足端一般用一维或三轴就够"),
    dict(model="Mini45", vendor="ATI", subtype="force", channel=6, iface="以太网/CAN",
         price_cny=35000, note="标定溯源到 NIST；科研论文里常见，量产不会用"),
    # 编码器
    dict(model="AS5047P", vendor="ams OSRAM", subtype="encoder", bits=14,
         absolute=True, iface="SPI/ABZ", price_cny=25,
         note="关节输出端 14 bit；配合双编（电机端 + 输出端）做减速器误差补偿"),
    dict(model="AS5600", vendor="ams OSRAM", subtype="encoder", bits=12,
         absolute=True, iface="I²C/模拟", price_cny=8,
         note="便宜、够用在云台；12 bit 对四足膝关节偏粗"),
    dict(model="MT6835", vendor="MagnTek 麦歌恩", subtype="encoder", bits=21,
         absolute=True, iface="SPI/ABZ", price_cny=35,
         note="21 bit 磁编，国产里性价比高；注意气隙公差和温漂"),
    dict(model="TS5700N8501", vendor="多摩川 Tamagawa", subtype="encoder", bits=17,
         absolute=True, iface="串行/ABZ", price_cny=600,
         note="工业伺服标准件；抗污抗振好，价格是磁编的 20 倍"),
]


def build(items, keys, category, subtype_default=None, extra_note_key="note",
          id_prefix=None):
    out = []
    for it in items:
        it = dict(it)
        note = it.pop(extra_note_key, None)
        price = it.pop("price_cny", None)
        subtype = it.get("subtype") or subtype_default
        if subtype_default:
            it.pop("subtype", None)
        specs = {}
        for k in keys:
            if k == "subtype":
                continue
            specs[k] = it.pop(k, None)
        out.append({
            "id": f"{(id_prefix or category[:4])}-{slug(it['vendor'])}-{slug(it['model'])}",
            "category": category,
            "subtype": subtype,
            "vendor": it["vendor"],
            "vendor_cn": None,
            "model": it["model"],
            "title": f'{it["vendor"]} {it["model"]}',
            "url": it.get("url"),
            "source_tier": it.get("source_tier", "B"),
            "verified": 0,
            "last_checked": "2026-10-27",
            "price_cny": price,
            "specs": specs,
            "notes": note or "",
        })
    return out


def main():
    highs = build(HIGH, HIGH_KEYS, "controller_high", "sbc")
    lows = build(LOW, LOW_KEYS, "controller_low", "driver")
    # 下位机里 MCU/驱动是 subtype=mcu；桥接件单独标
    for r, src in zip(lows, LOW):
        r["subtype"] = "bridge" if "桥" in (src.get("encoder") or "") else "mcu"

    # 传感器按子类拆成独立品类（IMU / 激光雷达 / 深度相机），其余并入「其余模块」。
    # 为什么拆：这三类是四足里各自独立决策的部件，混在「传感器」一个大类里，
    # 选型时既看不到各家横向对比，也没法给单类做专属字段。
    SENSOR_CATEGORY = {
        "imu": "imu", "lidar": "lidar", "camera": "camera",
        "force": "module", "encoder": "module",
    }
    sens = []
    for it in SENSORS:
        st = it["subtype"]
        cat = SENSOR_CATEGORY.get(st, "module")
        # id 前缀固定用 sens，不随品类改 —— 否则已有的引用（后台留痕、外链）全断
        sens += build([it], SENSOR_KEYS, cat, st, id_prefix="sens")

    # 焦点过滤：data/focus.json 只保留指定品类/厂商时，不写被移出的品类文件。
    # 为什么：这些是**采集产物**，重跑一次就把 focus_data.py 移走的东西带回来，
    # 白名单式的「当前只做关节电机」会被悄悄破坏。
    focus_path = DATA / "focus.json"
    keep_cat = None
    if focus_path.exists():
        keep_cat = set(json.loads(focus_path.read_text(encoding="utf-8"))
                       .get("categories") or []) or None

    for name, rows in (("controllers_high", highs), ("controllers_low", lows),
                       ("sensors", sens)):
        if keep_cat and name not in {"actuator"} and not (
                {r["category"] for r in rows} & keep_cat):
            p = DATA / f"{name}.json"
            if p.exists():
                p.unlink()
            print(f"跳过 {name}.json（不在 focus.json 范围内，已清理旧产物）")
            continue
        p = DATA / f"{name}.json"
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {p.name}: {len(rows)} 行")

    import collections
    by = collections.Counter(r["category"] for r in highs + lows + sens)
    print(f"  上位机 {len(highs)} / 下位机 {len(lows)}")
    print("  按品类：" + "、".join(f"{k} {v}" for k, v in sorted(by.items())))


if __name__ == "__main__":
    main()

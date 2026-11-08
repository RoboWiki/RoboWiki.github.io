"""目录字段白名单：后台提案、公开提案、校验共用一份。

分散定义会让「后台能改」与「提案能收」出现两套口径，最后 bot 生成的
PR 里带着 pipeline 拒收的字段。
"""
from __future__ import annotations

#: 可经提案修改的行级字段。category/subtype 涉及分类注册表，不在此列。
TOP_FIELDS = {
    "price_cny", "url", "source_tier", "verified", "last_checked", "notes",
    "origin", "title", "vendor", "vendor_cn", "model",
}

#: specs 里允许提案修改的字段。
#: 必须与`RoboWiki` 仓 pipeline/validate.py::KNOWN_SPEC_KEYS 同步；少一个键，
#: 对应品类的真实纠错就无法提交（连接器就曾因此被挡在审核队列外）。
SPEC_KEYS = {
    # 执行器
    "tau_peak_Nm", "tau_rated_Nm", "tau_basis", "speed_noload_rpm", "speed_rated_rpm",
    "gear", "mass_kg", "od_mm", "l_mm", "rotor_inertia_kgm2", "inertia_basis",
    "armature_kgm2", "voltage_V", "voltage_range_V", "kt_Nm_per_A", "r_phase_ohm",
    "l_phase_uh", "pole_pairs", "i_peak_A", "i_rated_A", "frictionloss_Nm",
    "damping_Nms_rad", "encoder", "comm", "driver_integrated", "ip",
    "image_url", "image_source",
    # 上位机 / 下位机
    "soc", "cpu", "cores", "cpu_arch", "gpu", "cuda_cores", "npu_tops", "ram_gb",
    "ram_bw_gbs", "storage_gb", "power_idle_w", "power_max_w", "os", "cuda", "ros2",
    "eth", "usb", "can", "csi", "pcie", "size_mm", "weight_g",
    "mcu", "clock_mhz", "ram_kb", "flash_kb", "foc_axes", "canfd",
    "current_loop_khz", "torque_mode", "voltage_in_V", "voltage_max_V", "comm_upper",
    # 传感器
    "gyro_range_dps", "accel_range_g", "odr_hz", "iface", "noise", "resolution",
    "depth_range_m", "fps", "fov", "range_m", "points_per_s", "channel", "bits",
    "absolute", "temp_range_C",
    # 遥控器 / CAN 模块
    "channels", "frequency_ghz", "control_range_m", "protocol", "battery",
    "can_speed_mbps", "isolation",
    # 归档导入字段
    "tau_stall_Nm", "tau_hold_Nm", "i_stall_A", "dims", "temp_range",
    "storage_temp_range", "meas_range", "accuracy", "response_time", "power_w",
    "motor_type", "gear_material", "housing_material", "bearing", "mounting",
    "connector", "backlash_arcmin",
    # 芯片
    "package",
    # 资料链接
    "doc_url", "doc_pdf", "repo_urls", "imu",
    # 电池
    "capacity_mah", "energy_wh", "discharge_rate_c", "current_rated_A",
    "v_charge_V", "mass_g", "chem",
    # 充电器（平衡充 / 充放管理）
    "input_voltage", "charge_power_w", "charge_current_a", "discharge_power_w",
    "discharge_current_a", "balance_current_ma", "cell_range", "chemistries",
    "usb_output", "wireless_charge_w", "display", "connectors", "smart_features",
    # 结构件 / 轮组 / 裁判系统 / 视觉与传感扩展
    "diameter_mm", "width_mm", "load_kg", "bore_mm", "module_type", "current_A",
    "led_count", "sensor", "mount",
    "focal_mm", "fov_deg",
    "material", "speed_s_60deg", "stall_torque_Nm",
    "build_volume_mm", "max_speed_mms", "temp_max_C", "materials",
    "connectivity",
    # 设备库：激光切割/雘刹与测量仪器
    "cut_area_mm", "laser_power_w", "bandwidth_mhz", "sample_rate_msps",
    "max_freq_mhz", "waveform",
    # 立创采集 / 电源芯片
    "category_cn", "lcsc_part", "params", "price_tiers", "price_lead", "stock",
    "stock_lead", "lead_time", "jlc_library", "tags", "fetched_at", "voltage_in",
    "voltage_out", "current_out", "function_type", "output_type", "polarity", "freq",
    "chip_function", "charge_current", "v_float", "battery_type", "cells",
    "switch_type", "logic", "features", "coupon",
    # 连接器
    "positions", "positions_options", "pitch_mm", "voltage_rated_V",
    "current_basis", "contact_resistance_mohm", "insulation_resistance_mohm",
    "withstand_voltage_V", "mating_cycles", "wire_awg", "mount_type", "lock_type",
    "power_positions", "signal_positions", "signal_current_rated_A",
    "contact_layout", "instantaneous_current_A", "use_cases",
    "impedance_ohm", "freq_max_ghz", "length_m", "awg",
}

#: 允许出现在提案里的字段全名 -> (存储位置, 字段名)
def split_field(key: str) -> tuple[str, str]:
    if key.startswith("specs."):
        return "specs", key.split(".", 1)[1]
    return "columns", key


def allowed(key: str) -> bool:
    where, field = split_field(key)
    if where == "specs":
        return field in SPEC_KEYS
    return field in TOP_FIELDS

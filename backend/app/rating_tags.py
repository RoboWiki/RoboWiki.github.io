"""评分理由词表（与前端 apps/web/src/lib/ratingTags.ts 对齐）。

前端按品类展示，后端只校验是否属于全部白名单；跨品类标签即使提交也不会污染
聚合，因为聚合只按 key 计数。
"""
from __future__ import annotations

UNIVERSAL_TAGS = frozenset({
    "good_value", "better_than_spec", "overstated", "build_quality",
    "docs_missing", "shipping", "not_recommend", "fake_chip", "heat",
    "durability",
})

CATEGORY_TAGS: dict[str, frozenset[str]] = {
    "actuator": frozenset({"encoder_drift", "backlash", "torque_margin", "cogging", "noise", "driver_compat", "thermal_drift"}),
    "servo": frozenset({"gear_metal", "gear_plastic", "backlash", "centering", "stall", "jitter", "wire_order", "horn_fit"}),
    "motor_driver": frozenset({"burned", "protection", "comm_error", "current_loop", "heating", "interface"}),
    "controller_low": frozenset({"realtime", "io", "power", "sdk", "firmware", "thermal"}),
    "controller_high": frozenset({"compute", "io", "power", "sdk", "thermal", "os"}),
    "remote_controller": frozenset({"latency", "range", "sticks", "battery", "compat"}),
    "esc": frozenset({"linearity", "heat", "sync", "brake", "firmware"}),
    "imu": frozenset({"drift", "noise", "bias", "vibration", "calibration"}),
    "sensor": frozenset({"accuracy", "drift", "noise", "latency", "calibration", "range"}),
    "lidar": frozenset({"range", "blind_zone", "reflectivity", "sunlight", "latency"}),
    "camera": frozenset({"resolution", "frame_rate", "low_light", "latency", "sync", "distortion"}),
    "battery": frozenset({"capacity_fake", "voltage_sag", "swelling", "charge_rate", "connector", "weight"}),
    "charger": frozenset({"charge_speed", "cutoff", "heat", "noise", "protocol", "connector"}),
    "connector": frozenset({"contact", "lock", "wire_gauge", "solder", "cycles"}),
    "module": frozenset({"compat", "docs", "power", "size"}),
    "chip": frozenset({"fake_chip", "solder", "datasheet", "availability"}),
    "open_hw": frozenset({"docs", "bom", "firmware", "community"}),
    "equipment": frozenset({"accuracy", "build", "usability", "accessories"}),
    "power": frozenset({"protection", "heat", "connector", "noise"}),
    "structural": frozenset({"tolerance", "hole_fit", "material", "stiffness", "weight", "finish"}),
    "wheel": frozenset({"grip", "wear", "concentricity", "weight", "hub_fit"}),
    "referee": frozenset({"compat", "stability", "docs"}),
}

LEGACY_TAGS = frozenset({"hard_to_solder", "lighting"})

ALL_TAGS = UNIVERSAL_TAGS | LEGACY_TAGS | frozenset().union(*CATEGORY_TAGS.values())

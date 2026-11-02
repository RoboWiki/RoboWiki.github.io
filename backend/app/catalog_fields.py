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

#: specs 里允许提案修改的字段（与 pipeline/validate.py 的白名单一致）
SPEC_KEYS = {
    "tau_peak_Nm", "tau_rated_Nm", "tau_basis", "speed_noload_rpm", "speed_rated_rpm",
    "gear", "mass_kg", "od_mm", "l_mm", "rotor_inertia_kgm2", "inertia_basis",
    "armature_kgm2", "voltage_V", "voltage_range_V", "kt_Nm_per_A", "r_phase_ohm",
    "l_phase_uh", "pole_pairs", "i_peak_A", "i_rated_A", "frictionloss_Nm",
    "damping_Nms_rad", "encoder", "comm", "driver_integrated", "ip",
    "image_url", "image_source",
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

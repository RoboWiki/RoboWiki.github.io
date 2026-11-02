"""提案字段白名单：必须覆盖每个品类的真实字段。"""
from __future__ import annotations

from app.catalog_fields import allowed, split_field


def test_connector_and_sensor_fields_are_proposable():
    for key in ("specs.positions", "specs.current_rated_A", "specs.voltage_rated_V",
                "specs.pitch_mm", "specs.use_cases",
                "specs.npu_tops", "specs.range_m", "specs.capacity_mah"):
        assert allowed(key), key


def test_top_level_fields_and_unknown_keys():
    assert allowed("price_cny") and allowed("source_tier") and allowed("origin")
    assert not allowed("is_admin")
    assert not allowed("category")          # 分类注册表不通过提案改
    assert not allowed("specs.minecraft_torque")


def test_split_field():
    assert split_field("specs.gear") == ("specs", "gear")
    assert split_field("price_cny") == ("columns", "price_cny")

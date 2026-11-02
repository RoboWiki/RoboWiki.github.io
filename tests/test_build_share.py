"""分享 JSON：品类字段、规范链接、版本。"""
from __future__ import annotations

import json

from pipeline.build_share import build


def _rows():
    return [
        {
            "id": "amass-xt30", "category": "connector", "vendor": "Amass",
            "model": "XT30", "title": "Amass XT30 大电流连接器",
            "source_tier": "A", "last_checked": "2026-10-31",
            "specs": {"positions": 2, "current_rated_A": 20,
                      "voltage_rated_V": 500, "wire_awg": "AWG 16"},
        },
        {
            "id": "cubemars-ak80-6", "category": "actuator", "vendor": "CubeMars",
            "model": "AK80-6", "title": "CubeMars AK80-6 关节模组",
            "source_tier": "B", "last_checked": "2026-10-31",
            "specs": {"tau_peak_Nm": 12, "tau_rated_Nm": 6, "voltage_V": 48,
                      "mass_kg": 0.485},
        },
    ]


def test_index_carries_canonical_url_and_category_facts(tmp_path):
    slugs = {"amass-xt30": "amass-xt30", "cubemars-ak80-6": "cubemars-ak80-6"}
    n = build(_rows(), slugs, tmp_path, "https://robowiki.org/", "data-v2026.11.0")
    assert n == 2

    idx = json.loads((tmp_path / "public/share/index.json").read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in idx}
    con = by_id["amass-xt30"]
    assert con["url"] == "https://robowiki.org/parts/connector/amass-xt30.html"
    assert "2 pin" in con["summary"] and "20 A" in con["summary"]
    assert "500 V" in con["summary"]

    act = by_id["cubemars-ak80-6"]
    assert "12 N·m" in act["summary"] and "6 N·m" in act["summary"]

    part = json.loads(
        (tmp_path / "public/share/parts/connector/amass-xt30.json").read_text(encoding="utf-8"))
    assert part["canonical_url"] == con["url"]
    assert part["id"] == "amass-xt30"
    assert any(p["label"] == "电流" and "20 A" in p["value"] for p in part["params"])

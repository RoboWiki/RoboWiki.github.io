"""连接器品类：分类、数据完整性与混合触点契约。

为什么要有这些测试：
    连接器不是「线束」换个名字。它要同时容纳线对板、大电流、射频和
    成品线束，参数口径（标称电流 / 测试条件 / 位数）不统一就会把
    XT30 和 JST GH 放在同一张表里硬比。这里把关键约定变成可检查的事。
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.load import load_parts, load_taxonomy  # noqa: E402

EXPECTED_IDS = {
    # 既有成品线束
    "feetech-5264-cable",     # JST 线对板
    "jst-gh-1p25", "jst-sh-1p0", "jst-xh-2p5", "jst-ph-2p0", "jst-zh-1p5",
    # Amass 大电流 + 电源/信号混合
    "amass-xt30", "amass-xt60", "amass-xt90", "amass-mr30",
    "amass-xt30-2p2", "amass-xt90-2p2",
    # 常见 B 级连接器
    "cjt-a2541-8p", "xunpu-fpc-05-24p",
    "degson-2edg-381-2p", "degson-2edg-508-2p",
    "xkb-usb-c-16p", "xkb-dc-5521",
    "cjt-db9", "cjt-rj45",
    "kinghelm-sma", "kinghelm-bnc", "weipu-gx12",
}

EXPECTED_SUBTYPES = {
    "wire_to_board", "power", "power_signal", "board", "ffc",
    "terminal", "data", "rf", "industrial", "cable",
}


def connector_rows() -> list[dict]:
    return [p for p in load_parts() if p["category"] == "connector"]


def test_connector_category_replaces_wiring():
    cats = {c["id"]: c for c in load_taxonomy()["categories"]}
    assert "connector" in cats, "品类注册表里没有 connector"
    assert "wiring" not in cats, "旧的 wiring 品类还在"
    assert cats["connector"]["name"] == "连接器"
    enum = set(json.loads(
        (ROOT / "schema" / "part.schema.json").read_text(encoding="utf-8")
    )["properties"]["category"]["enum"])
    assert "connector" in enum, "schema 还没允许 connector"
    assert "wiring" not in enum, "schema 还允许旧的 wiring"


def test_connector_category_has_expected_subtypes():
    cat = next(c for c in load_taxonomy()["categories"] if c["id"] == "connector")
    missing = EXPECTED_SUBTYPES - set((cat.get("subtypes") or {}).keys())
    assert not missing, f"连接器缺子类：{sorted(missing)}"


def test_connector_rows_present():
    rows = connector_rows()
    assert len(rows) == len(EXPECTED_IDS), f"连接器应为 {len(EXPECTED_IDS)} 条，实际 {len(rows)}"
    ids = {r["id"] for r in rows}
    missing = EXPECTED_IDS - ids
    assert not missing, f"缺少连接器条目：{sorted(missing)}"


def test_connector_rows_have_use_cases():
    for r in connector_rows():
        uc = (r.get("specs") or {}).get("use_cases")
        assert isinstance(uc, list) and uc, f"{r['id']} 缺 use_cases"
        assert all(isinstance(x, str) and x.strip() for x in uc), f"{r['id']} 的 use_cases 含空值"


def test_connector_a_rows_have_sources_and_current_basis():
    for r in connector_rows():
        if r.get("source_tier") != "A":
            continue
        s = r["specs"]
        assert s.get("current_basis"), f"{r['id']} 是 A 级但没写 current_basis"
        assert s.get("doc_pdf") or s.get("doc_url"), f"{r['id']} 是 A 级但没有官方资料链接"
        opts = s.get("positions_options")
        assert isinstance(opts, list) and opts, f"{r['id']} 缺 positions_options"
        assert s.get("positions") in opts, f"{r['id']} 的代表位数不在 positions_options 里"


def test_connector_hybrid_rows_declare_power_and_signal():
    by_id = {r["id"]: r for r in connector_rows()}
    for rid in ("amass-xt30-2p2", "amass-xt90-2p2"):
        s = by_id[rid]["specs"]
        assert s.get("power_positions") == 2, f"{rid} 的电源位数应为 2"
        assert s.get("signal_positions") == 2, f"{rid} 的信号位数应为 2"
        assert s.get("contact_layout"), f"{rid} 缺 contact_layout"
        assert s.get("signal_current_rated_A") == 1, f"{rid} 的信号针应为 1 A"

"""协议口径端点的测试。

核心断言：同一个「电流」在不同驱动里必须是不同的量。
这些数字来自 yssickjgd/robowalker_train 的驱动定标常量，一旦被抹平，
跨厂商比电流/力矩就全错了。
"""
from __future__ import annotations

import os
import pathlib
import sys

os.environ.setdefault("ROBOSELECT_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_protocols_list(client):
    d = client.get("/api/protocols").json()
    assert d["total"] >= 5
    assert "DJI RoboMaster" in d["vendors"]
    assert any("DM" in v for v in d["vendors"]), "达妙必须在列"
    assert d["checklist"], "口径自检清单不能为空"
    assert d["meta"]["source_url"].endswith("robowalker_train")


def test_current_full_scale_differs_per_driver(client):
    """C610 的 10000 与 C620 的 16384 不是一套比例 —— 这是最容易被抹平的一条。"""
    d = client.get("/api/protocols").json()
    by_id = {p["id"]: p for p in d["protocols"]}

    assert by_id["dji-c620"]["current_full_scale_A"] == 20.0
    assert by_id["dji-c610"]["current_full_scale_A"] == 10.0
    assert by_id["dji-gm6020"]["current_full_scale_A"] == 3.0
    assert by_id["dji-c620"]["current_scale_a_per_lsb"] != by_id["dji-c610"]["current_scale_a_per_lsb"]

    # 达妙的电流满量程是驱动定标值，不是厂商额定电流
    assert by_id["dm-mit"]["current_full_scale_A"] == pytest.approx(10.261194)


def test_m3508_gear_uses_protocol_value(client):
    """M3508 的协议减速比是 3591/187，不是手册写的 19。"""
    d = client.get("/api/protocols").json()
    c620 = next(p for p in d["protocols"] if p["id"] == "dji-c620")
    assert c620["gear_protocol"] == pytest.approx(3591 / 187)
    assert c620["gear_nominal"] == "19:1"

    part = client.get("/api/parts/dji-robomaster-m3508-p19").json()
    assert part["specs"]["gear"] == pytest.approx(3591 / 187), "目录里也要用协议值"
    assert "19" in part["notes"]


def test_every_protocol_has_evidence_and_notes(client):
    """没有证据的口径不许进库 —— 和零件字段同一条规矩。"""
    for p in client.get("/api/protocols").json()["protocols"]:
        assert p["evidence"].strip(), f"{p['id']} 缺证据"
        assert p["notes"].strip(), f"{p['id']} 缺口径提醒"
        assert p["control_modes"], f"{p['id']} 缺控制模式"


def test_protocol_detail_and_404(client):
    d = client.get("/api/protocols/dm-mit").json()
    assert d["vendor"] == "达妙 DM"
    assert "12 bit" in d["current_encoding"]
    assert client.get("/api/protocols/nope").status_code == 404

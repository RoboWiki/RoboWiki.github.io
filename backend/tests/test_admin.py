"""后台测试：口径、留痕、权限。

重点是**看板自己的口径**：`tau_rated_Nm` / `armature_kgm2` 这两个字段
对主控和传感器没有意义，把它们算进「缺口」会虚增 41 个。
曾经就犯过这个错（148 而不是 107），所以这里钉死。
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-admin-")
os.environ["ROBOSELECT_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOSELECT_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    from app.core.db import engine, reset_engine
    try:
        engine().dispose()
    except Exception:
        pass
    reset_engine()
    shutil.rmtree(_TMP, ignore_errors=True)


def staff(client) -> dict:
    """roboselect 是站务账号"""
    r = client.post("/api/auth/login",
                    json={"handle": "roboselect", "password": "roboselect"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def plain(client) -> dict:
    r = client.post("/api/auth/login", json={"handle": "demo1", "password": "roboselect"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── 权限 ────────────────────────────────────────────────────────────────────
def test_admin_requires_staff(client):
    h = plain(client)
    for path in ("/api/admin/stats", "/api/admin/parts"):
        assert client.get(path, headers=h).status_code == 403, path
    assert client.get("/api/admin/stats").status_code == 401   # 未登录


# ── 看板口径 ────────────────────────────────────────────────────────────────
def test_gap_counts_are_scoped_to_the_category_where_the_field_means_something(client):
    """缺额定扭矩 / 缺 armature 只能统计执行器。

    主控和传感器根本没有这两个字段；算进缺口会虚增 41 个。
    曾经把缺额定扭矩算成 148（= 全库 188 - 已有 40），真缺口是 107。
    """
    s = client.get("/api/admin/stats", headers=staff(client)).json()

    # 不写死具体数字（目录会增长），只钉「口径」这件事
    assert s["actuators"] >= 147
    assert s["parts"] >= s["actuators"]
    non_actuator = s["parts"] - s["actuators"]
    assert non_actuator >= 41, "主控 + 传感器至少 41 个"

    # 这两个数必须落在执行器范围内，而不是全库
    assert s["no_rated_torque"] <= s["actuators"], "缺额定扭矩不该超过执行器数"
    assert s["no_armature"] <= s["actuators"], "缺 armature 不该超过执行器数"
    # 关键回归：如果又按全库算，就会 >= 全库 - 已有数，比真缺口大出 non_actuator
    assert s["no_rated_torque"] <= s["actuators"] - 40 + 10
    assert "执行器" in s["scopes"]["no_rated_torque"]
    assert "执行器" in s["scopes"]["no_armature"]


def test_gap_filter_matches_the_dashboard_number(client):
    """看板说缺 107 个，筛出来也必须是 107 个 —— 否则用户点进去会发现对不上。"""
    h = staff(client)
    s = client.get("/api/admin/stats", headers=h).json()
    for gap, key in (("no_rated", "no_rated_torque"), ("no_armature", "no_armature")):
        d = client.get("/api/admin/parts", params={"gap": gap, "limit": 200},
                       headers=h).json()
        assert d["total"] == s[key], f"{gap}: 筛选 {d['total']} != 看板 {s[key]}"
        assert all(i["category"] == "actuator" for i in d["items"]), \
            f"{gap} 混进了非执行器"


def test_gap_filter_for_image_is_global(client):
    """产品图对每个品类都有意义，所以是全局口径。"""
    h = staff(client)
    s = client.get("/api/admin/stats", headers=h).json()
    d = client.get("/api/admin/parts", params={"gap": "no_image", "limit": 1}, headers=h).json()
    assert d["total"] == s["no_image"]


# ── 改字段与留痕 ────────────────────────────────────────────────────────────
def test_patch_writes_history_with_reason(client):
    h = staff(client)
    pid = "cubemars-ak80-9-v3"
    before = client.get(f"/api/admin/parts/{pid}", headers=h).json()
    n_before = len(before["history"])

    r = client.patch(f"/api/admin/parts/{pid}", headers=h, json={
        "changes": {"specs.tau_rated_Nm": 8.0},
        "note": "据 CubeMars AK80-9 V3 官方 datasheet 第 2 页扭矩曲线，额定 8 N·m @ 25℃",
        "source_url": "https://www.cubemars.com/product/ak80-9-v3-0-kv60-robotic-actuator.html",
    })
    assert r.status_code == 200
    assert r.json()["changed"] == 1

    after = client.get(f"/api/admin/parts/{pid}", headers=h).json()
    assert after["specs"]["tau_rated_Nm"] == 8.0
    assert len(after["history"]) == n_before + 1

    h0 = after["history"][0]
    assert h0["field"] == "specs.tau_rated_Nm"
    assert h0["new_value"] == "8.0"
    assert "datasheet" in h0["note"]           # 依据留下来了
    assert h0["source_url"].endswith(".html")  # 来源也留下来了
    assert h0["editor"] == "RoboSelect 编辑部"
    # 改完自动打核对日期
    assert after["last_checked"]


def test_patch_rejects_fields_outside_whitelist(client):
    h = staff(client)
    r = client.patch("/api/admin/parts/cubemars-ak80-9-v3", headers=h,
                     json={"changes": {"specs.minecraft_torque": 1}, "note": "不该被接受"})
    assert r.status_code == 422
    r = client.patch("/api/admin/parts/cubemars-ak80-9-v3", headers=h,
                     json={"changes": {"is_admin": True}, "note": "不该被接受"})
    assert r.status_code == 422


def test_patch_requires_a_reason(client):
    """没有依据的改动 = 编造数据，必须拒绝。"""
    h = staff(client)
    r = client.patch("/api/admin/parts/cubemars-ak80-9-v3", headers=h,
                     json={"changes": {"specs.mass_kg": 1.0}, "note": ""})
    assert r.status_code == 422


def test_patch_noop_returns_zero(client):
    h = staff(client)
    r = client.patch("/api/admin/parts/cubemars-ak80-9-v3", headers=h,
                     json={"changes": {"specs.tau_rated_Nm": 8.0}, "note": "重复提交同值"})
    assert r.status_code == 200 and r.json()["changed"] == 0


def test_verify_marks_and_timestamps(client):
    h = staff(client)
    r = client.post("/api/admin/parts/灵足-robstride-rs05/verify", headers=h)
    assert r.status_code == 200
    d = client.get("/api/admin/parts/灵足-robstride-rs05", headers=h).json()
    assert d["verified"] is True
    assert any(x["field"] == "verified" for x in d["history"])


def test_history_endpoint_lists_recent_edits(client):
    h = staff(client)
    d = client.get("/api/admin/history?limit=10", headers=h).json()
    assert isinstance(d, list) and d
    assert {"part_id", "field", "note", "editor"} <= set(d[0])

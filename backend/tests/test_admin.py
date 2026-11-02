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
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"
os.environ["ROBOWIKI_BOT_TOKEN"] = "test-bot-token"

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
                    json={"handle": "robowiki", "password": "robowiki"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def plain(client) -> dict:
    r = client.post("/api/auth/login", json={"handle": "demo1", "password": "robowiki"})
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
    assert s["actuators"] >= 40
    assert s["parts"] >= s["actuators"]
    non_actuator = s["parts"] - s["actuators"]
    assert non_actuator >= 0

    # 这两个数必须落在执行器范围内，而不是全库
    assert s["no_rated_torque"] <= s["actuators"], "缺额定扭矩不该超过执行器数"
    assert s["no_armature"] <= s["actuators"], "缺 armature 不该超过执行器数"
    # 关键回归：如果又按全库算，就会 >= 全库 - 已有数，比真缺口大出 non_actuator
    assert s["no_rated_torque"] < s["actuators"]
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


# ── 改字段：只生成提案，不写目录 ────────────────────────────────────────────
def test_patch_creates_submission_without_writing_catalog(client):
    """后台 PATCH 不得再改 parts：目录只能由 release 写。"""
    h = staff(client)
    pid = "达妙-dm-dm-j4340-2ec-v1-1"
    before = client.get(f"/api/admin/parts/{pid}", headers=h).json()
    old_rated = before["specs"]["tau_rated_Nm"]

    r = client.patch(f"/api/admin/parts/{pid}", headers=h, json={
        "changes": {"specs.tau_rated_Nm": 13.0},
        "note": "据达妙 DAMIAO-J4340-2EC V1.1 选型手册 p17 参数表，额定 12 N·m",
        "source_url": "https://www.damiao.tech/",
    })
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["changed"] == 2                 # 改动字段 + 刷新核对日期
    assert d["status"] == "pending"
    sid = d["submission_id"]
    assert d["diff"][0]["field"] == "specs.tau_rated_Nm"

    after = client.get(f"/api/admin/parts/{pid}", headers=h).json()
    assert after["specs"]["tau_rated_Nm"] == old_rated   # 目录未被写

    q = client.get("/api/v1/submissions/queue", headers=h).json()
    mine = [s for s in q if s["id"] == sid]
    assert mine and mine[0]["payload"]["specs.tau_rated_Nm"] == 13.0
    assert mine[0]["payload"]["last_checked"]
    assert mine[0]["evidence"]["source_url"] == "https://www.damiao.tech/"
    assert mine[0]["evidence"]["preview"][0]["old_value"] == old_rated
    assert mine[0]["evidence"]["preview"][0]["new_value"] == 13.0
    assert any(s["submission_id"] == sid for s in after["proposals"])


def test_patch_rejects_fields_outside_whitelist(client):
    h = staff(client)
    r = client.patch("/api/admin/parts/达妙-dm-dm-j4340-2ec-v1-1", headers=h,
                     json={"changes": {"specs.minecraft_torque": 1}, "note": "不该被接受"})
    assert r.status_code == 422
    r = client.patch("/api/admin/parts/达妙-dm-dm-j4340-2ec-v1-1", headers=h,
                     json={"changes": {"is_admin": True}, "note": "不该被接受"})
    assert r.status_code == 422


def test_patch_requires_a_reason(client):
    """没有依据的改动 = 编造数据，必须拒绝。"""
    h = staff(client)
    r = client.patch("/api/admin/parts/达妙-dm-dm-j4340-2ec-v1-1", headers=h,
                     json={"changes": {"specs.mass_kg": 1.0}, "note": ""})
    assert r.status_code == 422


def test_patch_noop_returns_zero(client):
    h = staff(client)
    pid = "达妙-dm-dm-j4340-2ec-v1-1"
    cur = client.get(f"/api/admin/parts/{pid}", headers=h).json()["specs"]["mass_kg"]
    r = client.patch(f"/api/admin/parts/{pid}", headers=h,
                     json={"changes": {"specs.mass_kg": cur}, "note": "重复提交同值"})
    assert r.status_code == 200 and r.json()["changed"] == 0
    assert "submission_id" not in r.json()


def test_verify_creates_submission_instead_of_writing(client):
    h = staff(client)
    gap = client.get("/api/admin/parts", params={"gap": "unverified", "limit": 1},
                     headers=h).json()
    pid = gap["items"][0]["id"]
    r = client.post(f"/api/admin/parts/{pid}/verify", headers=h)
    assert r.status_code == 200, r.text
    sid = r.json()["submission_id"]
    d = client.get(f"/api/admin/parts/{pid}", headers=h).json()
    assert d["verified"] is False          # 未发布，目录不动
    q = client.get("/api/v1/submissions/queue", headers=h).json()
    mine = [s for s in q if s["id"] == sid]
    assert mine and mine[0]["payload"]["verified"] is True
    assert mine[0]["payload"]["last_checked"]


def test_history_endpoint_lists_proposals(client):
    h = staff(client)
    d = client.get("/api/admin/history?limit=10", headers=h).json()
    assert isinstance(d, list) and d
    assert any(x["source"] == "proposal" for x in d)
    assert {"part_id", "note", "editor", "status"} <= set(d[0])

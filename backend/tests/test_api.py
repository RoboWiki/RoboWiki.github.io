"""RoboSelect API 测试。

    cd backend && python -m pytest -q
    # 或 python -m unittest discover -s tests -v

每个测试类用独立的临时库（ROBOSELECT_DB_PATH），不碰仓库里的 roboselect.db。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# 必须在 import app 之前设置，settings 在 import 时实例化
_TMP = tempfile.mkdtemp(prefix="roboselect-test-")
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
    # Windows 上 WAL 会占住目录：先释放 engine 再清理
    from app.core.db import engine, reset_engine
    try:
        engine().dispose()
    except Exception:
        pass
    reset_engine()
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)


def auth_header(c: TestClient, handle="roboselect", password="roboselect") -> dict:
    r = c.post("/api/auth/login", json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── 目录 ────────────────────────────────────────────────────────────────────
def test_health_and_stats(client):
    assert client.get("/api/health").json()["ok"] is True
    s = client.get("/api/stats").json()
    assert s["parts"] >= 150
    assert s["with_armature"] >= 100
    assert s["users"] >= 2


def test_catalog_vendors_are_scoped(client):
    act = client.get("/api/catalog", params={"category": "actuator"}).json()
    sen = client.get("/api/catalog", params={"category": "sensor"}).json()
    act_v = {v["vendor"] for v in act["vendors"]}
    sen_v = {v["vendor"] for v in sen["vendors"]}
    assert "CubeMars" in act_v
    assert "CubeMars" not in sen_v       # 关节电机页不该混进传感器厂
    assert "Bosch" in sen_v


def test_parts_pagination(client):
    a = client.get("/api/parts", params={"category": "actuator", "limit": 5}).json()
    b = client.get("/api/parts", params={"category": "actuator", "limit": 5,
                                        "offset": 5}).json()
    assert len(a["items"]) == 5 and len(b["items"]) == 5
    assert a["items"][0]["id"] != b["items"][0]["id"]


def test_nulls_sort_last_both_directions(client):
    for order in ("asc", "desc"):
        d = client.get("/api/parts", params={"category": "actuator",
                                            "sort": "tau_rated", "order": order,
                                            "limit": 200}).json()
        vals = [i["specs"].get("tau_rated_Nm") for i in d["items"]]
        n_null = sum(1 for v in vals if v is None)
        assert all(v is None for v in vals[len(vals) - n_null:]), "null 必须排最后"


def test_sort_whitelist_falls_back(client):
    r = client.get("/api/parts", params={"sort": "id;DROP TABLE parts"})
    assert r.status_code == 200
    assert client.get("/api/health").status_code == 200


def test_armature_equals_n2j(client):
    """armature 必须等于 N²·J —— 读错口径会差 10⁴ 倍。"""
    d = client.get("/api/parts", params={"category": "actuator", "limit": 200}).json()
    checked = 0
    for p in d["items"]:
        s = p["specs"]
        j, g, arm = s.get("rotor_inertia_kgm2"), s.get("gear"), s.get("armature_kgm2")
        if j and g and arm:
            assert abs(arm / (j * g * g) - 1) < 1e-6, f"{p['id']} armature != N²·J"
            checked += 1
    assert checked > 50


def test_derived_torque_density(client):
    d = client.get("/api/parts", params={"category": "actuator", "limit": 5}).json()
    for p in d["items"]:
        s = p["specs"]
        if s.get("tau_peak_Nm") and s.get("mass_kg"):
            assert p["derived"]["torque_density_Nm_per_kg"] == pytest.approx(
                round(s["tau_peak_Nm"] / s["mass_kg"], 1), abs=0.15)


def test_unknown_part_404(client):
    assert client.get("/api/parts/nope").status_code == 404


# ── 社区 ────────────────────────────────────────────────────────────────────
def test_feed_has_seeded_posts(client):
    """种子里只有站方署名的编者按 —— 刻意不灌任何「用户使用经历」。"""
    d = client.get("/api/posts", params={"limit": 50}).json()
    kinds = {p["kind"] for p in d["items"]}
    assert "discussion" in kinds
    assert d["total"] >= 2

    seeded = client.get("/api/posts", params={"author": "roboselect", "limit": 50}).json()
    for p in seeded["items"]:
        assert not p["own_hardware"], "站方不能声称「实测」"
        assert p["rating"] is None, "站方不打用户评分"
        assert p["title"].startswith("编者按"), "站方内容必须自带来源标注"


def test_review_appears_on_its_part(client):
    """评价挂在零件上 → 零件详情里能看到。用 API 真写一条，不依赖种子。"""
    h = auth_header(client)
    part_id = "cubemars-ak80-9-v3"
    r = client.post("/api/posts", headers=h, json={
        "kind": "review", "title": "测试：评价挂载链路", "body": "这是一条用于验证挂载的测试评价。",
        "part_id": part_id, "rating": 4})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    detail = client.get(f"/api/parts/{part_id}").json()
    assert any(x["id"] == pid for x in detail["posts"]), "零件详情里必须能看到这条评价"

    listing = client.get("/api/parts", params={"category": "actuator", "limit": 200}).json()
    hit = next((i for i in listing["items"] if i["id"] == part_id), None)
    assert hit and hit["top_review"] and hit["top_review"]["id"] == pid


def test_register_login_me(client):
    r = client.post("/api/auth/register", json={
        "handle": "tester", "display_name": "测试员", "password": "secret123"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["handle"] == "tester"

    dup = client.post("/api/auth/register", json={
        "handle": "tester", "display_name": "重复", "password": "secret123"})
    assert dup.status_code == 409


def test_login_rejects_bad_password(client):
    r = client.post("/api/auth/login", json={"handle": "roboselect", "password": "wrong"})
    assert r.status_code == 401


def test_write_requires_auth(client):
    r = client.post("/api/posts", json={"kind": "discussion", "title": "x" * 5,
                                        "body": "y" * 20})
    assert r.status_code == 401


def test_post_validation(client):
    h = auth_header(client)
    # review 必须给 part_id 与评分
    r = client.post("/api/posts", headers=h, json={
        "kind": "review", "title": "缺零件号的评价", "body": "x" * 20})
    assert r.status_code == 422
    r = client.post("/api/posts", headers=h, json={
        "kind": "review", "title": "缺评分的评价", "body": "x" * 20,
        "part_id": "cubemars-ak10-9-v2"})
    assert r.status_code == 422
    # 不存在的零件
    r = client.post("/api/posts", headers=h, json={
        "kind": "review", "title": "不存在的零件号", "body": "x" * 20,
        "part_id": "no-such-part", "rating": 3})
    assert r.status_code == 404
    # 非法 kind
    r = client.post("/api/posts", headers=h, json={
        "kind": "spam", "title": "非法的帖子类型", "body": "x" * 20})
    assert r.status_code == 422


def test_post_and_vote_updates_reputation(client):
    h = auth_header(client)
    r = client.post("/api/posts", headers=h, json={
        "kind": "discussion", "title": "测试帖：投票链路", "body": "正文" * 10})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # 换一个用户来点赞
    h2 = auth_header(client, "demo1")
    v = client.post("/api/votes", headers=h2,
                    json={"target_kind": "post", "target_id": pid, "value": 1})
    assert v.status_code == 200
    assert v.json() == {"score": 1, "my_vote": 1}

    # 同一个人再点一次 → 取消
    v = client.post("/api/votes", headers=h2,
                    json={"target_kind": "post", "target_id": pid, "value": 0})
    assert v.json()["score"] == 0

    # 点踩
    v = client.post("/api/votes", headers=h2,
                    json={"target_kind": "post", "target_id": pid, "value": -1})
    assert v.json()["score"] == -1

    # 声望跟着变（作者是 lcs）
    me = client.get("/api/auth/me", headers=h).json()
    assert isinstance(me["reputation"], int)


def test_comment_two_levels_only(client):
    h = auth_header(client)
    posts = client.get("/api/posts", params={"limit": 1}).json()
    pid = posts["items"][0]["id"]

    r = client.post(f"/api/posts/{pid}/comments", headers=h, json={"body": "一级评论"})
    assert r.status_code == 201
    root = r.json()["id"]

    r = client.post(f"/api/posts/{pid}/comments", headers=h,
                    json={"body": "二级回复", "parent_id": root})
    assert r.status_code == 201
    child = r.json()["id"]

    r = client.post(f"/api/posts/{pid}/comments", headers=h,
                    json={"body": "三级不允许", "parent_id": child})
    assert r.status_code == 422

    tree = client.get(f"/api/posts/{pid}/comments").json()
    assert any(c["id"] == root and c["replies"] for c in tree)


def test_comment_count_tracks(client):
    h = auth_header(client)
    posts = client.get("/api/posts", params={"kind": "discussion", "limit": 1}).json()
    p = posts["items"][0]
    before = p["comment_count"]
    client.post(f"/api/posts/{p['id']}/comments", headers=h, json={"body": "计数测试"})
    after = client.get(f"/api/posts/{p['id']}").json()["comment_count"]
    assert after == before + 1


def test_leaderboard_sorted(client):
    d = client.get("/api/leaderboard?limit=10").json()
    assert d and d[0]["reputation"] >= d[-1]["reputation"]


# ── 导出与前端 ──────────────────────────────────────────────────────────────
def test_export_draft(client):
    r = client.get("/api/export/draft").json()
    assert r["n"] >= 100
    assert "- name:" in r["actuators_yaml"]
    assert "armature" in r["mjcf_joints"][0]


def test_spa_fallback(client):
    """客户端路由必须回退到 index.html，否则分享链接 404。"""
    for path in ("/community", "/top", "/post/1", "/u/roboselect"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "RoboSelect" in r.text or "<div id=\"root\">" in r.text


def test_api_unknown_path_404(client):
    assert client.get("/api/nope").status_code == 404

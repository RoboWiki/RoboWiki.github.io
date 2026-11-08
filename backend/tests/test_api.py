"""RoboWiki API 测试。

    cd backend && python -m pytest -q
    # 或 python -m unittest discover -s tests -v

每个测试类用独立的临时库（ROBOWIKI_DB_PATH），不碰仓库里的 robowiki.db。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# 必须在 import app 之前设置，settings 在 import 时实例化
_TMP = tempfile.mkdtemp(prefix="roboselect-test-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"
os.environ["ROBOWIKI_BOT_TOKEN"] = "test-bot-token"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]


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


def auth_header(c: TestClient, handle="robowiki", password="robowiki") -> dict:
    r = c.post("/api/auth/login", json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── 目录 ────────────────────────────────────────────────────────────────────
def test_health_and_stats(client):
    assert client.get("/api/health").json()["ok"] is True
    s = client.get("/api/stats").json()
    assert s["parts"] >= 40
    assert s["with_armature"] >= 30
    assert s["users"] >= 2


def test_catalog_facets_are_scoped(client):
    """facets 里的厂商必须真的在该品类下有零件。

    注意：不能断言「某个厂商只出现在一个品类」—— 达妙既做关节电机也做 IMU
    （DM-IMU-L1），跨品类经营是常态。要测的是**分面数据与品类一致**。
    """
    for cat in ("actuator", "imu", "lidar", "camera", "module"):
        d = client.get("/api/catalog", params={"category": cat}).json()
        for v in d["vendors"]:
            assert v["n"] > 0, f"{cat} 的 {v['vendor']} 条数为 0"
        assert sum(v["n"] for v in d["vendors"]) == sum(
            f["n"] for f in d["facets"] if f["category"] == cat
        ) or d["vendors"][0]["n"] > 0



def test_catalog_empty_categories_match_facets(client):
    """待补充品类必须由实际计数推导，不能和 facets 自相矛盾。"""
    d = client.get("/api/catalog").json()
    present = {f["category"] for f in d["facets"] if f["n"] > 0}
    assert not (set(d["empty_categories"]) & present)
    assert set(d["empty_categories"]) <= set(d["categories"])
    assert d["data_version"] and d["site_url"]


def test_api_responses_are_not_cacheable(client):
    r = client.get("/api/meta")
    assert r.headers["cache-control"] == "no-store"


def test_catalog_rejects_unknown_category(client):
    r = client.get("/api/catalog", params={"category": "not_a_category"})
    assert r.status_code == 422


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


def test_sort_whitelist_rejects_unknown(client):
    r = client.get("/api/parts", params={"sort": "id;DROP TABLE parts"})
    assert r.status_code == 422
    assert client.get("/api/health").status_code == 200


def test_armature_equals_n2j(client):
    """armature 必须等于 N²·J —— 读错口径会差 10⁴ 倍。"""
    d = client.get("/api/parts", params={"category": "actuator",
                                          "has_armature": True, "limit": 200}).json()
    checked = 0
    for p in d["items"]:
        s = p["specs"]
        j, g, arm = s.get("rotor_inertia_kgm2"), s.get("gear"), s.get("armature_kgm2")
        if j and g and arm:
            assert abs(arm / (j * g * g) - 1) < 1e-6, f"{p['id']} armature != N²·J"
            checked += 1
    # 归档导入的行大多没有 armature（商品页不给），只对**人工核对的 A 级**
    # 要求「能复算的样本足够多」；否则这个断言会随着导入规模变成噪声
    assert checked >= 30, f"只校验到 {checked} 条，A 级数据可能被覆盖了"


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

    seeded = client.get("/api/posts", params={"author": "robowiki", "limit": 50}).json()
    for p in seeded["items"]:
        assert not p["own_hardware"], "站方不能声称「实测」"
        assert p["rating"] is None, "站方不打用户评分"
        assert p["title"].startswith("编者按"), "站方内容必须自带来源标注"


def test_review_appears_on_its_part(client):
    """评价挂在零件上 → 零件详情里能看到。用 API 真写一条，不依赖种子。"""
    h = auth_header(client)
    part_id = "达妙-dm-dm-j4340-2ec-v1-1"
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
    r = client.post("/api/auth/login", json={"handle": "robowiki", "password": "wrong"})
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
        "part_id": "达妙-dm-dm-j4340-2ec-v1-1"})
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
    assert r["n"] >= 30
    assert "- name:" in r["actuators_yaml"]
    assert "armature" in r["mjcf_joints"][0]


def test_console_legacy_redirects(client):
    """旧 /console 客户端路由已迁到静态站，保留 308 跳转，避免老通知断链。"""
    cases = {
        "/console": "/community.html",
        "/console/community": "/community.html",
        "/console/top": "/top.html",
        "/console/post/1": "/post.html?id=1",
        "/console/u/roboselect": "/u.html?handle=roboselect",
        "/console/submissions": "/admin.html?tab=submissions",
        "/console/reports": "/admin.html?tab=reports",
        "/console/semantics": "/semantics.html",
        "/login": "/login.html",
    }
    for path, target in cases.items():
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 308, path
        assert r.headers["location"] == target, path


def test_api_root_is_not_a_static_site(client):
    """API 不再托管静态站；未知非 API 路径统一 404，静态站由 Pages/1Panel 提供。"""
    r = client.get("/")
    assert r.status_code == 404


def test_api_unknown_path_404(client):
    assert client.get("/api/nope").status_code == 404


# ── v1 契约 ─────────────────────────────────────────────────────────────────
def test_api_v1_meta_and_release_header(client):
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    d = r.json()
    assert d["api_version"] == "v1"
    assert "data_version" in d
    assert r.headers["X-RoboWiki-API-Version"] == "v1"
    assert r.headers["X-RoboWiki-Data-Version"] == d["data_version"]


def test_api_legacy_alias_still_works(client):
    assert client.get("/api/meta").json()["api_version"] == "v1"
    assert client.get("/api/parts", params={"limit": 1}).status_code == 200


def test_bootstrap_admin_creates_staff(client, monkeypatch):
    from app.core.config import settings
    from app.core.db import bootstrap_admin, session
    monkeypatch.setattr(settings, "admin_handle", "opsadmin")
    monkeypatch.setattr(settings, "admin_password", "secret12345")
    db = session()
    try:
        assert bootstrap_admin(db) == "opsadmin"
    finally:
        db.close()
    r = client.post("/api/auth/login", json={"handle": "opsadmin",
                                            "password": "secret12345"})
    assert r.status_code == 200
    assert r.json()["user"]["is_staff"] is True


def test_openapi_has_security_schemes(client):
    r = client.get("/api/v1/openapi.json")
    assert r.status_code == 200
    d = r.json()
    assert "bearerAuth" in d["components"]["securitySchemes"]
    assert "botToken" in d["components"]["securitySchemes"]
    assert d["paths"]["/api/v1/bot/answer"]["get"]["security"] == [{"botToken": []}]
    assert d["paths"]["/api/v1/submissions"]["post"]["security"] == [{"bearerAuth": []}]


def test_ready_checks_database_and_request_id(client):
    r = client.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.json()["db"] == "ok"
    assert r.headers["X-Request-ID"]

    r = client.get("/api/v1/health", headers={"X-Request-ID": "trace-123"})
    assert r.headers["X-Request-ID"] == "trace-123"


def test_parts_sort_price_and_reject_unknown(client):
    r = client.get("/api/v1/parts", params={"sort": "price", "order": "desc", "limit": 3})
    assert r.status_code == 200
    prices = [x["price_cny"] for x in r.json()["items"] if x["price_cny"] is not None]
    assert prices == sorted(prices, reverse=True)
    assert client.get("/api/v1/parts", params={"sort": "typo"}).status_code == 422


def test_register_rejects_non_ascii_handle(client):
    r = client.post("/api/auth/register", json={
        "handle": "管理员", "display_name": "x", "password": "testpass123",
    })
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={
        "handle": "abcｄ", "display_name": "x", "password": "testpass123",
    })
    assert r.status_code == 422


def test_public_part_hides_internal_fields(client):
    d = client.get("/api/v1/parts", params={"category": "actuator", "limit": 1}).json()
    assert d["items"]
    item = d["items"][0]
    assert "source_tier" in item
    for internal in ("origin", "search"):
        assert internal not in item


# ── 数据提案 / outbox ───────────────────────────────────────────────────────
def test_submission_review_enqueues_outbox(client):
    h = auth_header(client)  # robowiki / staff
    r = client.post("/api/v1/submissions", headers=h, json={
        "kind": "part_patch",
        "target_id": "hota-d6-pro",
        "payload": {"price_cny": 3288.0},
        "evidence": {"source_url": "https://example.com/manual", "note": "test"},
    })
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert r.json()["status"] == "pending"
    preview = r.json()["evidence"]["preview"][0]
    assert preview["field"] == "price_cny"
    assert preview["new_value"] == 3288.0

    r = client.post(f"/api/v1/submissions/{sid}/review", headers=h, json={
        "decision": "accepted", "reason_code": "ok", "note": "test",
    })
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "accepted"
    assert r.json()["reviews"][0]["decision"] == "accepted"

    r = client.get("/api/v1/submissions/outbox", headers=h)
    assert r.status_code == 200
    assert any(x["submission_id"] == sid and x["status"] == "pending"
               for x in r.json())

    import os
    import shutil
    from app.worker import process_one
    outdir = ROOT / "backend" / ".tmp-outbox"
    shutil.rmtree(outdir, ignore_errors=True)
    outdir.mkdir(parents=True)
    os.environ["ROBOWIKI_OUTBOX_DIR"] = str(outdir)
    assert process_one() is True
    assert list(outdir.glob("submission-*.json"))
    shutil.rmtree(outdir, ignore_errors=True)


def test_submission_requires_evidence(client):
    h = auth_header(client)
    r = client.post("/api/v1/submissions", headers=h, json={
        "kind": "part_patch", "target_id": "hota-d6-pro",
        "payload": {"price_cny": 1.0}, "evidence": {},
    })
    assert r.status_code == 422


def test_submission_preview_is_server_generated(client):
    h = auth_header(client)
    r = client.post("/api/v1/submissions", headers=h, json={
        "kind": "part_patch", "target_id": "hota-d6-pro",
        "payload": {"price_cny": 1.0},
        "evidence": {"note": "test preview", "source_url": "https://example.com",
                     "preview": [{"field": "notes", "old_value": "a", "new_value": "b"}]},
    })
    assert r.status_code == 201
    preview = r.json()["evidence"]["preview"]
    assert preview[0]["field"] == "price_cny"
    assert preview[0]["new_value"] == 1.0


def test_submission_rejects_bad_value_shapes(client):
    h = auth_header(client)
    for payload in ({"price_cny": [1, 2, 3]},
                    {"specs.tau_peak_Nm": {"x": 1}},
                    {"specs.use_cases": [{"x": 1}]}):
        r = client.post("/api/v1/submissions", headers=h, json={
            "kind": "part_patch", "target_id": "hota-d6-pro",
            "payload": payload,
            "evidence": {"note": "shape test", "source_url": "https://example.com"},
        })
        assert r.status_code == 422, payload


def test_submission_rejects_bad_value_domains(client):
    h = auth_header(client)
    for payload in ({"price_cny": -1}, {"price_cny": "abc"},
                    {"source_tier": "Z"}, {"last_checked": "not-a-date"},
                    {"url": "ftp://example.com/file"}):
        r = client.post("/api/v1/submissions", headers=h, json={
            "kind": "part_patch", "target_id": "hota-d6-pro",
            "payload": payload,
            "evidence": {"note": "domain test", "source_url": "https://example.com"},
        })
        assert r.status_code == 422, payload


def test_review_post_updates_rating_aggregate(client):
    reg = client.post("/api/v1/auth/register", json={
        "handle": "reviewrating", "display_name": "Review Rating",
        "password": "pass1234"})
    assert reg.status_code == 201, reg.text
    h = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    part = "feetech-st-3250-c001"
    before = client.get(f"/api/v1/ratings/{part}").json()["count"]
    r = client.post("/api/v1/posts", headers=h, json={
        "kind": "review", "title": "评价与评分同源测试",
        "body": "这是一条用于验证评价和评分聚合一致性的测试内容。",
        "part_id": part, "rating": 5, "own_hardware": True})
    assert r.status_code == 201, r.text
    after = client.get(f"/api/v1/ratings/{part}", headers=h).json()
    assert after["count"] == before + 1
    assert after["mine"]["score"] == 5


def test_cannot_vote_own_content(client):
    h = auth_header(client)
    r = client.post("/api/v1/posts", headers=h, json={
        "kind": "discussion", "title": "自投票拦截测试",
        "body": "这是一条用于验证不能给自己投票的测试内容。"})
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    v = client.post("/api/v1/votes", headers=h, json={
        "target_kind": "post", "target_id": pid, "value": 1})
    assert v.status_code == 403


def test_submission_rejects_non_http_source(client):
    h = auth_header(client)
    r = client.post("/api/v1/submissions", headers=h, json={
        "kind": "part_patch", "target_id": "hota-d6-pro",
        "payload": {"price_cny": 1.0},
        "evidence": {"note": "测试来源校验", "source_url": "javascript:alert(1)"},
    })
    assert r.status_code == 422
    r = client.post("/api/v1/submissions", headers=h, json={
        "kind": "part_patch", "target_id": "hota-d6-pro",
        "payload": {"price_cny": 1.0},
        "evidence": {"note": "", "source_url": "https://example.com"},
    })
    assert r.status_code == 422


def test_non_staff_cannot_review(client):
    h = auth_header(client, "demo1", "robowiki")
    r = client.post("/api/v1/submissions/1/review", headers=h, json={
        "decision": "accepted",
    })
    assert r.status_code == 403


# ── 群机器人只读问答 ────────────────────────────────────────────────────────
BOT = {"X-Bot-Token": "test-bot-token"}


def test_bot_answer_is_one_line_with_url_and_version(client):
    r = client.get("/api/v1/bot/answer", params={"q": "m3508"}, headers=BOT)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["found"] is True
    assert d["part"]["model"].lower().startswith("m3508")
    assert d["url"].endswith(".html")
    assert d["data_version"]
    assert "\n" not in d["answer"]
    assert d["part"]["model"] in d["answer"]
    assert "已核对" not in d["answer"]  # B 级不显示核对信号


def test_bot_answer_uses_connector_rated_fields(client):
    r = client.get("/api/v1/bot/answer", params={"q": "xt30"}, headers=BOT)
    assert r.status_code == 200
    d = r.json()
    assert d["part"]["id"] == "amass-xt30"
    assert "20 A" in d["answer"] and "500 V" in d["answer"]


def test_bot_wildcards_do_not_match_everything(client):
    r = client.get("/api/v1/bot/answer", params={"q": "%"}, headers=BOT)
    assert r.status_code == 200
    assert r.json()["found"] is False


def test_bot_requires_token(client):
    assert client.get("/api/v1/bot/answer", params={"q": "ak80"}).status_code == 401
    assert client.get("/api/v1/bot/answer", params={"q": "ak80"},
                      headers={"X-Bot-Token": "wrong"}).status_code == 401


def test_bot_not_found_returns_search_hint(client):
    r = client.get("/api/v1/bot/answer", params={"q": "不存在型号zzz"}, headers=BOT)
    assert r.status_code == 200
    d = r.json()
    assert d["found"] is False
    assert d["url"].endswith("/catalog.html")
    assert "没找到" in d["answer"]


def test_worker_retries_failed_job(client, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app import worker
    from app.core.db import session
    from app.models import Outbox

    db = session()
    job = Outbox(action="part_patch", payload={"target_id": "x", "changes": {}},
                 idempotency_key="retry-test")
    db.add(job)
    db.commit()
    db.refresh(job)
    jid = job.id
    db.close()

    calls: list[int] = []

    def flaky(_job, _data_dir):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("boom")
        return {"dry_run": True, "file": "x.json"}

    monkeypatch.setattr(worker, "publish_job", flaky)
    assert worker.process_one() is True
    db = session()
    j = db.get(Outbox, jid)
    assert j.status == "pending" and j.attempts == 1 and "boom" in (j.last_error or "")
    j.next_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.add(j)
    db.commit()
    db.close()

    assert worker.process_one() is True
    db = session()
    j = db.get(Outbox, jid)
    assert j.status == "done" and j.attempts == 2 and j.result["dry_run"] is True
    db.close()


def test_staff_can_retry_failed_outbox(client):
    from app.core.db import session
    from app.models import Outbox

    db = session()
    row = Outbox(action="part_patch", payload={}, idempotency_key="retry-api",
                 status="failed", attempts=5, last_error="boom")
    db.add(row)
    db.commit()
    db.refresh(row)
    oid = row.id
    db.close()

    h = auth_header(client)
    r = client.post(f"/api/v1/submissions/outbox/{oid}/retry", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "pending" and r.json()["last_error"] is None


# ── 材质库 API ──────────────────────────────────────────────────────────────
def test_materials_list_and_meta(client):
    r = client.get("/api/v1/materials", params={"limit": 200})
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 36 and len(d["items"]) == 36
    assert d["data_version"]
    assert {x["category"] for x in d["items"]} == {"material", "process"}

    m = client.get("/api/v1/materials/meta").json()
    assert m["materials"] == 27 and m["processes"] == 9
    assert len(m["groups"]) >= 5


def test_material_detail_and_related(client):
    r = client.get("/api/v1/materials/proc-cnc")
    assert r.status_code == 200
    d = r.json()
    assert d["category"] == "process"
    assert d["specs"]["tolerance_mm"] == 0.05
    assert d["related"] and all(x["category"] == "material" for x in d["related"])

    r = client.get("/api/v1/materials/mat-alu-6061-t6")
    assert r.status_code == 200
    assert r.json()["related"]
    assert client.get("/api/v1/materials/nope").status_code == 404


def test_materials_search_and_filters(client):
    d = client.get("/api/v1/materials", params={"q": "CNC"}).json()
    assert d["total"] >= 1
    assert any(x["id"] == "proc-cnc" for x in d["items"])
    d = client.get("/api/v1/materials", params={"category": "material",
                                                "group": "metal"}).json()
    assert d["total"] >= 1
    assert all(x["category"] == "material" and x["group"] == "metal"
               for x in d["items"])


# ── 邮箱验证 / 找回密码 ─────────────────────────────────────────────────────
def test_email_verify_and_password_reset(client, monkeypatch):
    import re
    from app.api.routes import auth as auth_route

    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(auth_route, "send_email",
                        lambda to, subject, text, html=None: sent.append((to, subject, text)))
    r = client.post("/api/auth/register", json={
        "handle": "mailuser", "display_name": "Mail User",
        "email": "mailuser@example.com", "password": "oldpass123",
    })
    assert r.status_code == 201, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert r.json()["user"]["email_verified"] is False

    r = client.post("/api/auth/email/verify/request", headers=h)
    assert r.status_code == 200 and sent
    token = re.search(r"令牌：(\S+)", sent[-1][2]).group(1)
    r = client.post("/api/auth/email/verify", json={"token": token})
    assert r.status_code == 200 and r.json()["email_verified"] is True
    assert client.post("/api/auth/email/verify", json={"token": token}).status_code == 400

    r = client.post("/api/auth/password/forgot", json={"email": "mailuser@example.com"})
    assert r.status_code == 202 and len(sent) == 2
    token = re.search(r"令牌：(\S+)", sent[-1][2]).group(1)
    r = client.post("/api/auth/password/reset",
                    json={"token": token, "password": "newpass123"})
    assert r.status_code == 200
    assert client.post("/api/auth/login", json={
        "handle": "mailuser", "password": "oldpass123"}).status_code == 401
    assert client.post("/api/auth/login", json={
        "handle": "mailuser", "password": "newpass123"}).status_code == 200

    before = len(sent)
    r = client.post("/api/auth/password/forgot", json={"email": "none@example.com"})
    assert r.status_code == 202 and len(sent) == before
    assert client.post("/api/auth/password/reset",
                       json={"token": "x" * 20, "password": "newpass123"}).status_code == 400


# ── 移动端轻量接口 ───────────────────────────────────────────────────────────
def test_compact_part_list_omits_specs_for_mobile(client):
    full = client.get("/api/v1/parts", params={"limit": 3}).json()
    assert full.get("data_version")
    assert "specs" in full["items"][0]

    card = client.get("/api/v1/parts", params={"limit": 3, "compact": "true"}).json()
    assert card["total"] == full["total"]
    item = card["items"][0]
    assert "specs" not in item and "derived" not in item
    assert "title" in item and "image_url" in item and "price_cny" in item
    assert item["web_path"].startswith("/parts/") and item["web_path"].endswith(".html")
    assert item["web_path"].count(".html") == 1


def test_material_detail_carries_data_version(client):
    rows = client.get("/api/v1/materials", params={"limit": 1}).json()
    mid = rows["items"][0]["id"]
    detail = client.get(f"/api/v1/materials/{mid}").json()
    assert detail.get("data_version")

"""举报与处置：用户报，站务审，内容可隐藏/恢复。

举报本身不加隐藏；处置动作才改变可见性。这样站务不会因为一条匿名举报
就把内容下架，所有动作都有 note 与处置人留痕。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-reports-")
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
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)


def auth(c: TestClient, handle="robowiki", password="robowiki") -> dict:
    r = c.post("/api/auth/login", json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_post(c: TestClient, title: str) -> int:
    r = c.post("/api/posts", headers=auth(c, "demo1"), json={
        "kind": "discussion", "title": title,
        "body": "举报测试用的正文，足够长以通过校验。"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def report(c: TestClient, kind: str, target_id: int, reason="spam") -> dict:
    return c.post("/api/reports", headers=auth(c, "demo1"), json={
        "target_kind": kind, "target_id": target_id,
        "reason": reason, "detail": "测试举报"})


# ── 举报入口 ────────────────────────────────────────────────────────────────
def test_report_requires_login_and_valid_target(client):
    assert client.post("/api/reports", json={
        "target_kind": "post", "target_id": 1, "reason": "spam"}).status_code == 401

    h = auth(client, "demo1")
    assert client.post("/api/reports", headers=h, json={
        "target_kind": "post", "target_id": 999999, "reason": "spam",
    }).status_code == 404
    assert client.post("/api/reports", headers=h, json={
        "target_kind": "post", "target_id": 999999, "reason": "not-a-reason",
    }).status_code == 422
    assert client.post("/api/reports", headers=h, json={
        "target_kind": "user", "target_id": 1, "reason": "spam",
    }).status_code == 422


def test_report_is_idempotent_per_reporter(client):
    pid = make_post(client, "举报去重测试")
    first = report(client, "post", pid)
    assert first.status_code == 201, first.text
    assert first.json()["status"] == "open"
    dup = report(client, "post", pid)
    assert dup.status_code == 409


def test_admin_queue_shows_context_and_requires_staff(client):
    pid = make_post(client, "队列上下文测试")
    report(client, "post", pid)

    assert client.get("/api/admin/reports").status_code == 401
    assert client.get("/api/admin/reports", headers=auth(client, "demo1")).status_code == 403

    rows = client.get("/api/admin/reports", headers=auth(client)).json()["items"]
    row = next(r for r in rows if r["target_kind"] == "post" and r["target_id"] == pid)
    assert row["status"] == "open"
    assert row["reporter"]["handle"] == "demo1"
    assert row["target"]["title"] == "队列上下文测试"
    assert row["target"]["author"]["handle"] == "demo1"


# ── 处置动作 ────────────────────────────────────────────────────────────────
def test_hide_and_restore_post(client):
    pid = make_post(client, "隐藏与恢复测试")
    rid = report(client, "post", pid).json()["id"]
    staff = auth(client)

    plain = auth(client, "demo1")
    assert client.get(f"/api/posts/{pid}", headers=plain).status_code == 200

    r = client.patch(f"/api/admin/reports/{rid}", headers=staff, json={
        "action": "hide", "note": "测试：确认违规后隐藏"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "resolved"

    assert client.get(f"/api/posts/{pid}", headers=plain).status_code == 404
    feed = client.get("/api/posts", params={"limit": 100}).json()
    assert all(p["id"] != pid for p in feed["items"])
    assert client.get(f"/api/posts/{pid}", headers=staff).status_code == 200

    r = client.patch(f"/api/admin/reports/{rid}", headers=staff, json={
        "action": "restore", "note": "测试：申诉通过后恢复"})
    assert r.status_code == 200
    assert client.get(f"/api/posts/{pid}", headers=plain).status_code == 200
    feed = client.get("/api/posts", params={"limit": 100}).json()
    assert any(p["id"] == pid for p in feed["items"])


def test_hide_comment_also_hides_replies(client):
    pid = make_post(client, "评论隐藏测试")
    h = auth(client, "demo1")
    root = client.post(f"/api/posts/{pid}/comments", headers=h,
                       json={"body": "根评论"}).json()["id"]
    child = client.post(f"/api/posts/{pid}/comments", headers=h,
                        json={"body": "回复评论", "parent_id": root}).json()["id"]
    rid = report(client, "comment", root).json()["id"]

    assert client.patch(f"/api/admin/reports/{rid}", headers=auth(client), json={
        "action": "hide", "note": "测试：隐藏整条回复"}).status_code == 200
    tree = client.get(f"/api/posts/{pid}/comments").json()
    assert not any(c["id"] == root for c in tree)
    assert all(not any(r["id"] == child for r in c["replies"]) for c in tree)


def test_dismiss_keeps_content(client):
    pid = make_post(client, "驳回举报测试")
    rid = report(client, "post", pid).json()["id"]
    r = client.patch(f"/api/admin/reports/{rid}", headers=auth(client), json={
        "action": "dismiss", "note": "测试：不属于违规"})
    assert r.status_code == 200
    assert r.json()["status"] == "dismissed"
    assert client.get(f"/api/posts/{pid}").status_code == 200


def test_wiki_comment_report_and_hide(client):
    h = auth(client, "demo1")
    cid = client.post("/api/wiki/comments", headers=h, json={
        "page": "parts/actuator/cubemars", "body": "文档讨论测试"}).json()["id"]
    rid = report(client, "wiki_comment", cid).json()["id"]
    assert client.patch(f"/api/admin/reports/{rid}", headers=auth(client), json={
        "action": "hide", "note": "测试：隐藏文档讨论"}).status_code == 200
    d = client.get("/api/wiki/comments", params={
        "page": "parts/actuator/cubemars"}).json()
    assert all(c["id"] != cid for c in d["comments"])


def test_invalid_action_is_rejected(client):
    pid = make_post(client, "处置动作校验")
    rid = report(client, "post", pid).json()["id"]
    assert client.patch(f"/api/admin/reports/{rid}", headers=auth(client), json={
        "action": "delete-everything", "note": "测试非法动作"}).status_code == 422


# ── 处置动作的权限与留痕 ────────────────────────────────────────────────────
def test_resolve_requires_staff_and_a_note(client):
    """举报人不能自己处置自己的举报；note 必须写清楚，否则队列里只剩一个状态。"""
    pid = make_post(client, "处置权限测试")
    rid = report(client, "post", pid).json()["id"]
    staff = auth(client)

    assert client.patch(f"/api/admin/reports/{rid}",
                        headers=auth(client, "demo1"), json={
                            "action": "dismiss", "note": "我是举报人"}).status_code == 403
    assert client.patch(f"/api/admin/reports/{rid}", json={
        "action": "dismiss", "note": "未登录"}).status_code == 401
    # note 至少 2 个字的约束在 schema 层
    assert client.patch(f"/api/admin/reports/{rid}", headers=staff, json={
        "action": "dismiss", "note": "x"}).status_code == 422
    assert client.patch("/api/admin/reports/999999", headers=staff, json={
        "action": "dismiss", "note": "举报不存在"}).status_code == 404

    # 以上全部被拒：举报状态必须还是 open，内容也没被隐藏
    rows = client.get("/api/admin/reports", headers=staff).json()["items"]
    assert next(r for r in rows if r["id"] == rid)["status"] == "open"
    assert client.get(f"/api/posts/{pid}").status_code == 200


def test_resolving_report_on_deleted_target_is_404(client):
    """目标被硬删后，举报行还在队列里；处置必须给出 404 而不是 500。"""
    from app.core.db import session
    from app.models import Post

    pid = make_post(client, "目标被删除的举报")
    rid = report(client, "post", pid).json()["id"]

    db = session()
    try:
        row = db.get(Post, pid)
        assert row is not None
        db.delete(row)
        db.commit()
    finally:
        db.close()

    r = client.patch(f"/api/admin/reports/{rid}", headers=auth(client), json={
        "action": "hide", "note": "目标已删除"})
    assert r.status_code == 404, r.text
    # 举报本身没有被误标成 resolved
    rows = client.get("/api/admin/reports", headers=auth(client)).json()["items"]
    assert next(x for x in rows if x["id"] == rid)["status"] == "open"

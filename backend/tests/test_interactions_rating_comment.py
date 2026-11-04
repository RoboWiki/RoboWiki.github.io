"""互动核心：评分聚合 / 改分 / 撤销 / review→rating / 评论 / 回复 / 举报。

这些用例钉的是「链路没接上」或「静默失真」：
  · 没评过返回 0 分而不是「未知」（应该是 avg=None）
  · 同一人再提交变成两条票（应该只改分）
  · 评价帖写了、评分聚合里却没有（review 与 Rating 必须同源）
  · 未登录也能写（必须 401）
  · 举报没有落到 /reports 契约（target_kind / reason / 去重）

不依赖具体零件 id：从 /api/v1/parts 取真实条目，避免目录更新后测试假失败。
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="roboselect-interactions-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"

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


@pytest.fixture(scope="module", autouse=True)
def _clean_ratings(client):
    """评分是全局表：其它模块可能已经写过票，本模块先清空再从 0 验证。"""
    from sqlmodel import delete
    from app.core.db import session
    from app.models import Rating
    with session() as db:
        db.exec(delete(Rating))
        db.commit()
    yield


@pytest.fixture(scope="module")
def parts(client):
    rows = client.get("/api/v1/parts", params={"limit": 8}).json()["items"]
    ids = [r["id"] for r in rows]
    assert len(ids) >= 6, "目录条数不足，无法覆盖评分/评论场景"
    return ids


def register(client: TestClient) -> dict:
    handle = f"ix{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/auth/register", json={
        "handle": handle, "display_name": handle, "password": "pass1234"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def login(client: TestClient, handle="robowiki", password="robowiki") -> dict:
    r = client.post("/api/v1/auth/login", json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_post(client: TestClient, headers: dict, title: str, body: str) -> int:
    r = client.post("/api/v1/posts", headers=headers, json={
        "kind": "discussion", "title": title, "body": body})
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── 评分：未知 / 改分 / 撤销 / 聚合 ────────────────────────────────────────
def test_unrated_part_is_unknown_not_zero(client, parts):
    d = client.get(f"/api/v1/ratings/{parts[5]}").json()
    assert d["count"] == 0
    assert d["avg"] is None, "没评过不等于 0 分"
    assert d["histogram"] == {str(i): 0 for i in range(1, 6)}
    assert d["own_hardware_count"] == 0
    assert d["mine"] is None
    assert d["low_sample"] is True
    assert d["rank_score"] is None, "空样本不参与排序"


def test_change_score_is_same_vote(client, parts):
    h = register(client)
    part = parts[0]

    r1 = client.post(f"/api/v1/ratings/{part}", headers=h, json={
        "score": 5, "own_hardware": True, "note": "装过机"})
    assert r1.status_code == 201, r1.text
    d1 = r1.json()
    assert d1["created"] is True
    assert d1["count"] == 1 and d1["avg"] == 5.0
    assert d1["histogram"]["5"] == 1
    assert d1["own_hardware_count"] == 1
    assert d1["own_hardware_avg"] == 5.0
    assert d1["low_sample"] is True, "1 票必须标样本不足"
    assert d1["rank_score"] is not None
    assert d1["mine"]["score"] == 5 and d1["mine"]["hidden"] is False

    # 再投一次是改分，不是加票
    r2 = client.post(f"/api/v1/ratings/{part}", headers=h, json={
        "score": 2, "own_hardware": False})
    d2 = r2.json()
    assert d2["created"] is False
    assert d2["count"] == 1, "同一人不该变成两票"
    assert d2["avg"] == 2.0
    assert d2["histogram"]["2"] == 1 and d2["histogram"]["5"] == 0
    assert d2["own_hardware_count"] == 0
    assert d2["own_hardware_avg"] is None, "没有装机样本不等于 0 分"
    assert d2["mine"]["score"] == 2


def test_delete_score_returns_to_unknown(client, parts):
    h1, h2 = register(client), register(client)
    part = parts[1]

    assert client.post(f"/api/v1/ratings/{part}", headers=h1,
                       json={"score": 5}).status_code == 201
    assert client.post(f"/api/v1/ratings/{part}", headers=h2,
                       json={"score": 3}).status_code == 201
    d = client.get(f"/api/v1/ratings/{part}").json()
    assert d["count"] == 2 and d["avg"] == 4.0

    assert client.delete(f"/api/v1/ratings/{part}", headers=h1).status_code == 204
    d = client.get(f"/api/v1/ratings/{part}").json()
    assert d["count"] == 1 and d["avg"] == 3.0
    assert client.delete(f"/api/v1/ratings/{part}", headers=h1).status_code == 404

    assert client.delete(f"/api/v1/ratings/{part}", headers=h2).status_code == 204
    d = client.get(f"/api/v1/ratings/{part}").json()
    assert d["count"] == 0 and d["avg"] is None
    assert d["histogram"] == {str(i): 0 for i in range(1, 6)}


def test_summary_and_top_rated_share_rank_score(client, parts):
    """1 条 5 分不该压过 3 条 4 分；summary 与 top_rated 用同一套口径。"""
    h1, h2, h3, h4 = (register(client) for _ in range(4))
    thin, thick = parts[3], parts[4]

    assert client.post(f"/api/v1/ratings/{thin}", headers=h1,
                       json={"score": 5}).status_code == 201
    for h in (h2, h3, h4):
        assert client.post(f"/api/v1/ratings/{thick}", headers=h,
                           json={"score": 4}).status_code == 201

    summary = client.get("/api/v1/ratings/summary").json()
    assert summary["parts"][thin]["count"] == 1
    assert summary["parts"][thick]["count"] == 3
    assert summary["parts"][thick]["avg"] == 4.0
    assert summary["parts"][thin]["rank_score"] is not None
    assert summary["parts"][thick]["rank_score"] > summary["parts"][thin]["rank_score"]

    top = client.get("/api/v1/ratings", params={"min_count": 1, "limit": 200}).json()
    ids = [i["part_id"] for i in top["items"]]
    assert ids.index(thick) < ids.index(thin), "排序必须用 rank_score，而不是裸均分"
    scores = [i["rank_score"] for i in top["items"]]
    assert scores == sorted(scores, reverse=True)
    assert all("avg" in i and "count" in i for i in top["items"])


# ── 评价帖与评分同源 ────────────────────────────────────────────────────────
def test_review_post_feeds_same_rating(client, parts):
    h = register(client)
    part = parts[2]

    r = client.post("/api/v1/posts", headers=h, json={
        "kind": "review", "title": "互动测试：评价与评分同源",
        "body": "这是一条用于验证评价帖与评分聚合同源的测试正文。",
        "part_id": part, "rating": 4, "own_hardware": True})
    assert r.status_code == 201, r.text
    review_id = r.json()["id"]

    d = client.get(f"/api/v1/ratings/{part}", headers=h).json()
    assert d["count"] == 1 and d["avg"] == 4.0
    assert d["own_hardware_count"] == 1
    assert d["mine"]["score"] == 4 and d["mine"]["own_hardware"] is True

    # 同一人从评分入口改分：仍然是这一票，不该多出一条
    assert client.post(f"/api/v1/ratings/{part}", headers=h,
                       json={"score": 2}).status_code == 201
    d = client.get(f"/api/v1/ratings/{part}", headers=h).json()
    assert d["count"] == 1 and d["avg"] == 2.0

    # 再写一条评价：更新同一票，而不是两票
    r2 = client.post("/api/v1/posts", headers=h, json={
        "kind": "review", "title": "互动测试：评价与评分同源（更新）",
        "body": "同一人改主意后，评价帖与评分仍必须只保留一票。",
        "part_id": part, "rating": 5, "own_hardware": False})
    assert r2.status_code == 201, r2.text
    d = client.get(f"/api/v1/ratings/{part}", headers=h).json()
    assert d["count"] == 1 and d["avg"] == 5.0
    assert d["mine"]["score"] == 5 and d["mine"]["own_hardware"] is False

    feed = client.get("/api/v1/posts", params={
        "kind": "review", "part_id": part, "limit": 20}).json()
    assert any(p["id"] == review_id for p in feed["items"])
    assert all(p["kind"] == "review" and p["part_id"] == part for p in feed["items"])


def test_hidden_review_hides_rating_and_restore_returns_it(client, parts):
    """评价帖被站务隐藏时，同一人同一件的评分也不进公开聚合；恢复后回来。

    Rating 没有 hidden 列，所以可见性在读取时按同源关系派生
    （crud.shadowed_review_keys）；这条用例同时钉住 hide 与 restore 两个方向。
    """
    author, reporter = register(client), register(client)
    part = parts[6]

    review = client.post("/api/v1/posts", headers=author, json={
        "kind": "review", "title": "互动测试：隐藏评价与评分可见性",
        "body": "站务隐藏这条评价后，它对应的评分不应继续出现在公开聚合里。",
        "part_id": part, "rating": 4, "own_hardware": True})
    assert review.status_code == 201, review.text
    review_id = review.json()["id"]
    assert client.get(f"/api/v1/ratings/{part}").json()["count"] == 1

    rid = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "post", "target_id": review_id,
        "reason": "spam", "detail": "测试：隐藏评价同步评分"}).json()["id"]
    staff = login(client)
    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "hide", "note": "测试：确认违规后隐藏"}).status_code == 200

    d = client.get(f"/api/v1/ratings/{part}", headers=author).json()
    assert d["count"] == 0 and d["avg"] is None, "隐藏评价后不能继续计入均分"
    assert d["mine"]["score"] == 4 and d["mine"]["hidden"] is True, \
        "作者仍能看到自己的票，但要标记为已隐藏"
    summary = client.get("/api/v1/ratings/summary").json()
    assert summary["parts"][part]["count"] == 0

    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "restore", "note": "测试：申诉通过后恢复"}).status_code == 200
    d = client.get(f"/api/v1/ratings/{part}", headers=author).json()
    assert d["count"] == 1 and d["avg"] == 4.0
    assert d["mine"]["hidden"] is False


# ── 评论 / 回复 / 举报 ─────────────────────────────────────────────────────
def test_comment_reply_and_report(client):
    author, reporter = register(client), register(client)
    pid = make_post(client, author, "互动测试：评论与举报",
                    "这是一条用于验证评论、回复与举报链路的测试正文。")

    root = client.post(f"/api/v1/posts/{pid}/comments", headers=author,
                       json={"body": "根评论"}).json()
    reply = client.post(f"/api/v1/posts/{pid}/comments", headers=author,
                        json={"body": "二级回复", "parent_id": root["id"]})
    assert reply.status_code == 201, reply.text
    assert reply.json()["parent_id"] == root["id"]

    # 只支持两级：回复的回复必须被拒绝
    assert client.post(f"/api/v1/posts/{pid}/comments", headers=author,
                       json={"body": "三级回复", "parent_id": reply.json()["id"]}
                       ).status_code == 422

    tree = client.get(f"/api/v1/posts/{pid}/comments").json()
    node = next(c for c in tree if c["id"] == root["id"])
    assert any(r["id"] == reply.json()["id"] for r in node["replies"])

    rep = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "comment", "target_id": root["id"],
        "reason": "spam", "detail": "测试：重复广告"})
    assert rep.status_code == 201, rep.text
    assert rep.json()["status"] == "open"

    dup = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "comment", "target_id": root["id"], "reason": "spam"})
    assert dup.status_code == 409, "同一人对同一内容只能举报一次"


def test_wiki_comment_reply_and_report(client):
    author, reporter = register(client), register(client)
    page = f"parts/test/interactions-{uuid.uuid4().hex[:8]}"

    root = client.post("/api/v1/wiki/comments", headers=author,
                       json={"page": page, "body": "文档页根讨论"})
    assert root.status_code == 201, root.text
    reply = client.post("/api/v1/wiki/comments", headers=author,
                        json={"page": page, "body": "文档页回复",
                              "parent_id": root.json()["id"]})
    assert reply.status_code == 201, reply.text
    assert reply.json()["parent_id"] == root.json()["id"]

    # 回复不能跨页
    assert client.post("/api/v1/wiki/comments", headers=author, json={
        "page": page + "-other", "body": "跨页回复",
        "parent_id": root.json()["id"]}).status_code == 422

    d = client.get("/api/v1/wiki/comments", params={"page": page}).json()
    assert d["count"] == 2
    assert d["comments"][0]["parent_id"] is None
    assert d["comments"][1]["parent_id"] == root.json()["id"]

    rep = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "wiki_comment", "target_id": root.json()["id"],
        "reason": "misinfo", "detail": "测试：参数写错"})
    assert rep.status_code == 201, rep.text
    dup = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "wiki_comment", "target_id": root.json()["id"],
        "reason": "other"})
    assert dup.status_code == 409

    # 举报后的处置由站务在 /admin/reports 做；这里只验证入口契约
    assert client.get("/api/v1/admin/reports", headers=author).status_code == 403


# ── 未登录 ──────────────────────────────────────────────────────────────────
def test_writes_require_login(client, parts):
    part = parts[5]
    assert client.get(f"/api/v1/ratings/{part}").status_code == 200, "读评分是公开的"
    assert client.post(f"/api/v1/ratings/{part}",
                       json={"score": 5}).status_code == 401
    assert client.delete(f"/api/v1/ratings/{part}").status_code == 401
    assert client.post("/api/v1/posts", json={
        "kind": "discussion", "title": "未登录发帖",
        "body": "未登录不应该能发帖，这是一段足够长的正文。"}).status_code == 401
    assert client.post("/api/v1/posts/1/comments",
                       json={"body": "未登录评论"}).status_code == 401
    assert client.post("/api/v1/reports", json={
        "target_kind": "comment", "target_id": 1,
        "reason": "spam"}).status_code == 401
    assert client.post("/api/v1/wiki/comments", json={
        "page": "parts/test", "body": "未登录讨论"}).status_code == 401
    assert client.delete("/api/v1/wiki/comments/1").status_code == 401

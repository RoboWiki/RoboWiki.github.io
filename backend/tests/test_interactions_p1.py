"""P1 互动：通知 / 文档页嵌套评论与软删 / 媒体上传 / 内容安全 / 评分同源。

钉住的是「多端接入后最容易静默坏掉」的几条：
  · 回复没有通知、或通知读不掉；
  · wiki 回复没绑根，根分页时回复变孤儿；
  · 删父评论把子评论一起物理删了（线程断裂）；
  · pending 内容游客也能看到；
  · 媒体上传只信 Content-Type（伪造成 html 也能挂到站内）；
  · 内容安全接口没配置时把开发环境卡死；
  · 评价帖与 /ratings 聚合不是同一份事实。

不依赖具体零件 id：从 /api/v1/parts 取真实条目。
"""
from __future__ import annotations

import base64
import os
import pathlib
import shutil
import sys
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="robowiki-p1-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0001"
os.environ["ROBOWIKI_MEDIA_DIR"] = str(pathlib.Path(_TMP) / "media")
# 内容安全默认关闭外部调用：没有 AppID/Secret 时必须放行，而不是报错
os.environ["ROBOWIKI_WECHAT_MP_APPID"] = ""
os.environ["ROBOWIKI_WECHAT_MP_SECRET"] = ""

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.content_safety import check_text  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402

#: 1×1 透明 PNG（68 字节）
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGA"
    "hKmMIQAAAABJRU5ErkJggg=="
)


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
def _isolated_media_dir():
    """媒体目录必须临时：测试写的图不能落到仓库 var/media。

    不用 tmp_path_factory：本机 pytest 的默认临时根不可写（见 tests/conftest.py），
    直接用本模块自己的临时目录。
    """
    d = pathlib.Path(_TMP) / "media"
    old = settings.media_dir
    settings.media_dir = d
    yield d
    settings.media_dir = old
    shutil.rmtree(d, ignore_errors=True)


def register(client: TestClient) -> tuple[dict, int, str]:
    handle = f"p1{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/auth/register", json={
        "handle": handle, "display_name": handle, "password": "pass1234"})
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    me = client.get("/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"}).json()
    return {"Authorization": f"Bearer {token}"}, me["id"], handle


def staff_headers(client: TestClient) -> dict:
    r = client.post("/api/v1/auth/login",
                    json={"handle": "robowiki", "password": "robowiki"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_post(client: TestClient, headers: dict, title: str) -> int:
    r = client.post("/api/v1/posts", headers=headers, json={
        "kind": "discussion", "title": title,
        "body": "这是一条用于验证 P1 互动链路的测试正文。"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── 通知 ────────────────────────────────────────────────────────────────────
def test_comment_reply_creates_notification_and_read_flow(client):
    author, author_id, _ = register(client)
    replier, replier_id, _ = register(client)
    pid = make_post(client, author, "P1 测试：回复通知")
    assert client.get("/api/v1/notifications/unread_count",
                      headers=replier).json()["unread"] == 0

    root = client.post(f"/api/v1/posts/{pid}/comments", headers=author,
                       json={"body": "楼主的根评论"})
    assert root.status_code == 201, root.text
    reply = client.post(f"/api/v1/posts/{pid}/comments", headers=replier,
                        json={"body": "我来回复楼主", "parent_id": root.json()["id"]})
    assert reply.status_code == 201, reply.text

    unread = client.get("/api/v1/notifications/unread_count",
                        headers=author).json()["unread"]
    assert unread >= 1, "被回复必须产生未读通知"

    listing = client.get("/api/v1/notifications", headers=author).json()
    assert listing["unread"] == unread
    note = next(n for n in listing["items"] if n["type"] == "reply")
    assert note["read_at"] is None
    assert str(pid) in (note["link"] or ""), "通知要能直接点回帖子"
    assert note["subject"], "通知不能只有 id"

    # 别人不能读/不能替他标记已读
    assert client.post(f"/api/v1/notifications/{note['id']}/read",
                       headers=replier).status_code == 404
    assert client.post(f"/api/v1/notifications/{note['id']}/read",
                       headers=author).status_code == 200
    assert client.get("/api/v1/notifications/unread_count",
                      headers=author).json()["unread"] == unread - 1

    # 全部已读
    assert client.post("/api/v1/notifications/read-all",
                       headers=author).json()["updated"] >= 0
    assert client.get("/api/v1/notifications/unread_count",
                      headers=author).json()["unread"] == 0
    # 自己回自己不产生通知
    assert client.get("/api/v1/notifications", headers=replier).json()["total"] == 0
    assert author_id != replier_id


def test_report_resolution_notifies_target_author(client):
    author, _, _ = register(client)
    reporter, _, _ = register(client)
    pid = make_post(client, author, "P1 测试：处置通知")
    cid = client.post(f"/api/v1/posts/{pid}/comments", headers=author,
                      json={"body": "这条会被举报"}).json()["id"]

    rid = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "comment", "target_id": cid, "reason": "abuse",
        "detail": "P1 处置通知测试"}).json()["id"]
    staff = staff_headers(client)
    r = client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "hide", "note": "确认违规，隐藏处理"})
    assert r.status_code == 200, r.text

    items = client.get("/api/v1/notifications", headers=author).json()["items"]
    note = next(n for n in items if n["type"] == "moderation")
    assert "隐藏" in note["subject"]
    assert note["body"] == "确认违规，隐藏处理"


# ── 文档页评论：嵌套 / 根分页 / pending / 软删 ──────────────────────────────
def test_wiki_nested_replies_bind_root_and_paginate_by_root(client):
    a, _, _ = register(client)
    b, _, _ = register(client)
    page = f"parts/p1/nested-{uuid.uuid4().hex[:8]}"

    root = client.post("/api/v1/wiki/comments", headers=a,
                       json={"page": page, "body": "根讨论"}).json()
    reply = client.post("/api/v1/wiki/comments", headers=b,
                        json={"page": page, "body": "一级回复",
                              "parent_id": root["id"]})
    assert reply.status_code == 201, reply.text
    deep = client.post("/api/v1/wiki/comments", headers=a,
                       json={"page": page, "body": "二级回复（回复回复）",
                             "parent_id": reply.json()["id"]})
    assert deep.status_code == 201, deep.text

    assert reply.json()["root_id"] == root["id"]
    assert deep.json()["root_id"] == root["id"], "多层回复也必须绑到同一条根"
    assert deep.json()["parent_id"] == reply.json()["id"], "直接父节点要保留"

    d = client.get("/api/v1/wiki/comments", params={"page": page}).json()
    assert d["count"] == 3 and d["root_total"] == 1
    assert d["comments"][0]["parent_id"] is None
    assert d["comments"][0]["root_id"] == root["id"]

    # 再加两条根，按根分页
    for body in ("第二条根", "第三条根"):
        assert client.post("/api/v1/wiki/comments", headers=b,
                           json={"page": page, "body": body}).status_code == 201

    first = client.get("/api/v1/wiki/comments",
                       params={"page": page, "root_limit": 1}).json()
    assert first["root_total"] == 3
    assert first["count"] == 3, "只分页根，回复跟着根一起返回"
    second = client.get("/api/v1/wiki/comments", params={
        "page": page, "root_limit": 1, "root_offset": 1}).json()
    assert second["count"] == 1

    thread = client.get("/api/v1/wiki/comments", params={
        "page": page, "root_id": deep.json()["id"]}).json()
    assert thread["count"] == 3, "传回复 id 也要落到它所属的根"
    assert {c["id"] for c in thread["comments"]} == {
        root["id"], reply.json()["id"], deep.json()["id"]}


def test_wiki_pending_visible_only_to_author_and_staff(client):
    from app.core.db import session
    from app.models import WikiComment

    author, author_id, _ = register(client)
    other, _, _ = register(client)
    page = f"parts/p1/pending-{uuid.uuid4().hex[:8]}"

    with session() as db:
        c = WikiComment(page=page, user_id=author_id, body="待复核内容",
                        status="pending")
        db.add(c)
        db.commit()
        db.refresh(c)
        cid = c.id

    seen = client.get("/api/v1/wiki/comments",
                      params={"page": page}, headers=author).json()
    assert any(x["id"] == cid and x["status"] == "pending"
               for x in seen["comments"]), "作者必须能看到自己的 pending"

    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 0, "游客不能看到 pending"
    assert client.get("/api/v1/wiki/comments", params={"page": page},
                      headers=other).json()["count"] == 0, "其他用户不能看到 pending"

    staff = client.get("/api/v1/wiki/comments", params={"page": page},
                       headers=staff_headers(client)).json()
    assert any(x["id"] == cid for x in staff["comments"]), "站务要能看到待复核队列"

    # pending 不进入页面计数
    counts = client.get("/api/v1/wiki/comment-counts").json()["counts"]
    assert page not in counts


def test_wiki_soft_delete_keeps_children(client):
    from app.core.db import session
    from app.models import WikiComment

    a, _, _ = register(client)
    b, _, _ = register(client)
    other, _, _ = register(client)
    page = f"parts/p1/softdel-{uuid.uuid4().hex[:8]}"

    root = client.post("/api/v1/wiki/comments", headers=a,
                       json={"page": page, "body": "会被删掉的根"}).json()
    reply = client.post("/api/v1/wiki/comments", headers=b,
                        json={"page": page, "body": "子回复要留下",
                              "parent_id": root["id"]}).json()

    assert client.delete(f"/api/v1/wiki/comments/{root['id']}",
                         headers=other).status_code == 403, "非作者/非站务不能删"

    assert client.delete(f"/api/v1/wiki/comments/{root['id']}",
                         headers=a).status_code == 204
    # 重复删除幂等
    assert client.delete(f"/api/v1/wiki/comments/{root['id']}",
                         headers=a).status_code == 204

    d = client.get("/api/v1/wiki/comments", params={"page": page}).json()
    assert d["count"] == 2, "父节点变占位，子节点必须还在"
    tomb = next(c for c in d["comments"] if c["id"] == root["id"])
    assert tomb["deleted"] is True and tomb["body"] == "" and tomb["author"] is None
    child = next(c for c in d["comments"] if c["id"] == reply["id"])
    assert child["deleted"] is False and child["body"] == "子回复要留下"

    with session() as db:
        row = db.get(WikiComment, root["id"])
        assert row is not None, "软删除不能物理删行"
        assert row.deleted_at is not None and row.deleted_by is not None
        assert db.get(WikiComment, reply["id"]).deleted_at is None

    # 站务可以删别人的回复
    assert client.delete(f"/api/v1/wiki/comments/{reply['id']}",
                         headers=staff_headers(client)).status_code == 204
    assert client.get("/api/v1/wiki/comments",
                      params={"page": page}).json()["count"] == 0, \
        "没有可见后代的已删除节点整支不返回"


def test_wiki_reply_to_deleted_or_pending_is_rejected(client):
    from app.core.db import session
    from app.models import WikiComment

    a, a_id, _ = register(client)
    b, _, _ = register(client)
    page = f"parts/p1/reject-{uuid.uuid4().hex[:8]}"
    root = client.post("/api/v1/wiki/comments", headers=a,
                       json={"page": page, "body": "根"}).json()
    client.delete(f"/api/v1/wiki/comments/{root['id']}", headers=a)
    assert client.post("/api/v1/wiki/comments", headers=a, json={
        "page": page, "body": "回复已删除", "parent_id": root["id"]}
    ).status_code == 422

    with session() as db:
        pending = WikiComment(page=page, user_id=a_id, body="待审根",
                              status="pending")
        db.add(pending)
        db.commit()
        db.refresh(pending)
        pending_id = pending.id
    assert client.post("/api/v1/wiki/comments", headers=b, json={
        "page": page, "body": "回复待审", "parent_id": pending_id}
    ).status_code == 422


def test_wiki_report_hides_whole_nested_thread(client):
    """处置根评论必须覆盖多层回复：隐藏后整条线程消失，恢复后原样回来。"""
    a, _, _ = register(client)
    b, _, _ = register(client)
    reporter, _, _ = register(client)
    page = f"parts/p1/moderation-{uuid.uuid4().hex[:8]}"

    root = client.post("/api/v1/wiki/comments", headers=a,
                       json={"page": page, "body": "可能违规的根"}).json()
    reply = client.post("/api/v1/wiki/comments", headers=b,
                        json={"page": page, "body": "一级回复",
                              "parent_id": root["id"]}).json()
    assert client.post("/api/v1/wiki/comments", headers=a, json={
        "page": page, "body": "二级回复", "parent_id": reply["id"]}
    ).status_code == 201

    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 3
    rid = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "wiki_comment", "target_id": root["id"],
        "reason": "misinfo", "detail": "P1 测试：整条线程处置"}).json()["id"]

    staff = staff_headers(client)
    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "hide", "note": "确认违规，整条线程隐藏"}).status_code == 200
    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 0, "多层回复也要一起消失"

    note = next(n for n in client.get(
        "/api/v1/notifications", headers=a).json()["items"]
        if n["type"] == "moderation")
    assert "隐藏" in note["subject"]

    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "restore", "note": "申诉通过，恢复线程"}).status_code == 200
    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 3, "恢复后整条线程原样回来"


def test_restore_does_not_publish_pending_thread(client, monkeypatch):
    """隐藏 pending 再恢复，必须回到 pending，不能变成公开可见。"""
    from app.content_safety import SafetyResult

    a, _, _ = register(client)
    reporter, _, _ = register(client)
    page = f"parts/p1/pending-{uuid.uuid4().hex[:8]}"

    monkeypatch.setattr(
        "app.api.routes.wiki.check_user_text_chunks",
        lambda db, uid, text: SafetyResult(False, checked=True, reason="risky"),
    )
    c = client.post("/api/v1/wiki/comments", headers=a,
                    json={"page": page, "body": "需要人工复核的内容"}).json()
    assert c["status"] == "pending"

    rid = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "wiki_comment", "target_id": c["id"],
        "reason": "misinfo", "detail": "P1 测试：待审内容处置"}).json()["id"]
    staff = staff_headers(client)

    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "hide", "note": "先隐藏"}).status_code == 200
    assert client.patch(f"/api/v1/admin/reports/{rid}", headers=staff, json={
        "action": "restore", "note": "恢复但保持待审"}).status_code == 200

    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 0, "pending 恢复后仍不能公开"
    mine = client.get("/api/v1/wiki/comments", params={"page": page}, headers=a).json()
    assert mine["count"] == 1 and mine["comments"][0]["status"] == "pending"


# ── 媒体 ────────────────────────────────────────────────────────────────────
def test_media_upload_and_fetch(client):
    user, _, _ = register(client)
    assert client.post("/api/v1/media", files={
        "file": ("a.png", PNG_1PX, "image/png")}).status_code == 401

    r = client.post("/api/v1/media", headers=user,
                    files={"file": ("a.png", PNG_1PX, "image/png")})
    assert r.status_code == 201, r.text
    body = r.json()
    assert set(("id", "url", "content_type", "size")) <= set(body)
    assert body["content_type"] == "image/png"
    assert body["size"] == len(PNG_1PX)
    assert body["url"].startswith("/api/v1/media/")

    got = client.get(body["url"])
    assert got.status_code == 200
    assert got.headers["content-type"].startswith("image/png")
    assert got.headers["cache-control"].startswith("public")
    assert got.content == PNG_1PX


def test_media_rejects_type_spoof_and_oversize(client):
    user, _, _ = register(client)

    assert client.post("/api/v1/media", headers=user, files={
        "file": ("x.txt", b"hello", "text/plain")}).status_code == 415
    # 声明 png，实际是 jpeg：不能只信 Content-Type
    fake_jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    assert client.post("/api/v1/media", headers=user, files={
        "file": ("x.png", fake_jpeg, "image/png")}).status_code == 415

    old = settings.media_max_bytes
    settings.media_max_bytes = 32
    try:
        r = client.post("/api/v1/media", headers=user,
                        files={"file": ("big.png", PNG_1PX, "image/png")})
        assert r.status_code == 413, r.text
    finally:
        settings.media_max_bytes = old


def test_media_delete_own_only(client):
    owner, _, _ = register(client)
    other, _, _ = register(client)
    mid = client.post("/api/v1/media", headers=owner,
                      files={"file": ("d.png", PNG_1PX, "image/png")}
                      ).json()

    assert client.delete(f"/api/v1/media/{mid['id']}",
                         headers=other).status_code == 403
    assert client.delete(f"/api/v1/media/{mid['id']}",
                         headers=owner).status_code == 204
    assert client.get(mid["url"]).status_code == 404
    assert client.get("/api/v1/media/not-a-real-id").status_code == 404


# ── 内容安全：未配置必须放行 ────────────────────────────────────────────────
def test_content_safety_passes_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(settings, "wechat_mp_appid", None)
    monkeypatch.setattr(settings, "wechat_mp_secret", None)

    r = check_text("正常的讨论内容")
    assert r.passed is True and r.checked is False, "未配置时不能拦内容"
    r = check_text("带 openid 但未配置", openid="openid-123")
    assert r.passed is True and r.checked is False

    # 建评论链路也照常放行，且落在公开状态
    author, _, _ = register(client)
    page = f"parts/p1/safety-{uuid.uuid4().hex[:8]}"
    c = client.post("/api/v1/wiki/comments", headers=author,
                    json={"page": page, "body": "这条评论能正常发布"})
    assert c.status_code == 201, c.text
    assert c.json()["status"] == "visible"


# ── 评分单一事实源 ──────────────────────────────────────────────────────────
def test_review_post_and_rating_are_same_fact(client):
    parts = client.get("/api/v1/parts", params={"limit": 8}).json()["items"]
    assert parts, "目录为空，无法验证评分同源"
    part = parts[-1]["id"]

    before = client.get(f"/api/v1/ratings/{part}").json()
    user, _, _ = register(client)
    r = client.post("/api/v1/posts", headers=user, json={
        "kind": "review", "title": "P1 测试：评价帖与评分同源",
        "body": "评价帖写入后，/ratings 聚合必须立刻看到同一票。",
        "part_id": part, "rating": 5, "own_hardware": True})
    assert r.status_code == 201, r.text

    after = client.get(f"/api/v1/ratings/{part}", headers=user).json()
    assert after["count"] == before["count"] + 1
    assert after["mine"]["score"] == 5 and after["mine"]["own_hardware"] is True

    summary = client.get("/api/v1/ratings/summary").json()
    assert summary["parts"][part]["count"] == after["count"], \
        "/ratings 与 /ratings/summary 必须是同一份聚合"

    # 从评分入口改分：同一票，不新增
    assert client.post(f"/api/v1/ratings/{part}", headers=user,
                       json={"score": 3}).status_code == 201
    final = client.get(f"/api/v1/ratings/{part}", headers=user).json()
    assert final["count"] == after["count"] and final["avg"] is not None
    assert final["mine"]["score"] == 3


def test_staff_can_approve_or_hide_pending_comment(client, monkeypatch):
    from app.content_safety import SafetyResult

    a, _, _ = register(client)
    page = f"parts/p1/moderate-{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(
        "app.api.routes.wiki.check_user_text_chunks",
        lambda db, uid, text: SafetyResult(False, checked=True, reason="risky"),
    )
    c = client.post("/api/v1/wiki/comments", headers=a,
                    json={"page": page, "body": "待审内容"}).json()
    assert c["status"] == "pending"

    plain = client.patch(f"/api/v1/wiki/comments/{c['id']}/moderation",
                         headers=a, json={"action": "approve"})
    assert plain.status_code == 403

    staff = staff_headers(client)
    ok = client.patch(f"/api/v1/wiki/comments/{c['id']}/moderation",
                      headers=staff, json={"action": "approve"})
    assert ok.status_code == 200 and ok.json()["status"] == "visible"
    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 1

    hidden = client.patch(f"/api/v1/wiki/comments/{c['id']}/moderation",
                          headers=staff, json={"action": "hide"})
    assert hidden.status_code == 200 and hidden.json()["status"] == "hidden"
    assert client.get("/api/v1/wiki/comments", params={"page": page}
                      ).json()["count"] == 0

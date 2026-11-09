"""账号与社区共建：头像 / 贡献统计 / 帖子编辑删除 / 采纳 / 导出。

钉住的是「补齐之后最容易回退」的几条：
  · 头像只收 /media/... 与 http(s)，`javascript:` 不能进 <img src>；
  · user_out 的评分 / 提案 / 采纳数与真实行数一致；
  · 编辑帖子不能绕过创建时的 kind 校验（评价没分、整机报价没覆盖范围）；
  · 软删除只置 hidden，不物理删帖；
  · 采纳只落在 posts.accepted_comment_id，通知发对人；
  · `solved` 过滤对非 discussion 也不报错；
  · 导出只含本人数据，不含任何凭据。

    cd backend && python -m pytest tests/test_account_community.py -q
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="robowiki-account-community-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0002"
os.environ["ROBOWIKI_BOT_TOKEN"] = "test-bot-token"
os.environ["ROBOWIKI_MEDIA_DIR"] = str(pathlib.Path(_TMP) / "media")
# 内容安全默认关闭外部调用：没有 AppID/Secret 时必须放行，而不是报错
os.environ["ROBOWIKI_WECHAT_MP_APPID"] = ""
os.environ["ROBOWIKI_WECHAT_MP_SECRET"] = ""

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


# ── helpers ─────────────────────────────────────────────────────────────────
def register(client: TestClient, prefix: str = "acct") -> tuple[dict, dict]:
    handle = f"{prefix}{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/auth/register", json={
        "handle": handle, "display_name": handle, "password": "pass1234"})
    assert r.status_code == 201, r.text
    data = r.json()
    from app.core.db import session
    from app.models import User
    from sqlmodel import select
    with session() as db:
        u = db.exec(select(User).where(User.handle == handle)).first()
        if u is not None:
            u.email_verified = True
            db.add(u)
            db.commit()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]


def staff_headers(client: TestClient) -> dict:
    r = client.post("/api/v1/auth/login",
                    json={"handle": "robowiki", "password": "robowiki"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def first_part_id(client: TestClient) -> str:
    r = client.get("/api/v1/parts", params={"limit": 1})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert items, "测试需要目录数据（.data 或同级 RoboWiki 仓）"
    return items[0]["id"]


def create_post(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {
        "kind": "discussion",
        "title": "测试帖子标题",
        "body": "这是一段足够长的测试正文，用于创建帖子。",
        "tags": "测试,四足",
    }
    payload.update(overrides)
    r = client.post("/api/v1/posts", headers=headers, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def add_comment(client: TestClient, headers: dict, post_id: int, body: str) -> dict:
    r = client.post(f"/api/v1/posts/{post_id}/comments", headers=headers,
                    json={"body": body})
    assert r.status_code == 201, r.text
    return r.json()


# ── 1. 头像 ────────────────────────────────────────────────────────────────
def test_avatar_url_update_clear_and_validation(client):
    headers, me = register(client, "avt")

    r = client.patch("/api/v1/auth/me", headers=headers,
                     json={"avatar_url": "/media/abc123.png"})
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"] == "/media/abc123.png"
    assert client.get("/api/v1/auth/me", headers=headers).json()["avatar_url"] \
        == "/media/abc123.png"

    # 公开资料同步头像，但绝不带邮箱
    pub = client.get(f"/api/v1/users/{me['handle']}").json()
    assert pub["avatar_url"] == "/media/abc123.png"
    assert "email" not in pub

    r = client.patch("/api/v1/auth/me", headers=headers,
                     json={"avatar_url": "https://cdn.example.com/a.png?x=1"})
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"].startswith("https://")

    # null 清除自定义头像，回退到底色
    r = client.patch("/api/v1/auth/me", headers=headers, json={"avatar_url": None})
    assert r.status_code == 200, r.text
    assert r.json()["avatar_url"] is None

    for bad in ("javascript:alert(1)", "data:image/png;base64,AAAA",
                "ftp://example.com/a.png", "/media/", "not a url"):
        r = client.patch("/api/v1/auth/me", headers=headers,
                         json={"avatar_url": bad})
        assert r.status_code == 422, (bad, r.text)

    too_long = "https://example.com/" + "a" * 500
    r = client.patch("/api/v1/auth/me", headers=headers,
                     json={"avatar_url": too_long})
    assert r.status_code == 422, r.text
    # 非法值不能产生副作用
    assert client.get("/api/v1/auth/me", headers=headers).json()["avatar_url"] is None


# ── 2. 贡献统计 ────────────────────────────────────────────────────────────
def test_user_out_counts_ratings_submissions_and_accepted(client):
    owner, owner_user = register(client, "stat")
    helper, helper_user = register(client, "hlp")
    part_id = first_part_id(client)

    review = create_post(client, owner, kind="review", part_id=part_id, rating=4,
                         title="零件实测评价", body="用了两个月，回中位很稳，推荐。")
    assert review["rating"] == 4

    sub = client.post("/api/v1/submissions", headers=owner, json={
        "kind": "part_patch", "target_id": part_id,
        "payload": {"price_cny": 199.0},
        "evidence": {"note": "厂商报价单 2026-11"},
    })
    assert sub.status_code == 201, sub.text

    qa = create_post(client, owner, title="这个件配哪款减速器？",
                     body="想用在四足上，预算有限，求推荐搭配。")
    answer = add_comment(client, helper, qa["id"],
                         "配 6:1 行星减速器，低速力矩够用。")
    r = client.post(f"/api/v1/posts/{qa['id']}/accept", headers=owner,
                    json={"comment_id": answer["id"]})
    assert r.status_code == 200, r.text

    out = client.get(f"/api/v1/users/{owner_user['handle']}").json()
    assert out["post_count"] == 2
    assert out["comment_count"] == 0
    assert out["rating_count"] == 1
    assert out["submission_count"] == 1
    # 采纳数归回答者，不归帖主
    assert out["accepted_count"] == 0
    # 原有徽章口径不变
    assert "首次发帖" in out["badges"]
    assert "实测派" in out["badges"]

    helper_out = client.get(f"/api/v1/users/{helper_user['handle']}").json()
    assert helper_out["accepted_count"] == 1
    assert helper_out["reputation"] == 3
    assert "首答被采纳" in helper_out["badges"]


# ── 3. 帖子编辑 / 删除 ─────────────────────────────────────────────────────
def test_edit_post_permissions_and_kind_checks(client):
    owner, _ = register(client, "edit")
    other, _ = register(client, "oth")
    part_id = first_part_id(client)

    post = create_post(client, owner, tags="旧标签")
    r = client.patch(f"/api/v1/posts/{post['id']}", headers=owner, json={
        "title": "修改后的标题", "body": "修改后的正文，长度仍然满足要求。",
        "tags": "四足, 新标签", "use_case": "education",
        "own_hardware": True})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "修改后的标题"
    assert data["tags"] == ["四足", "新标签"]
    assert data["use_case"] == "education"
    assert data["own_hardware"] is True
    assert data["updated_at"] >= data["created_at"]

    # 权限：别人 403，游客 401，站务可以改
    assert client.patch(f"/api/v1/posts/{post['id']}", headers=other,
                        json={"title": "别人来改标题"}).status_code == 403
    assert client.patch(f"/api/v1/posts/{post['id']}",
                        json={"title": "游客来改标题"}).status_code == 401
    staff = staff_headers(client)
    assert client.patch(f"/api/v1/posts/{post['id']}", headers=staff,
                        json={"title": "站务修订标题"}).status_code == 200

    # 空标题 / 显式 null 正文都不能绕过校验
    assert client.patch(f"/api/v1/posts/{post['id']}", headers=owner,
                        json={"title": ""}).status_code == 422
    assert client.patch(f"/api/v1/posts/{post['id']}", headers=owner,
                        json={"body": None}).status_code == 422

    # review：不能把评分清空
    review = create_post(client, owner, kind="review", part_id=part_id, rating=5,
                         title="评价标题可以改", body="正文至少十个字符的评价内容。")
    assert client.patch(f"/api/v1/posts/{review['id']}", headers=owner,
                        json={"rating": None}).status_code == 422
    ok = client.patch(f"/api/v1/posts/{review['id']}", headers=owner,
                      json={"title": "改完仍然是评价", "rating": 3})
    assert ok.status_code == 200, ok.text
    assert ok.json()["rating"] == 3

    # build：有报价就必须有覆盖范围
    build = create_post(client, owner, kind="build", total_price_cny=3000,
                        price_scope="含四个关节电机", title="三千元四足方案",
                        body="这是一套完整的四足整机方案说明。")
    assert client.patch(f"/api/v1/posts/{build['id']}", headers=owner,
                        json={"price_scope": None}).status_code == 422
    assert client.patch(f"/api/v1/posts/{build['id']}", headers=owner,
                        json={"price_scope": "含电机与电池"}).status_code == 200

    # 普通作者不能自封「价格已核实」
    r = client.patch(f"/api/v1/posts/{build['id']}", headers=owner,
                     json={"price_verified": True})
    assert r.status_code == 200 and r.json()["price_verified"] is False


def test_soft_delete_permissions_and_visibility(client):
    from sqlmodel import select

    from app.core.db import session
    from app.models import Post

    owner, _ = register(client, "del")
    other, _ = register(client, "delo")
    post = create_post(client, owner, title="这条帖子会被删除")

    assert client.delete(f"/api/v1/posts/{post['id']}",
                         headers=other).status_code == 403
    assert client.delete(f"/api/v1/posts/{post['id']}").status_code == 401
    assert client.delete(f"/api/v1/posts/{post['id']}",
                         headers=owner).status_code == 204

    assert client.get(f"/api/v1/posts/{post['id']}").status_code == 404
    listed = client.get("/api/v1/posts", params={"q": "这条帖子会被删除"}).json()
    assert post["id"] not in {x["id"] for x in listed["items"]}

    # 软删除：行还在，只是 hidden
    with session() as db:
        row = db.get(Post, post["id"])
        assert row is not None and row.hidden is True

    # 站务可删别人的帖子
    post2 = create_post(client, owner, title="站务会删掉这条")
    assert client.delete(f"/api/v1/posts/{post2['id']}",
                         headers=staff_headers(client)).status_code == 204


# ── 4. 采纳答案 ────────────────────────────────────────────────────────────
def test_accept_unaccept_notification_and_solved_filter(client):
    from sqlmodel import select

    from app.core.db import session
    from app.models import Comment

    owner, _ = register(client, "acc")
    helper, helper_user = register(client, "acch")
    other, _ = register(client, "acco")
    part_id = first_part_id(client)

    post = create_post(client, owner, title="问答帖：舵机抖动怎么排查？",
                       body="上电后舵机持续抖动，换电源也没用，求助。")
    right = add_comment(client, helper, post["id"], "先查共地，再查 PWM 频率。")
    wrong = add_comment(client, other, post["id"], "换一个新的舵机试试。")

    # 只有作者或站务能采纳
    assert client.post(f"/api/v1/posts/{post['id']}/accept", headers=other,
                       json={"comment_id": right["id"]}).status_code == 403
    # 评论必须属于该帖
    other_post = create_post(client, owner, title="另一条帖子标题",
                             body="另一条帖子的正文内容，长度足够。")
    assert client.post(f"/api/v1/posts/{other_post['id']}/accept", headers=owner,
                       json={"comment_id": right["id"]}).status_code == 422
    assert client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                       json={"comment_id": 999999}).status_code == 404

    r = client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                    json={"comment_id": right["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["accepted_comment_id"] == right["id"]

    comments = client.get(f"/api/v1/posts/{post['id']}/comments").json()
    flags = {c["id"]: c["accepted"] for c in comments}
    assert flags[right["id"]] is True
    assert flags[wrong["id"]] is False

    # 通知发给了回答者，而不是楼主
    notes = client.get("/api/v1/notifications", headers=helper).json()["items"]
    accepted_notes = [n for n in notes if n["type"] == "accepted"]
    assert accepted_notes, notes
    assert accepted_notes[-1]["subject"] == "你的回答被采纳了"
    assert accepted_notes[-1]["link"] == f"/post.html?id={post['id']}"
    assert not [n for n in client.get("/api/v1/notifications",
                                      headers=owner).json()["items"]
                if n["type"] == "accepted"]

    # solved 过滤：只按 accepted_comment_id，对 review 也不报错
    author = client.get("/api/v1/auth/me", headers=owner).json()["handle"]
    solved = client.get("/api/v1/posts", params={
        "author": author, "solved": "true"}).json()["items"]
    unsolved = client.get("/api/v1/posts", params={
        "author": author, "solved": "false"}).json()["items"]
    assert post["id"] in {x["id"] for x in solved}
    assert post["id"] not in {x["id"] for x in unsolved}
    assert other_post["id"] in {x["id"] for x in unsolved}

    create_post(client, owner, kind="review", part_id=part_id, rating=4,
                title="已解决筛选下的评价", body="评价正文长度足够，用于筛选测试。")
    r = client.get("/api/v1/posts", params={"author": author, "solved": "false"})
    assert r.status_code == 200, r.text

    # 隐藏评论不能被采纳
    with session() as db:
        row = db.get(Comment, wrong["id"])
        row.hidden = True
        db.add(row)
        db.commit()
    assert client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                       json={"comment_id": wrong["id"]}).status_code == 422

    # 取消采纳
    assert client.delete(f"/api/v1/posts/{post['id']}/accept",
                         headers=other).status_code == 403
    assert client.delete(f"/api/v1/posts/{post['id']}/accept",
                         headers=owner).status_code == 204
    after = client.get(f"/api/v1/posts/{post['id']}").json()
    assert after["accepted_comment_id"] is None
    flags = {c["id"]: c["accepted"] for c in
             client.get(f"/api/v1/posts/{post['id']}/comments").json()}
    assert flags[right["id"]] is False

    # 站务可以替作者采纳
    r = client.post(f"/api/v1/posts/{post['id']}/accept",
                    headers=staff_headers(client),
                    json={"comment_id": right["id"]})
    assert r.status_code == 200, r.text


# ── 5. 账号导出 ────────────────────────────────────────────────────────────
def test_account_export_contains_only_own_data_and_no_credentials(client):
    owner, owner_user = register(client, "exp")
    stranger, _ = register(client, "exps")
    part_id = first_part_id(client)

    own_post = create_post(client, owner, title="我自己的帖子标题",
                           body="导出测试用的正文内容，长度足够。")
    stranger_post = create_post(client, stranger, title="别人的帖子标题",
                                body="别人的正文内容，不应出现在导出里。")
    own_comment = add_comment(client, owner, stranger_post["id"],
                              "我在别人帖子下的评论。")
    add_comment(client, stranger, own_post["id"], "别人在我帖子下的评论。")

    rate = client.post(f"/api/v1/ratings/{part_id}", headers=owner,
                       json={"score": 5, "note": "很稳"})
    assert rate.status_code == 201, rate.text
    sub = client.post("/api/v1/submissions", headers=owner, json={
        "kind": "part_patch", "target_id": part_id,
        "payload": {"price_cny": 288.0},
        "evidence": {"note": "官网价格页"},
    })
    assert sub.status_code == 201, sub.text

    assert client.get("/api/v1/auth/export").status_code == 401

    r = client.get("/api/v1/auth/export", headers=owner)
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data) == {"user", "posts", "comments", "ratings", "submissions"}

    assert data["user"]["id"] == owner_user["id"]
    assert data["user"]["handle"] == owner_user["handle"]
    assert data["user"]["email"] is None

    assert {p["id"] for p in data["posts"]} == {own_post["id"]}
    assert all(p["author"]["id"] == owner_user["id"] for p in data["posts"])
    assert {c["id"] for c in data["comments"]} == {own_comment["id"]}
    assert [x["part_id"] for x in data["ratings"]] == [part_id]
    assert len(data["submissions"]) == 1

    text = r.text
    for secret in ("password_hash", "refresh_token", "access_token",
                   "token_hash", "session_epoch"):
        assert secret not in text, secret
    # 别人的评论正文不能混进来
    assert "别人在我帖子下的评论" not in text

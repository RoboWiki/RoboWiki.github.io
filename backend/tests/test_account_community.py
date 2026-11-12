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


# ── 5. 站务置顶 / 锁定 ────────────────────────────────────────────────────
def test_admin_pin_lock_blocks_replies(client):
    owner, _ = register(client, "pin")
    other, _ = register(client, "pino")
    staff = staff_headers(client)
    post = create_post(client, owner, title="站务置顶锁定测试")
    url = f"/api/v1/admin/posts/{post['id']}"

    assert client.patch(url, headers=owner,
                        json={"pinned": True}).status_code == 403

    r = client.patch(url, headers=staff, json={"pinned": True, "locked": True})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["pinned"] is True and data["locked"] is True

    r = client.post(f"/api/v1/posts/{post['id']}/comments", headers=other,
                    json={"body": "普通用户回复"})
    assert r.status_code == 409, r.text

    r = client.post(f"/api/v1/posts/{post['id']}/comments", headers=staff,
                    json={"body": "站务回复"})
    assert r.status_code == 201, r.text

    r = client.patch(url, headers=staff, json={"locked": False})
    assert r.status_code == 200, r.text
    assert r.json()["locked"] is False
    r = client.post(f"/api/v1/posts/{post['id']}/comments", headers=other,
                    json={"body": "解锁后回复"})
    assert r.status_code == 201, r.text


# ── 6. 评分撤回同步评价帖 / 撤回已采纳评论回收声望 ────────────────────────
def test_withdraw_rating_demotes_review_post(client):
    owner, _ = register(client, "rwd")
    part = first_part_id(client)
    post = create_post(client, owner, kind="review", part_id=part, rating=5,
                       title="评分撤回测试", body="这条评价会在撤回评分后保留为讨论。")

    r = client.post(f"/api/v1/ratings/{part}", headers=owner, json={"score": 3})
    assert r.status_code == 201, r.text
    current = client.get(f"/api/v1/posts/{post['id']}").json()
    assert current["rating"] == 3, "评分入口改分要同步评价帖星级"

    assert client.delete(f"/api/v1/ratings/{part}", headers=owner).status_code == 204
    after = client.get(f"/api/v1/posts/{post['id']}").json()
    assert after["kind"] == "discussion" and after["rating"] is None


def test_withdraw_accepted_comment_rolls_back_reputation(client):
    owner, _ = register(client, "acc")
    answerer, answerer_user = register(client, "ans")
    post = create_post(client, owner, title="采纳撤回声望测试")
    comment = add_comment(client, answerer, post["id"], "这条回答会被采纳，然后撤回。")

    r = client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                    json={"comment_id": comment["id"]})
    assert r.status_code == 200, r.text
    rep_after = client.get("/api/v1/auth/me", headers=answerer).json()["reputation"]
    assert rep_after == int(answerer_user["reputation"]) + 3

    assert client.delete(f"/api/v1/comments/{comment['id']}",
                         headers=answerer).status_code == 204
    rep_back = client.get("/api/v1/auth/me", headers=answerer).json()["reputation"]
    assert rep_back == int(answerer_user["reputation"])


# ── 6. 评论编辑与软撤回 ────────────────────────────────────────────────────
def _reply(client: TestClient, headers: dict, post_id: int, parent_id: int,
           body: str) -> dict:
    r = client.post(f"/api/v1/posts/{post_id}/comments", headers=headers,
                    json={"body": body, "parent_id": parent_id})
    assert r.status_code == 201, r.text
    return r.json()


def test_comment_edit_permissions_and_validation(client):
    author, author_user = register(client, "ced")
    other, _ = register(client, "cedo")
    staff = staff_headers(client)
    post = create_post(client, author, title="评论编辑权限测试")
    c = add_comment(client, author, post["id"], "原始评论正文")
    url = f"/api/v1/comments/{c['id']}"

    # 他人不能改，站务可以代改
    assert client.patch(url, headers=other,
                        json={"body": "别人的越权修改"}).status_code == 403
    r = client.patch(url, headers=staff, json={"body": "站务代改的评论正文"})
    assert r.status_code == 200, r.text
    assert r.json()["body"] == "站务代改的评论正文"
    assert r.json()["withdrawn"] is False
    assert r.json()["edited_at"] is not None
    # 回复关系不变
    assert r.json()["post_id"] == post["id"]
    assert r.json()["author"]["handle"] == author_user["handle"]

    # 作者自己改 + edited_at 刷新
    r = client.patch(url, headers=author, json={"body": "作者修改后的评论正文"})
    assert r.status_code == 200, r.text
    assert r.json()["body"] == "作者修改后的评论正文"
    assert r.json()["edited_at"] is not None

    # 2–4000 字
    assert client.patch(url, headers=author,
                        json={"body": "短"}).status_code == 422
    assert client.patch(url, headers=author,
                        json={"body": "x" * 4001}).status_code == 422

    # 不存在的评论 404
    assert client.patch("/api/v1/comments/999999", headers=author,
                        json={"body": "不存在的评论"}).status_code == 404


def test_comment_soft_withdraw_keeps_replies(client):
    from sqlmodel import select

    from app.core.db import session
    from app.crud import touch_comment_count
    from app.models import Comment

    author, author_user = register(client, "cwd")
    other, _ = register(client, "cwdo")
    post = create_post(client, author, title="评论撤回保留回复树")
    root = add_comment(client, author, post["id"], "即将被撤回的评论")
    reply = _reply(client, other, post["id"], root["id"], "回复不会消失")

    # 他人不能撤回
    assert client.delete(f"/api/v1/comments/{root['id']}",
                         headers=other).status_code == 403
    r = client.delete(f"/api/v1/comments/{root['id']}", headers=author)
    assert r.status_code == 204, r.text

    nodes = {n["id"]: n for n in
             client.get(f"/api/v1/posts/{post['id']}/comments").json()}
    assert root["id"] in nodes, "撤回的评论保留可见占位"
    assert nodes[root["id"]]["withdrawn"] is True
    assert nodes[root["id"]]["body"] == ""
    assert nodes[root["id"]]["author"]["handle"] == author_user["handle"]
    assert nodes[root["id"]]["edited_at"] is not None
    assert [x["id"] for x in nodes[root["id"]]["replies"]] == [reply["id"]]
    child = nodes[root["id"]]["replies"][0]
    assert child["parent_id"] == root["id"]
    assert child["body"] == "回复不会消失"

    # 撤回后不能再编辑、也不能再被回复
    assert client.patch(f"/api/v1/comments/{root['id']}", headers=author,
                        json={"body": "撤回后再编辑"}).status_code == 409
    r = client.post(f"/api/v1/posts/{post['id']}/comments", headers=other,
                    json={"body": "回复已撤回的评论", "parent_id": root["id"]})
    assert r.status_code == 422, r.text

    # 撤回仍算一条可见占位；hidden 才不计入
    assert client.get(f"/api/v1/posts/{post['id']}").json()["comment_count"] == 2
    with session() as db:
        row = db.get(Comment, root["id"])
        row.hidden = True
        db.add(row)
        db.commit()
        touch_comment_count(db, post["id"])
    nodes = client.get(f"/api/v1/posts/{post['id']}/comments").json()
    assert root["id"] not in {n["id"] for n in nodes}
    assert client.get(f"/api/v1/posts/{post['id']}").json()["comment_count"] == 1


def test_withdraw_accepted_comment_clears_acceptance(client):
    owner, _ = register(client, "cwa")
    helper, _ = register(client, "cwah")
    post = create_post(client, owner, title="撤回已采纳评论测试")
    answer = add_comment(client, helper, post["id"], "这条回答会被采纳")

    r = client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                    json={"comment_id": answer["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["accepted_comment_id"] == answer["id"]

    r = client.delete(f"/api/v1/comments/{answer['id']}", headers=helper)
    assert r.status_code == 204, r.text

    after = client.get(f"/api/v1/posts/{post['id']}").json()
    assert after["accepted_comment_id"] is None
    nodes = {n["id"]: n for n in
             client.get(f"/api/v1/posts/{post['id']}/comments").json()}
    assert nodes[answer["id"]]["withdrawn"] is True
    assert nodes[answer["id"]]["accepted"] is False
    # 撤回的评论不能再被采纳
    r = client.post(f"/api/v1/posts/{post['id']}/accept", headers=owner,
                    json={"comment_id": answer["id"]})
    assert r.status_code == 422, r.text
    # 重复撤回仍是 204
    assert client.delete(f"/api/v1/comments/{answer['id']}",
                         headers=helper).status_code == 204


# ── 7. 引用回复 ────────────────────────────────────────────────────────────
def _quote(client: TestClient, headers: dict, post_id: int, body: str,
           quote_id: int, parent_id: int | None = None):
    payload = {"body": body, "quote_id": quote_id}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    return client.post(f"/api/v1/posts/{post_id}/comments", headers=headers,
                       json=payload)


def _flatten(nodes: list[dict]) -> dict[int, dict]:
    """评论是两级树：把 replies 展开成 id → 评论。"""
    flat: dict[int, dict] = {}
    for node in nodes:
        flat[node["id"]] = node
        flat.update(_flatten(node.get("replies") or []))
    return flat


def test_quote_comment_snapshots_author_and_excerpt(client):
    author, author_user = register(client, "quo")
    quoter, _ = register(client, "quq")
    post = create_post(client, author, title="引用回复快照测试")

    long_body = "这是一段会被引用的评论正文，用来验证 160 字截断是否生效。" * 12
    assert len(long_body) > 160
    root = add_comment(client, author, post["id"], long_body)

    # 引用与回复可以同时存在：parent_id 语义不变
    r = _quote(client, quoter, post["id"], "我引用一下这条评论。", root["id"],
               parent_id=root["id"])
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["quote_id"] == root["id"]
    assert data["quote_author"] == author_user["handle"]
    assert data["quote_excerpt"] == long_body[:160]
    assert data["parent_id"] == root["id"], "引用不改变 parent_id 语义"

    # 列表 / 详情同样返回三个 quote 字段
    nodes = _flatten(client.get(f"/api/v1/posts/{post['id']}/comments").json())
    assert nodes[data["id"]]["quote_id"] == root["id"]
    assert nodes[data["id"]]["quote_author"] == author_user["handle"]
    assert nodes[data["id"]]["quote_excerpt"] == long_body[:160]
    # 没有引用的评论这三项是空值，不是 None
    assert nodes[root["id"]]["quote_id"] is None
    assert nodes[root["id"]]["quote_author"] == ""
    assert nodes[root["id"]]["quote_excerpt"] == ""


def test_quote_rejects_cross_post_and_withdrawn(client):
    author, _ = register(client, "qrx")
    quoter, _ = register(client, "qrxq")
    post = create_post(client, author, title="引用校验用的帖子一")
    other_post = create_post(client, author, title="引用校验用的帖子二")
    foreign = add_comment(client, author, other_post["id"], "另一条帖子下的评论")

    r = _quote(client, quoter, post["id"], "跨帖引用应当被拒绝。", foreign["id"])
    assert r.status_code == 422, r.text
    assert "不属于这个帖子" in r.json()["detail"]

    # 不存在的评论同样是 422（不是 404：这是引用字段的校验，不是资源寻址）
    r = _quote(client, quoter, post["id"], "引用不存在的评论。", 999999)
    assert r.status_code == 422, r.text

    doomed = add_comment(client, author, post["id"], "这条评论随后会被撤回")
    assert client.delete(f"/api/v1/comments/{doomed['id']}",
                         headers=author).status_code == 204
    r = _quote(client, quoter, post["id"], "引用已撤回的评论。", doomed["id"])
    assert r.status_code == 422, r.text
    assert "已撤回" in r.json()["detail"]


def test_withdraw_quoted_comment_clears_excerpt_only(client):
    author, author_user = register(client, "qwd")
    quoter, _ = register(client, "qwdq")
    post = create_post(client, author, title="撤回被引用评论后清空快照")
    source = add_comment(client, author, post["id"], "这段原文不该通过引用继续可读")
    quoting = _quote(client, quoter, post["id"], "引用块里会存一份快照。",
                     source["id"]).json()
    assert quoting["quote_excerpt"] == "这段原文不该通过引用继续可读"

    assert client.delete(f"/api/v1/comments/{source['id']}",
                         headers=author).status_code == 204
    # 重复撤回仍 204，且不会把引用快照写回来
    assert client.delete(f"/api/v1/comments/{source['id']}",
                         headers=author).status_code == 204

    nodes = _flatten(client.get(f"/api/v1/posts/{post['id']}/comments").json())
    quoted = nodes[source["id"]]
    assert quoted["withdrawn"] is True and quoted["body"] == "", "占位仍在"
    q = nodes[quoting["id"]]
    assert q["quote_id"] == source["id"], "quote_id 保留"
    assert q["quote_author"] == author_user["handle"], "quote_author 保留"
    assert q["quote_excerpt"] == "", "撤回后不能继续泄露原文"
    assert q["body"] == "引用块里会存一份快照。"


def test_admin_hide_comment_clears_quote_excerpt(client):
    """站务隐藏被引用评论时，与撤回同口径清空引用快照。

    hide 的入口不在 admin.py，而在 /admin/reports 的处置分支（reports.py）。
    """
    author, author_user = register(client, "qhd")
    quoter, _ = register(client, "qhdq")
    reporter, _ = register(client, "qhdr")
    post = create_post(client, author, title="站务隐藏被引用评论")
    source = add_comment(client, author, post["id"], "站务隐藏后不该再被引用到")
    quoting = _quote(client, quoter, post["id"], "引用块快照会保持到处置为止。",
                     source["id"]).json()
    assert quoting["quote_excerpt"] == "站务隐藏后不该再被引用到"

    rid = client.post("/api/v1/reports", headers=reporter, json={
        "target_kind": "comment", "target_id": source["id"],
        "reason": "abuse", "detail": "测试：隐藏后清空引用快照"}).json()["id"]
    r = client.patch(f"/api/v1/admin/reports/{rid}", headers=staff_headers(client),
                     json={"action": "hide", "note": "确认违规，隐藏该评论"})
    assert r.status_code == 200, r.text

    nodes = _flatten(client.get(f"/api/v1/posts/{post['id']}/comments").json())
    assert source["id"] not in nodes, "隐藏的评论不再出现在列表里"
    q = nodes[quoting["id"]]
    assert q["quote_id"] == source["id"] and q["quote_author"] == author_user["handle"]
    assert q["quote_excerpt"] == "", "隐藏后引用块同样不能泄露原文"


# ── 8. 标签聚合 ────────────────────────────────────────────────────────────def test_tags_aggregation_dedupes_hidden_and_filters_kind(client):
    owner, _ = register(client, "tag")
    part = first_part_id(client)
    tag_a = f"引用测{uuid.uuid4().hex[:6]}"
    tag_b = f"标签{uuid.uuid4().hex[:6]}"

    # 同帖重复标签只计一次；B 只出现一次
    create_post(client, owner, tags=f"{tag_a}, {tag_a}, {tag_b}",
                title="标签聚合测试一", body="标签聚合测试用的正文内容，长度足够。")
    # 大小写不同按同一标签合并，展示名保留首次出现的写法
    create_post(client, owner, tags=tag_a.lower(),
                title="标签聚合测试二", body="标签聚合测试用的正文内容，长度足够。")
    # hidden 帖子不计
    deleted = create_post(client, owner, tags=tag_a,
                          title="标签聚合测试三（会被删除）",
                          body="标签聚合测试用的正文内容，长度足够。")
    assert client.delete(f"/api/v1/posts/{deleted['id']}",
                         headers=owner).status_code == 204
    # kind 过滤：评价帖的标签不混进 discussion
    create_post(client, owner, kind="review", part_id=part, rating=4, tags=tag_a,
                title="标签聚合测试四（评价）", body="标签聚合测试用的评价正文内容。")

    def items(**params):
        r = client.get("/api/v1/tags", params={"limit": 100, **params})
        assert r.status_code == 200, r.text
        return r.json()

    all_tags = items()
    by_key = {i["name"].casefold(): i for i in all_tags["items"]}
    assert by_key[tag_a.casefold()]["name"] == tag_a, "展示名保留首次写法"
    assert by_key[tag_a.casefold()]["count"] == 3, "两帖 + 一条评价；删除的不计"
    assert by_key[tag_b.casefold()]["count"] == 1, "同帖重复只算一次"
    assert all_tags["total"] == len(all_tags["items"]), "limit 足够大时 total 与 items 等长"
    counts = [i["count"] for i in all_tags["items"]]
    assert counts == sorted(counts, reverse=True), "按 count 降序"

    discussion = items(kind="discussion")
    by_key = {i["name"].casefold(): i for i in discussion["items"]}
    assert by_key[tag_a.casefold()]["count"] == 2, "kind=discussion 排除评价帖"
    assert not [i for i in discussion["items"]
                if i["name"] is None or not str(i["name"]).strip()]

    # limit 只截断 items，total 仍是去重标签总数
    limited = items(limit=1)
    assert len(limited["items"]) == 1
    assert limited["total"] == all_tags["total"]
    # 参数边界
    assert client.get("/api/v1/tags", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/tags", params={"limit": 101}).status_code == 422


# ── 9. 评分摘要返回评价条数 ────────────────────────────────────────────────
def test_rating_summary_reports_visible_review_count(client):
    first, _ = register(client, "rvc")
    second, _ = register(client, "rvc2")
    # 取一个本模块其它用例没用过的零件，基线才好断言
    part = client.get("/api/v1/parts", params={"limit": 200}).json()["items"][-1]["id"]

    def rating():
        r = client.get(f"/api/v1/ratings/{part}")
        assert r.status_code == 200, r.text
        return r.json()

    base = rating()
    assert base["review_count"] == 0, "新零件不该有评价帖"
    # 原有字段与口径不变
    assert base["count"] == 0 and base["avg"] is None
    assert set(base) >= {"count", "avg", "histogram", "mine", "review_count"}

    review1 = create_post(client, first, kind="review", part_id=part, rating=5,
                          title="评价条数测试一", body="用于验证 review_count 的评价正文。")
    create_post(client, second, kind="review", part_id=part, rating=3,
                title="评价条数测试二", body="用于验证 review_count 的评价正文。")
    d = rating()
    assert d["review_count"] == 2
    assert d["count"] == 2, "review_count 不改变评分数口径"

    # hidden 的评价帖不计入 review_count
    assert client.delete(f"/api/v1/posts/{review1['id']}",
                         headers=first).status_code == 204
    d = rating()
    assert d["review_count"] == 1
    assert d["count"] == 1, "隐藏评价同时退出公开聚合（原口径不变）"

    summary = client.get("/api/v1/ratings/summary").json()
    assert summary["parts"][part]["review_count"] == 1
    assert summary["parts"][part]["count"] == 1


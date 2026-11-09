"""后台用户管理回归：列表 / 角色 / 封禁即下线 / 解封恢复。

护栏：不能动自己、不能降级最后一名站务、封禁后登录与既有会话全部失效。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="robowiki-admin-users-")
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
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)


def login(c: TestClient, handle: str, password: str = "robowiki"):
    r = c.post("/api/auth/login", json={"handle": handle, "password": password})
    return r


def staff_headers(c: TestClient) -> dict:
    r = login(c, "robowiki")
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def user_id(c: TestClient, handle: str) -> int:
    items = c.get("/api/admin/users", params={"q": handle},
                  headers=staff_headers(c)).json()["items"]
    hit = next(i for i in items if i["handle"] == handle)
    return hit["id"]


def test_users_list_requires_staff(client):
    assert client.get("/api/admin/users").status_code == 401
    plain = login(client, "demo1")
    assert plain.status_code == 200
    h = {"Authorization": f"Bearer {plain.json()['access_token']}"}
    assert client.get("/api/admin/users", headers=h).status_code == 403


def test_users_list_has_counts_and_status(client):
    d = client.get("/api/admin/users", params={"limit": 5},
                   headers=staff_headers(client)).json()
    assert d["total"] >= 2
    robowiki = next(i for i in d["items"] if i["handle"] == "robowiki")
    assert robowiki["is_staff"] is True
    assert {"posts", "comments", "banned", "ban_reason"} <= set(robowiki)
    assert robowiki["posts"] >= 1


def test_cannot_change_self(client):
    h = staff_headers(client)
    me = client.get("/api/auth/me", headers=h).json()
    r = client.patch(f"/api/admin/users/{me['id']}", headers=h, json={"is_staff": False})
    assert r.status_code == 409
    r = client.patch(f"/api/admin/users/{me['id']}", headers=h, json={"banned": True})
    assert r.status_code == 409


def test_ban_then_login_blocked_and_unban_restores(client):
    h = staff_headers(client)
    uid = user_id(client, "demo1")

    # 封禁前能登录，先留一个旧 token 用于验证「封禁即下线」
    old = login(client, "demo1")
    assert old.status_code == 200
    old_token = old.json()["access_token"]

    r = client.patch(f"/api/admin/users/{uid}", headers=h,
                     json={"banned": True, "reason": "测试：违规内容"})
    assert r.status_code == 200, r.text
    assert r.json()["banned"] is True

    # 新登录被拒（403），旧 access 因会话代次 +1 立即失效（401）
    assert login(client, "demo1").status_code == 403
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me.status_code == 401

    # 列表里能看到封禁状态与原因
    row = next(i for i in client.get("/api/admin/users", params={"q": "demo1"},
                                     headers=h).json()["items"] if i["id"] == uid)
    assert row["banned"] is True and row["ban_reason"] == "测试：违规内容"

    # 重复封禁幂等
    r2 = client.patch(f"/api/admin/users/{uid}", headers=h, json={"banned": True})
    assert r2.status_code == 200

    # 解封后可以重新登录
    assert client.patch(f"/api/admin/users/{uid}", headers=h,
                        json={"banned": False}).status_code == 200
    assert login(client, "demo1").status_code == 200


def test_promote_and_demote_staff(client):
    h = staff_headers(client)
    uid = user_id(client, "demo1")

    assert client.patch(f"/api/admin/users/{uid}", headers=h,
                        json={"is_staff": True}).json()["is_staff"] is True
    # 被提升者立刻能进后台
    dh = {"Authorization": f"Bearer {login(client, 'demo1').json()['access_token']}"}
    assert client.get("/api/admin/users", headers=dh).status_code == 200

    assert client.patch(f"/api/admin/users/{uid}", headers=h,
                        json={"is_staff": False}).json()["is_staff"] is False
    assert client.get("/api/admin/users", headers=dh).status_code == 403

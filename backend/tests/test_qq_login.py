"""QQ 网页登录协议回归。

不连 QQ：token / openid / 用户资料三层都 monkeypatch，只验证本站这一侧的
state 校验、身份落库、绑定冲突和会话签发。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import uuid
from urllib.parse import parse_qs, urlparse

_TMP = tempfile.mkdtemp(prefix="robowiki-qq-test-")
os.environ.setdefault("ROBOWIKI_DB_PATH", str(pathlib.Path(_TMP) / "test.db"))
os.environ.setdefault("ROBOWIKI_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import select  # noqa: E402

from app.api.routes import auth as auth_route  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Identity, User  # noqa: E402

BASE = "https://testserver"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url=BASE) as c:
        yield c


@pytest.fixture()
def qq_ready(monkeypatch):
    monkeypatch.setattr(settings, "qq_app_id", "test-qq-app-id")
    monkeypatch.setattr(settings, "qq_app_key", "test-qq-app-key")
    monkeypatch.setattr(settings, "oauth_redirect_base", "https://robowiki.org.cn")
    subject = {"openid": f"qq-openid-{uuid.uuid4().hex[:10]}", "nickname": "QQ 用户"}

    async def fake_token(code: str, redirect_uri: str) -> dict:
        assert code == "good-code"
        assert redirect_uri == "https://robowiki.org.cn/api/v1/auth/qq/callback"
        return {"access_token": "qq-access-token", "expires_in": 7776000}

    async def fake_openid(access_token: str) -> dict:
        assert access_token == "qq-access-token"
        return {"client_id": "test-qq-app-id", "openid": subject["openid"]}

    async def fake_profile(access_token: str, openid: str) -> dict:
        assert openid == subject["openid"]
        return {"ret": 0, "nickname": subject["nickname"],
                "figureurl_qq_2": "http://thirdqq.qlogo.cn/qq-avatar.png"}

    monkeypatch.setattr(auth_route, "_qq_token", fake_token)
    monkeypatch.setattr(auth_route, "_qq_openid", fake_openid)
    monkeypatch.setattr(auth_route, "_qq_profile", fake_profile)
    return subject


def _state_from(location: str) -> str:
    query = parse_qs(urlparse(location).query)
    assert query["client_id"] == ["test-qq-app-id"]
    return query["state"][0]


def _identity(openid: str) -> Identity | None:
    from app.core.db import session
    db = session()
    try:
        return db.exec(select(Identity).where(
            Identity.provider == "qq", Identity.subject == openid)).first()
    finally:
        db.close()


def test_qq_authorize_url_and_login(client, qq_ready):
    r = client.get("/api/v1/auth/qq/login", follow_redirects=False)
    assert r.status_code == 302, r.text
    location = r.headers["location"]
    assert location.startswith("https://graph.qq.com/oauth2.0/authorize?")
    state = _state_from(location)

    r = client.get("/api/v1/auth/qq/callback",
                   params={"code": "good-code", "state": state},
                   headers={"Accept": "application/json"},
                   follow_redirects=False)
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token

    me = client.get("/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["display_name"] == "QQ 用户"
    assert body["trust_sources"] == ["qq"]

    ident = _identity(qq_ready["openid"])
    assert ident is not None
    assert ident.raw["avatar"] == "https://thirdqq.qlogo.cn/qq-avatar.png"


def test_qq_state_is_single_use(client, qq_ready):
    r = client.get("/api/v1/auth/qq/login", follow_redirects=False)
    state = _state_from(r.headers["location"])
    ok = client.get("/api/v1/auth/qq/callback",
                    params={"code": "good-code", "state": state},
                    headers={"Accept": "application/json"},
                    follow_redirects=False)
    assert ok.status_code == 200, ok.text
    replay = client.get("/api/v1/auth/qq/callback",
                        params={"code": "good-code", "state": state},
                        headers={"Accept": "application/json"},
                        follow_redirects=False)
    assert replay.status_code == 400, replay.text


def test_qq_login_twice_reuses_account(client, qq_ready):
    handles = set()
    for _ in range(2):
        r = client.get("/api/v1/auth/qq/login", follow_redirects=False)
        state = _state_from(r.headers["location"])
        cb = client.get("/api/v1/auth/qq/callback",
                        params={"code": "good-code", "state": state},
                        headers={"Accept": "application/json"},
                        follow_redirects=False)
        token = cb.json()["access_token"]
        me = client.get("/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()
        handles.add(me["handle"])
    assert len(handles) == 1


def test_qq_bind_and_conflict(client, qq_ready):
    def register(handle: str) -> str:
        r = client.post("/api/auth/register", json={
            "handle": handle, "display_name": handle, "password": "pass1234"})
        assert r.status_code == 201, r.text
        return r.json()["access_token"]

    first = register("qq-bind-one")
    r = client.post("/api/v1/auth/qq/bind",
                    params={"return_to": "https://robowiki.org.cn"},
                    headers={"Authorization": f"Bearer {first}"})
    assert r.status_code == 200, r.text
    state = _state_from(r.json()["url"])
    cb = client.get("/api/v1/auth/qq/callback",
                    params={"code": "good-code", "state": state},
                    follow_redirects=False)
    assert cb.status_code == 302
    assert cb.headers["location"] == "https://robowiki.org.cn/account.html?qq=bound"

    second = register("qq-bind-two")
    r = client.post("/api/v1/auth/qq/bind",
                    params={"return_to": "https://robowiki.org.cn"},
                    headers={"Authorization": f"Bearer {second}"})
    state = _state_from(r.json()["url"])
    cb = client.get("/api/v1/auth/qq/callback",
                    params={"code": "good-code", "state": state},
                    follow_redirects=False)
    assert cb.status_code == 302
    assert cb.headers["location"] == "https://robowiki.org.cn/account.html?qq=conflict"

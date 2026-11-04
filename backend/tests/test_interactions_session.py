"""跨域（CORS）+ 会话（refresh 轮换 / 登出）+ GitHub 回跳 handoff。

覆盖三件事：

1. **静态镜像跨域**：`https://robowiki.github.io` 能预检、带 Bearer 调接口，
   401 / 429 响应也必须带 CORS 头；未知 origin 一律不放行。
2. **会话**：access 2 小时带 `se`，refresh 30 天轮换；旧 refresh 复用即
   撤销整条 family；`/auth/sessions`、`/auth/logout`、`/auth/logout-all`
   行为符合预期（logout-all 通过自增 `session_epoch` 废掉旧 access）。
3. **GitHub 回跳**：`return_to` 只认白名单 origin；回调 Location 里是
   一次性 code 而不是 JWT；code 60 秒、只能换一次。

**不发真实网络请求**：GitHub 的换 token / 抓资料全部 monkeypatch。
测试库与其他模块共享（conftest 的 setdefault 约定），不碰真实 robowiki.db。

    cd backend && py -3.12 -m pytest tests/test_interactions_session.py -q
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

# 必须在 import app 之前设置（settings 在 import 时实例化）。
_TMP = tempfile.mkdtemp(prefix="robowiki-session-test-")
os.environ.setdefault("ROBOWIKI_DB_PATH", str(pathlib.Path(_TMP) / "test.db"))
os.environ.setdefault("ROBOWIKI_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")
os.environ.setdefault("ROBOWIKI_BOT_TOKEN", "test-bot-token")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import select  # noqa: E402

from app.api.routes import auth as auth_route  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.db import session as db_session  # noqa: E402
from app.core.security import (hash_secret, password_fingerprint)  # noqa: E402
from app.main import app  # noqa: E402
from app.models import HandoffCode, RefreshToken, User  # noqa: E402

# OAuth state cookie 是 Secure 的，https 基址才会被 httpx 回传。
BASE = "https://testserver"
MIRROR = "https://robowiki.github.io"
API = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url=BASE) as c:
        yield c
    from app.core.db import engine, reset_engine
    try:
        engine().dispose()
    except Exception:
        pass
    reset_engine()
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture
def github_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "test-client-secret")


# ── helpers ─────────────────────────────────────────────────────────────────
def _register(client: TestClient, handle: str, password: str = "pass1234") -> dict:
    r = client.post(f"{API}/auth/register", json={
        "handle": handle, "display_name": handle, "password": password})
    assert r.status_code == 201, r.text
    return r.json()


def _login(client: TestClient, handle: str, password: str = "pass1234") -> dict:
    r = client.post(f"{API}/auth/login",
                    json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _refresh(client: TestClient, raw: str):
    return client.post(f"{API}/auth/refresh", json={"refresh_token": raw})


def _sessions(client: TestClient, access: str) -> list[dict]:
    r = client.get(f"{API}/auth/sessions", headers=_auth(access))
    assert r.status_code == 200, r.text
    return r.json()


def _user(handle: str) -> User:
    db = db_session()
    try:
        user = db.exec(select(User).where(User.handle == handle)).first()
        assert user is not None
        return user
    finally:
        db.close()


def _fake_github(monkeypatch, *, subject: str, login: str) -> None:
    """替掉 Authlib 的两处副作用，不碰真实 GitHub。"""

    async def exchange(request, client):
        return {"access_token": "fake-token", "token_type": "bearer"}

    async def profile(client, token):
        return {"subject": subject, "login": login, "name": login.title(),
                "email": None, "email_verified": False,
                "raw": {"id": subject, "login": login}}

    monkeypatch.setattr(auth_route, "_github_exchange", exchange)
    monkeypatch.setattr(auth_route, "_github_profile", profile)


def _start_github(client: TestClient, return_to: str | None):
    params = {"return_to": return_to} if return_to else None
    return client.get(f"{API}/auth/github/login", params=params,
                      follow_redirects=False)


def _github_callback(client: TestClient):
    return client.get(f"{API}/auth/github/callback",
                      params={"code": "fake", "state": "fake"},
                      follow_redirects=False)


# ── 1. CORS：镜像可跨域、未知 origin 拒绝、错误响应也带 CORS ───────────────
def test_default_cors_covers_main_domain_mirror_and_localhost():
    origins = set(settings.cors_origins)
    assert "https://robowiki.org.cn" in origins
    assert "https://robowiki.github.io" in origins
    assert any("localhost" in o for o in origins)


def test_cors_preflight_allows_github_pages_with_authorization(client):
    r = client.options(f"{API}/auth/login", headers={
        "Origin": MIRROR,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type,x-client",
    })
    assert r.status_code == 200, r.text
    assert r.headers.get("access-control-allow-origin") == MIRROR
    assert r.headers.get("access-control-allow-credentials") == "true"
    allowed = (r.headers.get("access-control-allow-headers") or "").lower()
    assert "authorization" in allowed, allowed
    assert "x-client" in allowed, allowed


def test_cors_rejects_unknown_origin(client):
    r = client.options(f"{API}/auth/login", headers={
        "Origin": "https://evil.example.com",
        "Access-Control-Request-Method": "POST",
    })
    assert r.status_code == 400, r.text
    assert "access-control-allow-origin" not in r.headers

    # 简单请求同样不能拿到放行头
    plain = client.get(f"{API}/meta", headers={"Origin": "https://evil.example.com"})
    assert plain.status_code == 200
    assert "access-control-allow-origin" not in plain.headers


def test_cors_headers_present_on_401_and_429(client):
    bad = client.post(f"{API}/auth/login",
                      json={"handle": "no-such-user", "password": "nope"},
                      headers={"Origin": MIRROR})
    assert bad.status_code == 401
    assert bad.headers.get("access-control-allow-origin") == MIRROR

    last = None
    for _ in range(35):  # 登录桶上限 30 次
        last = client.post(f"{API}/auth/login",
                           json={"handle": "no-such-user", "password": "nope"},
                           headers={"Origin": MIRROR})
        if last.status_code == 429:
            break
    assert last is not None and last.status_code == 429, last.status_code if last else ""
    assert last.headers.get("access-control-allow-origin") == MIRROR
    assert last.headers.get("retry-after")


# ── 2. 会话：access 2h / refresh 轮换 / 复用撤销 family ─────────────────────
def test_tokens_include_refresh_and_two_hour_access(client):
    data = _register(client, "sessshape1")
    assert data["access_token"] and data["refresh_token"]
    assert data["user"]["handle"] == "sessshape1"

    payload = jwt.decode(data["access_token"], settings.secret_key,
                         algorithms=["HS256"])
    assert payload["se"] == 0
    ttl = payload["exp"] - payload["iat"]
    assert 7000 <= ttl <= 7300, f"access 应约 2 小时，实际 {ttl}s"

    sessions = _sessions(client, data["access_token"])
    assert len(sessions) == 1
    assert sessions[0]["client"] == "web"
    assert sessions[0]["expires_at"]


def test_refresh_rotates_and_returns_working_pair(client):
    data = _register(client, "sessrot1")
    r = _refresh(client, data["refresh_token"])
    assert r.status_code == 200, r.text
    new = r.json()

    assert new["refresh_token"] and new["refresh_token"] != data["refresh_token"]
    assert new["access_token"]
    assert client.get(f"{API}/auth/me",
                      headers=_auth(new["access_token"])).status_code == 200
    # 轮换不新增会话：链的末端仍是一条
    assert len(_sessions(client, new["access_token"])) == 1


def test_reusing_old_refresh_revokes_whole_family(client):
    data = _register(client, "sessreuse1")
    first = _refresh(client, data["refresh_token"]).json()

    reused = _refresh(client, data["refresh_token"])
    assert reused.status_code == 401, reused.text

    # family 已被整条撤销：刚才拿到的新 refresh 也立刻失效
    assert _refresh(client, first["refresh_token"]).status_code == 401
    assert _sessions(client, first["access_token"]) == []


def test_unknown_and_expired_refresh_are_401(client):
    assert _refresh(client, "x" * 64).status_code == 401

    data = _register(client, "sessexpire1")
    user = _user("sessexpire1")
    raw = "expired-refresh-token-" + "y" * 32
    db = db_session()
    try:
        db.add(RefreshToken(user_id=user.id, token_hash=hash_secret(raw),
                            family="expired-family", client="web",
                            expires_at=datetime.now(timezone.utc)
                            - timedelta(seconds=1)))
        db.commit()
    finally:
        db.close()
    assert _refresh(client, raw).status_code == 401
    assert len(_sessions(client, data["access_token"])) == 1


def test_logout_revokes_one_session_chain(client):
    data = _register(client, "sesslogout1")
    r = client.post(f"{API}/auth/logout",
                    json={"refresh_token": data["refresh_token"]},
                    headers=_auth(data["access_token"]))
    assert r.status_code == 200, r.text
    assert r.json()["revoked"] == 1

    assert _refresh(client, data["refresh_token"]).status_code == 401
    assert _sessions(client, data["access_token"]) == []


def test_logout_all_bumps_epoch_and_kills_old_access(client):
    _register(client, "sessall1")
    first = _login(client, "sessall1")
    second = _login(client, "sessall1")
    # register 也建了一条会话，共 3 条
    assert len(_sessions(client, first["access_token"])) == 3

    r = client.post(f"{API}/auth/logout-all",
                    headers=_auth(first["access_token"]))
    assert r.status_code == 200, r.text
    assert r.json()["revoked"] == 3
    assert r.json()["session_epoch"] == 1

    # 两枚旧 access 的 se=0，epoch 已变 1 → 401
    assert client.get(f"{API}/auth/me",
                      headers=_auth(first["access_token"])).status_code == 401
    assert client.get(f"{API}/auth/me",
                      headers=_auth(second["access_token"])).status_code == 401
    assert _refresh(client, first["refresh_token"]).status_code == 401
    assert _refresh(client, second["refresh_token"]).status_code == 401

    fresh = _login(client, "sessall1")
    payload = jwt.decode(fresh["access_token"], settings.secret_key,
                         algorithms=["HS256"])
    assert payload["se"] == 1
    assert client.get(f"{API}/auth/me",
                      headers=_auth(fresh["access_token"])).status_code == 200


def test_legacy_access_without_se_is_still_accepted(client):
    """旧 token 没有 se：视为 0，与存量账号（epoch=0）继续兼容。"""
    data = _register(client, "sesslegacy1")
    user = _user("sesslegacy1")
    now = int(time.time())
    legacy = jwt.encode({
        "sub": user.handle,
        "pv": password_fingerprint(user.password_hash),
        "iat": now, "exp": now + 3600,
    }, settings.secret_key, algorithm="HS256")
    assert client.get(f"{API}/auth/me", headers=_auth(legacy)).status_code == 200
    # 对照：带错误 se 的 token 必须 401
    wrong_se = jwt.encode({
        "sub": user.handle,
        "pv": password_fingerprint(user.password_hash),
        "se": 99, "iat": now, "exp": now + 3600,
    }, settings.secret_key, algorithm="HS256")
    assert client.get(f"{API}/auth/me", headers=_auth(wrong_se)).status_code == 401


# ── 3. GitHub 回跳：白名单 + 一次性 handoff code ────────────────────────────
def test_return_to_whitelist_rejects_open_redirects(client, github_configured):
    for bad in ("https://evil.example.com",
                "https://robowiki.github.io.evil.com",
                "https://robowiki.github.io/steal-path",
                "https://robowiki.github.io/?next=evil",
                "javascript:alert(1)"):
        r = _start_github(client, bad)
        assert r.status_code == 400, f"{bad} 应被拒绝，实际 {r.status_code}"


def test_return_to_allows_main_domain_mirror_and_localhost(client,
                                                           github_configured):
    for ok in ("https://robowiki.org.cn", MIRROR,
               "http://localhost:5173", "http://127.0.0.1:8000"):
        r = _start_github(client, ok)
        assert r.status_code in (302, 307), f"{ok}: {r.status_code} {r.text}"
        assert r.headers["location"].startswith(
            "https://github.com/login/oauth/authorize")


def test_handoff_redirect_carries_code_not_jwt(client, github_configured,
                                               monkeypatch):
    _fake_github(monkeypatch, subject="91001", login="mirror-user")
    assert _start_github(client, MIRROR).status_code in (302, 307)

    r = _github_callback(client)
    assert r.status_code == 302, r.text
    location = r.headers["location"]
    assert location.startswith(f"{MIRROR}/login#code="), location
    assert "#token=" not in location, "JWT 绝不能出现在 Location"
    code = location.split("#code=", 1)[1]
    assert len(code) >= 20

    exchange = client.post(f"{API}/auth/handoff", json={"code": code})
    assert exchange.status_code == 200, exchange.text
    data = exchange.json()
    assert data["access_token"] and data["refresh_token"]
    assert client.get(f"{API}/auth/me",
                      headers=_auth(data["access_token"])).status_code == 200
    assert _refresh(client, data["refresh_token"]).status_code == 200

    # 一次性：同一个 code 不能换第二次
    again = client.post(f"{API}/auth/handoff", json={"code": code})
    assert again.status_code == 401, again.text


def test_handoff_code_expires(client, github_configured, monkeypatch):
    _fake_github(monkeypatch, subject="91002", login="expire-user")
    _start_github(client, MIRROR)
    location = _github_callback(client).headers["location"]
    code = location.split("#code=", 1)[1]

    db = db_session()
    try:
        row = db.exec(select(HandoffCode).where(
            HandoffCode.code_hash == hash_secret(code))).first()
        assert row is not None
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.add(row)
        db.commit()
    finally:
        db.close()

    assert client.post(f"{API}/auth/handoff",
                       json={"code": code}).status_code == 401


def test_handoff_unknown_code_is_401(client):
    assert client.post(f"{API}/auth/handoff",
                       json={"code": "not-a-real-handoff-code"}).status_code == 401


def test_github_callback_json_path_still_works(client, github_configured,
                                               monkeypatch):
    """主站/小程序直连 JSON 的旧契约不变。"""
    _fake_github(monkeypatch, subject="91003", login="json-user")
    r = client.get(f"{API}/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"] and data["refresh_token"]
    payload = jwt.decode(data["access_token"], settings.secret_key,
                         algorithms=["HS256"])
    assert payload["scope"] == "github"

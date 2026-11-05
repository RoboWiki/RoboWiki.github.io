"""多端身份（Identity）测试。

覆盖的是「一个领域 API + 一套身份抽象」这件事本身：

  · `(provider, subject)` 唯一 —— 同一人重复登录落在同一行、同一个 user；
  · 未配置的渠道返回 503，而不是把应用带崩；
  · 小程序 mock 成功/失败都走同一条「找/建 user → 签现有 JWT」的路；
  · 解绑不能把账号锁死（至少留一种登录方式）；
  · 第三方建号不许并进「未验证邮箱」的已有账号（那是账号接管）。

**不发真实网络请求**：GitHub 的 Authlib 交换与资料抓取、微信的
jscode2session 全部 monkeypatch 掉。

    cd backend && py -3.12 -m pytest tests/test_identities.py -q
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# 必须在 import app 之前设置（settings 在 import 时实例化）。
# 用 setdefault：与其他模块同进程跑时复用它们的临时库，避免两套 engine 打架。
_TMP = tempfile.mkdtemp(prefix="roboselect-identity-test-")
os.environ.setdefault("ROBOWIKI_DB_PATH", str(pathlib.Path(_TMP) / "test.db"))
os.environ.setdefault("ROBOWIKI_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")
os.environ.setdefault("ROBOWIKI_BOT_TOKEN", "test-bot-token")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlmodel import select  # noqa: E402

from app.api.routes import auth as auth_route  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.security import create_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Identity, User  # noqa: E402

# https 基址：OAuth state cookie 是 Secure 的（site_url 默认 https），
# 用 http 基址 httpx 不会回传这个 cookie。
BASE = "https://testserver"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url=BASE) as c:
        yield c


def _db():
    from app.core.db import session
    return session()


def _count_identities(provider: str, subject: str) -> int:
    db = _db()
    try:
        return len(db.exec(select(Identity).where(
            Identity.provider == provider, Identity.subject == subject)).all())
    finally:
        db.close()


def _get_identity(provider: str, subject: str) -> Identity | None:
    db = _db()
    try:
        return db.exec(select(Identity).where(
            Identity.provider == provider, Identity.subject == subject)).first()
    finally:
        db.close()


def _user_by_handle(handle: str) -> User | None:
    db = _db()
    try:
        return db.exec(select(User).where(User.handle == handle)).first()
    finally:
        db.close()


def _register(client: TestClient, handle: str, password: str = "pass1234",
              email: str | None = None) -> dict:
    r = client.post("/api/auth/register", json={
        "handle": handle, "display_name": handle,
        "password": password, "email": email})
    assert r.status_code == 201, r.text
    return r.json()


def _bind(handle: str, provider: str, subject: str) -> None:
    """直接插一行身份：用来造「一个账号绑了两种身份」的场景。"""
    db = _db()
    try:
        u = db.exec(select(User).where(User.handle == handle)).first()
        assert u is not None
        db.add(Identity(user_id=u.id, provider=provider, subject=subject))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def github_configured(monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "test-client-secret")


@pytest.fixture
def wechat_configured(monkeypatch):
    monkeypatch.setattr(settings, "wechat_mp_appid", "wx-test-appid")
    monkeypatch.setattr(settings, "wechat_mp_secret", "wx-test-secret")


def fake_github(monkeypatch, *, subject: str, login: str, name: str = "GH User",
                email: str | None = None, verified: bool = True) -> None:
    """替掉 Authlib 的两处副作用：换 token、抓资料。不碰真实 GitHub。"""

    async def exchange(request, client):
        return {"access_token": "fake-token", "token_type": "bearer"}

    async def profile(client, token):
        return {"subject": subject, "login": login, "name": name,
                "email": email, "email_verified": bool(email) and verified,
                "raw": {"id": subject, "login": login}}

    monkeypatch.setattr(auth_route, "_github_exchange", exchange)
    monkeypatch.setattr(auth_route, "_github_profile", profile)


# ── 1. 身份表本身：(provider, subject) 唯一 ─────────────────────────────────
def test_identity_unique_constraint_holds(client):
    handle = "iduniq1"
    _register(client, handle)
    _bind(handle, "github", "uniq-subject-1")

    db = _db()
    try:
        u = db.exec(select(User).where(User.handle == handle)).first()
        db.add(Identity(user_id=u.id, provider="github", subject="uniq-subject-1"))
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()

    assert _count_identities("github", "uniq-subject-1") == 1


def test_one_user_can_bind_several_identities(client):
    handle = "idmulti1"
    _register(client, handle)
    _bind(handle, "github", "multi-gh-1")
    _bind(handle, "wechat_mini", "multi-wx-1")

    db = _db()
    try:
        u = db.exec(select(User).where(User.handle == handle)).first()
        rows = db.exec(select(Identity).where(Identity.user_id == u.id)).all()
        assert {r.provider for r in rows} == {"github", "wechat_mini"}
    finally:
        db.close()


# ── 2. GitHub：未配置 → 503，且应用不崩 ─────────────────────────────────────
def test_providers_reports_only_configured_channels(client, monkeypatch):
    """公开能力表：没配的渠道必须是 false，前端据此禁用按钮。"""
    monkeypatch.setattr(settings, "github_client_id", None)
    monkeypatch.setattr(settings, "github_client_secret", None)
    monkeypatch.setattr(settings, "wechat_mp_appid", None)
    monkeypatch.setattr(settings, "wechat_mp_secret", None)

    r = client.get("/api/v1/auth/providers")
    assert r.status_code == 200, r.text
    assert r.json() == {"email": True, "github": False, "wechat_mini": False}
    # 公开接口：不需要令牌
    assert "access_token" not in r.text


def test_providers_reflects_enabled_config(client, github_configured,
                                           wechat_configured):
    r = client.get("/api/v1/auth/providers")
    assert r.status_code == 200, r.text
    assert r.json() == {"email": True, "github": True, "wechat_mini": True}


def test_providers_channels_are_independent(client, github_configured, monkeypatch):
    """只配 GitHub 时不能把微信也报成可用（前端/小程序按此分支）。"""
    monkeypatch.setattr(settings, "wechat_mp_appid", None)
    monkeypatch.setattr(settings, "wechat_mp_secret", None)
    r = client.get("/api/v1/auth/providers")
    assert r.json() == {"email": True, "github": True, "wechat_mini": False}


def test_github_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "github_client_id", None)
    monkeypatch.setattr(settings, "github_client_secret", None)

    login = client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert login.status_code == 503, login.text

    callback = client.get("/api/v1/auth/github/callback", params={"code": "x"},
                          follow_redirects=False)
    assert callback.status_code == 503, callback.text

    # 未配置也不能影响口令登录
    assert client.post("/api/auth/login", json={"handle": "robowiki",
                                                "password": "robowiki"}).status_code == 200


def test_github_login_redirects_with_state(client, github_configured):
    r = client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert r.status_code in (302, 307), r.text
    location = r.headers["location"]
    assert location.startswith("https://github.com/login/oauth/authorize"), location
    assert "client_id=test-client-id" in location
    assert "state=" in location, "state 必须由 Authlib 生成，不能省"
    assert "code_challenge=" in location, "Authlib 默认走 PKCE"
    # state 落在签名 cookie 里，回调时校验
    assert any("robowiki_oauth_state" in v for k, v in r.headers.items()
               if k.lower() == "set-cookie")


# ── 3. GitHub：首次登录建号 / 再次登录复用 ──────────────────────────────────
def test_github_callback_creates_user_and_token(client, github_configured,
                                               monkeypatch):
    fake_github(monkeypatch, subject="90001", login="octo-one",
                name="Octo One", email="octo1@example.com")

    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    data = r.json()
    payload = jwt.decode(data["access_token"], settings.secret_key,
                         algorithms=["HS256"])
    assert payload["sub"] == data["user"]["handle"]
    assert payload["scope"] == "github", "token 声明来源，但不影响授权判断"
    assert payload["pv"], "第三方登录也必须带口令指纹（沿用现有撤销机制）"

    ident = _get_identity("github", "90001")
    assert ident is not None and ident.email == "octo1@example.com"
    assert ident.user_id == data["user"]["id"]

    user = _user_by_handle(data["user"]["handle"])
    assert user is not None
    assert user.password_set is False, "第三方建号没有可用口令"
    assert user.handle.startswith("gh-"), user.handle

    # 签出来的 token 与口令登录完全等价：能直接访问现有接口
    me = client.get("/api/auth/me",
                    headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == data["user"]["id"]


def test_github_callback_reuses_same_identity(client, github_configured,
                                              monkeypatch):
    fake_github(monkeypatch, subject="90002", login="octo-two",
                name="Octo Two", email="octo2@example.com")

    first = client.get("/api/v1/auth/github/callback",
                       params={"code": "fake", "state": "fake"},
                       headers={"Accept": "application/json"}).json()
    second = client.get("/api/v1/auth/github/callback",
                        params={"code": "fake", "state": "fake"},
                        headers={"Accept": "application/json"}).json()

    assert first["user"]["id"] == second["user"]["id"], "同一 subject 必须复用同一账号"
    assert _count_identities("github", "90002") == 1, "重复登录不能多出一行身份"


def test_github_callback_redirects_to_login_fragment(client, github_configured,
                                                    monkeypatch):
    fake_github(monkeypatch, subject="90003", login="octo-three",
                name="Octo Three", email="octo3@example.com")

    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   follow_redirects=False)
    assert r.status_code == 302, r.text
    location = r.headers["location"]
    prefix = f"{settings.site_url.rstrip('/')}/login#token="
    assert location.startswith(prefix), location
    token = location[len(prefix):]
    assert client.get("/api/auth/me",
                      headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_github_callback_rejects_incomplete_profile(client, github_configured,
                                                   monkeypatch):
    fake_github(monkeypatch, subject="", login="no-id")
    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 502, r.text


def test_github_oauth_error_is_400_not_500(client, github_configured,
                                           monkeypatch):
    async def boom(request, client):
        raise auth_route.OAuthError(error="mismatching_state")

    monkeypatch.setattr(auth_route, "_github_exchange", boom)
    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "bad"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 400, r.text
    assert "state" not in r.text.lower(), "不要回显协议细节"


# ── 4. 并号只认「提供方已验证」的邮箱 ───────────────────────────────────────
def test_github_links_verified_email_to_existing_account(client, github_configured,
                                                         monkeypatch):
    reg = _register(client, "idlink1", email="link1@example.com")
    before = reg["user"]["id"]

    fake_github(monkeypatch, subject="90010", login="linker",
                name="Linker", email="link1@example.com", verified=True)
    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["id"] == before, "已验证邮箱应并入已有账号"

    ident = _get_identity("github", "90010")
    assert ident is not None and ident.user_id == before
    # 认领未验证邮箱账号时必须清掉占位口令：否则先占邮箱的人还能继续登录。
    assert _user_by_handle("idlink1").password_set is False
    # GitHub 已经证明邮箱归属，本站的「已验证」跟着补齐
    assert _user_by_handle("idlink1").email_verified is True
    # 认领会提升 session_epoch，旧 access 立即失效
    old = reg.get("access_token")
    assert old
    assert client.get("/api/v1/auth/me",
                      headers={"Authorization": f"Bearer {old}"}).status_code == 401
    # 旧口令也不能再登录
    assert client.post("/api/v1/auth/login", json={
        "handle": "idlink1", "password": "pass1234"}).status_code == 401


def test_github_unverified_email_never_takes_over_account(client, github_configured,
                                                          monkeypatch):
    reg = _register(client, "idlink2", email="link2@example.com")
    victim_id = reg["user"]["id"]

    # 未验证邮箱：绝不能并进已有账号（否则就是账号接管）
    fake_github(monkeypatch, subject="90011", login="attacker",
                name="Attacker", email="link2@example.com", verified=False)
    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["id"] != victim_id, "未验证邮箱不得并入他人账号"

    ident = _get_identity("github", "90011")
    assert ident is not None and ident.user_id != victim_id
    assert _user_by_handle("idlink2").email == "link2@example.com", "受害者邮箱不能被顶掉"


def test_verified_email_does_not_merge_account_with_other_identities(
        client, github_configured, monkeypatch):
    """先占邮箱并绑自己 GitHub 的账号，不能靠受害者邮箱被并进来。"""
    reg = _register(client, "idlink3", email="link3@example.com")
    victim_id = reg["user"]["id"]
    _bind("idlink3", "wechat_mini", "attacker-openid")

    fake_github(monkeypatch, subject="90012", login="victim",
                name="Victim", email="link3@example.com", verified=True)
    r = client.get("/api/v1/auth/github/callback",
                   params={"code": "fake", "state": "fake"},
                   headers={"Accept": "application/json"})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["id"] != victim_id, "已有其他身份的账号不得被验证邮箱认领"
    # 原账号口令仍然有效，不会被并号清掉
    assert _user_by_handle("idlink3").password_set is True
    db = _db()
    try:
        assert len([i for i in db.exec(select(Identity)).all()
                    if i.user_id == victim_id]) == 1
    finally:
        db.close()


# ── 5. 微信小程序：未配置 503 / mock 成功 / mock 失败 ───────────────────────
def test_wechat_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "wechat_mp_appid", None)
    monkeypatch.setattr(settings, "wechat_mp_secret", None)
    r = client.post("/api/v1/auth/wechat/mini", json={"code": "abc"})
    assert r.status_code == 503, r.text
    assert "secret" not in r.text.lower()


def test_wechat_mini_mocked_success(client, wechat_configured, monkeypatch):
    async def fake_session(code: str) -> dict:
        assert code == "wx-code-ok"
        return {"openid": "openid-aaa", "session_key": "SHOULD-NOT-BE-STORED",
                "unionid": "union-aaa"}

    monkeypatch.setattr(auth_route, "_wechat_code2session", fake_session)
    r = client.post("/api/v1/auth/wechat/mini",
                    json={"code": "wx-code-ok", "nickname": "小陀螺"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["display_name"] == "小陀螺"

    payload = jwt.decode(data["access_token"], settings.secret_key,
                         algorithms=["HS256"])
    assert payload["scope"] == "wechat_mini"

    ident = _get_identity("wechat_mini", "openid-aaa")
    assert ident is not None and ident.user_id == data["user"]["id"]
    assert "session_key" not in (ident.raw or {}), "session_key 是密钥，不落库"
    assert ident.raw.get("unionid") == "union-aaa"

    # 同一 openid 再登一次：同一账号、不新增身份
    again = client.post("/api/v1/auth/wechat/mini", json={"code": "wx-code-ok"})
    assert again.status_code == 200
    assert again.json()["user"]["id"] == data["user"]["id"]
    assert _count_identities("wechat_mini", "openid-aaa") == 1


def test_wechat_mini_bad_code_is_400(client, wechat_configured, monkeypatch):
    async def fake_session(code: str) -> dict:
        return {"errcode": 40029, "errmsg": "invalid code"}

    monkeypatch.setattr(auth_route, "_wechat_code2session", fake_session)
    r = client.post("/api/v1/auth/wechat/mini", json={"code": "bad"})
    assert r.status_code == 400, r.text
    assert "invalid code" not in r.text, "不要把微信原文回显给客户端"


def test_wechat_mini_upstream_error_is_502(client, wechat_configured, monkeypatch):
    async def fake_session(code: str) -> dict:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(auth_route, "_wechat_code2session", fake_session)
    r = client.post("/api/v1/auth/wechat/mini", json={"code": "x"})
    assert r.status_code == 502, r.text


def test_wechat_mini_builds_request_body_and_hides_secret(client, wechat_configured,
                                                          monkeypatch):
    """不 mock 我们自己的函数，直接 mock httpx：验请求参数本身是对的。"""
    calls: list[tuple[str, dict]] = []

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"openid": "openid-httpx"}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, params=None):
            calls.append((url, dict(params or {})))
            return FakeResponse()

    monkeypatch.setattr(auth_route.httpx, "AsyncClient", FakeAsyncClient)
    r = client.post("/api/v1/auth/wechat/mini", json={"code": "code-xyz"})
    assert r.status_code == 200, r.text

    url, params = calls[-1]
    assert url.endswith("/sns/jscode2session"), url
    assert params["js_code"] == "code-xyz"
    assert params["grant_type"] == "authorization_code"
    assert params["appid"] == "wx-test-appid"
    assert params["secret"] == "wx-test-secret"
    # AppSecret 只在后端→微信这一跳里出现，绝不回到客户端
    assert "wx-test-secret" not in r.text


# ── 6. 身份列表 / 解绑 ──────────────────────────────────────────────────────
def test_identities_require_login(client):
    assert client.get("/api/v1/auth/identities").status_code == 401
    assert client.delete("/api/v1/auth/identities/github").status_code == 401


def test_list_identities(client):
    handle = "idlist1"
    reg = _register(client, handle)
    _bind(handle, "github", "list-gh-1")
    _bind(handle, "wechat_mini", "list-wx-1")
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    r = client.get("/api/v1/auth/identities", headers=headers)
    assert r.status_code == 200, r.text
    rows = r.json()
    assert {row["provider"] for row in rows} == {"github", "wechat_mini"}
    assert all("created_at" in row for row in rows)


def test_unbind_unknown_provider_404(client):
    reg = _register(client, "idunbind0")
    headers = {"Authorization": f"Bearer {reg['access_token']}"}
    r = client.delete("/api/v1/auth/identities/github", headers=headers)
    assert r.status_code == 404, r.text


def test_cannot_unbind_last_login_method(client, github_configured, monkeypatch):
    """第三方建号 + 只绑了一个身份：解绑后账号就再也进不来了，必须拒绝。"""
    fake_github(monkeypatch, subject="90020", login="onlyone",
                name="Only One", email="only1@example.com")
    data = client.get("/api/v1/auth/github/callback",
                      params={"code": "fake", "state": "fake"},
                      headers={"Accept": "application/json"}).json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    r = client.delete("/api/v1/auth/identities/github", headers=headers)
    assert r.status_code == 409, r.text
    assert _count_identities("github", "90020") == 1, "被拒绝的解绑不能生效"


def test_unbind_allowed_when_password_exists(client):
    handle = "idpass1"
    reg = _register(client, handle)
    _bind(handle, "github", "pass-gh-1")
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    r = client.delete("/api/v1/auth/identities/github", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["remaining"] == 0
    assert _count_identities("github", "pass-gh-1") == 0

    # 解绑后口令登录照旧
    assert client.post("/api/auth/login",
                       json={"handle": handle, "password": "pass1234"}).status_code == 200


def test_unbind_one_of_two_identities(client):
    handle = "idtwo1"
    reg = _register(client, handle)
    _bind(handle, "github", "two-gh-1")
    _bind(handle, "wechat_mini", "two-wx-1")
    headers = {"Authorization": f"Bearer {reg['access_token']}"}

    first = client.delete("/api/v1/auth/identities/github", headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["remaining"] == 1

    second = client.delete("/api/v1/auth/identities/wechat_mini", headers=headers)
    assert second.status_code == 200, second.text
    assert second.json()["remaining"] == 0


# ── 7. token 契约没被改坏 ───────────────────────────────────────────────────
def test_existing_password_token_still_accepted(client):
    """第三方身份上线后，老的口令登录 token 必须原样可用。"""
    reg = _register(client, "idcompat1")
    token = reg["access_token"]
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert payload["scope"] == "password"
    assert client.get("/api/auth/me",
                      headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_legacy_token_without_scope_still_works(client):
    """scope 是增量声明：不带 scope 的 token（旧客户端）不能被拒。"""
    handle = "idcompat2"
    _register(client, handle)
    user = _user_by_handle(handle)
    legacy = create_token(user.handle, user.password_hash)   # 不带 scopes
    payload = jwt.decode(legacy, settings.secret_key, algorithms=["HS256"])
    assert "scope" not in payload
    assert client.get("/api/auth/me",
                      headers={"Authorization": f"Bearer {legacy}"}).status_code == 200


def test_oauth_built_account_has_no_usable_password(client):
    handle = "idnopass1"
    db = _db()
    try:
        db.add(User(handle=handle, display_name=handle, email=None,
                    password_hash=hash_password("secret-of-nobody"),
                    password_set=False))
        db.commit()
    finally:
        db.close()
    # password_set=False 的语义：口令登录不是一条可用路径（口令没人知道）
    assert _user_by_handle(handle).password_set is False

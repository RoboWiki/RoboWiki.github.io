"""账号中心：改密链路。

钉住四件事：
  · 改密成功返回新 token，当前会话可以无缝继续；
  · 旧 token 因 `pv` 指纹变化而立刻失效（其他设备一并下线）；
  · 当前密码错误 / 新密码太短时，口令与旧 token 都不能被改动；
  · 错误话术不含账号信息（邮箱、handle、是否设过口令）。

    cd backend && py -3.12 -m pytest tests/test_interactions_account.py -q
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile

# 必须在 import app 之前设置（settings 在 import 时实例化）。
# 用 setdefault：与其它模块同进程跑时复用它们的临时库，避免两套 engine 打架。
_TMP = tempfile.mkdtemp(prefix="roboselect-account-test-")
os.environ.setdefault("ROBOWIKI_DB_PATH", str(pathlib.Path(_TMP) / "test.db"))
os.environ.setdefault("ROBOWIKI_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")
os.environ.setdefault("ROBOWIKI_BOT_TOKEN", "test-bot-token")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import select  # noqa: E402

from app.core.config import settings  # noqa: E402
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


def _register(client: TestClient, handle: str, password: str = "pass1234",
              email: str | None = None) -> dict:
    r = client.post("/api/auth/register", json={
        "handle": handle, "display_name": handle,
        "password": password, "email": email})
    assert r.status_code == 201, r.text
    return r.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, handle: str, password: str):
    return client.post("/api/auth/login",
                       json={"handle": handle, "password": password})


# ── 1. 成功：换新 token，旧 token 失效 ──────────────────────────────────────
def test_change_password_rotates_token(client):
    handle = "acct-chg-ok"
    reg = _register(client, handle, password="oldpass123",
                    email="acct-chg-ok@example.com")
    old_token = reg["access_token"]
    assert client.get("/api/auth/me", headers=_auth(old_token)).status_code == 200

    r = client.post("/api/v1/auth/password/change", headers=_auth(old_token),
                    json={"current_password": "oldpass123",
                          "new_password": "newpass456"})
    assert r.status_code == 200, r.text
    data = r.json()
    new_token = data["access_token"]
    assert new_token and new_token != old_token
    assert data["user"]["handle"] == handle
    assert data["user"]["password_set"] is True
    # 响应里绝不带口令哈希
    assert "password_hash" not in r.text

    payload = jwt.decode(new_token, settings.secret_key, algorithms=["HS256"])
    assert payload["sub"] == handle
    assert payload["pv"], "新 token 必须绑定新口令指纹"

    # 旧 token（pv 指向旧哈希）立刻失效；新 token 可继续用
    assert client.get("/api/auth/me", headers=_auth(old_token)).status_code == 401
    assert client.get("/api/auth/me", headers=_auth(new_token)).status_code == 200

    # 口令本身也换了：旧口令登不进，新口令可以
    assert _login(client, handle, "oldpass123").status_code == 401
    assert _login(client, handle, "newpass456").status_code == 200


# ── 2. 当前密码错：403，且不改口令、不撤销旧 token ─────────────────────────
def test_wrong_current_password_is_rejected_without_side_effects(client):
    handle = "acct-chg-wrong"
    reg = _register(client, handle, password="oldpass123",
                    email="acct-chg-wrong@example.com")
    token = reg["access_token"]

    r = client.post("/api/v1/auth/password/change", headers=_auth(token),
                    json={"current_password": "not-my-password",
                          "new_password": "newpass456"})
    assert r.status_code in (401, 403), r.text
    assert r.json()["detail"] == "当前密码不正确"
    # 错误信息不能变成账号探针
    for secret in (handle, "acct-chg-wrong@example.com", "password_set"):
        assert secret not in r.text, r.text

    # 失败不能有副作用：旧 token 仍可用，旧口令仍能登录
    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 200
    assert _login(client, handle, "oldpass123").status_code == 200
    assert _login(client, handle, "newpass456").status_code == 401


# ── 3. 新密码太短：422，且口令不变 ──────────────────────────────────────────
def test_short_new_password_is_422(client):
    handle = "acct-chg-short"
    reg = _register(client, handle, password="oldpass123")
    token = reg["access_token"]

    r = client.post("/api/v1/auth/password/change", headers=_auth(token),
                    json={"current_password": "oldpass123",
                          "new_password": "12345"})
    assert r.status_code == 422, r.text

    assert client.get("/api/auth/me", headers=_auth(token)).status_code == 200
    assert _login(client, handle, "oldpass123").status_code == 200


# ── 4. 未登录不能改密 ───────────────────────────────────────────────────────
def test_change_password_requires_login(client):
    r = client.post("/api/v1/auth/password/change",
                    json={"current_password": "whatever",
                          "new_password": "newpass456"})
    assert r.status_code == 401, r.text


# ── 资料编辑 / 首次设密 / 设备会话 ─────────────────────────────────────────
def test_profile_update_changes_public_fields(client):
    handle = "acct-profile"
    reg = _register(client, handle)
    token = reg["access_token"]

    r = client.patch("/api/v1/auth/me", headers=_auth(token),
                     json={"display_name": "新名字", "bio": "玩四足和机械臂"})
    assert r.status_code == 200, r.text
    assert r.json()["display_name"] == "新名字"
    assert r.json()["bio"] == "玩四足和机械臂"

    me = client.get("/api/v1/auth/me", headers=_auth(token)).json()
    assert me["display_name"] == "新名字"
    # 公开作者信息同步，但不泄露邮箱
    pub = client.get("/api/v1/users/" + handle).json()
    assert pub["display_name"] == "新名字"
    assert "email" not in pub


def test_third_party_account_can_set_password(client):
    from app.core.db import session
    from app.core.security import create_token, unusable_password_hash
    from app.models import User

    handle = "acct-thirdparty"
    with session() as db:
        u = User(handle=handle, display_name="第三方账号",
                 password_hash=unusable_password_hash(), password_set=False)
        db.add(u)
        db.commit()
        db.refresh(u)
        token = create_token(handle, u.password_hash,
                             session_epoch=u.session_epoch or 0)

    r = client.post("/api/v1/auth/password/set", headers=_auth(token),
                    json={"password": "thirdpass1"})
    assert r.status_code == 200, r.text
    new = r.json()
    assert new["access_token"] and new["refresh_token"]
    # 设密会提升 epoch：旧 access 不能继续用
    assert client.get("/api/v1/auth/me", headers=_auth(token)).status_code == 401
    assert client.get("/api/v1/auth/me",
                      headers=_auth(new["access_token"])).status_code == 200
    assert _login(client, handle, "thirdpass1").status_code == 200
    # 已设过只能走改密
    assert client.post("/api/v1/auth/password/set",
                       headers=_auth(new["access_token"]),
                       json={"password": "another1"}).status_code == 409


def test_session_list_and_revoke(client):
    handle = "acct-sessions"
    reg = _register(client, handle)
    token = reg["access_token"]
    sessions = client.get("/api/v1/auth/sessions", headers=_auth(token)).json()
    assert len(sessions) == 1
    sid = sessions[0]["id"]

    assert client.delete(f"/api/v1/auth/sessions/{sid}",
                         headers=_auth(token)).status_code == 204
    assert client.get("/api/v1/auth/sessions", headers=_auth(token)).json() == []
    # 该 refresh 已被撤销，不能再续期
    r = client.post("/api/v1/auth/refresh",
                    json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 401


def test_email_change_verifies_new_address_and_revokes_old_session(client, monkeypatch):
    import re
    from app.core.db import session
    from app.models import User

    handle = "acct-email-change"
    reg = _register(client, handle, email="old-address@example.com")
    token = reg["access_token"]
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.api.routes.auth.send_email",
        lambda to, subject, text, html=None: sent.append((to, text)),
    )

    bad = client.post("/api/v1/auth/email/change/request", headers=_auth(token),
                      json={"email": "new-address@example.com", "password": "wrong"})
    assert bad.status_code == 403

    ok = client.post("/api/v1/auth/email/change/request", headers=_auth(token),
                     json={"email": "new-address@example.com", "password": "pass1234"})
    assert ok.status_code == 200, ok.text
    assert sent and sent[-1][0] == "new-address@example.com"
    raw = re.search(r"验证令牌[：:]\s*(\S+)", sent[-1][1])
    assert raw, sent[-1][1]

    confirmed = client.post("/api/v1/auth/email/change/confirm",
                            headers=_auth(token), json={"token": raw.group(1)})
    assert confirmed.status_code == 200, confirmed.text
    data = confirmed.json()
    assert data["user"]["email"] == "new-address@example.com"
    assert data["user"]["email_verified"] is True
    # 换绑提升 session_epoch：旧 access 立即失效，新 access 可用
    assert client.get("/api/v1/auth/me", headers=_auth(token)).status_code == 401
    assert client.get("/api/v1/auth/me",
                      headers=_auth(data["access_token"])).status_code == 200
    with session() as db:
        u = db.exec(select(User).where(User.handle == handle)).first()
        assert u.email == "new-address@example.com" and u.email_verified


def test_email_change_rejects_taken_address(client):
    h1 = "acct-email-taken1"
    h2 = "acct-email-taken2"
    _register(client, h1, email="taken1@example.com")
    r2 = _register(client, h2)
    r = client.post("/api/v1/auth/email/change/request",
                    headers=_auth(r2["access_token"]),
                    json={"email": "taken1@example.com", "password": "pass1234"})
    assert r.status_code == 409


def test_verified_user_notification_queues_email(client):
    from app.core.db import session
    from app.models import EmailOutbox, User
    from app.api.routes.notifications import create_notification

    handle = "acct-email-notify"
    _register(client, handle, email="notify-me@example.com")
    with session() as db:
        u = db.exec(select(User).where(User.handle == handle)).first()
        u.email_verified = True
        u.email_notify = True
        db.add(u)
        db.commit()
        create_notification(db, u.id, type="reply", subject="测试通知",
                            body="有人回复了你", link="/catalog")
        db.commit()
        jobs = db.exec(select(EmailOutbox).where(
            EmailOutbox.user_id == u.id)).all()
        assert jobs and jobs[-1].to_addr == "notify-me@example.com"
        assert jobs[-1].status == "pending"


def test_login_accepts_email_or_handle(client):
    handle = "acct-email-login"
    email = "login-by-email@example.com"
    _register(client, handle, email=email)
    assert _login(client, handle, "pass1234").status_code == 200
    assert _login(client, email.upper(), "pass1234").status_code == 200

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

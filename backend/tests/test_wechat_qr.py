"""微信扫码登录（网页 + 小程序确认器）的协议回归。

整条链路：create 发 ticket 与小程序码 → confirm 用 code 换 openid 并原子占用票据
→ status 一次性取走会话。测试不连微信：二维码接口与 code2session 都打桩。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# 必须在 import app 之前设置，settings 在 import 时实例化
_TMP = tempfile.mkdtemp(prefix="robowiki-qr-test-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


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


@pytest.fixture()
def wechat_ready(monkeypatch):
    """把「微信已配置 + 二维码/会话接口打桩」打包成前置条件。"""
    from app.api.routes import auth as auth_routes

    monkeypatch.setattr(auth_routes.settings, "wechat_mp_appid", "wx-test-appid")
    monkeypatch.setattr(auth_routes.settings, "wechat_mp_secret", "wx-test-secret")

    async def fake_image(ticket: str) -> bytes:
        assert len(ticket) == 32, "ticket 必须正好 32 个字符（scene 上限）"
        return PNG_BYTES

    async def fake_code2session(code: str) -> dict:
        # 同一个 code 对应同一个 openid；不同 code 是新用户
        return {"openid": f"openid-{code}", "unionid": ""}

    monkeypatch.setattr(auth_routes, "_wechat_qr_image", fake_image)
    monkeypatch.setattr(auth_routes, "_wechat_code2session", fake_code2session)
    return auth_routes


def test_qr_create_is_503_when_wechat_not_configured(client, monkeypatch):
    from app.api.routes import auth as auth_routes
    monkeypatch.setattr(auth_routes.settings, "wechat_mp_appid", None)
    monkeypatch.setattr(auth_routes.settings, "wechat_mp_secret", None)
    r = client.post("/api/auth/wechat/qr")
    assert r.status_code == 503


def test_qr_login_end_to_end(client, wechat_ready):
    r = client.post("/api/auth/wechat/qr")
    assert r.status_code == 200, r.text
    created = r.json()
    ticket = created["ticket"]
    assert len(ticket) == 32 and int(ticket, 16) >= 0   # 32 位 hex
    assert created["qrcode"]
    assert created["expires_in"] == 300

    # 未确认前是 pending
    st = client.get("/api/auth/wechat/qr/status", params={"ticket": ticket})
    assert st.status_code == 200 and st.json()["status"] == "pending"

    # 小程序确认
    c = client.post("/api/auth/wechat/qr/confirm",
                    json={"ticket": ticket, "code": "code-1"})
    assert c.status_code == 200, c.text
    assert c.json() == {"ok": True}

    # 网页取走一次性会话
    st = client.get("/api/auth/wechat/qr/status", params={"ticket": ticket})
    body = st.json()
    assert body["status"] == "confirmed"
    token = body["token"]
    assert token["access_token"] and token["refresh_token"]
    assert token["user"]["handle"]

    # 票据已删除：再查就是 expired（防重放）
    st2 = client.get("/api/auth/wechat/qr/status", params={"ticket": ticket})
    assert st2.json()["status"] == "expired"

    # 用拿到的 access_token 能访问 /auth/me
    me = client.get("/api/auth/me",
                    headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200
    assert me.json()["handle"] == token["user"]["handle"]


def test_qr_confirm_twice_is_rejected(client, wechat_ready):
    ticket = client.post("/api/auth/wechat/qr").json()["ticket"]
    first = client.post("/api/auth/wechat/qr/confirm",
                        json={"ticket": ticket, "code": "code-dup"})
    assert first.status_code == 200
    second = client.post("/api/auth/wechat/qr/confirm",
                         json={"ticket": ticket, "code": "code-dup"})
    assert second.status_code == 409


def test_qr_confirm_unknown_ticket_is_410(client, wechat_ready):
    r = client.post("/api/auth/wechat/qr/confirm",
                    json={"ticket": "deadbeef" * 4, "code": "code-x"})
    assert r.status_code == 410


def test_qr_login_reuses_same_wechat_identity(client, wechat_ready):
    """同一微信号扫码两次必须落到同一个账号（identity 唯一约束）。"""
    handles = []
    for _ in range(2):
        ticket = client.post("/api/auth/wechat/qr").json()["ticket"]
        client.post("/api/auth/wechat/qr/confirm",
                    json={"ticket": ticket, "code": "code-same"})
        body = client.get("/api/auth/wechat/qr/status",
                          params={"ticket": ticket}).json()
        handles.append(body["token"]["user"]["handle"])
    assert handles[0] == handles[1]

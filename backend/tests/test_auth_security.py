"""认证/授权侧信道与资源耗尽回归测试。

对应四类问题（都是先能复现、再修）：

1. 登录账号枚举：用户不存在时短路跳过 PBKDF2，响应时长可区分账号是否存在；
2. 注册接口：409「邮箱已注册」本身就是枚举接口；
3. JWT 无撤销：改密 / 重置密码后旧 token 仍然可用；
4. 限流桶无上限：伪造 X-Forwarded-For 可以无限长内存；
5. 机器人令牌比较：非 ASCII 入参抛 TypeError → 500。

    cd backend && py -3.12 -m pytest tests/test_auth_security.py -q
"""
from __future__ import annotations

import pathlib
import re
import sys
import tempfile

# 必须在 import app 之前设置（settings 在 import 时实例化）。
# 用 setdefault：与 test_api.py 同进程跑时复用它的临时库，避免两套 engine 打架。
_TMP = tempfile.mkdtemp(prefix="roboselect-auth-test-")
_TMP_PATH = pathlib.Path(_TMP) / "test.db"
import os  # noqa: E402

os.environ.setdefault("ROBOWIKI_DB_PATH", str(_TMP_PATH))
os.environ.setdefault("ROBOWIKI_SECRET_KEY",
                      "test-secret-key-at-least-32-bytes-long-0000")
os.environ.setdefault("ROBOWIKI_BOT_TOKEN", "test-bot-token")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.requests import Request  # noqa: E402

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
    import shutil
    shutil.rmtree(_TMP, ignore_errors=True)


# ── 1. 登录不得泄露账号是否存在 ─────────────────────────────────────────────
def test_unknown_user_and_bad_password_look_identical(client):
    unknown = client.post("/api/auth/login",
                          json={"handle": "no-such-user-xyz", "password": "whatever123"})
    wrong = client.post("/api/auth/login",
                        json={"handle": "robowiki", "password": "wrong-password"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["detail"] == wrong.json()["detail"]
    assert unknown.json()["detail"] == "账号或密码不对"


def test_unknown_user_still_runs_one_pbkdf2(client, monkeypatch):
    """用户不存在时也要对一个固定哑哈希跑一次 PBKDF2，否则时长可判读。"""
    from app.api.routes import auth as auth_route

    seen: list[str] = []
    real = auth_route.verify_password

    def spy(raw: str, stored: str) -> bool:
        seen.append(stored)
        return real(raw, stored)

    monkeypatch.setattr(auth_route, "verify_password", spy)
    r = client.post("/api/auth/login",
                    json={"handle": "no-such-user-xyz", "password": "whatever123"})
    assert r.status_code == 401
    assert len(seen) == 1, "用户不存在时必须仍然执行一次口令校验"
    assert seen[0].startswith("pbkdf2$"), "哑哈希也必须是同成本的 PBKDF2 串"


def test_existing_user_still_verifies_once(client, monkeypatch):
    """对照：正常路径也只跑一次，避免修复后每登录多花一倍 CPU。"""
    from app.api.routes import auth as auth_route

    seen: list[str] = []
    real = auth_route.verify_password

    def spy(raw: str, stored: str) -> bool:
        seen.append(stored)
        return real(raw, stored)

    monkeypatch.setattr(auth_route, "verify_password", spy)
    assert client.post("/api/auth/login",
                       json={"handle": "robowiki",
                             "password": "robowiki"}).status_code == 200
    assert len(seen) == 1


# ── 2. 注册不得暴露「邮箱已注册」 ───────────────────────────────────────────
def test_register_does_not_reveal_taken_email(client):
    first = client.post("/api/auth/register", json={
        "handle": "emailowner", "display_name": "Owner",
        "email": "taken@example.com", "password": "pass1234"})
    assert first.status_code == 201, first.text

    dup = client.post("/api/auth/register", json={
        "handle": "emailprobe", "display_name": "Probe",
        "email": "taken@example.com", "password": "pass1234"})
    assert dup.status_code != 409, "邮箱冲突不能再用 409 明示"
    detail = dup.json()["detail"]
    assert "已注册" not in detail, detail
    assert detail == "注册未完成，请检查邮箱或稍后再试", detail

    # 内部仍必须真的拦住：探测用的 account 不能建出来
    assert client.post("/api/auth/login", json={
        "handle": "emailprobe", "password": "pass1234"}).status_code == 401

    # 正常注册不受影响
    ok = client.post("/api/auth/register", json={
        "handle": "freshmail", "display_name": "Fresh",
        "email": "fresh@example.com", "password": "pass1234"})
    assert ok.status_code == 201, ok.text


def test_register_duplicate_handle_keeps_conflict(client):
    """handle 是公开身份，重复 handle 仍给 409（客户端契约不变）。"""
    r = client.post("/api/auth/register", json={
        "handle": "emailowner", "display_name": "dup", "password": "pass1234"})
    assert r.status_code == 409


# ── 3. JWT 撤销：改密 / 重置后旧 token 失效 ─────────────────────────────────
def test_password_reset_invalidates_old_token(client, monkeypatch):
    from app.api.routes import auth as auth_route

    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(auth_route, "send_email",
                        lambda to, subject, text: sent.append((to, subject, text)))

    reg = client.post("/api/auth/register", json={
        "handle": "resetuser", "display_name": "Reset",
        "email": "resetuser@example.com", "password": "oldpass123"})
    assert reg.status_code == 201, reg.text
    old = {"Authorization": f"Bearer {reg.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=old).status_code == 200

    assert client.post("/api/auth/password/forgot",
                       json={"email": "resetuser@example.com"}).status_code == 202
    token = re.search(r"令牌：(\S+)", sent[-1][2]).group(1)
    assert client.post("/api/auth/password/reset",
                       json={"token": token,
                             "password": "newpass123"}).status_code == 200

    assert client.get("/api/auth/me", headers=old).status_code == 401, \
        "重置密码后旧 token 必须失效"

    login = client.post("/api/auth/login", json={
        "handle": "resetuser", "password": "newpass123"})
    assert login.status_code == 200
    new = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=new).status_code == 200


def test_token_carries_password_fingerprint(client):
    r = client.post("/api/auth/login", json={"handle": "robowiki",
                                            "password": "robowiki"})
    assert r.status_code == 200
    data = jwt.decode(r.json()["access_token"], settings.secret_key,
                      algorithms=["HS256"])
    assert isinstance(data.get("pv"), str) and len(data["pv"]) == 16
    assert all(c in "0123456789abcdef" for c in data["pv"])


def test_token_without_pv_is_rejected(client):
    """没有 pv 的旧 token 一律无效（未上线，可接受）。"""
    import time

    payload = {"sub": "robowiki", "iat": int(time.time()),
               "exp": int(time.time()) + 3600}
    legacy = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {legacy}"})
    assert r.status_code == 401


def test_token_for_other_password_is_rejected(client):
    """pv 与当前 password_hash 指纹不符 → 401（等价于撤销）。"""
    import time

    from app.core.security import password_fingerprint

    payload = {"sub": "robowiki", "pv": password_fingerprint("not-the-real-hash"),
               "iat": int(time.time()), "exp": int(time.time()) + 3600}
    forged = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    assert client.get("/api/auth/me",
                      headers={"Authorization": f"Bearer {forged}"}).status_code == 401


# ── 4. 限流桶必须有上限 ─────────────────────────────────────────────────────
def _req(ip: str) -> Request:
    return Request({
        "type": "http", "method": "GET", "path": "/api/auth/login",
        "headers": [(b"x-forwarded-for", ip.encode())],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80),
        "scheme": "http", "query_string": b"",
    })


def test_rate_limit_bucket_table_is_bounded(monkeypatch):
    from app.api import deps

    monkeypatch.setattr(deps, "_MAX_BUCKETS", 16)
    deps.reset_rate_limits()
    try:
        for i in range(300):
            deps.rate_limit(_req(f"10.{i // 250}.{i // 25 % 10}.{i % 25}"),
                            "probe", 1000)
        assert len(deps._buckets) <= 16, \
            f"桶表被伪造 XFF 撑到 {len(deps._buckets)} 个键"
        assert ("probe", "ip:10.1.1.24") in deps._buckets, "最近使用的桶不能被误淘汰"
    finally:
        deps.reset_rate_limits()


def test_rate_limit_evicts_expired_buckets(monkeypatch):
    """溢出清理时，窗口外的旧桶必须先被丢掉（而不是只按 LRU 硬砍）。"""
    from app.api import deps

    monkeypatch.setattr(deps, "_MAX_BUCKETS", 4)
    deps.reset_rate_limits()
    try:
        import collections
        for i in range(5):
            deps._buckets[("probe", f"ip:old{i}")] = collections.deque([0.0])
        deps.rate_limit(_req("10.9.9.9"), "probe", 1000)
        assert not any(k[1].startswith("ip:old") for k in deps._buckets)
        assert ("probe", "ip:10.9.9.9") in deps._buckets
        assert len(deps._buckets) <= 4
    finally:
        deps.reset_rate_limits()


def test_rate_limit_still_blocks_over_limit():
    from app.api import deps

    deps.reset_rate_limits()
    try:
        deps.rate_limit(_req("10.5.5.5"), "tiny", 2)
        deps.rate_limit(_req("10.5.5.5"), "tiny", 2)
        with pytest.raises(HTTPException) as exc:
            deps.rate_limit(_req("10.5.5.5"), "tiny", 2)
        assert exc.value.status_code == 429
    finally:
        deps.reset_rate_limits()


# ── 5. 机器人令牌：非 ASCII 不得 500 ────────────────────────────────────────
def _bot_request(raw_token: bytes) -> Request:
    return Request({
        "type": "http", "method": "GET", "path": "/api/v1/bot/answer",
        "headers": [(b"x-bot-token", raw_token)],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80),
        "scheme": "http", "query_string": b"q=ak80",
    })


def test_bot_non_ascii_token_is_401_not_500():
    from app.api.routes.bot import _auth

    with pytest.raises(HTTPException) as exc:
        _auth(_bot_request("令牌".encode("utf-8")), None)
    assert exc.value.status_code in (401, 403)


def test_bot_non_ascii_token_via_http_is_401_not_500(client):
    r = client.get("/api/v1/bot/answer", params={"q": "ak80"},
                   headers={"X-Bot-Token": "令牌".encode("utf-8")})
    assert r.status_code in (401, 403), r.text


def test_bot_correct_token_still_works(client):
    r = client.get("/api/v1/bot/answer", params={"q": "ak80"},
                   headers={"X-Bot-Token": "test-bot-token"})
    assert r.status_code == 200, r.text

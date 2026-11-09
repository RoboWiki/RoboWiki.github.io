"""方案复现记录。

与部件评分分开：评分问「值不值」，复现问「装不装得出来」。
这里钉四条：
  · 三态之外的值必须被拒（不能出现 4 星这种中间态）
  · 一人一方案只有一条，重复提交是改结论
  · 聚合按三态计数，total 自洽
  · 未登录可读，但不能写
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import uuid

_TMP = tempfile.mkdtemp(prefix="robowiki-repro-")
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


def register(c: TestClient, handle: str) -> dict:
    r = c.post("/api/auth/register", json={
        "email": f"{handle}@example.com",
        "handle": handle,
        "password": "Passw0rd!123",
        "display_name": handle,
    })
    assert r.status_code in (200, 201), r.text
    # 只读门禁：邮箱账号需验证后才能写；这里直接置位，避免依赖 SMTP。
    from app.core.db import session
    from app.models import User
    from sqlmodel import select
    with session() as db:
        u = db.exec(select(User).where(User.handle == handle)).first()
        if u is not None:
            u.email_verified = True
            db.add(u)
            db.commit()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_three_states_only_and_one_row_per_user(client):
    build = f"build-{uuid.uuid4().hex[:8]}"
    alice = register(client, f"alice{uuid.uuid4().hex[:6]}")
    bob = register(client, f"bob{uuid.uuid4().hex[:6]}")

    # 未登录可读
    empty = client.get(f"/api/reproductions/{build}")
    assert empty.status_code == 200
    assert empty.json()["total"] == 0 and empty.json()["mine"] is None

    # 未登录不能写
    assert client.post(f"/api/reproductions/{build}",
                       json={"outcome": "success"}).status_code == 401

    r = client.post(f"/api/reproductions/{build}", headers=alice,
                    json={"outcome": "success", "note": "四轮能跑"})
    assert r.status_code == 201, r.text
    assert r.json()["total"] == 1 and r.json()["success"] == 1 and r.json()["created"] is True

    # 同一人再提交：改结论，不新增
    r2 = client.post(f"/api/reproductions/{build}", headers=alice,
                     json={"outcome": "failed", "changes": "换了减速比"})
    assert r2.status_code == 201
    body = r2.json()
    assert body["total"] == 1 and body["failed"] == 1 and body["success"] == 0
    assert body["created"] is False
    assert body["mine"]["changes"] == "换了减速比"

    # 另一个人：partial，聚合自洽
    client.post(f"/api/reproductions/{build}", headers=bob, json={"outcome": "partial"})
    agg = client.get(f"/api/reproductions/{build}").json()
    assert agg["total"] == 2
    assert agg["success"] + agg["partial"] + agg["failed"] == agg["total"]

    # 三态之外一律 422
    bad = client.post(f"/api/reproductions/{build}", headers=alice, json={"outcome": "maybe"})
    assert bad.status_code == 422
    assert client.post(f"/api/reproductions/{build}", headers=alice,
                       json={"outcome": "success", "note": "x" * 501}).status_code == 422

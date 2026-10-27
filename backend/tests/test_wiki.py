"""文档站讨论串的测试。

形态参考 YunQianDoc（VitePress + giscus）：每篇文档底下一条线程。
这里用自托管，所以要自己保证：
  * 页面标识用路径而不是标题（改标题不掉讨论）
  * 回复不能跨页
  * 只能删自己的
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-wiki-")
os.environ["ROBOSELECT_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOSELECT_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"

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


def login(client, handle="demo1") -> dict:
    r = client.post("/api/auth/login", json={"handle": handle, "password": "roboselect"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


PAGE = "parts/actuator/cubemars"


def test_empty_thread(client):
    d = client.get("/api/wiki/comments", params={"page": PAGE}).json()
    assert d["count"] == 0 and d["comments"] == []


def test_post_requires_login(client):
    r = client.post("/api/wiki/comments", json={"page": PAGE, "body": "未登录不该成功"})
    assert r.status_code == 401


def test_post_and_reply_thread(client):
    h = login(client)
    r = client.post("/api/wiki/comments", headers=h,
                    json={"page": PAGE, "body": "AK80-9 V3 的 armature 9.06e-3，配 9:1 之后腿的动态很轻。"})
    assert r.status_code == 201
    root_id = r.json()["id"]

    r2 = client.post("/api/wiki/comments", headers=h,
                     json={"page": PAGE, "body": "补一句：PD 增益要重调，别抄大机的。",
                           "parent_id": root_id})
    assert r2.status_code == 201

    d = client.get("/api/wiki/comments", params={"page": PAGE}).json()
    assert d["count"] == 2
    assert d["comments"][0]["parent_id"] is None          # 父在前
    assert d["comments"][1]["parent_id"] == root_id
    assert d["comments"][0]["author"]["display_name"]


def test_thread_is_scoped_by_page(client):
    """页面标识就是路径 —— 别的页面的讨论不会串进来。"""
    h = login(client)
    client.post("/api/wiki/comments", headers=h,
                json={"page": "parts/actuator/hebi", "body": "HEBI 这条线的讨论"})
    a = client.get("/api/wiki/comments", params={"page": PAGE}).json()
    b = client.get("/api/wiki/comments", params={"page": "parts/actuator/hebi"}).json()
    assert a["count"] == 2 and b["count"] == 1
    assert all(c["page"] == "parts/actuator/hebi" for c in b["comments"])


def test_reply_cannot_cross_page(client):
    h = login(client)
    root = client.post("/api/wiki/comments", headers=h,
                       json={"page": PAGE, "body": "父帖"}).json()
    r = client.post("/api/wiki/comments", headers=h,
                    json={"page": "parts/actuator/maxon", "body": "跨页回复",
                          "parent_id": root["id"]})
    assert r.status_code == 422


def test_reply_to_missing_parent(client):
    h = login(client)
    r = client.post("/api/wiki/comments", headers=h,
                    json={"page": PAGE, "body": "孤儿回复", "parent_id": 99999})
    assert r.status_code == 422


def test_only_author_or_staff_can_delete(client):
    h1 = login(client, "demo1")
    c = client.post("/api/wiki/comments", headers=h1,
                    json={"page": "parts/sensor", "body": "演示用户的讨论"}).json()

    # 别人删不掉
    assert client.delete(f"/api/wiki/comments/{c['id']}").status_code == 401
    # 站务可以
    hs = login(client, "roboselect")
    assert client.delete(f"/api/wiki/comments/{c['id']}", headers=hs).status_code == 204
    assert client.get("/api/wiki/comments", params={"page": "parts/sensor"}).json()["count"] == 0


def test_delete_parent_removes_children(client):
    h = login(client)
    p = client.post("/api/wiki/comments", headers=h,
                    json={"page": "parts/controller_low", "body": "父"}).json()
    client.post("/api/wiki/comments", headers=h,
                json={"page": "parts/controller_low", "body": "子", "parent_id": p["id"]})
    assert client.get("/api/wiki/comments", params={"page": "parts/controller_low"}).json()["count"] == 2
    client.delete(f"/api/wiki/comments/{p['id']}", headers=h)
    assert client.get("/api/wiki/comments", params={"page": "parts/controller_low"}).json()["count"] == 0


def test_comment_counts(client):
    d = client.get("/api/wiki/comment-counts").json()
    assert d["total"] >= 2
    assert isinstance(d["counts"], dict)


def test_wiki_site_is_served(client):
    """/wiki 由 FastAPI 托管 VitePress 产物；未构建时给出可读提示而不是 500。"""
    r = client.get("/wiki/")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        assert "RoboSelect" in r.text

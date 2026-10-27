"""评分的测试。

要点：
  · 没评过返回 count=0 且 avg=None（不是 0 分 —— 0 分是差评）
  · 一人一票：再提交是**改分**，不是加一条
  · 分布要一起返回（只看均分会把「5 人 5 分」和「1 人 5 分 + 4 人 1 分」看成一样）
  · min_count 门槛：1 票的 5.0 不该压过 20 票的 4.6
"""
from __future__ import annotations

import os
import pathlib
import shutil
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-rate-")
os.environ["ROBOSELECT_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOSELECT_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PART = "达妙-dm-dm-j4340-2ec-v1-1"
PART2 = "灵足-robstride-rs04"


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


def login(c, handle="demo1") -> dict:
    r = c.post("/api/auth/login", json={"handle": handle, "password": "roboselect"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_unrated_returns_null_not_zero(client):
    d = client.get(f"/api/ratings/{PART}").json()
    assert d["count"] == 0
    assert d["avg"] is None, "没评过不等于 0 分"
    assert d["histogram"] == {str(i): 0 for i in range(1, 6)}


def test_requires_login(client):
    assert client.post(f"/api/ratings/{PART}", json={"score": 5}).status_code == 401


def test_score_range_validated(client):
    h = login(client)
    assert client.post(f"/api/ratings/{PART}", headers=h, json={"score": 0}).status_code == 422
    assert client.post(f"/api/ratings/{PART}", headers=h, json={"score": 6}).status_code == 422


def test_unknown_part_404(client):
    h = login(client)
    assert client.post("/api/ratings/no-such", headers=h, json={"score": 5}).status_code == 404


def test_rate_then_change_is_same_vote(client):
    h = login(client)
    r1 = client.post(f"/api/ratings/{PART}", headers=h,
                     json={"score": 4, "own_hardware": True, "note": "装过机"})
    assert r1.status_code == 201 and r1.json()["created"] is True
    assert r1.json()["count"] == 1 and r1.json()["avg"] == 4.0
    assert r1.json()["own_hardware_count"] == 1

    # 再投一次是改分，不是加票
    r2 = client.post(f"/api/ratings/{PART}", headers=h,
                     json={"score": 2, "own_hardware": False})
    assert r2.json()["created"] is False
    assert r2.json()["count"] == 1, "同一人不该变成两票"
    assert r2.json()["avg"] == 2.0
    assert r2.json()["mine"]["score"] == 2


def test_histogram_and_avg_across_users(client):
    h1 = login(client, "demo1")
    h2 = login(client, "roboselect")
    client.post(f"/api/ratings/{PART2}", headers=h1, json={"score": 5, "own_hardware": True})
    client.post(f"/api/ratings/{PART2}", headers=h2, json={"score": 2, "own_hardware": False})

    d = client.get(f"/api/ratings/{PART2}").json()
    assert d["count"] == 2
    assert d["avg"] == 3.5
    assert d["histogram"]["5"] == 1 and d["histogram"]["2"] == 1
    assert d["own_hardware_count"] == 1, "装机票要单独统计"


def test_mine_visible_only_when_logged_in(client):
    h = login(client, "demo1")
    anon = client.get(f"/api/ratings/{PART2}").json()
    assert anon["mine"] is None
    authed = client.get(f"/api/ratings/{PART2}", headers=h).json()
    assert authed["mine"]["score"] == 5


def test_summary_covers_all_parts(client):
    d = client.get("/api/ratings/summary").json()
    assert d["total_ratings"] >= 2
    assert PART in d["parts"] and PART2 in d["parts"]
    assert d["parts"][PART2]["avg"] == 3.5


def test_top_rated_respects_min_count(client):
    # 只有 1 票的件，在 min_count=2 时不该出现
    d1 = client.get("/api/ratings", params={"min_count": 1}).json()
    d2 = client.get("/api/ratings", params={"min_count": 2}).json()
    assert d1["total"] >= 2
    assert all(i["count"] >= 2 for i in d2["items"])
    assert d1["total"] > d2["total"]


def test_delete_rating(client):
    h = login(client, "demo1")
    assert client.delete(f"/api/ratings/{PART2}", headers=h).status_code == 204
    d = client.get(f"/api/ratings/{PART2}").json()
    assert d["count"] == 1
    assert client.delete(f"/api/ratings/{PART2}", headers=h).status_code == 404

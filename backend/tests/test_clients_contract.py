"""小程序/静态站客户端契约：字段、分页、canonical 路径、公开读权限。

这些接口是小程序壳的底线契约；改字段前先改这里，避免「页面能跑、链接 404」。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-clients-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"
os.environ["ROBOWIKI_BOT_TOKEN"] = "test-bot-token"

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


@pytest.fixture(scope="module", autouse=True)
def _clean_ratings(client):
    """契约测试要求“未评分”是真空：清掉其它模块留下的评分。"""
    from sqlmodel import delete
    from app.core.db import session
    from app.models import Rating
    with session() as db:
        db.exec(delete(Rating))
        db.commit()
    yield


def test_meta_exposes_site_url_and_version(client):
    d = client.get("/api/v1/meta").json()
    assert d["site_url"].startswith("https://")
    assert d["data_version"]


def test_part_list_has_share_fields_and_compact_shape(client):
    d = client.get("/api/v1/parts", params={"limit": 5, "compact": "true"}).json()
    assert d["site_url"] and d["data_version"]
    assert d["items"]
    item = d["items"][0]
    assert "specs" not in item
    assert "rating_count" in item and "rating_avg" in item
    assert 0 < len(item["key_specs"]) <= 3
    assert all(x.get("label") and x.get("value") for x in item["key_specs"])
    assert item["web_path"].startswith("/parts/")
    assert item["web_path"].endswith(".html")
    assert item["web_path"].count(".html") == 1


def test_part_detail_has_site_url_and_version(client):
    first = client.get("/api/v1/parts", params={"limit": 1}).json()["items"][0]
    d = client.get(f"/api/v1/parts/{first['id']}", params={
        "posts_kind": "review", "posts_limit": 3}).json()
    assert d["site_url"] and d["data_version"]
    assert d["web_path"] == first["web_path"]
    assert len(d["posts"]) <= 3


def test_material_list_and_detail_have_web_path(client):
    rows = client.get("/api/v1/materials", params={"limit": 5}).json()
    assert rows["site_url"] and rows["data_version"]
    assert rows["items"]
    first = rows["items"][0]
    assert first["web_path"].startswith("/materials/")
    assert first["web_path"].endswith(".html")

    detail = client.get(f"/api/v1/materials/{first['id']}").json()
    assert detail["web_path"] == first["web_path"]
    assert detail["site_url"] and detail["data_version"]
    assert all(s.get("name") for s in detail["suppliers"])


def test_material_web_path_matches_category_prefix(client):
    rows = client.get("/api/v1/materials", params={"limit": 200}).json()["items"]
    for r in rows:
        if r["category"] == "process":
            assert "/materials/process-" in r["web_path"]
        else:
            assert "/materials/process-" not in r["web_path"]


def test_part_rating_endpoint_is_public_and_null_when_unrated(client):
    first = client.get("/api/v1/parts", params={"limit": 1}).json()["items"][0]
    d = client.get(f"/api/v1/ratings/{first['id']}").json()
    assert d["count"] == 0
    assert d["avg"] is None


def test_openapi_public_gets_do_not_require_auth(client):
    schema = client.get("/api/openapi.json").json()
    for path in ("/api/v1/parts", "/api/v1/parts/{part_id}",
                 "/api/v1/materials", "/api/v1/materials/{item_id}",
                 "/api/v1/ratings/{part_id}"):
        assert schema["paths"][path]["get"].get("security") == [], path
    assert schema["paths"]["/api/v1/admin/stats"]["get"].get("security"), \
        "后台接口仍必须显示鉴权要求"

"""方案库 / 学习指南只读接口测试。

数据直接来自 `.data` 下的 release 产物（conftest 已设置 ROBOWIKI_DATA_DIR），
不联网、不写库；这里只验证契约形状与 canonical 路径。
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-builds-")
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


def test_builds_list(client):
    r = client.get("/api/v1/builds")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] > 0
    assert d["items"], "方案库不应为空"
    assert d["limit"] == 20 and d["offset"] == 0
    for item in d["items"]:
        assert item["id"]
        assert item["web_path"].startswith("/builds/")
        assert item["web_path"].endswith(".html")


def test_build_detail(client):
    first = client.get("/api/v1/builds").json()["items"][0]
    r = client.get(f"/api/v1/builds/{first['id']}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["id"] == first["id"]
    assert d["web_path"] == first["web_path"]
    assert isinstance(d["specs"], dict)


def test_learn_list(client):
    r = client.get("/api/v1/learn")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["total"] > 0
    assert d["items"], "学习指南不应为空"
    for item in d["items"]:
        assert item["slug"]
        assert item["web_path"] == f"/learn/{item['slug']}.html"


def test_unknown_build_404(client):
    r = client.get("/api/v1/builds/no-such-build")
    assert r.status_code == 404
    assert r.json()["detail"] == "方案不存在"

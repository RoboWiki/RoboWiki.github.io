"""口径端点、MCP、整机报价口径的测试。

单独一个文件，避免和 test_api.py 的 module 级环境变量互相干扰。
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-mcp-")
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
    shutil.rmtree(_TMP, ignore_errors=True)


def _rpc(c, method, params=None, rid=1):
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": rid, "method": method,
                             "params": params or {}})
    assert r.status_code == 200
    return r.json()


def _tool(c, name, args=None):
    body = _rpc(c, "tools/call", {"name": name, "arguments": args or {}})
    assert "result" in body, body
    res = body["result"]
    assert res["isError"] is False, res
    return json.loads(res["content"][0]["text"])


# ── 口径端点 ────────────────────────────────────────────────────────────────
def test_semantics_shape(client):
    d = client.get("/api/semantics").json()
    assert "tau_basis" in d["fields"]
    assert d["fields"]["inertia_basis"]["enum"] == ["rotor", "output"]
    ids = {r["id"] for r in d["red_lines"]}
    assert {"RL-01", "RL-02"} <= ids
    # 量纲互逆那条必须在换算里显式告警
    sec = next(c for c in d["conversions"] if c["from"] == "sec/60deg")
    assert "warning" in sec
    assert d["trinary"]["values"] == ["yes", "no", "unknown"]
    assert d["comparability"][0]["grade"] == "A"


def test_semantics_field_directions(client):
    d = client.get("/api/semantics").json()["fields"]
    assert d["mass_kg"]["higher_is_better"] is False
    assert d["tau_peak_Nm"]["higher_is_better"] is True
    # armature 不判优劣：太小也会让控制不稳
    assert d["armature_kgm2"]["higher_is_better"] is None


# ── MCP ─────────────────────────────────────────────────────────────────────
def test_mcp_manifest(client):
    m = client.get("/mcp").json()
    assert m["name"] == "robowiki"
    assert m["transport"] == "streamable-http"
    names = {t["name"] for t in m["tools"]}
    assert {"search_components", "get_component_detail",
            "compare_components", "get_parameter_semantics"} <= names
    assert "none" in m["authentication"]          # 只读免鉴权
    for t in m["tools"]:
        assert t["inputSchema"]["type"] == "object"


def test_mcp_initialize_and_list(client):
    r = _rpc(client, "initialize", {"protocolVersion": "2025-06-18"})
    assert r["result"]["serverInfo"]["name"] == "robowiki"
    assert "tools" in r["result"]["capabilities"]
    assert r["result"]["protocolVersion"]

    r = _rpc(client, "tools/list", rid=2)
    assert len(r["result"]["tools"]) == 4

    assert _rpc(client, "ping", rid=3)["result"] == {}


def test_mcp_unknown_method_and_tool(client):
    r = _rpc(client, "nope/method")
    assert r["error"]["code"] == -32601
    r = _rpc(client, "tools/call", {"name": "delete_everything", "arguments": {}})
    assert r["error"]["code"] == -32601


def test_mcp_search(client):
    d = _tool(client, "search_components", {"q": "J4340", "limit": 5})
    assert d["total"] >= 1
    assert all("id" in i for i in d["items"])
    assert "null 表示未公布" in d["hint"]


def test_mcp_detail_and_missing(client):
    d = _tool(client, "get_component_detail", {"id": "达妙-dm-dm-j4340-2ec-v1-1"})
    assert d["id"] == "达妙-dm-dm-j4340-2ec-v1-1"
    assert d["derived"]["torque_density_Nm_per_kg"] > 0
    assert "armature_ok" in d["derived"]

    miss = _tool(client, "get_component_detail", {"id": "no-such"})
    assert miss == {"error": "not_found", "id": "no-such"}


def test_mcp_compare(client):
    d = _tool(client, "compare_components",
              {"ids": ["达妙-dm-dm-j4340-2ec-v1-1", "灵足-robstride-rs04"]})
    assert set(d["table"]) == {"达妙-dm-dm-j4340-2ec-v1-1", "灵足-robstride-rs04"}
    assert "missing_means" in d
    # 一个不存在的 id 会单独标错，不拖垮其它
    d = _tool(client, "compare_components",
              {"ids": ["达妙-dm-dm-j4340-2ec-v1-1", "no-such"]})
    assert d["table"]["no-such"]["error"] == "not_found"


def test_mcp_semantics(client):
    d = _tool(client, "get_parameter_semantics")
    assert len(d["red_lines"]) >= 6
    assert d["trinary"]["values"] == ["yes", "no", "unknown"]


def test_mcp_rejects_bad_json(client):
    r = client.post("/mcp", content=b"not json",
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 200
    assert r.json()["error"]["code"] == -32700


# ── 整机报价口径 ────────────────────────────────────────────────────────────
def test_build_price_requires_scope(client):
    tok = client.post("/api/auth/login",
                      json={"handle": "demo1", "password": "robowiki"}).json()
    h = {"Authorization": f"Bearer {tok['access_token']}"}

    r = client.post("/api/posts", headers=h, json={
        "kind": "build", "title": "没写覆盖范围的整机", "body": "x" * 20,
        "total_price_cny": 30000})
    assert r.status_code == 422
    assert "覆盖范围" in r.json()["detail"]

    r = client.post("/api/posts", headers=h, json={
        "kind": "build", "title": "写了覆盖范围的整机", "body": "x" * 20,
        "total_price_cny": 30000,
        "price_scope": "12 个关节 + 上位机；结构件与电池另计",
        "price_verified": False})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["total_price_cny"] == 30000
    assert body["price_verified"] is False

    # 没有价格的 build 不需要 scope
    r = client.post("/api/posts", headers=h, json={
        "kind": "build", "title": "没报价的整机方案", "body": "x" * 20})
    assert r.status_code == 201

# ── MCP 的只读边界 ──────────────────────────────────────────────────────────
def test_mcp_only_exposes_read_only_tools(client):
    """Agent 只能查、不能写：工具清单是封闭的，任何写操作都没有入口。"""
    from app.api.routes.mcp import HANDLERS

    listed = [t["name"] for t in _rpc(client, "tools/list")["result"]["tools"]]
    assert sorted(listed) == sorted(HANDLERS), "tools/list 必须与已注册处理器同集合"
    assert set(listed) == {"search_components", "get_component_detail",
                           "compare_components", "get_parameter_semantics"}

    before = client.get("/api/v1/posts", params={"limit": 1}).json()["total"]
    for bad in ("create_post", "vote", "submit_patch", "delete_part",
                "update_part", "report_content", "mark_read"):
        r = _rpc(client, "tools/call", {"name": bad, "arguments": {}})
        assert r["error"]["code"] == -32601, f"{bad} 不该存在"
    # 非 JSON-RPC 的写方法（MCP 里的 resources / prompts / sampling 等）也不接
    for method in ("tools/write", "resources/list", "resources/read",
                   "prompts/list", "sampling/createMessage"):
        assert _rpc(client, method)["error"]["code"] == -32601, method

    after = client.get("/api/v1/posts", params={"limit": 1}).json()["total"]
    assert after == before, "只读端点不能改变任何数据"


def test_mcp_is_anonymous_and_sets_no_cookie(client):
    """免鉴权、无状态：不带 Authorization 也能用，响应不种 cookie。"""
    r = client.get("/mcp")
    assert r.status_code == 200
    assert "set-cookie" not in {k.lower() for k in r.headers}

    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1,
                                  "method": "initialize", "params": {}})
    assert r.status_code == 200
    assert "set-cookie" not in {k.lower() for k in r.headers}
    assert r.json()["result"]["capabilities"]["tools"]["listChanged"] is False

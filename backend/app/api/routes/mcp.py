"""MCP 端点：让 AI Agent 直接查选型数据。

形态参考 roboparts.cc/mcp（`GET` 返回清单、只读、免鉴权）。
这里实现最小可用集：initialize / tools/list / tools/call，四个只读工具。

    GET  /mcp   -> 服务清单与工具列表
    POST /mcp   -> JSON-RPC 2.0

刻意保持只读：Agent 可以查、可以比，但不能替你发帖或投票。
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import func
from sqlmodel import select

from ...crud import posts_out
from ...models import Part, Post
from ..deps import Db
from .catalog import part_out
from .semantics import (COMPARABILITY, CONVERSIONS, FIELD_SEMANTICS, RED_LINES,
                        SUPPLIER_QUESTIONS, TRINARY)

router = APIRouter(tags=["mcp"])

SERVER_INFO = {"name": "roboselect", "version": "0.2.0"}
PROTOCOL_VERSIONS = ["2025-06-18", "2025-03-26", "2024-11-05"]

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_components",
        "description": "按关键词/品类搜索四足机器人零部件（关节电机、上位机、下位机、传感器）。"
                       "返回摘要：id/model/vendor/关键规格/source_tier。"
                       "库存数字不写死在描述里，请读返回的 total。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "q": {"type": "string", "description": "关键词，可为空"},
                "category": {"type": "string",
                             "enum": ["actuator", "controller_high", "controller_low", "sensor"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
        },
    },
    {
        "name": "get_component_detail",
        "description": "按 id 取单个零件的全字段，含 source_tier / verified / last_checked、"
                       "派生量（扭矩密度、峰值额定比、armature 复算）与该件的用户评价。"
                       "决策前用它核对证据强度。",
        "inputSchema": {
            "type": "object", "required": ["id"],
            "properties": {"id": {"type": "string"}},
        },
    },
    {
        "name": "compare_components",
        "description": "并排对比 2–6 个零件的关键参数。缺失字段以 null 呈现，"
                       "**null 表示未公布，不等于不支持该特性**。",
        "inputSchema": {
            "type": "object", "required": ["ids"],
            "properties": {"ids": {"type": "array", "items": {"type": "string"},
                                   "minItems": 2, "maxItems": 6}},
        },
    },
    {
        "name": "get_parameter_semantics",
        "description": "获取参数口径规范：字段语义、物理红线（扭矩密度、峰值/额定比等）、"
                       "单位换算、可比性分级、向厂商问询清单。"
                       "用于判断两份参数表到底能不能直接比较——本平台的核心纪律。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def manifest() -> dict:
    return {
        "name": "roboselect",
        "version": SERVER_INFO["version"],
        "transport": "streamable-http",
        "endpoint": "/mcp",
        "protocol_versions": PROTOCOL_VERSIONS,
        "authentication": "none — 只读、免鉴权、不设 cookie、不存储调用方数据",
        "tools": TOOLS,
        "dataset": {
            "parts": "GET /api/parts",
            "semantics": "GET /api/semantics",
            "posts": "GET /api/posts",
        },
        "note": "只读端点。Agent 可以查、可以比，不能替你发帖或投票。",
    }


@router.get("/mcp")
def mcp_manifest():
    return manifest()


# ── 工具实现 ────────────────────────────────────────────────────────────────
def _tool_search(db, args: dict) -> str:
    q = (args.get("q") or "").strip().lower()
    cat = args.get("category")
    limit = max(1, min(50, int(args.get("limit") or 10)))
    stmt = select(Part)
    if cat:
        stmt = stmt.where(Part.category == cat)
    if q:
        stmt = stmt.where(Part.search.contains(q))
    total = db.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = db.exec(stmt.order_by(Part.vendor, Part.model).limit(limit)).all()
    out = {
        "total": int(total),
        "returned": len(rows),
        "items": [{
            "id": p.id, "model": p.model, "vendor": p.vendor,
            "category": p.category, "subtype": p.subtype,
            "tau_peak_Nm": p.specs.get("tau_peak_Nm"),
            "gear": p.specs.get("gear"),
            "mass_kg": p.specs.get("mass_kg"),
            "armature_kgm2": p.specs.get("armature_kgm2"),
            "source_tier": p.source_tier, "verified": p.verified,
        } for p in rows],
        "hint": "null 表示未公布，不等于不支持；跨厂商比较前请调用 get_parameter_semantics",
    }
    return json.dumps(out, ensure_ascii=False, indent=1)


def _tool_detail(db, args: dict) -> str:
    pid = str(args.get("id") or "")
    p = db.get(Part, pid)
    if p is None:
        return json.dumps({"error": "not_found", "id": pid}, ensure_ascii=False)
    out = part_out(p)
    posts = db.exec(select(Post).where(Post.part_id == pid)
                    .order_by(Post.score.desc()).limit(5)).all()
    # mode="json" 让 datetime 变成 ISO 字符串 —— 否则只要该零件有评价，
    # json.dumps 就会抛 "Object of type datetime is not JSON serializable"，
    # 整个 tools/call 变成 isError。这个 bug 只有「有评价的零件」才触发，
    # 所以是测试跑全量时才暴露出来的。
    out["top_posts"] = [x.model_dump(mode="json") for x in posts_out(db, list(posts))]
    out["evidence_note"] = (
        "source_tier=A 表示逐项核对过官方 datasheet；"
        "null 字段表示未公布；armature_ok=false 说明该行不变量校验未通过")
    return json.dumps(out, ensure_ascii=False, indent=1)


def _tool_compare(db, args: dict) -> str:
    ids = [str(x) for x in (args.get("ids") or [])][:6]
    if len(ids) < 2:
        return json.dumps({"error": "need 2-6 ids"}, ensure_ascii=False)
    rows = db.exec(select(Part).where(Part.id.in_(ids))).all()
    by_id = {p.id: part_out(p) for p in rows}
    keys = ["tau_peak_Nm", "tau_rated_Nm", "gear", "speed_noload_rpm", "mass_kg",
            "rotor_inertia_kgm2", "inertia_basis", "armature_kgm2", "voltage_V",
            "kt_Nm_per_A", "price_cny"]
    table = {}
    for pid in ids:
        p = by_id.get(pid)
        if not p:
            table[pid] = {"error": "not_found"}
            continue
        table[pid] = {k: p["specs"].get(k) for k in keys} | {
            "source_tier": p["source_tier"],
            "derived": {k: v for k, v in p["derived"].items()},
        }
    return json.dumps({
        "table": table,
        "missing_means": "null = 未公布，不代表不支持",
        "comparability": "跨厂商比较前先读 get_parameter_semantics；等级 C 以下不可直接比",
    }, ensure_ascii=False, indent=1)


def _tool_semantics(db, args: dict) -> str:
    return json.dumps({
        "fields": FIELD_SEMANTICS,
        "red_lines": RED_LINES,
        "conversions": CONVERSIONS,
        "comparability": COMPARABILITY,
        "supplier_questions": SUPPLIER_QUESTIONS,
        "trinary": TRINARY,
    }, ensure_ascii=False, indent=1)


HANDLERS = {
    "search_components": _tool_search,
    "get_component_detail": _tool_detail,
    "compare_components": _tool_compare,
    "get_parameter_semantics": _tool_semantics,
}


@router.post("/mcp")
async def mcp_rpc(request: Request, db: Db):
    """最小 JSON-RPC 2.0：initialize / tools/list / tools/call / ping。"""
    try:
        body = await request.json()
    except Exception:
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32700, "message": "invalid JSON"}}

    rid = body.get("id")
    method = body.get("method")
    params = body.get("params") or {}

    def ok(result):
        return {"jsonrpc": "2.0", "id": rid, "result": result}

    def err(code, msg):
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}

    if method == "initialize":
        return ok({
            "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": "只读数据端点。查零件用 search_components，"
                            "比参数前先调 get_parameter_semantics 确认口径。",
        })
    if method in ("notifications/initialized", "initialized"):
        return ok({})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        fn = HANDLERS.get(name)
        if fn is None:
            return err(-32601, f"unknown tool: {name}")
        try:
            text = fn(db, params.get("arguments") or {})
        except Exception as exc:                       # noqa: BLE001
            return ok({"content": [{"type": "text", "text": f"tool error: {exc}"}],
                       "isError": True})
        return ok({"content": [{"type": "text", "text": text}], "isError": False})

    return err(-32601, f"unknown method: {method}")

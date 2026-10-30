"""数据治理的三条硬规则（P0 落地后固定成测试，防止回退）。"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,63}$")


def _all_rows() -> list[dict]:
    rows = []
    for f in sorted((ROOT / "data" / "catalog").glob("*/*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))
    for f in sorted((ROOT / "data" / "robots").glob("*.json")):
        rows += json.loads(f.read_text(encoding="utf-8"))
    sw = ROOT / "data" / "software.json"
    if sw.exists():
        for it in json.loads(sw.read_text(encoding="utf-8")).get("items", []):
            rows.append({"id": f"software:{it['id']}", "specs": {}})
    return rows


def test_ids_are_registered_and_stable():
    reg = json.loads((ROOT / "data" / "_id_registry.json").read_text(encoding="utf-8"))["ids"]
    cur = {r["id"] for r in _all_rows()}
    assert not (cur - set(reg)), f"未登记的 id：{sorted(cur - set(reg))[:5]}"
    gone = [i for i in set(reg) - cur if not reg[i].get("removed")]
    assert not gone, f"注册表里的 id 消失了（改名/删除要留 tombstone）：{gone[:5]}"


def test_new_ids_are_ascii():
    reg = json.loads((ROOT / "data" / "_id_registry.json").read_text(encoding="utf-8"))["ids"]
    bad = [i for i in reg if not reg[i].get("legacy") and not ID_RE.match(i.split(":")[-1])]
    assert not bad, f"非 ASCII 的 id：{bad[:5]}"


def test_semantics_json_is_single_source():
    sm = json.loads((ROOT / "schema" / "semantics.json").read_text(encoding="utf-8"))
    for k in ("version", "field_semantics", "red_lines", "conversions",
              "comparability", "supplier_questions", "trinary"):
        assert k in sm, f"semantics.json 缺 {k}"
    # 静态站不能再 import 后端（拆仓前提）
    site = (ROOT / "pipeline" / "build_site.py").read_text(encoding="utf-8")
    assert "app.api.routes.semantics" not in site, "pipeline 不能 import 后端"
    assert "semantics.json" in site, "pipeline 应读 schema/semantics.json"


def test_every_image_has_provenance():
    bad = [r["id"] for r in _all_rows()
           if (r.get("specs") or {}).get("image_url")
           and not (r.get("specs") or {}).get("image_source")]
    assert not bad, f"有图但没写出处：{bad[:5]}"

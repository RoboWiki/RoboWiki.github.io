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
    # 供应商与协议也有永久 id（见 docs/ID-POLICY.md）——不读进来就会被当成「注册表里的 id 消失了」
    sp = ROOT / "data" / "suppliers.json"
    if sp.exists():
        for it in json.loads(sp.read_text(encoding="utf-8")):
            if it.get("id"):
                rows.append({"id": f"supplier:{it['id']}", "specs": {}})
    pr = ROOT / "data" / "protocols.json"
    if pr.exists():
        pr_data = json.loads(pr.read_text(encoding="utf-8"))
        # 结构可能是 {"protocols": [...]} 也可能直接是 list —— 先读再判断
        if isinstance(pr_data, dict):
            pr_rows = pr_data.get("protocols") or []
        else:
            pr_rows = pr_data if isinstance(pr_data, list) else []
        for it in pr_rows:
            if isinstance(it, dict) and it.get("id"):
                rows.append({"id": f"protocol:{it['id']}", "specs": {}})
    return rows


def test_ids_are_registered_and_stable():
    reg = json.loads((ROOT / "data" / "_id_registry.json").read_text(encoding="utf-8"))["ids"]
    cur = {r["id"] for r in _all_rows()}
    assert not (cur - set(reg)), f"未登记的 id：{sorted(cur - set(reg))[:5]}"
    # 出口只有两个：改名（alias_of）与删除（removed），条目不真删
    gone = [i for i in set(reg) - cur
            if not reg[i].get("removed") and not reg[i].get("alias_of")]
    assert not gone, f"注册表里的 id 消失了（改名/删除要留 tombstone）：{gone[:5]}"


def test_new_ids_are_ascii():
    reg = json.loads((ROOT / "data" / "_id_registry.json").read_text(encoding="utf-8"))["ids"]
    bad = [i for i in reg if not reg[i].get("legacy") and not ID_RE.match(i.split(":")[-1])]
    assert not bad, f"非 ASCII 的 id：{bad[:5]}"


def test_registry_has_no_duplicate_targets():
    """alias 指向必须落在册内：否则「旧 id → 新 id」这一跳是断的，改名等于删除。"""
    reg = json.loads((ROOT / "data" / "_id_registry.json").read_text(encoding="utf-8"))["ids"]
    dangling = {i: m["alias_of"] for i, m in reg.items()
                if m.get("alias_of") and m["alias_of"] not in reg}
    assert not dangling, f"alias_of 指向了不存在的 id：{dangling}"
    self_ref = [i for i, m in reg.items() if m.get("alias_of") == i]
    assert not self_ref, f"alias_of 指向自己：{self_ref}"


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

"""品类 / 品牌的单一真相源：data/taxonomy.json。

为什么要有这些测试：
    改一个品类名，站点导航、部件库筛选、后端标签、schema 校验、URL slug
    五处都得跟着变 —— 漏一处就是「页面上叫深度相机，排序里叫 camera」这种
    难查的错。这里把「一处定义、处处一致」变成机器可检查的事。
"""
from __future__ import annotations

import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.load import (  # noqa: E402
    cat_labels, load_parts, load_taxonomy, vendor_slug,
)


def test_taxonomy_categories_match_schema_enum():
    """注册表的品类 == schema 允许的品类。两者不一致时，闸门和表单会各说各话。"""
    tax = {c["id"] for c in load_taxonomy()["categories"]}
    enum = set(json.loads(
        (ROOT / "schema" / "part.schema.json").read_text(encoding="utf-8")
    )["properties"]["category"]["enum"])
    assert tax == enum, f"只在注册表: {tax - enum}；只在 schema: {enum - tax}"


def test_categories_have_names_and_unique_ids():
    cats = cat_labels()
    assert cats, "注册表里没有品类"
    ids = [c[0] for c in cats]
    assert len(ids) == len(set(ids)), "品类 id 重复"
    for cid, name, hint in cats:
        assert name, f"{cid} 缺展示名"
        # IMU / ToF 这类通用缩写就是对的展示名，不该被当成「没翻译」；
        # 真正要拦的是「展示名 == 内部 id」（说明漏了中文名）
        assert name.lower() != cid.lower() or name != cid, f"{cid} 的展示名和 id 一样"
        assert len(name) <= 12, f"{cid} 的展示名太长，导航会挤：{name}"
        assert isinstance(hint, str), f"{cid} 的 hint 必须是字符串"


def test_every_part_category_is_registered():
    known = {c["id"] for c in load_taxonomy()["categories"]}
    bad = sorted({p["category"] for p in load_parts()} - known)
    assert not bad, f"零件的品类没在注册表里登记：{bad}"


def test_every_part_vendor_is_registered():
    """厂商没登记时 slug 会退化成「去掉符号的小写」，文件名就会漂。"""
    known = set((load_taxonomy().get("vendors") or {}).keys())
    bad = sorted({p["vendor"] for p in load_parts()} - known)
    assert not bad, f"厂商没在注册表里登记：{bad}"


def test_vendor_slugs_are_ascii_and_unique():
    vendors = load_taxonomy().get("vendors") or {}
    slugs = [v["slug"] for v in vendors.values()]
    assert len(slugs) == len(set(slugs)), "两个厂商的 slug 撞了，文件会互相覆盖"
    for v, meta in vendors.items():
        assert meta["slug"].isascii(), f"{v} 的 slug 不是 ASCII：{meta['slug']}"
        assert vendor_slug(v) == meta["slug"]


def test_catalog_json_carries_categories():
    """前端不再硬编码品类表，产物里必须带上。"""
    p = ROOT / "wiki" / "docs" / "public" / "catalog.json"
    if not p.exists():
        import pytest
        pytest.skip("先跑 python -m pipeline build")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert [c["id"] for c in d["categories"]] == [c[0] for c in cat_labels()]


def test_featured_ids_exist():
    """精选清单是白名单：里面的 id 必须真实存在，否则按钮显示的件数与实际不符。"""
    import json
    from pipeline.load import load_parts

    feat = json.loads(
        (ROOT / "data" / "featured.json").read_text(encoding="utf-8"))
    ids = set(feat.get("ids") or [])
    have = {r["id"] for r in load_parts()}
    ghost = sorted(ids - have)
    assert not ghost, f"精选清单里有不存在的部件：{ghost}"

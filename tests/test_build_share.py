"""分享 JSON：品类字段、规范链接、版本；以及每页 OG 图与默认图。"""
from __future__ import annotations

import json
import pathlib

from pipeline.build_share import build

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _rows():
    return [
        {
            "id": "amass-xt30", "category": "connector", "vendor": "Amass",
            "model": "XT30", "title": "Amass XT30 大电流连接器",
            "source_tier": "A", "last_checked": "2026-10-31",
            "specs": {"positions": 2, "current_rated_A": 20,
                      "voltage_rated_V": 500, "wire_awg": "AWG 16",
                      "image_url": "/parts/amass-xt30.jpg"},
        },
        {
            "id": "cubemars-ak80-6", "category": "actuator", "vendor": "CubeMars",
            "model": "AK80-6", "title": "CubeMars AK80-6 关节模组",
            "source_tier": "B", "last_checked": "2026-10-31",
            "specs": {"tau_peak_Nm": 12, "tau_rated_Nm": 6, "voltage_V": 48,
                      "mass_kg": 0.485},
        },
    ]


def test_index_carries_canonical_url_and_category_facts(tmp_path):
    slugs = {"amass-xt30": "amass-xt30", "cubemars-ak80-6": "cubemars-ak80-6"}
    n = build(_rows(), slugs, tmp_path, "https://robowiki.org.cn/", "data-v2026.11.0")
    assert n == 2

    idx = json.loads((tmp_path / "public/share/index.json").read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in idx}
    con = by_id["amass-xt30"]
    assert con["url"] == "https://robowiki.org.cn/parts/connector/amass-xt30.html"
    assert "2 pin" in con["summary"] and "20 A" in con["summary"]
    assert "500 V" in con["summary"]

    act = by_id["cubemars-ak80-6"]
    assert "12 N·m" in act["summary"] and "6 N·m" in act["summary"]

    part = json.loads(
        (tmp_path / "public/share/parts/connector/amass-xt30.json").read_text(encoding="utf-8"))
    assert part["canonical_url"] == con["url"]
    assert part["id"] == "amass-xt30"
    assert any(p["label"] == "电流" and "20 A" in p["value"] for p in part["params"])
    # 分享图必须是绝对地址 —— QQ pics / 微信预览都只认绝对 URL。
    assert part["image_url"] == "https://robowiki.org.cn/parts/amass-xt30.jpg"


def test_copy_text_has_model_source_and_data_version(tmp_path):
    """分享文案必须自带型号、来源等级与数据版本 —— 转发到群里后看不清上下文。"""
    slugs = {"amass-xt30": "amass-xt30", "cubemars-ak80-6": "cubemars-ak80-6"}
    build(_rows(), slugs, tmp_path, "https://robowiki.org.cn/", "data-v2026.11.0")
    for slug, cat in (("amass-xt30", "connector"), ("cubemars-ak80-6", "actuator")):
        part = json.loads(
            (tmp_path / f"public/share/parts/{cat}/{slug}.json").read_text(encoding="utf-8"))
        text = part["copy_text"]
        assert part["title"] in text
        assert f"{part['source_tier']} 级来源" in text
        assert "data-v2026.11.0" in text
        assert part["canonical_url"] in text
        if part["last_checked"]:
            assert part["last_checked"] in text


def test_every_index_entry_resolves_to_a_card(tmp_path):
    """索引里的 json 路径必须真的落盘；客户端只读索引找卡片，不能给死链。"""
    slugs = {"amass-xt30": "amass-xt30", "cubemars-ak80-6": "cubemars-ak80-6"}
    build(_rows(), slugs, tmp_path, "https://robowiki.org.cn/", "data-v2026.11.0")
    idx = json.loads((tmp_path / "public/share/index.json").read_text(encoding="utf-8"))
    assert idx
    for row in idx:
        assert row["json"].startswith("/share/")
        card = tmp_path / "public" / row["json"].lstrip("/")
        assert card.is_file(), row["json"]
        payload = json.loads(card.read_text(encoding="utf-8"))
        assert payload["canonical_url"] == row["url"]
        assert payload["data_version"] == row["data_version"]
        assert payload["title"] == row["title"]
        assert payload["copy_text"]


def test_material_share_card_is_self_contained(tmp_path):
    """材质/工艺卡与部件卡同构：标题、参数、来源、版本、规范链接、文案都要有。"""
    from pipeline.build_share import build_materials

    pub = tmp_path / "public"
    rows = [{
        "id": "mat-alu-6061-t6", "category": "material", "name": "6061-T6 铝板",
        "source_tier": "B", "last_checked": "2026-10-31",
        "applications": ["结构件"],
        "specs": {"density_g_cm3": 2.7, "modulus_GPa": 69, "tensile_MPa": 310},
        "_href": "alu-6061-t6",
    }]
    assert build_materials(rows, pub, "https://robowiki.org.cn/", "data-v2026.11.0") == 1
    card = json.loads(
        (pub / "share/materials/alu-6061-t6.json").read_text(encoding="utf-8"))
    assert card["canonical_url"] == "https://robowiki.org.cn/materials/alu-6061-t6.html"
    assert card["summary"].startswith("密度 2.7 g/cm³")
    assert card["params"] and card["data_version"] == "data-v2026.11.0"
    assert "B 级来源" in card["copy_text"]
    assert "data-v2026.11.0" in card["copy_text"]
    assert card["canonical_url"] in card["copy_text"]
    # 材质卡没有产品图；页面 frontmatter 会写默认 OG，ShareBox 用它兜底。
    assert card["image_url"] is None


def test_part_frontmatter_writes_product_image():
    """部件页 frontmatter 必须带产品图，transformHead 才输出这张 og:image。"""
    from pipeline.build_site import part_front

    md = part_front({
        "id": "cubemars-ak80-6", "category": "actuator", "vendor": "CubeMars",
        "model": "AK80-6", "source_tier": "B", "last_checked": "2026-10-31",
        "specs": {"tau_peak_Nm": 12, "mass_kg": 0.485,
                  "image_url": "/parts/cubemars-ak80-6.jpg"},
    })
    assert md.startswith("---\n")
    head = md.split("---", 2)[1]
    assert 'image: "/parts/cubemars-ak80-6.jpg"' in head
    assert "title: CubeMars AK80-6" in head
    assert "description:" in head


def test_part_without_image_uses_default_og():
    """没有实拍图的型号退回默认 OG —— 不能让分享卡指向空图。"""
    from pipeline.build_site import DEFAULT_OG_IMAGE, part_front

    md = part_front({
        "id": "sens-ldrobot-ld14", "category": "lidar", "vendor": "LDROBOT",
        "model": "LD14", "source_tier": "B", "last_checked": "2026-10-31",
        "specs": {"range_m": 8},
    })
    assert f'image: "{DEFAULT_OG_IMAGE}"' in md


def test_material_and_process_frontmatter_use_default_og():
    """材质/工艺页没有产品图，frontmatter 明确写默认 OG（而不是留空）。"""
    from pipeline.build_materials import DEFAULT_OG_IMAGE, _material_page, _process_page

    mat = {
        "id": "mat-alu-6061-t6", "category": "material", "name": "6061-T6 铝板",
        "source_tier": "B", "last_checked": "2026-10-31",
        "specs": {"density_g_cm3": 2.7, "modulus_GPa": 69, "tensile_MPa": 310},
    }
    proc = {
        "id": "proc-fdm", "category": "process", "name": "FDM 3D 打印",
        "source_tier": "B", "last_checked": "2026-10-31",
        "specs": {"tolerance_mm": 0.2, "layer_height_mm": 0.2},
    }
    for md in (_material_page(mat, {}, {}), _process_page(proc, {}, {})):
        head = md.split("---", 2)[1]
        assert f'image: "{DEFAULT_OG_IMAGE}"' in head


def test_config_emits_one_absolute_og_image_per_page():
    """全局 head 不再写 og:image/twitter:image；每页由 transformHead 输出唯一一张。"""
    cfg = (ROOT / "wiki/docs/.vitepress/config.mts").read_text(encoding="utf-8")

    global_head = cfg.split("\n  head: [", 1)[1].split("\n  transformHead", 1)[0]
    # 注释里可以提，但不能再有真正的 meta 条目，否则同页两张 og:image。
    assert "property: 'og:image'" not in global_head
    assert "name: 'twitter:image'" not in global_head
    assert "property: 'og:image:width'" not in global_head
    assert "property: 'og:site_name'" in global_head

    transform = cfg.split("\n  transformHead", 1)[1]
    assert "pageData.frontmatter.image" in transform
    assert "absoluteImage(" in cfg
    assert "['meta', { property: 'og:image', content: image }]" in transform
    assert "['meta', { property: 'og:image:alt', content: imageAlt }]" in transform
    assert "['meta', { name: 'twitter:image', content: image }]" in transform
    # canonical / og:url 保持原样，不被图片逻辑改动。
    assert "['link', { rel: 'canonical', href: url }]" in transform
    assert "['meta', { property: 'og:url', content: url }]" in transform

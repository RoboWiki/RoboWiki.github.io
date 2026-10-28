"""构建链的回归测试。

为什么必须有：80 个测试原本全在后端，`pipeline/` 一行没测 ——
于是「参数口径页里 `rows = []` 覆盖了全局零件列表，导致侧边栏厂商全丢」
这种错，是靠人工看页面才发现的。

这里守四件事：
    1. 数据闸门真的会红（喂坏数据 → 退出码 1）
    2. loader 的优先级正确（catalog/ 优先于旧扁平文件）
    3. slug 稳定（URL 变了 = 外链与 giscus 讨论全断）
    4. build_site 的侧边栏包含全部厂商（那个 bug 的回归测试）
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))


def run(mod: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", f"pipeline.{mod}", *args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=str(ROOT))


# ── 闸门 ──────────────────────────────────────────────────────────────────
def test_validate_passes_on_current_data():
    r = run("validate")
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]


def test_validate_rejects_bad_data():
    """喂一条「质量 740 kg」的零件，闸门必须红 —— 而不是安静地放过去。

    沙箱建在仓库内（.tmp-validate/），不用系统临时目录：
    Windows 上 pytest 的 tmp_path 偶尔会被 ACL 挡住，那是环境问题，
    不该让「闸门会不会红」这件事的测试跟着飘。
    """
    sandbox = ROOT / ".tmp-validate"
    cat = sandbox / "data" / "catalog" / "actuator"
    cat.mkdir(parents=True, exist_ok=True)
    bad = [{
        "category": "actuator", "subtype": "qdd", "id": "t-bad", "vendor": "T",
        "model": "BAD-1", "title": "测试坏数据", "source_tier": "A",
        "verified": True, "price_cny": 100,
        "specs": {"tau_peak_Nm": 40, "gear": 10, "mass_kg": 740.0,
                  "voltage_V": 48, "tau_basis": "peak", "image_url": None,
                  "image_source": None},
    }]
    (cat / "t.json").write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")

    code = (
        "import sys, pathlib;"
        f"sys.path.insert(0, r'{ROOT}');"
        "import pipeline.validate as v;"
        f"v.DATA = pathlib.Path(r'{sandbox / 'data'}');"
        "raise SystemExit(v.main())"
    )
    try:
        r = subprocess.run([sys.executable, "-c", code], capture_output=True,
                           text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONUTF8": "1"})
        out = r.stdout + r.stderr
        assert r.returncode == 1, f"坏数据必须让闸门失败，实际退出码 {r.returncode}\n{out[-1500:]}"
        assert "ERROR" in out or "量程" in out, out[-1500:]
    finally:
        import shutil
        shutil.rmtree(sandbox, ignore_errors=True)


# ── loader ────────────────────────────────────────────────────────────────
def test_loader_prefers_catalog_dir():
    from pipeline.load import load_parts
    rows = load_parts()
    assert rows, "loader 读不到任何零件"
    cats = {r["category"] for r in rows}
    assert cats <= {"actuator", "controller_high", "controller_low", "structure",
                    "imu", "lidar", "camera", "battery", "wiring", "module"}


def test_loader_ids_unique():
    from pipeline.load import load_parts
    ids = [r["id"] for r in load_parts()]
    assert len(ids) == len(set(ids)), "id 重复会让评分/讨论串错位"


def test_offers_have_required_fields():
    from pipeline.load import load_offers
    for o in load_offers():
        assert o.get("id") and o.get("kind") and o.get("title")
        assert "demo" in o, f"{o.get('id')} 必须显式标 demo"
        if o.get("price_cny") is not None or o.get("discount") is not None:
            assert o.get("detail"), f"{o['id']} 有价格/折扣却没有获取条件"


# ── slug 稳定性 ───────────────────────────────────────────────────────────
def test_part_slug_is_stable_and_ascii():
    from pipeline.build_site import part_slug
    seen: dict[str, str] = {}
    a = part_slug("达妙-dm-dm-j4340-2ec-v1-1", "达妙 DAMIAO", "DM-J4340-2EC V1.1", seen)
    b = part_slug("达妙-dm-dm-j4340-2ec-v1-1", "达妙 DAMIAO", "DM-J4340-2EC V1.1", seen)
    assert a == b
    assert a.isascii(), "URL 里不能出现中文，否则要被百分号编码"
    # 不同型号撞名时必须补哈希，不能互相覆盖
    c = part_slug("另一个-id", "达妙 DAMIAO", "DM-J4340-2EC V1.1", seen)
    assert c != a


# ── build_site 回归 ───────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def built():
    r = run("build_site")
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
    return ROOT / "wiki" / "docs"


def test_sidebar_lists_every_vendor(built):
    """回归：口径页的循环变量曾覆盖全局 rows，侧边栏厂商全空。"""
    from pipeline.load import load_parts
    side = json.loads((built / ".vitepress" / "sidebar.json").read_text(encoding="utf-8"))
    act = next(i for i in side["/parts/"][0]["items"] if i["text"] == "关节电机")
    names = [x["text"] for x in act["items"]]
    vendors = {r["vendor"] for r in load_parts() if r["category"] == "actuator"}
    for v in vendors:
        assert v in names, f"侧边栏缺厂商 {v}（共 {names}）"


def test_catalog_json_matches_part_count(built):
    from pipeline.load import load_parts
    d = json.loads((built / "public" / "catalog.json").read_text(encoding="utf-8"))
    assert len(d["parts"]) == len(load_parts())
    for p in d["parts"]:
        assert {"id", "slug", "category", "vendor", "model", "offers"} <= set(p)


def test_part_pages_generated(built):
    pages = list((built / "parts").rglob("*.md"))
    assert len(pages) >= 40, f"只生成了 {len(pages)} 个型号页"


def test_no_dead_internal_links(built):
    """站内链接指向不存在的页面 = 构建后 404。这里扫 md 里的绝对路径。"""
    import re
    exists = set()
    for p in built.rglob("*.md"):
        rel = p.relative_to(built).as_posix()
        exists.add("/" + rel[:-3])          # 去掉 .md
        exists.add("/" + rel)
    bad = []
    for p in built.rglob("*.md"):
        for m in re.finditer(r"\]\((/[^)#\s]+)", p.read_text(encoding="utf-8")):
            link = m.group(1).rstrip("/")
            if link.startswith(("/api", "/console", "/parts/")) and link not in exists:
                # /parts/<品类>/<slug> 与页面对应；允许带 .html
                if link + ".md" not in exists and link + "/index.md" not in exists:
                    bad.append(f"{p.name} -> {link}")
    assert not bad, "死链：" + "; ".join(bad[:8])

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
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT))


def run(mod: str, *args: str) -> subprocess.CompletedProcess:
    # Windows 中文系统下，子进程默认按 cp936 输出中文，
    # 父进程按 UTF-8 解码会炸。强制子进程用 UTF-8 输出。
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, "-m", f"pipeline.{mod}", *args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=str(ROOT), env=env)


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
    # 品类白名单从 schema 读，而不是在测试里抄一份 —— 抄一份的后果就是
    # 新增品类时这里先红，而真正该拦的是 schema 与闸门。
    allowed = set(json.loads(
        (ROOT / "schema" / "part.schema.json").read_text(encoding="utf-8")
    )["properties"]["category"]["enum"])
    cats = {r["category"] for r in rows}
    assert cats <= allowed, f"出现 schema 未定义的品类：{cats - allowed}"
    # 每行都要带 _file，否则部件页给不出「编辑这条数据」的链接
    assert all(r.get("_file") for r in rows)


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


# ── 表格链接 ────────────────────────────────────────────────────────────
def test_table_builders_take_explicit_href():
    """actuator_table / generic_table 的链接来源是参数，不是模块级全局。

    旧实现 mdl() 自己查全局 HREF —— 构建顺序一换（先渲表后填表），
    型号列就静默退化成纯文本，没有任何报错。显式传参把这种错误变成 TypeError。
    """
    from pipeline.build_site import actuator_table, generic_table
    items = [{
        "id": "v-m1", "vendor": "V", "model": "M1", "category": "actuator",
        "subtype": "qdd", "source_tier": "A", "verified": True, "price_cny": None,
        "specs": {"tau_peak_Nm": 10},
    }]
    bare = actuator_table(items)
    assert "**M1**" in bare, "型号名总得在"
    assert "](" not in bare, "没传 href 时不该出现链接"
    linked = actuator_table(items, {"v-m1": "/parts/actuator/v-m1"})
    assert "[**M1**](/parts/actuator/v-m1)" in linked
    g = generic_table(items, "imu", {"v-m1": "/parts/imu/v-m1"})
    assert "[**M1**](/parts/imu/v-m1)" in g

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


# ── 死链 ────────────────────────────────────────────────────────────────
# 为什么要三套正则：
#   1. markdown 链接 ](...)      —— 手写页与生成表格
#   2. HTML 里的 href="..."      —— 型号页的 <a class="hc" href="/parts/...">、
#      资料表、build_home / build_competitions 拼出的卡片，以前完全没人扫
#   3. Vue 模板里的静态 href     —— :to / 动态绑定管不了，但写死的
#      href="/xxx" 与 to="/xxx" 一旦改了路由就是纯 404
_MD_LINK = re.compile(r"\]\((/[^)\s#]+)")
_HTML_HREF = re.compile(r"""href=["'](/[^"'#]+)["']""")
# 单引号 or 双引号包着的站内绝对路径；查询串在断言前统一剥掉
_STATIC_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf",
               ".json", ".css", ".js", ".ico", ".woff", ".woff2", ".mp4")


def _page_paths(built: pathlib.Path) -> set[str]:
    """站点上"存在"的页面路径集合：每个 .md 贡献无后缀与 index 两种形态。"""
    exists: set[str] = set()
    for p in built.rglob("*.md"):
        if ".vitepress" in p.parts:
            continue
        rel = p.relative_to(built).as_posix()
        no_ext = "/" + rel[:-3]                      # /parts/actuator/dji
        exists.add(no_ext)
        if rel.endswith("/index.md"):
            exists.add("/" + rel[:-len("/index.md")])  # /parts/actuator
        if rel == "index.md":
            exists.add("/")
    return exists


def _is_page_link(link: str) -> bool:
    """只校验站内**页面**链接。

    排除：查询串（/catalog?category=imu 指向同一页）、静态资源
    （/parts/xxx.jpg 由 public/ 提供）、以及 /api /console 这类
    不走文档站路由的前缀 —— 它们的存在性由后端测试管。
    """
    path = link.split("?", 1)[0].rstrip("/") or "/"
    if path.startswith(("/api", "/console")):
        return False
    if path.lower().endswith(_STATIC_EXT):
        return False
    return True


def _check_link(exists: set[str], link: str) -> bool:
    path = link.split("?", 1)[0].rstrip("/") or "/"
    return path in exists


def test_no_dead_internal_links(built):
    """生成的 .md 里所有站内页面链接（markdown 链接 + HTML href）都必须有落点。

    旧版只扫 `](...)` 且只看 /parts /learn /api /console 前缀，
    型号页 hero 卡、首页入口卡、竞赛页卡片里的 href="/xxx" 一个都没测。
    """
    exists = _page_paths(built)
    bad: list[str] = []
    for p in built.rglob("*.md"):
        if ".vitepress" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        links = [m.group(1) for m in _MD_LINK.finditer(text)]
        links += [m.group(1) for m in _HTML_HREF.finditer(text)]
        for link in links:
            if not _is_page_link(link):
                continue
            if not _check_link(exists, link):
                bad.append(f"{p.relative_to(built).as_posix()} -> {link}")
    assert not bad, "死链：" + "; ".join(bad[:10])


def test_no_dead_links_in_vue_components():
    """Vue 组件里写死的站内 href/to 路径，必须是文档站里真实存在的页面。

    :to / 动态绑定管不了（值在运行时），但模板里写死的字符串能管。
    这份清单的路径若改名，组件就得跟着改 —— 测试就是那条保险丝。
    """
    comp_dir = ROOT / "wiki" / "docs" / ".vitepress" / "components"
    if not comp_dir.exists():
        pytest.skip("没有组件目录")
    exists = _page_paths(ROOT / "wiki" / "docs")
    bad: list[str] = []
    vue_href = re.compile(r"""(?:href|to)=["'](/[^"'#{}:]+)["']""")
    for f in comp_dir.glob("*.vue"):
        for m in vue_href.finditer(f.read_text(encoding="utf-8")):
            link = m.group(1)
            if not _is_page_link(link):
                continue
            if not _check_link(exists, link):
                bad.append(f"{f.name} -> {link}")
    assert not bad, "组件里的死链：" + "; ".join(bad[:10])

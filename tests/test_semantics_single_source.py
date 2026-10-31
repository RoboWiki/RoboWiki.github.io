"""口径常量「真的只有一份」—— 把单源约束钉成测试。

背景（ADR-002 / 提交 4bf4f62）：
    口径常量原先写在 `backend/app/api/routes/semantics.py`，静态站为了复用不得不
    `sys.path.insert(backend)` 再 import 后端，于是数据和服务被绑成一个 Python 包。
    现在唯一事实源是 `schema/semantics.json`：`pipeline/build_site.py` 直接读文件，
    后端也从文件读，MCP 走 `/api/semantics`。

这里守四件事，任何一件破了都应该红：
    ① JSON 本身能被解析，七个顶层键齐全，version 是 1.0.0 那种三段式；
    ② 静态站不能再碰后端模块（回到「为了读常量而 import 后端」就是回退）；
    ③ 后端导出的常量与 JSON **逐字相等**（不是「差不多」，是 ==）；
    ④ backend/ 里没人又把口径常量手抄一份（抄一份就是两个事实源）。

fastapi 未安装时也能跑：第 ③ 项用 stub 顶掉 `fastapi`，不 import 整个 app。
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import shutil
import sys
import tempfile
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEMANTICS_JSON = ROOT / "schema" / "semantics.json"
BACKEND_SEMANTICS = ROOT / "backend" / "app" / "api" / "routes" / "semantics.py"
BUILD_SITE = ROOT / "pipeline" / "build_site.py"
VALIDATE = ROOT / "pipeline" / "validate.py"

#: version + 六组口径 = /semantics 与 MCP 的返回契约
TOP_LEVEL_KEYS = (
    "version",
    "field_semantics",
    "red_lines",
    "conversions",
    "comparability",
    "supplier_questions",
    "trinary",
)

#: 后端把这些键摊成同名模块常量，顺序也照 JSON 走
CONSTANT_BY_KEY = {
    "field_semantics": "FIELD_SEMANTICS",
    "red_lines": "RED_LINES",
    "conversions": "CONVERSIONS",
    "comparability": "COMPARABILITY",
    "supplier_questions": "SUPPLIER_QUESTIONS",
    "trinary": "TRINARY",
}

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

#: 判定「手抄常量」的形状：常量名 + 直接赋值成字面量容器
HARDCODED_ASSIGN_RE = re.compile(
    r"^[ \t]*(%s)\s*(?::[^=\n]+)?=\s*[\[{]" % "|".join(CONSTANT_BY_KEY.values()),
    re.MULTILINE,
)

#: 抄文案也算抄：口径里的长句比数字更难凑巧撞上
COPIED_TEXT_MIN_LEN = 12


def _json() -> dict:
    return json.loads(SEMANTICS_JSON.read_text(encoding="utf-8"))


def _backend_py_files() -> list[pathlib.Path]:
    return [
        p
        for p in sorted((ROOT / "backend").rglob("*.py"))
        if "__pycache__" not in p.parts
    ]


class _StubRouter:
    """够用的 APIRouter：给 decorator 用，不注册任何东西。"""

    def __init__(self, *args, **kwargs) -> None:
        pass

    def get(self, *args, **kwargs):
        def _decorator(func):
            return func

        return _decorator


def _load_backend_semantics(name: str = "_semantics_under_test"):
    """按文件路径 import 后端的 semantics.py，不依赖 fastapi 是否安装。

    注入 stub 而不是真 fastapi：既不需要 fastapi 装在环境里，
    也避免为了读四个常量就把整个 app 拉起来（DB、配置、路由全都不要）。
    """
    assert BACKEND_SEMANTICS.is_file(), f"后端口径模块不见了：{BACKEND_SEMANTICS}"
    stub = types.ModuleType("fastapi")
    stub.APIRouter = _StubRouter
    saved = sys.modules.get("fastapi")
    sys.modules["fastapi"] = stub
    try:
        spec = importlib.util.spec_from_file_location(name, BACKEND_SEMANTICS)
        assert spec and spec.loader, "semantics.py 无法按文件加载"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if saved is None:
            sys.modules.pop("fastapi", None)
        else:
            sys.modules["fastapi"] = saved


# ── ① JSON 形状 ────────────────────────────────────────────────────────
def test_semantics_json_parses_and_has_all_keys():
    data = _json()
    assert isinstance(data, dict), "schema/semantics.json 顶层必须是对象"
    missing = [k for k in TOP_LEVEL_KEYS if k not in data]
    assert not missing, f"semantics.json 缺顶层键：{missing}"
    unexpected_shape = {
        k: type(data[k]).__name__
        for k in ("field_semantics", "trinary")
        if not isinstance(data[k], dict)
    }
    assert not unexpected_shape, f"这两组必须对象：{unexpected_shape}"
    for k in ("red_lines", "conversions", "comparability", "supplier_questions"):
        assert isinstance(data[k], list) and data[k], f"{k} 必须是非空数组"


def test_semantics_version_is_semver():
    version = _json()["version"]
    assert isinstance(version, str) and VERSION_RE.match(version), (
        f"version 要写成 x.y.z（当前 {version!r}）—— 升级规则见 schema/semantics.README.md"
    )


def test_semantics_red_lines_carry_threshold_shape():
    """红线是页面上的硬结论，review/absurd 两个阈值不能悄悄退化成别的键名。"""
    red_lines = {item["id"]: item for item in _json()["red_lines"]}
    for rid in ("RL-01", "RL-02"):
        assert rid in red_lines, f"red_lines 缺 {rid}"
    for key in ("review_above", "absurd_above"):
        for rid in ("RL-01", "RL-02"):
            assert key in red_lines[rid], f"{rid} 缺 {key}"
            assert isinstance(red_lines[rid][key], (int, float)), f"{rid}.{key} 必须是数字"
    assert red_lines["RL-01"]["review_above"] < red_lines["RL-01"]["absurd_above"]
    assert red_lines["RL-02"]["review_above"] < red_lines["RL-02"]["absurd_above"]


# ── ② 静态站不许碰后端 ────────────────────────────────────────────────
def test_build_site_reads_json_not_backend():
    site = BUILD_SITE.read_text(encoding="utf-8")
    assert "app.api.routes.semantics" not in site, (
        "pipeline/build_site.py 又 import 后端口径模块了 —— 静态站必须直接读 schema/semantics.json"
    )
    assert "from app" not in site and "import app" not in site, (
        "build_site.py 出现了后端包 import"
    )
    assert "semantics.json" in site, "build_site.py 应该读 schema/semantics.json"


def test_pipeline_never_reaches_into_backend():
    """整个 pipeline/ 都不该 import 后端（动态站和静态站要能各自跑起来）。"""
    offenders = []
    for path in sorted((ROOT / "pipeline").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "app.api.routes" in text or ("path.insert" in text and "backend" in text):
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, f"pipeline 里出现后端依赖：{offenders}"


# ── ③ 后端常量 == JSON 内容 ───────────────────────────────────────────
def test_backend_constants_equal_json_exactly():
    data = _json()
    module = _load_backend_semantics()
    for key, attr in CONSTANT_BY_KEY.items():
        actual = getattr(module, attr, "<缺失>")
        assert actual == data[key], f"{attr} 与 schema/semantics.json 的 {key} 不一致"
    assert module.SEMANTICS_VERSION == data["version"]


def test_backend_resolves_the_repo_json():
    module = _load_backend_semantics("_semantics_path_under_test")
    resolved = pathlib.Path(module.SEMANTICS_FILE).resolve()
    assert resolved == SEMANTICS_JSON.resolve(), (
        f"后端读到的 JSON 不是仓库里那份：{resolved}"
    )


def test_backend_reports_missing_file_clearly():
    """文件没了要炸出人话，不能等到请求里冒 KeyError。"""
    module = _load_backend_semantics("_semantics_error_under_test")
    with pytest.raises(RuntimeError) as exc:
        module._load(SEMANTICS_JSON.with_name("no-such-semantics.json"))
    assert "no-such-semantics.json" in str(exc.value)


def test_backend_reports_missing_key_clearly(tmp_path):
    """顶层键少一个时点名缺哪个，而不是 KeyError: 'trinary'。"""
    module = _load_backend_semantics("_semantics_key_under_test")
    broken = tmp_path / "semantics.json"
    payload = {k: v for k, v in _json().items() if k != "trinary"}
    broken.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(RuntimeError) as exc:
        module._load(broken)
    assert "trinary" in str(exc.value)


def test_backend_search_fails_loudly_outside_repo():
    """向上找不到 JSON 时给可执行说明 —— 顺带证明路径解析不是写死下标。"""
    module = _load_backend_semantics("_semantics_search_under_test")
    # 仓库内的任何临时目录都会向上撞到 schema/，所以探针放到仓库外层
    probe_root = pathlib.Path(tempfile.mkdtemp(prefix="sem-probe-", dir=str(ROOT.parent)))
    try:
        deep = probe_root / "a" / "b" / "c"
        deep.mkdir(parents=True)
        with pytest.raises(RuntimeError) as exc:
            module._find_semantics_file(deep / "semantics.py")
        message = str(exc.value)
        assert "schema/semantics.json" in message
        assert "semantics.README.md" in message, "报错里要给排查入口"
    finally:
        shutil.rmtree(probe_root, ignore_errors=True)


# ── ④ backend/ 里不许有手抄副本 ───────────────────────────────────────
def test_backend_has_no_hand_copied_constants():
    offenders = []
    for path in _backend_py_files():
        if path == BACKEND_SEMANTICS:
            continue  # 唯一允许「定义」这些名字的地方（值来自 JSON）
        text = path.read_text(encoding="utf-8")
        for match in HARDCODED_ASSIGN_RE.finditer(text):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(1)} = [...]/{{...}}")
    assert not offenders, (
        "backend/ 里出现手抄的口径常量副本（事实源只有 schema/semantics.json）：\n  "
        + "\n  ".join(offenders)
    )


def test_backend_has_no_hand_copied_semantics_text():
    """数字能抄，文案也能抄：把口径长句搬进代码同样等于两个事实源。"""
    data = _json()
    quotes: dict[str, str] = {}
    for field, spec in data["field_semantics"].items():
        for key in ("meaning", "missing_means", "why", "known_bias"):
            value = spec.get(key)
            if isinstance(value, str) and len(value) >= COPIED_TEXT_MIN_LEN:
                quotes.setdefault(value, f"field_semantics.{field}.{key}")
    for collection in ("red_lines", "comparability"):
        for item in data[collection]:
            name = item.get("id") or item.get("grade")
            for key, value in item.items():
                if isinstance(value, str) and len(value) >= COPIED_TEXT_MIN_LEN:
                    quotes.setdefault(value, f"{collection}.{name}.{key}")

    offenders = []
    for path in _backend_py_files():
        if path == BACKEND_SEMANTICS:
            continue
        text = path.read_text(encoding="utf-8")
        for quote, where in quotes.items():
            if quote in text:
                offenders.append(f"{path.relative_to(ROOT)} 抄了 {where}")
    assert not offenders, "backend/ 里出现口径文案副本：\n  " + "\n  ".join(offenders)


def test_pipeline_thresholds_come_from_json():
    """validate.py 的红线阈值只取数不复制：改了 JSON 就该跟着变。"""
    source = VALIDATE.read_text(encoding="utf-8")
    literal = re.search(
        r"^[ \t]*(TD_REVIEW|TD_ABSURD|PR_REVIEW|PR_ABSURD)\s*=\s*\d", source, re.MULTILINE
    )
    assert not literal, (
        f"pipeline/validate.py 又把红线阈值写成字面量了（{literal.group(1)}）—— 应该读 red_lines"
    )
    spec = importlib.util.spec_from_file_location("_validate_under_test", VALIDATE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    red_lines = {item["id"]: item for item in _json()["red_lines"]}
    assert module.TD_REVIEW == red_lines["RL-01"]["review_above"]
    assert module.TD_ABSURD == red_lines["RL-01"]["absurd_above"]
    assert module.PR_REVIEW == red_lines["RL-02"]["review_above"]
    assert module.PR_ABSURD == red_lines["RL-02"]["absurd_above"]

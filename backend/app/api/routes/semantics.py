"""参数口径规范（可机读版）—— 现在**数据在 schema/semantics.json**。

历史：常量原先写在这个模块里，静态站为了复用不得不 `sys.path.insert(backend)` 再 import，
于是「数据」和「服务」被绑成了一个 Python 包（拆仓时最硬的钉子）。
现在常量搬进 JSON：静态站直接读文件，FastAPI 也从文件读，两边同一份，且不再互相 import。

本模块只剩三件事：
  1. 找到那份 JSON（唯一事实源），找不到就**说清为什么失败**；
  2. 把 JSON 的顶层键摊成模块常量，给 `routes/mcp.py` 之类的同包消费者用；
  3. 保留 `/semantics` 路由，形状不变（老客户端不受影响）。
字段约定、消费者清单、version 升级规则见 `schema/semantics.README.md`。
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["semantics"])

#: JSON 必须有的顶层键。缺一个就在 import 时炸掉并说清缺哪个，
#: 而不是等到某次请求里冒出 `KeyError: 'trinary'` 才被发现。
REQUIRED_KEYS = (
    "version",
    "field_semantics",
    "red_lines",
    "conversions",
    "comparability",
    "supplier_questions",
    "trinary",
)


def _find_semantics_file(start: Path | None = None) -> Path:
    """从本文件位置（或给定的起点）逐级向上找 `schema/semantics.json`。

    不写死 `parents[N]`：后端目录层级被动过（vendored、挪进 src/、装成包）之后，
    写死的下标要么指向不存在的路径，要么更糟 —— 指到别人家仓库的同名文件上，
    静默读到一份过期口径。逐级向上找 + 找不到就报错，两种病一起治。
    原先的 `parents[4]` 正好落在仓库根上，是对的；但它只是「当前布局恰好对」，
    不是「布局变了还对」。
    """
    here = Path(__file__).resolve() if start is None else Path(start).resolve()
    for base in here.parents:
        candidate = base / "schema" / "semantics.json"
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "找不到参数口径的唯一事实源 schema/semantics.json。\n"
        f"  查找起点：{here}\n"
        "  已从该位置逐级向上查找 schema/semantics.json，全部未命中。\n"
        "这份 JSON 是静态站 / FastAPI / MCP 共用的唯一事实源，缺了不该启动。\n"
        "  排查：① backend/ 和 schema/ 是否在同一个仓库根下（ADR-002 单仓）；"
        "② 部署时是否只拷了 backend/；③ 参考 schema/semantics.README.md。"
    )


def _load(path: Path) -> dict:
    """读 + 解析 + 校验顶层键，任何一步失败都给可执行的说明。"""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"参数口径 JSON 读不出来：{path}（{exc}）") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"参数口径 JSON 不是合法 JSON：{path} 第 {exc.lineno} 行第 {exc.colno} 列：{exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"参数口径 JSON 顶层必须是对象，实际是 {type(data).__name__}：{path}")
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise RuntimeError(
            f"参数口径 JSON 缺顶层键 {missing}：{path}\n"
            "  这七个键（version + 六组口径）是 /semantics 与 MCP 的契约，"
            "加/删键请同步 schema/semantics.README.md 的 version 规则。"
        )
    return data


SEMANTICS_FILE = _find_semantics_file()

_DATA = _load(SEMANTICS_FILE)

SEMANTICS_VERSION = _DATA["version"]
FIELD_SEMANTICS = _DATA["field_semantics"]
RED_LINES = _DATA["red_lines"]
CONVERSIONS = _DATA["conversions"]
COMPARABILITY = _DATA["comparability"]
SUPPLIER_QUESTIONS = _DATA["supplier_questions"]
TRINARY = _DATA["trinary"]


@router.get("/semantics")
def get_semantics() -> dict:
    """参数口径规范：字段含义、红线阈值、单位换算、可比性分级。"""
    return {
        "version": SEMANTICS_VERSION,
        "fields": FIELD_SEMANTICS,
        "red_lines": RED_LINES,
        "conversions": CONVERSIONS,
        "comparability": COMPARABILITY,
        "supplier_questions": SUPPLIER_QUESTIONS,
        "trinary": TRINARY,
    }

"""参数口径规范（可机读版）—— 现在**数据在 schema/semantics.json**。

历史：常量原先写在这个模块里，静态站为了复用不得不 `sys.path.insert(backend)` 再 import，
于是「数据」和「服务」被绑成了一个 Python 包（拆仓时最硬的钉子）。
现在常量搬进 JSON：静态站直接读文件，FastAPI 也从文件读，两边同一份，且不再互相 import。
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["semantics"])

SEMANTICS_FILE = Path(__file__).resolve().parents[4] / "schema" / "semantics.json"


def _load() -> dict:
    return json.loads(SEMANTICS_FILE.read_text(encoding="utf-8"))


_DATA = _load()

FIELD_SEMANTICS = _DATA["field_semantics"]
RED_LINES = _DATA["red_lines"]
CONVERSIONS = _DATA["conversions"]
COMPARABILITY = _DATA["comparability"]
SUPPLIER_QUESTIONS = _DATA["supplier_questions"]
TRINARY = _DATA["trinary"]
SEMANTICS_VERSION = _DATA.get("version", "0")


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

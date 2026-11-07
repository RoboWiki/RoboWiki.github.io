"""群机器人只读问答：一个型号 -> 一句话 + 链接。

只做被动查询，不做推送；QQ 主动消息每月只有 4 条，推送不是这个接口的事。
认证用共享令牌（`ROBOWIKI_BOT_TOKEN`），未配置即关闭。
"""
from __future__ import annotations

import re
import secrets

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlmodel import select

from ...core.config import settings
from ...models import Part
from ..deps import Db, rate_limit
from .catalog import public_part, subtype_label

router = APIRouter(prefix="/bot", tags=["bot"])
bot_scheme = APIKeyHeader(name="X-Bot-Token", auto_error=False, scheme_name="botToken",
                         description="与后端 ROBOWIKI_BOT_TOKEN 相同的共享令牌")

#: 一句话里优先展示的字段（按品类取前三个有值的）
_FACTS: dict[str, list[tuple[str, str]]] = {
    "actuator": [
        ("tau_rated_Nm", "额定 {} N·m"), ("tau_peak_Nm", "峰值 {} N·m"),
        ("voltage_V", "{} V"), ("gear", "减速比 {}"), ("mass_kg", "{} kg"),
    ],
    "controller_high": [
        ("npu_tops", "{} TOPS"), ("cpu", "{}"), ("ram_gb", "{} GB RAM"),
        ("power_max_w", "{} W"),
    ],
    "controller_low": [
        ("mcu", "{}"), ("can", "CAN {}"), ("io", "{}"), ("voltage_in_V", "{} V"),
    ],
    "motor_driver": [
        ("mcu", "{}"), ("can", "CAN {}"), ("voltage_in_V", "{} V"),
    ],
    "imu": [("gyro_range_dps", "陀螺 {} °/s"), ("iface", "{}"), ("noise", "{}")],
    "camera": [("depth_range_m", "{} m"), ("fov", "{}"), ("fps", "{} fps")],
    "lidar": [("range_m", "{} m"), ("fov", "{}"), ("points_per_s", "{} pts/s")],
    "connector": [("positions", "{} pin"), ("pitch_mm", "{} mm"),
                  ("current_rated_A", "{} A"), ("voltage_rated_V", "{} V"),
                  ("wire_awg", "{}"), ("mating_cycles", "{} 次")],
    "module": [("iface", "{}"), ("voltage_V", "{} V"), ("channel", "{} 通道")],
}
_GENERIC = [("voltage_V", "{} V"), ("iface", "{}"), ("channel", "{} 通道"),
            ("mass_kg", "{} kg")]


def _auth(request: Request, token: str | None = None) -> None:
    expected = settings.bot_token
    if not expected:
        raise HTTPException(503, "机器人问答未启用：未配置 ROBOWIKI_BOT_TOKEN")
    got = str(token or request.headers.get("X-Bot-Token") or "")
    # compare_digest 对 str 只接受 ASCII；非 ASCII 入参会抛 TypeError → 500。
    # 统一按字节比较，非法输入只是「不相等」，不泄露预期值、也不炸栈。
    try:
        match = secrets.compare_digest(got.encode("utf-8"),
                                       str(expected).encode("utf-8"))
    except (TypeError, UnicodeError):
        match = False
    if not got or not match:
        raise HTTPException(401, "机器人令牌无效")


def _normalize(q: str) -> str:
    q = re.sub(r"[\x00-\x1f\x7f]", " ", q)[:100]
    q = re.sub(r"^\s*(?:@\S+\s+|/[\w-]+\s+)", "", q)
    q = re.sub(r"^\s*(?:查一下|查一查|查询|查|search)\s*[:：]?\s*", "", q,
               flags=re.I)
    return re.sub(r"\s+", " ", q).strip()


def _fact_line(p: Part, limit: int = 3) -> str:
    specs = p.specs or {}
    picked: list[str] = []
    for key, fmt in _FACTS.get(p.category, []) + _GENERIC:
        v = specs.get(key)
        if v in (None, "", 0):
            continue
        # 字符串值常常自带单位/区间说明，不再套单位，避免「0.2–10 mm m」
        text = fmt.format(v) if isinstance(v, (int, float)) and not isinstance(v, bool) \
            else str(v)
        if text not in picked:
            picked.append(text)
        if len(picked) >= limit:
            break
    return " · ".join(picked) if picked else subtype_label(p.category, p.subtype)


def _slug(p: Part) -> str:
    """与 pipeline/build_site.py 的型号页 slug 规则一致。"""
    base = re.sub(r"[^A-Za-z0-9]+", "-", f"{p.vendor}-{p.model}").strip("-").lower()
    return re.sub(r"-+", "-", base)[:60] or "part"


def _url(p: Part) -> str:
    return f"{settings.site_url.rstrip('/')}/parts/{p.category}/{_slug(p)}.html"


def _best(rows: list[Part], terms: list[str]) -> Part:
    q = " ".join(terms).lower()

    def score(p: Part) -> int:
        model = (p.model or "").lower()
        s = 0
        if (p.id or "").lower() == q:
            s += 100
        if model == q:
            s += 80
        if q and q in model:
            s += 40
        if p.verified:
            s += 2
        if p.source_tier == "A":
            s += 1
        return s

    return max(rows, key=score)


@router.get("/answer")
def answer(request: Request, db: Db, q: str, limit: int = 3,
           x_bot_token: Annotated[str | None, Security(bot_scheme)] = None):
    _auth(request, x_bot_token)
    rate_limit(request, "bot", 300)
    text = _normalize(q)
    terms = text.split()
    if not terms:
        raise HTTPException(422, "q 不能为空")
    if all(set(t) <= set("%_\\") for t in terms):
        return {
            "found": False,
            "answer": "请给出型号或厂商关键词，例如 AK80-6、XT30",
            "url": f"{settings.site_url.rstrip('/')}/catalog.html",
            "data_version": settings.data_version,
        }

    stmt = select(Part)
    for t in terms:
        # 手动转义：用户输入里的 % / _ 不能当通配符把整个目录捞出来
        safe = t.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(Part.search.like(f"%{safe}%", escape="\\"))
    rows = db.exec(stmt.limit(max(1, min(limit, 10)) * 4)).all()

    if not rows:
        return {
            "found": False,
            "answer": f"没找到「{text}」；换个厂商或型号关键词再试",
            "url": f"{settings.site_url.rstrip('/')}/catalog.html",
            "data_version": settings.data_version,
        }

    p = _best(rows, terms)
    facts = _fact_line(p)
    tier = f"来源 {p.source_tier or '—'}" + ("·已核对" if (p.verified and p.source_tier == "A") else "")
    line = f"{p.vendor} {p.model}" + (f" · {facts}" if facts else "") + f"（{tier}）"
    return {
        "found": True,
        "answer": line,
        "url": _url(p),
        "data_version": settings.data_version,
        "part": public_part(p),
    }

"""目录字段变更提案：提交 → 审核 → outbox。

不直接改 `parts` 表：审核通过只入 outbox，由 worker 产出可发布变更
（PR / release）；`parts` 仍是 release 的只读投影。
"""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from ...catalog_fields import allowed, split_field
from ...models import Outbox, Part, Submission, SubmissionReview, User
from ...schemas import (OutboxOut, ReviewIn, ReviewOut, SubmissionIn,
                        SubmissionOut)
from ..deps import CurrentUser, Db, MaybeUser, rate_limit, require_verified_email
from .notifications import create_notification

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _staff(user: User) -> None:
    if not user.is_staff:
        raise HTTPException(403, "需要 staff 权限")


LIST_FIELDS = {
    "specs.use_cases", "specs.positions_options", "specs.repo_urls",
    "specs.tags", "specs.features", "specs.price_tiers", "specs.params",
}

#: 审核理由是一份封闭的分类（照 Gitea 的 review 选项）：通过=ok，
#: 驳回必须落在某个具体原因上，避免出现「驳回但没人知道为什么」。
ACCEPT_REASONS = {"ok"}
REJECT_REASONS = {"insufficient_evidence", "wrong_value", "out_of_scope",
                  "duplicate", "other"}

#: 目录值域：数值上限与 PostIn.total_price_cny 保持同一量级。
MAX_PRICE_CNY = 10_000_000
MIN_CHECKED = date(1990, 1, 1)


def _page_limit(value: int, cap: int) -> int:
    """分页上限夹到 [1, cap]。

    只写 `min(limit, cap)` 时，负数会原样进 SQL：SQLite 的 `LIMIT -1` 表示
    「不设上限」（等于把整表读出来），Postgres 则直接报
    `LIMIT must not be negative` —— 同一个参数在两种部署下表现完全不同。
    """
    return max(1, min(int(value), cap))


def _http_url(value: str) -> bool:
    """只收真正的 http(s) 绝对链接：协议对、有主机、没有空白字符。"""
    if not value.lower().startswith(("http://", "https://")):
        return False
    if any(c.isspace() for c in value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(parsed.netloc)


def _check_review(payload: ReviewIn) -> tuple[str, str, str]:
    """校验审核决定并归一化 (decision, reason_code, note)。

    通过固定为 ok；驳回必须给出具体原因，「其他」还必须写明说明 ——
    提交者看到的就是这条理由，空着等于没审。
    """
    decision = payload.decision
    reason = (payload.reason_code or "").strip()
    note = (payload.note or "").strip()
    if decision == "accepted":
        if reason and reason not in ACCEPT_REASONS:
            raise HTTPException(422, "通过时的 reason_code 只能是 ok")
        return decision, "ok", note
    if reason not in REJECT_REASONS:
        raise HTTPException(422, "驳回理由必须是 insufficient_evidence / wrong_value / "
                                 "out_of_scope / duplicate / other 之一")
    if reason == "other" and len(note) < 4:
        raise HTTPException(422, "选择「其他」时必须写明具体原因（至少 4 个字）")
    return decision, reason, note


def _check_payload(payload: dict, user: User) -> None:
    if not payload:
        raise HTTPException(422, "payload 不能为空")
    if len(json.dumps(payload, ensure_ascii=False)) > 8192:
        raise HTTPException(422, "payload 过大（上限 8 KB）")
    for key, value in payload.items():
        if not allowed(key):
            raise HTTPException(422, f"不允许通过提案修改字段：{key}")
        if key == "verified" and not user.is_staff:
            raise HTTPException(403, "verified 只能由站务标记")
        if isinstance(value, dict):
            raise HTTPException(422, f"{key} 不接受嵌套对象")
        if isinstance(value, list):
            if key not in LIST_FIELDS:
                raise HTTPException(422, f"{key} 不接受列表")
            if len(value) > 50:
                raise HTTPException(422, f"{key} 列表过长（上限 50）")
            if any(isinstance(x, (dict, list)) for x in value):
                raise HTTPException(422, f"{key} 列表只能放标量")
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise HTTPException(422, f"{key} 的值类型不支持")
        if isinstance(value, str) and len(value) > 4000:
            raise HTTPException(422, f"{key} 文本过长（上限 4000 字）")

        # 值域校验放在服务端：UI 的约束可以被绕过，审核通过后会直接进 outbox/PR。
        if key == "price_cny" and value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise HTTPException(422, "price_cny 必须是数字")
            if not math.isfinite(float(value)) or not 0 <= value <= MAX_PRICE_CNY:
                raise HTTPException(422, f"price_cny 必须在 0–{MAX_PRICE_CNY} 之间")
        if key == "source_tier" and value not in ("A", "B", "C"):
            raise HTTPException(422, "source_tier 只能是 A/B/C")
        if key == "last_checked":
            if not isinstance(value, str):
                raise HTTPException(422, "last_checked 必须是 YYYY-MM-DD")
            try:
                checked = date.fromisoformat(value)
            except ValueError:
                raise HTTPException(422, "last_checked 必须是 YYYY-MM-DD") from None
            # 太早的日期多半是手滑（0199 / 1899），未来的日期则是提前「核对」
            if checked < MIN_CHECKED or checked > date.today() + timedelta(days=366):
                raise HTTPException(422, "last_checked 不在合理范围内（1990 之后、一年以内）")
        if key in ("url", "doc_url", "doc_pdf") and isinstance(value, str):
            if not _http_url(value):
                raise HTTPException(422, f"{key} 必须是完整的 http/https 链接")


def _out(db: Db, s: Submission) -> SubmissionOut:
    reviews = db.exec(
        select(SubmissionReview).where(SubmissionReview.submission_id == s.id)
        .order_by(SubmissionReview.created_at)
    ).all()
    return SubmissionOut(
        id=s.id or 0, kind=s.kind, target_id=s.target_id, payload=s.payload,
        evidence=s.evidence, submitter_id=s.submitter_id, status=s.status,
        revision=s.revision, created_at=s.created_at,
        reviews=[ReviewOut(id=r.id or 0, decision=r.decision,
                           reason_code=r.reason_code, note=r.note,
                           reviewer_id=r.reviewer_id, created_at=r.created_at)
                 for r in reviews],
    )


@router.post("", response_model=SubmissionOut, status_code=201)
def create_submission(payload: SubmissionIn, request: Request, db: Db,
                      user: CurrentUser):
    require_verified_email(user)
    rate_limit(request, "submission", 20, user.id)
    _check_payload(payload.payload, user)
    if not payload.evidence:
        raise HTTPException(422, "evidence 不能为空：请给出 source_url / 手册页码 / 说明")
    note = str(payload.evidence.get("note") or "").strip()
    if len(note) < 2:
        raise HTTPException(422, "请写清依据：至少 2 个字的说明或手册页码")
    if len(note) > 2000:
        raise HTTPException(422, "依据过长（上限 2000 字）")
    src = str(payload.evidence.get("source_url") or "").strip()
    if len(src) > 500:
        raise HTTPException(422, "source_url 过长（上限 500）")
    if src and not _http_url(src):
        raise HTTPException(422, "source_url 必须是完整的 http/https 链接")
    # 目标部件只查一次：既省一条查询，也避免「查到了→再查又没了」的 TOCTOU 窗口
    part = None
    if payload.kind == "part_patch":
        if not payload.target_id:
            raise HTTPException(422, "part_patch 需要 target_id")
        part = db.get(Part, payload.target_id)
        if part is None:
            raise HTTPException(404, "目标部件不存在")

    evidence = dict(payload.evidence)
    # preview 必须由服务端按当前目录生成；客户端传的一律丢弃，否则审核员看到的 diff 可被伪造
    evidence.pop("preview", None)
    if part is not None:
        specs = part.specs or {}
        preview = []
        for key, new in payload.payload.items():
            where, field = split_field(key)
            old = specs.get(field) if where == "specs" else getattr(part, field, None)
            preview.append({"field": key, "old_value": old, "new_value": new})
        evidence["preview"] = preview

    s = Submission(kind=payload.kind, target_id=payload.target_id,
                   payload=payload.payload, evidence=evidence,
                   submitter_id=user.id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return _out(db, s)


@router.get("/mine", response_model=list[SubmissionOut])
def my_submissions(db: Db, user: CurrentUser, limit: int = 50):
    rows = db.exec(
        select(Submission).where(Submission.submitter_id == user.id)
        .order_by(Submission.created_at.desc()).limit(_page_limit(limit, 200))
    ).all()
    return [_out(db, s) for s in rows]


@router.get("/outbox", response_model=list[OutboxOut])
def outbox(db: Db, user: CurrentUser, limit: int = 100):
    _staff(user)
    rows = db.exec(select(Outbox).order_by(Outbox.created_at.desc())
                   .limit(_page_limit(limit, 500))).all()
    return [OutboxOut(id=r.id or 0, submission_id=r.submission_id,
                      action=r.action, status=r.status, attempts=r.attempts,
                      last_error=r.last_error, result=r.result or {},
                      created_at=r.created_at)
            for r in rows]


@router.post("/outbox/{outbox_id}/retry", response_model=OutboxOut)
def retry_outbox(outbox_id: int, db: Db, user: CurrentUser):
    _staff(user)
    row = db.get(Outbox, outbox_id)
    if row is None:
        raise HTTPException(404, "outbox 任务不存在")
    if row.status == "running":
        raise HTTPException(409, "任务正在执行，稍后再试")
    row.status = "pending"
    row.next_at = datetime.now(timezone.utc)
    row.last_error = None
    db.add(row)
    db.commit()
    db.refresh(row)
    return OutboxOut(id=row.id or 0, submission_id=row.submission_id,
                     action=row.action, status=row.status, attempts=row.attempts,
                     last_error=row.last_error, result=row.result or {},
                     created_at=row.created_at)


@router.get("/queue", response_model=list[SubmissionOut])
def queue(db: Db, user: CurrentUser, status: str = "pending", limit: int = 100):
    _staff(user)
    rows = db.exec(
        select(Submission).where(Submission.status == status)
        .order_by(Submission.created_at).limit(_page_limit(limit, 500))
    ).all()
    return [_out(db, s) for s in rows]


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(submission_id: int, db: Db, user: MaybeUser):
    s = db.get(Submission, submission_id)
    if s is None:
        raise HTTPException(404, "提案不存在")
    if not user or (user.id != s.submitter_id and not user.is_staff):
        raise HTTPException(403, "无权查看")
    return _out(db, s)


@router.post("/{submission_id}/review", response_model=SubmissionOut)
def review_submission(submission_id: int, payload: ReviewIn, db: Db,
                      user: CurrentUser):
    _staff(user)
    s = db.get(Submission, submission_id)
    if s is None:
        raise HTTPException(404, "提案不存在")
    if s.status != "pending":
        raise HTTPException(409, f"提案当前状态是 {s.status}，不能重复审核")

    decision, reason, note = _check_review(payload)
    review = SubmissionReview(submission_id=s.id, reviewer_id=user.id,
                              decision=decision,
                              reason_code=reason, note=note)
    db.add(review)
    s.status = decision
    s.updated_at = review.created_at

    if s.submitter_id:
        verdict = "通过" if decision == "accepted" else "驳回"
        detail = note or reason or ""
        create_notification(
            db, s.submitter_id, type="moderation",
            subject=f"你的参数提案已{verdict}",
            body=detail[:300], link="/catalog.html", actor_id=user.id)

    if decision == "accepted":
        db.add(Outbox(
            submission_id=s.id,
            action=s.kind,
            payload={"target_id": s.target_id, "changes": s.payload,
                     "evidence": s.evidence},
            idempotency_key=f"submission:{s.id}:{s.revision}",
        ))
        # 通过提案给提交者记声望；审核通过 ≠ 已发布，页面仍需 data-v* 发布后更新。
        if s.submitter_id:
            submitter = db.get(User, s.submitter_id)
            if submitter:
                submitter.reputation = int(submitter.reputation or 0) + 5
                db.add(submitter)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "该提案已在处理中，请刷新后再看") from None
    db.refresh(s)
    return _out(db, s)

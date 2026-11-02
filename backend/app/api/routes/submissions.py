"""目录字段变更提案：提交 → 审核 → outbox。

不直接改 `parts` 表：审核通过只入 outbox，由 worker 产出可发布变更
（PR / release）；`parts` 仍是 release 的只读投影。
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from ...catalog_fields import allowed, split_field
from ...models import Outbox, Part, Submission, SubmissionReview, User
from ...schemas import (OutboxOut, ReviewIn, ReviewOut, SubmissionIn,
                        SubmissionOut)
from ..deps import CurrentUser, Db, MaybeUser, rate_limit

router = APIRouter(prefix="/submissions", tags=["submissions"])


def _staff(user: User) -> None:
    if not user.is_staff:
        raise HTTPException(403, "需要 staff 权限")


def _check_payload(payload: dict) -> None:
    if not payload:
        raise HTTPException(422, "payload 不能为空")
    for key in payload:
        if not allowed(key):
            raise HTTPException(422, f"不允许通过提案修改字段：{key}")


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
    rate_limit(request, "submission", 20)
    _check_payload(payload.payload)
    if not payload.evidence:
        raise HTTPException(422, "evidence 不能为空：请给出 source_url / 手册页码 / 说明")
    if payload.kind == "part_patch":
        if not payload.target_id:
            raise HTTPException(422, "part_patch 需要 target_id")
        if db.get(Part, payload.target_id) is None:
            raise HTTPException(404, "目标部件不存在")

    evidence = dict(payload.evidence)
    if payload.kind == "part_patch" and "preview" not in evidence:
        p = db.get(Part, payload.target_id)
        specs = (p.specs or {}) if p else {}
        preview = []
        for key, new in payload.payload.items():
            where, field = split_field(key)
            old = specs.get(field) if where == "specs" else getattr(p, field, None)
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
        .order_by(Submission.created_at.desc()).limit(min(limit, 200))
    ).all()
    return [_out(db, s) for s in rows]


@router.get("/outbox", response_model=list[OutboxOut])
def outbox(db: Db, user: CurrentUser, limit: int = 100):
    _staff(user)
    rows = db.exec(select(Outbox).order_by(Outbox.created_at.desc())
                   .limit(min(limit, 500))).all()
    return [OutboxOut(id=r.id or 0, submission_id=r.submission_id,
                      action=r.action, status=r.status, attempts=r.attempts,
                      last_error=r.last_error, result=r.result or {},
                      created_at=r.created_at)
            for r in rows]


@router.get("/queue", response_model=list[SubmissionOut])
def queue(db: Db, user: CurrentUser, status: str = "pending", limit: int = 100):
    _staff(user)
    rows = db.exec(
        select(Submission).where(Submission.status == status)
        .order_by(Submission.created_at).limit(min(limit, 500))
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

    review = SubmissionReview(submission_id=s.id, reviewer_id=user.id,
                              decision=payload.decision,
                              reason_code=payload.reason_code, note=payload.note)
    db.add(review)
    s.status = payload.decision
    s.updated_at = review.created_at

    if payload.decision == "accepted":
        db.add(Outbox(
            submission_id=s.id,
            action=s.kind,
            payload={"target_id": s.target_id, "changes": s.payload,
                     "evidence": s.evidence},
            idempotency_key=f"submission:{s.id}:{s.revision}",
        ))
    db.commit()
    db.refresh(s)
    return _out(db, s)

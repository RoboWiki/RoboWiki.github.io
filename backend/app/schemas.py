"""请求 / 响应模型。"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ── 认证 ────────────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    handle: str = Field(min_length=2, max_length=24)
    display_name: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=200)

    @field_validator("handle")
    @classmethod
    def _handle_ok(cls, v: str) -> str:
        if not all(c.isalnum() or c in "-_" for c in v):
            raise ValueError("handle 只能包含字母、数字、- 和 _")
        return v.lower()


class LoginIn(BaseModel):
    handle: str
    password: str


class UserOut(BaseModel):
    id: int
    handle: str
    display_name: str
    bio: str = ""
    avatar_hue: int = 160
    is_staff: bool = False
    reputation: int = 0
    created_at: datetime
    post_count: int = 0
    comment_count: int = 0
    badges: list[str] = []


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── 帖子 ────────────────────────────────────────────────────────────────────
class PostIn(BaseModel):
    kind: str = "discussion"
    title: str = Field(min_length=4, max_length=120)
    body: str = Field(min_length=10, max_length=20000)
    part_id: str | None = None
    tags: str = Field(default="", max_length=80)
    rating: int | None = Field(default=None, ge=1, le=5)
    use_case: str | None = Field(default=None, max_length=16)
    own_hardware: bool = False
    total_price_cny: float | None = Field(default=None, ge=0, le=10_000_000)
    price_scope: str | None = Field(default=None, max_length=200)
    price_verified: bool = False

    @field_validator("kind")
    @classmethod
    def _kind_ok(cls, v: str) -> str:
        if v not in ("discussion", "review", "build"):
            raise ValueError("kind 必须是 discussion / review / build")
        return v


class PostOut(BaseModel):
    id: int
    kind: str
    title: str
    body: str
    tags: list[str] = []
    part_id: str | None = None
    part_title: str | None = None
    rating: int | None = None
    use_case: str | None = None
    own_hardware: bool = False
    total_price_cny: float | None = None
    price_scope: str | None = None
    price_verified: bool = False
    score: int = 0
    comment_count: int = 0
    view_count: int = 0
    pinned: bool = False
    created_at: datetime
    author: UserOut | None = None
    my_vote: int = 0


class PostListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[PostOut]


class CommentIn(BaseModel):
    body: str = Field(min_length=2, max_length=4000)
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    post_id: int
    parent_id: int | None = None
    body: str
    score: int = 0
    created_at: datetime
    author: UserOut | None = None
    my_vote: int = 0
    replies: list["CommentOut"] = []


class VoteIn(BaseModel):
    target_kind: str
    target_id: int
    value: int

    @field_validator("target_kind")
    @classmethod
    def _tk(cls, v: str) -> str:
        if v not in ("post", "comment"):
            raise ValueError("target_kind 必须是 post 或 comment")
        return v

    @field_validator("value")
    @classmethod
    def _v(cls, v: int) -> int:
        if v not in (-1, 0, 1):
            raise ValueError("value 只能是 -1 / 0 / 1")
        return v


class VoteOut(BaseModel):
    score: int
    my_vote: int


# ── 数据变更提案 ────────────────────────────────────────────────────────────
class SubmissionIn(BaseModel):
    kind: str = "part_patch"
    target_id: str | None = None
    payload: dict = Field(default_factory=dict)
    evidence: dict = Field(default_factory=dict)

    @field_validator("kind")
    @classmethod
    def _kind_ok(cls, v: str) -> str:
        if v != "part_patch":
            raise ValueError("当前只接受 part_patch")
        return v


class ReviewIn(BaseModel):
    decision: str
    reason_code: str = Field(default="", max_length=80)
    note: str = Field(default="", max_length=2000)

    @field_validator("decision")
    @classmethod
    def _decision_ok(cls, v: str) -> str:
        if v not in ("accepted", "rejected"):
            raise ValueError("decision 必须是 accepted / rejected")
        return v


class ReviewOut(BaseModel):
    id: int
    decision: str
    reason_code: str = ""
    note: str = ""
    reviewer_id: int | None = None
    created_at: datetime


class SubmissionOut(BaseModel):
    id: int
    kind: str
    target_id: str | None = None
    payload: dict = {}
    evidence: dict = {}
    submitter_id: int | None = None
    status: str
    revision: int
    created_at: datetime
    reviews: list[ReviewOut] = []


class OutboxOut(BaseModel):
    id: int
    submission_id: int | None = None
    action: str
    status: str
    attempts: int = 0
    last_error: str | None = None
    result: dict = {}
    created_at: datetime

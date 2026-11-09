"""请求 / 响应模型。"""
from __future__ import annotations

import re
from typing import Literal
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_AVATAR_HTTP_RE = re.compile(r"^https?://", re.IGNORECASE)


def _normalize_email(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip().lower()
    if not v:
        return None
    if len(v) > 200:
        raise ValueError("邮箱过长")
    if not _EMAIL_RE.match(v):
        raise ValueError("邮箱格式不正确")
    return v


def _normalize_avatar_url(v: str | None) -> str | None:
    """头像只收两类：本站媒体路径或 http(s) 外链。

    `javascript:` / `data:` 之类会进 `<img src>` 的值一律拒掉 —— 前端
    直接渲染这个字段，协议白名单必须由服务端兜住，不能靠客户端自觉。
    空串视同清除，返回 None。
    """
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    if len(v) > 500:
        raise ValueError("头像地址过长")
    if any(c.isspace() for c in v):
        raise ValueError("头像地址不能包含空白字符")
    if v.startswith("/media/") and len(v) > len("/media/"):
        return v
    if _AVATAR_HTTP_RE.match(v):
        try:
            parsed = urlparse(v)
        except ValueError:
            parsed = None
        if parsed is not None and parsed.netloc:
            return v
    raise ValueError("头像地址只能是 /media/... 或 http(s) 链接")


# ── 认证 ────────────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    handle: str = Field(min_length=2, max_length=24)
    #: 昵称可选；不填时用 handle
    display_name: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=6, max_length=128)
    email: str | None = Field(default=None, max_length=200)

    @field_validator("handle")
    @classmethod
    def _handle_ok(cls, v: str) -> str:
        low = v.lower()
        if not low[0].isascii() or not (low[0].isalnum()) or \
                any(not (c.isascii() and (c.isalnum() or c in "-_")) for c in low[1:]):
            raise ValueError("handle 只能使用 a-z、0-9、- 和 _，且以字母或数字开头")
        return low

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str | None) -> str | None:
        return _normalize_email(v)


class VerifyEmailIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ForgotIn(BaseModel):
    email: str = Field(min_length=3, max_length=200)

    @field_validator("email")
    @classmethod
    def _email_ok(cls, v: str) -> str:
        normalized = _normalize_email(v)
        if normalized is None:
            raise ValueError("邮箱不能为空")
        return normalized


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=6, max_length=128)


class PasswordChangeIn(BaseModel):
    """已登录用户改密：必须证明自己知道当前口令。"""

    current_password: str = Field(min_length=1, max_length=128)
    # 与注册 / 找回保持同一强度下限；太短由 pydantic 直接 422。
    new_password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    handle: str
    password: str


class UserOut(BaseModel):
    id: int
    handle: str
    display_name: str
    bio: str = ""
    avatar_hue: int = 160
    avatar_url: str | None = None
    is_staff: bool = False
    email_verified: bool = False
    reputation: int = 0
    created_at: datetime
    post_count: int = 0
    comment_count: int = 0
    #: 贡献统计：打分数 / 目录变更提案数 / 回答被采纳数
    rating_count: int = 0
    submission_count: int = 0
    accepted_count: int = 0
    badges: list[str] = []


class AccountOut(UserOut):
    """账号本人视角：比公开的 UserOut 多邮箱与「是否有可用口令」。

    `email` 只出现在 /auth/me、登录响应与邮箱验证结果里。帖子作者、榜单
    等公开位置仍然用 UserOut —— 那些响应不能带出任何人的邮箱。
    """

    email: str | None = None
    #: False = 第三方建号（口令是随机串，没人知道），只能靠绑定的身份进来
    password_set: bool = False
    email_notify: bool = False
    #: 可信度 0–3（来源数量；站务固定 3）。权限不按等级细分。
    trust_level: int = 0
    trust_sources: list[str] = Field(default_factory=list)
    #: 第三方首登的临时账号名，可调用 PATCH /auth/handle 改一次
    handle_provisional: bool = False


class HandleIn(BaseModel):
    """第三方首登的临时账号名改成自己的；只允许一次。"""

    handle: str = Field(min_length=2, max_length=24)

    @field_validator("handle")
    @classmethod
    def _handle_ok(cls, v: str) -> str:
        low = v.lower()
        if not low[0].isascii() or not low[0].isalnum() or                 any(not (c.isascii() and (c.isalnum() or c in "-_")) for c in low[1:]):
            raise ValueError("账号名只能使用 a-z、0-9、- 和 _，且以字母或数字开头")
        if low in {"admin", "robowiki", "api", "mcp", "community", "account",
                   "root", "support", "staff", "system", "official"}:
            raise ValueError("这个账号名不可用")
        return low


class AccountUpdateIn(BaseModel):
    """本人可改的公开资料；邮箱/身份走验证流程，不在这里直接改。"""

    display_name: str | None = Field(default=None, min_length=1, max_length=32)
    bio: str | None = Field(default=None, max_length=500)
    avatar_hue: int | None = Field(default=None, ge=0, le=359)
    #: None = 清除自定义头像，回退到 avatar_hue 底色
    avatar_url: str | None = Field(default=None, max_length=500)
    email_notify: bool | None = None

    @field_validator("avatar_url")
    @classmethod
    def _avatar_ok(cls, v: str | None) -> str | None:
        return _normalize_avatar_url(v)


class PasswordSetIn(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class EmailChangeIn(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    #: 已设置密码的账号必须验证当前口令；第三方建号可不填
    password: str | None = Field(default=None, max_length=128)


class EmailChangeConfirmIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    #: 长寿命轮换凭据；每次刷新都会换新，旧值复用即撤销整条会话链。
    #: 可选默认值是为了兼容只返回 access_token 的内部构造（如独立脚本）。
    refresh_token: str | None = None
    user: AccountOut


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=512)


class LogoutIn(BaseModel):
    """退出登录：带 refresh_token 只撤销那一条会话链，否则撤销全部。"""

    refresh_token: str | None = Field(default=None, max_length=512)


class HandoffIn(BaseModel):
    """GitHub 回跳拿到的一次性 code（60 秒、只能换一次）。"""

    code: str = Field(min_length=8, max_length=256)


class SessionOut(BaseModel):
    """`GET /auth/sessions`：仍可用的 refresh 会话。"""

    id: int
    client: str = "web"
    created_at: datetime
    expires_at: datetime


class ProvidersOut(BaseModel):
    """服务端当前真正可用的登录渠道；前端据此决定按钮显示/禁用。"""

    email: bool = True
    github: bool = False
    wechat_mini: bool = False


class QrCreateOut(BaseModel):
    """`POST /auth/wechat/qr`：ticket 给前端轮询，qrcode 是 base64 图。"""

    ticket: str
    qrcode: str
    expires_in: int = 300


class QrConfirmIn(BaseModel):
    """小程序确认页提交：scene 里的 ticket + wx.login 的 code。"""

    ticket: str = Field(min_length=16, max_length=64)
    code: str = Field(min_length=1, max_length=128)


class QrStatusOut(BaseModel):
    """网页轮询结果；confirmed 时带一次性会话（TokenOut）。"""

    status: Literal["pending", "confirmed", "expired"]
    token: TokenOut | None = None


class WechatMiniIn(BaseModel):
    """小程序 `wx.login()` 拿到的 code；nickname 只是建号时的展示名。"""

    code: str = Field(min_length=1, max_length=128)
    nickname: str | None = Field(default=None, max_length=32)

    @field_validator("code")
    @classmethod
    def _code_ok(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("code 不能为空")
        return v


class IdentityOut(BaseModel):
    """一个已绑定的第三方身份。`subject` 是提供方侧的稳定 ID。"""

    provider: str
    subject: str
    email: str | None = None
    created_at: datetime


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
    #: 非空即「已解决」；对应 CommentOut.accepted
    accepted_comment_id: int | None = None
    created_at: datetime
    updated_at: datetime
    author: UserOut | None = None
    my_vote: int = 0


class PostPatchIn(BaseModel):
    """编辑帖子：只传要改的字段，`kind` 与 `part_id` 不可变。

    留空（不传）与显式 null 是两件事：只有传了的键才会被写回，
    所以 `rating: null` 能清掉评分，而不传 `rating` 则保持原值。
    """

    title: str | None = Field(default=None, min_length=4, max_length=120)
    body: str | None = Field(default=None, min_length=10, max_length=20000)
    tags: str | None = Field(default=None, max_length=80)
    rating: int | None = Field(default=None, ge=1, le=5)
    use_case: str | None = Field(default=None, max_length=16)
    own_hardware: bool | None = None
    total_price_cny: float | None = Field(default=None, ge=0, le=10_000_000)
    price_scope: str | None = Field(default=None, max_length=200)
    price_verified: bool | None = None


class AcceptIn(BaseModel):
    """采纳本楼的一条回答。"""

    comment_id: int


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
    #: 是否是本楼被采纳的答案
    accepted: bool = False
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


# ── 文档页评论（/wiki/comments）────────────────────────────────────────────
class WikiCommentIn(BaseModel):
    page: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    parent_id: int | None = None


class WikiCommentOut(BaseModel):
    """一条讨论。字段只增不删：前端已按 id/page/body/parent_id/created_at/author 组树。"""

    id: int
    page: str
    body: str
    parent_id: int | None = None
    root_id: int | None = None
    status: str = "visible"
    deleted: bool = False
    deleted_at: datetime | None = None
    created_at: datetime
    author: UserOut | None = None
    #: 兼容旧字段：站务是否已处置（status=hidden 时为 true）
    hidden: bool = False


# ── 通知 ────────────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    id: int
    type: str
    subject: str = ""
    body: str = ""
    link: str | None = None
    read_at: datetime | None = None
    created_at: datetime


class NotificationListOut(BaseModel):
    total: int
    unread: int
    limit: int
    offset: int
    items: list[NotificationOut]


# ── 媒体 ────────────────────────────────────────────────────────────────────
class MediaOut(BaseModel):
    id: str
    url: str
    content_type: str
    size: int


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


# ── 方案库 / 学习指南 ───────────────────────────────────────────────────────
class KeySpecOut(BaseModel):
    key: str
    label: str
    value: str


class BuildSummaryOut(BaseModel):
    id: str
    slug: str
    subtype: str | None = None
    subtype_label: str | None = None
    vendor: str | None = None
    vendor_cn: str | None = None
    model: str | None = None
    title: str | None = None
    url: str | None = None
    source_tier: str | None = None
    verified: bool = False
    last_checked: str | None = None
    price_cny: float | None = None
    image_url: str | None = None
    key_specs: list[KeySpecOut] = []
    web_path: str


class BuildDetailOut(BuildSummaryOut):
    specs: dict = {}
    notes: str = ""
    origin: str | None = None
    ecosystem: dict | None = None


class BuildListOut(BaseModel):
    total: int
    limit: int
    offset: int
    data_version: str | None = None
    items: list[BuildSummaryOut]


class LearnArticleOut(BaseModel):
    slug: str
    title: str
    summary: str | None = None
    tags: list[str] = []
    level: str | None = None
    minutes: int | None = None
    web_path: str


class LearnListOut(BaseModel):
    updated_at: str | None = None
    total: int
    items: list[LearnArticleOut]


# ── 账号数据导出（「我的数据可带走」）───────────────────────────────────────
class CommentExportOut(BaseModel):
    id: int
    post_id: int
    parent_id: int | None = None
    body: str
    score: int = 0
    hidden: bool = False
    created_at: datetime


class RatingExportOut(BaseModel):
    part_id: str
    part_title: str | None = None
    score: int
    own_hardware: bool = False
    usage_level: str = ""
    reason_tags: list[str] = []
    note: str = ""
    created_at: datetime
    updated_at: datetime


class SubmissionExportOut(BaseModel):
    id: int
    kind: str
    target_id: str | None = None
    payload: dict = {}
    evidence: dict = {}
    status: str
    revision: int
    created_at: datetime
    updated_at: datetime


class AccountExportOut(BaseModel):
    """只含本人内容；不含口令哈希、refresh token 等凭据。"""

    user: AccountOut
    posts: list[PostOut] = []
    comments: list[CommentExportOut] = []
    ratings: list[RatingExportOut] = []
    submissions: list[SubmissionExportOut] = []

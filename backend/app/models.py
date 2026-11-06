"""数据模型。

核心设计：**「评价」不是一张独立的表，而是挂在零件上的帖子**。
于是社区信息流、零件评价、整机方案共用同一套 Post / Comment / Vote，
只差 `kind` 与 `part_id`。少一套机制，少一处漂移。

实体取自开源社区项目的标准骨架（user / post / comment / vote / report / notification …），
收藏、修订仍不在本轮范围内。
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, Index, UniqueConstraint
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── 目录 ────────────────────────────────────────────────────────────────────
class Part(SQLModel, table=True):
    """目录条目。只由种子灌入，用户不能改。"""

    __tablename__ = "parts"

    id: str = Field(primary_key=True)
    category: str = Field(index=True)
    subtype: str = Field(index=True)
    vendor: str = Field(index=True)
    vendor_cn: str | None = None
    model: str
    title: str
    url: str | None = None
    source_tier: str = "B"
    verified: bool = False
    last_checked: str | None = None
    price_cny: float | None = None
    specs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    notes: str = ""
    origin: str | None = None
    search: str = Field(default="", index=True)


class Offer(SQLModel, table=True):
    __tablename__ = "offers"

    id: str = Field(primary_key=True)
    part_id: str | None = Field(default=None, foreign_key="parts.id", index=True)
    vendor: str | None = None
    kind: str                 # sponsor | coupon | discount | giveaway
    title: str
    detail: str = ""
    url: str | None = None
    starts_on: str | None = None
    expires_on: str | None = None
    demo: bool = False
    #: 厂商级优惠不适用的型号（JSON 数组）。例：灵足教育 9 折排除 EL05。
    #: 没有这一列，API 会把一个拿不到的价显示在卡片上。
    exclude_parts: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


# ── 社区 ────────────────────────────────────────────────────────────────────
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    handle: str = Field(index=True, unique=True)       # 登录名 / URL
    display_name: str
    email: str | None = Field(default=None, unique=True)
    email_verified: bool = False
    #: 是否接收站内通知的邮件副本（回复/审核/安全事件）；默认关闭，用户主动开
    email_notify: bool = False
    password_hash: str
    #: 是否设置过可用口令。第三方登录（GitHub / 小程序）建出来的账号拿着
    #: 一个没人知道的随机哈希，这里记 False —— 解绑最后一个身份前，
    #: 必须还有别的登录方式，否则账号就锁死了。
    password_set: bool = True
    bio: str = ""
    avatar_hue: int = 160                              # 头像底色，免上传
    is_staff: bool = False
    reputation: int = 0                                # 收到的赞之和，冗余字段
    #: 会话代次。access JWT 的 `se` 必须等于它；`logout-all` 自增一次即可
    #: 让该账号此前签发的**所有** access token 立刻失效（无需黑名单）。
    session_epoch: int = 0
    created_at: datetime = Field(default_factory=utcnow)

    #: 帖子数 / 评论数在个人页按需聚合，不落库


class EmailToken(SQLModel, table=True):
    """邮箱验证 / 找回密码的一次性令牌；只存 hash，不存原文。"""

    __tablename__ = "email_tokens"
    __table_args__ = (Index("ix_email_tokens_user_purpose", "user_id", "purpose"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    purpose: str = Field(index=True)          # verify | reset | change_email
    token_hash: str = Field(index=True, unique=True)
    #: 换绑邮箱时记录目标地址；只放在一次性令牌行里，确认后才写 users.email
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))
    expires_at: datetime = Field(index=True)
    used_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class EmailOutbox(SQLModel, table=True):
    """异步邮件队列：站内通知的邮件副本由 worker 发送并重试。"""

    __tablename__ = "email_outbox"
    __table_args__ = (Index("ix_email_outbox_status_next", "status", "next_at"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    to_addr: str = Field(index=True)
    subject: str
    text: str
    html: str | None = None
    kind: str = "notification"
    #: 同一事件只发一次；为空表示不去重
    dedupe_key: str | None = Field(default=None, unique=True, index=True)
    status: str = Field(default="pending", index=True)  # pending|running|done|failed
    attempts: int = 0
    next_at: datetime = Field(default_factory=utcnow, index=True)
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    sent_at: datetime | None = None


class RefreshToken(SQLModel, table=True):
    """一枚 refresh token（只存 hash）。一次登录 = 一个 family。

    轮换规则：每次 `/auth/refresh` 都把当前行标记 `used_at` 并签发同一
    family 的新行。若一个已用过的 refresh 再次出现，说明它被复制/窃取了，
    整条 family 立即撤销并 401 —— 正常客户端只会持有一条链的末端。
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_user_family", "user_id", "family"),
        Index("ix_refresh_expires", "expires_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    #: sha256(raw)；原文只回给客户端一次，不落库
    token_hash: str = Field(index=True, unique=True)
    #: 同一次登录轮换出来的 token 共享一个 family；复用检测按它整组撤销
    family: str = Field(index=True)
    #: 来源标签（web / console / mirror / mini / 来源 host），仅用于会话列表
    client: str = "web"
    expires_at: datetime = Field(index=True)
    used_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class HandoffCode(SQLModel, table=True):
    """GitHub 回跳的一次性 code。

    OAuth 回调不再把 JWT 放进 Location（那会进浏览器历史与反代日志）；
    改为 302 带一个 60 秒、只能换一次的 code，静态端用
    `POST /auth/handoff` 换 TokenOut。这里同样只存 hash。
    """

    __tablename__ = "auth_handoffs"
    __table_args__ = (Index("ix_handoff_expires", "expires_at"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    code_hash: str = Field(index=True, unique=True)
    #: 校验过白名单的 origin（scheme://host[:port]）
    return_to: str
    expires_at: datetime = Field(index=True)
    used_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Identity(SQLModel, table=True):
    """第三方身份。一个 user 可以绑多个（GitHub / 微信小程序 / 以后更多）。

    为什么是独立一张表而不是往 users 上加 `github_id`、`wechat_openid`：
    每接一个渠道就多一列、多一次迁移、多一处「这列可能为 NULL」；
    这里多接一个渠道只是多一行。

    `(provider, subject)` 唯一是整张表的核心约束：
      · provider —— `github` / `wechat_mini`，是我们自己的枚举；
      · subject  —— 提供方侧的稳定 ID（GitHub 数字 id / 微信 openid），
                    改昵称、改邮箱都不会变，所以它才是主键的一半。
    同一个人重复登录必须落在同一行上，靠数据库保证，而不是靠代码自查。
    """

    __tablename__ = "identities"
    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_identity_provider_subject"),
        Index("ix_identities_user_provider", "user_id", "provider"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    provider: str = Field(index=True)                  # github | wechat_mini
    subject: str = Field(index=True)                   # 提供方侧稳定 ID
    #: 提供方返回的邮箱（可能为空；微信小程序没有邮箱）
    email: str | None = Field(default=None, index=True)
    #: 提供方资料快照（不含 token / session_key —— 那是不该落库的密钥）
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Post(SQLModel, table=True):
    """一条帖子。kind 决定它出现在哪里：

    discussion — 社区讨论，可挂零件也可不挂
    review     — 零件评价，part_id 必填，带 rating
    build      — 整机方案，正文是 BOM 说明
    """

    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_kind_created", "kind", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(index=True, default="discussion")
    title: str
    body: str = ""
    author_id: int = Field(foreign_key="users.id", index=True)
    part_id: str | None = Field(default=None, foreign_key="parts.id", index=True)
    tags: str = ""                                     # 逗号分隔，够用
    # review 专用
    rating: int | None = None
    use_case: str | None = None
    own_hardware: bool = False
    # build 专用：整机报价必须三件套一起给（数字 + 覆盖范围 + 是否核实）
    # 只给一个数字的整机报价，比不给更有害。
    total_price_cny: float | None = None
    price_scope: str | None = None
    price_verified: bool = False
    # 统计（冗余，写入时维护）
    score: int = 0
    comment_count: int = 0
    view_count: int = 0
    pinned: bool = False
    #: 站务处置后隐藏；列表、详情与评分聚合都不再返回，站务仍可在后台查看
    hidden: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: int | None = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="posts.id", index=True)
    parent_id: int | None = Field(default=None, foreign_key="comments.id", index=True)
    author_id: int = Field(foreign_key="users.id", index=True)
    body: str
    score: int = 0
    hidden: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Notification(SQLModel, table=True):
    """站内通知：被回复、举报处置结果。

    刻意只做「写入即读」的最小集：不建订阅表、不发推送。通知是**结果**，
    不是事实源 —— 主流程（发评论/处置举报）必须先成功，通知写失败只记日志。
    `read_at` 为空即未读；列表与 unread_count 都按它过滤。
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)   # 收件人
    type: str = Field(index=True)                              # reply | moderation
    subject: str = ""                                          # 一句话标题
    body: str = ""                                             # 摘要，不含全文
    #: 站内相对链接（例：/parts/actuator/cubemars#comment-12）
    link: str | None = None
    read_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Media(SQLModel, table=True):
    """用户上传的图片（评论配图）。

    只存元数据，文件落在 `settings.media_dir`；id 是 32 位 uuid hex，
    既是主键也是文件名（扩展名按实际类型补），不做目录分片 —— 单机
    规模用不上，分片会让备份和迁移多一层映射。
    """

    __tablename__ = "media"

    id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    filename: str                                      # 磁盘文件名（id + 扩展名）
    original_name: str = ""                            # 客户端原名，仅用于展示
    content_type: str                                  # image/jpeg | image/png | image/webp
    size: int = 0
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Vote(SQLModel, table=True):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("user_id", "target_kind", "target_id", name="uq_vote_once"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    target_kind: str                                   # post | comment
    target_id: int = Field(index=True)
    value: int = 1                                     # +1 / -1
    created_at: datetime = Field(default_factory=utcnow)


class Report(SQLModel, table=True):
    """用户举报。举报不改可见性；站务处置（hide/dismiss）才产生状态变更。"""

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("reporter_id", "target_kind", "target_id",
                         name="uq_report_once"),
        Index("ix_reports_status_created", "status", "created_at"),
        Index("ix_reports_target", "target_kind", "target_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    reporter_id: int = Field(foreign_key="users.id", index=True)
    target_kind: str                                   # post | comment | wiki_comment
    target_id: int = Field(index=True)
    reason: str                                        # spam | abuse | misinfo | other
    detail: str = ""
    status: str = Field(default="open", index=True)    # open | resolved | dismissed
    resolution_note: str = ""
    resolver_id: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=utcnow, index=True)
    resolved_at: datetime | None = None


class PartEdit(SQLModel, table=True):
    """零件字段的修改记录 —— 这就是「数据来源」的可追溯部分。

    每次后台改一个字段写一行：谁改的、从什么改成什么、依据是什么。
    有这一张表，任何数字都能回答「它什么时候、被谁、凭什么被改成了现在这样」。
    """

    __tablename__ = "part_edits"
    __table_args__ = (Index("ix_edits_part_created", "part_id", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    part_id: str = Field(foreign_key="parts.id", index=True)
    field: str                                         # specs.tau_peak_Nm / price_cny / source_tier …
    old_value: str | None = None
    new_value: str | None = None
    editor_id: int | None = Field(default=None, foreign_key="users.id")
    note: str = ""                                     # 依据：哪份 datasheet 的哪一页 / 哪封厂商邮件
    source_url: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class WikiComment(SQLModel, table=True):
    """文档页的讨论串 —— 一个页面一条线程，挂在 page 路径上。

    形态参考 YunQianDoc（VitePress + giscus）：每篇文章底下就能说话，
    不需要先进「论坛」再找板块。这里用自托管实现，因为 giscus 需要
    一个公开的 GitHub 仓库并开启 Discussions。

    三级字段各管一件事，互不替代：
      · `parent_id` —— 回复谁（直接父节点，前端据此组树）；
      · `root_id`   —— 属于哪条根讨论（分页、跨层回复、通知去重都按它）；
      · `status`    —— visible / pending / hidden。pending 只有作者与站务
                       能看到（内容安全拦截或待人工复核）；
      · `deleted_at`—— 软删除。删父节点不动子节点，页面用占位节点保留线程。
    `hidden` 保留为站务处置的兼容字段：hide 时同时写 status=hidden，
    旧的只读 `hidden == False` 的查询不会因此放出已处置内容。
    """

    __tablename__ = "wiki_comments"
    __table_args__ = (
        Index("ix_wiki_page_created", "page", "created_at"),
        Index("ix_wiki_root_created", "root_id", "created_at"),
        Index("ix_wiki_page_status", "page", "status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    page: str = Field(index=True)                      # 例：parts/actuator/cubemars
    user_id: int = Field(foreign_key="users.id", index=True)
    body: str
    parent_id: int | None = Field(default=None, foreign_key="wiki_comments.id")
    #: 根讨论 id；根节点为 NULL（读取时按 parent 链回填，兼容旧数据）
    root_id: int | None = Field(default=None, foreign_key="wiki_comments.id",
                                index=True)
    status: str = Field(default="visible", index=True)  # visible | pending | hidden
    hidden: bool = Field(default=False, index=True)     # 兼容：站务处置标记
    deleted_at: datetime | None = Field(default=None, index=True)
    deleted_by: int | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=utcnow)


class Rating(SQLModel, table=True):
    """零件评分：一人一件一票，可改。

    为什么评分必须自托管而不能靠 giscus：giscus 只有 reaction，没有分档；
    而「这个件值不值」需要一个能聚合、能画分布、能进排序的数。
    所以评分进本站库，评论继续交给 giscus（那道 GitHub 账号门槛由它兜住）。

    唯一约束保证「一人一票」，重复提交是**改分**不是刷分。
    """

    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "part_id", name="uq_rating_once"),
        Index("ix_rating_part", "part_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    part_id: str = Field(foreign_key="parts.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    score: int                                          # 1–5
    #: 打分的依据（是否装过机）。没有这个字段，5 分可能来自「看着不错」
    own_hardware: bool = False
    #: 使用时长分档：long（>6 个月）/ short（<1 个月）/ unboxed（只开箱）。
    #: 与 own_hardware 互补：装过机但只用了三天，参考价值低于用了半年。
    usage_level: str = ""
    #: 打分的理由标签，逗号分隔、最多 3 个。空表示「没给理由」，
    #: 这类票仍计入均分，但不进标签分布——理由是可聚合的解释，不是必填噪音。
    reason_tags: str = ""
    note: str = ""                                      # 一句话理由，可空
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Reproduction(SQLModel, table=True):
    """方案复现记录：一条 = 一次真实的复现尝试。

    为什么不给方案打 5 星：同一套结构换个人装，结果只有「成 / 部分成 / 没成」，
    再加上「我改了什么」。评分是偏好，复现是事实，两者不能混。
    """

    __tablename__ = "reproductions"
    __table_args__ = (
        UniqueConstraint("user_id", "build_id", name="uq_reproduction_once"),
        Index("ix_reproduction_build", "build_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    #: 方案 id（数据仓 robots 的 id，非外键：方案不在本站库里）
    build_id: str = Field(index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    #: success / partial / failed
    outcome: str
    #: 相对原方案改了什么（换了电机、改了减速比…），空表示照做
    changes: str = ""
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# ── 数据变更：提交 → 审核 → outbox ───────────────────────────────────────────
class Submission(SQLModel, table=True):
    """目录字段的变更提案。审核通过也不直接改库；由 outbox 走 PR → release。"""

    __tablename__ = "submissions"
    __table_args__ = (Index("ix_submissions_status_created", "status", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    kind: str = Field(default="part_patch", index=True)
    target_id: str | None = Field(default=None, index=True)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    evidence: dict = Field(default_factory=dict, sa_column=Column(JSON))
    submitter_id: int | None = Field(default=None, foreign_key="users.id", index=True)
    status: str = Field(default="pending", index=True)
    revision: int = 1
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)


class SubmissionReview(SQLModel, table=True):
    """审核记录：只追加，不覆盖。"""

    __tablename__ = "submission_reviews"
    __table_args__ = (Index("ix_subreview_submission", "submission_id", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="submissions.id", index=True)
    reviewer_id: int | None = Field(default=None, foreign_key="users.id")
    decision: str                                      # accepted | rejected
    reason_code: str = ""
    note: str = ""
    created_at: datetime = Field(default_factory=utcnow)


class Outbox(SQLModel, table=True):
    """DB → GitHub 的可靠副作用。idempotency_key 防止重复开 PR。"""

    __tablename__ = "outbox"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_outbox_idempotency"),
        Index("ix_outbox_status_next", "status", "next_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    submission_id: int | None = Field(default=None, foreign_key="submissions.id", index=True)
    action: str = "part_patch"
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    idempotency_key: str = Field(index=True)
    status: str = Field(default="pending", index=True)
    attempts: int = 0
    next_at: datetime = Field(default_factory=utcnow, index=True)
    last_error: str | None = None
    #: 发布结果（PR URL / dry-run 产物路径 / 提交 SHA）
    result: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)

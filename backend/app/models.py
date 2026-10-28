"""数据模型。

核心设计：**「评价」不是一张独立的表，而是挂在零件上的帖子**。
于是社区信息流、零件评价、整机方案共用同一套 Post / Comment / Vote，
只差 `kind` 与 `part_id`。少一套机制，少一处漂移。

实体取自开源社区项目的标准骨架（user / post / comment / vote / badge …），
精简掉本轮不需要的通知、收藏、举报、修订。
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
    password_hash: str
    bio: str = ""
    avatar_hue: int = 160                              # 头像底色，免上传
    is_staff: bool = False
    reputation: int = 0                                # 收到的赞之和，冗余字段
    created_at: datetime = Field(default_factory=utcnow)

    #: 帖子数 / 评论数在个人页按需聚合，不落库


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
    """

    __tablename__ = "wiki_comments"
    __table_args__ = (Index("ix_wiki_page_created", "page", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    page: str = Field(index=True)                      # 例：parts/actuator/cubemars
    user_id: int = Field(foreign_key="users.id", index=True)
    body: str
    parent_id: int | None = Field(default=None, foreign_key="wiki_comments.id")
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
    note: str = ""                                      # 一句话理由，可空
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

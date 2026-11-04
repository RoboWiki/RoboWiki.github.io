#!/usr/bin/env python3
"""把 giscus（GitHub Discussions）历史讨论离线导入 `wiki_comments`。

为什么是离线脚本：
    giscus 的数据在 GitHub，本站没有 API 凭据也不该在部署机上联网抓取。
    先在有权限的机器上用 GraphQL 导出成 JSON，再把文件拷过来导入。
    本脚本**不发起任何网络请求**，只读本地 JSON、可选写本地数据库。

输入：
    * GraphQL 导出：`{"data":{"repository":{"discussions":{"nodes":[...]}}}}`
    * 简化导出：`{"discussions":[...]}` 或直接一个 discussion 数组
    * 每条 discussion 需有 `title`（giscus 的 term/pathname 就存在标题里）、
      `comments`（`{"nodes":[...]}` 或数组）；回复可以放在 `replies` 下。

映射：
    * `--mapping pathname`（默认）：标题就是页路径，如 `/parts/actuator/dm`；
    * `--mapping url`：标题是完整 URL，取 path；
    * `--mapping term`：同 pathname，只是把标题当 giscus `specific` 的 term；
    * `--mapping title`：标题是人类标题，按 slug 规则转成 page（建议配 `--page-map`）。
    `--page-map` 可以按 discussion number / title / url 精确覆盖，优先级最高。

作者：
    giscus 只给 `author.login`，没有本站 user id。导入时为每个登录名建一个
    占位账号 `giscus-<login>`（`password_set=False`、无邮箱），并写一条
    `identities(provider="giscus", subject=<login>)` 便于以后合并。
    占位账号不能登录；真正的 GitHub 绑定要在用户登录后人工合并。

最小字段：
    目标表当前只有 `page/body/parent_id/created_at/user_id`，没有
    `source`/`external_ref` 列。脚本把来源与外部 id 保留在诊断输出与
    `--ledger` 里；等 P1 迁移加上 `source`/`external_ref` 与唯一索引后，
    应改为直接写列并删掉 ledger 兜底。**不要**在本次操作里改表结构。

用法：
    # 只看统计与前几条（默认就是 dry-run）
    python scripts/import_giscus.py --input giscus.json --dry-run

    # 输出规范化 JSONL，便于人工核对
    python scripts/import_giscus.py --input giscus.json --format jsonl

    # 真正写库（先备份）
    python scripts/import_giscus.py --input giscus.json --apply \
        --database-url "postgresql+psycopg://robowiki:***@127.0.0.1:5432/robowiki" \
        --ledger .giscus-import-ledger.json

安全：
    * 默认 dry-run；`--apply` 必须显式给出。
    * 目标页已有评论时拒绝写入，除非 `--allow-nonempty`。
    * 同一 external_ref 或同一 (page, body, created_at) 已存在则跳过，
      重复执行不会无限复制；但极短时间内的相同正文仍可能被当成两条。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import secrets
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

SOURCE = "giscus"
ROOT = pathlib.Path(__file__).resolve().parents[1]


# ── 输入解析 ─────────────────────────────────────────────────────────────────
def _nodes(value: Any) -> list[dict]:
    """把 `{"nodes":[...]}` / 数组 / 单个对象统一成 list。"""
    if value is None:
        return []
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        if isinstance(value.get("nodes"), list):
            return [x for x in value["nodes"] if isinstance(x, dict)]
        if isinstance(value.get("edges"), list):
            return [e["node"] for e in value["edges"]
                    if isinstance(e, dict) and isinstance(e.get("node"), dict)]
        return [value]
    return []


def load_discussions(doc: Any) -> list[dict]:
    """兼容 GraphQL 导出、`{"discussions":...}` 与裸数组。"""
    if isinstance(doc, list):
        return [d for d in doc if isinstance(d, dict)]
    if not isinstance(doc, dict):
        raise ValueError("输入必须是 JSON 对象或数组")
    repo = (doc.get("data") or {}).get("repository") or {}
    for candidate in (repo.get("discussions"), doc.get("discussions"),
                      doc.get("repository", {}).get("discussions")
                      if isinstance(doc.get("repository"), dict) else None):
        if candidate is not None:
            return _nodes(candidate)
    if isinstance(doc.get("nodes"), list):
        return _nodes(doc)
    raise ValueError("找不到 discussions：需要 GraphQL data.repository.discussions"
                     " 或顶层 discussions/nodes")


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _author(comment: dict) -> tuple[str | None, str | None]:
    author = comment.get("author")
    if isinstance(author, dict):
        return _text(author.get("login")) or None, _text(author.get("avatarUrl")) or None
    if isinstance(author, str):
        return _text(author) or None, None
    # 简化导出常见字段
    return _text(comment.get("author_login")) or None, None


def _created(comment: dict) -> datetime:
    raw = (comment.get("createdAt") or comment.get("created_at")
           or comment.get("publishedAt") or "")
    if not raw:
        return datetime.now(timezone.utc)
    return parse_dt(str(raw))


def parse_dt(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(s)
    except ValueError:
        # 只给日期的情况
        value = datetime.fromisoformat(s[:10] + "T00:00:00+00:00")
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _external_ref(comment: dict, fallback: str) -> str:
    for key in ("id", "node_id", "databaseId", "database_id"):
        value = comment.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


# ── page / term ─────────────────────────────────────────────────────────────
def _slug_title(raw: str) -> str:
    text = unicodedata.normalize("NFKC", raw).strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff/-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-/")
    return text or "index"


def normalize_page(raw: str, *, mapping: str, strip_prefix: str = "") -> str:
    """把 giscus 的 term/pathname/url/标题归一成站内 page。"""
    value = (raw or "").strip()
    if not value:
        return "index"
    if mapping == "url" or value.lower().startswith(("http://", "https://")):
        path = urlparse(value).path or "/"
    else:
        path = value.split("?", 1)[0].split("#", 1)[0]
        if path.lower().startswith(("http://", "https://")):
            path = urlparse(path).path or "/"
    path = unquote(path)

    prefix = strip_prefix.rstrip("/")
    if prefix and (path == prefix or path.startswith(prefix + "/")):
        path = path[len(prefix):]
    path = path.strip("/")
    for suffix in (".html", ".htm", ".md"):
        if path.lower().endswith(suffix):
            path = path[: -len(suffix)]
    if mapping == "title":
        return _slug_title(path)
    # pathname/term：保留层级，去掉空段与 ..
    parts = [p for p in path.split("/") if p and p not in (".", "..")]
    return "/".join(parts) or "index"


@dataclass
class Row:
    page: str
    body: str
    created_at: datetime
    external_ref: str
    parent_ref: str | None
    author_login: str | None
    author_avatar: str | None
    discussion_number: int | None
    discussion_title: str
    discussion_url: str | None
    source: str = SOURCE

    def as_dict(self) -> dict:
        return {
            "page": self.page,
            "body": self.body,
            "parent_ref": self.parent_ref,
            # P1 加列后：这两项直接写 wiki_comments.source / external_ref
            "source": self.source,
            "external_ref": self.external_ref,
            "author": {"login": self.author_login, "avatar_url": self.author_avatar},
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
            "discussion": {
                "number": self.discussion_number,
                "title": self.discussion_title,
                "url": self.discussion_url,
            },
        }


@dataclass
class BuildStats:
    discussions: int = 0
    pages: set[str] = field(default_factory=set)
    comments: int = 0
    roots: int = 0
    replies: int = 0
    skipped_empty: int = 0
    skipped_orphan_reply: int = 0
    truncated: int = 0
    authors: set[str] = field(default_factory=set)


def _override_page(disc: dict, term: str, mapping: str, strip_prefix: str,
                   page_map: dict) -> str:
    number = disc.get("number")
    for key in ((str(number) if number is not None else ""), term,
                _text(disc.get("page")), _text(disc.get("url"))):
        if key and key in page_map:
            return normalize_page(str(page_map[key]), mapping="pathname",
                                  strip_prefix=strip_prefix)
    explicit = _text(disc.get("page")) or _text(disc.get("term"))
    if explicit:
        return normalize_page(explicit, mapping="pathname",
                              strip_prefix=strip_prefix)
    return normalize_page(term, mapping=mapping, strip_prefix=strip_prefix)


def build_rows(discussions: Iterable[dict], *, mapping: str = "pathname",
               strip_prefix: str = "", page_map: dict | None = None,
               max_body: int = 0, limit: int = 0) -> tuple[list[Row], BuildStats]:
    page_map = page_map or {}
    stats = BuildStats()
    rows: list[Row] = []
    seen_refs: set[str] = set()

    def walk(comments: Any, *, page: str, parent_ref: str | None,
             disc: dict, number: int | None, title: str, url: str | None,
             index_prefix: str) -> None:
        for idx, comment in enumerate(_nodes(comments)):
            if limit and len(rows) >= limit:
                return
            fallback = f"{number if number is not None else 'x'}:{index_prefix}{idx}"
            ref = _external_ref(comment, fallback)
            body = comment.get("body")
            body = body if isinstance(body, str) else _text(comment.get("bodyHTML"))
            body = body.strip()
            if not body:
                stats.skipped_empty += 1
                continue
            if max_body and len(body) > max_body:
                body = body[:max_body].rstrip() + "\n\n…（导入时截断）"
                stats.truncated += 1
            if parent_ref and parent_ref not in seen_refs:
                # 父评论被跳过（空正文/被删），子评论没有合法挂载点
                stats.skipped_orphan_reply += 1
                continue
            login, avatar = _author(comment)
            if login:
                stats.authors.add(login)
            rows.append(Row(
                page=page, body=body, created_at=_created(comment),
                external_ref=ref, parent_ref=parent_ref,
                author_login=login, author_avatar=avatar,
                discussion_number=number, discussion_title=title,
                discussion_url=url,
            ))
            seen_refs.add(ref)
            stats.comments += 1
            if parent_ref:
                stats.replies += 1
            else:
                stats.roots += 1
            walk(comment.get("replies"), page=page, parent_ref=ref, disc=disc,
                 number=number, title=title, url=url,
                 index_prefix=f"{index_prefix}{idx}.")

    for disc in discussions:
        stats.discussions += 1
        title = _text(disc.get("title")) or _text(disc.get("name"))
        term = _text(disc.get("term")) or _text(disc.get("page")) or title
        page = _override_page(disc, term, mapping, strip_prefix, page_map)
        stats.pages.add(page)
        number = disc.get("number")
        url = _text(disc.get("url")) or None
        walk(disc.get("comments") or disc.get("posts"), page=page,
             parent_ref=None, disc=disc,
             number=number if isinstance(number, int) else None,
             title=title, url=url, index_prefix="")
        if limit and len(rows) >= limit:
            break

    return rows, stats


# ── 写库（只在 --apply）──────────────────────────────────────────────────────
class ImportAbort(Exception):
    """可预期的拒绝（目标页非空、库缺列等）；由 CLI 转成退出码 3。"""


def _slug_handle(login: str | None) -> str:
    if not login:
        return "giscus-anon"
    text = unicodedata.normalize("NFKC", login).strip().lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text).strip("-")
    if not text:
        text = "u" + hashlib.sha1((login or "").encode()).hexdigest()[:8]
    return f"giscus-{text[:12].strip('-')}"


def _apply(rows: list[Row], *, database_url: str, ledger_path: pathlib.Path | None,
           allow_nonempty: bool) -> dict:
    # 延迟导入：dry-run 不需要后端依赖
    if str(ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT / "backend"))
    try:
        from sqlmodel import Session, create_engine, select  # noqa: WPS433

        from app.core.security import hash_password  # noqa: WPS433
        from app.models import Identity, User, WikiComment  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover - 依赖缺失时的人工提示
        raise ImportAbort(
            "写库需要后端依赖：pip install -r backend/requirements.txt") from exc

    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}
    engine = create_engine(database_url, connect_args=connect_args)

    ledger: dict[str, int] = {}
    if ledger_path and ledger_path.exists():
        raw = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger = {str(k): int(v) for k, v in (raw.get("comments") or {}).items()}

    stats = {
        "inserted": 0, "skipped_existing": 0, "skipped_ledger": 0,
        "users_created": 0, "users_reused": 0, "orphan_replies": 0,
    }
    pages = sorted({r.page for r in rows})
    # 占位账号永远不能登录（password_set=False），一次哈希供所有占位账号复用，
    # 避免每个作者跑一遍 240k 次 PBKDF2。
    placeholder_hash = hash_password(secrets.token_urlsafe(32))

    with Session(engine) as db:
        # 台账里的 id 可能已被删库/换库：失效项丢掉，按新数据重新导入
        ledger_pages: set[str] = set()
        for ref, comment_id in list(ledger.items()):
            row = db.get(WikiComment, comment_id)
            if row is None:
                del ledger[ref]
            else:
                ledger_pages.add(row.page)

        if not allow_nonempty:
            for page in pages:
                if page in ledger_pages:
                    continue
                if db.exec(select(WikiComment.id)
                           .where(WikiComment.page == page).limit(1)).first():
                    raise ImportAbort(
                        f"目标页已有评论：{page}。先备份并确认这是首次导入；"
                        "确实要追加时加 --allow-nonempty。")

        def placeholder(login: str | None, avatar: str | None) -> User:
            # GitHub 登录名大小写不敏感：subject 统一小写，避免 Alice/alice 建两个号
            subject = (login or "(deleted)").lower()
            ident = db.exec(select(Identity).where(
                Identity.provider == SOURCE,
                Identity.subject == subject).limit(1)).first()
            if ident is not None:
                user = db.get(User, ident.user_id)
                if user is not None:
                    stats["users_reused"] += 1
                    return user

            handle = _slug_handle(login)
            user = db.exec(select(User).where(User.handle == handle)).first()
            if user is not None:
                # 已有同名的真人账号：绝不复用，避免把历史评论挂到别人名下
                suffix = hashlib.sha1(subject.encode()).hexdigest()[:6]
                handle = f"{handle[:24]}-{suffix}"
                user = db.exec(select(User).where(User.handle == handle)).first()
            if user is None:
                user = User(
                    handle=handle,
                    display_name=(login or "giscus 已注销用户")[:32],
                    email=None,
                    password_hash=placeholder_hash,
                    password_set=False,
                    bio="由 giscus 历史讨论导入的占位账号",
                )
                db.add(user)
                db.flush()
                stats["users_created"] += 1
            else:
                stats["users_reused"] += 1
            db.add(Identity(
                user_id=user.id, provider=SOURCE, subject=subject,
                email=None,
                raw={"login": login, "avatar_url": avatar,
                     "imported_from": "giscus"},
            ))
            db.flush()
            return user

        id_map: dict[str, int] = {}
        for row in rows:
            if row.external_ref in ledger:
                stats["skipped_ledger"] += 1
                id_map[row.external_ref] = ledger[row.external_ref]
                continue
            parent_id = None
            if row.parent_ref is not None:
                parent_id = id_map.get(row.parent_ref)
                if parent_id is None:
                    stats["orphan_replies"] += 1
                    continue
            # 没有 source/external_ref 唯一索引时的兜底去重
            dup = db.exec(select(WikiComment).where(
                WikiComment.page == row.page,
                WikiComment.body == row.body,
                WikiComment.created_at == row.created_at,
            ).limit(1)).first()
            if dup is not None:
                stats["skipped_existing"] += 1
                id_map[row.external_ref] = int(dup.id)
                continue
            user = placeholder(row.author_login, row.author_avatar)
            comment = WikiComment(
                page=row.page, user_id=user.id, body=row.body,
                parent_id=parent_id, created_at=row.created_at,
            )
            db.add(comment)
            db.flush()
            id_map[row.external_ref] = int(comment.id)
            stats["inserted"] += 1

        db.commit()

    if ledger_path:
        payload = {"version": 1, "source": SOURCE, "comments": id_map}
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = ledger_path.with_suffix(ledger_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(ledger_path)

    return stats


# ── CLI ─────────────────────────────────────────────────────────────────────
def _load_page_map(path: str | None) -> dict:
    if not path:
        return {}
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("--page-map 必须是 {key: page} 的 JSON 对象")
    return {str(k): str(v) for k, v in data.items()}


def main(argv: list[str] | None = None) -> int:
    # Windows 控制台默认 GBK：统一按 UTF-8 输出，JSONL 才能稳定管道传输
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description="离线导入 giscus Discussions 到 wiki_comments（不联网）")
    ap.add_argument("--input", required=True, help="GraphQL/JSON 导出文件")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="只解析与打印，不写库（默认）")
    mode.add_argument("--apply", action="store_true", help="真正写库")
    ap.add_argument("--database-url", default="",
                    help="apply 时的 SQLAlchemy URL；缺省读 ROBOWIKI_DATABASE_URL")
    ap.add_argument("--mapping", choices=("pathname", "url", "term", "title"),
                    default="pathname", help="标题如何映射到 page")
    ap.add_argument("--strip-prefix", default="",
                    help="去掉路径前缀，如 /docs")
    ap.add_argument("--page-map", default="",
                    help="精确覆盖：{discussion number/title/url: page}")
    ap.add_argument("--max-body", type=int, default=0,
                    help="正文上限；0 = 不截断")
    ap.add_argument("--limit", type=int, default=0,
                    help="最多导入多少条评论；0 = 全部")
    ap.add_argument("--format", choices=("table", "jsonl"), default="table",
                    help="dry-run 输出格式")
    ap.add_argument("--sample", type=int, default=5,
                    help="table 模式打印多少条样例")
    ap.add_argument("--ledger", default="",
                    help="apply 时的 external_ref → 新 id 台账（JSON）")
    ap.add_argument("--allow-nonempty", action="store_true",
                    help="目标页已有评论时仍然追加（默认拒绝）")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.input)
    if not path.is_file():
        raise SystemExit(f"找不到输入文件：{path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        discussions = load_discussions(doc)
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"解析失败：{exc}") from exc

    rows, stats = build_rows(
        discussions, mapping=args.mapping, strip_prefix=args.strip_prefix,
        page_map=_load_page_map(args.page_map), max_body=max(0, args.max_body),
        limit=max(0, args.limit))

    if args.format == "jsonl" or not args.apply:
        if args.format == "jsonl":
            for row in rows:
                print(json.dumps(row.as_dict(), ensure_ascii=False))
        else:
            print(f"discussions : {stats.discussions}")
            print(f"pages       : {len(stats.pages)}")
            print(f"comments    : {stats.comments}"
                  f"（roots {stats.roots} / replies {stats.replies}）")
            print(f"authors     : {len(stats.authors)}")
            print(f"skipped     : empty {stats.skipped_empty}, "
                  f"orphan_reply {stats.skipped_orphan_reply}, "
                  f"truncated {stats.truncated}")
            for row in rows[: max(0, args.sample)]:
                preview = row.body.replace("\n", " ")[:60]
                print(f"  - [{row.page}] {row.author_login or '(deleted)'}"
                      f" {row.created_at:%Y-%m-%d} {preview}")

    if not args.apply:
        print("dry-run：未写数据库。确认后加 --apply。", file=sys.stderr)
        return 0

    database_url = args.database_url.strip()
    if not database_url:
        database_url = (os.environ.get("ROBOWIKI_DATABASE_URL") or "").strip()
    if not database_url:
        raise SystemExit("--apply 需要 --database-url 或 ROBOWIKI_DATABASE_URL")
    if not rows:
        print("没有可导入的评论。", file=sys.stderr)
        return 0

    ledger = pathlib.Path(args.ledger) if args.ledger else None
    try:
        result = _apply(rows, database_url=database_url, ledger_path=ledger,
                        allow_nonempty=args.allow_nonempty)
    except ImportAbort as exc:
        print(f"已停止：{exc}", file=sys.stderr)
        return 3
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

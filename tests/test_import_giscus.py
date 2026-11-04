"""giscus 离线导入脚本：解析、page/term 映射、父评论、写库幂等。

这些都是“导错一次就很难回头”的点：
  · 标题里的 pathname 带前导斜杠 / .html / 查询串，直接入库会让讨论挂错页；
  · 回复必须先于父评论落库，否则 parent_id 丢失；
  · 重复执行不能把同一批历史评论复制两遍。
脚本本身不联网；测试也只读本地 JSON 与临时 SQLite。
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "import_giscus.py"

sys.path.insert(0, str(ROOT / "backend"))


def _comment(cid, body, when, login="alice", replies=None):
    return {
        "id": cid,
        "body": body,
        "createdAt": when,
        "author": {"login": login} if login else None,
        "replies": {"nodes": replies or []},
    }


@pytest.fixture()
def graphql_export(tmp_path):
    doc = {
        "data": {"repository": {"discussions": {"nodes": [
            {
                "number": 1,
                "title": "/parts/actuator/dm",
                "url": "https://github.com/RoboWiki/RoboWiki.github.io/discussions/1",
                "comments": {"nodes": [
                    _comment("DC_1", "第一条顶层", "2026-10-01T10:00:00Z",
                             replies=[
                                 _comment("DC_2", "回复第一条",
                                          "2026-10-01T10:05:00Z", login="bob"),
                             ]),
                    _comment("DC_3", "", "2026-10-01T10:06:00Z"),
                    _comment("DC_4", "第二条顶层", "2026-10-01T10:10:00Z"),
                ]},
            },
            {
                "number": 2,
                "title": "parts/imu/bno085",
                "comments": [
                    _comment("DC_5", "另一页的讨论", "2026-10-02T08:00:00Z",
                             login=None),
                ],
            },
        ]}}}
    }
    p = tmp_path / "giscus.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p


def _run(*args, env=None):
    full_env = os.environ.copy()
    full_env.setdefault("ROBOWIKI_SECRET_KEY", "test-secret-key-at-least-32-bytes-long-0000")
    full_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", env=full_env)


def test_dry_run_maps_pages_and_parents(graphql_export):
    r = _run("--input", graphql_export, "--dry-run", "--format", "jsonl")
    assert r.returncode == 0, r.stderr
    rows = [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
    assert len(rows) == 4

    by_ref = {x["external_ref"]: x for x in rows}
    assert by_ref["DC_1"]["page"] == "parts/actuator/dm"
    assert by_ref["DC_1"]["parent_ref"] is None
    assert by_ref["DC_2"]["parent_ref"] == "DC_1"
    assert by_ref["DC_5"]["page"] == "parts/imu/bno085"
    assert by_ref["DC_5"]["author"]["login"] is None
    assert by_ref["DC_1"]["source"] == "giscus"
    # 空正文被跳过，不占位
    assert "DC_3" not in by_ref
    # 父评论先于子评论
    order = [x["external_ref"] for x in rows]
    assert order.index("DC_1") < order.index("DC_2")


def test_url_and_page_map(tmp_path):
    doc = {"discussions": [
        {"number": 7,
         "title": "https://robowiki.org.cn/docs/parts/actuator/dm.html?utm=x",
         "comments": [_comment("D1", "url 映射", "2026-10-03T00:00:00Z")]},
        {"number": 8, "title": "Some Human Title",
         "comments": [_comment("D2", "page-map 覆盖", "2026-10-03T00:00:00Z")]},
    ]}
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    pm = tmp_path / "map.json"
    pm.write_text(json.dumps({"Some Human Title": "/manual/page"}), encoding="utf-8")

    r = _run("--input", inp, "--format", "jsonl", "--mapping", "url",
             "--strip-prefix", "/docs", "--page-map", pm)
    assert r.returncode == 0, r.stderr
    rows = [json.loads(x) for x in r.stdout.splitlines() if x.strip()]
    pages = {x["external_ref"]: x["page"] for x in rows}
    assert pages["D1"] == "parts/actuator/dm"
    # 第 1 条按 url 映射；第 2 条被 page-map 命中（key 是原始标题）
    assert pages["D2"] == "manual/page"


def _make_schema(db_path: pathlib.Path):
    from sqlmodel import SQLModel, create_engine
    import app.models  # noqa: F401  注册所有表
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def test_apply_is_idempotent(graphql_export, tmp_path):
    db_path = tmp_path / "test.db"
    engine = _make_schema(db_path)
    ledger = tmp_path / "ledger.json"

    r = _run("--input", graphql_export, "--apply",
             "--database-url", f"sqlite:///{db_path}", "--ledger", ledger)
    assert r.returncode == 0, r.stderr
    result = json.loads(r.stdout.strip().splitlines()[-1])
    assert result["inserted"] == 4
    assert result["users_created"] == 3      # alice / bob / 匿名

    from sqlmodel import Session, select
    from app.models import Identity, User, WikiComment
    with Session(engine) as db:
        rows = db.exec(select(WikiComment).order_by(WikiComment.created_at)).all()
        assert len(rows) == 4
        assert sum(1 for x in rows if x.parent_id is None) == 3
        parent = next(x for x in rows if x.body == "第一条顶层")
        reply = next(x for x in rows if x.body == "回复第一条")
        assert reply.parent_id == parent.id
        assert db.exec(select(User).where(User.handle == "giscus-alice")).first()
        # 占位账号不能登录
        assert db.exec(select(User).where(User.handle == "giscus-bob")).first().password_set is False
        assert db.exec(select(Identity).where(Identity.provider == "giscus")).first()
    assert ledger.is_file()

    # 同一台账重跑：不再复制
    r2 = _run("--input", graphql_export, "--apply",
              "--database-url", f"sqlite:///{db_path}", "--ledger", ledger)
    assert r2.returncode == 0, r2.stderr
    result2 = json.loads(r2.stdout.strip().splitlines()[-1])
    assert result2["inserted"] == 0
    assert result2["skipped_ledger"] == 4
    with Session(engine) as db:
        assert len(db.exec(select(WikiComment)).all()) == 4


def test_refuses_nonempty_page_without_flag(graphql_export, tmp_path):
    db_path = tmp_path / "test.db"
    engine = _make_schema(db_path)

    from sqlmodel import Session, select
    from app.core.security import hash_password
    from app.models import User, WikiComment
    from datetime import datetime, timezone
    with Session(engine) as db:
        u = User(handle="someone", display_name="someone",
                 password_hash=hash_password("secret123"), password_set=True)
        db.add(u)
        db.flush()
        db.add(WikiComment(page="parts/actuator/dm", user_id=u.id,
                           body="已有的站内评论",
                           created_at=datetime(2026, 9, 1, tzinfo=timezone.utc)))
        db.commit()

    r = _run("--input", graphql_export, "--apply",
             "--database-url", f"sqlite:///{db_path}")
    assert r.returncode == 3, r.stderr
    with Session(engine) as db:
        assert len(db.exec(select(WikiComment)).all()) == 1

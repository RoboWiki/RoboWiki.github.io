"""投稿修正 → 审核 → outbox 的交互契约。

这条链路的边界很窄但很容易被「UI 看起来对」骗过去：
- 提案里的 preview 必须由服务端按当前目录生成，客户端传的一律丢弃；
- 值域（price / date / source_tier / url）必须在服务端拒绝；
- 审核只能做一次，重复审核是 409，不产生第二条 outbox；
- 驳回理由要能回给提交者；「其他」必须写说明；
- 通过只进 outbox，worker 默认 dry-run，不碰 GitHub。

共享同一个进程内 app（与 test_api 相同的测试库约定）；每个用例前 conftest
会清一次限流桶，所以这里可以放心地一次发多条提案。
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile

_TMP = tempfile.mkdtemp(prefix="roboselect-submission-")
os.environ["ROBOWIKI_DB_PATH"] = str(pathlib.Path(_TMP) / "test.db")
os.environ["ROBOWIKI_SECRET_KEY"] = "test-secret-key-at-least-32-bytes-long-0000"
os.environ["ROBOWIKI_BOT_TOKEN"] = "test-bot-token"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PART = "cubemars-ak80-6"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    # Windows 上 WAL 会占住目录：先释放 engine 再清理
    from app.core.db import engine, reset_engine
    try:
        engine().dispose()
    except Exception:
        pass
    reset_engine()
    shutil.rmtree(_TMP, ignore_errors=True)


def auth(c: TestClient, handle="robowiki", password="robowiki") -> dict:
    r = c.post("/api/v1/auth/login", json={"handle": handle, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def staff(client):
    return auth(client)


@pytest.fixture()
def outbox_dir():
    """独立产物目录。

    不用 pytest 的 tmp_path：这台机器上默认临时根不可写（见 tests/conftest.py），
    而 backend/tests 不继承那份 conftest。和 test_publisher 一样自己建临时目录。
    """
    d = pathlib.Path(tempfile.mkdtemp(prefix="rw-outbox-"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def submit(c: TestClient, headers: dict, payload: dict, *,
           note: str = "官方手册 p12：含驱动器报价", source: str = "https://example.com/manual",
           target: str = PART):
    return c.post("/api/v1/submissions", headers=headers, json={
        "kind": "part_patch",
        "target_id": target,
        "payload": payload,
        "evidence": {"note": note, "source_url": source},
    })


def review(c: TestClient, headers: dict, sid: int, decision: str,
           reason: str = "ok", note: str = ""):
    return c.post(f"/api/v1/submissions/{sid}/review", headers=headers, json={
        "decision": decision, "reason_code": reason, "note": note,
    })


# ── 合法提交 ────────────────────────────────────────────────────────────────
def test_valid_submission_preview_is_server_generated(client, staff):
    r = submit(client, staff, {"price_cny": 3288.0})
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["status"] == "pending"
    assert d["target_id"] == PART
    assert d["evidence"]["note"] == "官方手册 p12：含驱动器报价"
    preview = d["evidence"]["preview"]
    assert [p["field"] for p in preview] == ["price_cny"]
    assert preview[0]["new_value"] == 3288.0
    assert "old_value" in preview[0]

    # 客户端伪造的 preview 必须被丢掉：审核员看到的 diff 只能来自目录
    r = client.post("/api/v1/submissions", headers=staff, json={
        "kind": "part_patch", "target_id": PART,
        "payload": {"source_tier": "B"},
        "evidence": {
            "note": "伪造 preview 应被覆盖", "source_url": "https://example.com",
            "preview": [{"field": "notes", "old_value": "a", "new_value": "b"}],
        },
    })
    assert r.status_code == 201, r.text
    preview = r.json()["evidence"]["preview"]
    assert [p["field"] for p in preview] == ["source_tier"]
    assert preview[0]["new_value"] == "B"


def test_unknown_field_and_missing_target_are_rejected(client, staff):
    r = submit(client, staff, {"specs.not_a_real_key": 1}, note="白名单外的字段")
    assert r.status_code == 422
    r = submit(client, staff, {"price_cny": 1.0}, target="no-such-part")
    assert r.status_code == 404


# ── 非法值域 ────────────────────────────────────────────────────────────────
def test_invalid_value_domains_are_rejected(client, staff):
    cases = [
        {"price_cny": -1},
        {"price_cny": "abc"},
        {"price_cny": True},
        {"source_tier": "Z"},
        {"last_checked": "not-a-date"},
        {"last_checked": "1899-12-31"},
        {"url": "ftp://example.com/file"},
        {"url": "https://"},
        {"doc_url": "//example.com/manual"},
    ]
    for payload in cases:
        r = submit(client, staff, payload, note="值域测试")
        assert r.status_code == 422, (payload, r.text)


def test_evidence_requires_note_and_http_source(client, staff):
    r = submit(client, staff, {"price_cny": 1.0}, note="")
    assert r.status_code == 422
    r = submit(client, staff, {"price_cny": 1.0}, source="javascript:alert(1)")
    assert r.status_code == 422


# ── 权限 ────────────────────────────────────────────────────────────────────
def test_non_staff_cannot_review_or_list_queues(client, staff):
    r = submit(client, staff, {"price_cny": 2999.0})
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    plain = auth(client, "demo1")
    assert review(client, plain, sid, "accepted").status_code == 403
    assert client.get("/api/v1/submissions/queue", headers=plain).status_code == 403
    assert client.get("/api/v1/submissions/outbox", headers=plain).status_code == 403
    # 不是提交人也不是站务：连详情都看不到
    assert client.get(f"/api/v1/submissions/{sid}", headers=plain).status_code == 403


# ── 通过 → outbox → worker dry-run ──────────────────────────────────────────
def test_accept_enqueues_outbox_and_worker_dry_run(client, staff, capsys,
                                                   outbox_dir, monkeypatch):
    r = submit(client, staff, {"price_cny": 4321.0})
    assert r.status_code == 201, r.text
    sid = r.json()["id"]

    r = review(client, staff, sid, "accepted", "ok", "已按官方页核对")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "accepted"
    assert d["reviews"][-1]["decision"] == "accepted"
    assert d["reviews"][-1]["reason_code"] == "ok"
    assert d["reviews"][-1]["note"] == "已按官方页核对"

    tasks = client.get("/api/v1/submissions/outbox", headers=staff).json()
    mine = [t for t in tasks if t["submission_id"] == sid]
    assert mine, "通过后必须出现 outbox 任务"
    assert mine[0]["status"] == "pending"

    # 默认 dry-run：worker 写本地产物，不开 PR（测试里指到临时目录以免污染仓库）
    from app.worker import process_one
    monkeypatch.setenv("ROBOWIKI_OUTBOX_DIR", str(outbox_dir))
    target = outbox_dir / f"submission-{sid}.json"
    for _ in range(30):
        if target.exists():
            break
        assert process_one() is True
    assert target.exists(), "worker 没有产出 dry-run 产物"

    artifact = json.loads(target.read_text(encoding="utf-8"))
    assert artifact["dry_run"] is True
    assert artifact["submission_id"] == sid
    assert artifact["payload"]["changes"]["price_cny"] == 4321.0
    assert artifact["payload"]["evidence"]["note"]

    out = capsys.readouterr().out
    assert "dry-run" in out, "worker 必须把 dry-run 写进日志"


# ── 驳回理由 ────────────────────────────────────────────────────────────────
def test_rejection_records_reason_and_enqueues_nothing(client, staff):
    r = submit(client, staff, {"price_cny": 2599.0})
    sid = r.json()["id"]

    r = review(client, staff, sid, "rejected", "wrong_value", "官网现价 2999，不是 2599")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["status"] == "rejected"
    last = d["reviews"][-1]
    assert (last["decision"], last["reason_code"], last["note"]) == \
        ("rejected", "wrong_value", "官网现价 2999，不是 2599")

    # 提交者/站务在详情里都能看到同一条理由
    detail = client.get(f"/api/v1/submissions/{sid}", headers=staff).json()
    assert detail["reviews"][-1]["note"] == "官网现价 2999，不是 2599"

    # 驳回不进发布队列
    tasks = client.get("/api/v1/submissions/outbox", headers=staff).json()
    assert not [t for t in tasks if t["submission_id"] == sid]


def test_reject_other_requires_note(client, staff):
    r = submit(client, staff, {"source_tier": "B"})
    sid = r.json()["id"]

    r = review(client, staff, sid, "rejected", "other", "   ")
    assert r.status_code == 422, r.text

    r = review(client, staff, sid, "rejected", "other", "这条其实属于分类问题，转给数据组")
    assert r.status_code == 200, r.text
    assert r.json()["reviews"][-1]["reason_code"] == "other"

    # 理由必须是封闭集合里的值
    r = submit(client, staff, {"source_tier": "B"})
    sid2 = r.json()["id"]
    assert review(client, staff, sid2, "rejected", "", "").status_code == 422
    assert review(client, staff, sid2, "rejected", "whatever", "理由乱写").status_code == 422


# ── 重复审核 ────────────────────────────────────────────────────────────────
def test_duplicate_review_returns_409(client, staff):
    r = submit(client, staff, {"price_cny": 3001.0})
    sid = r.json()["id"]

    assert review(client, staff, sid, "accepted", "ok", "第一次").status_code == 200
    again = review(client, staff, sid, "accepted", "ok", "第二次")
    assert again.status_code == 409, again.text
    # 改成驳回也不行：状态已经不是 pending
    assert review(client, staff, sid, "rejected", "duplicate", "重复提案").status_code == 409


def test_review_notifies_submitter(client, staff):
    r = client.post("/api/v1/auth/register", json={
        "handle": "notify-submitter", "display_name": "提案人",
        "password": "pass1234",
    })
    assert r.status_code == 201, r.text
    user = {"Authorization": f"Bearer {r.json()['access_token']}"}

    sid = submit(client, user, {"price_cny": 3111.0}).json()["id"]
    assert review(client, staff, sid, "rejected", "wrong_value",
                  "官网价格不对").status_code == 200

    notes = client.get("/api/v1/notifications", headers=user).json()
    hit = [n for n in notes["items"] if n["type"] == "moderation"]
    assert hit and "驳回" in hit[0]["subject"]
    assert "官网价格不对" in hit[0]["body"]

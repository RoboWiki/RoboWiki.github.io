"""聚合脚本的测试（用假 issue JSON，不联网）。

真正的风险点在解析：Issue Forms 渲染出来的正文是 `### 字段名\n\n值`，
字段名里还有全角括号（`评分（1–5）`）。这些细节一错，分数就全错或者全丢，
所以用固定的样例把它钉住。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _issue(num, author, part, score, own="", note="理由", state="open",
           labels=("rating",)):
    body = f"""### 部件 id

{part}

### 评分（1–5）

{score}

### 使用情况

{own}

### 一句话理由

{note}

### 用在什么上（可选）

四足
"""
    return {"number": num, "title": f"[评分] {part}", "state": state,
            "author": {"login": author}, "body": body,
            "labels": [{"name": l} for l in labels], "createdAt": f"2026-10-{num:02d}T00:00:00Z"}


def run(issues) -> dict:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "issues.json"
        p.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "ingest_ratings.py"), str(p)],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
        return json.loads((ROOT / "data" / "ratings_snapshot.json").read_text(encoding="utf-8"))


PART = "达妙-dm-dm-j4340-2ec-v1-1"
PART2 = "灵足-robstride-rs04"


def test_parses_form_body():
    d = run([_issue(1, "alice", PART, 4)])
    p = d["parts"][PART]
    assert p["count"] == 1 and p["avg"] == 4.0
    assert p["histogram"]["4"] == 1


def test_own_hardware_detected():
    d = run([
        _issue(1, "alice", PART, 5, own="- [X] 我装过 / 用过这个件"),
        _issue(2, "bob", PART, 3),
    ])
    p = d["parts"][PART]
    assert p["count"] == 2 and p["avg"] == 4.0
    assert p["own_hardware_count"] == 1, "只有勾了装过机的那条算"


def test_one_vote_per_user_latest_wins():
    d = run([
        _issue(1, "alice", PART, 1),
        _issue(5, "alice", PART, 5),      # 同一人改主意，取最新
    ])
    p = d["parts"][PART]
    assert p["count"] == 1, "一人一票"
    assert p["avg"] == 5.0


def test_closed_and_unlabeled_ignored():
    d = run([
        _issue(1, "alice", PART, 4),
        _issue(2, "bob", PART, 1, state="closed"),
        _issue(3, "carol", PART2, 1, labels=()),
    ])
    assert d["total_ratings"] == 1
    assert PART2 not in d["parts"]


def test_unknown_part_and_bad_score_are_dropped():
    d = run([
        _issue(1, "alice", PART, 4),
        _issue(2, "bob", "no-such-part", 5),
        _issue(3, "carol", PART2, 9),
    ])
    assert d["total_ratings"] == 1
    errs = json.loads((ROOT / "data" / "ratings_errors.json").read_text(encoding="utf-8"))
    assert len(errs) == 2, errs


def test_title_fallback_when_field_missing():
    it = _issue(1, "alice", PART, 4)
    # 把「部件 id」字段的值挖空，靠标题里的 [评分] <id> 兜底
    it["body"] = it["body"].replace(f"### 部件 id\n\n{PART}", "### 部件 id\n\n")
    d = run([it])
    assert d["parts"][PART]["count"] == 1

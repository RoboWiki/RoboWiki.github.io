"""聚合脚本的测试（用假 issue JSON，不联网）。

真正的风险点在解析：Issue Forms 渲染出来的正文是 `### 字段名\n\n值`，
字段名里还有全角括号（`评分（1–5）`）。这些细节一错，分数就全错或者全丢，
所以用固定的样例把它钉住。

另一类风险是「链路没接上」：部件目录来自`RoboWiki` 仓的锁定 release，本仓没有
data/catalog。目录读空时聚合脚本会把每条评分都当成无效条目丢掉，产出一份
空快照 —— 看起来像「没人评分」。所以这里用临时 catalog 夹具显式喂目录，
不依赖本机有没有 .data/；目录缺失时必须直接失败。
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PART = "达妙-dm-dm-j4340-2ec-v1-1"
PART2 = "灵足-robstride-rs04"


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


def _catalog(root: pathlib.Path) -> pathlib.Path:
    """最小目录夹具：聚合脚本只用 `id` 校验部件是否在册。"""
    data = root / "data"
    (data / "catalog" / "actuator").mkdir(parents=True)
    (data / "catalog" / "actuator" / "fixture.json").write_text(
        json.dumps([{"id": PART}, {"id": PART2}], ensure_ascii=False),
        encoding="utf-8")
    return data


def _run(issues, data_dir: pathlib.Path, out_dir: pathlib.Path) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "issues.json"
        p.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "pipeline" / "ingest_ratings.py"),
                               str(p), "--out", str(out_dir)],
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "ROBOWIKI_DATA_DIR": str(data_dir),
                                   "PYTHONIOENCODING": "utf-8"})


def run(issues) -> tuple[dict, list]:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        data = _catalog(root)
        out = root / "out"
        r = _run(issues, data, out)
        assert r.returncode == 0, r.stdout + r.stderr
        # 目录与产物必须分开：产物若落在 catalog 所在目录，生产里就会写进
        # release 解压物（下次解压即丢），页面永远读不到。
        assert not (data / "ratings_snapshot.json").exists(), "快照不该写进目录数据目录"
        snap = json.loads((out / "ratings_snapshot.json").read_text(encoding="utf-8"))
        errs = json.loads((out / "ratings_errors.json").read_text(encoding="utf-8"))
        return snap, errs


def test_parses_form_body():
    d, _ = run([_issue(1, "alice", PART, 4)])
    p = d["parts"][PART]
    assert p["count"] == 1 and p["avg"] == 4.0
    assert p["histogram"]["4"] == 1


def test_snapshot_contract_shape():
    """快照结构是前端契约：站点 / 小程序按这些字段读，改结构要同步改消费方。"""
    d, _ = run([_issue(1, "alice", PART, 4)])
    assert set(d) == {"total_ratings", "parts", "snapshot", "source"}
    assert d["snapshot"] is True and d["source"] == "github-issues"
    assert set(d["parts"][PART]) == {
        "count", "avg", "histogram", "own_hardware_count", "own_hardware_avg",
        "dims_avg", "dims_n", "usage_count", "low_sample", "mine", "votes"}


def test_own_hardware_detected():
    d, _ = run([
        _issue(1, "alice", PART, 5, own="- [X] 我装过 / 用过这个件"),
        _issue(2, "bob", PART, 3),
    ])
    p = d["parts"][PART]
    assert p["count"] == 2 and p["avg"] == 4.0
    assert p["own_hardware_count"] == 1, "只有勾了装过机的那条算"


def test_one_vote_per_user_latest_wins():
    d, _ = run([
        _issue(1, "alice", PART, 1),
        _issue(5, "alice", PART, 5),      # 同一人改主意，取最新
    ])
    p = d["parts"][PART]
    assert p["count"] == 1, "一人一票"
    assert p["avg"] == 5.0


def test_closed_and_unlabeled_ignored():
    d, _ = run([
        _issue(1, "alice", PART, 4),
        _issue(2, "bob", PART, 1, state="closed"),
        _issue(3, "carol", PART2, 1, labels=()),
    ])
    assert d["total_ratings"] == 1
    assert PART2 not in d["parts"]


def test_unknown_part_and_bad_score_are_dropped():
    d, errs = run([
        _issue(1, "alice", PART, 4),
        _issue(2, "bob", "no-such-part", 5),
        _issue(3, "carol", PART2, 9),
    ])
    assert d["total_ratings"] == 1
    assert len(errs) == 2, errs


def test_title_fallback_when_field_missing():
    it = _issue(1, "alice", PART, 4)
    # 把「部件 id」字段的值挖空，靠标题里的 [评分] <id> 兜底
    it["body"] = it["body"].replace(f"### 部件 id\n\n{PART}", "### 部件 id\n\n")
    d, _ = run([it])
    assert d["parts"][PART]["count"] == 1


def test_missing_catalog_fails_loudly():
    """目录读空必须失败，不能产出一份「看起来没人评分」的空快照。"""
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        out = root / "out"
        r = _run([_issue(1, "alice", PART, 4)], root / "no-catalog", out)
        assert r.returncode != 0, r.stdout + r.stderr
        assert "部件目录" in (r.stdout + r.stderr)
        assert not (out / "ratings_snapshot.json").exists(), "失败时不能留下假空快照"

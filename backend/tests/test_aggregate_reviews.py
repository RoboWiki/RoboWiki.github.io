"""实测聚合的测试。

真正的风险在解析：Issue Forms 渲染成 `### 字段名\\n\\n值`，字段名带全角括号
（`典型负载（N·m）`）。解析错一条，部件页上的「平均负载」就是假的 ——
所以用固定样例把边界钉住。
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PART = "达妙-dm-dm-j4340-2ec-v1-1"


def _issue(num, **kw):
    b = f"""### 部件 id

{kw.get('part', PART)}

### 装在什么上

{kw.get('used_on', '四足 20 kg')}

### 用在哪个关节

{kw.get('joint', '膝')}

### 典型负载（N·m）

{kw.get('load', '28')}

### 占空比 / 运行方式

{kw.get('duty', '连续 30 分钟歇 5 分钟')}

### 累计运行时长

{kw.get('hours', '约 120 小时')}

### 外壳温升（℃）

{kw.get('temp', '环境 26℃，外壳 58℃')}

### 有没有坏过

{kw.get('failure', '没坏，一直在用')}

### 具体情况

{kw.get('detail', '一直正常')}

### 有没有可公开的证据（可选）

{kw.get('source', '')}
"""
    return {"number": num, "title": f"[实测] {kw.get('part', PART)}", "state": "open",
            "author": {"login": kw.get("author", "alice")}, "body": b,
            "labels": [{"name": n} for n in kw.get("labels", ("review",))]}


def run(issues) -> dict:
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td) / "issues.json"
        p.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
        out = pathlib.Path(td) / "out"
        r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "ingest_reviews.py"),
                            str(p), "--out", str(out)],
                           capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, r.stdout + r.stderr
        snap = json.loads((out / "reviews_snapshot.json").read_text(encoding="utf-8"))
        errs = json.loads((out / "reviews_errors.json").read_text(encoding="utf-8"))
        return snap, errs


def test_basic_aggregate():
    d, _ = run([_issue(1)])
    p = d["parts"][PART]
    assert p["count"] == 1
    assert p["load_avg"] == 28.0 and p["load_max"] == 28.0
    assert p["hours_max"] == 120.0
    assert p["joints"]["knee"] == 1
    assert p["failures"]["ok"] == 1


def test_failure_kept_not_dropped():
    """坏过是最值钱的信息，不能因为「不好看」就丢掉"""
    d, _ = run([_issue(1), _issue(2, failure="坏过，已修 / 已换", author="bob")])
    p = d["parts"][PART]
    assert p["count"] == 2
    assert p["failures"]["broken"] == 1 and p["failures"]["ok"] == 1
    assert p["load_avg"] == 28.0


def test_missing_load_or_hours_excluded():
    d, errs = run([_issue(1), _issue(2, load="不清楚", author="bob"),
                   _issue(3, hours="还没跑", author="carol")])
    p = d["parts"][PART]
    assert p["count"] == 1, "缺工况的条目不能进可比统计"
    assert len(errs) == 2


def test_months_converted_and_flagged():
    d, _ = run([_issue(1, hours="3 个月")])
    # 3 个月 ≈ 3×30×4 = 360 小时（粗估，条目里保留原始文本）
    assert d["parts"][PART]["hours_max"] == 360.0


def test_unlabeled_and_closed_ignored():
    d, _ = run([_issue(1), _issue(2, labels=()),
                {**_issue(3), "state": "closed"}])
    assert d["parts"][PART]["count"] == 1


def test_unknown_part_rejected():
    d, errs = run([_issue(1, part="no-such-part")])
    assert d["parts"] == {}
    assert "不在目录里" in errs[0]

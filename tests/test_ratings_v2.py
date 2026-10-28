"""评分 v2：四维、工况、样本量、旧格式兼容、勾选框判断。

这几条都是「静默失真」型的坑：不报错，但数字是错的。
    · 四维缺项被补 0      → 均值被拉低
    · 勾选框用子串匹配    → 每条都被算成「装过机」
    · 低样本不给提示      → 1 条 5 分看起来和 20 条 5 分一样确定
"""
from __future__ import annotations

import json
import subprocess
import sys

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PART = "dji-robomaster-m3508-p19"


def _blk(name, value):
    return f"### {name}\n\n{value}\n\n"


def _issue(n, login, dims, usage, own, note, score="4", created="2026-10-20T10:00:00Z"):
    body = _blk("部件 id", PART) + _blk("总分（1–5）", score)
    for k, v in dims.items():
        body += _blk(k, f"{v} - 示例")
    body += _blk("使用情况", "- [x] 我装过 / 用过这个件" if own
                 else "- [ ] 我装过 / 用过这个件")
    for k, v in usage.items():
        body += _blk(k, v)
    body += _blk("一句话理由", note)
    return {"number": n, "title": f"[评分] {PART}", "body": body, "createdAt": created,
            "state": "open", "labels": [{"name": "rating"}], "author": {"login": login}}


def _run(tmp_path, issues):
    f = tmp_path / "issues.json"
    f.write_text(json.dumps(issues, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "pipeline.ingest_ratings",
                        str(f), "--out", str(tmp_path)], cwd=ROOT, capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "ignore")[-2000:]
    return json.loads((tmp_path / "ratings_snapshot.json").read_text(encoding="utf-8"))


def test_dims_usage_and_low_sample(tmp_path):
    snap = _run(tmp_path, [
        _issue(1, "alice", {"参数可信度": 5, "做工": 4, "文档与支持": 3, "性价比": 5},
               {"用了多久": "3-12个月", "负载情况": "满载连续", "使用批量": "小批量"},
               True, "髋关节连续 30 N·m 三个月"),
        _issue(2, "bob", {}, {}, False, "只看参数", score="3",
               created="2026-10-21T10:00:00Z"),
    ])
    one = snap["parts"][PART]
    assert one["count"] == 2
    assert one["low_sample"] is True
    # 只有 alice 装过机；bob 的 - [ ] 不能被算成装过
    assert one["own_hardware_count"] == 1
    assert one["own_hardware_avg"] == 4.0
    # 四维只统计填了的那一条，且分母单独给出
    assert one["dims_avg"] == {"spec_trust": 5, "build": 4, "docs": 3, "value": 5}
    assert one["dims_n"]["docs"] == 1
    # 工况分布
    assert one["usage_count"] == {"duration": {"3-12个月": 1},
                                  "load": {"满载连续": 1},
                                  "batch": {"小批量": 1}}


def test_old_format_still_works(tmp_path):
    """v1 表单（只有「评分」字段、没有四维）必须继续能聚合，且四维留空不补 0。"""
    old = {"number": 9, "title": f"[评分] {PART}",
           "body": _blk("部件 id", PART) + _blk("评分（1–5）", "5")
                   + _blk("一句话理由", "旧格式"),
           "createdAt": "2026-10-01T00:00:00Z", "state": "open",
           "labels": [{"name": "rating"}], "author": {"login": "carol"}}
    one = _run(tmp_path, [old])["parts"][PART]
    assert one["count"] == 1
    assert one["avg"] == 5
    assert one["dims_avg"] is None
    assert one["own_hardware_count"] == 0

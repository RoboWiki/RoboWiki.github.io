"""把「实测评价」issue 聚合成部件页能用的汇总。

为什么不在 giscus 里自由发言就完事：
    自由发言搜不出来。「这个件跑过的人平均 28 N·m、最长 400 小时、2 人报温升超 60℃」
    这种句子只能从**结构化**的 issue 里算出来。所以表单要问工况。

产出 data/reviews_snapshot.json：
    {
      "parts": {
        "<part_id>": {
          "count": 3,
          "load_avg": 26.3, "load_max": 35,
          "hours_max": 400,
          "failures": {"none": 2, "bent": 1, ...},
          "joints": {"knee": 2, "hip": 1},
          "with_evidence": 1,
          "entries": [ {author, joint, load, duty, hours, temp, failure, detail, source} ]
        }
      }
    }

口径纪律：
    · 只统计填全「负载 + 运行时长」的条目 —— 缺这两项就不是可比的实测
    · 坏过的条目**不删**，反而单独计数：这是最有价值的信息
    · 不写均分：评分在 ratings 里，这里只放使用条件与结果，避免两套分数打架
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reviews_snapshot.json"

FIELD_ALIASES = {
    "part": ["部件 id"],
    "used_on": ["装在什么上"],
    "joint": ["用在哪个关节"],
    "load": ["典型负载（N·m）", "典型负载"],
    "duty": ["占空比 / 运行方式", "占空比"],
    "hours": ["累计运行时长"],
    "temp": ["外壳温升（℃）", "外壳温升"],
    "failure": ["有没有坏过"],
    "detail": ["具体情况"],
    "source": ["有没有可公开的证据（可选）", "有没有可公开的证据"],
}

FAIL_KEY = {
    "没坏": "ok",
    "坏过": "broken",
    "有异常": "degraded",
    "全新": "unused",
}

JOINT_KEY = {
    "髋": "hip", "膝": "knee", "踝": "ankle", "肩": "shoulder",
    "肘": "elbow", "腕": "wrist", "不适用": "na",
}


def field(body: str, names: list[str]) -> str:
    for n in names:
        m = re.search(rf"^###\s*{re.escape(n)}\s*$\s*(.+?)(?=^###|\Z)",
                      body or "", re.S | re.M)
        if m:
            return m.group(1).strip()
    return ""


def num(s: str) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", s or "")
    return float(m.group(0)) if m else None


def hours_of(s: str) -> float | None:
    """「约 120 小时」→120；「3 个月」按每天 4 小时粗算并标注不精确。"""
    n = num(s)
    if n is None:
        return None
    if "月" in s:
        return round(n * 30 * 4, 0)      # 粗估，条目标 precise=false
    if "天" in s:
        return round(n * 4, 0)
    return n


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: aggregate_reviews.py <issues.json>")
        raise SystemExit(2)
    issues = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    known = {r["id"] for f in (ROOT / "data" / "catalog").glob("*/*.json")
             for r in json.loads(f.read_text(encoding="utf-8"))}

    by: dict[str, list[dict]] = {}
    errors: list[str] = []
    for it in issues:
        labels = {l["name"] for l in (it.get("labels") or [])}
        if "review" not in labels or (it.get("state") or "open").lower() != "open":
            continue
        body = it.get("body") or ""
        pid = field(body, FIELD_ALIASES["part"]).strip("` ")
        if not pid:
            m = re.match(r"^\s*\[实测\]\s*(\S+)", it.get("title") or "")
            pid = m.group(1) if m else ""
        if pid not in known:
            errors.append(f"#{it['number']}: 部件 id 不在目录里（{pid!r}）")
            continue
        load = num(field(body, FIELD_ALIASES["load"]))
        hours = hours_of(field(body, FIELD_ALIASES["hours"]))
        if load is None or hours is None:
            errors.append(f"#{it['number']}: 缺负载或运行时长，不进汇总（→{pid}）")
            continue
        ftext = field(body, FIELD_ALIASES["failure"])
        fkey = next((v for k, v in FAIL_KEY.items() if k in ftext), "unknown")
        jtext = field(body, FIELD_ALIASES["joint"])
        jkey = next((v for k, v in JOINT_KEY.items() if k in jtext), "other")
        by.setdefault(pid, []).append({
            "issue": it["number"],
            "author": (it.get("author") or {}).get("login"),
            "used_on": field(body, FIELD_ALIASES["used_on"]),
            "joint": jkey,
            "load": load,
            "duty": field(body, FIELD_ALIASES["duty"]),
            "hours": hours,
            "temp": field(body, FIELD_ALIASES["temp"]),
            "failure": fkey,
            "detail": field(body, FIELD_ALIASES["detail"])[:600],
            "source": field(body, FIELD_ALIASES["source"])[:200],
        })

    parts = {}
    for pid, rows in by.items():
        loads = [r["load"] for r in rows]
        fails: dict[str, int] = {}
        joints: dict[str, int] = {}
        for r in rows:
            fails[r["failure"]] = fails.get(r["failure"], 0) + 1
            joints[r["joint"]] = joints.get(r["joint"], 0) + 1
        parts[pid] = {
            "count": len(rows),
            "load_avg": round(sum(loads) / len(loads), 1),
            "load_max": max(loads),
            "hours_max": max(r["hours"] for r in rows),
            "failures": fails,
            "joints": joints,
            "with_evidence": sum(1 for r in rows if r["source"]),
            "entries": sorted(rows, key=lambda r: -r["hours"]),
        }

    OUT.write_text(json.dumps({"parts": parts}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    (ROOT / "data" / "reviews_errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"实测 {sum(v['count'] for v in parts.values())} 条 / {len(parts)} 个零件")
    for e in errors[:10]:
        print("  " + e)


if __name__ == "__main__":
    main()

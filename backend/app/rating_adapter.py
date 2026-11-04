"""issue 快照适配层。

`pipeline/ingest_ratings.py` 产出的是**已经聚合过**的快照：
`parts[part_id] = {count, avg, histogram, own_hardware_count, ...}`。
它没有逐条事实（可选保留 `votes` 明细），所以适配时不能从空 rows 重算 ——
那会把 count 归零，页面看起来像「没人评分」。

这里做两件事：
    1. `aggregate_from_snapshot_part`：把聚合块转成 `rating_stats.aggregate`
       的形状，缺失字段保持 None，绝不补 0（0 分是差评，未知是未知）。
    2. `facts_from_snapshot_part`：当快照保留了 votes 明细时，把它还原成
       RatingFact，供需要重新按新先验计算的场景使用。

字段缺失口径：
    · own_hardware_count / own_hardware_avg 缺失 → None（不是 0）
    · dims_avg / dims_n / usage_count 缺失 → None（不是 {}）
    · histogram 缺失 → None；存在时补全 1–5 分档为 0（这是分布本身的语义，
      不是把一个未知字段伪造成 0）
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .rating_stats import (
    DEFAULT_PRIOR_MEAN,
    DEFAULT_PRIOR_WEIGHT,
    LOW_SAMPLE_N,
    RECOMMEND_MIN_SCORE,
    RatingFact,
    bayesian_score,
    coerce_fact,
    wilson_lower_bound,
)

_HISTOGRAM_KEYS = ("1", "2", "3", "4", "5")


def _opt_int(value: Any, field: str) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} 必须是整数，收到布尔值")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field} 必须是整数，收到 {value!r}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是整数，收到 {value!r}") from exc


def _opt_float(value: Any, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是数字，收到 {value!r}") from exc


def _histogram(value: Any) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("histogram 必须是映射")
    if not value:
        return None
    out = {key: 0 for key in _HISTOGRAM_KEYS}
    for key, count in value.items():
        try:
            bucket = int(key)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"histogram 分档非法：{key!r}") from exc
        if not 1 <= bucket <= 5:
            raise ValueError(f"histogram 分档必须在 1–5：{key!r}")
        number = _opt_int(count, f"histogram[{key}]")
        out[str(bucket)] = number or 0
    return out


def _dims_avg(value: Any) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("dims_avg 必须是映射")
    out: dict[str, float] = {}
    for key, item in value.items():
        if item is None:
            continue
        number = _opt_float(item, f"dims_avg[{key}]")
        if number is None:
            continue
        if not 1 <= number <= 5:
            raise ValueError(f"dims_avg[{key}] 必须在 1–5：{item!r}")
        out[str(key)] = number
    return out or None


def _int_map(value: Any, field: str) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} 必须是映射")
    out: dict[str, int] = {}
    for key, item in value.items():
        number = _opt_int(item, f"{field}[{key}]")
        if number is None:
            continue
        out[str(key)] = number
    return out or None


def _usage_count(value: Any) -> dict[str, dict[str, int]] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError("usage_count 必须是映射")
    out: dict[str, dict[str, int]] = {}
    for category, bucket in value.items():
        counts = _int_map(bucket, f"usage_count[{category}]")
        if counts:
            out[str(category)] = counts
    return out or None


def _low_sample(value: Any, count: int | None) -> bool | None:
    if value is not None:
        return bool(value)
    if count is not None:
        return count < LOW_SAMPLE_N
    return None


def _recommend(histogram: dict[str, int] | None) -> tuple[int | None, float | None,
                                                               float | None]:
    if histogram is None:
        # 没有分布就不知道有多少人打 4–5 分；保持未知，不把 0 当成结论。
        return None, None, None
    total = sum(histogram.values())
    positive = sum(histogram[key] for key in ("4", "5"))
    if total == 0:
        return positive, None, None
    return positive, round(positive / total, 4), round(
        wilson_lower_bound(positive, total), 4)


def aggregate_from_snapshot_part(
    part: Mapping[str, Any],
    *,
    prior_mean: float = DEFAULT_PRIOR_MEAN,
    m: float = DEFAULT_PRIOR_WEIGHT,
) -> dict:
    """把快照里的一个 parts[part_id] 块转成聚合结果形状。

    这是**转换**不是重算：count / avg / histogram 等以快照为准；
    只有 confidence / rank_score / 推荐率这些派生值按当前口径现算。
    缺失字段一律保持 None。
    """
    if not isinstance(part, Mapping):
        raise ValueError(f"快照部件块必须是映射，收到 {type(part).__name__}")
    if m < 0:
        raise ValueError(f"m 不能为负，收到 {m}")

    count = _opt_int(part.get("count"), "count")
    avg = _opt_float(part.get("avg"), "avg")
    histogram = _histogram(part.get("histogram"))
    own_count = _opt_int(part.get("own_hardware_count"), "own_hardware_count")
    own_avg = _opt_float(part.get("own_hardware_avg"), "own_hardware_avg")

    confidence = (round(count / (count + m), 4)
                  if count is not None and count + m > 0 else None)
    rank_score = None
    if count is not None and count > 0 and avg is not None:
        rank_score = round(bayesian_score(avg, count, prior_mean, m), 4)

    recommend_count, recommend_rate, wilson_lower = _recommend(histogram)

    return {
        "count": count,
        "avg": avg,
        "histogram": histogram,
        "own_hardware_count": own_count,
        "own_hardware_avg": own_avg,
        "dims_avg": _dims_avg(part.get("dims_avg")),
        "dims_n": _int_map(part.get("dims_n"), "dims_n"),
        "usage_count": _usage_count(part.get("usage_count")),
        "low_sample": _low_sample(part.get("low_sample"), count),
        "confidence": confidence,
        "rank_score": rank_score,
        "recommend_count": recommend_count,
        "recommend_rate": recommend_rate,
        "wilson_lower": wilson_lower,
    }


def aggregate_snapshot(
    snapshot: Mapping[str, Any],
    *,
    prior_mean: float = DEFAULT_PRIOR_MEAN,
    m: float = DEFAULT_PRIOR_WEIGHT,
) -> dict[str, dict]:
    """把整份 ratings_snapshot.json 转成 {part_id: 聚合结果}。"""
    if not isinstance(snapshot, Mapping):
        raise ValueError("快照必须是映射")
    parts = snapshot.get("parts") or {}
    if not isinstance(parts, Mapping):
        raise ValueError("快照的 parts 必须是映射")
    return {
        str(part_id): aggregate_from_snapshot_part(part, prior_mean=prior_mean, m=m)
        for part_id, part in parts.items()
    }


def facts_from_snapshot_part(part: Mapping[str, Any],
                             part_id: str | None = None) -> list[RatingFact]:
    """从快照保留的 votes 明细还原 RatingFact（没有 votes 时返回空列表）。

    用途：快照里只有聚合值时无法重算；当 pipeline 保留了逐条明细，
    换先验、换阈值时可以在这里重新聚合，而不必回 GitHub 拉 issue。
    """
    if not isinstance(part, Mapping):
        raise ValueError("快照部件块必须是映射")
    votes = part.get("votes") or []
    if not isinstance(votes, list):
        raise ValueError("votes 必须是列表")

    facts: list[RatingFact] = []
    for vote in votes:
        if not isinstance(vote, Mapping):
            raise ValueError("votes 的条目必须是映射")
        pid = part_id or vote.get("part_id") or part.get("part_id")
        facts.append(coerce_fact({
            "user_key": vote.get("author") or vote.get("user_key"),
            "part_id": pid,
            "score": vote.get("score", vote.get("rating")),
            "own_hardware": vote.get("own_hardware", False),
            "dims": vote.get("dims"),
            "usage": vote.get("usage"),
            "source": "issue",
            "external_ref": vote.get("issue"),
            "created_at": vote.get("at") or vote.get("createdAt"),
        }))
    return facts


__all__ = [
    "aggregate_from_snapshot_part",
    "aggregate_snapshot",
    "facts_from_snapshot_part",
]

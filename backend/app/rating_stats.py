"""评分聚合的纯函数层。

为什么单独一层：
    评分事实有三个来源（网页评分、GitHub issue 快照、未来的 bot 导入），
    但「怎么算一个可信的分」只能有一套口径。把口径收在这里，路由、快照适配、
    排序都调同一组函数，就不会出现「页面 4.6 / 接口 4.2」这种漂移。

参考口径：
    · MusicBrainz 的评分聚合：均分必须带样本量，分布要一起给
    · Open Food Facts 的完整度：缺项就是缺项，不补 0（0 分是差评，不是未知）
    · Evan Miller 的 Wilson 下界：只用于「≥4 推荐率」这类比例，
      **不要拿它修正 1–5 的均值** —— Wilson 的输入是二项计数，不是连续均分

规范事实（RatingFact）：
    user_key     谁打的（站点 user_id 或 GitHub login，统一转成字符串）
    part_id      打的是哪个零件
    score        1–5
    own_hardware 是否装过机（最有参考价值的子样本）
    dims         四维细分分，缺项为 None
    usage        使用工况，缺项为 None
    source       web | issue | bot（来源要能追溯）
    external_ref 站外引用（issue 号等）
    created_at   时间（datetime 或 ISO 字符串都接受）

聚合结果（aggregate 返回）：
    count / avg / histogram / own_hardware_count / own_hardware_avg /
    dims_avg / dims_n / usage_count / low_sample / confidence / rank_score /
    recommend_count / recommend_rate / wilson_lower

    · n=0 时 avg=None，绝不返回 0 分
    · n<3 时 low_sample=True
    · dims 缺失不参与均值，也不补 0；dims_n 单独给分母
    · rank_score 是贝叶斯收缩后的均分（1 条 5 分会被先验拉回），用于排序
    · confidence = n/(n+m)，是「数据相对先验的权重」，不是概率
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

#: 样本量低于这个值时页面要显示「样本不足」
LOW_SAMPLE_N = 3
#: 贝叶斯先验：全站均分的保守锚点；没有它，1 条 5 分会压过 20 条 4.6
DEFAULT_PRIOR_MEAN = 3.0
#: 先验权重。m=5 表示「5 条真实评分才追平先验」
DEFAULT_PRIOR_WEIGHT = 5.0
#: 「推荐」阈值：4 分及以上算正向
RECOMMEND_MIN_SCORE = 4

HISTOGRAM_KEYS = ("1", "2", "3", "4", "5")
DIMENSION_KEYS = ("value", "build", "docs", "spec_trust", "compat")
USAGE_KEYS = ("duration", "load", "batch")
FACT_SOURCES = ("web", "issue", "bot")

_SOURCE_ALIASES = {
    "github": "issue",
    "github-issues": "issue",
    "github_issue": "issue",
    "issue_form": "issue",
    "api": "web",
    "site": "web",
    "website": "web",
}

#: 聚合结果的键集合。适配器与路由按这个形状对齐。
AGGREGATE_FIELDS = (
    "count",
    "avg",
    "histogram",
    "own_hardware_count",
    "own_hardware_avg",
    "dims_avg",
    "dims_n",
    "usage_count",
    "low_sample",
    "confidence",
    "rank_score",
    "recommend_count",
    "recommend_rate",
    "wilson_lower",
)

_MISSING = object()


def _as_score(value: Any, field: str = "score") -> int:
    """把输入转成 1–5 的整数；越界、布尔、小数都直接报错，不静默截断。"""
    if isinstance(value, bool):
        raise ValueError(f"{field} 必须是 1–5 的整数，收到布尔值")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{field} 必须是整数，收到 {value!r}")
        number = int(value)
    elif isinstance(value, str):
        text = value.strip()
        try:
            number = int(text)
        except ValueError as exc:
            raise ValueError(f"{field} 必须是 1–5 的整数，收到 {value!r}") from exc
    else:
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} 必须是 1–5 的整数，收到 {value!r}") from exc
    if not 1 <= number <= 5:
        raise ValueError(f"{field} 必须在 1–5 之间，收到 {number}")
    return number


def _norm_dims(value: Any) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"dims 必须是映射或 None，收到 {type(value).__name__}")
    out: dict[str, int] = {}
    for key, item in value.items():
        if item is None:
            continue
        out[str(key)] = _as_score(item, f"dims[{key}]")
    return out or None


def _norm_usage(value: Any) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(f"usage 必须是映射或 None，收到 {type(value).__name__}")
    out: dict[str, str] = {}
    for key, item in value.items():
        if item is None:
            continue
        text = str(item).strip()
        if text:
            out[str(key)] = text
    return out or None


def _norm_source(value: Any) -> str:
    source = str(value or "web").strip().lower()
    source = _SOURCE_ALIASES.get(source, source)
    if source not in FACT_SOURCES:
        raise ValueError(f"source 必须是 {FACT_SOURCES} 之一，收到 {value!r}")
    return source


@dataclass(frozen=True, slots=True)
class RatingFact:
    """一条规范化评分事实。构造时即校验，避免错误数据流进聚合。"""

    user_key: str
    part_id: str
    score: int
    own_hardware: bool = False
    dims: dict[str, int] | None = None
    usage: dict[str, str] | None = None
    source: str = "web"
    external_ref: str | None = None
    created_at: Any = None

    def __post_init__(self) -> None:
        user_key = str(self.user_key).strip()
        if not user_key:
            raise ValueError("user_key 不能为空")
        part_id = str(self.part_id).strip()
        if not part_id:
            raise ValueError("part_id 不能为空")
        object.__setattr__(self, "user_key", user_key)
        object.__setattr__(self, "part_id", part_id)
        object.__setattr__(self, "score", _as_score(self.score))
        object.__setattr__(self, "own_hardware", bool(self.own_hardware))
        object.__setattr__(self, "dims", _norm_dims(self.dims))
        object.__setattr__(self, "usage", _norm_usage(self.usage))
        object.__setattr__(self, "source", _norm_source(self.source))
        if self.external_ref is not None:
            object.__setattr__(self, "external_ref", str(self.external_ref))


def _first(get, *names: str) -> Any:
    for name in names:
        value = get(name, _MISSING)
        if value is not _MISSING and value is not None:
            return value
    return None


def _user_key(value: Any) -> str:
    if isinstance(value, Mapping):
        value = (value.get("login") or value.get("handle")
                 or value.get("user_key") or value.get("id"))
    elif not isinstance(value, str):
        value = (getattr(value, "login", None) or getattr(value, "handle", None)
                 or getattr(value, "id", value))
    if value is None or not str(value).strip():
        raise ValueError("评分事实缺少 user_key（站点 user_id / issue author）")
    return str(value)


def _part_id(value: Any) -> str:
    if value is None or not str(value).strip():
        raise ValueError("评分事实缺少 part_id")
    return str(value)


def coerce_fact(row: Any, *, default_source: str = "web") -> RatingFact:
    """把 dict / SQLModel 行 / RatingFact 统一成 RatingFact。

    兼容现有 Rating 模型（user_id、part_id、score、own_hardware）与 issue
    快照里的 votes 行（author、part_id、score、issue、at、dims、usage）。
    """
    if isinstance(row, RatingFact):
        return row

    if isinstance(row, Mapping):
        def get(name: str, default: Any = None) -> Any:
            return row.get(name, default)
    else:
        def get(name: str, default: Any = None) -> Any:
            return getattr(row, name, default)

    score = _first(get, "score", "rating")
    if score is None:
        raise ValueError("评分事实缺少 score / rating")
    source = _first(get, "source") or default_source
    return RatingFact(
        user_key=_user_key(_first(get, "user_key", "user_id", "author", "user")),
        part_id=_part_id(_first(get, "part_id", "part")),
        score=score,
        own_hardware=bool(_first(get, "own_hardware", "own")),
        dims=_first(get, "dims", "dimensions"),
        usage=_first(get, "usage"),
        source=source,
        external_ref=_first(get, "external_ref", "issue", "id"),
        created_at=_first(get, "created_at", "at", "createdAt"),
    )


def bayesian_score(mean: float | None, n: int, prior_mean: float,
                   m: float = DEFAULT_PRIOR_WEIGHT) -> float:
    """贝叶斯收缩均分：(mean·n + prior_mean·m) / (n + m)。

    n=0 返回先验均值（中性锚点），**不返回 0 分**。
    m=0 时退化为原始均分；m 越大，小样本越被拉向先验。
    """
    if n < 0:
        raise ValueError(f"n 不能为负，收到 {n}")
    if m < 0:
        raise ValueError(f"m 不能为负，收到 {m}")
    if n == 0:
        return float(prior_mean)
    if mean is None:
        raise ValueError("n>0 时 mean 不能为 None")
    denominator = n + m
    if denominator <= 0:
        return float(prior_mean)
    return (float(mean) * n + float(prior_mean) * m) / denominator


def wilson_lower_bound(positive: int, n: int, z: float = 1.96) -> float:
    """比例的 Wilson 下界，返回 0–1。

    只用于「≥4 推荐率」这类**二项比例**（positive / n）。
    1–5 的均值不是比例，不要直接套这个公式；要比较均分请用 bayesian_score。

    n=0 返回 0.0（没有任何证据）；positive 会被夹到 [0, n]。
    """
    if n < 0:
        raise ValueError(f"n 不能为负，收到 {n}")
    if z < 0:
        raise ValueError(f"z 不能为负，收到 {z}")
    if n == 0:
        return 0.0
    positive = max(0, min(int(positive), n))
    phat = positive / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = phat + z2 / (2.0 * n)
    margin = z * math.sqrt(phat * (1.0 - phat) / n + z2 / (4.0 * n * n))
    lower = (center - margin) / denominator
    return max(0.0, min(1.0, lower))


def _ordered(keys: Iterable[str], preferred: tuple[str, ...]) -> list[str]:
    keys = set(keys)
    head = [key for key in preferred if key in keys]
    tail = sorted(key for key in keys if key not in preferred)
    return head + tail


def aggregate(rows: Iterable[Any], *, prior_mean: float = DEFAULT_PRIOR_MEAN,
              m: float = DEFAULT_PRIOR_WEIGHT) -> dict:
    """把评分事实聚合成页面/接口/排序共用的一份结果。

    rows 可以是 RatingFact、dict 或带 score/part_id 的对象（如 Rating 行）。
    0 条时 avg / own_hardware_avg / rank_score 都是 None，不是 0。
    """
    if m < 0:
        raise ValueError(f"m 不能为负，收到 {m}")
    facts = [coerce_fact(row) for row in rows]
    n = len(facts)

    histogram = {key: 0 for key in HISTOGRAM_KEYS}
    score_total = 0
    recommend_count = 0
    own_scores: list[int] = []
    dims_values: dict[str, list[int]] = {}
    usage_counts: dict[str, dict[str, int]] = {}

    for fact in facts:
        histogram[str(fact.score)] += 1
        score_total += fact.score
        if fact.score >= RECOMMEND_MIN_SCORE:
            recommend_count += 1
        if fact.own_hardware:
            own_scores.append(fact.score)
        for key, value in (fact.dims or {}).items():
            dims_values.setdefault(key, []).append(value)
        for key, value in (fact.usage or {}).items():
            usage_counts.setdefault(key, {}).setdefault(value, 0)
            usage_counts[key][value] += 1

    avg = round(score_total / n, 2) if n else None
    own_hardware_avg = (round(sum(own_scores) / len(own_scores), 2)
                        if own_scores else None)
    dims_n = ({key: len(dims_values[key]) for key in _ordered(dims_values, DIMENSION_KEYS)}
              if dims_values else None)
    dims_avg = ({key: round(sum(dims_values[key]) / dims_n[key], 2)
                 for key in dims_n} if dims_n else None)
    usage_count = ({key: dict(sorted(usage_counts[key].items()))
                    for key in _ordered(usage_counts, USAGE_KEYS)}
                   if usage_counts else None)

    confidence = round(n / (n + m), 4) if n + m > 0 else 0.0
    rank_score = (round(bayesian_score(score_total / n, n, prior_mean, m), 4)
                  if n else None)
    recommend_rate = round(recommend_count / n, 4) if n else None
    lower = round(wilson_lower_bound(recommend_count, n), 4) if n else None

    return {
        "count": n,
        "avg": avg,
        "histogram": histogram,
        "own_hardware_count": len(own_scores),
        "own_hardware_avg": own_hardware_avg,
        "dims_avg": dims_avg,
        "dims_n": dims_n,
        "usage_count": usage_count,
        "low_sample": n < LOW_SAMPLE_N,
        "confidence": confidence,
        "rank_score": rank_score,
        "recommend_count": recommend_count,
        "recommend_rate": recommend_rate,
        "wilson_lower": lower,
    }


__all__ = [
    "AGGREGATE_FIELDS",
    "DEFAULT_PRIOR_MEAN",
    "DEFAULT_PRIOR_WEIGHT",
    "DIMENSION_KEYS",
    "FACT_SOURCES",
    "HISTOGRAM_KEYS",
    "LOW_SAMPLE_N",
    "RECOMMEND_MIN_SCORE",
    "RatingFact",
    "aggregate",
    "bayesian_score",
    "coerce_fact",
    "wilson_lower_bound",
]

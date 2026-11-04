"""评分统计纯函数的测试。

这些用例钉的是「静默失真」型问题：不报错但数字错。
    · 0 条被算成 0 分
    · 1 条 5 分压过 20 条 4.6
    · 四维缺项被补 0，拉低均值
    · 快照缺字段被补 0，页面显示一个不存在的结论
    · 把 Wilson 下界套到 1–5 均值上（它只适用于比例）

测试不连数据库、不连 GitHub：rating_stats / rating_adapter 都是纯函数。
"""
from __future__ import annotations

import pytest

from app.rating_adapter import (
    aggregate_from_snapshot_part,
    aggregate_snapshot,
    facts_from_snapshot_part,
)
from app.rating_stats import (
    AGGREGATE_FIELDS,
    DEFAULT_PRIOR_MEAN,
    DEFAULT_PRIOR_WEIGHT,
    LOW_SAMPLE_N,
    RatingFact,
    aggregate,
    bayesian_score,
    coerce_fact,
    wilson_lower_bound,
)


def fact(user: str, score: int, *, part: str = "part-a", own: bool = False,
         dims: dict | None = None, usage: dict | None = None,
         source: str = "web", ref: str | None = None) -> RatingFact:
    return RatingFact(user_key=user, part_id=part, score=score,
                      own_hardware=own, dims=dims, usage=usage,
                      source=source, external_ref=ref)


# ── 空样本 / 低样本 ─────────────────────────────────────────────────────────
def test_empty_aggregate_is_unknown_not_zero():
    result = aggregate([])
    assert result["count"] == 0
    assert result["avg"] is None, "没评过不是 0 分"
    assert result["rank_score"] is None, "空样本不参与排序"
    assert result["own_hardware_avg"] is None
    assert result["dims_avg"] is None and result["dims_n"] is None
    assert result["usage_count"] is None
    assert result["histogram"] == {str(i): 0 for i in range(1, 6)}
    assert result["low_sample"] is True
    assert result["confidence"] == 0.0
    assert result["recommend_rate"] is None and result["wilson_lower"] is None


def test_low_sample_boundary_is_three():
    assert LOW_SAMPLE_N == 3
    assert aggregate([fact("u1", 5), fact("u2", 4)])["low_sample"] is True
    assert aggregate([fact("u1", 5), fact("u2", 4), fact("u3", 3)])["low_sample"] is False


def test_aggregate_has_stable_shape():
    assert set(aggregate([fact("u1", 5)])) == set(AGGREGATE_FIELDS)
    assert set(aggregate([])) == set(AGGREGATE_FIELDS)


# ── 排序 / 置信度 ───────────────────────────────────────────────────────────
def test_single_five_does_not_beat_twenty_ratings_of_4_6():
    one = aggregate([fact("solo", 5)])
    twenty = aggregate([fact(f"u{i}", 5) for i in range(12)]
                       + [fact(f"v{i}", 4) for i in range(8)])

    assert one["avg"] == 5.0
    assert twenty["count"] == 20 and twenty["avg"] == 4.6
    assert twenty["rank_score"] > one["rank_score"], "排序分必须惩罚小样本"
    assert twenty["confidence"] > one["confidence"]
    assert sorted([one, twenty], key=lambda a: a["rank_score"], reverse=True)[0] is twenty


def test_bayesian_score_boundaries():
    assert bayesian_score(None, 0, DEFAULT_PRIOR_MEAN, DEFAULT_PRIOR_WEIGHT) == 3.0
    assert bayesian_score(5, 0, 3.0) == 3.0, "n=0 返回先验，不返回 0"
    assert bayesian_score(5, 1, 3.0, 5) == pytest.approx(20 / 6)
    assert bayesian_score(4.6, 20, 3.0, 5) == pytest.approx(107 / 25)
    assert bayesian_score(4.0, 2, 3.0, 0) == pytest.approx(4.0), "m=0 退化为原始均分"
    with pytest.raises(ValueError):
        bayesian_score(4.0, -1, 3.0)
    with pytest.raises(ValueError):
        bayesian_score(4.0, 1, 3.0, -5)


# ── own_hardware 分组 ───────────────────────────────────────────────────────
def test_own_hardware_grouped_separately():
    result = aggregate([
        fact("owner-1", 5, own=True),
        fact("owner-2", 4, own=True),
        fact("browser-1", 1),
    ])
    assert result["count"] == 3
    assert result["own_hardware_count"] == 2
    assert result["own_hardware_avg"] == 4.5, "只对装过机的样本求均值"
    assert result["avg"] == pytest.approx(3.33)


def test_no_owner_means_null_owner_average():
    result = aggregate([fact("u1", 5), fact("u2", 3)])
    assert result["own_hardware_count"] == 0
    assert result["own_hardware_avg"] is None, "没有装机样本不等于 0 分"


# ── dims / usage ────────────────────────────────────────────────────────────
def test_missing_dims_do_not_drag_down_average():
    result = aggregate([
        fact("u1", 5, dims={"value": 5}),
        fact("u2", 4, dims=None),
        fact("u3", 3),                       # dims 缺省
    ])
    assert result["count"] == 3
    assert result["dims_avg"] == {"value": 5.0}, "缺项不补 0，也不进分母"
    assert result["dims_n"] == {"value": 1}
    assert result["dims_avg"]["value"] == 5.0


def test_partial_dims_keep_per_dimension_denominator():
    result = aggregate([
        fact("u1", 4, dims={"value": 5, "build": 2}),
        fact("u2", 4, dims={"value": 3}),
    ])
    assert result["dims_avg"] == {"value": 4.0, "build": 2.0}
    assert result["dims_n"] == {"value": 2, "build": 1}


def test_usage_is_counted_not_averaged():
    result = aggregate([
        fact("u1", 4, usage={"duration": "3-12个月", "load": "常规"}),
        fact("u2", 5, usage={"duration": "3-12个月"}),
        fact("u3", 3),
    ])
    assert result["usage_count"] == {
        "duration": {"3-12个月": 2},
        "load": {"常规": 1},
    }


# ── Wilson 下界 ─────────────────────────────────────────────────────────────
def test_wilson_lower_bound_edges():
    assert wilson_lower_bound(0, 0) == 0.0
    assert wilson_lower_bound(0, 10) == 0.0
    assert wilson_lower_bound(1, 1) == pytest.approx(0.2065, abs=1e-3)
    assert wilson_lower_bound(100, 100) == pytest.approx(0.9630, abs=1e-3)
    assert wilson_lower_bound(3, 5, z=0) == pytest.approx(0.6), "z=0 退化为 phat"
    # 越界计数夹到 [0, n]，不产生 >1 或 <0 的下界
    assert wilson_lower_bound(10, 5) == wilson_lower_bound(5, 5)
    assert wilson_lower_bound(-3, 5) == wilson_lower_bound(0, 5)


def test_wilson_used_for_recommendation_rate_not_rating_mean():
    result = aggregate([
        fact("u1", 5), fact("u2", 4), fact("u3", 3), fact("u4", 2),
    ])
    # 1–5 均值是 3.5；Wilson 只作用在「≥4 推荐率」2/4 上
    assert result["avg"] == 3.5
    assert result["recommend_count"] == 2
    assert result["recommend_rate"] == 0.5
    assert result["wilson_lower"] == round(wilson_lower_bound(2, 4), 4)
    assert result["wilson_lower"] != result["rank_score"], "均值排序分不能用 Wilson"


# ── 事实规范化 ──────────────────────────────────────────────────────────────
def test_mapping_and_object_rows_follow_existing_model():
    class RatingRow:
        user_id = 7
        part_id = "part-a"
        score = 5
        own_hardware = True

    result = aggregate([
        RatingRow(),
        {"user_id": 8, "part_id": "part-a", "rating": 3, "own_hardware": False},
    ])
    assert result["count"] == 2 and result["avg"] == 4.0
    assert result["own_hardware_count"] == 1
    assert result["own_hardware_avg"] == 5.0


def test_invalid_score_and_source_are_rejected():
    with pytest.raises(ValueError):
        RatingFact(user_key="u", part_id="p", score=0)
    with pytest.raises(ValueError):
        RatingFact(user_key="u", part_id="p", score=6)
    with pytest.raises(ValueError):
        RatingFact(user_key="u", part_id="p", score=True)
    with pytest.raises(ValueError):
        RatingFact(user_key="u", part_id="p", score=4, source="email")
    with pytest.raises(ValueError):
        coerce_fact({"part_id": "p", "score": 4})


# ── issue 快照兼容 ──────────────────────────────────────────────────────────
SNAPSHOT_PART = {
    "count": 2,
    "avg": 4.0,
    "histogram": {"1": 0, "2": 0, "3": 1, "4": 0, "5": 1},
    "own_hardware_count": 1,
    "own_hardware_avg": 5.0,
    "dims_avg": {"value": 5.0},
    "dims_n": {"value": 1},
    "usage_count": {"duration": {"3-12个月": 1}},
    "low_sample": True,
    "mine": None,
    "votes": [
        {"issue": 11, "author": "dave", "part_id": "part-a", "score": 5,
         "own_hardware": True, "note": "装过", "at": "2026-10-28T00:00:00Z",
         "dims": {"value": 5}, "usage": {"duration": "3-12个月"}},
        {"issue": 12, "author": "erin", "part_id": "part-a", "score": 3,
         "own_hardware": False, "note": "只看参数", "at": "2026-10-29T00:00:00Z",
         "dims": None, "usage": None},
    ],
}


def test_snapshot_part_converts_to_aggregate_shape():
    result = aggregate_from_snapshot_part(SNAPSHOT_PART)
    assert set(result) == set(AGGREGATE_FIELDS)

    assert result["count"] == 2 and result["avg"] == 4.0
    assert result["histogram"] == {"1": 0, "2": 0, "3": 1, "4": 0, "5": 1}
    assert result["own_hardware_count"] == 1
    assert result["own_hardware_avg"] == 5.0
    assert result["dims_avg"] == {"value": 5.0}
    assert result["dims_n"] == {"value": 1}
    assert result["usage_count"] == {"duration": {"3-12个月": 1}}
    assert result["low_sample"] is True

    # 派生值按当前口径现算，不照抄快照里的旧数
    assert result["confidence"] == round(2 / 7, 4)
    assert result["rank_score"] == round(bayesian_score(4.0, 2, 3.0, 5), 4)
    assert result["recommend_count"] == 1
    assert result["recommend_rate"] == 0.5
    assert result["wilson_lower"] == round(wilson_lower_bound(1, 2), 4)


def test_snapshot_missing_fields_stay_null_not_zero():
    result = aggregate_from_snapshot_part(
        {"count": 1, "avg": 5.0, "histogram": {"5": 1}})
    assert result["own_hardware_count"] is None
    assert result["own_hardware_avg"] is None
    assert result["dims_avg"] is None
    assert result["dims_n"] is None
    assert result["usage_count"] is None
    assert result["low_sample"] is True, "缺 low_sample 时由 count 推出"


def test_snapshot_old_format_keeps_explicit_zero_but_not_missing():
    # v1 快照可能明确写了 own_hardware_count=0，但没有 own_hardware_avg / dims
    result = aggregate_from_snapshot_part({
        "count": 1, "avg": 5.0, "histogram": {"5": 1},
        "own_hardware_count": 0,
    })
    assert result["own_hardware_count"] == 0, "明确的 0 是真实值，要保留"
    assert result["own_hardware_avg"] is None, "缺失的均值不能补 0"
    assert result["dims_avg"] is None and result["dims_n"] is None


def test_empty_snapshot_part_is_unknown_not_zero():
    result = aggregate_from_snapshot_part({})
    for key in ("count", "avg", "histogram", "own_hardware_count",
                "own_hardware_avg", "dims_avg", "dims_n", "usage_count",
                "low_sample", "confidence", "rank_score", "recommend_count",
                "recommend_rate", "wilson_lower"):
        assert result[key] is None, f"{key} 缺失时应为 None"


def test_snapshot_votes_can_be_rebuilt_into_facts():
    facts = facts_from_snapshot_part(SNAPSHOT_PART, part_id="part-a")
    assert len(facts) == 2
    assert facts[0].user_key == "dave" and facts[0].source == "issue"
    assert facts[0].external_ref == "11"
    assert facts[0].own_hardware is True
    assert facts[0].dims == {"value": 5}
    assert facts[1].user_key == "erin" and facts[1].dims is None

    rebuilt = aggregate(facts)
    assert rebuilt["count"] == 2 and rebuilt["avg"] == 4.0
    assert rebuilt["own_hardware_count"] == 1
    assert rebuilt["dims_avg"] == {"value": 5.0}
    assert rebuilt["usage_count"] == {"duration": {"3-12个月": 1}}


def test_aggregate_snapshot_covers_every_part():
    result = aggregate_snapshot({"parts": {"part-a": SNAPSHOT_PART, "part-b": {}}})
    assert set(result) == {"part-a", "part-b"}
    assert result["part-a"]["avg"] == 4.0
    assert result["part-b"]["avg"] is None

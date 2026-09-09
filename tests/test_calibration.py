"""Offline calibration masks, denominators, paired rules and immutability."""

from copy import deepcopy

import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.spatial.calibration import (
    candidate_definitions,
    compare_distributions,
    composition,
    eligibility,
    empirical_thresholds,
    evaluate_candidates,
    goalkeeper_comparison,
    prepare,
    resolve_rule,
    summarize_retention,
)
from leverkusen.spatial.geometry import build_frame_geometry


@pytest.fixture
def geometry():
    rows = []
    for match in (1, 2):
        frames, events = [], []
        for i in range(5):
            players = [
                {
                    "location": [10 + j * 6, 20 + (j % 3) * 10],
                    "teammate": j % 2 == 0,
                    "keeper": j == 0,
                    "actor": j == 1,
                }
                for j in range(i + 2)
            ]
            if i == 1:
                players[-1]["location"] = [125, -2]
            if i == 2:
                players.append(deepcopy(players[1]))
            frames.append(
                {
                    "event_uuid": str(i),
                    "freeze_frame": players,
                    "visible_area": [0, 0, 20 + i * 15, 0, 20 + i * 15, 80, 0, 80],
                }
            )
            events.append(
                {"id": str(i), "type": {"name": "Pass" if i % 2 else "Carry"}}
            )
        rows.append(
            build_frame_geometry(
                match, events, frames, source_revision=STATSBOMB_REVISION
            )
        )
    return pd.concat(rows, ignore_index=True)


def rule_for(table, name, metric, variant=("all_visible", "included")):
    candidate = next(c for c in candidate_definitions() if c.candidate == name)
    return resolve_rule(candidate, metric, variant, empirical_thresholds(table))


def test_deterministic_definitions_and_order_independent_thresholds(geometry):
    assert candidate_definitions() == candidate_definitions()
    pd.testing.assert_frame_equal(
        empirical_thresholds(geometry),
        empirical_thresholds(geometry.sample(frac=1, random_state=4)),
    )
    defs = candidate_definitions()
    assert len({c.candidate for c in defs}) == len(defs)
    assert all(c.paired_primary in {d.candidate for d in defs} for c in defs)


def test_quantiles_weight_original_frames_and_retain_integer_ties(geometry):
    thresholds = empirical_thresholds(geometry)
    area = thresholds.loc[
        thresholds.variable.eq("area") & thresholds["quantile"].eq(20)
    ].iloc[0]
    assert area.threshold == pytest.approx(
        geometry.drop_duplicates(
            ["match_id", "frame_index"]
        ).visible_area_fraction.quantile(0.2)
    )
    counts = thresholds.loc[thresholds.variable.eq("count")]
    assert counts.threshold.mod(1).eq(0).all()
    assert counts.observed_at_threshold.gt(0).all()


def test_baseline_uses_only_locked_status_no_hidden_threshold(geometry):
    t = prepare(geometry)
    group = t.loc[
        t.selected_subset.eq("all_visible") & t.goalkeeper_policy.eq("included")
    ]
    for metric in (
        "visible_width",
        "convex_hull_area",
        "mean_nearest_neighbor_distance",
    ):
        mask = eligibility(group, metric, rule_for(t, "A", metric))
        assert mask.equals(group[f"{metric}_status"].eq("ok"))
    assert eligibility(group, "visible_width", rule_for(t, "A", "visible_width")).all()


def test_metric_specific_rules_and_ambiguity_policy(geometry):
    t = prepare(geometry)
    hull = rule_for(t, "D_sensitivity", "convex_hull_area")
    nn = rule_for(t, "D_sensitivity", "mean_nearest_neighbor_distance")
    assert hull["count_quantile"] == 25 and nn["count_quantile"] == 5
    assert hull["exclude_oob"] and not hull["exclude_coincidence"]
    assert nn["exclude_coincidence"] and not nn["exclude_oob"]
    depth = rule_for(t, "D_sensitivity", "visible_depth")
    assert depth["minimum_n"] is None and not depth["exclude_oob"]
    mask = eligibility(t, "visible_width", rule_for(t, "D_primary", "visible_width"))
    assert not mask[t.actor_status.eq("multiple")].any()


def test_oob_is_entire_frame_including_unaffected_subsets(geometry):
    t = prepare(geometry)
    group = t.loc[
        t.selected_subset.eq("teammate_false") & t.goalkeeper_policy.eq("excluded")
    ]
    assert group.loc[group.frame_index.eq(1), "n_out_of_bounds_points"].eq(0).all()
    mask = eligibility(
        group, "visible_width", rule_for(t, "OOB_B_sensitivity", "visible_width")
    )
    assert not mask[group.frame_index.eq(1)].any()
    assert rule_for(t, "OOB_C_sensitivity", "visible_width")["exclude_oob"]
    assert not rule_for(t, "OOB_C_sensitivity", "visible_depth")["exclude_oob"]


def test_paired_primary_sensitivity_and_no_mutation(geometry):
    before = geometry.copy(deep=True)
    t = prepare(geometry)
    for metric in (
        "visible_width",
        "convex_hull_area",
        "mean_nearest_neighbor_distance",
    ):
        primary = eligibility(t, metric, rule_for(t, "D_primary", metric))
        sensitivity = eligibility(t, metric, rule_for(t, "D_sensitivity", metric))
        assert not (sensitivity & ~primary).any()
    assert len(t) == len(geometry)
    pd.testing.assert_frame_equal(geometry, before)
    # Supplied excursion contributes an 82-unit span: no clipping or point deletion.
    width = t.loc[
        t.selected_subset.eq("all_visible")
        & t.goalkeeper_policy.eq("included")
        & t.frame_index.eq(1),
        "visible_depth",
    ]
    assert width.eq(115).all()


def test_retention_includes_zero_retained_matches(geometry):
    t = prepare(geometry)
    group = t.loc[
        t.selected_subset.eq("all_visible") & t.goalkeeper_policy.eq("included")
    ]
    mask = group.match_id.eq(1)
    comp = composition(group, mask, "visible_width", "match_id")
    summary = summarize_retention(group, mask, "visible_width", comp)
    assert summary["eligible_frames"] == 5 and summary["eligible_percent"] == 50
    assert summary["affected_matches"] == 1
    assert summary["minimum_retained_per_match"] == 0
    assert summary["median_retained_per_match"] == 2.5
    assert comp.eligible_frames.tolist() == [5, 0]


def test_distribution_exact_denominators_and_zero_relative_baseline():
    d = compare_distributions(pd.Series([0.0, 1.0, 2.0, None]), pd.Series([1.0, 2.0]))
    assert d["full_mean"] == 1 and d["retained_mean"] == 1.5
    assert d["delta_median"] == 0.5 and d["relative_delta_mean"] == 0.5
    assert d["full_std"] == 1
    assert d["retained_p05"] == pytest.approx(1.05)
    assert pd.isna(
        compare_distributions(pd.Series([0.0, 0.0]), pd.Series([0.0]))[
            "relative_delta_mean"
        ]
    )
    assert pd.isna(
        compare_distributions(pd.Series([1.0]), pd.Series(dtype=float))["retained_mean"]
    )


def test_keeper_pairing_uses_match_and_ordinal_and_reports_availability(geometry):
    pairs = goalkeeper_comparison(geometry.sample(frac=1, random_state=1))
    count = pairs.loc[
        pairs.selected_subset.eq("all_visible")
        & pairs.metric.eq("visible_player_count")
        & pairs.scope.eq("keeper_removed")
    ].iloc[0]
    assert count.jointly_defined == 10 and count["mean"] == -1
    assert count.mean_absolute_delta == 1


@pytest.mark.parametrize("damage", ["revision", "duplicate", "status", "coverage"])
def test_rejects_inconsistent_inputs(geometry, damage):
    if damage == "revision":
        geometry.loc[0, "statsbomb_revision"] = "wrong"
    elif damage == "duplicate":
        geometry = pd.concat([geometry, geometry.iloc[[0]]])
    elif damage == "status":
        geometry.loc[0, "visible_width_status"] = "empty_points"
    else:
        geometry.loc[0, "visible_area_fraction"] = 0.99
    with pytest.raises(ValueError):
        prepare(geometry)


def test_end_to_end_candidates_preserve_all_input_and_pair_outputs(geometry):
    before = geometry.copy(deep=True)
    outputs = evaluate_candidates(geometry)
    pd.testing.assert_frame_equal(geometry, before)
    ret = outputs["candidate_retention"]
    assert len(ret) == 20 * 6 * 9
    assert ret.population_frames.eq(10).all()
    assert ret.eligible_frames.le(ret.mathematically_defined_frames).all()
    assert not any(
        "location" in c or "freeze_frame" in c
        for df in outputs.values()
        for c in df.columns
    )
    assert outputs["threshold_stability"].successive_frames_removed.ge(0).all()
    dist = outputs["candidate_distribution_effects"]
    sensitivity = dist.loc[dist.candidate.eq("D_sensitivity")]
    assert sensitivity.paired_primary.eq("D_primary").all()
    assert sensitivity.eligible_frames.le(sensitivity.primary_eligible_frames).all()
    support = outputs["count_coverage_support"]
    assert (
        support.groupby(["selected_subset", "goalkeeper_policy"])
        .frames.sum()
        .eq(10)
        .all()
    )


def test_raw_points_unchanged_and_duplicates_preserved():
    frames = [
        {
            "event_uuid": "x",
            "visible_area": [0, 0, 10, 0, 10, 10, 0, 10],
            "freeze_frame": [
                {
                    "location": [-5, 0],
                    "teammate": True,
                    "keeper": False,
                    "actor": False,
                },
                {
                    "location": [-5, 0],
                    "teammate": True,
                    "keeper": False,
                    "actor": False,
                },
                {
                    "location": [130, 90],
                    "teammate": False,
                    "keeper": True,
                    "actor": True,
                },
            ],
        }
    ]
    original = deepcopy(frames)
    table = prepare(
        build_frame_geometry(
            1, [{"id": "x"}], frames, source_revision=STATSBOMB_REVISION
        )
    )
    group = table.loc[
        table.selected_subset.eq("all_visible") & table.goalkeeper_policy.eq("included")
    ]
    assert group.visible_depth.iloc[0] == 135
    assert group.visible_player_count.iloc[0] == 3
    assert group.n_coincident_records.iloc[0] == 1
    assert eligibility(
        group, "visible_width", rule_for(table, "A", "visible_width")
    ).all()
    assert not eligibility(
        group, "visible_width", rule_for(table, "OOB_B_sensitivity", "visible_width")
    ).any()
    assert frames == original and len(frames[0]["freeze_frame"]) == 3


def test_missing_coverage_and_anomalies_have_explicit_candidate_semantics(geometry):
    geometry.loc[geometry.frame_index.eq(0), "visible_area_fraction"] = float("nan")
    geometry.loc[geometry.frame_index.eq(0), "n_out_of_bounds_points"] = float("nan")
    t = prepare(geometry)
    group = t.loc[
        t.selected_subset.eq("all_visible") & t.goalkeeper_policy.eq("included")
    ]
    assert eligibility(group, "visible_width", rule_for(t, "A", "visible_width"))[
        group.frame_index.eq(0)
    ].all()
    assert not eligibility(
        group, "visible_width", rule_for(t, "C_q20", "visible_width")
    )[group.frame_index.eq(0)].any()
    assert not eligibility(
        group, "visible_width", rule_for(t, "OOB_B_sensitivity", "visible_width")
    )[group.frame_index.eq(0)].any()

"""Focused offline grouping, binning and pairing tests on toy observations."""

from copy import deepcopy
from math import sqrt

import pandas as pd
import pytest

from leverkusen.spatial.geometry import build_frame_geometry
from leverkusen.spatial import observation_sensitivity as s


@pytest.fixture
def observations():
    locations = [
        [(0, 0), (3, 0), (0, 4), (10, 0)],
        [(0, 0), (6, 0), (0, 8)],
        [(9, 9)],
        [(0, 0), (20, 10)],
        [(0, 0), (12, 0), (0, 8)],
    ]
    raw = [
        {
            "freeze_frame": [
                {
                    "location": list(p),
                    "actor": j == 0,
                    "teammate": j != 2,
                    "keeper": True
                    if (i, j) in ((0, 3), (2, 0))
                    else None
                    if (i, j) == (3, 1)
                    else False,
                }
                for j, p in enumerate(points)
            ]
        }
        for i, points in enumerate(locations)
    ]
    table = build_frame_geometry(1, [], raw, source_revision=s.STATSBOMB_REVISION)
    coverage = {0: 0.1, 1: 0.2, 2: 0.3, 3: None, 4: 0.9}
    table["visible_area_fraction"] = table["frame_index"].map(coverage)
    return raw, table


def test_exact_n_grouping_denominators_and_quantiles(observations):
    _, table = observations
    result = s.summarize_by_point_count(table).set_index(
        ["selected_subset", "goalkeeper_policy", "n_valid_points_used", "metric"]
    )
    depth = result.loc[("all_visible", "included", 3, "visible_depth")]
    assert depth["frame_count"] == depth["denominator"] == 2
    assert depth["mean"] == depth["median"] == 9
    assert depth["std"] == pytest.approx(sqrt(18))
    assert depth[["p05", "p25", "p75", "p95"]].tolist() == pytest.approx(
        [6.3, 7.5, 10.5, 11.7]
    )
    hull = result.loc[("all_visible", "included", 1, "convex_hull_area")]
    assert hull["frame_count"] == hull["na_count"] == 1
    assert hull["denominator"] == 0
    assert hull[["mean", "median", "std", "p05", "p95"]].isna().all()


def test_binning_is_deterministic_shared_and_original_frame_weighted(observations):
    _, table = observations
    table["visible_area_fraction"] = table["frame_index"].map(
        {0: 0.1, 1: 0.1, 2: 0.1, 3: 0.3, 4: 0.9}
    )
    labeled, bounds = s.bin_visible_area(table)
    shuffled, shuffled_bounds = s.bin_visible_area(
        table.sample(frac=1, random_state=17)
    )
    keys = [*s.FRAME, *s.VARIANT]
    pd.testing.assert_frame_equal(
        labeled.sort_values(keys).reset_index(drop=True),
        shuffled.sort_values(keys).reset_index(drop=True),
    )
    pd.testing.assert_frame_equal(bounds, shuffled_bounds)
    assert bounds["original_frame_count"].sum() == 5  # Not 30 variants.
    assert labeled.groupby(s.FRAME)["visible_area_bin"].nunique().eq(1).all()
    assert (
        labeled.loc[
            labeled["visible_area_fraction"].eq(0.1), "visible_area_bin"
        ].nunique()
        == 1
    )
    assert bounds["effective_bins"].iloc[0] < 5  # Tied edges collapse.
    assert bounds.iloc[0]["lower"] == 0.1 and bounds.iloc[-1]["upper"] == 0.9


@pytest.mark.parametrize(
    "coverage,expected_bin,effective", [(0.0, "B1", 1), (None, "unavailable", 0)]
)
def test_constant_or_missing_coverage_retains_every_row(
    observations, coverage, expected_bin, effective
):
    _, table = observations
    table["visible_area_fraction"] = coverage
    labeled, bounds = s.bin_visible_area(table)
    assert len(labeled) == len(table)
    assert labeled["visible_area_bin"].eq(expected_bin).all()
    assert bounds.iloc[0]["effective_bins"] == effective
    assert bounds.iloc[0]["original_frame_count"] == 5


def test_shared_coverage_inconsistency_is_not_arbitrarily_resolved(observations):
    _, table = observations
    table.loc[0, "visible_area_fraction"] = 0.99
    with pytest.raises(ValueError, match="agree"):
        s.bin_visible_area(table)


def test_same_frame_pairing_na_exclusion_and_unknown_keeper_denominators(observations):
    _, table = observations
    result = s.summarize_goalkeeper_pairs(
        table.sample(frac=1, random_state=3)
    ).set_index(["selected_subset", "scope", "metric"])
    depth = result.loc[("all_visible", "all_frames", "visible_depth")]
    assert depth["total_frames"] == depth["scope_frames"] == 5
    assert depth["keeper_removed_frames"] == 2
    assert depth["unknown_keeper_removed_frames"] == 1
    assert depth["jointly_defined_count"] == 4 and depth["na_pair_count"] == 1
    assert depth["mean"] == -6.75 and depth["median"] == -3.5
    assert depth["mean_absolute_delta"] == 6.75
    assert depth["numerically_changed_count"] == 2
    assert depth["proportion_numerically_changed"] == 0.5
    affected = result.loc[("all_visible", "keeper_removed", "visible_depth")]
    assert affected["scope_frames"] == 2 and affected["jointly_defined_count"] == 1
    assert affected["mean"] == -7 and affected["proportion_numerically_changed"] == 1
    hull = result.loc[("all_visible", "all_frames", "convex_hull_area")]
    assert hull["jointly_defined_count"] == 3  # Never turn undefined hulls into zeros.
    assert hull["mean"] == pytest.approx(-14 / 3)


def test_pairing_uses_match_and_ordinal_not_event_uuid(observations):
    _, first = observations
    second = first.copy()
    second["match_id"] = 2
    second["visible_depth"] *= 2
    together = pd.concat([first, second], ignore_index=True).sample(
        frac=1, random_state=8
    )
    result = s.summarize_goalkeeper_pairs(together).set_index(
        ["selected_subset", "scope", "metric"]
    )
    row = result.loc[("all_visible", "all_frames", "visible_depth")]
    assert row["jointly_defined_count"] == 8
    assert row["mean"] == -10.125
    with pytest.raises(ValueError, match="Duplicate"):
        s.summarize_goalkeeper_pairs(pd.concat([first, first]))


def test_all_summaries_retain_low_n_missing_area_and_flags_without_mutation(
    observations,
):
    raw, table = observations
    before_raw, before = deepcopy(raw), table.copy(deep=True)
    result = s.summarize_observation_sensitivity(table)
    pd.testing.assert_frame_equal(before, table)
    assert raw == before_raw
    by_n = result["metric_by_valid_point_count"]
    assert 0 in set(by_n["n_valid_points_used"])
    assert by_n.groupby([*s.VARIANT, "metric"])["frame_count"].sum().eq(5).all()
    by_area = result["metric_by_visible_area"]
    assert "unavailable" in set(by_area["visible_area_bin"])
    assert by_area.groupby([*s.VARIANT, "metric"])["frame_count"].sum().eq(5).all()
    joint = result["visibility_vs_player_count"]
    assert joint.groupby(s.VARIANT)["frame_count"].sum().eq(5).all()
    # Existing input flags are not an eligibility selector in this diagnostic.
    assert table["measurement_flags"].str.contains("missing_visible_area").all()


def test_inconsistent_metric_status_is_not_silently_used(observations):
    _, table = observations
    table.loc[0, "visible_depth_status"] = "numeric_error"
    with pytest.raises(ValueError, match="inconsistency"):
        s.summarize_observation_sensitivity(table)

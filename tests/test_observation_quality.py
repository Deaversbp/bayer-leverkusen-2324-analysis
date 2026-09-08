"""Offline checks for diagnostic topology, multiplicity and selection contracts."""

from copy import deepcopy
from math import sqrt

import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Polygon, box

from leverkusen.spatial import observation_quality as q
from leverkusen.spatial.geometry import build_frame_geometry, measure_points


@pytest.mark.parametrize(
    "point,excess,sides",
    [
        ((-3, 84), (3, 4, 5), (True, False, False, True)),
        ((122, -2), (2, 2, sqrt(8)), (False, True, True, False)),
        ((120, 80), (0, 0, 0), (False, False, False, False)),
        ((-1e-12, 40), (1e-12, 0, 1e-12), (True, False, False, False)),
    ],
)
def test_excursion_exact_sides_and_rectangle_distance(point, excess, sides):
    result = q.excursion(point)
    assert tuple(result[s] for s in q.SIDES) == sides
    assert result["sides_violated"] == sum(sides)
    assert tuple(
        result[s] for s in ("x_excess", "y_excess", "pitch_distance")
    ) == pytest.approx(excess)


@pytest.mark.parametrize("bad", [(float("nan"), 0), (True, 3), (0,), ("0", 0)])
def test_invalid_excursions_rejected(bad):
    with pytest.raises(ValueError):
        q.excursion(bad)


def test_polygon_inside_crossing_touching_and_outside():
    for flat, inside, outside, contained, touches in (
        ([10, 10, 20, 10, 20, 20, 10, 20], 100, 0, True, False),
        ([-10, 0, 10, 0, 10, 10, -10, 10], 100, 100, False, True),
        ([0, 0, 10, 0, 10, 10, 0, 10], 100, 0, True, True),
        ([-20, 10, -10, 10, -10, 20, -20, 20], 0, 100, False, False),
    ):
        original = flat.copy()
        polygon, result = q.polygon_diagnostics(flat)
        assert polygon.area == inside + outside
        assert result["area_inside_pitch"] == inside
        assert result["area_outside_pitch"] == outside
        assert result["contained_in_pitch"] == contained
        assert result["intersects_pitch_boundary"] == touches
        assert result["fraction_outside_pitch"] == outside / (inside + outside)
        assert result["visible_area_fraction"] == inside / 9600
        assert flat == original


@pytest.mark.parametrize("flat", [None, [], [0, 1, 2], [0, 0, 2, 2, 0, 2, 2, 0]])
def test_invalid_polygon_is_unavailable_without_repair(flat):
    polygon, result = q.polygon_diagnostics(flat)
    assert polygon is None
    assert result["area_outside_pitch"] is None
    assert result["visible_area_fraction"] is None
    info = q.point_polygon_diagnostics([(1, 1)], polygon)[0]
    assert info == {
        "polygon_status": "unavailable",
        "polygon_covered": None,
        "visible_boundary_distance": None,
    }
    edge, ties = q.edge_diagnostics([(1, 1)], polygon)
    assert edge["edge_status"] == "polygon_unavailable"
    assert edge["minimum_selected_edge_distance"] is None
    assert ties == []


def test_point_polygon_inside_boundary_outside_and_unsigned_distances():
    result = q.point_polygon_diagnostics(
        [(5, 5), (0, 4), (-3, 4), (-3, -4)], box(0, 0, 10, 10)
    )
    assert [r["polygon_status"] for r in result] == [
        "inside",
        "boundary",
        "outside",
        "outside",
    ]
    assert [r["polygon_covered"] for r in result] == [True, True, False, False]
    assert [r["visible_boundary_distance"] for r in result] == [5, 0, 3, 5]
    invalid = Polygon([(0, 0), (2, 2), (0, 2), (2, 0)])
    assert (
        q.point_polygon_diagnostics([(1, 1)], invalid)[0]["polygon_status"]
        == "unavailable"
    )


def test_extreme_selection_preserves_every_tie_and_distances():
    points = [(1, 2), (1, 5), (8, 8), (5, 2)]
    assert q.extreme_indices(points) == {
        "min_x": [0, 1],
        "max_x": [2],
        "min_y": [0, 3],
        "max_y": [2],
    }
    result, tied = q.edge_diagnostics(points, box(0, 0, 10, 10))
    assert result["min_y_edge_distance"] == 1
    assert result["minimum_selected_edge_distance"] == 1
    assert result["median_selected_edge_distance"] == 1.5
    assert [r["edge_distance"] for r in tied if r["extreme"] == "min_y"] == [1, 2]
    assert q.edge_diagnostics([], box(0, 0, 10, 10))[0]["edge_status"] == "empty_points"


def test_coincident_grouping_and_empirical_multiplicity_influence():
    points = [(0, 0), (0, 0), (6, 0), (0, 8)]
    assert q.coincident_groups(points) == [[0, 1]]
    base = measure_points(points)
    added = measure_points(points + [points[0]])
    for metric in ("visible_width", "visible_depth", "convex_hull_area"):
        assert added[metric] == base[metric]
    for metric in (
        "visible_player_count",
        "centroid_x",
        "centroid_y",
        "mean_pairwise_distance",
        "median_pairwise_distance",
        "mean_nearest_neighbor_distance",
    ):
        assert added[metric] != base[metric]
    assert points == [(0, 0), (0, 0), (6, 0), (0, 8)]


def toy_observations():
    frames = []
    for i in range(4):
        frames.append(
            {
                "event_uuid": f"event{i}",
                "visible_area": [-5, 0, 120, 0, 120, 80, -5, 80],
                "freeze_frame": [
                    {
                        "location": list(p),
                        "teammate": j % 2 == 0,
                        "actor": j < 2,
                        "keeper": j == 3,
                    }
                    for j, p in enumerate([(-2, 3), (-2, 3), (5 + i, 8), (20, 20)])
                ],
            }
        )
    events = [{"id": f"event{i}", "type": {"name": "Pass"}} for i in range(4)]
    geometry = build_frame_geometry(
        1, events, frames, source_revision=q.loader.STATSBOMB_REVISION
    )
    return frames, q.add_keeper_deltas(geometry)


def test_match_diagnostics_no_mutation_clipping_or_threshold_filter():
    frames, geometry = toy_observations()
    original, old_geometry = deepcopy(frames), geometry.copy(deep=True)
    enriched, diagnostics, _ = q.inspect_match(frames, geometry)
    assert frames == original
    pd.testing.assert_frame_equal(geometry, old_geometry)
    assert len(enriched) == 24
    assert len(diagnostics["out_of_bounds_records"]) == 8
    assert diagnostics["out_of_bounds_records"].polygon_status.eq("inside").all()
    assert enriched.n_out_of_bounds_points.gt(0).any()
    pd.testing.assert_frame_equal(enriched[list(geometry)], geometry)
    assert len(diagnostics["multiple_actor_review"]) == 4
    assert diagnostics["multiple_actor_review"].actor_pair_distance_max.eq(0).all()


def test_representative_selection_deterministic_ties_and_all_multiple_actors():
    frames, geometry = toy_observations()
    enriched, _, _ = q.inspect_match(frames, geometry)
    a = q.select_representatives(enriched)
    b = q.select_representatives(enriched.sample(frac=1, random_state=4))
    pd.testing.assert_frame_equal(a, b)
    assert len(a.loc[a.selection_rule.eq("multiple_actor")]) == 4
    assert a.loc[a.selection_rule.eq("max_x_excess"), "frame_index"].iloc[0] == 0


def test_quantiles_keep_ties_missing_and_constant_values():
    values = pd.Series([0, 0, 0, 1, 2, np.nan])
    labels, bounds = q.quantile_groups(values)
    assert labels.iloc[:3].nunique() == 1
    assert labels.iloc[-1] == "unavailable"
    assert bounds[0]["lower_inclusive"]
    labels, bounds = q.quantile_groups(pd.Series([2, 2]))
    assert labels.tolist() == ["Q1", "Q1"]
    assert bounds[0]["lower"] == bounds[0]["upper"] == 2


def test_actor_flags_alone_cannot_change_locked_geometry():
    frames, original = toy_observations()
    changed = deepcopy(frames)
    for frame in changed:
        for record in frame["freeze_frame"]:
            record["actor"] = False
    altered = build_frame_geometry(
        1, [], changed, source_revision=q.loader.STATSBOMB_REVISION
    )
    pd.testing.assert_frame_equal(original[list(q.METRICS)], altered[list(q.METRICS)])


def test_invalid_polygon_does_not_remove_geometry_or_oob_records():
    frames, _ = toy_observations()
    frames[0]["visible_area"] = [0, 0, 2, 2, 0, 2, 2, 0]
    geometry = q.add_keeper_deltas(
        build_frame_geometry(
            1,
            [{"id": f"event{i}"} for i in range(4)],
            frames,
            source_revision=q.loader.STATSBOMB_REVISION,
        )
    )
    enriched, diagnostics, _ = q.inspect_match(frames, geometry)
    first = enriched.loc[enriched.frame_index.eq(0)]
    assert len(first) == 6
    assert first.minimum_selected_edge_distance.isna().all()
    assert first.visible_width.notna().all()
    oob = diagnostics["out_of_bounds_records"]
    assert oob.loc[oob.frame_index.eq(0), "polygon_status"].eq("unavailable").all()


def test_summaries_keep_variant_denominators_and_original_frame_inventory():
    frames, geometry = toy_observations()
    enriched, diagnostics, _ = q.inspect_match(frames, geometry)
    summaries = q.summarize_quality(enriched, diagnostics)
    population = (
        summaries["out_of_bounds_summary"]
        .query("scope == 'population' and measure == 'pitch_distance'")
        .iloc[0]
    )
    assert population["rows"] == 8
    assert population.affected_frames == 4
    assert population.affected_matches == 1
    groups = (
        summaries["coincident_records_summary"].query("scope == 'population'").iloc[0]
    )
    assert groups.groups == groups.excess_records == groups.affected_frames == 4
    relation = summaries["metric_edge_relationship"]
    counts = relation.groupby([*q.VARIANT, "metric", "edge_measure"])["rows"].sum()
    assert counts.eq(4).all()
    empty_hulls = relation.query(
        "metric == 'convex_hull_area' and selected_subset == 'teammate_true'"
    )
    assert empty_hulls.denominator.eq(0).all()
    assert empty_hulls["median"].isna().all()


def test_raw_frame_id_mismatch_aborts_diagnostics():
    frames, geometry = toy_observations()
    frames[0]["event_uuid"] = "different"
    with pytest.raises(ValueError, match="ordinal/event ID"):
        q.inspect_match(frames, geometry)


def test_side_representative_score_uses_only_points_violating_that_side():
    frames, _ = toy_observations()
    frames[0]["freeze_frame"][0]["location"] = [-1, 40]
    frames[0]["freeze_frame"][1]["location"] = [10, -15]
    geometry = q.add_keeper_deltas(
        build_frame_geometry(
            1,
            [{"id": f"event{i}"} for i in range(4)],
            frames,
            source_revision=q.loader.STATSBOMB_REVISION,
        )
    )
    enriched, _, _ = q.inspect_match(frames, geometry)
    selected = q.select_representatives(enriched)
    winner = selected.loc[selected.selection_rule.eq("largest_on_x_below_0")].iloc[0]
    assert winner.frame_index == 1
    assert winner.selection_value == 2


def test_offline_runner_preserves_source_and_writes_only_derived_outputs(
    tmp_path, monkeypatch
):
    from leverkusen.visualization import observation_quality as plotting

    frames, geometry = toy_observations()
    # The runner creates its own paired diagnostic columns.
    geometry = geometry.drop(
        columns=[c for c in geometry if c.startswith("abs_keeper_delta_")]
    )
    source = tmp_path / "phase2a.csv"
    geometry.to_csv(source, index=False)
    original_bytes = source.read_bytes()
    fetched = []

    def load(match_id):
        fetched.append(match_id)
        return frames

    monkeypatch.setattr(q.loader, "load_360", load)
    monkeypatch.setattr(plotting, "write_quality_figures", lambda *args: None)
    output = tmp_path / "diagnostics"
    result = q.run_observation_quality(
        source, output, tmp_path / "figures", progress=lambda _: None
    )
    assert fetched == [1]
    assert source.read_bytes() == original_bytes
    assert result["run_summary"].iloc[0].original_frames == 4
    assert result["run_summary"].iloc[0].variant_rows == 24
    for path in output.iterdir():
        assert path.suffix == ".csv"
        fields = pd.read_csv(path, nrows=0).columns
        assert not {"freeze_frame", "location", "visible_area", "x", "y"}.intersection(
            fields
        )
    invariants = result["coincident_metric_sensitivity"].query(
        "metric in ['visible_width', 'visible_depth', 'convex_hull_area']"
    )
    assert invariants.changed_exact_count.eq(0).all()

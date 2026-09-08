"""Offline contract tests against hand-computable record geometry."""

from copy import deepcopy
from math import sqrt
from unittest.mock import Mock, PropertyMock

import pandas as pd
import pytest
from shapely.errors import GEOSException

from leverkusen.data.observability import frame_observability
from leverkusen.spatial import geometry as g


def player(point=(0, 0), teammate=True, keeper=False, actor=False):
    return dict(location=list(point), teammate=teammate, keeper=keeper, actor=actor)


def frame(players, **kwargs):
    return dict(
        freeze_frame=players,
        event_uuid="e",
        visible_area=[0, 0, 120, 0, 120, 80, 0, 80],
        **kwargs,
    )


def rows(raw):
    return g.frame_geometry(raw, match_id=1, frame_index=7, source_revision="synthetic")


@pytest.mark.parametrize("point", [[1, 2.5], (0, 80), [-1, 121], [10**400, 0]])
def test_numeric_values_preserved(point):
    assert g.valid_point(point) == tuple(point)
    assert type(g.valid_point(point)[0]) is type(point[0])


@pytest.mark.parametrize(
    "point",
    [
        None,
        [],
        [1],
        [1, 2, 3],
        "1,2",
        {"x": 1, "y": 2},
        ["1", 2],
        [True, 2],
        [1, False],
        [float("nan"), 2],
        [1, float("inf")],
        [float("-inf"), 2],
    ],
)
def test_invalid_locations(point):
    assert g.valid_point(point) is None
    with pytest.raises(ValueError):
        g.measure_points([point])


@pytest.mark.parametrize("container", [None, {}, "bad", ()])
def test_unavailable_not_zero(container):
    for row in rows(frame(container)):
        for metric in g.METRICS:
            assert row[metric] is None
            assert row[f"{metric}_status"] == "frame_unavailable"
        for field in (
            "total_visible_players",
            "n_valid_points_used",
            "n_unique_points",
            "actor_count",
            "n_keeper_true_excluded",
        ):
            assert row[field] is None
        assert row["actor_status"] == "unknown"


def test_empty_and_singleton():
    empty = g.measure_points([])
    assert empty["visible_player_count"] == 0
    for metric in g.METRICS[1:5]:
        assert empty[metric] is None and empty[f"{metric}_status"] == "empty_points"
    one = g.measure_points([(13, 24)])
    assert [one[k] for k in g.METRICS[:5]] == [1, 13, 24, 0, 0]
    for measured in (empty, one):
        for metric in g.METRICS[5:]:
            assert measured[metric] is None
            assert measured[f"{metric}_status"] == "insufficient_points"
    assert all(r["actor_status"] == "none" for r in rows(frame([])))


def test_triangle_odd_pairs_and_native_spans():
    measured = g.measure_points([(0, 0), (3, 0), (0, 4)])
    expected = [3, 1, 4 / 3, 4, 3, 6, 4, 4, 10 / 3]
    assert [measured[k] for k in g.METRICS] == pytest.approx(expected)
    assert all(measured[f"{k}_status"] == "ok" for k in g.METRICS)


def test_even_pair_count_median_and_nearest_ties():
    # Six pair distances: 1, 2, 3, 7, 9, 10; four NN distances: 1, 1, 2, 7.
    measured = g.measure_points([(0, 0), (1, 0), (3, 0), (10, 0)])
    assert measured["mean_pairwise_distance"] == pytest.approx(32 / 6)
    assert measured["median_pairwise_distance"] == 5
    assert measured["mean_nearest_neighbor_distance"] == 11 / 4
    square = g.measure_points([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert square["mean_nearest_neighbor_distance"] == 2
    assert square["mean_pairwise_distance"] == pytest.approx((8 + 4 * sqrt(2)) / 6)
    assert square["median_pairwise_distance"] == 2
    assert square["convex_hull_area"] == 4


@pytest.mark.parametrize(
    "points,distance", [([(0, 0), (3, 4)], 5), ([(3, 4), (3, 4)], 0)]
)
def test_two_records_and_index_self_exclusion(points, distance):
    measured = g.measure_points(points)
    for key in g.METRICS[6:]:
        assert measured[key] == distance and measured[f"{key}_status"] == "ok"


def test_duplicate_weight_is_retained():
    measured = g.measure_points([(0, 0), (0, 0), (3, 0), (0, 4)])
    assert measured["visible_player_count"] == 4
    assert (measured["centroid_x"], measured["centroid_y"]) == (0.75, 1)
    assert (
        measured["visible_width"],
        measured["visible_depth"],
        measured["convex_hull_area"],
    ) == (4, 3, 6)
    assert measured["mean_pairwise_distance"] == pytest.approx(19 / 6)
    assert measured["median_pairwise_distance"] == 3.5
    assert measured["mean_nearest_neighbor_distance"] == 7 / 4
    coincident = g.measure_points([(2, 3)] * 3)
    assert [coincident[k] for k in g.METRICS[:5]] == [3, 2, 3, 0, 0]
    assert all(coincident[k] == 0 for k in g.METRICS[6:])


@pytest.mark.parametrize(
    "points,status",
    [
        ([], "insufficient_points"),
        ([(0, 0)] * 2, "insufficient_points"),
        ([(0, 0)] * 3, "insufficient_unique_points"),
        ([(0, 0), (1, 1), (0, 0)], "insufficient_unique_points"),
        ([(0, 0), (1, 1), (2, 2)], "degenerate_hull"),
    ],
)
def test_hull_gates(points, status):
    measured = g.measure_points(points)
    assert measured["convex_hull_area"] is None
    assert measured["convex_hull_area_status"] == status


def test_small_positive_hull_has_no_tolerance():
    measured = g.measure_points([(0, 0), (1, 0), (0, 1e-20)])
    assert measured["convex_hull_area"] == 5e-21
    assert measured["convex_hull_area_status"] == "ok"


@pytest.mark.parametrize(
    "kind,valid,empty,area,status",
    [
        ("Polygon", True, False, 0, "degenerate_hull"),
        ("Polygon", True, False, -1, "geometry_error"),
        ("Polygon", True, False, float("inf"), "numeric_error"),
        ("Polygon", False, False, 1, "geometry_error"),
        ("MultiPolygon", True, False, 1, "geometry_error"),
        ("Point", True, False, 0, "degenerate_hull"),
        ("Polygon", True, True, 0, "degenerate_hull"),
    ],
)
def test_hull_return_status(monkeypatch, kind, valid, empty, area, status):
    hull = Mock(geom_type=kind, is_valid=valid, is_empty=empty, area=area)
    monkeypatch.setattr(g, "MultiPoint", Mock(return_value=Mock(convex_hull=hull)))
    measured = g.measure_points([(0, 0), (1, 0), (0, 1)])
    assert measured["convex_hull_area"] is None
    assert measured["convex_hull_area_status"] == status
    assert measured["visible_player_count_status"] == "ok"


@pytest.mark.parametrize("stage", ["construction", "area"])
def test_expected_geos_failures(monkeypatch, stage):
    if stage == "construction":
        constructor = Mock(side_effect=GEOSException("synthetic failure"))
    else:
        hull = Mock(is_empty=False, geom_type="Polygon", is_valid=True)
        type(hull).area = PropertyMock(side_effect=GEOSException("synthetic failure"))
        constructor = Mock(return_value=Mock(convex_hull=hull))
    monkeypatch.setattr(g, "MultiPoint", constructor)
    measured = g.measure_points([(0, 0), (1, 0), (0, 1)])
    assert measured["convex_hull_area_status"] == "geometry_error"
    assert measured["hull_error_category"] == "GEOSException"


@pytest.mark.parametrize("error", [RuntimeError, TypeError, ValueError, AttributeError])
def test_programming_errors_surface(monkeypatch, error):
    monkeypatch.setattr(g, "MultiPoint", Mock(side_effect=error("bug")))
    with pytest.raises(error):
        g.measure_points([(0, 0), (1, 0), (0, 1)])


def test_numeric_errors_are_metric_specific():
    measured = g.measure_points([(1e308, 0), (1e308, 1)])
    assert measured["centroid_x"] is measured["centroid_y"] is None
    assert (
        measured["centroid_x_status"]
        == measured["centroid_y_status"]
        == "numeric_error"
    )
    assert measured["visible_width"] == measured["mean_pairwise_distance"] == 1
    measured = g.measure_points([(-1e308, 0), (1e308, 0)])
    for key in ("visible_depth", *g.METRICS[6:]):
        assert measured[key] is None and measured[f"{key}_status"] == "numeric_error"
    measured = g.measure_points([(10**400, 0)])
    assert measured["centroid_x_status"] == "numeric_error"


def test_subset_filters_unknowns_and_invalid_counts_without_mutation():
    raw = frame(
        [
            player((1, 1), True, False, True),
            player((2, 2), True, True),
            player((3, 3), False, False),
            player((4, 4), False, None),
            player((5, 5), 1, False),
            player((6, 6), None, 0),
            player((7, 7), "True", True),
            player(("bad", 1)),
            "bad record",
        ]
    )
    original = deepcopy(raw)
    output = rows(raw)
    assert len(output) == 6
    assert [r["visible_player_count"] for r in output] == [7, 3, 2, 1, 2, 1]
    for r in output:
        assert r["total_visible_players"] == 9
        assert r["n_non_dictionary_records"] == r["n_invalid_locations"] == 1
        assert r["n_unknown_teammate"] == 3
        assert r["actor_status"] == "unknown"
        assert {
            "unknown_teammate",
            "unknown_keeper",
            "partial_invalid_input",
            "actor_status_unknown",
        } <= set(r["measurement_flags"].split("|"))
    included, excluded = output[:2]
    assert (
        included["n_keeper_true_excluded"] == included["n_keeper_unknown_excluded"] == 0
    )
    assert (
        excluded["n_keeper_true_excluded"] == excluded["n_keeper_unknown_excluded"] == 2
    )
    assert raw == original
    assert frame_observability(raw)["visible_players"] == 8  # Old audit unchanged.


@pytest.mark.parametrize(
    "actors,status",
    [
        ([True, False], "single"),
        ([False, False], "none"),
        ([True, None], "unknown"),
        ([False, 0], "unknown"),
        ([True, True, None], "multiple"),
    ],
)
def test_actor_status_inherited_before_subset_filter(actors, status):
    output = rows(frame([player(actor=a) for a in actors]))
    assert all(r["actor_status"] == status for r in output)
    if status in ("multiple", "unknown"):
        flag = "multiple_actor" if status == "multiple" else "actor_status_unknown"
        assert all(flag in r["measurement_flags"] for r in output)
    assert output[0]["visible_player_count"] == len(actors)
    assert output[0]["n_coincident_records"] == len(actors) - 1
    assert output[4]["visible_player_count"] == 0


@pytest.mark.parametrize(
    "polygon,status",
    [
        (None, "missing"),
        ([], "malformed"),
        ([0, 0, 1, 1, 0, 1, 1, 0], "invalid"),
        ([0, 0, 1, 0, 1, 1, 0, 1], "valid"),
    ],
)
def test_visibility_is_context_not_suppression(polygon, status):
    raw = frame([player((-2, 81)), player((120, 80))])
    raw["visible_area"] = polygon
    measured = rows(raw)[0]
    assert measured["visible_area_status"] == status
    assert measured["visible_area_fraction"] == (
        1 / 9600 if status == "valid" else None
    )
    assert measured["n_out_of_bounds_points"] == 1
    assert "out_of_bounds_points" in measured["measurement_flags"]
    assert measured["visible_depth"] == 122
    assert measured["mean_pairwise_distance_status"] == "ok"


def test_builder_join_grain_metadata_and_no_mutation():
    events = [
        {"id": "e", "type": {"name": "Pass"}},
        {"id": "e", "type": {"name": "Shot"}},
        {"id": "unique", "type": {"name": "Carry"}},
        {"id": "without-frame"},
        {"id": None},
    ]
    frames = [frame([player()]) for _ in range(5)]
    for raw, identifier in zip(frames, ["e", "e", "unique", "orphan", None]):
        raw["event_uuid"] = identifier
    before = deepcopy((events, frames))
    table = g.build_frame_geometry(123, events, frames, source_revision="synthetic")
    assert len(table) == 30
    assert table.groupby("frame_index").size().eq(6).all()
    first = table.iloc[::6]
    assert first["event_join_status"].tolist() == [
        "ambiguous",
        "ambiguous",
        "unique",
        "unmatched",
        "unmatched",
    ]
    assert first["event_type"].dropna().tolist() == ["Carry"]
    assert pd.isna(first.iloc[-1]["event_id"])
    assert table["statsbomb_revision"].eq("synthetic").all()
    assert table["match_id"].eq(123).all()
    assert set(table["frame_index"]) == set(range(5))
    assert "eligibility" not in " ".join(table.columns)
    assert (events, frames) == before
    assert g.build_frame_geometry(123, events, [], source_revision="synthetic").empty
    assert not any("location" == key or "freeze_frame" == key for key in table.columns)


def test_builder_rejects_unsafe_join_metadata():
    with pytest.raises(ValueError):
        g.frame_geometry({}, match_id=1, frame_index=0, source_revision="s", event={})


def test_visible_polygon_failure_does_not_suppress_geometry(monkeypatch):
    inspector = g.inspect_visible_area
    monkeypatch.setattr(
        g,
        "inspect_visible_area",
        Mock(side_effect=[GEOSException("failure"), inspector(None)]),
    )
    measured = rows(frame([player(), player((3, 4))]))[0]
    assert measured["visible_area_status"] == "invalid"
    assert measured["visible_area_reason"] == "GEOSException"
    assert measured["visible_area_fraction"] is None
    assert measured["mean_pairwise_distance"] == 5
    assert "invalid_visible_area" in measured["measurement_flags"]


def test_numeric_hull_construction_failure(monkeypatch):
    monkeypatch.setattr(g, "MultiPoint", Mock(side_effect=OverflowError("failure")))
    measured = g.measure_points([(0, 0), (1, 0), (0, 1)])
    assert measured["convex_hull_area_status"] == "numeric_error"
    assert measured["hull_error_category"] == "OverflowError"


def test_failed_pair_is_not_replaced_or_dropped_from_summaries():
    measured = g.measure_points([(-1e308, 0)] * 2 + [(1e308, 0)] * 2)
    for metric in g.METRICS[6:]:
        assert measured[metric] is None
        assert measured[f"{metric}_status"] == "numeric_error"


@pytest.mark.parametrize(
    "identifier,kind,diagnostic",
    [
        ("  ", "str", "'  '"),
        (0, "int", "0"),
        (False, "bool", "False"),
        ({}, "dict", None),
        (None, "NoneType", None),
    ],
)
def test_invalid_event_id_keeps_separate_diagnostic_context(
    identifier, kind, diagnostic
):
    raw = frame([])
    raw["event_uuid"] = identifier
    measured = rows(raw)[0]
    assert measured["event_id"] is None
    assert measured["event_id_raw_type"] == kind
    assert measured["invalid_event_id_scalar"] == diagnostic

"""Synthetic observability regressions: no network or real raw-data fixtures."""

from copy import deepcopy
from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from leverkusen.data import observability as audit


def match(match_id=1):
    return {
        "match_id": match_id,
        "match_date": "2024-04-06",
        "match_week": 28,
        "home_team": {"home_team_name": "Union Berlin"},
        "away_team": {"away_team_name": "Bayer Leverkusen"},
    }


def event(identifier="e1", team="Bayer Leverkusen", event_type="Pass"):
    return {
        "id": identifier,
        "index": 7,
        "type": {"name": event_type},
        "team": {"name": team},
        "location": [10, 20],
    }


def frame(identifier="e1"):
    return {
        "event_uuid": identifier,
        "freeze_frame": [
            {"teammate": True, "actor": True, "keeper": False, "location": [13, 24]},
            {"teammate": True, "actor": False, "keeper": True, "location": [20, 10]},
            {"teammate": False, "actor": False, "keeper": False, "location": [40, 50]},
        ],
        "visible_area": [0, 0, 60, 0, 60, 80, 0, 80],
    }


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(
        audit.loader.requests,
        "get",
        Mock(side_effect=AssertionError("Unexpected HTTP")),
    )


def test_join_keeps_unmatched_events_and_orphan_frames_without_mutation():
    events, frames = [event(), event("e2", "Union Berlin")], [frame(), frame("orphan")]
    before = deepcopy((events, frames))
    summary, frame_table, event_table = audit.audit_match(match(), events, frames)
    assert summary["opponent"] == "Union Berlin" and summary["venue"] == "Away"
    assert summary["total_events"] == summary["total_frames"] == 2
    assert summary["matched_events"] == summary["events_without_frames"] == 1
    assert summary["frames_without_matching_events"] == 1
    assert frame_table["event_link_status"].tolist() == ["unique", "unmatched"]
    assert frame_table["event_type"].tolist() == ["Pass", "<unmatched>"]
    assert frame_table.loc[0, "event_index"] == 7
    assert event_table["has_360_frame"].tolist() == [True, False]
    assert frame_table.loc[0, "actor_distance"] == 5
    assert pd.isna(frame_table.loc[1, "actor_distance"])
    assert (events, frames) == before


def test_duplicate_ids_do_not_multiply_rows_or_select_arbitrary_event():
    events = [event(), event(event_type="Shot")]
    summary, frames, event_table = audit.audit_match(
        match(), events, [frame(), frame()]
    )
    assert summary["unique_event_ids"] == summary["unique_frame_event_uuids"] == 1
    assert summary["duplicate_event_ids"] == summary["duplicate_frame_uuids"] == 1
    assert (
        summary["duplicate_event_id_groups"]
        == summary["duplicate_frame_uuid_groups"]
        == 1
    )
    assert len(frames) == len(event_table) == 2  # Not four from a many-to-many join.
    assert frames["event_link_status"].eq("ambiguous").all()
    assert frames["event_type"].eq("<ambiguous>").all()
    assert not frames["actor_consistency_measurable"].any()
    assert summary["frames_with_ambiguous_event"] == 2
    counts = audit.summarize_attrition(event_table, frames).iloc[0]
    assert counts["all_events"] == counts["all_frames"] == 2
    assert counts["frames_unique_event_and_frame_id"] == 0


def test_ids_do_not_join_across_matches():
    _, frames, _ = audit.audit_match(match(2), [event("different")], [frame()])
    assert frames.iloc[0]["event_link_status"] == "unmatched"


@pytest.mark.parametrize("identifier", [None, "", "   ", 42, ["bad"]])
def test_missing_or_malformed_identifiers_never_match(identifier):
    summary, frames, events = audit.audit_match(
        match(), [event(identifier)], [frame(identifier)]
    )
    assert summary["events_missing_id"] == summary["frames_missing_uuid"] == 1
    assert summary["matched_events"] == 0
    assert summary["duplicate_event_ids"] == summary["duplicate_frame_uuids"] == 0
    assert frames.iloc[0]["event_link_status"] == "unmatched"
    assert not events.iloc[0]["has_360_frame"]


def test_raw_flags_and_single_actor_distance():
    result = audit.frame_observability(frame(), event())
    assert result["visible_players"] == result["valid_player_locations"] == 3
    assert result["teammate_true"] == 2
    assert result["teammate_false"] == result["keepers"] == result["actors"] == 1
    assert result["teammate_unknown"] == 0
    assert result["actor_distance"] == 5
    assert result["actor_consistency_measurable"]


def test_empty_freeze_frame_is_observed_zero():
    record = frame()
    record["freeze_frame"] = []
    result = audit.frame_observability(record, event())
    assert result["freeze_frame_empty"]
    assert result["visible_players"] == result["actors"] == 0
    assert not result["actor_consistency_measurable"]
    assert result["actor_distance"] is None


@pytest.mark.parametrize(
    "freeze,missing,malformed", [(None, True, False), ({}, False, True)]
)
def test_missing_or_malformed_freeze_frame_is_not_zero(freeze, missing, malformed):
    record = frame()
    record["freeze_frame"] = freeze
    result = audit.frame_observability(record, event())
    assert result["freeze_frame_missing"] == missing
    assert result["freeze_frame_malformed"] == malformed
    assert result["visible_players"] is None
    assert result["freeze_frame_empty"] is None


def test_unknown_flags_and_invalid_player_records_remain_visible():
    record = frame()
    record["freeze_frame"].extend([{}, {"teammate": 1}, "bad"])
    result = audit.frame_observability(record, event())
    assert result["visible_players"] == 5
    assert result["invalid_player_records"] == 1
    assert result["freeze_frame_malformed"]
    assert result["teammate_unknown"] == 2
    assert result["teammate_true"] == 2  # Integer 1 is not a boolean flag.


def test_missing_visible_area():
    result = audit.inspect_visible_area(None)
    assert result["visible_area_missing"]
    assert not result["visible_area_exists"]
    assert not result["visible_area_valid"]
    assert result["visible_area_fraction"] is None


def test_polygon_area_and_pitch_fraction():
    result = audit.inspect_visible_area(frame()["visible_area"])
    assert result["visible_area_valid"]
    assert result["visible_area_coordinate_count"] == 8
    assert result["visible_area_vertex_count"] == 4
    assert (
        result["visible_area_polygon_area"]
        == result["visible_area_on_pitch_area"]
        == 4800
    )
    assert result["visible_area_fraction"] == 0.5


def test_polygon_is_clipped_to_pitch_without_rewriting_polygon():
    result = audit.inspect_visible_area([-60, 0, 60, 0, 60, 80, -60, 80])
    assert result["visible_area_polygon_area"] == 9600
    assert result["visible_area_fraction"] == 0.5
    assert result["visible_area_outside_pitch"]


@pytest.mark.parametrize(
    "area",
    [
        [],
        [0, 0, 1],
        "bad",
        [[0, 0], [1, 1], [2, 2]],
        [0, 0, 1, 0, float("nan"), 1],
        [0, 0, 1, 0, True, 1],
    ],
)
def test_malformed_area_is_not_repaired(area):
    result = audit.inspect_visible_area(area)
    assert result["visible_area_malformed"]
    assert not result["visible_area_valid"]
    assert result["visible_area_polygon_area"] is None


@pytest.mark.parametrize("area", [[0, 0, 10, 10, 0, 10, 10, 0], [0, 0, 1, 1, 2, 2]])
def test_self_intersecting_or_degenerate_polygon(area):
    result = audit.inspect_visible_area(area)
    assert not result["visible_area_malformed"]
    assert not result["visible_area_valid"]
    assert result["visible_area_reason"] != "valid"
    assert result["visible_area_fraction"] is None


@pytest.mark.parametrize("length,width", [(0, 80), (120, -1), (float("inf"), 80)])
def test_invalid_pitch_dimensions(length, width):
    with pytest.raises(ValueError, match="Pitch dimensions"):
        audit.inspect_visible_area(None, length, width)


@pytest.mark.parametrize(
    "case", ["no_actor", "two_actors", "bad_actor_point", "no_event", "bad_event_point"]
)
def test_actor_distance_unavailable_is_not_zero(case):
    record, linked = frame(), event()
    if case == "no_actor":
        record["freeze_frame"][0]["actor"] = False
    elif case == "two_actors":
        record["freeze_frame"][1]["actor"] = True
    elif case == "bad_actor_point":
        record["freeze_frame"][0]["location"] = [float("inf"), 1]
    elif case == "no_event":
        linked = None
    else:
        linked["location"] = None
    result = audit.frame_observability(record, linked)
    assert not result["actor_consistency_measurable"]
    assert result["actor_distance"] is None


def test_actor_statistics_and_review_ranking_do_not_set_threshold():
    records = pd.DataFrame(
        {
            "actor_distance": [0, 5, 10, None],
            "actor_consistency_measurable": [True, True, True, False],
        }
    )
    result = audit.summarize_actor_distances(records)
    assert result["actor_distance_count"] == 3
    assert result["actor_distance_mean"] == result["actor_distance_median"] == 5
    assert result["actor_distance_max"] == 10
    assert result["actor_distance_q95"] == pytest.approx(9.5)
    assert audit.largest_actor_discrepancies(records, 2)["actor_distance"].tolist() == [
        10,
        5,
    ]
    assert (
        audit.summarize_actor_distances(records.iloc[0:0])["actor_distance_mean"]
        is None
    )


def test_attrition_denominators_and_all_group_partitions():
    empty = frame("e2")
    empty["freeze_frame"] = []
    _, frames, events = audit.audit_match(
        match(),
        [event(), event("e2", "Union Berlin", "Shot"), event("e3")],
        [frame(), empty, frame("orphan")],
    )
    result = audit.summarize_attrition(events, frames)
    season = result.iloc[0]
    assert season["all_events"] == season["all_frames"] == 3
    assert season["events_with_360_frame"] == 2
    assert season["frames_nonempty_freeze_frame"] == 2
    assert season["frames_valid_visible_area"] == 3
    assert season["frames_actor_measurable"] == season["frames_joint_checks"] == 1
    for scope in ["match_id", "event_type", "event_team_group"]:
        partition = result[result["scope"].eq(scope)]
        assert partition["all_events"].sum() == 3
        assert partition["all_frames"].sum() == 3
    unknown = result[
        result["scope"].eq("event_team_group") & result["group"].eq("Unknown")
    ].iloc[0]
    assert unknown["all_events"] == 0 and unknown["all_frames"] == 1


def test_null_metadata_retained_in_attrition_groups():
    record = event()
    record["type"] = {"name": None}
    _, frames, events = audit.audit_match(match(), [record], [frame()])
    result = audit.summarize_attrition(events, frames)
    assert result[result["scope"].eq("event_type")]["all_events"].sum() == 1
    assert frames.iloc[0]["event_type"] == "<missing>"


@pytest.mark.parametrize(
    "failure,status",
    [
        (FileNotFoundError("404"), "missing"),
        (requests.Timeout("timeout"), "error"),
        (ValueError("invalid JSON"), "error"),
    ],
)
def test_season_missing_360_records_failure_without_fake_frame(
    monkeypatch, failure, status
):
    monkeypatch.setattr(audit.loader, "load_matches", Mock(return_value=[match()]))
    load_events = Mock(return_value=[event()])
    monkeypatch.setattr(audit.loader, "load_events", load_events)
    monkeypatch.setattr(audit.loader, "load_360", Mock(side_effect=failure))
    matches, frames, attrition = audit.audit_season(expected_matches=1)
    load_events.assert_called_once_with(1)
    assert matches.iloc[0]["frames_load_status"] == status
    assert pd.isna(matches.iloc[0]["total_frames"])
    assert frames.empty
    season = attrition.iloc[0]
    assert season["all_events"] == season["events_360_load_unavailable"] == 1
    assert season["all_frames"] == season["frames_nonempty_freeze_frame"] == 0


def test_season_fetches_once_per_match_and_does_not_join_across_matches(monkeypatch):
    monkeypatch.setattr(
        audit.loader, "load_matches", Mock(return_value=[match(1), match(2)])
    )
    load_events = Mock(side_effect=[[event()], [event("other")]])
    load_frames = Mock(side_effect=[[frame()], [frame()]])
    monkeypatch.setattr(audit.loader, "load_events", load_events)
    monkeypatch.setattr(audit.loader, "load_360", load_frames)
    matches, frames, attrition = audit.audit_season(expected_matches=2)
    assert load_events.call_count == load_frames.call_count == 2
    assert matches["matched_events"].tolist() == [1, 0]
    assert frames["event_link_status"].tolist() == ["unique", "unmatched"]
    assert attrition.iloc[0]["all_events"] == 2


def test_duplicate_match_inventory_aborts_before_event_loading(monkeypatch):
    monkeypatch.setattr(
        audit.loader, "load_matches", Mock(return_value=[match(), match()])
    )
    load_events = Mock(side_effect=AssertionError("Should not load events"))
    monkeypatch.setattr(audit.loader, "load_events", load_events)
    with pytest.raises(ValueError, match="unique"):
        audit.audit_season(expected_matches=2)
    load_events.assert_not_called()


def test_event_load_failure_aborts_instead_of_inventing_denominator(monkeypatch):
    monkeypatch.setattr(audit.loader, "load_matches", Mock(return_value=[match()]))
    monkeypatch.setattr(
        audit.loader, "load_events", Mock(side_effect=requests.Timeout("events"))
    )
    with pytest.raises(requests.Timeout):
        audit.audit_season(expected_matches=1)


def test_writer_outputs_only_three_derived_csvs(tmp_path):
    summary, frames, events = audit.audit_match(match(), [event()], [frame()])
    audit.write_audit_outputs(
        pd.DataFrame([summary]),
        frames,
        audit.summarize_attrition(events, frames),
        tmp_path,
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "phase1_attrition.csv",
        "phase1_frame_summary.csv",
        "phase1_match_summary.csv",
    ]
    written = pd.read_csv(tmp_path / "phase1_frame_summary.csv")
    assert len(written) == 1
    assert not {"freeze_frame", "visible_area", "location"} & set(written.columns)

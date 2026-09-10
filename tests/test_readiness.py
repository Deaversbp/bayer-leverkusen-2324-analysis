"""Offline audit contracts: complete event context and unchanged semantic scope."""

from copy import deepcopy

import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences.readiness import (
    KEY,
    anchor_gaps,
    match_event_inventory,
    possession_inventory,
    representative_possessions,
    summarize_readiness,
    temporal_windows,
    validate_locked_reconciliation,
)
from leverkusen.spatial.orientation import VALIDATED


@pytest.fixture
def example():
    match = {
        "match_id": 1,
        "match_date": "2024-01-01",
        "home_team": {"home_team_id": 904, "home_team_name": "Bayer Leverkusen"},
        "away_team": {"away_team_id": 100, "away_team_name": "Opponent"},
    }
    specs = [
        # Nonconsecutive provider indices ensure row gaps aren't index gaps.
        (1, 1, 1, 904, 904, "Pass", 0, True),
        (3, 1, 1, 904, 904, "Ball Receipt*", 1, True),
        (5, 1, 1, 904, 100, "Pressure", 2, True),
        (6, 1, 1, 904, 904, "Dribble", 2, False),
        (7, 1, 1, 904, 904, "Shot", 5, True),
        (8, 1, 2, 904, 904, "Dribble", 6, True),
        (9, 1, 3, 904, 904, "Pass", 8, True),
        (10, 1, 4, 100, 904, "Pass", 9, True),
        # Provider possession ID reused in another period must stay separate.
        (11, 2, 1, 904, 904, "Carry", 0, True),
    ]
    events, frames = [], []
    for index, period, possession, pteam, eteam, typ, seconds, linked in specs:
        event = {
            "id": f"e{index}",
            "index": index,
            "period": period,
            "possession": possession,
            "possession_team": {"id": pteam},
            "team": {"id": eteam},
            "type": {"name": typ},
            "timestamp": f"00:00:{seconds:06.3f}",
            "location": [index, 20],
        }
        if typ == "Shot":
            event["shot"] = {"outcome": {"name": "Goal"}}
        events.append(event)
        if linked:
            frames.append(
                {
                    "event_uuid": event["id"],
                    "freeze_frame": [
                        {
                            "location": [index, 20],
                            "actor": True,
                            "teammate": True,
                            "keeper": False,
                        },
                        {
                            "location": [100, 40],
                            "actor": False,
                            "teammate": False,
                            "keeper": True,
                        },
                    ],
                }
            )
    return match, events, frames


def inventory(example, revision=STATSBOMB_REVISION):
    return match_event_inventory(*example, source_revision=revision)


def selected(example):
    full = inventory(example)
    return full[full.possession_team_id.eq(904)].copy()


def test_provider_grouping_selection_period_and_zero_anchor_denominator(example):
    stream = selected(example)
    p = possession_inventory(stream)
    assert len(p) == 4
    assert p.validated_spatial_anchor_count.tolist() == [3, 0, 1, 1]
    assert stream.event_index.tolist() == [1, 3, 5, 6, 7, 8, 9, 11]
    assert p.total_event_count.sum() == len(stream)
    assert p.loc[p.period.eq(2), "possession_duration_seconds"].item() == 0


def test_unsupported_and_unlinked_events_retained_without_spatial_states(example):
    stream = selected(example)
    assert stream.event_type.eq("Ball Receipt*").sum() == 1
    assert stream.event_type.eq("Dribble").sum() == 2
    assert not stream.loc[
        stream.event_type.isin(["Ball Receipt*", "Dribble"]), "validated_anchor"
    ].any()
    assert (
        stream.loc[stream.event_index.eq(6), "semantics_status"].item()
        == "no_360_frame"
    )
    p = possession_inventory(stream).iloc[0]
    assert p.total_event_count == 5
    assert p.total_360_linked_event_count == 4
    assert p.unsupported_360_frame_count == 1
    assert p.validated_anchor_span_seconds == 5


def test_anchor_order_gaps_and_intervening_event_count(example):
    match, events, frames = example
    stream = selected((match, list(reversed(events)), frames))
    gaps = anchor_gaps(stream)
    assert gaps.previous_event_index.tolist() == [1, 5]
    assert gaps.next_event_index.tolist() == [5, 7]
    assert gaps.elapsed_seconds.tolist() == [2, 3]
    assert gaps.event_index_gap.tolist() == [4, 2]
    assert gaps.intervening_event_count.tolist() == [1, 1]
    assert gaps.previous_anchor_type.tolist() == ["Pass", "Pressure"]
    assert gaps.next_anchor_type.tolist() == ["Pressure", "Shot"]


def test_opponent_event_is_anchor_in_leverkusen_possession(example):
    stream = selected(example)
    pressure = stream[stream.event_type.eq("Pressure")].iloc[0]
    assert pressure.event_team_id == 100 and pressure.possession_team_id == 904
    assert pressure.semantics_status == VALIDATED
    assert possession_inventory(stream).opponent_anchor_count.sum() == 1


def test_shot_groups_and_match_aggregation(example):
    stream = selected(example)
    p, gaps = possession_inventory(stream), anchor_gaps(stream)
    tables = summarize_readiness(p, gaps, stream, [example[0]])
    row = tables["match_coverage"].iloc[0]
    assert row.possession_count == 4
    assert row.pct_ge_3_anchors == 25
    assert row.median_anchor_gap_seconds == 2.5
    assert row.p90_anchor_gap_seconds == pytest.approx(2.9)
    shot = tables["shot_coverage"].set_index("population")
    assert shot.loc["shot_containing", "possession_count"] == 1
    assert shot.loc["no_shot", "possession_count"] == 3
    assert shot.loc["literal_final_event_shot", "possession_count"] == 1
    assert p.has_goal.sum() == 1
    assert p.leverkusen_shot_count.sum() == 1
    teams = tables["event_team_composition"]
    opponent = teams[teams.event_team.eq("Opponent") & teams.event_type.eq("All")].iloc[
        0
    ]
    assert opponent.anchor_count == 1
    assert opponent.percentage_of_all_anchors == 20


def test_shot_containing_does_not_mean_final_event_shot(example):
    example[1][4]["type"]["name"] = "Goal Keeper"
    example[1][2]["type"]["name"] = "Shot"
    p = possession_inventory(selected(example)).iloc[0]
    assert p.has_shot and not p.ends_in_shot
    assert p.opponent_shot_count == 1


def test_temporal_windows_are_inclusive_and_period_bounded(example):
    rows = temporal_windows(selected(example)).set_index(
        ["unit", "states", "window_seconds"]
    )
    assert rows.loc[("consecutive_anchor_tuples", 2, 3), "count"] == 2
    assert rows.loc[("consecutive_anchor_tuples", 3, 3), "count"] == 0
    assert rows.loc[("consecutive_anchor_tuples", 3, 5), "count"] == 1
    assert rows.loc[("possessions_with_any_tuple", 3, 10), "count"] == 1
    assert rows.loc[("possessions_with_any_tuple", 4, 10), "count"] == 0


def test_equal_timestamp_anchor_gap_is_zero(example):
    example[1][2]["timestamp"] = "00:00:00.000"
    example[1][1]["timestamp"] = "00:00:00.000"
    assert anchor_gaps(selected(example)).elapsed_seconds.iloc[0] == 0


def test_match_boundaries_and_rates_use_each_matches_own_denominator(example):
    other = deepcopy(example)
    other[0]["match_id"] = 2
    other[0]["match_date"] = "2024-01-02"
    # Match two contains only the five-event, three-anchor possession. Reused
    # indices/possession IDs must not connect anchors to match one.
    other[1][:] = other[1][:5]
    other[2][:] = other[2][:4]
    stream = pd.concat([selected(example), selected(other)], ignore_index=True)
    p, gaps = possession_inventory(stream), anchor_gaps(stream)
    tables = summarize_readiness(p, gaps, stream, [example[0], other[0]])
    m = tables["match_coverage"].set_index("match_id")
    assert m.loc[1, "possession_count"] == 4
    assert m.loc[2, "possession_count"] == 1
    assert m.loc[1, "pct_ge_3_anchors"] == 25
    assert m.loc[2, "pct_ge_3_anchors"] == 100
    assert gaps.groupby("match_id").size().to_dict() == {1: 2, 2: 2}
    assert len(p) == 5


def test_stoppage_time_and_missing_anchor_times(example):
    for event in example[1]:
        if event["period"] == 1:
            event["timestamp"] = "00:48:10.250"
    p = possession_inventory(selected(example))
    assert p.first_validated_anchor_time.iloc[0] == 2890.25
    zero = p[p.validated_spatial_anchor_count.eq(0)].iloc[0]
    assert pd.isna(zero.first_validated_anchor_time)
    assert pd.isna(zero.validated_anchor_span_seconds)


def test_raw_events_coordinates_and_configuration_unchanged(example):
    before = deepcopy(example)
    stream = selected(example)
    p, gaps = possession_inventory(stream), anchor_gaps(stream)
    summarize_readiness(p, gaps, stream, [example[0]])
    assert example == before
    assert not any(
        "x_attacking" in c or "trajectory" in c or "eligible" in c for c in stream
    )
    assert p.validated_spatial_anchor_count.sum() == stream.validated_anchor.sum()


@pytest.mark.parametrize(
    "typ", ["Ball Receipt*", "Dribble", "Dispossessed", "Foul Won", "Duel"]
)
def test_exact_actor_alignment_never_promotes_unsupported_type(example, typ):
    example[1][0]["type"]["name"] = typ
    row = inventory(example).iloc[0]
    assert not row.validated_anchor
    assert row.semantics_status == "unsupported_event_type"


def test_core_type_still_requires_existing_frame_gates(example):
    example[2][0]["freeze_frame"][0]["location"] = [1.01, 20]
    row = inventory(example).iloc[0]
    assert row.semantics_status == "actor_encoding_unresolved"
    assert not row.validated_anchor


def test_incoming_conflict_from_opponent_possession_quarantines_anchor(example):
    # Opposite-team related event outside the selected population has the same
    # cloud AND same labels, contradicting expected inversion. Audit before selection.
    example[1][7]["team"]["id"] = 100
    example[1][7]["related_events"] = ["e1"]
    example[2][6]["freeze_frame"] = deepcopy(example[2][0]["freeze_frame"])
    row = selected(example).iloc[0]
    assert row.semantics_status == "related_team_label_conflict"
    assert not row.validated_anchor


def test_unpinned_source_cannot_supply_anchors(example):
    assert not inventory(example, "0" * 40).validated_anchor.any()


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_event",
        "duplicate_frame",
        "orphan",
        "index",
        "missing_team",
        "conflicting_possession_team",
        "time",
        "noncontiguous",
    ],
)
def test_ambiguous_or_invalid_stream_aborts(example, failure):
    _, events, frames = example
    if failure == "duplicate_event":
        events.append(deepcopy(events[0]))
    elif failure == "duplicate_frame":
        frames.append(deepcopy(frames[0]))
    elif failure == "orphan":
        frames[0]["event_uuid"] = "absent"
    elif failure == "index":
        events[1]["index"] = events[0]["index"]
    elif failure == "missing_team":
        events[0].pop("possession_team")
    elif failure == "conflicting_possession_team":
        events[1]["possession_team"]["id"] = 100
    elif failure == "time":
        events[0]["timestamp"] = "00:10:00.000"
    elif failure == "noncontiguous":
        events[6]["possession"] = 1
    with pytest.raises(ValueError):
        inventory(example)


def test_single_anchor_groups_produce_no_synthetic_intervals(example):
    stream = selected(example)
    stream = stream[stream.event_index.isin([8, 9, 11])]
    gaps = anchor_gaps(stream)
    assert gaps.empty and "elapsed_seconds" in gaps
    p = possession_inventory(stream)
    tables = summarize_readiness(p, gaps, stream, [example[0]])
    assert tables["sequence_candidates"].capable_possessions.eq(0).all()
    assert len(tables["possession_anchor_coverage"]) == 3


def test_representatives_are_deterministic_unique_and_keep_full_timelines(example):
    stream = selected(example)
    p = possession_inventory(stream)
    first, timeline = representative_possessions(p, stream)
    second, _ = representative_possessions(p.sample(frac=1, random_state=2), stream)
    pd.testing.assert_frame_equal(first, second)
    assert not first[KEY].duplicated().any()
    for key, group in timeline.groupby(KEY):
        expected = stream.set_index(KEY).loc[[key]]
        assert len(group) == len(expected)


def test_locked_run_reconciliation_accepts_recorded_revision_and_both_populations():
    validate_locked_reconciliation(
        "533862946a73608c134d18b78226b6371ce7173c",
        (137765, 118581, 72596, 45985),
        (2888, 86025, 74647, 46143, 28504),
    )


@pytest.mark.parametrize(
    "population,index",
    [
        *(("season", i) for i in range(4)),
        *(("possession", i) for i in range(5)),
    ],
)
def test_locked_run_reconciliation_rejects_any_count_drift(population, index):
    season = [137765, 118581, 72596, 45985]
    possession = [2888, 86025, 74647, 46143, 28504]
    (season if population == "season" else possession)[index] += 1
    with pytest.raises(ValueError, match="reconciliation failed"):
        validate_locked_reconciliation(STATSBOMB_REVISION, season, possession)


def test_locked_run_counts_are_not_a_universal_other_revision_fixture():
    with pytest.raises(ValueError, match="recorded source revision"):
        validate_locked_reconciliation(
            "0" * 40,
            (137765, 118581, 72596, 45985),
            (2888, 86025, 74647, 46143, 28504),
        )

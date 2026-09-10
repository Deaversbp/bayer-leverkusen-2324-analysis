"""Offline progression evidence contracts; no episode/reset classifier."""

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences.progression_diagnostics import (
    action_path,
    enrich_match,
    progression_possessions,
    progression_runs,
    provider_signals,
    recovery_inventory,
    summarize_progression,
    temporal_diagnostics,
)


@pytest.fixture
def example():
    match = {
        "match_id": 1,
        "home_team": {"home_team_id": 904},
        "away_team": {"away_team_id": 100},
    }
    events, frames = [], []

    def add(typ, start, end, time, team=904, possession=1, period=1, linked=True):
        index = len(events) + 1
        event = {
            "id": f"e{index}",
            "index": index,
            "period": period,
            "possession": possession,
            "possession_team": {"id": 904},
            "team": {"id": team},
            "type": {"name": typ},
            "timestamp": f"00:00:{time:06.3f}",
            "location": [start, 20],
        }
        if end is not None:
            event[typ.lower()] = {"end_location": [end, 23]}
        events.append(event)
        if linked:
            frames.append(
                {
                    "event_uuid": event["id"],
                    "freeze_frame": [
                        {
                            "location": [start, 20],
                            "actor": True,
                            "teammate": True,
                            "keeper": False,
                        }
                    ],
                }
            )

    xs = [42, 58, 76, 85, 74, 61, 48, 60, 85, 90]
    for i, (a, b) in enumerate(zip(xs, xs[1:])):
        add("Pass" if i % 2 == 0 else "Carry", a, b, i * 3)
        add("Ball Receipt*", b, None, i * 3 + 1)
        if i == 0:
            add("Pressure", 15, None, 1.5, team=100)
    add("Pass", 10, 20, 28, possession=2)
    add("Pass", 5, 7, 0, period=2)
    return match, events, frames


def extracted(example):
    return enrich_match(*example, source_revision=STATSBOMB_REVISION)


def first_actions(example):
    stream = extracted(example)[1]
    return stream[stream.safe_action & stream.period.eq(1) & stream.possession_id.eq(1)]


def test_action_delta_and_components_preserve_coordinates(example):
    before = deepcopy(example)
    a = first_actions(example)
    assert a.delta_x.tolist() == [16, 18, 9, -11, -13, -13, 12, 25, 5]
    assert a.delta_y.eq(3).all()
    assert a.euclidean_displacement.iloc[0] == pytest.approx(np.hypot(16, 3))
    assert a.delta_x.clip(lower=0).sum() == 85
    assert -a.delta_x.clip(upper=0).sum() == 37
    assert example == before


def test_running_peak_retreat_and_path_endpoints(example):
    path = action_path(first_actions(example))
    assert len(path) == 18
    assert path.attacking_x.iloc[0] == 42 and path.attacking_x.iloc[-1] == 90
    assert path.running_peak_x.max() == 90
    assert path.retreat_from_peak.max() == 37
    assert path.running_peak_x.diff().dropna().ge(0).all()
    assert path.retreat_from_peak.ge(0).all()


def test_possession_net_and_cumulative_use_only_explicit_vectors(example):
    stream = extracted(example)[1]
    a = stream[stream.safe_action]
    path = action_path(a)
    p = progression_possessions(
        stream, a, path, progression_runs(a), recovery_inventory(path)
    )
    assert len(p) == 3
    first = p.iloc[0]
    assert first.net_x_progression == 48
    assert first.cumulative_forward_x == 85 and first.cumulative_backward_x == 37
    assert first.forward_to_backward_ratio == pytest.approx(85 / 37)
    assert first.inter_action_x_jump_sum == 0
    assert p.iloc[1].max_attacking_x_reached == 20
    assert p.iloc[2].max_attacking_x_reached == 7
    assert pd.isna(p.iloc[1].forward_to_backward_ratio)


def test_positive_negative_runs_and_context_counts(example):
    runs = progression_runs(first_actions(example))
    positive = runs[runs.run_kind.eq("positive")]
    negative = runs[runs.run_kind.eq("negative")]
    assert positive.action_count.tolist() == [3, 3]
    assert positive.cumulative_x_component.tolist() == [43, 42]
    n = negative.iloc[0]
    assert n.action_count == 3 and n.cumulative_x_component == 37
    assert n.maximum_single_component == 13 and n.timestamp_span_seconds == 6
    assert n.start_x == 85 and n.end_x == 48
    assert n.intervening_context_events == 2


def test_zero_actions_separate_strict_runs_but_not_nonpositive_alternative(example):
    a = first_actions(example).copy()
    a.loc[a.index[4], "delta_x"] = 0
    runs = progression_runs(a)
    assert runs.loc[runs.run_kind.eq("negative"), "action_count"].tolist() == [1, 1]
    assert runs.loc[runs.run_kind.eq("nonpositive"), "action_count"].tolist() == [3]


def test_recovery_first_observed_equality_and_time_reference(example):
    recovery = recovery_inventory(action_path(first_actions(example)))
    assert len(recovery) == 1
    r = recovery.iloc[0]
    assert r.previous_peak_x == 85 and r.retreat_size == 37
    assert r.recovered_previous_peak and r.new_peak_reached
    assert r.time_to_recover_previous_peak == 12
    assert r.time_peak_to_trough == 6
    assert r.time_trough_to_recovery == 6
    assert not r.censored_at_last_safe_observation


def test_unobserved_recovery_is_censored_not_zero_duration(example):
    recovery = recovery_inventory(action_path(first_actions(example).iloc[:6]))
    r = recovery.iloc[0]
    assert not r.recovered_previous_peak and not r.new_peak_reached
    assert pd.isna(r.time_to_recover_previous_peak)
    assert r.observed_followup_seconds == 6
    assert r.censored_at_last_safe_observation


def test_opponent_pressure_anchor_is_rotated_but_not_own_action(example):
    stream = extracted(example)[1]
    r = stream[stream.event_type.eq("Pressure")].iloc[0]
    assert r.event_team_id == 100 and r.possession_team_id == 904
    assert r.validated_anchor and r.anchor_x == 105
    assert not r.safe_action and pd.isna(r.delta_x)


def test_unsupported_and_unlinked_retained_without_normalization(example):
    example[2].pop(0)
    stream = extracted(example)[1]
    assert len(stream) == len(example[1])
    assert not stream.iloc[0].safe_action and pd.isna(stream.iloc[0].anchor_x)
    receipt = stream[stream.event_type.eq("Ball Receipt*")]
    assert receipt.anchor_x.isna().all() and receipt.delta_x.isna().all()
    assert not receipt.validated_anchor.any()


def test_missing_endpoint_excludes_action_only_not_validated_anchor(example):
    example[1][0]["pass"].pop("end_location")
    r = extracted(example)[1].iloc[0]
    assert r.validated_anchor and not r.safe_action
    assert r.action_status == "missing_or_invalid_endpoint"


def test_explicit_opponent_pass_is_not_leverkusen_vector(example):
    example[1][0]["team"]["id"] = 100
    r = extracted(example)[1].iloc[0]
    assert r.validated_anchor and r.anchor_x == 78
    assert not r.safe_action and pd.isna(r.delta_x)


def test_ordering_and_all_three_temporal_layers_keep_boundaries(example):
    m, e, f = example
    stream = enrich_match(
        m, list(reversed(e)), list(reversed(f)), source_revision=STATSBOMB_REVISION
    )[1]
    assert stream.event_index.is_monotonic_increasing
    summary, pairs = temporal_diagnostics(stream, stream[stream.safe_action])
    counts = summary.set_index("layer")["count"]
    assert counts.full_events == len(stream) - 3
    assert counts.safe_actions == 8
    assert counts.validated_anchors == 9
    assert pairs["safe_actions"].elapsed_seconds.eq(3).all()


def test_no_cross_match_paths_runs_or_recoveries(example):
    a = first_actions(example)
    b = a.assign(match_id=2)
    both = pd.concat([a, b], ignore_index=True)
    assert len(action_path(both)) == 2 * len(action_path(a))
    assert len(progression_runs(both)) == 2 * len(progression_runs(a))
    assert len(recovery_inventory(action_path(both))) == 2


def test_between_action_jump_is_not_added_to_forward_component(example):
    stream = extracted(example)[1]
    # A discontinuity between explicit action vectors stays descriptive, not movement.
    a = first_actions(example).copy()
    a.loc[a.index[1], ["start_x", "end_x"]] += 10
    path = action_path(a)
    p = progression_possessions(
        stream, a, path, progression_runs(a), recovery_inventory(path)
    )
    assert p.iloc[0].cumulative_forward_x == 85
    assert p.iloc[0].cumulative_backward_x == 37


def test_provider_inventory_uses_literal_fields_without_outcome_leakage():
    e = {
        "type": {"name": "Pass"},
        "out": True,
        "pass": {"type": {"name": "Throw-in"}, "outcome": {"name": "Out"}},
    }
    assert provider_signals(e) == ["out:true", "pass.outcome:Out", "pass.type:Throw-in"]
    assert provider_signals(
        {
            "type": {"name": "Shot"},
            "shot": {"outcome": {"name": "Goal"}, "statsbomb_xg": 0.9},
        }
    ) == ["type:Shot"]


def test_summaries_keep_all_possessions_and_emit_no_segmentation(example):
    before = deepcopy(example)
    _, stream, signals = extracted(example)
    tables = summarize_progression(stream, signals)
    assert "run_statistics" in tables and "run_summary" not in tables
    assert len(tables["possession_progression_summary"]) == 3
    assert set(tables["retreat_threshold_inventory"].retreat_at_least) == {
        5,
        10,
        15,
        20,
        25,
        30,
        40,
    }
    for t in tables.values():
        assert not {
            "episode_id",
            "reset",
            "is_reset",
            "eligible",
            "success",
            "danger",
            "boundary_strength",
        } & set(t.columns)
    assert len(tables["representative_timelines"]) == len(stream)
    assert example == before


def test_no_safe_actions_retains_missing_progression(example):
    m, e, _ = example
    _, stream, signals = enrich_match(m, e, [], source_revision=STATSBOMB_REVISION)
    tables = summarize_progression(stream, signals)
    p = tables["possession_progression_summary"]
    assert len(p) == 3 and p.safe_action_count.eq(0).all()
    assert p.cumulative_forward_x.isna().all()
    assert tables["retreat_from_peak"].empty

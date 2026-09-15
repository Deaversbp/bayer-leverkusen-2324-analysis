"""Twelve focused Phase 5A definition, attribution and reconciliation tests."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from leverkusen.outcomes.danger import (
    CONTEXT, OUTCOME_COLUMNS, build_anchor_outcomes, detect_outcome_events,
    is_box_entry, outcome_summary, validate_outcomes,
)
from leverkusen.outcomes.runner import boundary_audit, load_inputs


def action(typ="Pass", start=None, end=None, outcome=None, team=904):
    event = {"type": {"name": typ}, "team": {"id": team},
             "location": [101, 40] if start is None else start,
             typ.lower(): {"end_location": [102, 18] if end is None else end}}
    if outcome is not None:
        event[typ.lower()]["outcome"] = {"name": outcome}
    return event


def state(index, seconds=0, typ="Pass", spell="s1", team=904):
    return dict(match_id=1, attacking_control_spell_id=spell, event_id=f"e{index}",
                event_index=index, period=1, timestamp=str(pd.Timedelta(seconds=seconds)),
                event_type=typ, event_team="Bayer Leverkusen" if team == 904 else "Opponent",
                event_team_id=team)


def event(row, typ="shot", xg=0.2):
    return {**row, "outcome_type": typ, "shot_xg": xg if typ == "shot" else np.nan,
            "start_x": np.nan, "start_y": np.nan, "end_x": np.nan, "end_y": np.nan}


def construct(refs, outcomes):
    anchors = pd.DataFrame(refs, columns=CONTEXT)
    events = pd.DataFrame(outcomes, columns=OUTCOME_COLUMNS)
    result = build_anchor_outcomes(anchors, events)
    validate_outcomes(anchors, events, result)
    return result


def test_completed_pass_outside_to_inside_and_coordinate_guards():
    assert is_box_entry(action())
    assert is_box_entry(action(end=[120, 62]))
    for end in ([102, 17.99], [102, 62.01], [101.99, 40], [], [np.nan, 40],
                [121, 40], [True, 40], [105, 40, 0]):
        assert not is_box_entry(action(end=end))
    missing = action()
    del missing["pass"]["end_location"]
    assert not is_box_entry(missing)
    assert not is_box_entry(action(team=100))


def test_failed_pass_does_not_count():
    for outcome in ("Incomplete", "Out", "Pass Offside", "Unknown", "Injury Clearance"):
        assert not is_box_entry(action(outcome=outcome))


def test_carry_outside_to_inside_counts():
    assert is_box_entry(action("Carry"))
    assert not is_box_entry(action("Carry", start=[-1, 40]))


def test_inside_to_inside_is_not_entry():
    for typ in ("Pass", "Carry"):
        assert not is_box_entry(action(typ, start=[102, 62], end=[110, 40]))


def test_reference_shot_is_immediate_including_penalty_and_set_piece():
    ref = state(1, typ="Shot")
    row = construct([ref], [event(ref, xg=0.78)]).iloc[0]
    assert row.reference_is_shot == row.shot_within_5s == 1
    assert row.reference_shot_xg == row.next_shot_xg == row.future_xg_5s == 0.78
    assert row.seconds_to_next_shot == 0
    raw = {"id": "e1", "index": 1, "period": 1, "timestamp": ref["timestamp"],
           "type": {"name": "Shot"}, "team": {"id": 904, "name": "Bayer Leverkusen"},
           "possession": 1, "possession_team": {"id": 904},
           "shot": {"type": {"name": "Penalty"}, "statsbomb_xg": 0.78}}
    context = pd.DataFrame([{**ref, "source_order": 0, "provider_possession_id": 1}])
    assert detect_outcome_events(context, [raw]).shot_xg.tolist() == [0.78]
    context["attacking_control_spell_id"] = None
    assert detect_outcome_events(context, [raw]).empty


def test_future_shot_within_spell_and_missing_next_fields():
    refs = [state(1, 1, team=100), state(3, 8)]
    rows = construct(refs, [event(state(2, 7, "Shot"))])
    assert rows.iloc[0].reference_event_team == "Opponent"
    assert rows.iloc[0].shot_within_5s == 0
    assert rows.iloc[0].shot_within_10s == 1
    assert rows.iloc[0].seconds_to_next_shot == 6
    assert rows.iloc[1].shot_before_spell_end == 0
    assert pd.isna(rows.iloc[1].seconds_to_next_shot)
    assert pd.isna(rows.iloc[1].next_shot_event_id)


def test_new_spell_and_other_match_outcomes_never_label_previous_spell():
    ref = state(1)
    later = event(state(2, 1, "Shot", "s2"))
    other_match = event({**state(2, 1, "Shot"), "match_id": 2})
    row = construct([ref], [later, other_match]).iloc[0]
    assert row.shot_before_spell_end == row.future_xg_rest_of_spell == 0
    assert pd.isna(row.next_shot_event_id)
    refs, context, spells, outcomes = [], [], [], []
    for n, reason in enumerate(("OPPONENT_CONTROL", "BALL_OUT", "FOUL_STOPPAGE", "TERMINAL_SHOT")):
        first = state(n * 4 + 1, n * 4, spell=f"s{n}a")
        boundary = state(n * 4 + 2, n * 4 + 1, spell=None)
        following = state(n * 4 + 3, n * 4 + 2, "Shot", spell=f"s{n}b")
        refs.append(first)
        context.extend([first, boundary, following])
        outcomes.append(event(following))
        for r, end_reason in ((first, reason), (following, "PROVIDER_PARENT_END")):
            spells.append({**r, "start_event": r["event_index"], "end_event": r["event_index"],
                           "end_reason": end_reason})
    anchors = pd.DataFrame(refs)
    events = pd.DataFrame(outcomes, columns=OUTCOME_COLUMNS)
    result = build_anchor_outcomes(anchors, events)
    audit = boundary_audit(anchors, pd.DataFrame(context), pd.DataFrame(spells), events, result)
    assert len(audit) == 4 and audit.result.eq("PASS").all()


def test_multiple_shots_sum_and_missing_xg_propagates_without_imputation():
    ref = state(1)
    shots = [event(state(2, 2, "Shot"), xg=0.2), event(state(3, 8, "Shot"), xg=0.3)]
    row = construct([ref], shots).iloc[0]
    assert row.future_xg_5s == 0.2
    assert row.future_xg_10s == 0.5
    shots[1]["shot_xg"] = np.nan
    result = construct([ref], shots)
    assert result.iloc[0].shot_within_10s == 1
    assert np.isnan(result.iloc[0].future_xg_10s)
    assert outcome_summary(result).missing_future_xg_anchors.tolist() == [0, 1, 1, 1]


def test_exact_horizon_edges_and_nesting_for_all_families():
    refs = [state(1, 0.001)]
    outcomes = [event(state(2, 5.001, "Shot"), xg=0.1),
                event(state(3, 10.001, "Carry"), "box_entry"),
                event(state(4, 15.001, "Shot"), xg=0.2),
                event(state(5, 15.002, "Shot"), xg=0.4)]
    row = construct(refs, outcomes).iloc[0]
    assert [row.box_entry_within_5s, row.box_entry_within_10s, row.box_entry_within_15s,
            row.box_entry_before_spell_end] == [0, 1, 1, 1]
    assert row.future_xg_5s == row.future_xg_10s == 0.1
    assert row.future_xg_15s == pytest.approx(0.3)
    assert row.future_xg_rest_of_spell == pytest.approx(0.7)


def test_all_trusted_anchors_retained_and_locked_population_reconciles():
    anchors, _, spells = load_inputs(Path(__file__).resolve().parents[1])
    assert len(anchors) == 43737 and len(spells) == 3202
    assert anchors.match_id.nunique() == 34
    refs = [state(1), state(2, spell="s2", team=100), state(3, spell="s3")]
    result = construct(refs, [])
    assert result.reference_event_id.tolist() == ["e1", "e2", "e3"]
    assert result.future_xg_rest_of_spell.eq(0).all()


def test_same_timestamp_respects_source_order_and_immediate_entry():
    refs = [state(2, 10, "Carry"), state(4, 10)]
    outcomes = [event(state(1, 10, "Shot"), xg=0.9),
                event(refs[0], "box_entry"), event(state(3, 10, "Shot"), xg=0.1)]
    rows = construct(refs, outcomes)
    assert rows.iloc[0].future_xg_5s == 0.1
    assert rows.iloc[0].next_shot_event_id == "e3"
    assert rows.iloc[0].seconds_to_next_shot == 0
    assert rows.iloc[0].reference_is_box_entry == 1
    assert rows.iloc[1].future_xg_rest_of_spell == 0


def test_deterministic_core_output_and_corrupt_labels_rejected():
    refs = pd.DataFrame([state(1), state(3, 10)], columns=CONTEXT)
    events = pd.DataFrame([event(state(2, 5, "Shot"))], columns=OUTCOME_COLUMNS)
    first = build_anchor_outcomes(refs, events)
    second = build_anchor_outcomes(refs.iloc[::-1], events)
    assert first.to_csv(index=False) == second.to_csv(index=False)
    first.loc[1, "future_xg_rest_of_spell"] = 0.2
    with pytest.raises(ValueError, match="reconstruction"):
        validate_outcomes(refs, events, first)

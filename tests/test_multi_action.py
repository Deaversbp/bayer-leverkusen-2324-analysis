"""Strict-chain construction and fixed-motif descriptive analysis contracts."""

import numpy as np
import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences.multi_action import construct_windows, window_scope
from leverkusen.spatial.motif_analysis import fit_clustered, motif_summary
from leverkusen.spatial.orientation import VALIDATED
from leverkusen.spatial.progression_change import RESPONSES, clustered_regression


def chain(types="PPCP", dx=None, gaps=None, match=1, spell="s1"):
    n = len(types)
    dx = dx or [5., -2., 0., 8.][:n]
    gaps = gaps or [1.] * n
    times = np.r_[0, np.cumsum(gaps)]
    positions = np.r_[0, np.cumsum([2 if i % 2 == 0 else 1 for i in range(n)])]
    states, legs, actions = [], [], []
    for i, code in enumerate(types + "X"):
        typ = {"P": "Pass", "C": "Carry", "X": "Pressure"}[code]
        row = dict(match_id=match, event_id=f"{match}-{spell}-{i}", period=1, provider_possession_id=1,
            attacking_control_spell_id=spell, spatial_anchor_order=i+1, source_order=positions[i],
            event_index=positions[i]+1, event_type=typ, event_team_id=100 if code == "X" else 904,
            period_seconds=times[i], statsbomb_revision=STATSBOMB_REVISION, semantics_status=VALIDATED,
            actor_status="single", visible_area_fraction=.4,
            frame_oob=False, frame_oob_unknown=False, frame_coincident=False, frame_coincident_unknown=False,
            opp_n_valid_points_used=8, lev_n_valid_points_used=7,
            opp_goalkeeper_policy="excluded", lev_goalkeeper_policy="excluded")
        for metric in RESPONSES:
            row[metric] = 40. + i*3
            row[f"{metric}_available"] = True
            row[f"{metric}_status"] = "ok"
        states.append(row)
    for i in range(n):
        row = dict(match_id=match, from_event_id=states[i]["event_id"], to_event_id=states[i+1]["event_id"],
            statsbomb_revision=STATSBOMB_REVISION, seconds_from_previous_anchor=gaps[i],
            events_from_previous_anchor=positions[i+1]-positions[i],
            intervening_event_count=positions[i+1]-positions[i]-1)
        for metric in RESPONSES:
            row[f"delta_{metric}"] = 3.
            row[f"delta_{metric}_status"] = "ok"
        legs.append(row)
        if types[i] != "X":
            actions.append(dict(match_id=match, from_event_id=states[i]["event_id"], to_event_id=states[i+1]["event_id"],
                attacking_control_spell_id=spell, action_type=states[i]["event_type"], action_status="eligible",
                action_start_x=20. + i*2, action_end_x=20. + i*2 + dx[i], action_delta_x=dx[i],
                statsbomb_revision=STATSBOMB_REVISION))
    return pd.DataFrame(states), pd.DataFrame(legs), pd.DataFrame(actions)


@pytest.mark.parametrize("motif", ["PP", "PC", "CP", "CC"])
def test_two_action_motifs(motif):
    windows, audit = construct_windows(*chain(motif, dx=[2., 3.]))
    assert len(windows) == 1
    assert windows.iloc[0].action_type_motif == motif
    assert audit.N.sum() == 1


@pytest.mark.parametrize("motif", ["PPP", "PPC", "PCP", "PCC", "CPP", "CPC", "CCP", "CCC"])
def test_three_action_motifs(motif):
    windows, _ = construct_windows(*chain(motif, dx=[2., 3., 4.]))
    assert windows[windows.window_length.eq(3)].action_type_motif.item() == motif
    assert windows.window_length.eq(2).sum() == 2


@pytest.mark.parametrize("different_match", [False, True])
def test_no_cross_spell_or_match_windows(different_match):
    first = chain("P", dx=[1.])
    second = chain("C", dx=[1.], match=2 if different_match else 1, spell="s1" if different_match else "s2")
    inputs = [pd.concat([a, b], ignore_index=True) for a, b in zip(first, second)]
    windows, _ = construct_windows(*inputs)
    assert windows.empty


def test_trusted_context_anchor_cannot_be_skipped():
    windows, audit = construct_windows(*chain("PXP", dx=[2., 0., 3.]))
    assert windows.empty
    assert audit.N.sum() == 3
    assert set(audit.selection_reason) == {"opponent_from_anchor"}


def test_ineligible_action_breaks_chain_without_skipping():
    anchors, legs, actions = chain("PPP", dx=[1., 2., 3.])
    windows, audit = construct_windows(anchors, legs, actions.drop(index=1))
    assert windows.empty
    assert set(audit.selection_reason) == {"not_eligible_under_phase4a_progression_rules"}


def test_final_observation_and_net_delta_and_progression():
    windows, _ = construct_windows(*chain("PCP", dx=[5., -2., 0.], gaps=[2., 1., 4.]))
    row = windows[windows.window_length.eq(3)].iloc[0]
    assert row.anchor_3_event_id == "1-s1-3" and row.action_3_event_id == "1-s1-2"
    assert row.net_opp_centroid_x == 9. and row.leg_2_delta_opp_centroid_x == 3.
    assert row.total_progression == 3. and row.total_positive_progression == 5.
    assert row.total_nonpositive_magnitude == 2. and row.direction_profile == "FRR"
    assert row.net_action_progression == 4.  # endpoint-to-start differs from summed vectors
    assert row.duration_seconds == 7. and row.intervening_full_event_count == 2
    assert row.full_event_span_count == 6


def test_overlap_ids_and_bytes_deterministic_under_input_shuffle():
    inputs = chain()
    first, _ = construct_windows(*inputs)
    second, _ = construct_windows(*[f.sample(frac=1, random_state=4) for f in inputs])
    assert len(first) == 5 and first.window_id.nunique() == 5
    assert first.to_csv(index=False) == second.to_csv(index=False)
    two = first[first.window_length.eq(2)]
    assert two.iloc[0].action_2_event_id == two.iloc[1].action_1_event_id


@pytest.mark.parametrize("scope,gaps,expected", [
    ("gap_le_5", [5., 1., 1.], True), ("gap_le_5", [1., 5.1, 1.], False),
    ("gap_le_3", [3., 3., 3.], True), ("gap_le_3", [1., 1., 3.1], False)])
def test_gap_sensitivity_checks_every_leg_not_total_duration(scope, gaps, expected):
    windows, _ = construct_windows(*chain("PPP", dx=[1., 2., 3.], gaps=gaps))
    assert bool(window_scope(windows[windows.window_length.eq(3)], scope).item()) is expected


def test_missing_geometry_is_metric_specific_and_partial_ranges_explicit():
    anchors, legs, actions = chain("PPP", dx=[1., 2., 3.])
    anchors.loc[1, "opp_convex_hull_area"] = np.nan
    anchors.loc[1, "opp_convex_hull_area_status"] = "insufficient_points"
    anchors.loc[1, "opp_convex_hull_area_available"] = False
    for i, status in ((0, "to_endpoint_unavailable"), (1, "from_endpoint_unavailable")):
        legs.loc[i, "delta_opp_convex_hull_area"] = np.nan
        legs.loc[i, "delta_opp_convex_hull_area_status"] = status
    windows, _ = construct_windows(anchors, legs, actions)
    whole = windows[windows.window_length.eq(3)].iloc[0]
    assert whole.net_opp_convex_hull_area == 9.  # endpoints available despite missing interior
    assert whole.observed_opp_convex_hull_area_count == 3
    assert whole.observed_opp_convex_hull_area_status == "partial_available_states"
    assert np.isnan(whole.leg_1_delta_opp_convex_hull_area)
    ending = windows[windows.window_length.eq(2)].iloc[1]
    assert np.isnan(ending.net_opp_convex_hull_area)
    assert ending.net_opp_centroid_x == 6.


def test_no_outcome_columns_used():
    inputs = chain()
    clean, _ = construct_windows(*inputs)
    polluted = [f.assign(future_goal=True, xg=99., box_entry=True) for f in inputs]
    actual, _ = construct_windows(*polluted)
    assert clean.to_csv(index=False) == actual.to_csv(index=False)
    assert not {"future_goal", "xg", "box_entry"} & set(actual)


def test_any_interior_anomaly_counts_and_terminal_team_not_replaced():
    anchors, legs, actions = chain("PPP", dx=[1., 2., 3.])
    anchors.loc[1, "frame_oob"] = True
    anchors.loc[1, "frame_coincident"] = True
    windows, _ = construct_windows(anchors, legs, actions)
    assert not window_scope(windows, "exclude_oob").any()
    assert not window_scope(windows, "exclude_coincidence").any()
    whole = windows[windows.window_length.eq(3)]
    assert not window_scope(whole, "terminal_leverkusen").any()
    assert whole.terminal_event_type.item() == "Pressure"


def test_empty_motifs_retained_in_summary():
    windows, _ = construct_windows(*chain("PPP", dx=[1., 2., 3.]))
    summary = motif_summary(windows, system="action")
    assert len(summary) == 12 and summary.N.eq(0).sum() == 10
    assert set(summary.motif_system) == {"action"}


def test_multivariate_cluster_covariance_matches_phase4a_when_no_dummies():
    x = np.arange(12, dtype=float)
    y = x * .5 + np.tile([1., -1., 2.], 4)
    matches = np.repeat([1, 2, 3, 4], 3)
    new = fit_clustered(np.column_stack([np.ones(12), x]), y, matches)
    old = clustered_regression(x, y, matches)
    assert new["beta"][1] == pytest.approx(old["slope"])
    assert new["se"][1] == pytest.approx(old["cluster_se"])
    assert new["low"][1] == pytest.approx(old["ci_low"])

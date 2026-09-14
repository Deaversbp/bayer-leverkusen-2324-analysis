"""Focused Phase 4A selection, inference and deterministic-summary contracts."""

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.spatial.orientation import VALIDATED
from leverkusen.spatial.progression_change import (
    RESPONSES, action_inventory, clustered_regression, scope_mask,
    select_transitions, starting_third, summarize,
)


@pytest.fixture
def sample():
    contexts, raw, inventories, anchor_rows, pairs = [], [], [], [], []
    specs = [("Pass", 10, 20, 904), ("Carry", 20, 25, 904), ("Pass", 25, 35, 100),
             ("Pass", 25, 60, 904), ("Clearance", 60, None, 100), ("Carry", 15, 18, 904),
             ("Carry", 18, 30, 904), ("Pass", 30, 40, 904), ("Pass", 40, 34, 904),
             ("Shot", 34, None, 904), ("Carry", 20, None, 904), ("Shot", 21, None, 904)]
    for mid in (1, 2, 3, 4):
        events, context = [], []
        for i, (typ, start, end, team) in enumerate(specs, 1):
            eid, spell = f"{mid}-{i}", f"{mid}-s{1 if i <= 10 else 2}"
            stamp = f"00:00:{i:02}.000"
            event = dict(id=eid, index=i, period=1, timestamp=stamp,
                         team=dict(id=team), type=dict(name=typ), location=[start, 20])
            if end is not None:
                event[typ.lower()] = dict(end_location=[end, 20])
            if i == 4:
                event["pass"]["outcome"] = {"name": "Incomplete"}
            if i == 8:
                event["pass"]["type"] = {"name": "Free Kick"}
            events.append(event)
            context.append(dict(match_id=mid, event_id=eid, event_index=i, period=1, timestamp=stamp,
                period_seconds=float(i), source_order=i-1, event_team_id=team, event_type=typ,
                home_team_id=904, away_team_id=100, attacking_control_spell_id=spell,
                semantics_status=VALIDATED if typ != "Clearance" else "unsupported_event_type",
                statsbomb_revision=STATSBOMB_REVISION))
        c = pd.DataFrame(context)
        inventory = action_inventory(c, events)
        contexts.append(c)
        raw.append(events)
        inventories.append(inventory)
        a = c[c.semantics_status.eq(VALIDATED)].copy()
        a["spatial_anchor_order"] = a.groupby("attacking_control_spell_id").cumcount() + 1
        a["orientation_status"] = np.where(a.event_team_id.eq(904), "identity_explicit", "rotated_180")
        anchor_rows.append(a)
        for _, group in a.groupby("attacking_control_spell_id"):
            records = list(group.itertuples(index=False))
            for first, last in zip(records, records[1:]):
                row = dict(match_id=mid, period=1, provider_possession_id=1,
                    attacking_control_spell_id=first.attacking_control_spell_id,
                    from_event_id=first.event_id, to_event_id=last.event_id,
                    from_event_index=first.event_index, to_event_index=last.event_index,
                    from_event_type=first.event_type, to_event_type=last.event_type,
                    to_event_team_id=last.event_team_id,
                    seconds_from_previous_anchor=6. if first.event_index == 1 else 3. if first.event_index == 2 else 1.,
                    events_from_previous_anchor=last.source_order-first.source_order,
                    intervening_event_count=last.source_order-first.source_order-1,
                    statsbomb_revision=STATSBOMB_REVISION)
                for endpoint in ("from", "to"):
                    for key, value in dict(visible_area_fraction=.4, actor_status="single", frame_oob=False,
                        frame_oob_unknown=False, frame_coincident=False, frame_coincident_unknown=False,
                        opp_n_valid_points_used=8, lev_n_valid_points_used=7,
                        opp_goalkeeper_policy="excluded", lev_goalkeeper_policy="excluded").items():
                        row[f"{endpoint}_{key}"] = value
                for response in RESPONSES:
                    row[f"delta_{response}"] = float(first.event_index + mid)
                    row[f"delta_{response}_status"] = "ok"
                pairs.append(row)
    return pd.concat(contexts), raw, pd.concat(inventories), pd.concat(anchor_rows), pd.DataFrame(pairs)


def selected(sample):
    return select_transitions(sample[4], sample[3], sample[2])


@pytest.mark.parametrize("typ,index,dx", [("Pass", 1, 10.), ("Carry", 2, 5.), ("Pass", 9, -6.)])
def test_eligible_actions_and_signed_delta(sample, typ, index, dx):
    data, _ = selected(sample)
    row = data[data.from_event_id.eq(f"1-{index}")].iloc[0]
    assert row.action_type == typ and row.action_delta_x == dx
    assert row.action_end_x - row.action_start_x == dx


def test_opponent_from_and_non_actions_excluded(sample):
    data, audit = selected(sample)
    assert "1-3" not in set(data.from_event_id)
    assert audit.set_index("from_event_id").loc["1-3", "selection_reason"] == "opponent_from_anchor"


def test_cross_spell_and_missing_match_anchor_excluded(sample):
    pairs = sample[4].copy()
    pairs.loc[0, "to_event_id"] = "1-11"
    _, audit = select_transitions(pairs, sample[3], sample[2])
    assert audit.iloc[0].selection_reason == "cross_spell"
    pairs.loc[0, "to_event_id"] = "2-2"
    _, audit = select_transitions(pairs, sample[3], sample[2])
    assert audit.iloc[0].selection_reason == "missing_exact_anchor"


def test_failed_invalid_restart_and_relocation_guards(sample):
    data, audit = selected(sample)
    reasons = audit.set_index("from_event_id").selection_reason
    assert reasons["1-4"] == "failed_or_unknown_pass_endpoint"
    assert reasons["1-6"] == "inherited_relocation_affected"
    assert reasons["1-8"] == "inherited_restart_context"
    assert reasons["1-11"] == "missing_or_invalid_endpoint"
    assert "1-7" in set(data.from_event_id)  # existing state restores eligibility at peak


def test_existing_metric_delta_and_missingness_remain_metric_specific(sample):
    pairs = sample[4].copy()
    pairs.loc[0, "delta_opp_centroid_x"] = np.nan
    pairs.loc[0, "delta_opp_centroid_x_status"] = "to_endpoint_unavailable"
    data, _ = select_transitions(pairs, sample[3], sample[2])
    row = data.iloc[0]
    assert np.isnan(row.delta_opp_centroid_x)
    assert row.delta_opp_visible_depth == 2
    table = summarize(data)["metric_summary"]
    table = table[table.action_type.eq("Pass")].set_index("response_metric")
    assert table.loc["opp_centroid_x", "N"] == table.loc["opp_visible_depth", "N"] - 1


def test_gap_filters_inclusive_and_to_anchor_filter_does_not_skip(sample):
    data, _ = selected(sample)
    assert scope_mask(data, "all").all()
    assert not scope_mask(data, "gap_le_5")[data.from_event_id.eq("1-1")].item()
    assert scope_mask(data, "gap_le_3")[data.from_event_id.eq("1-2")].item()
    assert not scope_mask(data, "to_leverkusen")[data.from_event_id.eq("1-2")].item()
    assert data[data.from_event_id.eq("1-2")].to_event_id.item() == "1-3"


def test_thirds_are_descriptive_and_oob_is_not_dropped():
    assert starting_third(pd.Series([-1, 0, 39.9, 40, 79.9, 80, 120, 121])).tolist() == [
        "outside_pitch", "defensive_third", "defensive_third", "middle_third",
        "middle_third", "attacking_third", "attacking_third", "outside_pitch"]


def test_pass_carry_separate_and_deterministic(sample):
    data, _ = selected(sample)
    a, b = summarize(data), summarize(data.sample(frac=1, random_state=3))
    assert set(a["metric_summary"].action_type) == {"Pass", "Carry"}
    assert len(a["metric_summary"]) == 36
    for key in a:
        assert a[key].to_csv(index=False) == b[key].to_csv(index=False)


def test_outcomes_cannot_affect_actions_or_enter_dataset(sample):
    events = deepcopy(sample[1][0])
    for event in events:
        event["shot"] = {"outcome": {"name": "Goal"}, "statsbomb_xg": .99}
        event["future_xg"] = 10
    actual = action_inventory(sample[0][sample[0].match_id.eq(1)], events)
    expected = sample[2][sample[2].match_id.eq(1)]
    pd.testing.assert_frame_equal(actual, expected)
    pairs = sample[4].assign(future_goal=True, xg=.99)
    data, _ = select_transitions(pairs, sample[3], sample[2])
    assert not any("goal" in c or "xg" in c or "outcome" in c for c in data.columns if "goalkeeper" not in c)


def test_whole_frame_sensitivities_use_both_endpoints(sample):
    data, _ = selected(sample)
    data.loc[0, "to_frame_oob"] = True
    data.loc[1, "from_frame_coincident"] = True
    assert not scope_mask(data, "exclude_oob").iloc[0]
    assert not scope_mask(data, "exclude_coincidence").iloc[1]
    assert scope_mask(data, "all").all()


def test_match_cluster_se_against_centered_scalar_formula():
    x = np.array([0., 1., 3., 5., 2., 6., 8., 10.])
    y = 2 + .4 * x + np.array([1., -1., 2., -2., 3., -1., -2., 1.])
    groups = np.repeat([1, 2, 3, 4], 2)
    fit = clustered_regression(x, y, groups)
    centered = x - x.mean()
    slope = np.sum(centered * (y-y.mean())) / np.sum(centered**2)
    residual = y - (y.mean() - slope*x.mean()) - slope*x
    score = np.array([np.sum(centered[groups==g] * residual[groups==g]) for g in np.unique(groups)])
    se = np.sqrt(np.sum(score**2) / np.sum(centered**2)**2 * (4/3) * (7/6))
    assert fit["slope"] == pytest.approx(slope)
    assert fit["cluster_se"] == pytest.approx(se)
    assert fit["ci_low"] < slope < fit["ci_high"]
    assert np.isnan(clustered_regression(x, y, np.ones(len(x)))["cluster_se"])

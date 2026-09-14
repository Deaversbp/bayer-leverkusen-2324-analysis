"""New Phase 3B joins, observational gaps and metric-specific transitions."""

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences.spatial_readiness import write_identical
from leverkusen.sequences.spatial_sequences import (
    EVENT, attach_geometry, attach_membership, construct_sequences, event_context,
    require_revision, spell_readiness,
)
from leverkusen.spatial.geometry import build_frame_geometry
from leverkusen.spatial.orientation import VALIDATED


@pytest.fixture
def example():
    contexts, memberships, geometry, summaries = [], [], [], []
    for mid in (11, 22):
        match = dict(match_id=mid, home_team=dict(home_team_id=100), away_team=dict(away_team_id=904))
        events, frames = [], []
        types = ["Pass", "Ball Receipt*", "Duel", "Pressure", "Shot", "Pass", "Duel"]
        stamps = ["00:00:00.000", "00:00:00.250", "00:00:01.500", "00:00:01.500",
                  "00:00:15.000", "00:00:16.200", "00:00:30.000"]
        for i, (typ, stamp) in enumerate(zip(types, stamps), 1):
            event = dict(id=f"{mid}-{i}", index=i * 10, period=2, timestamp=stamp, possession=1,
                         team=dict(id=100 if typ == "Pressure" else 904, name="Opponent" if typ == "Pressure" else "Leverkusen"),
                         possession_team=dict(id=904, name="Leverkusen"), type=dict(name=typ), location=[10, 20])
            events.append(event)
            if typ == "Duel":
                continue
            points = [dict(location=p, teammate=flag, keeper=keeper, actor=j == 0)
                      for j, (p, flag, keeper) in enumerate([
                          ([10, 20], True, False), ([20, 20], True, False), ([10, 30], True, False),
                          ([30, 40], False, False), ([40, 40], False, False), ([30, 50], False, False),
                          ([121, 0], False, True), ([10, 20], True, False)])]
            if typ == "Shot":
                points = [points[0], points[3]]
            frames.append(dict(event_uuid=event["id"], freeze_frame=points, visible_area=[0, 0, 120, 0, 120, 80, 0, 80]))
        original = deepcopy(events)
        context = event_context(match, events, frames, source_revision=STATSBOMB_REVISION)
        assert events == original
        member = context[["match_id", "period", "provider_possession_id", "possession_team_id",
                          "event_index", "timestamp", "period_seconds", "event_type", "event_team"]].copy()
        # Intentionally reuse spell labels across matches to exercise match isolation.
        member["attacking_control_spell_id"] = ["s1"] * 5 + ["s2", "s3"]
        member["spell_event_order"] = [1, 2, 3, 4, 5, 1, 1]
        member["membership_status"] = "inside_spell"
        for spell, count, start, end, duration in (("s1", 5, 10, 50, 15.), ("s2", 1, 60, 60, 0.), ("s3", 1, 70, 70, 0.)):
            summaries.append(dict(match_id=mid, period=2, provider_possession_id=1, possession_team_id=904,
                                  attacking_control_spell_id=spell, event_count=count, start_event=start,
                                  end_event=end, duration_seconds=duration, statsbomb_revision=STATSBOMB_REVISION))
        contexts.append(context)
        memberships.append(member)
        geometry.append(build_frame_geometry(mid, events, frames, source_revision=STATSBOMB_REVISION))
    canonical = pd.concat(contexts, ignore_index=True)
    membership = pd.concat(memberships, ignore_index=True)
    return membership, canonical, pd.concat(geometry, ignore_index=True), pd.DataFrame(summaries)


def build(example):
    membership, canonical, geometry, _ = example
    context = attach_membership(membership, canonical)
    a, t = construct_sequences(context, geometry)
    return context, a, t


def test_exact_join_hydrates_uuid_and_rejects_approximate_or_changed_identity(example):
    membership, canonical, _, _ = example
    joined = attach_membership(membership.sample(frac=1, random_state=1), canonical)
    assert len(joined) == 14
    assert joined.event_id.tolist() == canonical.event_id.tolist()
    changed = membership.copy()
    changed.loc[0, "event_index"] += 1
    with pytest.raises(ValueError, match="missing or extra"):
        attach_membership(changed, canonical)
    for column, value in (("event_type", "Carry"), ("timestamp", "00:00:00.001"), ("period", 1)):
        changed = membership.copy()
        changed.loc[0, column] = value
        with pytest.raises(ValueError, match="context mismatch"):
            attach_membership(changed, canonical)
    changed = membership.assign(event_id=canonical.event_id)
    changed.loc[0, "event_id"] = "wrong-uuid"
    with pytest.raises(ValueError, match="event_id"):
        attach_membership(changed, canonical)


def test_duplicate_identity_rejected(example):
    membership, canonical, _, _ = example
    with pytest.raises(pd.errors.MergeError):
        attach_membership(pd.concat([membership, membership.iloc[:1]]), canonical)


def test_trusted_anchor_attaches_and_unsupported_stays_context(example):
    context, a, _ = build(example)
    assert len(context) == 14 and len(a) == 8
    assert a.semantics_status.eq(VALIDATED).all()
    receipt = context[context.event_type.eq("Ball Receipt*")]
    assert receipt.linked_360.all()
    assert receipt.semantics_status.eq("unsupported_event_type").all()
    assert not a.event_id.isin(receipt.event_id).any()
    assert context[context.event_type.eq("Duel")].semantics_status.eq("no_360_frame").all()


@pytest.mark.parametrize("event_id,lev_x,lev_y,opp_x,opp_y,orientation", [
    ("11-1", 12.5, 22.5, 100 / 3, 130 / 3, "identity_explicit"),
    ("11-4", 120 - 100 / 3, 80 - 130 / 3, 107.5, 57.5, "rotated_180"),
])
def test_team_mapping_and_180_degree_normalization(example, event_id, lev_x, lev_y, opp_x, opp_y, orientation):
    _, a, _ = build(example)
    row = a.set_index("event_id").loc[event_id]
    assert row.lev_centroid_x == pytest.approx(lev_x)
    assert row.lev_centroid_y == pytest.approx(lev_y)
    assert row.opp_centroid_x == pytest.approx(opp_x)
    assert row.opp_centroid_y == pytest.approx(opp_y)
    assert row.orientation_status == orientation
    assert row.lev_visible_width == row.opp_visible_width == 10
    assert row.lev_goalkeeper_policy == "excluded"


def test_opponent_pressure_is_context_not_ball_progression(example):
    _, a, _ = build(example)
    pressure = a[a.event_type.eq("Pressure")]
    assert pressure.anchor_role.eq("opponent_context").all()
    assert not pressure.is_ball_progression_action.any()


def test_no_cross_spell_or_cross_match_transition(example):
    _, a, t = build(example)
    assert len(t) == 4
    assert t.attacking_control_spell_id.eq("s1").all()
    lookup = a.set_index(EVENT)
    for row in t.itertuples():
        assert lookup.loc[(row.match_id, row.from_event_id), "attacking_control_spell_id"] == row.attacking_control_spell_id
        assert lookup.loc[(row.match_id, row.to_event_id), "attacking_control_spell_id"] == row.attacking_control_spell_id
    assert a[a.attacking_control_spell_id.eq("s2")].previous_spatial_anchor_event_id.isna().all()


def test_source_order_and_actual_timestamp_gaps_include_unsupported_events(example):
    membership, canonical, geometry, _ = example
    context = attach_membership(membership, canonical).sample(frac=1, random_state=7)
    a, t = construct_sequences(context, geometry.sample(frac=1, random_state=8))
    first = t.iloc[0]
    assert (first.from_event_id, first.to_event_id) == ("11-1", "11-4")
    assert first.events_from_previous_anchor == 3  # index difference is 30
    assert first.intervening_event_count == 2
    assert first.seconds_from_previous_anchor == 1.5
    assert a.loc[a.event_id.eq("11-4"), "events_from_spell_start"].item() == 3
    assert a[a.event_id.eq("11-5")].seconds_from_spell_start.item() == 15
    assert a[a.attacking_control_spell_id.eq("s1")].spatial_anchor_order.tolist() == [1, 2, 3, 1, 2, 3]


def test_deltas_require_both_metric_endpoints_and_retain_reasons(example):
    _, a, t = build(example)
    first, second = t.iloc[0], t.iloc[1]
    assert first.delta_lev_centroid_x == pytest.approx((120 - 100 / 3) - 12.5)
    assert first.delta_lev_centroid_x_status == "ok"
    assert np.isnan(second.delta_lev_convex_hull_area)
    assert second.delta_lev_convex_hull_area_status == "to_endpoint_unavailable"
    assert second.to_lev_convex_hull_area_status == "insufficient_points"
    # Existing one-point span/count metrics remain available independently.
    assert second.delta_lev_visible_width_status == "ok"
    assert second.delta_lev_visible_player_count == -2
    assert not a[a.event_type.eq("Shot")].lev_convex_hull_area_available.any()


def test_missing_from_and_both_endpoint_status(example):
    membership, canonical, geometry, _ = example
    geometry = geometry.copy()
    subset = geometry.selected_subset.eq("all_visible") & geometry.goalkeeper_policy.eq("excluded")
    for event_id in ("11-1", "11-4"):
        mask = subset & geometry.event_id.eq(event_id)
        geometry.loc[mask, "mean_pairwise_distance"] = np.nan
        geometry.loc[mask, "mean_pairwise_distance_status"] = "numeric_error"
    _, t = construct_sequences(attach_membership(membership, canonical), geometry)
    assert t.iloc[0].delta_all_mean_pairwise_distance_status == "both_endpoints_unavailable"
    assert t.iloc[1].delta_all_mean_pairwise_distance_status == "from_endpoint_unavailable"
    assert t.iloc[:2].delta_all_mean_pairwise_distance.isna().all()


def test_no_interpolation_no_gap_split_and_no_forward_fill(example):
    _, a, t = build(example)
    assert len(a) == 8 and len(t) == 4
    assert t.seconds_from_previous_anchor.max() == 13.5
    assert a[a.event_type.eq("Shot")].lev_convex_hull_area.isna().all()
    assert a[a.attacking_control_spell_id.eq("s1")].next_spatial_anchor_event_id.isna().sum() == 2


def test_original_frame_flags_survive_keeper_exclusion(example):
    _, a, t = build(example)
    row = a.iloc[0]
    assert row.frame_oob and row.frame_coincident
    assert row.all_n_out_of_bounds_points == 0  # OOB keeper remains in whole-frame flag
    assert row.all_n_coincident_records == 1
    assert row.all_visible_player_count == 7
    assert row.all_visible_player_count_keeper_included == 8
    assert row.visible_area_fraction == 1
    assert t.iloc[0].from_frame_oob


def test_missing_or_wrong_geometry_rejected(example):
    membership, canonical, geometry, _ = example
    context = attach_membership(membership, canonical)
    with pytest.raises(ValueError, match="Missing exact geometry"):
        construct_sequences(context, geometry[~geometry.event_id.eq("11-1")])
    wrong = geometry.copy()
    wrong.loc[wrong.event_id.eq("11-1"), "statsbomb_revision"] = "0" * 40
    with pytest.raises(ValueError, match="revision"):
        construct_sequences(context, wrong)
    with pytest.raises(ValueError, match="Only trusted"):
        attach_geometry(context, geometry)


def test_readiness_retains_zero_one_and_multi_anchor_spells(example):
    context, a, _ = build(example)
    r = spell_readiness(context, a, example[3])
    assert len(r) == 6
    assert r.has_0_anchors.sum() == r.has_1_anchors.sum() == r.has_3_plus_anchors.sum() == 2
    assert r[r.has_0_anchors].first_anchor_event_id.isna().all()
    assert r[r.has_1_anchors].median_anchor_gap.isna().all()
    assert r[r.has_3_plus_anchors].anchor_proportion.eq(.6).all()


def test_deterministic_bytes_with_reordered_input_and_output_protection(example, tmp_path):
    membership, canonical, geometry, _ = example
    first = construct_sequences(attach_membership(membership, canonical), geometry)
    second = construct_sequences(attach_membership(membership.sample(frac=1, random_state=4), canonical), geometry.sample(frac=1, random_state=5))
    for index, (a, b) in enumerate(zip(first, second)):
        text = a.to_csv(index=False)
        assert text == b.to_csv(index=False)
        path = tmp_path / f"{index}.csv"
        assert write_identical(path, text) == write_identical(path, text)
        with pytest.raises(ValueError, match="Refusing to overwrite"):
            write_identical(path, text + "changed")


@pytest.mark.parametrize("revision", ["0" * 40, None, "main"])
def test_source_revision_fail_closed(example, revision):
    membership, canonical, _, _ = example
    canonical.loc[0, "statsbomb_revision"] = revision
    with pytest.raises(ValueError, match="revision"):
        attach_membership(membership, canonical)
    with pytest.raises(ValueError, match="revision"):
        require_revision([STATSBOMB_REVISION, revision])

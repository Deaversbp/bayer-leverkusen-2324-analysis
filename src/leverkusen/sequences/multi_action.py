"""Strict overlapping two/three-action windows on frozen Phase 3B/4A identities."""

from collections import Counter
from itertools import product

import numpy as np
import pandas as pd

from leverkusen.data.semantic_diagnostics import TEAM_ID
from leverkusen.sequences.spatial_sequences import EVENT, SPELL, require_revision
from leverkusen.spatial.orientation import VALIDATED
from leverkusen.spatial.progression_change import RESPONSES, starting_third

LENGTHS = (2, 3)
SCOPES = ("all", "gap_le_5", "gap_le_3", "terminal_leverkusen", "exclude_oob", "exclude_coincidence")


def motif_labels(length, system="action"):
    if length not in LENGTHS or system not in ("action", "direction"):
        raise ValueError("Only two/three-action symbolic motifs are supported")
    return ["".join(p) for p in product("PC" if system == "action" else "FR", repeat=length)]


def construct_windows(anchors, transitions, eligible):
    """Reuse materialized Phase 4A eligibility/vectors; never reclassify progression.

    Candidate denominator is every contiguous k+1-anchor tuple in each spell,
    including those with ineligible FROM states. First-failure reasons partition it.
    Geometry availability never changes window membership.
    """
    for table in (anchors, transitions, eligible):
        require_revision(table.statsbomb_revision)
    if anchors.duplicated(EVENT).any() or eligible.duplicated(["match_id", "from_event_id"]).any():
        raise ValueError("Ambiguous anchor/action identity")
    pairkey = ["match_id", "from_event_id", "to_event_id"]
    if transitions.duplicated(pairkey).any():
        raise ValueError("Ambiguous transition identity")
    a = anchors.sort_values(["match_id", "source_order"]).reset_index(drop=True)
    if not a.semantics_status.eq(VALIDATED).all():
        raise ValueError("Anchor input contains unsupported states")
    by_event = {(r.match_id, r.event_id): r for r in a.itertuples(index=False)}
    pairs = {tuple(getattr(r, c) for c in pairkey): r for r in transitions.itertuples(index=False)}
    actions = {(r.match_id, r.from_event_id): r for r in eligible.itertuples(index=False)}
    for key, row in actions.items():
        first, last = by_event.get(key), by_event.get((row.match_id, row.to_event_id))
        if first is None or last is None or (row.match_id, row.from_event_id, row.to_event_id) not in pairs:
            raise ValueError("Eligible Phase 4A leg lacks exact Phase 3B identity")
        if (first.attacking_control_spell_id != last.attacking_control_spell_id
                or row.attacking_control_spell_id != first.attacking_control_spell_id
                or last.spatial_anchor_order != first.spatial_anchor_order + 1):
            raise ValueError("Eligible Phase 4A leg skips an anchor or crosses a spell")
        if first.event_team_id != TEAM_ID or first.event_type not in ("Pass", "Carry") or row.action_status != "eligible":
            raise ValueError("Inconsistent Phase 4A eligible action contract")
        if not np.isfinite([row.action_start_x, row.action_end_x, row.action_delta_x]).all():
            raise ValueError("Nonfinite inherited progression")
        if not np.isclose(row.action_end_x - row.action_start_x, row.action_delta_x, rtol=0, atol=1e-10):
            raise ValueError("Inherited progression differs from explicit vector")
    rows, counts = [], Counter()
    for _, group in a.groupby(SPELL, sort=True):
        states = list(group.itertuples(index=False))
        if group.period.nunique() != 1 or group.provider_possession_id.nunique() != 1:
            raise ValueError("Spell crosses a period or provider parent")
        if not group.spatial_anchor_order.eq(np.arange(1, len(group) + 1)).all():
            raise ValueError("Incomplete or unordered trusted-anchor inventory")
        for length in LENGTHS:
            for start in range(len(states) - length):
                chain = states[start:start + length + 1]
                legs, vectors, reason = [], [], "eligible"
                for first, last in zip(chain, chain[1:]):
                    leg = pairs.get((first.match_id, first.event_id, last.event_id))
                    action = actions.get((first.match_id, first.event_id))
                    if leg is None:
                        raise ValueError("Consecutive anchors lack a frozen Phase 3B transition")
                    if first.event_team_id != TEAM_ID:
                        reason = "opponent_from_anchor"
                    elif first.event_type not in ("Pass", "Carry"):
                        reason = "non_pass_carry_from_anchor"
                    elif action is None:
                        reason = "not_eligible_under_phase4a_progression_rules"
                    if reason != "eligible":
                        break
                    legs.append(leg)
                    vectors.append(action)
                counts[(length, reason)] += 1
                if reason == "eligible":
                    rows.append(window_row(chain, legs, vectors))
    audit = pd.DataFrame([dict(window_length=k, selection_reason=reason, N=n)
                          for (k, reason), n in sorted(counts.items())])
    windows = pd.DataFrame(rows)
    if not windows.empty:
        windows["starting_third"] = starting_third(windows.first_action_start_x)
        windows = windows.sort_values(["window_length", "match_id", "first_anchor_source_order"]).reset_index(drop=True)
    return windows, audit


def window_row(states, legs, actions):
    first, last, length = states[0], states[-1], len(actions)
    dx = np.array([r.action_delta_x for r in actions])
    gaps = np.array([r.seconds_from_previous_anchor for r in legs])
    event_gaps = np.array([r.events_from_previous_anchor for r in legs])
    if (gaps < 0).any() or (event_gaps < 1).any():
        raise ValueError("Invalid inherited leg gaps")
    row = dict(window_id=f"{first.match_id}:{first.attacking_control_spell_id}:k{length}:a{first.spatial_anchor_order}",
        match_id=first.match_id, period=first.period, provider_possession_id=first.provider_possession_id,
        attacking_control_spell_id=first.attacking_control_spell_id, window_length=length,
        first_anchor_source_order=first.source_order,
        action_type_motif="".join(r.action_type[0] for r in actions),
        direction_profile="".join("F" if value > 0 else "R" for value in dx),
        carry_action_count=sum(r.action_type == "Carry" for r in actions),
        total_progression=float(dx.sum()), total_positive_progression=float(dx.clip(0).sum()),
        total_nonpositive_magnitude=float(-dx.clip(max=0).sum()),
        first_action_start_x=actions[0].action_start_x, final_action_end_x=actions[-1].action_end_x,
        net_action_progression=actions[-1].action_end_x - actions[0].action_start_x,
        duration_seconds=last.period_seconds - first.period_seconds,
        maximum_leg_gap=float(gaps.max()), mean_leg_gap=float(gaps.mean()), median_leg_gap=float(np.median(gaps)),
        intervening_full_event_count=int(sum(r.intervening_event_count for r in legs)),
        full_event_span_steps=int(last.source_order - first.source_order),
        full_event_span_count=int(last.source_order - first.source_order + 1),
        terminal_event_type=last.event_type, terminal_event_team_id=last.event_team_id,
        statsbomb_revision=first.statsbomb_revision)
    if not np.isclose(gaps.sum(), row["duration_seconds"], atol=1e-9, rtol=0) or event_gaps.sum() != row["full_event_span_steps"]:
        raise ValueError("Inherited leg gaps do not reconcile to full window span")
    for i in range(4):
        state = states[i] if i <= length else None
        row[f"anchor_{i}_event_id"] = state.event_id if state else None
        for col in ("period_seconds", "event_index", "visible_area_fraction", "actor_status",
                    "frame_oob", "frame_oob_unknown", "frame_coincident", "frame_coincident_unknown",
                    "opp_n_valid_points_used", "lev_n_valid_points_used", "opp_goalkeeper_policy", "lev_goalkeeper_policy"):
            row[f"anchor_{i}_{col}"] = getattr(state, col) if state else None
    for flag in ("frame_oob", "frame_oob_unknown", "frame_coincident", "frame_coincident_unknown"):
        row[f"any_{flag}"] = any(getattr(r, flag) for r in states)
    for i in range(1, 4):
        action = actions[i - 1] if i <= length else None
        leg = legs[i - 1] if i <= length else None
        for name, attr in (("event_id", "from_event_id"), ("type", "action_type"),
                           ("delta_x", "action_delta_x"), ("start_x", "action_start_x"), ("end_x", "action_end_x")):
            row[f"action_{i}_{name}"] = getattr(action, attr) if action else None
        row[f"leg_{i}_gap_seconds"] = gaps[i - 1] if leg else None
        row[f"leg_{i}_intervening_events"] = leg.intervening_event_count if leg else None
    for metric in RESPONSES:
        values = np.array([getattr(s, metric) for s in states], dtype=float)
        available = np.array([getattr(s, f"{metric}_available") for s in states], dtype=bool)
        if np.any(available & ~np.isfinite(values)):
            raise ValueError(f"Available geometry has no finite value: {metric}")
        for label, index in (("start", 0), ("end", -1)):
            row[f"{label}_{metric}"] = values[index]
            row[f"{label}_{metric}_status"] = getattr(states[index], f"{metric}_status")
        both = available[0] and available[-1]
        row[f"net_{metric}"] = values[-1] - values[0] if both else np.nan
        row[f"net_{metric}_status"] = "ok" if both else "both_endpoints_unavailable" if not available[0] and not available[-1] else "start_endpoint_unavailable" if not available[0] else "end_endpoint_unavailable"
        observed = values[available]
        row[f"observed_{metric}_count"] = len(observed)
        row[f"observed_{metric}_status"] = "complete" if available.all() else "partial_available_states" if len(observed) else "unavailable"
        for name, op in (("min", np.min), ("max", np.max), ("range", np.ptp)):
            row[f"observed_{metric}_{name}"] = op(observed) if len(observed) else np.nan
        if metric.endswith("centroid_x"):
            row[f"maximum_{metric}_advancement_from_start"] = max(0, observed.max() - values[0]) if available[0] else np.nan
            row[f"maximum_{metric}_reversal_from_start"] = max(0, values[0] - observed.min()) if available[0] else np.nan
        for i in range(1, 4):
            leg = legs[i - 1] if i <= length else None
            row[f"leg_{i}_delta_{metric}"] = getattr(leg, f"delta_{metric}") if leg else np.nan
            row[f"leg_{i}_delta_{metric}_status"] = getattr(leg, f"delta_{metric}_status") if leg else "not_applicable"
            if leg and available[i - 1] and available[i]:
                if row[f"leg_{i}_delta_{metric}_status"] != "ok" or not np.isclose(row[f"leg_{i}_delta_{metric}"], values[i] - values[i - 1], atol=1e-9, rtol=0):
                    raise ValueError("Frozen per-leg delta disagrees with its exact anchor endpoints")
    return row


def window_scope(data, scope):
    if scope == "all":
        return pd.Series(True, index=data.index)
    if scope in ("gap_le_5", "gap_le_3"):
        return data.maximum_leg_gap.le(int(scope[-1]))
    if scope == "terminal_leverkusen":
        return data.terminal_event_team_id.eq(TEAM_ID)
    if scope in ("exclude_oob", "exclude_coincidence"):
        flag = "oob" if scope == "exclude_oob" else "coincident"
        return ~data[f"any_frame_{flag}"] & ~data[f"any_frame_{flag}_unknown"]
    raise ValueError(f"Unknown window scope: {scope}")

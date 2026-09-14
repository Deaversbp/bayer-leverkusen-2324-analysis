"""Exact attachment and partial-observation sequences; no new football boundaries."""

import numpy as np
import pandas as pd

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.sequences.readiness import match_event_inventory
from leverkusen.spatial.calibration import (
    candidate_definitions, eligibility, prepare, resolve_rule,
)
from leverkusen.spatial.geometry import METRICS
from leverkusen.spatial.orientation import (
    VALIDATED, normalize_attacking_point, point_team_label,
)

EVENT = ["match_id", "event_id"]
SPELL = ["match_id", "attacking_control_spell_id"]
PARENT = ["match_id", "period", "provider_possession_id", "possession_team_id"]
SIDES = ("all", "lev", "opp")
SUPPORT = (
    "goalkeeper_policy", "n_valid_points_used", "n_unique_points",
    "n_coincident_records", "n_out_of_bounds_points", "measurement_flags",
    "n_keeper_true_before_filter", "n_keeper_unknown_before_filter",
    "n_keeper_true_excluded", "n_keeper_unknown_excluded", "hull_error_category",
)
FRAME_SUPPORT = (
    "frame_index", "actor_status", "actor_count", "event_join_status",
    "frame_oob", "frame_coincident", "frame_oob_unknown", "frame_coincident_unknown",
    "visible_area_status", "visible_area_fraction", "visible_area_polygon_area",
    "visible_area_on_pitch_area", "visible_area_outside_pitch", "freeze_frame_status",
    "total_visible_players", "n_invalid_locations", "n_unknown_teammate",
    "n_unknown_actor_flags", "n_non_dictionary_records",
)


def require_revision(values):
    values = pd.Series(values, dtype="string")
    if values.empty or values.isna().any() or not values.eq(STATSBOMB_REVISION).all():
        raise ValueError("Source revision reconciliation failed")


def event_context(match, events, frames, *, source_revision):
    """Reuse the complete-match Phase 2C audit, exporting only outcome-free context.

    Strip outcome-bearing payloads before the shared inventory validator sees them.
    Explicit provider related-event edges in the COMPLETE match still drive semantics.
    """
    require_revision([source_revision])
    fields = ("id", "index", "period", "timestamp", "possession", "possession_team",
              "team", "type", "location", "related_events")
    safe = [{k: e[k] for k in fields if k in e} for e in events]
    table = match_event_inventory(match, safe, frames, source_revision=source_revision)
    table = table.drop(columns=["is_shot", "is_goal"])
    raw = {e["index"]: e for e in safe}
    table["event_id"] = [raw[i]["id"] for i in table.event_index]
    table["source_order"] = table.event_id.map({e["id"]: i for i, e in enumerate(safe)})
    if not table.source_order.is_monotonic_increasing:
        raise ValueError("Provider indices disagree with source order")
    for output, key in (("event_team", "team"), ("possession_team", "possession_team")):
        table[output] = [field(raw[i], key, "name") for i in table.event_index]
    table["home_team_id"] = field(match, "home_team", "home_team_id")
    table["away_team_id"] = field(match, "away_team", "away_team_id")
    table["statsbomb_revision"] = source_revision
    return table[table.possession_team_id.eq(TEAM_ID)].rename(
        columns={"possession_id": "provider_possession_id"}
    ).reset_index(drop=True)


def attach_membership(membership, canonical):
    """Hydrate absent UUIDs by exact provider index, checking every context field.

    Index equality identifies a canonical record, never a nearby event. All later
    joins use match + UUID. Missing, extra, duplicate or changed identities fail.
    """
    require_revision(canonical.statsbomb_revision)
    key = ["match_id", "event_index"]
    check = ["period", "provider_possession_id", "possession_team_id", "timestamp",
             "period_seconds", "event_type", "event_team"]
    if "event_id" in membership:
        check.append("event_id")
    joined = membership.merge(canonical, on=key, how="outer", validate="one_to_one",
                              suffixes=("_membership", ""), indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Exact event-to-spell join has missing or extra events")
    for col in check:
        left, right = joined[f"{col}_membership"], joined[col]
        # CSV decimal parsing can differ by one floating-point rounding unit.
        equal = np.isclose(left, right, rtol=0, atol=1e-9) if col == "period_seconds" else left.eq(right)
        if not np.all(equal):
            raise ValueError(f"Exact event-to-spell context mismatch: {col}")
    joined = joined.drop(columns=["_merge", *[f"{c}_membership" for c in check]])
    if joined[EVENT].isna().any().any() or joined.duplicated(EVENT).any():
        raise ValueError("Ambiguous exact event identity")
    return joined.sort_values(["match_id", "source_order"]).reset_index(drop=True)


def attach_geometry(anchors, geometry):
    """Reuse Phase 2B values/status/eligibility; normalize only centroid location.

    Width, depth, area and distances are invariant under the approved rotation.
    Literal variants map through Phase 2C's point_team_label, not a new team rule.
    """
    require_revision(anchors.statsbomb_revision)
    if not anchors.semantics_status.eq(VALIDATED).all():
        raise ValueError("Only trusted anchors may receive normalized geometry")
    geometry = prepare(geometry)
    if geometry.duplicated([*EVENT, "selected_subset", "goalkeeper_policy"]).any():
        raise ValueError("Ambiguous geometry event identity")
    joined = anchors.merge(geometry, on=EVENT, how="left", validate="one_to_many",
                           suffixes=("", "_geometry"))
    if joined.frame_index.isna().any() or len(joined) != 6 * len(anchors):
        raise ValueError("Missing exact geometry variants for trusted anchor")
    if not joined.event_type.eq(joined.event_type_geometry).all():
        raise ValueError("Geometry event type mismatch")
    primary = next(c for c in candidate_definitions() if c.candidate == "D_primary")
    for metric in METRICS:
        rule = resolve_rule(primary, metric, ("all_visible", "excluded"), pd.DataFrame())
        joined[f"{metric}_available"] = eligibility(joined, metric, rule)
    side_map = {}
    for team, home, away in anchors[["event_team_id", "home_team_id", "away_team_id"]].drop_duplicates().itertuples(index=False, name=None):
        for subset, flag in (("teammate_true", True), ("teammate_false", False)):
            mapped = point_team_label(flag, team, (home, away), semantics_status=VALIDATED)
            side_map[(team, home, away, subset)] = {"leverkusen": "lev", "opponent": "opp"}[mapped["frame_player_side"]]
    joined["side"] = [
        "all" if r.selected_subset == "all_visible" else
        side_map[(r.event_team_id, r.home_team_id, r.away_team_id, r.selected_subset)]
        for r in joined.itertuples(index=False)
    ]
    result = anchors.copy()
    result["anchor_role"] = np.where(result.event_team_id.eq(TEAM_ID), "leverkusen_action", "opponent_context")
    result["is_leverkusen_event"] = result.event_team_id.eq(TEAM_ID)
    result["is_ball_progression_action"] = result.is_leverkusen_event & result.event_type.isin(["Pass", "Carry"])
    result["orientation_status"] = [normalize_attacking_point(
        (0, 0), reference_team_id=r.event_team_id, target_team_id=TEAM_ID,
        match_team_ids=(r.home_team_id, r.away_team_id), semantics_status=r.semantics_status,
    )["orientation_status"] for r in result.itertuples(index=False)]
    result["orientation_basis"] = "validated_event_team_reference; target_team_attacks_increasing_x"
    common = joined[joined.side.eq("all") & joined.goalkeeper_policy.eq("included")]
    result = result.merge(common[[*EVENT, *FRAME_SUPPORT]], on=EVENT, validate="one_to_one")
    for side in SIDES:
        selected = joined[joined.side.eq(side) & joined.goalkeeper_policy.eq("excluded")].copy()
        normalized = [normalize_attacking_point(
            (r.centroid_x, r.centroid_y), reference_team_id=r.event_team_id,
            target_team_id=TEAM_ID, match_team_ids=(r.home_team_id, r.away_team_id),
            semantics_status=r.semantics_status,
        ) for r in selected.itertuples(index=False)]
        selected["centroid_x"] = [r["x_attacking"] for r in normalized]
        selected["centroid_y"] = [r["y_attacking"] for r in normalized]
        cols = [*SUPPORT, "selected_subset", *METRICS,
                *[f"{m}_{suffix}" for m in METRICS for suffix in ("status", "available")]]
        result = result.merge(selected[[*EVENT, *cols]].rename(
            columns={c: f"{side}_{c}" for c in cols}), on=EVENT, validate="one_to_one")
        included = joined[joined.side.eq(side) & joined.goalkeeper_policy.eq("included")]
        result = result.merge(included[[*EVENT, "visible_player_count", "visible_player_count_status"]].rename(
            columns={c: f"{side}_{c}_keeper_included" for c in ("visible_player_count", "visible_player_count_status")}),
            on=EVENT, validate="one_to_one")
    return result.sort_values(["match_id", "source_order"]).reset_index(drop=True)


def construct_sequences(context, geometry):
    """Return ordered states and consecutive within-spell observational deltas."""
    members = context[context.attacking_control_spell_id.notna()].copy()
    if members.groupby(SPELL)[["period", "provider_possession_id"]].nunique().gt(1).any().any():
        raise ValueError("A spell crosses a period or provider parent")
    members = members.sort_values(["match_id", "source_order"])
    groups = members.groupby(SPELL, sort=False)
    members["events_from_spell_start"] = groups.cumcount()
    if not members.spell_event_order.eq(members.events_from_spell_start + 1).all():
        raise ValueError("Noncontiguous or changed spell event order")
    members["seconds_from_spell_start"] = members.period_seconds - groups.period_seconds.transform("first")
    if groups.period_seconds.diff().dropna().lt(0).any():
        raise ValueError("Nonmonotonic spell timestamps")
    anchors = attach_geometry(members[members.semantics_status.eq(VALIDATED)], geometry)
    groups = anchors.groupby(SPELL, sort=False)
    anchors["spatial_anchor_order"] = groups.cumcount() + 1
    anchors["previous_spatial_anchor_event_id"] = groups.event_id.shift(1)
    anchors["next_spatial_anchor_event_id"] = groups.event_id.shift(-1)
    anchors["seconds_from_previous_anchor"] = groups.period_seconds.diff()
    anchors["events_from_previous_anchor"] = groups.source_order.diff()
    anchors["intervening_event_count"] = anchors.events_from_previous_anchor - 1
    return anchors, construct_transitions(anchors)


def construct_transitions(anchors):
    groups = anchors.groupby(SPELL, sort=False)
    has_previous = anchors.spatial_anchor_order.gt(1)
    columns = {c: anchors[c] for c in [*PARENT, "attacking_control_spell_id", "statsbomb_revision"]}
    for col in ("event_id", "event_index", "source_order", "spatial_anchor_order", "event_type",
                "event_team_id", "timestamp", "period_seconds", "anchor_role", "orientation_status",
                *FRAME_SUPPORT, *[f"{s}_{c}" for s in SIDES for c in SUPPORT]):
        columns[f"from_{col}"] = groups[col].shift(1)
        columns[f"to_{col}"] = anchors[col]
    for col in ("seconds_from_previous_anchor", "events_from_previous_anchor", "intervening_event_count"):
        columns[col] = anchors[col]
    for side in SIDES:
        for metric in METRICS:
            name = f"{side}_{metric}"
            previous_value = groups[name].shift(1)
            previous_ok = groups[f"{name}_available"].shift(1).eq(True)
            current_ok = anchors[f"{name}_available"].eq(True)
            both = previous_ok & current_ok & previous_value.notna() & anchors[name].notna()
            columns[f"delta_{name}"] = (anchors[name] - previous_value).where(both)
            columns[f"delta_{name}_status"] = pd.Series(np.select(
                [both, ~previous_ok & ~current_ok, ~previous_ok, ~current_ok],
                ["ok", "both_endpoints_unavailable", "from_endpoint_unavailable", "to_endpoint_unavailable"],
                default="endpoint_value_missing"), index=anchors.index)
            for suffix in ("status", "available"):
                columns[f"from_{name}_{suffix}"] = groups[f"{name}_{suffix}"].shift(1)
                columns[f"to_{name}_{suffix}"] = anchors[f"{name}_{suffix}"]
    return pd.DataFrame(columns).loc[has_previous].reset_index(drop=True)


def spell_readiness(context, anchors, summary):
    require_revision(summary.statsbomb_revision)
    if summary.duplicated(SPELL).any():
        raise ValueError("Duplicate spell summary")
    members = context[context.attacking_control_spell_id.notna()]
    counts = members.groupby(SPELL).size()
    expected = summary.set_index(SPELL).event_count.sort_index()
    if not counts.sort_index().equals(expected):
        raise ValueError("Spell summary membership count mismatch")
    grouped = {key: group for key, group in anchors.groupby(SPELL)}
    rows = []
    for s in summary.sort_values(["match_id", "start_event"]).itertuples(index=False):
        a = grouped.get((s.match_id, s.attacking_control_spell_id), anchors.iloc[:0])
        gap = a.seconds_from_previous_anchor.dropna()
        n = len(a)
        row = {c: getattr(s, c) for c in [*PARENT, "attacking_control_spell_id", "event_count", "duration_seconds", "start_event", "end_event", "statsbomb_revision"]}
        row.update(trusted_anchor_count=n, leverkusen_anchor_count=int(a.event_team_id.eq(TEAM_ID).sum()),
                   opponent_anchor_count=int(a.event_team_id.ne(TEAM_ID).sum()), transition_count=max(n - 1, 0),
                   anchor_proportion=n / s.event_count, median_anchor_gap=gap.median(),
                   p90_anchor_gap=gap.quantile(.9), max_anchor_gap=gap.max())
        for label, condition in (("0", n == 0), ("1", n == 1), ("2", n == 2), ("3_plus", n >= 3), ("5_plus", n >= 5)):
            row[f"has_{label}_anchors"] = condition
        for typ in ("Pass", "Carry", "Pressure", "Shot"):
            row[f"anchor_count_{typ.lower()}"] = int(a.event_type.eq(typ).sum())
        for endpoint, index in (("first", 0), ("last", -1)):
            for col in ("event_id", "events_from_spell_start", "seconds_from_spell_start"):
                row[f"{endpoint}_anchor_{col}"] = a.iloc[index][col] if n else None
        for side in SIDES:
            for metric in METRICS:
                row[f"{side}_{metric}_available_count"] = int(a[f"{side}_{metric}_available"].sum())
        rows.append(row)
    return pd.DataFrame(rows)

"""Phase 2C pinned, in-memory schema and semantic evidence; no coordinate repair."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data import loader
from leverkusen.data.observability import coordinate_diagnostics
from leverkusen.spatial.geometry import valid_point

TEAM_ID = 904
CORE_TYPES = ("Shot", "Pass", "Carry", "Pressure")
DIFFICULT_TYPES = (
    "Dribbled Past",
    "Dispossessed",
    "Foul Won",
    "Duel",
    "50/50",
    "Ball Receipt*",
    "Dribble",
)


def field(record, name, child="id"):
    value = record.get(name)
    return value.get(child) if isinstance(value, dict) else None


def team_context(event, match):
    ids = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )
    event_id, possession_id = field(event, "team"), field(event, "possession_team")
    valid_match = None not in ids and ids[0] != ids[1] and TEAM_ID in ids
    agreement = (
        "missing_both"
        if event_id is None and possession_id is None
        else "missing_event_team"
        if event_id is None
        else "missing_possession_team"
        if possession_id is None
        else "invalid_match_team"
        if not valid_match or event_id not in ids or possession_id not in ids
        else "same"
        if event_id == possession_id
        else "different"
    )
    return {
        "event_team_id": event_id,
        "event_team_name": field(event, "team", "name"),
        "possession_team_id": possession_id,
        "possession_team_name": field(event, "possession_team", "name"),
        "event_team_is_leverkusen": event_id == TEAM_ID
        if valid_match and event_id in ids
        else None,
        "possession_team_is_leverkusen": possession_id == TEAM_ID
        if valid_match and possession_id in ids
        else None,
        "event_team_valid": valid_match and event_id in ids,
        "team_agreement": agreement,
        "leverkusen_home": ids[0] == TEAM_ID,
        "attacking_context": "ambiguous_possession_context"
        if agreement not in ("same", "different")
        else "opponent_event_in_leverkusen_possession"
        if possession_id == TEAM_ID and event_id in ids and event_id != TEAM_ID
        else "leverkusen_event_in_leverkusen_possession"
        if possession_id == TEAM_ID and event_id == TEAM_ID
        else "leverkusen_event_in_opponent_possession"
        if event_id == TEAM_ID
        else "opponent_possession_context",
    }


def codec_alignment(event_location, actor_location):
    """Exact supplied or float32 encoding equality, NOT a distance tolerance.

    This tests a provider encoding fingerprint; it neither rounds measurements
    nor establishes identity. Neither direct-vs-mirrored distance rank is a gate.
    """
    a, b = valid_point(event_location), valid_point(actor_location)
    if a is None or b is None:
        return "unavailable"
    if a == b:
        return "exact_supplied"
    with np.errstate(over="ignore"):
        encoded = tuple(float(v) for v in np.asarray(a, dtype=np.float32))
    return "exact_float32" if encoded == b else "not_exact"


def points(frame):
    if not isinstance(frame.get("freeze_frame"), list):
        return []
    return [
        p
        for p in frame.get("freeze_frame", [])
        if isinstance(p, dict) and valid_point(p.get("location")) is not None
    ]


def cloud(frame):
    return Counter((tuple(p["location"]), p.get("keeper")) for p in points(frame))


def labeled_cloud(frame, opposite=False):
    return Counter(
        (
            tuple(p["location"]),
            p.get("keeper"),
            not p["teammate"]
            if opposite and type(p.get("teammate")) is bool
            else p.get("teammate"),
        )
        for p in points(frame)
    )


def related_evidence(event, frame, events_by_id, frames_by_id):
    """Directed provider related-event edges; no temporal/sequence matching."""
    rows = []
    for identifier in sorted(set(event.get("related_events", []))):
        other = events_by_id.get(identifier)
        if other is None:
            continue
        other_frame = frames_by_id.get(identifier)
        same = field(event, "team") == field(other, "team")
        equal_cloud = bool(
            other_frame and cloud(frame) and cloud(frame) == cloud(other_frame)
        )
        expected = equal_cloud and labeled_cloud(frame) == labeled_cloud(
            other_frame, opposite=not same
        )
        rows.append(
            {
                "event_id": event["id"],
                "related_event_id": identifier,
                "event_type": field(event, "type", "name"),
                "actor_codec": actor_codec(event, frame),
                "related_event_type": field(other, "type", "name"),
                "same_event_team": same,
                "related_has_frame": other_frame is not None,
                "equal_native_cloud": equal_cloud,
                "expected_team_labels_agree": expected,
                "equal_cloud_team_label_conflict": equal_cloud and not expected,
                "related_actor_codec": actor_codec(other, other_frame)
                if other_frame
                else "unavailable",
            }
        )
    return rows


def actor_codec(event, frame):
    actors = [p for p in points(frame) if p.get("actor") is True]
    return (
        codec_alignment(event.get("location"), actors[0].get("location"))
        if len(actors) == 1
        else "unavailable"
    )


def related_conflict_ids(edges_by_id):
    """Quarantine both endpoints, even if a provider edge is not reciprocal."""
    return {
        edge[key]
        for edges in edges_by_id.values()
        for edge in edges
        if edge["equal_cloud_team_label_conflict"]
        for key in ("event_id", "related_event_id")
    }


def inspect_event(event, frame, match, lineup_ids):
    ps = points(frame)
    actors = [p for p in ps if p.get("actor") is True]
    raw = frame.get("freeze_frame")
    actor_status = (
        "multiple"
        if len(actors) > 1
        else "unknown"
        if not isinstance(raw, list)
        or len(ps) != len(raw)
        or any(type(p.get("actor")) is not bool for p in ps)
        else "single"
        if len(actors) == 1
        else "none"
    )
    typ = field(event, "type", "name")
    start = valid_point(event.get("location"))
    nested = event.get({"Goal Keeper": "goalkeeper"}.get(typ, str(typ).lower()), {})
    end_raw = nested.get("end_location") if isinstance(nested, dict) else None
    end = (
        valid_point(end_raw[:2])
        if isinstance(end_raw, list) and len(end_raw) in (2, 3)
        else None
    )
    row = {
        "event_id": event["id"],
        "event_type": typ,
        "period": event.get("period"),
        "event_index": event.get("index"),
        **team_context(event, match),
        "actor_status": actor_status,
        "actor_records": len(actors),
        "actor_teammate_true": sum(p.get("teammate") is True for p in actors),
        "actor_teammate_false": sum(p.get("teammate") is False for p in actors),
        "unknown_teammate_records": sum(
            type(p.get("teammate")) is not bool for p in ps
        ),
        "point_records": len(ps),
        "teammate_true_records": sum(p.get("teammate") is True for p in ps),
        "teammate_false_records": sum(p.get("teammate") is False for p in ps),
        "invalid_point_records": len(raw) - len(ps) if isinstance(raw, list) else None,
        "actor_codec": actor_codec(event, frame),
        "event_player_in_event_team_lineup": field(event, "player")
        in lineup_ids.get(field(event, "team"), set())
        if field(event, "player") is not None
        else None,
        "start_x": start[0] if start else None,
        "start_y": start[1] if start else None,
        "end_x": end[0] if end else None,
        "end_y": end[1] if end else None,
        "delta_x": end[0] - start[0] if start and end else None,
        "pass_type": field(nested, "type", "name") if typ == "Pass" else None,
        "is_normal_pass": typ == "Pass" and field(nested, "type") is None,
        **coordinate_diagnostics(
            event.get("location"), actors[0]["location"] if len(actors) == 1 else None
        ),
    }
    for team in (True, False):
        xs = [
            p["location"][0]
            for p in ps
            if p.get("keeper") is True and p.get("teammate") is team
        ]
        row[f"keeper_{str(team).lower()}_count"] = len(xs)
        row[f"keeper_{str(team).lower()}_mean_x"] = float(np.mean(xs)) if xs else None
    return row


def shot_checks(event, frame, lineup_ids):
    """Nearest 360 point to independently named shot-FF observations; no identities assigned."""
    rows = []
    ps = points(frame)
    if not ps:
        return rows
    for record in event.get("shot", {}).get("freeze_frame", []):
        p = valid_point(record.get("location"))
        if p is None or type(record.get("teammate")) is not bool:
            continue
        ds = [
            float(np.hypot(p[0] - q["location"][0], p[1] - q["location"][1]))
            for q in ps
        ]
        nearest = [q for q, d in zip(ps, ds) if d == min(ds)]
        expected_id = (
            field(event, "team")
            if record["teammate"]
            else next((i for i in lineup_ids if i != field(event, "team")), None)
        )
        rows.append(
            {
                "nearest_distance": min(ds),
                "unique_nearest": len(nearest) == 1,
                "all_nearest_team_flags_agree": all(
                    q.get("teammate") is record["teammate"] for q in nearest
                ),
                "named_shot_record_in_expected_lineup": field(record, "player")
                in lineup_ids.get(expected_id, set()),
            }
        )
    return rows


def describe(values):
    v = pd.Series(values).dropna()
    return {
        "defined": len(v),
        "mean": v.mean() if len(v) else None,
        "min": v.min() if len(v) else None,
        "max": v.max() if len(v) else None,
        **{
            f"p{q:02}": v.quantile(q / 100) if len(v) else None
            for q in (5, 25, 50, 75, 95)
        },
    }


def summarize(table, pairs, shots, anchors):
    results = {}
    results["event_vs_possession_team"] = (
        table.groupby(["event_type", "team_agreement"], dropna=False)
        .size()
        .rename("frames")
        .reset_index()
    )
    results["attacking_context"] = (
        table.groupby(["event_type", "attacking_context"], dropna=False)
        .size()
        .rename("frames")
        .reset_index()
    )
    rows = []
    for typ, g in table.groupby("event_type"):
        comparable = g.actor_distance_direct.notna() & g.actor_distance_mirrored.notna()
        rows.append(
            {
                "event_type": typ,
                "frame_count": len(g),
                "matches": g.match_id.nunique(),
                "event_team_possession_team_agreement_rate": g.team_agreement.eq(
                    "same"
                ).mean(),
                "actor_coordinate_denominator": int(comparable.sum()),
                "actor_coordinate_direct_rate": g.loc[
                    comparable, "coordinate_comparison"
                ]
                .eq("direct_closer")
                .mean(),
                "actor_coordinate_mirrored_rate": g.loc[
                    comparable, "coordinate_comparison"
                ]
                .eq("mirrored_closer")
                .mean(),
                "actor_codec_exact_frames": g.actor_codec.isin(
                    ["exact_supplied", "exact_float32"]
                ).sum(),
                "actor_records": g.actor_records.sum(),
                "actor_teammate_true": g.actor_teammate_true.sum(),
                "actor_teammate_false": g.actor_teammate_false.sum(),
                "unknown_teammate_records": g.unknown_teammate_records.sum(),
                "point_records": g.point_records.sum(),
                "lineup_checked_events": g.event_player_in_event_team_lineup.notna().sum(),
                "lineup_membership_failures": g.event_player_in_event_team_lineup.eq(
                    False
                ).sum(),
                "direct_distance_median": g.actor_distance_direct.median(),
                "direct_distance_p95": g.actor_distance_direct.quantile(0.95),
                "mirrored_distance_median": g.actor_distance_mirrored.median(),
                "mirrored_distance_p95": g.actor_distance_mirrored.quantile(0.95),
                "equal_cloud_conflicting_frames": g.paired_label_conflict.sum(),
            }
        )
    results["team_semantics_summary"] = pd.DataFrame(rows)
    results["paired_event_evidence"] = (
        pairs.groupby(
            [
                "event_type",
                "related_event_type",
                "same_event_team",
                "actor_codec",
                "related_actor_codec",
            ],
            dropna=False,
        )
        .agg(
            directed_edges=("equal_native_cloud", "size"),
            equal_native_cloud=("equal_native_cloud", "sum"),
            expected_team_labels_agree=("expected_team_labels_agree", "sum"),
            equal_cloud_team_label_conflict=("equal_cloud_team_label_conflict", "sum"),
        )
        .reset_index()
    )
    rows = []
    for scope, g in [("all_shot_ff_records", shots)]:
        rows.append(
            {
                "scope": scope,
                **describe(g.nearest_distance),
                "unique_nearest": g.unique_nearest.sum(),
                "nearest_team_agreement": g.all_nearest_team_flags_agree.sum(),
                "shot_lineup_agreement": g.named_shot_record_in_expected_lineup.sum(),
            }
        )
    results["shot_team_crosscheck"] = pd.DataFrame(rows)
    rows = []
    for keys, g in anchors.groupby(
        [
            "scope",
            "match_id",
            "event_team_id",
            "event_team_is_leverkusen",
            "period",
            "event_type",
        ],
        dropna=False,
    ):
        if keys[-1] not in (*CORE_TYPES, "Goal Keeper"):
            continue
        for metric in (
            "start_x",
            "end_x",
            "delta_x",
            "keeper_true_mean_x",
            "keeper_false_mean_x",
        ):
            rows.append(
                {
                    **dict(
                        zip(
                            [
                                "scope",
                                "match_id",
                                "event_team_id",
                                "event_team_is_leverkusen",
                                "period",
                                "event_type",
                            ],
                            keys,
                        )
                    ),
                    "metric": metric,
                    "events": len(g),
                    **describe(g[metric]),
                    "above_midfield": int(g[metric].gt(60).sum())
                    if metric in ("start_x", "end_x")
                    else None,
                    "at_x120": int(g[metric].eq(120).sum())
                    if metric == "end_x"
                    else None,
                }
            )
    results["orientation_by_team_period"] = pd.DataFrame(rows)
    rows = []
    for keys, g in anchors.groupby(
        ["scope", "event_type", "team_agreement", "is_normal_pass"], dropna=False
    ):
        for metric in (
            "start_x",
            "end_x",
            "delta_x",
            "keeper_true_mean_x",
            "keeper_false_mean_x",
        ):
            rows.append(
                {
                    **dict(
                        zip(
                            ["scope", "event_type", "team_agreement", "is_normal_pass"],
                            keys,
                        )
                    ),
                    "metric": metric,
                    "events": len(g),
                    **describe(g[metric]),
                    "positive_dx": int(g.delta_x.gt(0).sum()),
                    "negative_dx": int(g.delta_x.lt(0).sum()),
                }
            )
    results["orientation_anchor_summary"] = pd.DataFrame(rows)
    return results


def representative_rules(row):
    """Stable first match/frame for explicit strata; never an effectiveness selection."""
    rules = []
    if row["event_type"] in ("Shot", "Pass", "Carry") and row["period"] in (1, 2):
        rules.append(
            f"{row['event_type']}_{row['event_team_is_leverkusen']}_period{row['period']}"
        )
        if not row["leverkusen_home"] and row["event_type"] == "Pass":
            rules.append(
                f"away_Pass_{row['event_team_is_leverkusen']}_period{row['period']}"
            )
    if row["event_type"] in DIFFICULT_TYPES or row["event_type"] == "Pressure":
        rules.append(f"difficult_{row['event_type']}")
    if row["paired_label_conflict"]:
        rules.append("equal_cloud_team_label_conflict")
    if row["event_type"] in CORE_TYPES and row["actor_codec"] == "not_exact":
        rules.append(f"core_nonexact_{row['event_type']}")
    return rules


def semantic_decision_summaries(table, type_summary):
    """A deliberately restricted decision, separate from locked geometry eligibility."""
    from leverkusen.spatial.orientation import VALIDATED

    results = {}
    results["coordinate_alignment_context"] = (
        table.groupby(["event_type", "team_agreement", "actor_codec"], dropna=False)
        .agg(
            frames=("event_id", "size"),
            direct_closer=(
                "coordinate_comparison",
                lambda v: v.eq("direct_closer").sum(),
            ),
            mirrored_closer=(
                "coordinate_comparison",
                lambda v: v.eq("mirrored_closer").sum(),
            ),
            direct_distance_median=("actor_distance_direct", "median"),
            mirrored_distance_median=("actor_distance_mirrored", "median"),
        )
        .reset_index()
    )
    results["normalization_validation"] = (
        table.groupby(
            ["event_type", "semantics_status", "orientation_status"], dropna=False
        )
        .agg(
            frames=("event_id", "size"),
            point_records=("point_records", "sum"),
            locations_checked=("normalized_locations_checked", "sum"),
            max_roundtrip_absolute_error=("max_roundtrip_absolute_error", "max"),
        )
        .reset_index()
    )
    results["semantic_team_mapping"] = (
        table.groupby(
            ["event_type", "semantics_status", "event_team_is_leverkusen"], dropna=False
        )
        .agg(
            frames=("event_id", "size"),
            teammate_true_records=("teammate_true_records", "sum"),
            teammate_false_records=("teammate_false_records", "sum"),
        )
        .reset_index()
    )
    mapping = results["semantic_team_mapping"]
    mapping["mapped_leverkusen_points"] = mapping.apply(
        lambda r: (
            (
                r.teammate_true_records
                if r.event_team_is_leverkusen
                else r.teammate_false_records
            )
            if r.semantics_status == VALIDATED
            else None
        ),
        axis=1,
    )
    mapping["mapped_opponent_points"] = mapping.apply(
        lambda r: (
            (
                r.teammate_false_records
                if r.event_team_is_leverkusen
                else r.teammate_true_records
            )
            if r.semantics_status == VALIDATED
            else None
        ),
        axis=1,
    )
    classification = type_summary.copy()
    valid_counts = (
        table[table.semantics_status.eq(VALIDATED)].groupby("event_type").size()
    )
    classification["validated_scope_frames"] = (
        classification.event_type.map(valid_counts).fillna(0).astype(int)
    )
    classification["unsupported_frames"] = (
        classification.frame_count - classification.validated_scope_frames
    )
    paired_types = ("Dribbled Past", "Dispossessed", "Foul Won")
    classification["orientation_anchor_quality"] = classification.event_type.map(
        lambda t: (
            "safe_primary_anchor_conditional"
            if t == "Shot"
            else "supporting_anchor_conditional"
            if t in CORE_TYPES
            else "exclude_from_orientation_inference"
        )
    )
    classification["teammate_semantics_status"] = classification.event_type.map(
        lambda t: (
            "usable_with_event_team_semantics_conditional"
            if t in CORE_TYPES
            else "unresolved_for_operational_mapping"
        )
    )
    classification["coordinate_semantics_status"] = classification.event_type.map(
        lambda t: (
            "event_team_plus_x_conditional"
            if t in CORE_TYPES
            else "paired_or_opponent_referenced"
            if t in paired_types
            else "mixed_semantics"
            if t in DIFFICULT_TYPES
            else "exclude_from_orientation_inference"
        )
    )
    classification["later_sequence_use"] = (
        "not_implemented; phase3_method_design_authorized_for_validated_scope_only"
    )
    classification["notes"] = classification.event_type.map(
        lambda t: (
            "Only exact actor encoding, one actor, known flags, audited no related-cloud conflict; not whole event type"
            if t in CORE_TYPES
            else "Exact related clouds support reuse; no automatic rotation or identity inference"
            if t in paired_types
            else "Mixed direct/mirrored evidence; no operational normalization"
            if t in DIFFICULT_TYPES
            else "Descriptive audit only; not promoted from direct distance alone"
        )
    )
    results["event_semantics"] = classification
    return results


def run_semantic_diagnostics(output_dir, progress=print):
    """Fetch pinned events/360/lineups once per match; retain bounded raw examples only in RAM."""
    from leverkusen.spatial.orientation import frame_semantics, normalization_check

    output_dir = Path(output_dir)
    matches = sorted(
        [
            m
            for m in loader.load_matches()
            if TEAM_ID
            in (
                field(m, "home_team", "home_team_id"),
                field(m, "away_team", "away_team_id"),
            )
        ],
        key=lambda m: m["match_id"],
    )
    if len(matches) != 34:
        raise ValueError("Expected pinned 34-match season")
    rows, paired, shot_rows, anchors, inventory = [], [], [], [], []
    representatives = {}
    for done, match in enumerate(matches, 1):
        mid = match["match_id"]
        events = loader.load_events(mid)
        frames = loader.load_360(mid)
        lineups = loader.load_lineups(mid)
        if len({e["id"] for e in events}) != len(events) or len(
            {f["event_uuid"] for f in frames}
        ) != len(frames):
            raise ValueError("Ambiguous event/frame join")
        by_id = {e["id"]: e for e in events}
        by_frame = {f["event_uuid"]: f for f in frames}
        if set(by_frame) - set(by_id):
            raise ValueError("Orphan frames")
        lineup_ids = {
            lineup["team_id"]: {p["player_id"] for p in lineup["lineup"]}
            for lineup in lineups
        }
        # Provider links need not be reciprocal: quarantine BOTH endpoints of
        # every observed equal-cloud contradiction, including incoming edges.
        edges_by_id = {
            identifier: related_evidence(by_id[identifier], frame, by_id, by_frame)
            for identifier, frame in by_frame.items()
        }
        conflict_ids = related_conflict_ids(edges_by_id)
        for ordinal, frame in enumerate(frames):
            event = by_id[frame["event_uuid"]]
            row = {
                "match_id": mid,
                "frame_index": ordinal,
                **inspect_event(event, frame, match, lineup_ids),
            }
            edges = edges_by_id[event["id"]]
            row["paired_label_conflict"] = event["id"] in conflict_ids
            row.update(
                frame_semantics(
                    event,
                    frame,
                    match,
                    source_revision=loader.STATSBOMB_REVISION,
                    related_team_conflict=row["paired_label_conflict"],
                )
            )
            row.update(
                normalization_check(event, frame, match, row["semantics_status"])
            )
            paired.extend({"match_id": mid, **r} for r in edges)
            rows.append(row)
            for rule in representative_rules(row):
                if rule not in representatives:
                    representatives[rule] = (frame, event, match, row)
            if row["event_type"] == "Shot":
                shot_rows.extend(shot_checks(event, frame, lineup_ids))
            if row["event_type"] in (*CORE_TYPES, "Goal Keeper"):
                anchors.append({"scope": "360_linked", **row})
        for event in events:
            if field(event, "type", "name") in (*CORE_TYPES, "Goal Keeper"):
                anchors.append(
                    {
                        "scope": "all_events",
                        "match_id": mid,
                        **inspect_event(event, {"freeze_frame": []}, match, lineup_ids),
                    }
                )
        inventory.append(
            {
                "match_id": mid,
                "events": len(events),
                "frames": len(frames),
                "lineup_teams": len(lineups),
            }
        )
        progress(f"Phase 2C {done}/34: {mid}; {len(frames)} linked frames")
    table = pd.DataFrame(rows)
    results = summarize(
        table, pd.DataFrame(paired), pd.DataFrame(shot_rows), pd.DataFrame(anchors)
    )
    results["match_inventory"] = pd.DataFrame(inventory)
    results.update(
        semantic_decision_summaries(table, results["team_semantics_summary"])
    )
    results["run_summary"] = pd.DataFrame(
        [
            {
                "frames": len(table),
                "events": sum(r["events"] for r in inventory),
                "matches": len(matches),
                "points": table.point_records.sum(),
                "actor_records": table.actor_records.sum(),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "raw_persisted": False,
            }
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, t in results.items():
        t["statsbomb_revision"] = loader.STATSBOMB_REVISION
        t.to_csv(output_dir / f"phase2c_{name}.csv", index=False)
    return table, representatives, results

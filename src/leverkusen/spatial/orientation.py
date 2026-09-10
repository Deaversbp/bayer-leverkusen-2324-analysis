"""Additional, fail-closed Phase 2C semantic coordinates; Phase 2A stays native.

Supported scope is deliberately narrower than provider documentation: four
anchor types with an exact actor encoding fingerprint and no linked-frame flag
contradiction. Unsupported events are never corrected by the closer hypothesis.
"""

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.data.semantic_diagnostics import (
    CORE_TYPES,
    TEAM_ID,
    actor_codec,
    field,
    points,
)
from leverkusen.spatial.geometry import valid_point

VALIDATED = "validated_core_event_team_scope"


def frame_semantics(event, frame, match, *, source_revision, related_team_conflict):
    """Return a scoped status; never infer orientation from closer distances.

    related_team_conflict must explicitly be False after checking incoming AND
    outgoing provider links in the complete match. None means not audited.
    Passing False is a caller evidence assertion, not an automatic validation.
    """
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )
    actor = [p for p in points(frame) if p.get("actor") is True]
    reason = (
        "unsupported_source_revision"
        if source_revision != STATSBOMB_REVISION
        else "invalid_event_frame_join"
        if not event.get("id") or event.get("id") != frame.get("event_uuid")
        else "invalid_match_team"
        if TEAM_ID not in teams
        or None in teams
        or teams[0] == teams[1]
        or field(event, "team") not in teams
        else "unsupported_event_type"
        if field(event, "type", "name") not in CORE_TYPES
        else "related_team_audit_unresolved"
        if type(related_team_conflict) is not bool
        else "related_team_label_conflict"
        if related_team_conflict
        else "actor_status_unresolved"
        if not isinstance(frame.get("freeze_frame"), list)
        or len(points(frame)) != len(frame["freeze_frame"])
        or any(type(p.get("actor")) is not bool for p in points(frame))
        or len(actor) != 1
        else "actor_team_flag_unresolved"
        if actor[0].get("teammate") is not True
        else "point_flags_unresolved"
        if any(
            type(p.get("teammate")) is not bool or type(p.get("keeper")) is not bool
            for p in points(frame)
        )
        else "actor_encoding_unresolved"
        if actor_codec(event, frame) not in ("exact_supplied", "exact_float32")
        else VALIDATED
    )
    return {
        "semantics_status": reason,
        "orientation_basis": "provider_event_team_plus_core_anchor_and_exact_actor_encoding"
        if reason == VALIDATED
        else "unsupported_no_guess",
        "orientation_reference_team_id": field(event, "team")
        if reason == VALIDATED
        else None,
    }


def point_team_label(teammate, event_team_id, match_team_ids, *, semantics_status):
    """Map a literal flag only in validated scope; never attach named identity."""
    unknown = {
        "frame_player_side": "unresolved",
        "is_leverkusen": None,
        "is_opponent": None,
        "team_id": None,
    }
    if (
        semantics_status != VALIDATED
        or type(teammate) is not bool
        or len(match_team_ids) != 2
        or len(set(match_team_ids)) != 2
        or None in match_team_ids
        or TEAM_ID not in match_team_ids
        or event_team_id not in match_team_ids
    ):
        return unknown
    team = (
        event_team_id
        if teammate
        else next(t for t in match_team_ids if t != event_team_id)
    )
    return {
        "frame_player_side": "leverkusen" if team == TEAM_ID else "opponent",
        "is_leverkusen": team == TEAM_ID,
        "is_opponent": team != TEAM_ID,
        "team_id": team,
    }


def normalize_attacking_point(
    location, *, reference_team_id, target_team_id, match_team_ids, semantics_status
):
    """Rotate both axes only when switching a validated event-team reference.

    The derivative -I has determinant +1; x-only reflection is never used.
    Neither period nor home/away enters the rule. Out-of-bounds values stay so.
    """
    p = valid_point(location)
    row = {
        "x_raw": p[0] if p else None,
        "y_raw": p[1] if p else None,
        "x_attacking": None,
        "y_attacking": None,
        "orientation_status": "unsupported",
        "orientation_basis": "unsupported_no_guess",
    }
    if p is None:
        row["orientation_status"] = "invalid_location"
        return row
    if (
        semantics_status != VALIDATED
        or len(match_team_ids) != 2
        or len(set(match_team_ids)) != 2
        or None in match_team_ids
        or reference_team_id not in match_team_ids
        or target_team_id not in match_team_ids
    ):
        return row
    same = reference_team_id == target_team_id
    row.update(
        x_attacking=p[0] if same else 120 - p[0],
        y_attacking=p[1] if same else 80 - p[1],
        orientation_status="identity_explicit" if same else "rotated_180",
        orientation_basis="validated_event_team_reference; target_team_attacks_increasing_x",
    )
    return row


def normalization_check(event, frame, match, semantics_status):
    """Compact arithmetic check on every valid supplied point, with no persistence."""
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )
    values = [p["location"] for p in points(frame)]
    start = valid_point(event.get("location"))
    if start:
        values.append(start)
    maximum = 0.0
    count = 0
    status = "unsupported"
    for p in values:
        row = normalize_attacking_point(
            p,
            reference_team_id=field(event, "team"),
            target_team_id=TEAM_ID,
            match_team_ids=teams,
            semantics_status=semantics_status,
        )
        status = row["orientation_status"]
        if status not in ("identity_explicit", "rotated_180"):
            continue
        count += 1
        x, y = row["x_attacking"], row["y_attacking"]
        recovered = (x, y) if status == "identity_explicit" else (120 - x, 80 - y)
        maximum = max(maximum, abs(p[0] - recovered[0]), abs(p[1] - recovered[1]))
    return {
        "orientation_status": status,
        "normalized_locations_checked": count,
        "max_roundtrip_absolute_error": maximum if count else None,
    }

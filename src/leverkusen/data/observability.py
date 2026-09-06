"""Event/360 coverage diagnostics without raw persistence or tactical inference.

Event and frame rows are counted independently: duplicates never multiply a join,
and unmatched rows are retained. Counts describe observations, not eligibility
under a calibrated research visibility threshold.
"""

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from math import hypot, isfinite
from numbers import Real
from pathlib import Path

import pandas as pd
import requests
from shapely.geometry import Polygon, box
from shapely.validation import explain_validity

from leverkusen.data import loader
from leverkusen.data.transforms import get_team_match_context


def _finite_number(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)


def _point(value: object) -> tuple[float, float] | None:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        if all(_finite_number(coordinate) for coordinate in value):
            return tuple(float(coordinate) for coordinate in value)
    return None


def _identifier(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def inspect_visible_area(
    visible_area: object, pitch_length: float = 120, pitch_width: float = 80
) -> dict:
    """Validate a flat x/y polygon and measure its intersection with the pitch.

    Missing means None/absent; an empty list is malformed. A numeric polygon can
    be structurally well-formed but topologically invalid. Invalid polygons are
    never repaired. Area is in squared coordinate units; coverage is clipped to
    the pitch, while the original polygon area is also retained.
    """
    if not all(_finite_number(v) and v > 0 for v in (pitch_length, pitch_width)):
        raise ValueError("Pitch dimensions must be positive finite numbers")
    is_sequence = isinstance(visible_area, (list, tuple))
    result = {
        "visible_area_exists": visible_area is not None,
        "visible_area_missing": visible_area is None,
        "visible_area_coordinate_count": len(visible_area) if is_sequence else None,
        "visible_area_vertex_count": None,
        "visible_area_malformed": False,
        "visible_area_valid": False,
        "visible_area_reason": "missing",
        "visible_area_polygon_area": None,
        "visible_area_on_pitch_area": None,
        "visible_area_fraction": None,
        "visible_area_outside_pitch": None,
    }
    if visible_area is None:
        return result
    if (
        not is_sequence
        or len(visible_area) < 6
        or len(visible_area) % 2
        or not all(_finite_number(value) for value in visible_area)
    ):
        result.update(
            visible_area_malformed=True, visible_area_reason="malformed coordinates"
        )
        return result
    points = list(zip(visible_area[::2], visible_area[1::2]))
    result["visible_area_vertex_count"] = len(points)
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 0:
        result["visible_area_reason"] = explain_validity(polygon)
        return result
    pitch = box(0, 0, pitch_length, pitch_width)
    on_pitch_area = polygon.intersection(pitch).area
    result.update(
        visible_area_valid=True,
        visible_area_reason="valid",
        visible_area_polygon_area=polygon.area,
        visible_area_on_pitch_area=on_pitch_area,
        visible_area_fraction=on_pitch_area / (pitch_length * pitch_width),
        visible_area_outside_pitch=not pitch.covers(polygon),
    )
    return result


def frame_observability(
    frame: dict,
    event: dict | None = None,
    *,
    pitch_length: float = 120,
    pitch_width: float = 80,
) -> dict:
    """Count raw frame flags and compare a single actor to a linked event point.

    True/False flags retain provider semantics; no attacker/defender assignment
    or coordinate reorientation is performed. Missing or malformed freeze-frame
    containers have unknown counts, whereas an observed empty list has zero.
    """
    freeze = frame.get("freeze_frame")
    valid_container = isinstance(freeze, list)
    players = [p for p in freeze if isinstance(p, dict)] if valid_container else []
    actors = [p for p in players if p.get("actor") is True]
    result = {
        "freeze_frame_missing": freeze is None,
        "freeze_frame_malformed": (
            (freeze is not None and not valid_container)
            or (valid_container and len(players) != len(freeze))
        ),
        "freeze_frame_empty": len(freeze) == 0 if valid_container else None,
        "visible_players": len(players) if valid_container else None,
        "invalid_player_records": len(freeze) - len(players)
        if valid_container
        else None,
        "teammate_true": sum(p.get("teammate") is True for p in players)
        if valid_container
        else None,
        "teammate_false": sum(p.get("teammate") is False for p in players)
        if valid_container
        else None,
        "teammate_unknown": sum(type(p.get("teammate")) is not bool for p in players)
        if valid_container
        else None,
        "keepers": sum(p.get("keeper") is True for p in players)
        if valid_container
        else None,
        "actors": len(actors) if valid_container else None,
        "valid_player_locations": sum(
            _point(p.get("location")) is not None for p in players
        )
        if valid_container
        else None,
        "actor_distance": None,
        "actor_consistency_measurable": False,
    }
    actor_location = _point(actors[0].get("location")) if len(actors) == 1 else None
    event_location = _point(event.get("location")) if event is not None else None
    if not valid_container:
        reason = "freeze_frame unavailable"
    elif len(actors) != 1:
        reason = "actor count is not one"
    elif actor_location is None:
        reason = "actor location unavailable or invalid"
    elif event is None:
        reason = "event link missing or ambiguous"
    elif event_location is None:
        reason = "event location unavailable or invalid"
    else:
        reason = "measurable"
        result["actor_consistency_measurable"] = True
        result["actor_distance"] = hypot(
            actor_location[0] - event_location[0], actor_location[1] - event_location[1]
        )
    result["actor_consistency_reason"] = reason
    result.update(
        inspect_visible_area(frame.get("visible_area"), pitch_length, pitch_width)
    )
    return result


def summarize_actor_distances(frames: pd.DataFrame) -> dict:
    """Return measured actor-distance statistics in unmodified coordinate units."""
    distances = pd.to_numeric(frames["actor_distance"], errors="coerce").dropna()
    result = {"actor_distance_count": len(distances)}
    for name in ("mean", "median", "max"):
        result[f"actor_distance_{name}"] = (
            getattr(distances, name)() if len(distances) else None
        )
    for quantile in (0.25, 0.75, 0.90, 0.95, 0.99):
        result[f"actor_distance_q{int(100 * quantile)}"] = (
            distances.quantile(quantile) if len(distances) else None
        )
    return result


def _event_metadata(
    event: dict | None, team_name: str, opponent: str, missing: str
) -> dict:
    def name(field):
        value = event.get(field) if event else None
        label = value.get("name") if isinstance(value, dict) else None
        return label if isinstance(label, str) and label.strip() else "<missing>"

    event_team = name("team") if event is not None else missing
    team_group = "Unknown"
    if event_team == team_name:
        team_group = "Leverkusen"
    elif event_team == opponent:
        team_group = "Opponent"
    return {
        "event_index": event.get("index") if event else None,
        "event_type": name("type") if event is not None else missing,
        "event_team": event_team,
        "event_team_group": team_group,
    }


def audit_match(
    match: dict,
    events: list[dict],
    frames: list[dict] | None,
    *,
    team_name: str = "Bayer Leverkusen",
    pitch_length: float = 120,
    pitch_width: float = 80,
    load_status: str = "loaded",
    load_error: str | None = None,
) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Audit one match, returning inventory, one row/frame and one row/event.

    Duplicate counts mean excess records beyond the first; separate group counts
    give the number of duplicated identifiers. Missing IDs never match each other.
    A duplicated event ID makes frame metadata/actor comparisons ambiguous. All
    duplicate frames remain in the output with their original ordinal.
    """
    if (frames is None) != (load_status != "loaded"):
        raise ValueError("frames must be None exactly when 360 did not load")
    match_id = match["match_id"]
    opponent, venue = get_team_match_context(match, team_name)
    event_counts = Counter(_identifier(e.get("id")) for e in events)
    frame_counts = Counter(_identifier(f.get("event_uuid")) for f in (frames or []))
    unique_events = {
        e["id"]: e
        for e in events
        if _identifier(e.get("id")) is not None and event_counts[e["id"]] == 1
    }
    event_rows = []
    for ordinal, event in enumerate(events):
        identifier = _identifier(event.get("id"))
        event_rows.append(
            {
                "match_id": match_id,
                "event_ordinal": ordinal,
                "event_id": identifier,
                **_event_metadata(event, team_name, opponent, "<missing>"),
                "has_360_frame": identifier is not None
                and frame_counts[identifier] > 0,
                "frames_load_status": load_status,
            }
        )
    event_table = pd.DataFrame(
        event_rows,
        columns=[
            "match_id",
            "event_ordinal",
            "event_id",
            "event_index",
            "event_type",
            "event_team",
            "event_team_group",
            "has_360_frame",
            "frames_load_status",
        ],
    )
    frame_rows = []
    for ordinal, frame in enumerate(frames or []):
        identifier = _identifier(frame.get("event_uuid"))
        event_count = event_counts[identifier] if identifier is not None else 0
        event = unique_events.get(identifier)
        frame_rows.append(
            {
                "match_id": match_id,
                "frame_ordinal": ordinal,
                "event_id": identifier,
                "matching_event_records": event_count,
                "frame_uuid_records": frame_counts[identifier]
                if identifier is not None
                else 0,
                "event_link_status": "unique"
                if event_count == 1
                else "ambiguous"
                if event_count > 1
                else "unmatched",
                **_event_metadata(
                    event,
                    team_name,
                    opponent,
                    "<ambiguous>" if event_count > 1 else "<unmatched>",
                ),
                **frame_observability(
                    frame, event, pitch_length=pitch_length, pitch_width=pitch_width
                ),
            }
        )
    frame_table = pd.DataFrame(
        frame_rows,
        columns=[
            "match_id",
            "frame_ordinal",
            "event_id",
            "matching_event_records",
            "frame_uuid_records",
            "event_link_status",
            "event_index",
            "event_type",
            "event_team",
            "event_team_group",
            *frame_observability(
                {}, pitch_length=pitch_length, pitch_width=pitch_width
            ).keys(),
        ],
    )
    valid_event_counts = {
        key: count for key, count in event_counts.items() if key is not None
    }
    valid_frame_counts = {
        key: count for key, count in frame_counts.items() if key is not None
    }
    matched_events = int(event_table["has_360_frame"].sum())
    summary = {
        "match_id": match_id,
        "date": match.get("match_date"),
        "opponent": opponent,
        "venue": venue,
        "match_week": match.get("match_week"),
        "total_events": len(events),
        "unique_event_ids": len(valid_event_counts),
        "events_missing_id": event_counts[None],
        "duplicate_event_ids": sum(n - 1 for n in valid_event_counts.values()),
        "duplicate_event_id_groups": sum(n > 1 for n in valid_event_counts.values()),
        "frames_load_status": load_status,
        "frames_loaded": frames is not None,
        "frames_load_error": load_error,
        "total_frames": len(frames) if frames is not None else None,
        "unique_frame_event_uuids": len(valid_frame_counts)
        if frames is not None
        else None,
        "frames_missing_uuid": frame_counts[None] if frames is not None else None,
        "duplicate_frame_uuids": sum(n - 1 for n in valid_frame_counts.values())
        if frames is not None
        else None,
        "duplicate_frame_uuid_groups": sum(n > 1 for n in valid_frame_counts.values())
        if frames is not None
        else None,
        "matched_events": matched_events,
        "events_without_frames": len(events) - matched_events,
        "frames_without_matching_events": int(
            frame_table["matching_event_records"].eq(0).sum()
        )
        if frames is not None
        else None,
        "frames_with_ambiguous_event": int(
            frame_table["matching_event_records"].gt(1).sum()
        )
        if frames is not None
        else None,
        **summarize_actor_distances(frame_table),
    }
    return summary, frame_table, event_table


def _coverage_counts(events: pd.DataFrame, frames: pd.DataFrame) -> dict:
    nonempty = frames["freeze_frame_empty"].eq(False)
    valid_area = frames["visible_area_valid"].eq(True)
    measurable = frames["actor_consistency_measurable"].eq(True)
    unique_link = frames["event_link_status"].eq("unique") & frames[
        "frame_uuid_records"
    ].eq(1)
    valid_players = frames["freeze_frame_malformed"].eq(False) & frames[
        "valid_player_locations"
    ].eq(frames["visible_players"])
    return {
        "all_events": len(events),
        "events_with_360_frame": int(events["has_360_frame"].sum()),
        "events_without_frame": int((~events["has_360_frame"].astype(bool)).sum()),
        "events_360_load_unavailable": int(
            events["frames_load_status"].ne("loaded").sum()
        ),
        "all_frames": len(frames),
        "frames_nonempty_freeze_frame": int(nonempty.sum()),
        "frames_valid_visible_area": int(valid_area.sum()),
        "frames_actor_measurable": int(measurable.sum()),
        "frames_missing_visible_area": int(
            frames["visible_area_missing"].eq(True).sum()
        ),
        "frames_malformed_visible_area": int(
            frames["visible_area_malformed"].eq(True).sum()
        ),
        "frames_invalid_polygon": int(
            (
                frames["visible_area_exists"].eq(True)
                & frames["visible_area_malformed"].eq(False)
                & ~valid_area
            ).sum()
        ),
        "frames_unique_event_and_frame_id": int(unique_link.sum()),
        "frames_unique_nonempty": int((unique_link & nonempty).sum()),
        "frames_unique_nonempty_valid_area": int(
            (unique_link & nonempty & valid_area).sum()
        ),
        "frames_joint_checks": int(
            (unique_link & nonempty & valid_area & measurable & valid_players).sum()
        ),
        **summarize_actor_distances(frames),
    }


def summarize_attrition(events: pd.DataFrame, frames: pd.DataFrame) -> pd.DataFrame:
    """Summarize independent coverage counts and a cumulative mechanical subset.

    Scope rows are alternative partitions, not additive across scopes. Each scope
    preserves all rows, including unknown/orphan/ambiguous categories. Event
    coverage uses event rows; frame criteria use frame rows. ``frames_joint_checks``
    is not a final research sample or an actor-distance tolerance test.
    """
    rows = [{"scope": "season", "group": "all", **_coverage_counts(events, frames)}]
    for column in ("match_id", "event_type", "event_team_group"):
        values = pd.concat(
            [events[column], frames[column]], ignore_index=True
        ).drop_duplicates()
        for value in values:
            event_group = events[events[column].eq(value)]
            frame_group = frames[frames[column].eq(value)]
            rows.append(
                {
                    "scope": column,
                    "group": str(value),
                    **_coverage_counts(event_group, frame_group),
                }
            )
    return pd.DataFrame(rows)


def largest_actor_discrepancies(frames: pd.DataFrame, count: int = 10) -> pd.DataFrame:
    """Return the largest measured distances for review, not threshold failures."""
    if count < 1:
        raise ValueError("count must be positive")
    return (
        frames.loc[frames["actor_consistency_measurable"].eq(True)]
        .sort_values("actor_distance", ascending=False, kind="stable")
        .head(count)
    )


def audit_season(
    *,
    team_name: str = "Bayer Leverkusen",
    expected_matches: int = 34,
    pitch_length: float = 120,
    pitch_width: float = 80,
    progress: Callable[[int, int, int], None] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch each match's events/360 once and return three derived audit tables.

    Event-load failures abort: a season denominator cannot be inferred. Missing
    360 and other 360 load errors are recorded separately and do not fabricate
    frame rows. Match uniqueness is checked before match-level network calls.
    """
    matches = [
        m
        for m in loader.load_matches()
        if team_name
        in (
            m.get("home_team", {}).get("home_team_name"),
            m.get("away_team", {}).get("away_team_name"),
        )
    ]
    identifiers = [m["match_id"] for m in matches]
    if len(matches) != expected_matches or len(set(identifiers)) != expected_matches:
        raise ValueError(
            f"Expected {expected_matches} unique {team_name} matches; found {len(matches)} records / {len(set(identifiers))} unique IDs"
        )
    summaries, frame_tables, event_tables = [], [], []
    for number, match in enumerate(matches, 1):
        events = loader.load_events(match["match_id"])
        status, error = "loaded", None
        try:
            frames = loader.load_360(match["match_id"])
        except FileNotFoundError as exc:
            frames, status, error = None, "missing", str(exc)
        except (requests.RequestException, ValueError) as exc:
            frames, status, error = None, "error", f"{type(exc).__name__}: {exc}"
        summary, frame_table, event_table = audit_match(
            match,
            events,
            frames,
            team_name=team_name,
            pitch_length=pitch_length,
            pitch_width=pitch_width,
            load_status=status,
            load_error=error,
        )
        summary["retrieved_at_utc"] = datetime.now(timezone.utc).isoformat()
        summary["source_base_url"] = loader.BASE_URL
        summaries.append(summary)
        frame_tables.append(frame_table)
        event_tables.append(event_table)
        if progress is not None:
            progress(number, len(matches), match["match_id"])
    frames = pd.concat(frame_tables, ignore_index=True)
    events = pd.concat(event_tables, ignore_index=True)
    frames["actor_distance"] = pd.to_numeric(frames["actor_distance"], errors="coerce")
    frames["actor_distance_review_rank"] = (
        frames["actor_distance"].rank(method="first", ascending=False).astype("Int64")
    )
    return pd.DataFrame(summaries), frames, summarize_attrition(events, frames)


def write_audit_outputs(
    matches: pd.DataFrame,
    frames: pd.DataFrame,
    attrition: pd.DataFrame,
    output_directory: Path,
) -> None:
    """Write only the three derived Phase 1 CSV tables (never raw records)."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    for name, table in (
        ("match_summary", matches),
        ("frame_summary", frames),
        ("attrition", attrition),
    ):
        table.to_csv(output_directory / f"phase1_{name}.csv", index=False)

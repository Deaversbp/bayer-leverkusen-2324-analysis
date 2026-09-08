"""Locked Phase 2A record geometry in native StatsBomb coordinate units.

No orientation, identity inference, eligibility filtering or raw persistence.
Every output has a ``<output>_status``; centroid statuses always agree.
"""

from collections import Counter
from math import hypot, isfinite
from numbers import Integral, Real
from statistics import median

import pandas as pd
from shapely.errors import ShapelyError
from shapely.geometry import MultiPoint

from leverkusen.data.observability import inspect_visible_area

SUBSETS = ("all_visible", "teammate_true", "teammate_false")
KEEPER_POLICIES = ("included", "excluded")
METRICS = (
    "visible_player_count",
    "centroid_x",
    "centroid_y",
    "visible_width",
    "visible_depth",
    "convex_hull_area",
    "mean_pairwise_distance",
    "median_pairwise_distance",
    "mean_nearest_neighbor_distance",
)


def valid_point(location: object) -> tuple | None:
    """Return supplied numeric values unchanged, or None for an invalid location."""
    if not isinstance(location, (list, tuple)) or len(location) != 2:
        return None
    if not all(
        isinstance(v, Real)
        and not isinstance(v, bool)
        and (isinstance(v, Integral) or isfinite(v))
        for v in location
    ):
        return None
    return tuple(location)


def _numeric(operation) -> tuple[object, str]:
    try:
        value = operation()
        return (value, "ok") if isfinite(value) else (None, "numeric_error")
    except (OverflowError, FloatingPointError):
        return None, "numeric_error"


def _hull(points: list[tuple]) -> tuple[object, str, str | None]:
    if len(points) < 3:
        return None, "insufficient_points", None
    if len(set(points)) < 3:
        return None, "insufficient_unique_points", None
    try:
        hull = MultiPoint(points).convex_hull
        if hull.is_empty or hull.geom_type in ("Point", "LineString"):
            return None, "degenerate_hull", hull.geom_type
        if hull.geom_type != "Polygon" or not hull.is_valid:
            return None, "geometry_error", "invalid_or_unexpected_geometry"
        area = hull.area
        if not isfinite(area):
            return None, "numeric_error", "nonfinite_area"
        if area < 0:
            return None, "geometry_error", "negative_area"
        if area == 0:
            return None, "degenerate_hull", "zero_area"
        return area, "ok", None
    except ShapelyError as exc:
        return None, "geometry_error", type(exc).__name__
    except (OverflowError, FloatingPointError) as exc:
        return None, "numeric_error", type(exc).__name__


def measure_points(points: list[tuple] | None) -> dict:
    """Measure selected valid records without deduplication.

    None denotes an unavailable container; [] denotes known empty. Invalid point
    arguments raise ValueError: extraction belongs in ``frame_geometry``.
    Only expected numeric and Shapely failures become missing measurements.
    """
    result = {key: None for key in METRICS}
    result.update({f"{key}_status": "frame_unavailable" for key in METRICS})
    result["hull_error_category"] = None
    if points is None:
        return result
    if any(valid_point(p) is None for p in points):
        raise ValueError("measure_points requires valid selected points")
    points = [tuple(p) for p in points]
    n = len(points)

    def put(key, value, status):
        result[key], result[f"{key}_status"] = value, status

    put("visible_player_count", n, "ok")
    for key in METRICS[1:]:
        put(key, None, "empty_points" if key in METRICS[1:5] else "insufficient_points")
    if n:
        xs, ys = zip(*points)
        cx, sx = _numeric(lambda: sum(xs) / n)
        cy, sy = _numeric(lambda: sum(ys) / n)
        status = "ok" if sx == sy == "ok" else "numeric_error"
        put("centroid_x", cx if status == "ok" else None, status)
        put("centroid_y", cy if status == "ok" else None, status)
        put("visible_width", *_numeric(lambda: max(ys) - min(ys)))
        put("visible_depth", *_numeric(lambda: max(xs) - min(xs)))
    if n >= 2:
        pairs, nearest = [], [float("inf")] * n
        pair_failure = False
        for i, (x, y) in enumerate(points):
            for j in range(i + 1, n):
                distance, _ = _numeric(
                    lambda: hypot(x - points[j][0], y - points[j][1])
                )
                if distance is None:
                    pair_failure = True
                    continue
                pairs.append(distance)
                nearest[i] = min(nearest[i], distance)
                nearest[j] = min(nearest[j], distance)
        if pair_failure:
            # All three summaries depend on the prescribed distance collection;
            # do not replace failed pairs or summarize an incomplete collection.
            for key in METRICS[6:]:
                put(key, None, "numeric_error")
        else:
            put("mean_pairwise_distance", *_numeric(lambda: sum(pairs) / len(pairs)))
            put("median_pairwise_distance", *_numeric(lambda: median(pairs)))
            put("mean_nearest_neighbor_distance", *_numeric(lambda: sum(nearest) / n))
    area, status, category = _hull(points)
    put("convex_hull_area", area, status)
    result["hull_error_category"] = category
    return result


def _identifier(value):
    return value if isinstance(value, str) and value.strip() else None


def frame_geometry(
    frame: dict,
    *,
    match_id: int,
    frame_index: int,
    source_revision: str,
    event: dict | None = None,
    event_join_status: str = "unmatched",
) -> list[dict]:
    """Return six wide variant rows for one original frame without mutation.

    ``event`` must come from a unique match-local join. Use build_frame_geometry
    to resolve that join automatically. Polygon metadata reuses the Phase 1
    inspector; raw player inventory here is explicitly the entire list length.
    """
    if event_join_status not in ("unique", "ambiguous", "unmatched"):
        raise ValueError("Unknown event join status")
    if (event is not None) != (event_join_status == "unique"):
        raise ValueError("Only a unique event join may supply event metadata")
    freeze = frame.get("freeze_frame")
    available = isinstance(freeze, list)
    records = [p for p in freeze if isinstance(p, dict)] if available else []
    located = [(p, valid_point(p.get("location"))) for p in records]
    valid = [(p, point) for p, point in located if point is not None]
    nondicts = len(freeze) - len(records) if available else None
    invalid_locations = len(records) - len(valid) if available else None
    actor_count = sum(p.get("actor") is True for p in records) if available else None
    unknown_actor = (
        sum(type(p.get("actor")) is not bool for p in records) if available else None
    )
    actor_status = (
        "multiple"
        if actor_count is not None and actor_count >= 2
        else "unknown"
        if not available or nondicts or invalid_locations or unknown_actor
        else "single"
        if actor_count == 1
        else "none"
    )
    try:
        area = inspect_visible_area(frame.get("visible_area"))
    except (ShapelyError, OverflowError, FloatingPointError) as exc:
        # A polygon-evaluation failure is context, not a gate on player geometry.
        # Keep the Phase 1 inspector itself unchanged and surface schema bugs.
        polygon = frame.get("visible_area")
        area = inspect_visible_area(None)
        area.update(
            visible_area_exists=polygon is not None,
            visible_area_missing=polygon is None,
            visible_area_coordinate_count=len(polygon)
            if isinstance(polygon, (list, tuple))
            else None,
            visible_area_reason=type(exc).__name__,
        )
    area_status = (
        "missing"
        if area["visible_area_missing"]
        else "malformed"
        if area["visible_area_malformed"]
        else "valid"
        if area["visible_area_valid"]
        else "invalid"
    )
    type_field = event.get("type") if event is not None else None
    event_type = (
        _identifier(type_field.get("name")) if isinstance(type_field, dict) else None
    )
    unknown_team = (
        sum(type(p.get("teammate")) is not bool for p, _ in valid)
        if available
        else None
    )
    context = {
        "match_id": match_id,
        "frame_index": frame_index,
        "event_id": _identifier(frame.get("event_uuid")),
        "event_id_raw_type": type(frame.get("event_uuid")).__name__,
        "invalid_event_id_scalar": repr(frame.get("event_uuid"))
        if _identifier(frame.get("event_uuid")) is None
        and isinstance(frame.get("event_uuid"), (str, Real))
        else None,
        "event_type": event_type,
        "event_join_status": event_join_status,
        "statsbomb_revision": source_revision,
        "total_visible_players": len(freeze) if available else None,
        "n_non_dictionary_records": nondicts,
        "n_invalid_locations": invalid_locations,
        "n_unknown_teammate": unknown_team,
        "actor_count": actor_count,
        "n_unknown_actor_flags": unknown_actor,
        "actor_status": actor_status,
        "freeze_frame_status": "available"
        if available
        else "missing"
        if freeze is None
        else "malformed",
        "visible_area_status": area_status,
        **area,
    }
    flags = set()
    if not available:
        flags.add("frame_unavailable")
    if nondicts or invalid_locations:
        flags.add("partial_invalid_input")
    if any(type(p.get("teammate")) is not bool for p in records):
        flags.add("unknown_teammate")
    if any(type(p.get("keeper")) is not bool for p in records):
        flags.add("unknown_keeper")
    if actor_status == "multiple":
        flags.add("multiple_actor")
    if actor_status == "unknown":
        flags.add("actor_status_unknown")
    if area_status != "valid":
        flags.add(
            "missing_visible_area"
            if area_status == "missing"
            else "invalid_visible_area"
        )
    if event_join_status != "unique":
        flags.add(f"{event_join_status}_event_join")
    if event_type is None:
        flags.add("unknown_event_type")
    rows = []
    for subset in SUBSETS:
        selected = [
            (p, point)
            for p, point in valid
            if subset == "all_visible"
            or p.get("teammate") is (subset == "teammate_true")
        ]
        keepers = (
            sum(p.get("keeper") is True for p, _ in selected) if available else None
        )
        unknown_keepers = (
            sum(type(p.get("keeper")) is not bool for p, _ in selected)
            if available
            else None
        )
        for policy in KEEPER_POLICIES:
            points = (
                [
                    point
                    for p, point in selected
                    if policy == "included" or p.get("keeper") is False
                ]
                if available
                else None
            )
            n = len(points) if available else None
            u = len(set(points)) if available else None
            coincidence = n - u if available else None
            out_of_bounds = (
                sum(not (0 <= x <= 120 and 0 <= y <= 80) for x, y in points)
                if available
                else None
            )
            row_flags = flags.copy()
            if coincidence:
                row_flags.add("coincident_records")
            if out_of_bounds:
                row_flags.add("out_of_bounds_points")
            rows.append(
                {
                    **context,
                    "selected_subset": subset,
                    "goalkeeper_policy": policy,
                    "n_valid_points_used": n,
                    "n_unique_points": u,
                    "n_coincident_records": coincidence,
                    "n_out_of_bounds_points": out_of_bounds,
                    "n_keeper_true_before_filter": keepers,
                    "n_keeper_unknown_before_filter": unknown_keepers,
                    "n_keeper_true_excluded": keepers
                    if policy == "excluded"
                    else 0
                    if available
                    else None,
                    "n_keeper_unknown_excluded": unknown_keepers
                    if policy == "excluded"
                    else 0
                    if available
                    else None,
                    "measurement_flags": "|".join(sorted(row_flags)),
                    **measure_points(points),
                }
            )
    return rows


def build_frame_geometry(
    match_id: int,
    events: list[dict],
    frames: list[dict],
    *,
    source_revision: str,
) -> pd.DataFrame:
    """Build six rows per original frame, retaining duplicate IDs and orphan frames.

    Match-local event matching has Phase 1 unique/ambiguous/unmatched semantics.
    Events without frames create no geometry rows. A missing 360 resource belongs
    in a match inventory, not in a fabricated frame.
    """
    counts = Counter(_identifier(e.get("id")) for e in events)
    unique = {
        e["id"]: e
        for e in events
        if _identifier(e.get("id")) is not None and counts[e["id"]] == 1
    }
    rows = []
    for index, frame in enumerate(frames):
        identifier = _identifier(frame.get("event_uuid"))
        count = counts[identifier] if identifier is not None else 0
        rows.extend(
            frame_geometry(
                frame,
                match_id=match_id,
                frame_index=index,
                source_revision=source_revision,
                event=unique.get(identifier),
                event_join_status="unique"
                if count == 1
                else "ambiguous"
                if count > 1
                else "unmatched",
            )
        )
    if not rows:
        columns = frame_geometry(
            {}, match_id=match_id, frame_index=0, source_revision=source_revision
        )[0].keys()
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows)

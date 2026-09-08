"""Phase 2B-2 diagnostics, without repair, filtering or geometry redefinition.

Raw coordinates live in memory only. Distances are unsigned native units, including
for points outside the supplied polygon. Exact topology predicates use no buffer.
"""

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from math import hypot
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import Polygon, box

from leverkusen.data import loader
from leverkusen.data.observability import inspect_visible_area
from leverkusen.spatial.diagnostics import FRAME, VARIANT, validate_variants
from leverkusen.spatial.geometry import METRICS, measure_points, valid_point

PITCH = box(0, 0, 120, 80)
SIDES = ("x_below_0", "x_above_120", "y_below_0", "y_above_80")
EDGE_FIELDS = (
    "min_x_edge_distance",
    "max_x_edge_distance",
    "min_y_edge_distance",
    "max_y_edge_distance",
    "minimum_selected_edge_distance",
    "median_selected_edge_distance",
)
RELATIONSHIPS = (
    ("visible_width", "min_y_edge_distance"),
    ("visible_width", "max_y_edge_distance"),
    ("visible_depth", "min_x_edge_distance"),
    ("visible_depth", "max_x_edge_distance"),
    ("convex_hull_area", "minimum_selected_edge_distance"),
)
MAJOR = (
    "visible_width",
    "visible_depth",
    "convex_hull_area",
    "mean_pairwise_distance",
    "mean_nearest_neighbor_distance",
)


def excursion(point):
    """Distance to the nominal rectangle, retaining the supplied point unchanged."""
    if valid_point(point) is None:
        raise ValueError("Expected a finite coordinate pair")
    x, y = point
    dx, dy = max(0, -x, x - 120), max(0, -y, y - 80)
    sides = dict(zip(SIDES, (x < 0, x > 120, y < 0, y > 80)))
    return {
        **sides,
        "sides_violated": sum(sides.values()),
        "x_excess": dx,
        "y_excess": dy,
        "pitch_distance": hypot(dx, dy),
    }


def polygon_diagnostics(visible_area):
    """Reuse Phase 1 validation; intersection is measured without altering input."""
    info = inspect_visible_area(visible_area)
    extra = dict.fromkeys(
        (
            "contained_in_pitch",
            "intersects_pitch_boundary",
            "extends_outside_pitch",
            "area_inside_pitch",
            "area_outside_pitch",
            "fraction_outside_pitch",
        )
    )
    polygon = None
    if info["visible_area_valid"]:
        polygon = Polygon(zip(visible_area[::2], visible_area[1::2]))
        outside = polygon.difference(PITCH).area
        extra.update(
            contained_in_pitch=PITCH.covers(polygon),
            intersects_pitch_boundary=polygon.intersects(PITCH.boundary),
            extends_outside_pitch=not PITCH.covers(polygon),
            area_inside_pitch=info["visible_area_on_pitch_area"],
            area_outside_pitch=outside,
            fraction_outside_pitch=outside / polygon.area,
        )
    return polygon, {**info, **extra}


def point_polygon_diagnostics(points, polygon):
    """Exclusive inside/boundary/outside status plus inclusive covered predicate."""
    if polygon is None or not polygon.is_valid or polygon.area <= 0:
        return [
            {
                "polygon_status": "unavailable",
                "polygon_covered": None,
                "visible_boundary_distance": None,
            }
            for _ in points
        ]
    if not points:
        return []
    geometries = shapely.points(points)
    inside = shapely.contains(polygon, geometries)
    covered = shapely.covers(polygon, geometries)
    distances = shapely.distance(geometries, polygon.boundary)
    return [
        {
            "polygon_status": "inside" if i else "boundary" if c else "outside",
            "polygon_covered": bool(c),
            "visible_boundary_distance": float(d),
        }
        for i, c, d in zip(inside, covered, distances)
    ]


def extreme_indices(points):
    """All record indices tied at each extreme, in original selected order."""
    if not points:
        return {name: [] for name in ("min_x", "max_x", "min_y", "max_y")}
    values = np.asarray(points)
    return {
        name: np.flatnonzero(values[:, axis] == op(values[:, axis])).tolist()
        for name, axis, op in (
            ("min_x", 0, np.min),
            ("max_x", 0, np.max),
            ("min_y", 1, np.min),
            ("max_y", 1, np.max),
        )
    }


def edge_diagnostics(points, polygon, point_info=None):
    """Tie summary is minimum distance; every tied distance is also returned.

    An empty selection or invalid polygon yields NA, never a fabricated zero.
    The supplemental tied-extreme table retains all tied records and distances.
    """
    result = dict.fromkeys(EDGE_FIELDS)
    result.update(
        edge_status="empty_points" if not points else "polygon_unavailable",
        selected_outside_polygon_count=None,
    )
    if not points or polygon is None or not polygon.is_valid or polygon.area <= 0:
        return result, []
    info = (
        point_info
        if point_info is not None
        else point_polygon_diagnostics(points, polygon)
    )
    distances = np.array([r["visible_boundary_distance"] for r in info])
    result.update(
        edge_status="ok",
        minimum_selected_edge_distance=distances.min(),
        median_selected_edge_distance=float(np.median(distances)),
        selected_outside_polygon_count=sum(
            r["polygon_status"] == "outside" for r in info
        ),
    )
    ties = []
    for name, indices in extreme_indices(points).items():
        result[f"{name}_edge_distance"] = distances[indices].min()
        result[f"{name}_tied_records"] = len(indices)
        if len(indices) > 1:
            ties.extend(
                {
                    "extreme": name,
                    "selected_record_index": i,
                    "edge_distance": distances[i],
                    "polygon_status": info[i]["polygon_status"],
                }
                for i in indices
            )
    return result, ties


def coincident_groups(points):
    """Exact-coordinate index groups; no claim about player identity."""
    groups = defaultdict(list)
    for i, point in enumerate(points):
        groups[tuple(point)].append(i)
    return [indices for indices in groups.values() if len(indices) > 1]


def selected_records(frame, subset="all_visible", policy="included"):
    freeze = frame.get("freeze_frame")
    if not isinstance(freeze, list):
        return []
    return [
        (i, r, valid_point(r.get("location")))
        for i, r in enumerate(freeze)
        if isinstance(r, dict)
        and valid_point(r.get("location")) is not None
        and (
            subset == "all_visible" or r.get("teammate") is (subset == "teammate_true")
        )
        and (policy == "included" or r.get("keeper") is False)
    ]


def describe(values):
    values = pd.Series(values, dtype=float)
    observed = values.dropna()
    return {
        "rows": len(values),
        "denominator": len(observed),
        "na_count": values.isna().sum(),
        "mean": observed.mean(),
        "min": observed.min(),
        "max": observed.max(),
        "median": observed.median(),
        **{
            f"p{q:02d}": observed.quantile(q / 100)
            for q in (1, 5, 10, 25, 75, 90, 95, 99)
        },
    }


def quantile_groups(values, bins=5):
    """Right-closed empirical bins, minimum included, ties kept, NA explicit."""
    labels = pd.Series("unavailable", index=values.index)
    observed = values.dropna()
    if observed.empty:
        return labels, []
    edges = np.unique(observed.quantile(np.linspace(0, 1, bins + 1)))
    if len(edges) == 1:
        edges = np.repeat(edges, 2)
        labels.loc[observed.index] = "Q1"
    else:
        codes = pd.cut(observed, edges, labels=False, include_lowest=True)
        labels.loc[observed.index] = codes.map(lambda c: f"Q{int(c) + 1}")
    return labels, [
        {
            "bin": f"Q{i + 1}",
            "lower": left,
            "upper": right,
            "lower_inclusive": i == 0,
            "upper_inclusive": True,
        }
        for i, (left, right) in enumerate(zip(edges[:-1], edges[1:]))
    ]


def select_representatives(table):
    """Deterministic rules; ties by match, frame, literal subset and keeper policy.

    Metric extremes use defined positive-area hulls as a review preference only;
    all rows remain in population summaries. A frame may satisfy multiple rules.
    The rule table can have more rows than the unique rendered frame set.
    """
    table = table.sort_values(FRAME + VARIANT).copy()
    all_visible = table.loc[
        table.selected_subset.eq("all_visible") & table.goalkeeper_policy.eq("included")
    ]
    rows = []

    def pick(pool, field, rule, target=None, largest=False):
        pool = pool.dropna(subset=[field])
        if pool.empty:
            return
        score = pool[field] if target is None else (pool[field] - target).abs()
        index = score.idxmax() if largest else score.idxmin()
        rows.append(
            {
                **pool.loc[index].to_dict(),
                "selection_rule": rule,
                "selection_field": field,
                "selection_value": pool.loc[index, field],
            }
        )

    oob = all_visible.loc[all_visible.n_out_of_bounds_points.gt(0)]
    for field in ("max_x_excess", "max_y_excess"):
        pick(oob, field, field, largest=True)
    pick(oob, "min_positive_pitch_distance", "smallest_positive_excursion")
    for side in SIDES:
        pick(
            oob.loc[oob[f"count_{side}"].gt(0)],
            f"max_distance_{side}",
            f"largest_on_{side}",
            largest=True,
        )
    for q, label in ((0, "lowest"), (0.5, "typical"), (1, "highest")):
        pick(
            all_visible,
            "visible_area_fraction",
            f"{label}_coverage",
            target=all_visible.visible_area_fraction.quantile(q),
        )
    for largest in (False, True):
        pick(
            all_visible,
            "n_valid_points_used",
            f"{'high' if largest else 'low'}_count",
            largest=largest,
        )
    usable = table.loc[table.convex_hull_area.notna()]
    for metric in MAJOR:
        for largest in (False, True):
            pick(
                usable,
                metric,
                f"{'high' if largest else 'low'}_{metric}",
                largest=largest,
            )
    for metric in ("visible_depth", "convex_hull_area", "centroid_x"):
        pick(
            table,
            f"abs_keeper_delta_{metric}",
            f"largest_keeper_change_{metric}",
            largest=True,
        )
    for _, row in all_visible.loc[all_visible.actor_count.gt(1)].iterrows():
        rows.append(
            {
                **row.to_dict(),
                "selection_rule": "multiple_actor",
                "selection_field": "actor_count",
                "selection_value": row.actor_count,
            }
        )
    coincident = all_visible.loc[
        all_visible.n_coincident_records.gt(0) & all_visible.actor_count.le(1)
    ]
    # Prefer event-type diversity; stable source keys resolve every tie.
    for _, row in coincident.drop_duplicates("event_type").head(3).iterrows():
        rows.append(
            {
                **row.to_dict(),
                "selection_rule": "coincident_event_type_example",
                "selection_field": "n_coincident_records",
                "selection_value": row.n_coincident_records,
            }
        )
    return pd.DataFrame(rows)


def add_keeper_deltas(table):
    table = table.copy()
    included = table.loc[table.goalkeeper_policy.eq("included")].set_index(
        FRAME + ["selected_subset"]
    )
    excluded = table.loc[table.goalkeeper_policy.eq("excluded")].set_index(
        FRAME + ["selected_subset"]
    )
    delta = pd.DataFrame(index=included.index)
    for metric in ("visible_depth", "convex_hull_area", "centroid_x"):
        delta[f"abs_keeper_delta_{metric}"] = (
            excluded[metric] - included[metric]
        ).abs()
    return table.merge(
        delta.reset_index(), on=FRAME + ["selected_subset"], validate="many_to_one"
    )


def inspect_match(frames, geometry, preferred_keys=()):
    """Return derived diagnostics and a bounded in-memory representative pool."""
    oob, polygons, edges, coincidences, impacts, actors, ties = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    keyed = geometry.groupby("frame_index", sort=False)
    for index, frame in enumerate(frames):
        variants = keyed.get_group(index)
        first = variants.iloc[0]
        if not variants.event_id.eq(frame.get("event_uuid")).all():
            raise ValueError("Raw frame ordinal/event ID disagrees with Phase 2A")
        context = {k: first[k] for k in (*FRAME, "event_id", "event_type")}
        records = selected_records(frame)
        points = [p for _, _, p in records]
        polygon, polygon_info = polygon_diagnostics(frame.get("visible_area"))
        raw_fraction = polygon_info["visible_area_fraction"]
        if not (
            (pd.isna(raw_fraction) and pd.isna(first.visible_area_fraction))
            or (
                pd.notna(raw_fraction)
                and pd.notna(first.visible_area_fraction)
                and np.isclose(
                    raw_fraction, first.visible_area_fraction, rtol=0, atol=1e-14
                )
            )
        ):
            raise ValueError("Coverage disagrees with Phase 2A")
        point_info = point_polygon_diagnostics(points, polygon)
        by_index = {i: info for (i, _, _), info in zip(records, point_info)}
        excursions = [excursion(p) for p in points]
        positive = [e["pitch_distance"] for e in excursions if e["pitch_distance"] > 0]
        polygons.append(
            {
                **context,
                **polygon_info,
                "max_x_excess": max((e["x_excess"] for e in excursions), default=0),
                "max_y_excess": max((e["y_excess"] for e in excursions), default=0),
                "max_pitch_distance": max(positive, default=0),
                "min_positive_pitch_distance": min(positive, default=None),
                **{f"count_{s}": sum(e[s] for e in excursions) for s in SIDES},
                **{
                    f"max_distance_{s}": max(
                        (e["pitch_distance"] for e in excursions if e[s]), default=0
                    )
                    for s in SIDES
                },
            }
        )
        for (i, record, _), exc, info in zip(records, excursions, point_info):
            if exc["sides_violated"]:
                oob.append(
                    {
                        **context,
                        "record_index": i,
                        **exc,
                        **info,
                        **{
                            flag: record.get(flag)
                            if type(record.get(flag)) is bool
                            else "unknown"
                            for flag in ("teammate", "keeper", "actor")
                        },
                    }
                )
        groups = coincident_groups(points)
        for group_index, group in enumerate(groups):
            members = [records[i][1] for i in group]
            coincidences.append(
                {
                    **context,
                    "group_index": group_index,
                    "group_size": len(group),
                    "excess_records": len(group) - 1,
                    **{
                        f"{flag}_{value}_count": sum(
                            r.get(flag) is value for r in members
                        )
                        for flag in ("teammate", "keeper", "actor")
                        for value in (True, False)
                    },
                    **{
                        f"{flag}_unknown_count": sum(
                            type(r.get(flag)) is not bool for r in members
                        )
                        for flag in ("teammate", "keeper", "actor")
                    },
                }
            )
        actor_records = [(i, r, p) for i, r, p in records if r.get("actor") is True]
        if first.actor_count > 1:
            actor_points = [p for _, _, p in actor_records]
            pair_distances = [
                hypot(a[0] - b[0], a[1] - b[1])
                for i, a in enumerate(actor_points)
                for b in actor_points[i + 1 :]
            ]
            actors.append(
                {
                    **context,
                    "actor_count": first.actor_count,
                    "valid_actor_count": len(actor_points),
                    "unique_actor_locations": len(set(actor_points)),
                    "actor_pair_distance_min": min(pair_distances, default=None),
                    "actor_pair_distance_max": max(pair_distances, default=None),
                    "coincident_actor_excess": len(actor_points)
                    - len(set(actor_points)),
                    **{
                        f"actor_{flag}_{value}_count": sum(
                            r.get(flag) is value for _, r, _ in actor_records
                        )
                        for flag in ("teammate", "keeper")
                        for value in (True, False)
                    },
                    **{metric: first[metric] for metric in METRICS},
                    "geometry_policy": "unchanged records retained; actor flag is not a geometry input",
                }
            )
        for row in variants.to_dict("records"):
            selected = selected_records(
                frame, row["selected_subset"], row["goalkeeper_policy"]
            )
            selected_points = [p for _, _, p in selected]
            if len(selected_points) != row["n_valid_points_used"]:
                raise ValueError("Selection count disagrees with Phase 2A")
            result, tied = edge_diagnostics(
                selected_points, polygon, [by_index[i] for i, _, _ in selected]
            )
            key = {k: row[k] for k in FRAME + VARIANT}
            edges.append({**key, **result})
            ties.extend({**key, **t} for t in tied)
            for group_index, group in enumerate(coincident_groups(selected_points)):
                # Add a record only in this diagnostic counterfactual. Never
                # deduplicate, mutate, or substitute the locked geometry values.
                perturbed = measure_points(
                    selected_points + [selected_points[group[0]]]
                )
                for metric in METRICS:
                    base, changed = row[metric], perturbed[metric]
                    impacts.append(
                        {
                            **context,
                            **key,
                            "group_index": group_index,
                            "metric": metric,
                            "original": base,
                            "one_extra_record": changed,
                            "delta": changed - base
                            if changed is not None and pd.notna(base)
                            else None,
                            "original_status": row[f"{metric}_status"],
                            "perturbed_status": perturbed[f"{metric}_status"],
                        }
                    )
    polygons = pd.DataFrame(polygons)
    enriched = geometry.merge(
        pd.DataFrame(edges), on=FRAME + VARIANT, validate="one_to_one"
    )
    new_columns = [c for c in polygons if c not in enriched or c in FRAME]
    enriched = enriched.merge(polygons[new_columns], on=FRAME, validate="many_to_one")
    candidates = select_representatives(enriched)
    raw_candidates = {
        (int(row.match_id), int(row.frame_index)): frames[int(row.frame_index)]
        for row in candidates.itertuples()
    }
    for match_id, frame_index in preferred_keys:
        if match_id == int(geometry.iloc[0].match_id):
            raw_candidates[(match_id, frame_index)] = frames[frame_index]
    return (
        enriched,
        {
            "out_of_bounds_records": pd.DataFrame(oob),
            "polygon_frames": polygons,
            "coincident_groups": pd.DataFrame(coincidences),
            "coincident_multiplicity_impact": pd.DataFrame(impacts),
            "multiple_actor_review": pd.DataFrame(actors),
            "tied_extreme_distances": pd.DataFrame(ties),
        },
        raw_candidates,
    )


def summarize_quality(table, diagnostics):
    oob, polygons = diagnostics["out_of_bounds_records"], diagnostics["polygon_frames"]
    summaries = {}
    rows = []
    scopes = [("population", "all", oob)]
    for field in (
        "sides_violated",
        *SIDES,
        "teammate",
        "keeper",
        "actor",
        "polygon_status",
    ):
        scopes.extend(
            (field, str(value), group)
            for value, group in oob.groupby(field, dropna=False)
        )
    labels, bounds = quantile_groups(oob.pitch_distance)
    summaries["excursion_quantile_bins"] = pd.DataFrame(bounds)
    scopes.extend(
        ("excursion_quantile", label, oob.loc[labels.eq(label)])
        for label in labels.unique()
    )
    for scope, value, group in scopes:
        for measure in (
            "pitch_distance",
            "x_excess",
            "y_excess",
            "visible_boundary_distance",
        ):
            rows.append(
                {
                    "scope": scope,
                    "value": value,
                    "measure": measure,
                    "affected_frames": len(group.drop_duplicates(FRAME)),
                    "affected_matches": group.match_id.nunique(),
                    "covered_count": group.polygon_covered.eq(True).sum(),
                    "outside_count": group.polygon_status.eq("outside").sum(),
                    **describe(group[measure]),
                }
            )
    summaries["out_of_bounds_summary"] = pd.DataFrame(rows)
    original = table.loc[
        table.selected_subset.eq("all_visible") & table.goalkeeper_policy.eq("included")
    ]
    for field in ("match_id", "event_type"):
        groups = []
        for value, population in original.groupby(field, dropna=False):
            group = oob.loc[oob[field].eq(value)]
            groups.append(
                {
                    field: value,
                    "population_frames": len(population),
                    "affected_frames": len(group.drop_duplicates(FRAME)),
                    "out_of_bounds_records": len(group),
                    **describe(group.pitch_distance),
                }
            )
        summaries[f"out_of_bounds_by_{'match' if field == 'match_id' else field}"] = (
            pd.DataFrame(groups)
        )
    rows = []
    for scope, group in (
        ("all_frames", polygons),
        ("extends_outside", polygons.loc[polygons.extends_outside_pitch.eq(True)]),
    ):
        for measure in (
            "area_inside_pitch",
            "area_outside_pitch",
            "fraction_outside_pitch",
            "visible_area_fraction",
        ):
            rows.append(
                {
                    "scope": scope,
                    "measure": measure,
                    "valid_polygons": group.visible_area_valid.sum(),
                    "contained_count": group.contained_in_pitch.eq(True).sum(),
                    "intersects_boundary_count": group.intersects_pitch_boundary.eq(
                        True
                    ).sum(),
                    "extends_outside_count": group.extends_outside_pitch.eq(True).sum(),
                    **describe(group[measure]),
                }
            )
    summaries["visible_polygon_bounds_summary"] = pd.DataFrame(rows)
    edge_rows, relation_rows, extreme_rows, tail_rows = [], [], [], []
    for variant, group in table.groupby(VARIANT):
        context = dict(zip(VARIANT, variant))
        for field in EDGE_FIELDS:
            edge_rows.append(
                {
                    **context,
                    "measure": field,
                    **describe(group[field]),
                    "exact_boundary_count": group[field].eq(0).sum(),
                    "outside_selected_frames": group.selected_outside_polygon_count.gt(
                        0
                    ).sum(),
                }
            )
        for metric, edge in RELATIONSHIPS:
            labels, bounds = quantile_groups(group[edge])
            for bound in bounds + (
                [{"bin": "unavailable"}] if labels.eq("unavailable").any() else []
            ):
                part = group.loc[labels.eq(bound["bin"])]
                relation_rows.append(
                    {
                        **context,
                        "metric": metric,
                        "edge_measure": edge,
                        **bound,
                        "edge_median": part[edge].median(),
                        "n_median": part.n_valid_points_used.median(),
                        "coverage_median": part.visible_area_fraction.median(),
                        **describe(part[metric]),
                    }
                )
        for metric in MAJOR:
            values = group[metric].dropna()
            for label, q in (
                ("lower_1_percent", 0.01),
                ("upper_1_percent", 0.99),
                ("all_defined", None),
            ):
                cutoff = values.quantile(q) if q is not None else None
                part = group.loc[
                    group[metric].notna()
                    & (
                        group[metric].le(cutoff)
                        if q == 0.01
                        else group[metric].ge(cutoff)
                        if q == 0.99
                        else True
                    )
                ]
                tail_rows.append(
                    {
                        **context,
                        "metric": metric,
                        "tail": label,
                        "empirical_cutoff": cutoff,
                        "rows": len(part),
                        "metric_median": part[metric].median(),
                        **{
                            f"{field}_median": part[field].median()
                            for field in (
                                "n_valid_points_used",
                                "visible_area_fraction",
                                *EDGE_FIELDS,
                            )
                        },
                        "n_min": part.n_valid_points_used.min(),
                        "n_max": part.n_valid_points_used.max(),
                        "coverage_p25": part.visible_area_fraction.quantile(0.25),
                        "coverage_p75": part.visible_area_fraction.quantile(0.75),
                        **{
                            f"{name}_fraction": mask.mean()
                            for name, mask in (
                                ("out_of_bounds", part.n_out_of_bounds_points.gt(0)),
                                ("coincident", part.n_coincident_records.gt(0)),
                                ("multiple_actor", part.actor_count.gt(1)),
                                (
                                    "keeper_present",
                                    part.n_keeper_true_before_filter.gt(0)
                                    & part.goalkeeper_policy.eq("included"),
                                ),
                                (
                                    "selected_outside_polygon",
                                    part.selected_outside_polygon_count.gt(0),
                                ),
                            )
                        },
                    }
                )
            for high in (False, True):
                part = (
                    group.dropna(subset=[metric])
                    .sort_values([metric, *FRAME], ascending=[not high, True, True])
                    .head(1)
                )
                extreme_rows.extend(
                    {
                        **r,
                        "review_metric": metric,
                        "tail": "maximum" if high else "minimum",
                    }
                    for r in part.to_dict("records")
                )
    summaries["edge_distance_summary"] = pd.DataFrame(edge_rows)
    summaries["metric_edge_relationship"] = pd.DataFrame(relation_rows)
    summaries["extreme_geometry_review"] = pd.DataFrame(extreme_rows)
    summaries["extreme_tail_summary"] = pd.DataFrame(tail_rows)
    groups = diagnostics["coincident_groups"]
    summaries["coincident_records_summary"] = pd.DataFrame(
        [
            {
                "scope": scope,
                "value": str(value),
                "groups": len(g),
                "affected_frames": len(g.drop_duplicates(FRAME)),
                "affected_matches": g.match_id.nunique(),
                "excess_records": g.excess_records.sum(),
                "records_in_groups": g.group_size.sum(),
                **{c: g[c].sum() for c in groups if c.endswith("_count")},
            }
            for scope, value, g in [("population", "all", groups)]
            + [
                (field, value, g)
                for field in ("match_id", "event_type", "group_size")
                for value, g in groups.groupby(field, dropna=False)
            ]
        ]
    )
    impacts = diagnostics["coincident_multiplicity_impact"]
    summaries["coincident_metric_sensitivity"] = summarize_multiplicity(impacts)
    return summaries


def summarize_multiplicity(impacts):
    """Summarize exact added-record deltas using round-trip-preserved values."""
    return pd.DataFrame(
        [
            {
                **dict(zip([*VARIANT, "metric"], key)),
                **describe(g.delta),
                "changed_exact_count": g.delta.dropna().ne(0).sum(),
                "max_absolute_delta": g.delta.abs().max(),
                "status_changed_count": g.original_status.ne(g.perturbed_status).sum(),
            }
            for key, g in impacts.groupby([*VARIANT, "metric"])
        ]
    )


def run_observation_quality(source, output_dir, figure_dir, progress=print):
    """Read pinned geometry; retrieve raw 360 once per match with existing loader.

    Strict source/key/population checks abort an incomplete run. Raw records are
    never persisted. Only the selected representative candidate pool spans matches.
    """
    source, output_dir, figure_dir = Path(source), Path(output_dir), Path(figure_dir)
    with source.open("rb") as handle:
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
        source_hash = digest.hexdigest()
    table = pd.read_csv(source, float_precision="round_trip")
    if table.empty or not table.statsbomb_revision.eq(loader.STATSBOMB_REVISION).all():
        raise ValueError("Missing or different Phase 2A source revision")
    validate_variants(table)
    table = add_keeper_deltas(table)
    originals = table.loc[
        table.selected_subset.eq("all_visible") & table.goalkeeper_policy.eq("included")
    ].sort_values(FRAME)
    typical = (
        (originals.visible_area_fraction - originals.visible_area_fraction.median())
        .abs()
        .idxmin()
    )
    preferred_keys = [tuple(int(v) for v in originals.loc[typical, FRAME])]
    inventory, tables, diagnostic_parts, candidates = [], [], defaultdict(list), {}
    for done, (match_id, geometry) in enumerate(
        table.groupby("match_id", sort=True), 1
    ):
        frames = loader.load_360(int(match_id))
        if len(frames) * 6 != len(geometry) or set(geometry.frame_index) != set(
            range(len(frames))
        ):
            raise ValueError("Raw frame inventory disagrees with Phase 2A")
        enriched, diagnostics, raw_candidates = inspect_match(
            frames, geometry, preferred_keys
        )
        tables.append(enriched)
        candidates.update(raw_candidates)
        for name, diagnostic in diagnostics.items():
            if not diagnostic.empty:
                diagnostic_parts[name].append(diagnostic)
        inventory.append(
            {
                "match_id": match_id,
                "frames": len(frames),
                "variants": len(geometry),
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        progress(
            f"Phase 2B-2: {done}/{table.match_id.nunique()} matches; {match_id}; {len(frames)} frames"
        )
        del frames
    enriched = pd.concat(tables, ignore_index=True)
    diagnostics = {
        name: pd.concat(parts, ignore_index=True)
        for name, parts in diagnostic_parts.items()
    }
    representatives = select_representatives(enriched)
    # The nearest-to-global-median frame need not be a local median candidate.
    # Retain that exact frame before retrieval starts using preferred_keys.
    missing = set(map(tuple, representatives[FRAME].to_numpy())) - candidates.keys()
    if missing:
        raise ValueError(f"Representative candidate pool missed frames: {missing}")
    summaries = summarize_quality(enriched, diagnostics)
    summaries.update(
        {
            name: diagnostics[name]
            for name in (
                "coincident_groups",
                "coincident_multiplicity_impact",
                "multiple_actor_review",
                "tied_extreme_distances",
            )
        }
    )
    summaries["representative_frames"] = representatives
    summaries["match_inventory"] = pd.DataFrame(inventory)
    original = enriched.drop_duplicates(FRAME)
    summaries["run_summary"] = pd.DataFrame(
        [
            {
                "source_file": source.name,
                "source_sha256": source_hash,
                "csv_float_precision": "round_trip",
                "original_frames": len(original),
                "variant_rows": len(enriched),
                "matches": len(inventory),
                "out_of_bounds_frames": original.n_out_of_bounds_points.gt(0).sum(),
                "coincident_frames": original.n_coincident_records.gt(0).sum(),
                "multiple_actor_frames": original.actor_count.gt(1).sum(),
                "unknown_keeper_variant_rows": enriched.n_keeper_unknown_before_filter.gt(
                    0
                ).sum(),
                "geometry_numeric_error_rows": enriched[
                    [f"{m}_status" for m in METRICS]
                ]
                .isin(["geometry_error", "numeric_error"])
                .any(axis=1)
                .sum(),
                "representative_unique_frames": len(
                    representatives.drop_duplicates(FRAME)
                ),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, summary in summaries.items():
        summary["statsbomb_revision"] = loader.STATSBOMB_REVISION
        summary.to_csv(output_dir / f"phase2b2_{name}.csv", index=False)
    from leverkusen.visualization.observation_quality import write_quality_figures

    write_quality_figures(
        summaries, diagnostics, representatives, candidates, figure_dir
    )
    return summaries


def read_observation_quality(output_dir):
    """Read compact derived tables for notebook review, checking every revision."""
    names = (
        "run_summary",
        "out_of_bounds_summary",
        "out_of_bounds_by_match",
        "out_of_bounds_by_event_type",
        "excursion_quantile_bins",
        "visible_polygon_bounds_summary",
        "edge_distance_summary",
        "metric_edge_relationship",
        "coincident_records_summary",
        "coincident_metric_sensitivity",
        "multiple_actor_review",
        "representative_frames",
        "extreme_geometry_review",
        "extreme_tail_summary",
    )
    summaries = {
        name: pd.read_csv(Path(output_dir) / f"phase2b2_{name}.csv") for name in names
    }
    for name, table in summaries.items():
        if (
            "statsbomb_revision" not in table
            or not table.statsbomb_revision.eq(loader.STATSBOMB_REVISION).all()
        ):
            raise ValueError(f"Unknown or different revision in {name}")
    return summaries

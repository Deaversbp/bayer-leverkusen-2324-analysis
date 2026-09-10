"""Temporary Phase 2C-2 inventories, not an analytical sequence dataset.

Full event context is retained in memory. Only existing, independently audited
Phase 2C frame decisions supply anchors. No geometry, interpolation, eligibility
rule or outcome definition is introduced here.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import (
    CORE_TYPES,
    TEAM_ID,
    field,
    related_conflict_ids,
    related_evidence,
)
from leverkusen.spatial.orientation import VALIDATED, frame_semantics

KEY = ["match_id", "period", "possession_id", "possession_team_id"]
LEVELS = (1, 2, 3, 4, 5, 6, 8, 10)
GAP_COLUMNS = [
    *KEY,
    "previous_event_index",
    "next_event_index",
    "event_index_gap",
    "intervening_event_count",
    "elapsed_seconds",
    "previous_anchor_type",
    "next_anchor_type",
    "previous_event_team_id",
    "next_event_team_id",
]


def match_event_inventory(match, events, frames, *, source_revision):
    """Audit the COMPLETE match before selecting possession-team 904.

    Ambiguous joins/order/possession annotations fail explicitly, rather than
    selecting arbitrary records. Period-local timestamps retain stoppage time;
    they are never joined across a half or converted to a guessed match clock.
    """
    by_id = {e.get("id"): e for e in events}
    by_frame = {f.get("event_uuid"): f for f in frames}
    if (
        None in by_id
        or None in by_frame
        or not all(by_id)
        or not all(by_frame)
        or len(by_id) != len(events)
        or len(by_frame) != len(frames)
    ):
        raise ValueError("Ambiguous event/frame join")
    if set(by_frame) - set(by_id):
        raise ValueError("Orphan frames")
    edges = {
        eid: related_evidence(by_id[eid], frame, by_id, by_frame)
        for eid, frame in by_frame.items()
    }
    conflicts = related_conflict_ids(edges)
    rows = []
    for event in events:
        frame = by_frame.get(event["id"])
        status = (
            "no_360_frame"
            if frame is None
            else frame_semantics(
                event,
                frame,
                match,
                source_revision=source_revision,
                related_team_conflict=event["id"] in conflicts,
            )["semantics_status"]
        )
        typ = field(event, "type", "name")
        rows.append(
            {
                "match_id": match["match_id"],
                "period": event.get("period"),
                "possession_id": event.get("possession"),
                "possession_team_id": field(event, "possession_team"),
                "event_index": event.get("index"),
                "timestamp": event.get("timestamp"),
                "event_type": typ,
                "event_team_id": field(event, "team"),
                "linked_360": frame is not None,
                "semantics_status": status,
                "validated_anchor": status == VALIDATED,
                "is_shot": typ == "Shot",
                "is_goal": typ == "Shot"
                and field(event.get("shot", {}), "outcome", "name") == "Goal",
            }
        )
    table = pd.DataFrame(rows)
    required = [*KEY, "event_index", "timestamp", "event_type", "event_team_id"]
    if table.empty or table[required].isna().any().any():
        raise ValueError("Missing event order/time/possession/team annotation")
    if table.event_index.duplicated().any():
        raise ValueError("Ambiguous event order")
    table = table.sort_values("event_index", kind="stable").reset_index(drop=True)
    table["period_seconds"] = pd.to_timedelta(table.timestamp).dt.total_seconds()
    if not np.isfinite(table.period_seconds).all() or table.period_seconds.lt(0).any():
        raise ValueError("Invalid event timestamp")
    if table.period.diff().dropna().lt(0).any():
        raise ValueError("Reversed period order")
    if table.groupby("period").period_seconds.diff().dropna().lt(0).any():
        raise ValueError("Nonmonotonic timestamps within period")
    if (
        table.groupby(["period", "possession_id"])
        .possession_team_id.nunique()
        .gt(1)
        .any()
    ):
        raise ValueError("Conflicting provider possession-team annotation")
    # A reused identifier after another possession would silently join runs.
    keys = list(table[KEY].itertuples(index=False, name=None))
    runs = [k for i, k in enumerate(keys) if i == 0 or k != keys[i - 1]]
    if len(set(runs)) != len(runs):
        raise ValueError("Noncontiguous provider possession identifier")
    table["event_position"] = table.groupby(KEY, sort=False).cumcount()
    return table


def possession_inventory(stream):
    """One diagnostic row per provider possession/period; retain zero anchors."""
    rows = []
    for key, events in stream.groupby(KEY, sort=True):
        events = events.sort_values("event_index")
        anchors = events[events.validated_anchor]
        first, last = events.iloc[0], events.iloc[-1]
        linked = int(events.linked_360.sum())
        count = len(anchors)
        start = anchors.period_seconds.iloc[0] if count else np.nan
        end = anchors.period_seconds.iloc[-1] if count else np.nan
        rows.append(
            {
                **dict(zip(KEY, key)),
                "first_event_index": first.event_index,
                "last_event_index": last.event_index,
                "first_timestamp": first.timestamp,
                "last_timestamp": last.timestamp,
                "possession_duration_seconds": last.period_seconds
                - first.period_seconds,
                "total_event_count": len(events),
                "total_360_linked_event_count": linked,
                "validated_spatial_anchor_count": count,
                "unsupported_360_frame_count": linked - count,
                "first_validated_anchor_time": start,
                "last_validated_anchor_time": end,
                "validated_anchor_span_seconds": end - start,
                "proportion_of_360_frames_validated": count / linked
                if linked
                else np.nan,
                **{
                    f"anchor_count_{typ.lower()}": int(anchors.event_type.eq(typ).sum())
                    for typ in CORE_TYPES
                },
                "opponent_anchor_count": int(anchors.event_team_id.ne(TEAM_ID).sum()),
                "has_shot": bool(events.is_shot.any()),
                "has_goal": bool(events.is_goal.any()),
                "leverkusen_shot_count": int(
                    (events.is_shot & events.event_team_id.eq(TEAM_ID)).sum()
                ),
                "opponent_shot_count": int(
                    (events.is_shot & events.event_team_id.ne(TEAM_ID)).sum()
                ),
                "ends_in_shot": bool(last.is_shot),
                "final_recorded_event_type": last.event_type,
            }
        )
    return pd.DataFrame(rows)


def anchor_gaps(stream):
    """Consecutive anchors, counting ALL intervening events, including unsupported."""
    rows = []
    for key, events in stream.groupby(KEY, sort=True):
        anchors = events[events.validated_anchor].sort_values("event_index")
        records = list(anchors.itertuples(index=False))
        for previous, following in zip(records, records[1:]):
            rows.append(
                {
                    **dict(zip(KEY, key)),
                    "previous_event_index": previous.event_index,
                    "next_event_index": following.event_index,
                    "event_index_gap": following.event_index - previous.event_index,
                    "intervening_event_count": following.event_position
                    - previous.event_position
                    - 1,
                    "elapsed_seconds": following.period_seconds
                    - previous.period_seconds,
                    "previous_anchor_type": previous.event_type,
                    "next_anchor_type": following.event_type,
                    "previous_event_team_id": previous.event_team_id,
                    "next_event_team_id": following.event_team_id,
                }
            )
    return pd.DataFrame(rows, columns=GAP_COLUMNS)


def distribution(values):
    values = pd.Series(values, dtype=float)
    return {
        "count": len(values),
        "mean": values.mean(),
        "median": values.median(),
        **{
            f"p{int(q * 100):02}": values.quantile(q)
            for q in (0.05, 0.25, 0.75, 0.90, 0.95)
        },
        "maximum": values.max(),
    }


def coverage(group):
    counts = group.validated_spatial_anchor_count
    return {
        "possession_count": len(group),
        "mean_anchors": counts.mean(),
        "median_anchors": counts.median(),
        **{f"pct_ge_{n}_anchors": 100 * counts.ge(n).mean() for n in LEVELS},
    }


def temporal_windows(stream):
    """Overlapping consecutive tuples, inclusive windows, never across possessions."""
    counts = {(length, window): 0 for length in (2, 3) for window in (3, 5, 10, 15)}
    possession_counts = {(3, 10): 0, (4, 10): 0, (3, 15): 0}
    for _, group in stream.groupby(KEY, sort=True):
        times = (
            group[group.validated_anchor]
            .sort_values("event_index")
            .period_seconds.to_numpy()
        )
        for length, window in counts:
            spans = (
                times[length - 1 :] - times[: len(times) - length + 1]
                if len(times) >= length
                else []
            )
            counts[length, window] += int(np.sum(np.asarray(spans) <= window))
        for length, window in possession_counts:
            if len(times) >= length:
                spans = times[length - 1 :] - times[: len(times) - length + 1]
                possession_counts[length, window] += int(np.any(spans <= window))
    return pd.DataFrame(
        [
            {
                "unit": "consecutive_anchor_tuples",
                "states": n,
                "window_seconds": w,
                "count": c,
            }
            for (n, w), c in counts.items()
        ]
        + [
            {
                "unit": "possessions_with_any_tuple",
                "states": n,
                "window_seconds": w,
                "count": c,
            }
            for (n, w), c in possession_counts.items()
        ]
    )


def representative_possessions(possessions, stream):
    """Ten disjoint lexicographic examples; density categories use empirical quartiles."""
    p = possessions.sort_values(KEY)
    n, duration = p.validated_spatial_anchor_count, p.possession_duration_seconds
    rate = n / duration.replace(0, np.nan)
    rules = {
        "zero_anchors": n.eq(0),
        "one_anchor": n.eq(1),
        "two_anchors": n.eq(2),
        "moderate_anchor_count": n.between(n.quantile(0.25), n.quantile(0.75))
        & n.ge(3),
        "high_anchor_count": n.ge(n.quantile(0.95)),
        "shot_containing": p.has_shot,
        "opponent_anchor": p.opponent_anchor_count.gt(0),
        "long_sparse": duration.ge(duration.quantile(0.75))
        & rate.le(rate.quantile(0.25)),
        "short_dense": duration.le(duration.quantile(0.25))
        & rate.ge(rate.quantile(0.75)),
        "maximum_anchor_count": n.eq(n.max()),
    }
    selected, used = [], set()
    # Reserve maximum first so an earlier high-count category cannot consume it.
    for rule in [
        "maximum_anchor_count",
        *[r for r in rules if r != "maximum_anchor_count"],
    ]:
        candidates = p[rules[rule] & ~p.index.isin(used)]
        if candidates.empty:
            continue
        index = candidates.index[0]
        used.add(index)
        selected.append({"selection_rule": rule, **p.loc[index].to_dict()})
    manifest = pd.DataFrame(selected)
    timelines = stream.merge(
        manifest[[*KEY, "selection_rule"]], on=KEY, validate="many_to_one"
    )
    timelines["elapsed_possession_seconds"] = (
        timelines.period_seconds
        - timelines.groupby(KEY).period_seconds.transform("min")
    )
    timelines["event_team"] = np.where(
        timelines.event_team_id.eq(TEAM_ID), "Leverkusen", "Opponent"
    )
    timelines["spatial_status"] = np.where(
        timelines.validated_anchor,
        "validated",
        np.where(timelines.linked_360, "unsupported", "no_360_frame"),
    )
    return manifest, timelines[
        [
            "selection_rule",
            *KEY,
            "event_index",
            "elapsed_possession_seconds",
            "timestamp",
            "event_type",
            "event_team",
            "spatial_status",
            "semantics_status",
        ]
    ].sort_values([*KEY, "event_index"])


def summarize_readiness(possessions, gaps, stream, matches):
    """Empirical inventories only: every possession remains in the denominator."""
    p, a = possessions, stream[stream.validated_anchor]
    tables = {}
    rows = []
    for label, group in (("all", p), ("shot_containing", p[p.has_shot])):
        for n in (0, *LEVELS):
            count = int(
                group.validated_spatial_anchor_count.eq(0).sum()
                if n == 0
                else group.validated_spatial_anchor_count.ge(n).sum()
            )
            rows.append(
                {
                    "population": label,
                    "anchor_requirement": "zero" if n == 0 else f">={n}",
                    "possession_count": count,
                    "denominator": len(group),
                    "percentage": 100 * count / len(group) if len(group) else np.nan,
                }
            )
    tables["anchor_count_coverage"] = pd.DataFrame(rows)
    tables["distributions"] = pd.DataFrame(
        [
            {"measure": name, **distribution(values)}
            for name, values in (
                ("anchors_per_possession", p.validated_spatial_anchor_count),
                ("anchor_time_gap_seconds", gaps.elapsed_seconds),
                ("event_index_gap", gaps.event_index_gap),
                ("intervening_events", gaps.intervening_event_count),
            )
        ]
    )
    tables["gap_thresholds"] = pd.DataFrame(
        [
            {
                "seconds": n,
                "interval_count": int(gaps.elapsed_seconds.le(n).sum()),
                "denominator": len(gaps),
                "percentage": 100 * gaps.elapsed_seconds.le(n).mean(),
            }
            for n in (1, 2, 3, 5, 10, 15)
        ]
    )
    match_rows = []
    for match in matches:
        mid = match["match_id"]
        group, intervals = p[p.match_id.eq(mid)], gaps[gaps.match_id.eq(mid)]
        frames = group.total_360_linked_event_count.sum()
        match_rows.append(
            {
                "match_id": mid,
                "match_date": match.get("match_date"),
                "opponent": field(match, "away_team", "away_team_name")
                if field(match, "home_team", "home_team_id") == TEAM_ID
                else field(match, "home_team", "home_team_name"),
                **coverage(group),
                "median_anchor_gap_seconds": intervals.elapsed_seconds.median(),
                "p90_anchor_gap_seconds": intervals.elapsed_seconds.quantile(0.9),
                "proportion_linked_frames_validated": group.validated_spatial_anchor_count.sum()
                / frames
                if frames
                else np.nan,
            }
        )
    match_table = pd.DataFrame(match_rows).sort_values(["match_date", "match_id"])
    match_table["rank_ge_3_coverage_ascending"] = match_table.pct_ge_3_anchors.rank(
        method="min"
    ).astype(int)
    tables["match_coverage"] = match_table
    # Documented simple bins, including zero duration in the first bin.
    labels = [
        "[0,5) seconds",
        "[5,15) seconds",
        "[15,30) seconds",
        "[30,60) seconds",
        "[60,infinity) seconds",
    ]
    binned = p.assign(
        duration_bin=pd.cut(
            p.possession_duration_seconds,
            [0, 5, 15, 30, 60, np.inf],
            right=False,
            labels=labels,
        )
    )
    tables["duration_coverage"] = pd.DataFrame(
        [
            {
                "duration_bin": str(label),
                **coverage(group),
                "median_events": group.total_event_count.median(),
            }
            for label, group in binned.groupby("duration_bin", observed=False)
        ]
    )
    composition = []
    for typ in sorted(set(CORE_TYPES) | set(a.event_type)):
        group = a[a.event_type.eq(typ)]
        composition.append(
            {
                "event_type": typ,
                "anchor_count": len(group),
                "percentage_of_anchors": 100 * len(group) / len(a)
                if len(a)
                else np.nan,
                "possessions_containing": len(group[KEY].drop_duplicates()),
                "percentage_of_possessions": 100
                * len(group[KEY].drop_duplicates())
                / len(p),
                "match_count": group.match_id.nunique(),
            }
        )
    tables["anchor_type_composition"] = pd.DataFrame(composition)
    transitions = (
        gaps.groupby(["previous_anchor_type", "next_anchor_type"])
        .agg(
            interval_count=("elapsed_seconds", "size"),
            median_gap_seconds=("elapsed_seconds", "median"),
            match_count=("match_id", "nunique"),
        )
        .reset_index()
    )
    transitions["percentage_of_intervals"] = (
        100 * transitions.interval_count / len(gaps) if len(gaps) else np.nan
    )
    tables["anchor_type_transitions"] = transitions
    team_rows = []
    for side, group in (
        ("Leverkusen", a[a.event_team_id.eq(TEAM_ID)]),
        ("Opponent", a[a.event_team_id.ne(TEAM_ID)]),
    ):
        for typ in ("All", *sorted(CORE_TYPES)):
            sub = group if typ == "All" else group[group.event_type.eq(typ)]
            team_rows.append(
                {
                    "event_team": side,
                    "event_type": typ,
                    "anchor_count": len(sub),
                    "percentage_of_all_anchors": 100 * len(sub) / len(a)
                    if len(a)
                    else np.nan,
                    "percentage_within_event_team": 100 * len(sub) / len(group)
                    if len(group)
                    else np.nan,
                    "possessions_containing": len(sub[KEY].drop_duplicates()),
                    "match_count": sub.match_id.nunique(),
                }
            )
    tables["event_team_composition"] = pd.DataFrame(team_rows)
    shot_rows = []
    for label, group in (
        ("shot_containing", p[p.has_shot]),
        ("no_shot", p[~p.has_shot]),
        ("literal_final_event_shot", p[p.ends_in_shot]),
    ):
        intervals = gaps.merge(group[KEY], on=KEY, validate="many_to_one")
        shot_rows.append(
            {
                "population": label,
                **coverage(group),
                **{
                    f"gap_{k}": v
                    for k, v in distribution(intervals.elapsed_seconds).items()
                },
            }
        )
    tables["shot_coverage"] = pd.DataFrame(shot_rows)
    tables["temporal_windows"] = temporal_windows(stream)
    tables["sequence_candidates"] = pd.DataFrame(
        [
            {
                "states": n,
                "capable_possessions": int(
                    p.validated_spatial_anchor_count.ge(n).sum()
                ),
                "consecutive_tuples": int(
                    (p.validated_spatial_anchor_count - n + 1).clip(lower=0).sum()
                ),
                "available_anchor_states_in_capable_possessions": int(
                    p.loc[
                        p.validated_spatial_anchor_count.ge(n),
                        "validated_spatial_anchor_count",
                    ].sum()
                ),
            }
            for n in (2, 3, 4, 5, 6, 8)
        ]
    )
    metrics = {
        "total_leverkusen_possessions": len(p),
        "total_full_stream_events": len(stream),
        "total_validated_anchor_states": len(a),
        "median_events_per_possession": p.total_event_count.median(),
        "median_360_frames_per_possession": p.total_360_linked_event_count.median(),
        "median_validated_anchors_per_possession": p.validated_spatial_anchor_count.median(),
        **{
            f"pct_possessions_ge_{n}_anchors": 100
            * p.validated_spatial_anchor_count.ge(n).mean()
            for n in LEVELS
        },
        "median_anchor_time_gap_seconds": gaps.elapsed_seconds.median(),
        "p90_anchor_time_gap_seconds": gaps.elapsed_seconds.quantile(0.9),
        "pct_anchor_gaps_le_3_seconds": 100 * gaps.elapsed_seconds.le(3).mean(),
        "pct_anchor_gaps_le_5_seconds": 100 * gaps.elapsed_seconds.le(5).mean(),
        "pct_shot_possessions_ge_3_anchors": 100
        * p.loc[p.has_shot, "validated_spatial_anchor_count"].ge(3).mean(),
        "minimum_match_pct_ge_3_anchors": match_table.pct_ge_3_anchors.min(),
        "maximum_match_pct_ge_3_anchors": match_table.pct_ge_3_anchors.max(),
    }
    tables["sequence_readiness_summary"] = pd.DataFrame(
        [{"metric": k, "value": v} for k, v in metrics.items()]
    )
    tables["representative_possessions"], tables["representative_timelines"] = (
        representative_possessions(p, stream)
    )
    tables["possession_anchor_coverage"], tables["anchor_gap_summary"] = p, gaps
    return tables


def run_readiness(output_dir, progress=print):
    """Read pinned events/frames once per match, persist only derived diagnostics."""
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
    if len(matches) != 34 or len({m["match_id"] for m in matches}) != 34:
        raise ValueError("Expected 34 unique pinned season matches")
    streams, inventory = [], []
    for done, match in enumerate(matches, 1):
        mid = match["match_id"]
        events, frames = loader.load_events(mid), loader.load_360(mid)
        table = match_event_inventory(
            match, events, frames, source_revision=loader.STATSBOMB_REVISION
        )
        selected = table[table.possession_team_id.eq(TEAM_ID)].copy()
        streams.append(selected)
        inventory.append(
            {
                "match_id": mid,
                "all_events": len(events),
                "all_linked_frames": len(frames),
                "all_validated_frames": int(table.validated_anchor.sum()),
                "all_unsupported_frames": int(
                    (table.linked_360 & ~table.validated_anchor).sum()
                ),
                "leverkusen_possession_events": len(selected),
                "source_events_url": f"{loader.BASE_URL}/events/{mid}.json",
                "source_frames_url": f"{loader.BASE_URL}/three-sixty/{mid}.json",
            }
        )
        del events, frames, table
        progress(
            f"Phase 2C-2 {done}/34: {mid}; {len(selected)} Leverkusen-possession events"
        )
    inventory = pd.DataFrame(inventory)
    totals = tuple(
        int(inventory[c].sum())
        for c in (
            "all_events",
            "all_linked_frames",
            "all_validated_frames",
            "all_unsupported_frames",
        )
    )
    if totals != (137765, 118581, 72596, 45985):
        raise ValueError(f"Phase 2C source/scope reconciliation failed: {totals}")
    stream = pd.concat(streams, ignore_index=True)
    p, gaps = possession_inventory(stream), anchor_gaps(stream)
    if len(gaps) != int((p.validated_spatial_anchor_count - 1).clip(lower=0).sum()):
        raise ValueError("Anchor pair reconciliation failed")
    tables = summarize_readiness(p, gaps, stream, matches)
    tables["source_inventory"] = inventory
    tables["run_summary"] = pd.DataFrame(
        [
            {
                "matches": len(matches),
                "all_events": totals[0],
                "all_linked_frames": totals[1],
                "all_validated_frames": totals[2],
                "all_unsupported_frames": totals[3],
                "leverkusen_possessions": len(p),
                "leverkusen_possession_events": len(stream),
                "leverkusen_linked_frames": int(stream.linked_360.sum()),
                "leverkusen_validated_anchors": int(stream.validated_anchor.sum()),
                "consecutive_anchor_intervals": len(gaps),
                "raw_persisted": False,
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "python_version": __import__("platform").python_version(),
                "pandas_version": pd.__version__,
                "numpy_version": np.__version__,
                "phase2c_status": "VALIDATED PARTIALLY — NOT LOCKED",
                "box_entry_inventory": "skipped: full event-location semantics and entry/completion rules remain unresolved",
                "shot_ending_convention": "literal final recorded event only; final meaningful event not defined",
            }
        ]
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table["statsbomb_revision"] = loader.STATSBOMB_REVISION
        table.to_csv(output_dir / f"phase2c2_{name}.csv", index=False)
    return tables

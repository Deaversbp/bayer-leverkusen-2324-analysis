"""Phase 3A-1 descriptive action paths, drawdowns and runs; no episode labels.

Coordinates belong to recorded actions/actors. Connecting ordered observations
does not recover a ball path. Every diagnostic setting is a presentation/sweep
choice; no reset, sequence eligibility or effectiveness rule is emitted.
"""

from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.sequences.readiness import (
    KEY,
    anchor_gaps,
    match_event_inventory,
    possession_inventory,
    validate_locked_reconciliation,
)
from leverkusen.spatial.geometry import valid_point
from leverkusen.spatial.orientation import PHASE2C_STATUS, normalize_attacking_point

STATUS = "DIAGNOSTIC / NOT A METHOD LOCK"
RETREAT_SWEEP = (5, 10, 15, 20, 25, 30, 40)
DEPTH_EDGES = [-np.inf, 0, 30, 60, 80, 100, 120, np.inf]
DEPTH_LABELS = [
    "below 0",
    "[0,30)",
    "[30,60)",
    "[60,80)",
    "[80,100)",
    "[100,120)",
    "120 or above",
]


def describe(values):
    """Finite measured values only; expose missing and zero denominators."""
    s = pd.Series(values, dtype=float)
    s = s[np.isfinite(s)]
    return {
        "count": len(s),
        "mean": s.mean(),
        "median": s.median(),
        **{
            f"p{int(q * 100):02}": s.quantile(q)
            for q in (0.05, 0.10, 0.25, 0.75, 0.90, 0.95, 0.99)
        },
        "minimum": s.min(),
        "maximum": s.max(),
    }


def provider_signals(event):
    """Literal provider fields/types, not inferred hard episode boundaries."""
    signals = []
    typ = field(event, "type", "name")
    if typ in (
        "Shot",
        "Foul Won",
        "Foul Committed",
        "Offside",
        "Injury Stoppage",
        "Referee Ball-Drop",
        "Half End",
        "Half Start",
        "Dispossessed",
        "Miscontrol",
        "Interception",
        "Ball Recovery",
        "Duel",
        "Block",
        "Clearance",
    ):
        signals.append(f"type:{typ}")
    if event.get("out") is True:
        signals.append("out:true")
    if event.get("counterpress") is True:
        signals.append("counterpress:true")
    for parent in ("pass", "duel", "interception", "ball_receipt"):
        name = field(event.get(parent, {}), "outcome", "name")
        if name is not None:
            signals.append(f"{parent}.outcome:{name}")
    # Enumerate actual named pass types; no provisional zone or inferred restart.
    name = field(event.get("pass", {}), "type", "name")
    if name is not None:
        signals.append(f"pass.type:{name}")
    return signals


def enrich_match(match, events, frames, *, source_revision):
    """Reuse complete-match semantic audit; add scalar context, never mutate raw."""
    full = match_event_inventory(match, events, frames, source_revision=source_revision)
    by_index = {e["index"]: e for e in events}
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )
    rows = []
    signals = []
    for r in full.itertuples(index=False):
        event = by_index[r.event_index]
        own_vector_type = r.event_team_id == TEAM_ID and r.event_type in (
            "Pass",
            "Carry",
        )
        start = valid_point(event.get("location"))
        end = (
            valid_point(event.get(r.event_type.lower(), {}).get("end_location"))
            if own_vector_type
            else None
        )
        start_normalized = normalize_attacking_point(
            event.get("location"),
            reference_team_id=r.event_team_id,
            target_team_id=TEAM_ID,
            match_team_ids=teams,
            semantics_status=r.semantics_status,
        )
        end_normalized = (
            normalize_attacking_point(
                end,
                reference_team_id=r.event_team_id,
                target_team_id=TEAM_ID,
                match_team_ids=teams,
                semantics_status=r.semantics_status,
            )
            if end
            else {}
        )
        safe = (
            own_vector_type
            and r.validated_anchor
            and start is not None
            and end is not None
        )
        row = {
            **r._asdict(),
            "event_id": event["id"],
            "safe_action": safe,
            "action_candidate": own_vector_type,
            "explicit_vector_available": own_vector_type
            and start is not None
            and end is not None,
            "action_status": "safe_validated_frame_vector"
            if safe
            else "not_leverkusen_pass_carry"
            if not own_vector_type
            else "unsupported_or_unlinked_frame"
            if not r.validated_anchor
            else "missing_or_invalid_endpoint",
            "anchor_x": start_normalized["x_attacking"],
            "anchor_y": start_normalized["y_attacking"],
            "start_x_raw": start[0] if start else np.nan,
            "start_y_raw": start[1] if start else np.nan,
            "end_x_raw": end[0] if end else np.nan,
            "end_y_raw": end[1] if end else np.nan,
            "start_x": start_normalized["x_attacking"] if safe else np.nan,
            "start_y": start_normalized["y_attacking"] if safe else np.nan,
            "end_x": end_normalized.get("x_attacking") if safe else np.nan,
            "end_y": end_normalized.get("y_attacking") if safe else np.nan,
        }
        row["delta_x"] = row["end_x"] - row["start_x"] if safe else np.nan
        row["delta_y"] = row["end_y"] - row["start_y"] if safe else np.nan
        row["euclidean_displacement"] = (
            float(np.hypot(row["delta_x"], row["delta_y"])) if safe else np.nan
        )
        rows.append(row)
        if r.possession_team_id == TEAM_ID:
            for signal in provider_signals(event):
                signals.append(
                    {
                        **{k: getattr(r, k) for k in KEY},
                        "event_index": r.event_index,
                        "event_type": r.event_type,
                        "event_team_id": r.event_team_id,
                        "signal": signal,
                        "period_seconds": r.period_seconds,
                    }
                )
    enriched = pd.DataFrame(rows)
    selected = enriched[enriched.possession_team_id.eq(TEAM_ID)].copy()
    selected["elapsed_possession_time"] = selected.period_seconds - selected.groupby(
        KEY
    ).period_seconds.transform("min")
    # Literal final provider record, alongside actual next-event context. No inference of loss.
    for _, group in selected.groupby(KEY, sort=True):
        last = group.iloc[-1]
        signals.append(
            {
                **{k: last[k] for k in KEY},
                "event_index": last.event_index,
                "event_type": last.event_type,
                "event_team_id": last.event_team_id,
                "signal": "provider_group_final_record",
                "period_seconds": last.period_seconds,
            }
        )
    signal_table = pd.DataFrame(
        signals,
        columns=[
            *KEY,
            "event_index",
            "event_type",
            "event_team_id",
            "signal",
            "period_seconds",
        ],
    )
    following = enriched[
        ["event_index", "event_type", "event_team_id", "possession_team_id", "period"]
    ].shift(-1)
    following.columns = [f"next_{c}" for c in following.columns]
    lookup = pd.concat([enriched[["event_index"]], following], axis=1)
    signal_table = signal_table.merge(
        lookup, on="event_index", how="left", validate="many_to_one"
    )
    return enriched, selected, signal_table


def action_path(actions):
    """Ordered start/end vertices; endpoint times are ACTION-START references.

    No endpoint arrival time is inferred. Repeated start/end coordinates stay
    explicit, and inter-action coordinate discontinuities are not displacement.
    """
    rows = []
    for key, group in actions.groupby(KEY, sort=True):
        peak = -np.inf
        for r in group.sort_values("event_index").itertuples(index=False):
            for vertex, x in (("start", r.start_x), ("end", r.end_x)):
                peak = max(peak, x)
                rows.append(
                    {
                        **dict(zip(KEY, key)),
                        "event_id": r.event_id,
                        "event_index": r.event_index,
                        "event_position": r.event_position,
                        "event_type": r.event_type,
                        "period_seconds": r.period_seconds,
                        "elapsed_possession_time": r.elapsed_possession_time,
                        "vertex": vertex,
                        "attacking_x": x,
                        "running_peak_x": peak,
                        "retreat_from_peak": peak - x,
                    }
                )
    return pd.DataFrame(
        rows,
        columns=[
            *KEY,
            "event_id",
            "event_index",
            "event_position",
            "event_type",
            "period_seconds",
            "elapsed_possession_time",
            "vertex",
            "attacking_x",
            "running_peak_x",
            "retreat_from_peak",
        ],
    )


def progression_runs(actions):
    """Maximal same-sign runs in usable action order, NOT full-event adjacency.

    Other contextual events do not vanish: the run records intervening rows.
    Strict sign has no magnitude tolerance. Non-positive is a separate zero-
    tolerant presentation alternative; no near-zero threshold is introduced.
    """
    rows = []
    for key, group in actions.groupby(KEY, sort=True):
        records = list(group.sort_values("event_index").itertuples(index=False))
        for kind, predicate in (
            ("positive", lambda dx: dx > 0),
            ("negative", lambda dx: dx < 0),
            ("nonpositive", lambda dx: dx <= 0),
        ):
            current = []

            def emit(run):
                if not run or (
                    kind == "nonpositive" and not any(r.delta_x < 0 for r in run)
                ):
                    return
                first, last = run[0], run[-1]
                rows.append(
                    {
                        **dict(zip(KEY, key)),
                        "run_kind": kind,
                        "first_event_index": first.event_index,
                        "last_event_index": last.event_index,
                        "action_count": len(run),
                        "negative_action_count": sum(r.delta_x < 0 for r in run),
                        "cumulative_x_component": sum(abs(r.delta_x) for r in run),
                        "maximum_single_component": max(abs(r.delta_x) for r in run),
                        "timestamp_span_seconds": last.period_seconds
                        - first.period_seconds,
                        "start_x": first.start_x,
                        "end_x": last.end_x,
                        "intervening_context_events": last.event_position
                        - first.event_position
                        + 1
                        - len(run),
                    }
                )

            for r in records:
                if predicate(r.delta_x):
                    current.append(r)
                else:
                    emit(current)
                    current = []
            emit(current)
    return pd.DataFrame(
        rows,
        columns=[
            *KEY,
            "run_kind",
            "first_event_index",
            "last_event_index",
            "action_count",
            "negative_action_count",
            "cumulative_x_component",
            "maximum_single_component",
            "timestamp_span_seconds",
            "start_x",
            "end_x",
            "intervening_context_events",
        ],
    )


def recovery_inventory(path):
    """Nonoverlapping excursions below the running peak; right-censored if unseen.

    Recovery is first later observed vertex >= the pre-decline peak. Ties update
    the reference to its most recent observation. No reset magnitude/duration.
    Time is measured between source action-start timestamps, not arrival times.
    """
    rows = []
    for key, group in path.groupby(KEY, sort=True):
        records = list(group.itertuples(index=False))
        peak = records[0]
        active = None
        for i, r in enumerate(records):
            if active is None:
                if r.attacking_x >= peak.attacking_x:
                    peak = r
                else:
                    active = {"peak": peak, "onset": r, "trough": r, "start": i}
            if active is not None:
                if r.attacking_x < active["trough"].attacking_x:
                    active["trough"] = r
                recovered = r.attacking_x >= active["peak"].attacking_x
                if recovered or i == len(records) - 1:
                    prior, onset, trough = (
                        active["peak"],
                        active["onset"],
                        active["trough"],
                    )
                    rows.append(
                        {
                            **dict(zip(KEY, key)),
                            "peak_event_index": prior.event_index,
                            "onset_event_index": onset.event_index,
                            "trough_event_index": trough.event_index,
                            "last_observed_event_index": r.event_index,
                            "previous_peak_x": prior.attacking_x,
                            "trough_x": trough.attacking_x,
                            "retreat_size": prior.attacking_x - trough.attacking_x,
                            "recovered_previous_peak": recovered,
                            "new_peak_reached": any(
                                t.attacking_x > prior.attacking_x
                                for t in records[active["start"] :]
                            ),
                            "time_to_recover_previous_peak": r.period_seconds
                            - prior.period_seconds
                            if recovered
                            else np.nan,
                            "events_to_recover_previous_peak": r.event_position
                            - prior.event_position
                            if recovered
                            else np.nan,
                            "observed_followup_seconds": r.period_seconds
                            - prior.period_seconds,
                            "time_peak_to_trough": trough.period_seconds
                            - prior.period_seconds,
                            "time_trough_to_recovery": r.period_seconds
                            - trough.period_seconds
                            if recovered
                            else np.nan,
                            "censored_at_last_safe_observation": not recovered,
                        }
                    )
                    active = None
                    peak = r if recovered else peak
    return pd.DataFrame(
        rows,
        columns=[
            *KEY,
            "peak_event_index",
            "onset_event_index",
            "trough_event_index",
            "last_observed_event_index",
            "previous_peak_x",
            "trough_x",
            "retreat_size",
            "recovered_previous_peak",
            "new_peak_reached",
            "time_to_recover_previous_peak",
            "events_to_recover_previous_peak",
            "observed_followup_seconds",
            "time_peak_to_trough",
            "time_trough_to_recovery",
            "censored_at_last_safe_observation",
        ],
    ).astype(
        {
            "recovered_previous_peak": bool,
            "new_peak_reached": bool,
            "censored_at_last_safe_observation": bool,
        }
    )


def progression_possessions(stream, actions, path, runs, recoveries):
    p = possession_inventory(stream).drop(columns=["has_goal"])
    rows = []
    paths = {key: g for key, g in path.groupby(KEY, sort=True)}
    for key, g in actions.groupby(KEY, sort=True):
        g = g.sort_values("event_index")
        f, b = g.delta_x.clip(lower=0).sum(), -g.delta_x.clip(upper=0).sum()
        vertices = paths[key]
        rows.append(
            {
                **dict(zip(KEY, key)),
                "safe_action_count": len(g),
                "first_safe_action_x": g.start_x.iloc[0],
                "last_safe_action_x": g.end_x.iloc[-1],
                "max_attacking_x_reached": vertices.attacking_x.max(),
                "min_attacking_x_reached": vertices.attacking_x.min(),
                "net_x_progression": g.end_x.iloc[-1] - g.start_x.iloc[0],
                "cumulative_forward_x": f,
                "cumulative_backward_x": b,
                "forward_to_backward_ratio": f / b if b > 0 else np.nan,
                "backward_denominator_zero": b == 0,
                "maximum_retreat_from_peak": vertices.retreat_from_peak.max(),
                "maximum_single_backward_action": max(0, -g.delta_x.min()),
                "positive_action_count": int(g.delta_x.gt(0).sum()),
                "negative_action_count": int(g.delta_x.lt(0).sum()),
                "zero_action_count": int(g.delta_x.eq(0).sum()),
                "inter_action_x_jump_sum": float(
                    (g.start_x.iloc[1:].to_numpy() - g.end_x.iloc[:-1].to_numpy()).sum()
                ),
            }
        )
    columns = [
        *KEY,
        "safe_action_count",
        "first_safe_action_x",
        "last_safe_action_x",
        "max_attacking_x_reached",
        "min_attacking_x_reached",
        "net_x_progression",
        "cumulative_forward_x",
        "cumulative_backward_x",
        "forward_to_backward_ratio",
        "backward_denominator_zero",
        "maximum_retreat_from_peak",
        "maximum_single_backward_action",
        "positive_action_count",
        "negative_action_count",
        "zero_action_count",
        "inter_action_x_jump_sum",
    ]
    p = p.merge(
        pd.DataFrame(rows, columns=columns), on=KEY, how="left", validate="one_to_one"
    )
    p["safe_action_count"] = p.safe_action_count.fillna(0).astype(int)
    for kind in ("positive", "negative", "nonpositive"):
        sub = runs[runs.run_kind.eq(kind)]
        agg = (
            sub.groupby(KEY)
            .action_count.max()
            .rename(f"maximum_{kind}_run_actions")
            .reset_index()
        )
        p = p.merge(agg, on=KEY, how="left", validate="one_to_one")
        p[f"maximum_{kind}_run_actions"] = (
            p[f"maximum_{kind}_run_actions"].fillna(0).astype(int)
        )
    agg = (
        recoveries.groupby(KEY)
        .agg(
            retreat_excursion_count=("retreat_size", "size"),
            observed_recovery_count=("recovered_previous_peak", "sum"),
        )
        .reset_index()
    )
    p = p.merge(agg, on=KEY, how="left", validate="one_to_one")
    for col in ("retreat_excursion_count", "observed_recovery_count"):
        p[col] = p[col].fillna(0).astype(int)
    return p


def temporal_diagnostics(stream, actions):
    rows = []
    pair_tables = {}
    for label, events in (
        ("full_events", stream),
        ("safe_actions", actions),
        ("validated_anchors", stream[stream.validated_anchor]),
    ):
        ordered = events.sort_values([*KEY, "event_index"])
        dt = ordered.groupby(KEY).period_seconds.diff()
        pairs = ordered.loc[dt.notna(), KEY + ["event_index"]].copy()
        pairs["elapsed_seconds"] = dt.dropna()
        pair_tables[label] = pairs
        values = pairs.elapsed_seconds
        rows.append(
            {
                "layer": label,
                **describe(values),
                **{
                    f"pct_above_{n}_seconds": 100 * values.gt(n).mean()
                    for n in (3, 5, 10, 15)
                },
            }
        )
    return pd.DataFrame(rows), pair_tables


def representative_manifest(p):
    """Top 20 in each extreme inventory; separate bounded 26-case review manifest."""
    ranked = {}
    for col in (
        "possession_duration_seconds",
        "total_event_count",
        "validated_spatial_anchor_count",
        "maximum_retreat_from_peak",
    ):
        for rank, (_, r) in enumerate(
            p.sort_values(
                [col, *KEY], ascending=[False, *([True] * len(KEY))], na_position="last"
            )
            .head(20)
            .iterrows(),
            1,
        ):
            key = tuple(r[k] for k in KEY)
            ranked.setdefault(key, []).append(f"{col}:rank_{rank}")
    extremes = p.merge(
        pd.DataFrame(
            [
                {**dict(zip(KEY, k)), "ranking_reasons": ";".join(v)}
                for k, v in ranked.items()
            ]
        ),
        on=KEY,
        validate="one_to_one",
    )
    usable = p.safe_action_count.gt(0)
    conditions = {
        "nonnegative_action_vectors": usable
        & p.negative_action_count.eq(0)
        & p.positive_action_count.ge(2),
        "one_small_backward_action": p.negative_action_count.eq(1)
        & p.maximum_single_backward_action.le(5)
        & p.cumulative_forward_x.ge(p.cumulative_forward_x.quantile(0.75)),
        "large_single_backward_action": p.maximum_single_backward_action.ge(
            p.maximum_single_backward_action.quantile(0.95)
        ),
        "multiple_backward_actions": p.maximum_negative_run_actions.ge(3),
        "retreat_then_observed_recovery": p.observed_recovery_count.gt(0),
        "multiple_peak_excursions": p.retreat_excursion_count.ge(
            p.retreat_excursion_count.quantile(0.95)
        ),
        "short_high_net_rate": usable
        & p.possession_duration_seconds.gt(0)
        & p.possession_duration_seconds.le(p.possession_duration_seconds.quantile(0.25))
        & (p.net_x_progression / p.possession_duration_seconds.replace(0, np.nan)).ge(
            (
                p.net_x_progression / p.possession_duration_seconds.replace(0, np.nan)
            ).quantile(0.90)
        ),
        "shot_context": p.has_shot,
        "many_anchors": p.validated_spatial_anchor_count.ge(
            p.validated_spatial_anchor_count.quantile(0.95)
        ),
        "sparse_anchors": p.validated_spatial_anchor_count.le(1),
        "net_cumulative_disagreement": p.inter_action_x_jump_sum.abs().ge(
            p.inter_action_x_jump_sum.abs().quantile(0.95)
        ),
    }
    chosen = {}
    for reason, mask in conditions.items():
        for _, r in p[mask].sort_values(KEY).head(2).iterrows():
            key = tuple(r[k] for k in KEY)
            chosen.setdefault(key, []).append(reason)
    # Ensure the four extreme leaders are explicitly inspectable, then fill to 26.
    for col in (
        "possession_duration_seconds",
        "total_event_count",
        "validated_spatial_anchor_count",
        "maximum_retreat_from_peak",
    ):
        r = p.sort_values([col, *KEY], ascending=[False, *([True] * len(KEY))]).iloc[0]
        chosen.setdefault(tuple(r[k] for k in KEY), []).append(f"maximum_{col}")
    for _, r in extremes.sort_values(
        ["possession_duration_seconds", *KEY], ascending=[False, *([True] * len(KEY))]
    ).iterrows():
        if len(chosen) >= 26:
            break
        chosen.setdefault(tuple(r[k] for k in KEY), []).append("long_possession_review")
    manifest = p.merge(
        pd.DataFrame(
            [
                {**dict(zip(KEY, k)), "selection_reasons": ";".join(v)}
                for k, v in chosen.items()
            ]
        ),
        on=KEY,
        validate="one_to_one",
    )
    return extremes, manifest


def summarize_progression(stream, signals):
    """Return compact derived evidence and bounded review timelines, no raw corpus."""
    actions = stream[stream.safe_action].copy()
    path = action_path(actions)
    runs = progression_runs(actions)
    recoveries = recovery_inventory(path)
    p = progression_possessions(stream, actions, path, runs, recoveries)
    tables = {
        "possession_progression_summary": p,
        "retreat_from_peak": path,
        "run_inventory": runs,
        "recovery_inventory": recoveries,
    }
    tables["action_scope_inventory"] = (
        stream[stream.action_candidate]
        .groupby(
            ["event_type", "action_status", "explicit_vector_available"], dropna=False
        )
        .agg(event_count=("event_index", "size"), match_count=("match_id", "nunique"))
        .reset_index()
    )
    tables["action_displacement_summary"] = pd.DataFrame(
        [
            {
                "event_type": label,
                **describe(g.delta_x),
                "pct_positive": 100 * g.delta_x.gt(0).mean(),
                "pct_zero": 100 * g.delta_x.eq(0).mean(),
                "pct_negative": 100 * g.delta_x.lt(0).mean(),
            }
            for label, g in [
                ("Pass", actions[actions.event_type.eq("Pass")]),
                ("Carry", actions[actions.event_type.eq("Carry")]),
                ("Pass + Carry", actions),
            ]
        ]
    )
    bins = pd.cut(
        actions.delta_x,
        [-np.inf, -20, -10, 0, 10, 20, np.inf],
        right=False,
        labels=["dx < -20", "[-20,-10)", "[-10,0)", "[0,10)", "[10,20)", "dx >= 20"],
    )
    bin_table = (
        actions.assign(displacement_bin=bins)
        .groupby(["event_type", "displacement_bin"], observed=False)
        .size()
        .rename("count")
        .reset_index()
    )
    bin_table["percentage"] = (
        100
        * bin_table["count"]
        / bin_table.groupby("event_type")["count"].transform("sum")
    )
    tables["action_displacement_bins"] = bin_table
    metrics = [
        "net_x_progression",
        "cumulative_forward_x",
        "cumulative_backward_x",
        "forward_to_backward_ratio",
        "maximum_retreat_from_peak",
        "maximum_single_backward_action",
        "inter_action_x_jump_sum",
        "possession_duration_seconds",
        "total_event_count",
        "validated_spatial_anchor_count",
        "safe_action_count",
    ]
    tables["possession_distributions"] = pd.DataFrame(
        [
            {
                "measure": c,
                **describe(p[c]),
                "missing_possessions": int(p[c].isna().sum()),
            }
            for c in metrics
        ]
    )
    tables["retreat_distributions"] = pd.DataFrame(
        [
            {"population": label, **describe(g)}
            for label, g in [
                ("all_action_vertices", path.retreat_from_peak),
                ("possession_maximum", p.maximum_retreat_from_peak),
            ]
        ]
    )
    tables["retreat_threshold_inventory"] = pd.DataFrame(
        [
            {
                "retreat_at_least": n,
                "possessions": int(p.maximum_retreat_from_peak.ge(n).sum()),
                "pct_all_possessions": 100 * p.maximum_retreat_from_peak.ge(n).mean(),
                "pct_measurable_possessions": 100
                * p.loc[p.safe_action_count.gt(0), "maximum_retreat_from_peak"]
                .ge(n)
                .mean(),
            }
            for n in RETREAT_SWEEP
        ]
    )
    depths = []
    for boundary in (30, 60, 80, 100):
        maxima = []
        for _, g in path.groupby(KEY, sort=True):
            reached = g.running_peak_x.ge(boundary)
            if reached.any():
                maxima.append(g.loc[reached, "retreat_from_peak"].max())
        depths.append({"first_reached_x_at_least": boundary, **describe(maxima)})
    tables["retreat_after_depth_inventory"] = pd.DataFrame(depths)
    tables["run_statistics"] = pd.DataFrame(
        [
            {"run_kind": kind, "measure": measure, **describe(g[measure])}
            for kind, g in runs.groupby("run_kind")
            for measure in [
                "action_count",
                "cumulative_x_component",
                "timestamp_span_seconds",
                "maximum_single_component",
                "start_x",
                "end_x",
                "intervening_context_events",
            ]
        ]
    )
    tables["recovery_summary"] = pd.DataFrame(
        [
            {
                "recovered_previous_peak": recovered,
                "excursion_count": len(g),
                "new_peak_count": int(g.new_peak_reached.sum()),
                "measure": measure,
                **describe(g[measure]),
            }
            for recovered, g in recoveries.groupby("recovered_previous_peak")
            for measure in [
                "retreat_size",
                "time_to_recover_previous_peak",
                "events_to_recover_previous_peak",
                "observed_followup_seconds",
                "time_peak_to_trough",
                "time_trough_to_recovery",
            ]
        ]
    )
    tables["temporal_gap_summary"], pairs = temporal_diagnostics(stream, actions)
    # Retain type/team distinction in anchor-coordinate differences. Mixed actor
    # locations are not the action path used for territorial retreat diagnostics.
    anchors = stream[stream.validated_anchor].sort_values([*KEY, "event_index"]).copy()
    anchors["previous_anchor_type"] = anchors.groupby(KEY).event_type.shift()
    anchors["previous_event_team_id"] = anchors.groupby(KEY).event_team_id.shift()
    anchors["anchor_delta_x"] = anchors.groupby(KEY).anchor_x.diff()
    anchors["previous_event_team_id"] = anchors.previous_event_team_id.astype("Int64")
    tables["spatial_anchor_displacement_summary"] = pd.DataFrame(
        [
            {
                "previous_anchor_type": key[0],
                "next_anchor_type": key[1],
                "previous_event_team_id": key[2],
                "next_event_team_id": key[3],
                **describe(g.anchor_delta_x),
            }
            for key, g in anchors.dropna(subset=["previous_anchor_type"]).groupby(
                [
                    "previous_anchor_type",
                    "event_type",
                    "previous_event_team_id",
                    "event_team_id",
                ]
            )
        ]
    )
    field_rows = []
    for label, g in actions.assign(
        depth_bin=pd.cut(actions.start_x, DEPTH_EDGES, labels=DEPTH_LABELS, right=False)
    ).groupby("depth_bin", observed=False):
        field_rows.append(
            {
                "starting_x_band": str(label),
                **describe(g.delta_x),
                "pct_backward": 100 * g.delta_x.lt(0).mean(),
                **{
                    f"backward_at_least_{n}": int(g.delta_x.le(-n).sum())
                    for n in (5, 15, 30)
                },
            }
        )
    tables["field_position_summary"] = pd.DataFrame(field_rows)
    tables["duration_landmarks"] = pd.DataFrame(
        [
            {
                "duration_above_seconds": n,
                "possessions": int(p.possession_duration_seconds.gt(n).sum()),
                "percentage": 100 * p.possession_duration_seconds.gt(n).mean(),
            }
            for n in (30, 60, 90, 120)
        ]
    )
    # Provider tokens can overlap. Count literal source signals, not invented labels.
    tables["football_termination_inventory"] = (
        signals.groupby(
            [
                "signal",
                "event_type",
                "event_team_id",
                "next_event_type",
                "next_possession_team_id",
            ],
            dropna=False,
        )
        .agg(event_count=("event_index", "size"), match_count=("match_id", "nunique"))
        .reset_index()
    )
    signal_sets = {}

    def register(name, setting, frame):
        signal_sets[(name, str(setting))] = set(
            frame[KEY].itertuples(index=False, name=None)
        )

    register("provider_group_final_record", "all", p)
    for sig in sorted(signals.signal.unique()):
        if sig != "provider_group_final_record":
            register("provider_field", sig, signals[signals.signal.eq(sig)])
    for n in RETREAT_SWEEP:
        register("single_backward_action", n, actions[actions.delta_x.le(-n)])
        register(
            "cumulative_retreat_from_peak", n, p[p.maximum_retreat_from_peak.ge(n)]
        )
    for kind in ("negative", "nonpositive"):
        for n in (2, 3, 4, 5):
            register(
                f"{kind}_run_actions",
                n,
                runs[runs.run_kind.eq(kind) & runs.action_count.ge(n)],
            )
    for layer, g in pairs.items():
        for n in (3, 5, 10, 15):
            register(f"{layer}_gap_above_seconds", n, g[g.elapsed_seconds.gt(n)])
    for n in (3, 5, 10, 15, 30):
        register(
            "observed_peak_recovery_time_above_seconds",
            n,
            recoveries[
                recoveries.recovered_previous_peak
                & recoveries.time_to_recover_previous_peak.gt(n)
            ],
        )
        register(
            "unrecovered_followup_above_seconds",
            n,
            recoveries[
                ~recoveries.recovered_previous_peak
                & recoveries.observed_followup_seconds.gt(n)
            ],
        )
    register(
        "observed_recovery_after_retreat",
        "any",
        recoveries[recoveries.recovered_previous_peak],
    )
    tables["candidate_reset_signal_inventory"] = pd.DataFrame(
        [
            {
                "candidate_signal": name,
                "descriptive_setting": setting,
                "possession_count": len(keys),
                "denominator": len(p),
                "percentage": 100 * len(keys) / len(p),
            }
            for (name, setting), keys in signal_sets.items()
        ]
    )
    # All cross-family settings are reported; no preferred setting or joint score.
    sweep_sets = {
        k: v
        for k, v in signal_sets.items()
        if k[0]
        in (
            "single_backward_action",
            "cumulative_retreat_from_peak",
            "negative_run_actions",
            "safe_actions_gap_above_seconds",
            "observed_peak_recovery_time_above_seconds",
        )
    }
    tables["candidate_signal_overlap"] = pd.DataFrame(
        [
            {
                "signal_a": a[0],
                "setting_a": a[1],
                "signal_b": b[0],
                "setting_b": b[1],
                "both_possessions": len(sa & sb),
                "either_possessions": len(sa | sb),
                "denominator": len(p),
            }
            for (a, sa), (b, sb) in combinations(sweep_sets.items(), 2)
            if a[0] != b[0]
        ]
    )
    tables["candidate_review_possessions"], tables["representative_possessions"] = (
        representative_manifest(p)
    )
    selected = stream.merge(
        tables["representative_possessions"][KEY + ["selection_reasons"]],
        on=KEY,
        validate="many_to_one",
    )
    end_path = path[path.vertex.eq("end")][
        KEY + ["event_index", "running_peak_x", "retreat_from_peak"]
    ]
    selected = selected.merge(
        end_path, on=KEY + ["event_index"], how="left", validate="one_to_one"
    )
    tables["representative_timelines"] = selected[
        [
            *KEY,
            "event_id",
            "event_index",
            "elapsed_possession_time",
            "event_type",
            "event_team_id",
            "timestamp",
            "safe_action",
            "action_status",
            "start_x",
            "end_x",
            "delta_x",
            "anchor_x",
            "running_peak_x",
            "retreat_from_peak",
            "validated_anchor",
            "semantics_status",
            "selection_reasons",
        ]
    ]
    tables["representative_path_vertices"] = path.merge(
        tables["representative_possessions"][KEY], on=KEY, validate="many_to_one"
    )
    tables["representative_termination_context"] = signals.merge(
        tables["representative_possessions"][KEY], on=KEY, validate="many_to_one"
    )
    tables["data_quality_summary"] = pd.DataFrame(
        [
            {
                "full_events_retained": len(stream),
                "safe_actions": len(actions),
                "possessions_without_safe_actions": int(
                    p.safe_action_count.eq(0).sum()
                ),
                "explicit_own_vectors_excluded_by_scope": int(
                    (
                        stream.action_candidate
                        & stream.explicit_vector_available
                        & ~stream.validated_anchor
                    ).sum()
                ),
                "validated_own_vectors_missing_endpoint": int(
                    (
                        stream.action_candidate
                        & stream.validated_anchor
                        & ~stream.explicit_vector_available
                    ).sum()
                ),
                "safe_actions_with_oob_coordinates": int(
                    (
                        actions[["start_x", "end_x"]].lt(0).any(axis=1)
                        | actions[["start_x", "end_x"]].gt(120).any(axis=1)
                        | actions[["start_y", "end_y"]].lt(0).any(axis=1)
                        | actions[["start_y", "end_y"]].gt(80).any(axis=1)
                    ).sum()
                ),
                "opponent_validated_anchors": int(
                    (stream.validated_anchor & stream.event_team_id.ne(TEAM_ID)).sum()
                ),
                "zero_backward_denominators": int(
                    p.backward_denominator_zero.fillna(False).sum()
                ),
                "zero_action_time_gaps": int(
                    pairs["safe_actions"].elapsed_seconds.eq(0).sum()
                ),
                "anchor_gap_intervals": len(pairs["validated_anchors"]),
            }
        ]
    )
    return tables


def run_progression_diagnostics(output_dir, progress=print):
    """One pinned retrieval per match; no source cache or prior-output mutation."""
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
        raise ValueError("Expected 34 unique pinned matches")
    streams, signals, inventory = [], [], []
    for i, match in enumerate(matches, 1):
        mid = match["match_id"]
        events, frames = loader.load_events(mid), loader.load_360(mid)
        full, selected, sig = enrich_match(
            match, events, frames, source_revision=loader.STATSBOMB_REVISION
        )
        streams.append(selected)
        signals.append(sig)
        inventory.append(
            {
                "match_id": mid,
                "all_events": len(full),
                "all_linked_frames": int(full.linked_360.sum()),
                "all_validated_frames": int(full.validated_anchor.sum()),
                "all_unsupported_frames": int(
                    (full.linked_360 & ~full.validated_anchor).sum()
                ),
                "source_events_url": f"{loader.BASE_URL}/events/{mid}.json",
                "source_frames_url": f"{loader.BASE_URL}/three-sixty/{mid}.json",
            }
        )
        del events, frames, full
        progress(
            f"Phase 3A-1 {i}/34: {mid}; {int(selected.safe_action.sum())} safe action vectors"
        )
    stream = pd.concat(streams, ignore_index=True)
    inventory = pd.DataFrame(inventory)
    p = possession_inventory(stream)
    validate_locked_reconciliation(
        loader.STATSBOMB_REVISION,
        tuple(
            int(inventory[c].sum())
            for c in [
                "all_events",
                "all_linked_frames",
                "all_validated_frames",
                "all_unsupported_frames",
            ]
        ),
        (
            len(p),
            len(stream),
            int(stream.linked_360.sum()),
            int(stream.validated_anchor.sum()),
            int((stream.linked_360 & ~stream.validated_anchor).sum()),
        ),
    )
    gaps = anchor_gaps(stream)
    if (
        len(gaps) != 43431
        or not np.isclose(gaps.elapsed_seconds.median(), 1.103)
        or not np.isclose(gaps.elapsed_seconds.quantile(0.9), 3.214)
    ):
        raise ValueError("Phase 2C-2 anchor-gap reconciliation failed")
    tables = summarize_progression(stream, pd.concat(signals, ignore_index=True))
    tables["source_inventory"] = inventory
    tables["run_summary"] = pd.DataFrame(
        [
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "phase3a1_status": STATUS,
                "phase2c_status": PHASE2C_STATUS,
                "matches": len(matches),
                "possession_groups": len(p),
                "retained_events": len(stream),
                "validated_anchors": int(stream.validated_anchor.sum()),
                "anchor_gap_intervals": len(gaps),
                "safe_action_vectors": int(stream.safe_action.sum()),
                "raw_persisted": False,
                "pandas_version": pd.__version__,
                "numpy_version": np.__version__,
            }
        ]
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table["statsbomb_revision"] = loader.STATSBOMB_REVISION
        table.to_csv(output_dir / f"phase3a1_{name}.csv", index=False)
    return tables

"""Bounded Phase 3A-2A review assembly. Sampling never defines segmentation.

Human columns are deliberately empty. All geometry and coordinates delegate to
the locked implementations; only scalar derivatives are persisted.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import TEAM_ID, field, points
from leverkusen.sequences.progression_diagnostics import (
    DEPTH_EDGES,
    DEPTH_LABELS,
    action_path,
    enrich_match,
    progression_runs,
    provider_signals,
)
from leverkusen.sequences.readiness import KEY
from leverkusen.spatial.geometry import METRICS, frame_geometry, valid_point
from leverkusen.spatial.orientation import (
    VALIDATED,
    normalize_attacking_point,
    point_team_label,
)

STATUS = "REVIEW PACK READY — HUMAN LABELING PENDING"
HUMAN_COLUMNS = [
    "review_label",
    "review_boundary_event_index",
    "review_boundary_time",
    "review_confidence",
    "review_notes",
]
LABELS = {
    "CONTINUE": "The attacking phase appears continuous despite backward/lateral movement.",
    "POSSIBLE_RESET": "Evidence suggests the phase may have reset, but is not sufficiently clear.",
    "CLEAR_RESET": "Possession continues, but the prior attacking phase appears abandoned/reorganized before renewed progression.",
    "HARD_BOUNDARY": "A football event/context provides a very strong candidate phase termination/reset.",
    "AMBIGUOUS": "Available event/spatial evidence does not support a confident judgment.",
}
RESTARTS = ("Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off")
# Presentation order and explicit REVIEW SAMPLING CRITERIA, never approval gates.
CATEGORIES = [
    (
        "nearly_monotonic",
        ">=2 positive actions; full safe path maximum retreat <=5",
        "01_forward_contrasts",
    ),
    (
        "one_small_backward",
        "one negative action <=5; cumulative forward >=30",
        "01_forward_contrasts",
    ),
    (
        "large_single_backward",
        "maximum single backward action >=20",
        "02_single_action_retreat",
    ),
    (
        "single_without_extended_run",
        "single backward >=20; longest strict negative run=1",
        "02_single_action_retreat",
    ),
    (
        "gradual_multi_action",
        "strict negative run >=3; cumulative backward >=15; largest action <20",
        "03_multi_action_retreat",
    ),
    (
        "high_backward_without_large_action",
        "cumulative backward >=40; largest single backward <20",
        "03_multi_action_retreat",
    ),
    (
        "immediate_observed_recovery",
        "observed record-peak recovery span <=3 seconds",
        "04_recovery",
    ),
    (
        "delayed_observed_recovery",
        "observed record-peak recovery span >15 seconds",
        "04_recovery",
    ),
    (
        "unrecovered_observation",
        "censored record-peak excursion; no assertion about unseen recovery",
        "04_recovery",
    ),
    (
        "retreat_then_renewed_progression",
        "observed excursion followed by a higher safe vertex",
        "04_recovery",
    ),
    ("corner_started", "first own Pass/Carry provider type Corner", "05_set_pieces"),
    (
        "free_kick_started",
        "first own Pass/Carry provider type Free Kick",
        "05_set_pieces",
    ),
    ("throw_in_restart", "literal provider Throw-in context", "05_set_pieces"),
    ("out_context", "literal out=True in parent", "05_set_pieces"),
    (
        "shot_context",
        "Shot event type in parent; no Shot outcome used",
        "06_shot_context",
    ),
    (
        "shot_then_same_parent_actions",
        "own Shot then own Pass/Carry later in same provider parent; source control unverified",
        "06_shot_context",
    ),
    (
        "multiple_local_peaks_long",
        ">60 seconds; >=3 strict local peak plateaus in safe vertex order",
        "07_long_complex",
    ),
    ("very_long", ">120 seconds between first/last event starts", "07_long_complex"),
    ("dense_anchors", ">=50 validated anchors", "07_long_complex"),
    (
        "advanced_origin_retreat",
        "record-peak origin >=100; excursion magnitude 20–40",
        "08_borderline_context",
    ),
    (
        "deeper_origin_retreat",
        "record-peak origin <=60; excursion magnitude 20–40",
        "08_borderline_context",
    ),
    (
        "short_fast",
        "0<duration<=10 seconds; net x/duration >=3",
        "08_borderline_context",
    ),
    (
        "opponent_pressure_anchor",
        "validated opponent Pressure exists; actor location is not ball",
        "08_borderline_context",
    ),
    ("sparse_anchors", "<=1 validated anchor", "08_borderline_context"),
    (
        "circulation_for_review",
        "5<=maximum retreat<=25; >=2 positive and >=2 negative actions; duration<=60",
        "08_borderline_context",
    ),
]


def keyed(table, key):
    return table.loc[table[KEY].eq(list(key)).all(axis=1)].copy()


def read_prior(directory, name):
    table = pd.read_csv(Path(directory) / f"phase3a1_{name}.csv")
    if table.empty or not table.statsbomb_revision.eq(loader.STATSBOMB_REVISION).all():
        raise ValueError(f"Missing or different pinned Phase 3A-1 evidence: {name}")
    return table


def complete_timeline(stream, events):
    """Keep every full-context row; do not forward-fill unobserved spatial state."""
    result = (
        stream.copy(deep=True).sort_values(KEY + ["event_index"]).reset_index(drop=True)
    )
    source = {e["index"]: e for e in events}
    result["player_name"] = [
        field(source[i], "player", "name") for i in result.event_index
    ]
    result["event_team"] = [
        field(source[i], "team", "name") or str(source[i]["team"]["id"])
        for i in result.event_index
    ]
    result["provider_context"] = [
        ";".join(provider_signals(source[i])) for i in result.event_index
    ]
    result["restart_context"] = [
        field(source[i].get("pass", {}), "type", "name")
        if field(source[i].get("pass", {}), "type", "name") in RESTARTS
        else ""
        for i in result.event_index
    ]
    result["spatial_state_status"] = np.select(
        [result.validated_anchor, result.linked_360],
        ["validated_spatial_anchor", "linked_360_unsupported_semantics"],
        default="no_360_frame",
    )
    result["prior_event_gap_seconds"] = result.groupby(KEY).period_seconds.diff()
    path = action_path(result[result.safe_action])
    ends = path[path.vertex.eq("end")][
        KEY + ["event_index", "running_peak_x", "retreat_from_peak"]
    ]
    result = result.merge(
        ends, on=KEY + ["event_index"], how="left", validate="one_to_one"
    )
    runs = progression_runs(result[result.safe_action])
    for kind in ("positive", "negative", "nonpositive"):
        result[f"{kind}_run_id"] = ""
        result[f"{kind}_run_length_so_far"] = np.nan
        for num, run in enumerate(
            runs[runs.run_kind.eq(kind)].itertuples(index=False), 1
        ):
            mask = result[KEY].eq([getattr(run, k) for k in KEY]).all(axis=1)
            mask &= result.safe_action & result.event_index.between(
                run.first_event_index, run.last_event_index
            )
            result.loc[mask, f"{kind}_run_id"] = f"{kind}_{num:04}"
            result.loc[mask, f"{kind}_run_length_so_far"] = np.arange(1, mask.sum() + 1)
    # Goal and success fields from readiness must not enter the review artifacts.
    return result.drop(columns=["is_goal"], errors="ignore")


def local_peak_count(path):
    x = path.attacking_x
    x = x[x.ne(x.shift())].to_numpy()  # Equal plateaus collapse for this count only.
    return int(((x[1:-1] > x[:-2]) & (x[1:-1] > x[2:])).sum())


def category_matches(summary, timeline, recoveries):
    """Descriptive pool coverage; absent clean examples remain absent."""
    s = summary
    actions = timeline[timeline.safe_action]
    path = action_path(actions)
    own = timeline[
        timeline.event_team_id.eq(TEAM_ID) & timeline.event_type.isin(["Pass", "Carry"])
    ]
    first_restart = own.restart_context.iloc[0] if len(own) else ""
    observed = recoveries[recoveries.recovered_previous_peak]
    shot_indices = timeline.loc[
        timeline.event_type.eq("Shot") & timeline.event_team_id.eq(TEAM_ID),
        "event_index",
    ]
    second = any(own.event_index.gt(i).any() for i in shot_indices)
    retreat_band = recoveries.retreat_size.between(20, 40)
    return {
        "nearly_monotonic": s.positive_action_count >= 2
        and s.maximum_retreat_from_peak <= 5,
        "one_small_backward": s.negative_action_count == 1
        and s.maximum_single_backward_action <= 5
        and s.cumulative_forward_x >= 30,
        "large_single_backward": s.maximum_single_backward_action >= 20,
        "single_without_extended_run": s.maximum_single_backward_action >= 20
        and s.maximum_negative_run_actions == 1,
        "gradual_multi_action": s.maximum_negative_run_actions >= 3
        and s.cumulative_backward_x >= 15
        and s.maximum_single_backward_action < 20,
        "high_backward_without_large_action": s.cumulative_backward_x >= 40
        and s.maximum_single_backward_action < 20,
        "immediate_observed_recovery": observed.time_to_recover_previous_peak.le(
            3
        ).any(),
        "delayed_observed_recovery": observed.time_to_recover_previous_peak.gt(
            15
        ).any(),
        "unrecovered_observation": recoveries.censored_at_last_safe_observation.any(),
        "retreat_then_renewed_progression": recoveries.new_peak_reached.any(),
        "corner_started": first_restart == "Corner",
        "free_kick_started": first_restart == "Free Kick",
        "throw_in_restart": timeline.restart_context.eq("Throw-in").any(),
        "out_context": timeline.provider_context.str.contains(
            "out:true", regex=False
        ).any(),
        "shot_context": timeline.event_type.eq("Shot").any(),
        "shot_then_same_parent_actions": second,
        "multiple_local_peaks_long": s.possession_duration_seconds > 60
        and local_peak_count(path) >= 3,
        "very_long": s.possession_duration_seconds > 120,
        "dense_anchors": s.validated_spatial_anchor_count >= 50,
        "advanced_origin_retreat": (
            retreat_band & recoveries.previous_peak_x.ge(100)
        ).any(),
        "deeper_origin_retreat": (
            retreat_band & recoveries.previous_peak_x.le(60)
        ).any(),
        "short_fast": 0 < s.possession_duration_seconds <= 10
        and s.net_x_progression / s.possession_duration_seconds >= 3,
        "opponent_pressure_anchor": (
            timeline.validated_anchor
            & timeline.event_team_id.ne(TEAM_ID)
            & timeline.event_type.eq("Pressure")
        ).any(),
        "sparse_anchors": s.validated_spatial_anchor_count <= 1,
        "circulation_for_review": 5 <= s.maximum_retreat_from_peak <= 25
        and s.positive_action_count >= 2
        and s.negative_action_count >= 2
        and s.possession_duration_seconds <= 60,
    }


def select_cases(pool, prior_keys, limit=28):
    """First key per category, preferring prior cases; fill with unused prior keys."""
    if pool[KEY].duplicated().any():
        raise ValueError("Duplicate possession key")
    ordered = pool.copy()
    ordered["prior_case"] = [
        tuple(r) in prior_keys for r in ordered[KEY].itertuples(index=False, name=None)
    ]
    ordered = ordered.sort_values(
        ["prior_case"] + KEY, ascending=[False] + [True] * len(KEY)
    )
    selected = []
    for category, _, _ in CATEGORIES:
        choices = ordered[ordered[category]]
        if len(choices):
            key = tuple(choices.iloc[0][KEY])
            if key not in selected:
                selected.append(key)
    for key in ordered[KEY].itertuples(index=False, name=None):
        if len(selected) >= limit:
            break
        if key not in selected:
            selected.append(key)
    if len(selected) > limit:
        raise ValueError("Coverage requires more cases than the review limit")
    result = pd.DataFrame(selected, columns=KEY).merge(
        pool, on=KEY, validate="one_to_one"
    )
    result["selection_reason"] = [
        ";".join(c for c, _, _ in CATEGORIES if row[c]) for _, row in result.iterrows()
    ]
    result["review_group"] = [
        next(group for c, _, group in CATEGORIES if row[c])
        if any(row[c] for c, _, _ in CATEGORIES)
        else "08_borderline_context"
        for _, row in result.iterrows()
    ]
    result = result.sort_values(["review_group"] + KEY).reset_index(drop=True)
    result["case_id"] = [f"C{i:02}" for i in range(1, len(result) + 1)]
    result["reused_phase3a1_case"] = [
        tuple(r) in prior_keys for r in result[KEY].itertuples(index=False, name=None)
    ]
    return result


def anchor_neighbors(timeline, event_index):
    """Require exactly one parent; no nearest search may cross that parent."""
    if (
        len(timeline[KEY].drop_duplicates()) != 1
        or not timeline.event_index.eq(event_index).any()
    ):
        raise ValueError("Candidate lookup requires one complete provider parent")
    good = timeline[timeline.validated_anchor].sort_values("event_index")
    before = good[good.event_index.lt(event_index)]
    at = good[good.event_index.eq(event_index)]
    after = good[good.event_index.gt(event_index)]
    return {
        "before": None if before.empty else int(before.event_index.iloc[-1]),
        "candidate": None if at.empty else int(at.event_index.iloc[0]),
        "after": None if after.empty else int(after.event_index.iloc[0]),
    }


def candidate_moments(timeline, case_id):
    """Permissive, bounded REVIEW SAMPLING CRITERIA; no outcome fields consulted.

    Union first observations at several Phase 3A-1 settings, sign-turn context,
    two recovery examples, and literal football context. Deduplicate by event.
    """
    if len(timeline[KEY].drop_duplicates()) != 1:
        raise ValueError("Candidates require one provider parent")
    a = timeline[timeline.safe_action]
    path = action_path(a).reset_index(drop=True)
    candidates = {}

    def add(index, reason):
        candidates.setdefault(int(index), set()).add(reason)

    for level in (5, 15, 30, 40):
        for name, mask in (
            ("single_negative", a.delta_x.le(-level)),
            ("peak_retreat", a.retreat_from_peak.ge(level)),
        ):
            hit = a[mask]
            if len(hit):
                add(
                    hit.event_index.iloc[0],
                    f"review sampling criterion: {name}>={level}",
                )
    runs = progression_runs(a)
    for kind in ("negative", "nonpositive"):
        for count in (2, 3):
            hit = runs[
                runs.run_kind.eq(kind) & runs.action_count.ge(count)
            ].sort_values("first_event_index")
            if len(hit):
                add(
                    hit.last_event_index.iloc[0],
                    f"review sampling criterion: {kind} run>={count}",
                )
    # Weak sign-turn and renewal examples remain available below magnitude sweeps.
    neg = a[a.delta_x.lt(0)]
    if len(neg):
        add(
            neg.event_index.iloc[0],
            "review sampling criterion: first negative vector (no magnitude minimum)",
        )
    renewed = a[a.delta_x.gt(0) & a.delta_x.shift().lt(0)]
    if len(renewed):
        add(
            renewed.event_index.iloc[0],
            "review sampling criterion: first negative-to-positive action turn",
        )
    from leverkusen.sequences.progression_diagnostics import recovery_inventory

    recoveries = recovery_inventory(path)
    observed = recoveries[recoveries.recovered_previous_peak]
    if len(observed):
        for r in (
            observed.sort_values(
                ["time_to_recover_previous_peak", "onset_event_index"]
            ).iloc[0],
            observed.sort_values(
                ["time_to_recover_previous_peak", "onset_event_index"]
            ).iloc[-1],
        ):
            add(
                r.last_observed_event_index,
                "review sampling criterion: shortest/longest observed record-peak recovery",
            )
    for gap in (3, 10, 15):
        hit = timeline[timeline.prior_event_gap_seconds.gt(gap)]
        if len(hit):
            add(
                hit.event_index.iloc[0],
                f"review sampling criterion: first full-event gap>{gap}s",
            )
    for r in timeline.itertuples(index=False):
        if (
            r.event_type
            in (
                "Shot",
                "Foul Won",
                "Foul Committed",
                "Injury Stoppage",
                "Half Start",
                "Half End",
                "Offside",
                "Referee Ball-Drop",
            )
            or r.restart_context
            or "out:true" in r.provider_context
        ):
            add(r.event_index, "review sampling criterion: literal football context")
    rows, contexts = [], []
    for number, (index, reasons) in enumerate(sorted(candidates.items()), 1):
        r = timeline[timeline.event_index.eq(index)].iloc[0]
        candidate_id = f"{case_id}_M{number:02}"
        neighbors = anchor_neighbors(timeline, index)
        prior = path[path.event_index.le(index)]
        current = r.end_x if r.safe_action else np.nan
        peak = (
            prior.loc[prior.attacking_x.eq(prior.attacking_x.max())].iloc[-1]
            if len(prior)
            else None
        )
        peak_x = peak.attacking_x if peak is not None else np.nan
        # At a non-action event only the prior action peak is known, not current ball x.
        later = path[path.event_index.gt(index)]
        retreat = peak_x - current if r.safe_action else np.nan
        below = r.safe_action and retreat > 0
        recovery = later[later.attacking_x.ge(peak_x)] if below else later.iloc[0:0]
        recent = a[a.event_index.le(index)].tail(3)
        start = path.attacking_x.iloc[0] if len(path) else np.nan
        row = {
            "case_id": case_id,
            **{k: r[k] for k in KEY},
            "candidate_id": candidate_id,
            "candidate_event_index": index,
            "candidate_elapsed_seconds": r.elapsed_possession_time,
            "candidate_event_type": r.event_type,
            "candidate_event_team": r.event_team,
            "restart_context": r.restart_context,
            "possession_restart_context": ";".join(
                sorted(set(timeline.restart_context) - {""})
            ),
            "candidate_reason": "; ".join(sorted(reasons)),
            "attacking_x": current,
            "current_x_reference": "safe_action_end"
            if r.safe_action
            else "unavailable_no_safe_action_vector",
            "candidate_anchor_x": r.anchor_x,
            "prior_peak_x": peak_x,
            "retreat_from_peak": retreat,
            "largest_recent_negative_dx": recent.delta_x.clip(upper=0).min()
            if len(recent)
            else np.nan,
            "negative_run_length": r.negative_run_length_so_far,
            "nonpositive_run_length": r.nonpositive_run_length_so_far,
            "time_since_peak": r.period_seconds - peak.period_seconds
            if peak is not None
            else np.nan,
            "events_since_peak": r.event_position - peak.event_position
            if peak is not None
            else np.nan,
            "observed_recovery": bool(len(recovery)) if below else None,
            "time_to_recovery": recovery.period_seconds.iloc[0] - r.period_seconds
            if len(recovery)
            else np.nan,
            "events_to_recovery": recovery.event_position.iloc[0] - r.event_position
            if len(recovery)
            else np.nan,
            "new_peak_afterward": bool(later.attacking_x.gt(peak_x).any())
            if below
            else None,
            "starting_field_position_band": pd.cut(
                pd.Series([start]), DEPTH_EDGES, labels=DEPTH_LABELS, right=False
            ).iloc[0],
            **{
                f"{slot}_event_index": value
                for slot, value in neighbors.items()
                if slot != "candidate"
            },
            **{
                f"{slot}_spatial_state_available": value is not None
                for slot, value in neighbors.items()
            },
            **dict.fromkeys(HUMAN_COLUMNS, ""),
        }
        rows.append(row)
        position = timeline.index.get_loc(r.name)
        context = timeline.iloc[max(0, position - 3) : position + 4].copy()
        context["candidate_id"] = candidate_id
        context["context_event_offset"] = (
            np.arange(max(0, position - 3), min(len(timeline), position + 4)) - position
        )
        contexts.append(context)
    return pd.DataFrame(rows), pd.concat(
        contexts, ignore_index=True
    ) if contexts else pd.DataFrame()


def write_blank_sheet(sheet, path):
    """Never overwrite human work during a rerun."""
    path = Path(path)
    if path.exists():
        old = pd.read_csv(path, keep_default_na=False)
        if any(old[c].astype(str).str.strip().ne("").any() for c in HUMAN_COLUMNS):
            raise ValueError(
                "Existing worksheet contains human annotations; use a new output directory"
            )
    if any(sheet[c].fillna("").ne("").any() for c in HUMAN_COLUMNS):
        raise ValueError("Review pack must leave all human fields blank")
    sheet.to_csv(path, index=False)


def normalized_snapshot(event, frame, match, timeline_row):
    """Anonymous point derivatives and explicit vectors, using locked helpers only."""
    if timeline_row.semantics_status != VALIDATED:
        raise ValueError("Unsupported frame cannot enter normalized pitch panels")
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )

    def transform(p):
        return normalize_attacking_point(
            p,
            reference_team_id=field(event, "team"),
            target_team_id=TEAM_ID,
            match_team_ids=teams,
            semantics_status=timeline_row.semantics_status,
        )

    rows = []
    for i, point in enumerate(points(frame)):
        n = transform(point["location"])
        rows.append(
            {
                "point_order": i,
                "x_attacking": n["x_attacking"],
                "y_attacking": n["y_attacking"],
                "side": point_team_label(
                    point["teammate"],
                    field(event, "team"),
                    teams,
                    semantics_status=VALIDATED,
                )["frame_player_side"],
                "keeper": point["keeper"],
                "actor": point["actor"],
            }
        )
    polygon = frame.get("visible_area", [])
    vertices = []
    if isinstance(polygon, list) and len(polygon) >= 6 and len(polygon) % 2 == 0:
        pairs = [valid_point(polygon[i : i + 2]) for i in range(0, len(polygon), 2)]
        if all(p is not None for p in pairs):
            vertices = [transform(p) for p in pairs]
    end = event.get(timeline_row.event_type.lower(), {}).get("end_location")
    explicit = (
        timeline_row.event_type in ("Pass", "Carry", "Shot")
        and isinstance(end, list)
        and len(end) >= 2
        and valid_point(end[:2]) is not None
    )
    endpoint = transform(end[:2]) if explicit else {}
    return (
        rows,
        vertices,
        {
            "vector_end_x": endpoint.get("x_attacking"),
            "vector_end_y": endpoint.get("y_attacking"),
        },
    )


def snapshot_geometry(event, frame, frame_index, match, timeline_row):
    """All six locked native variants and original support/status fields survive."""
    if timeline_row.semantics_status != VALIDATED:
        raise ValueError("Unsupported geometry cannot receive team semantics")
    native = pd.DataFrame(
        frame_geometry(
            frame,
            match_id=match["match_id"],
            frame_index=frame_index,
            source_revision=loader.STATSBOMB_REVISION,
            event=event,
            event_join_status="unique",
        )
    )
    original = native[
        native.selected_subset.eq("all_visible")
        & native.goalkeeper_policy.eq("included")
    ].iloc[0]
    native["frame_oob"] = original.n_out_of_bounds_points > 0
    native["frame_coincident"] = original.n_coincident_records > 0
    native["frame_oob_unknown"] = pd.isna(original.n_out_of_bounds_points)
    native["frame_coincident_unknown"] = pd.isna(original.n_coincident_records)
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )
    native["semantic_side"] = [
        "all_visible"
        if subset == "all_visible"
        else point_team_label(
            subset == "teammate_true",
            field(event, "team"),
            teams,
            semantics_status=VALIDATED,
        )["frame_player_side"]
        for subset in native.selected_subset
    ]
    native["semantics_status"] = VALIDATED
    for metric in METRICS:
        primary = native[f"{metric}_status"].eq("ok") & native.actor_status.isin(
            ["single", "none"]
        )
        native[f"{metric}_d_primary_eligible"] = primary
        native[f"{metric}_oob_b_eligible"] = (
            primary & ~native.frame_oob & ~native.frame_oob_unknown
        )
    # Preserve native centroid; add the same validated transform as point geometry.
    normalized = [
        normalize_attacking_point(
            [r.centroid_x, r.centroid_y],
            reference_team_id=field(event, "team"),
            target_team_id=TEAM_ID,
            match_team_ids=teams,
            semantics_status=VALIDATED,
        )
        for r in native.itertuples(index=False)
    ]
    native["centroid_x_attacking"] = [r["x_attacking"] for r in normalized]
    native["centroid_y_attacking"] = [r["y_attacking"] for r in normalized]
    native["keeper_role"] = np.where(
        native.goalkeeper_policy.eq("excluded"),
        "primary_outfield",
        "full_visible_sensitivity",
    )
    return native


def order_for_review(manifest):
    """Presentation groups only; stable case IDs survive overlapping coverage."""
    result = manifest.copy()
    result["sampling_group"] = result.get("sampling_group", result.review_group)

    def group(row):
        if row.nearly_monotonic or row.one_small_backward:
            return "01_forward_contrasts"
        if row.shot_then_same_parent_actions:
            return "06_shot_context"
        if row.corner_started or row.free_kick_started or row.throw_in_restart:
            return "05_set_pieces"
        if row.very_long:
            return "07_long_complex"
        if row.large_single_backward:
            return "02_single_action_retreat"
        if row.gradual_multi_action:
            return "03_multi_action_retreat"
        if (
            row.circulation_for_review
            or row.sparse_anchors
            or row.advanced_origin_retreat
        ):
            return "08_borderline_context"
        return "04_recovery"

    result["review_group"] = [group(row) for row in result.itertuples(index=False)]
    result = result.sort_values(["review_group", "case_id"]).reset_index(drop=True)
    result["review_order"] = range(1, len(result) + 1)
    return result


def select_panel_candidates(sheet, manifest):
    """Fifteen distributed cases plus a Corner/continuing-Shot contrast pair."""
    # One instructive candidate per case, then take 15 distinct cases. Prioritize
    # named football context and largest observed retreat.
    panels = []
    for case_id, group in sheet.groupby("case_id", sort=True):
        choices = group.copy()
        choices["football_context"] = choices.restart_context.ne(
            ""
        ) | choices.candidate_event_type.eq("Shot")
        choices = choices.sort_values(
            ["football_context", "retreat_from_peak", "candidate_event_index"],
            ascending=[False, False, True],
            na_position="last",
        )
        panels.append(choices.iloc[0].candidate_id)
    # Spread across review groups instead of selecting only the first groups.
    panel_candidates = sheet[sheet.candidate_id.isin(panels)].merge(
        manifest[["case_id", "review_group"]]
        if "sampling_group" not in manifest
        else manifest[["case_id", "sampling_group"]].rename(
            columns={"sampling_group": "review_group"}
        ),
        on="case_id",
    )
    panel_candidates["within_group"] = panel_candidates.groupby(
        "review_group"
    ).cumcount()
    panel_candidates = panel_candidates.sort_values(
        ["within_group", "review_group", "case_id"]
    ).head(15)
    contrast = manifest[
        manifest.corner_started & manifest.shot_then_same_parent_actions
    ].sort_values(KEY)
    extras = []
    if len(contrast):
        case_sheet = sheet[sheet.case_id.eq(contrast.case_id.iloc[0])]
        for mask in (
            case_sheet.restart_context.eq("Corner"),
            case_sheet.candidate_event_type.eq("Shot"),
        ):
            hit = case_sheet[mask].sort_values("candidate_event_index")
            if len(hit):
                extras.append(hit.iloc[[0]])
    return pd.concat([panel_candidates, *extras], ignore_index=True).drop_duplicates(
        "candidate_id"
    )


def build_snapshot_tables(panel_candidates, timeline, sources):
    """Build only requested slots; full-match audit must precede this helper."""
    slots, point_rows, polygons, geometry = [], [], [], []
    for c in panel_candidates.itertuples(index=False):
        parent = timeline[timeline.case_id.eq(c.case_id)]
        neighbors = anchor_neighbors(parent, c.candidate_event_index)
        for slot, index in neighbors.items():
            slot_id = f"{c.candidate_id}_{slot}"
            info = {
                "case_id": c.case_id,
                "candidate_id": c.candidate_id,
                "slot": slot,
                "slot_id": slot_id,
                **{k: getattr(c, k) for k in KEY},
                "candidate_event_index": c.candidate_event_index,
                "spatial_state_available": index is not None,
            }
            if index is not None:
                r = parent[parent.event_index.eq(index)].iloc[0]
                match, events, frames = sources[int(c.match_id)]
                event = events[index]
                frame_index, frame = frames[event["id"]]
                point_data, polygon_data, endpoint = normalized_snapshot(
                    event, frame, match, r
                )
                info |= {
                    "event_index": index,
                    "event_id": r.event_id,
                    "elapsed_seconds": r.elapsed_possession_time,
                    "event_type": r.event_type,
                    "event_team": r.event_team,
                    "anchor_x": r.anchor_x,
                    "anchor_y": r.anchor_y,
                    "retreat_from_peak": r.retreat_from_peak,
                    "semantics_status": r.semantics_status,
                    "spatial_state_status": r.spatial_state_status,
                    **endpoint,
                }
                point_rows.extend({"slot_id": slot_id, **p} for p in point_data)
                polygons.extend(
                    {
                        "slot_id": slot_id,
                        "vertex_order": i,
                        "x_attacking": p["x_attacking"],
                        "y_attacking": p["y_attacking"],
                    }
                    for i, p in enumerate(polygon_data)
                )
                g = snapshot_geometry(event, frame, frame_index, match, r)
                g["slot_id"] = slot_id
                geometry.append(g)
            else:
                info["spatial_state_status"] = "no_validated_state_in_parent_for_slot"
                if slot == "candidate":
                    r = parent[parent.event_index.eq(c.candidate_event_index)].iloc[0]
                    info |= {
                        "event_index": r.event_index,
                        "event_id": r.event_id,
                        "elapsed_seconds": r.elapsed_possession_time,
                        "event_type": r.event_type,
                        "event_team": r.event_team,
                        "semantics_status": r.semantics_status,
                        "spatial_state_status": r.spatial_state_status,
                    }
            slots.append(info)
    return {
        "spatial_slots": pd.DataFrame(slots),
        "spatial_points": pd.DataFrame(point_rows),
        "spatial_polygons": pd.DataFrame(polygons),
        "spatial_geometry": pd.concat(geometry, ignore_index=True),
    }


def run_review_pack(root, progress=print):
    """Reuse season diagnostics; fetch only prior representative matches once."""
    root = Path(root)
    directory = root / "outputs/diagnostics"
    sheet_path = directory / "phase3a2_boundary_review_sheet.csv"
    if sheet_path.exists():
        existing = pd.read_csv(sheet_path, keep_default_na=False)
        if existing[HUMAN_COLUMNS].apply(lambda c: c.str.strip().ne("").any()).any():
            raise ValueError(
                "Human annotations exist; refusing to overwrite review pack"
            )
    summaries = read_prior(directory, "possession_progression_summary")
    prior = read_prior(directory, "representative_possessions")
    recoveries = read_prior(directory, "recovery_inventory")
    prior_keys = set(prior[KEY].itertuples(index=False, name=None))
    matches = {m["match_id"]: m for m in loader.load_matches()}
    match_ids = sorted(prior.match_id.unique())
    pool_keys = prior_keys | set(
        summaries.loc[summaries.match_id.eq(match_ids[0]), KEY].itertuples(
            index=False, name=None
        )
    )
    streams, sources, source_inventory = {}, {}, []
    for mid in match_ids:
        mid = int(mid)
        progress(
            f"Bounded match {mid}: load events/360 and reuse full-match semantic audit"
        )
        events, frames = loader.load_events(mid), loader.load_360(mid)
        _, selected, _ = enrich_match(
            matches[mid], events, frames, source_revision=loader.STATSBOMB_REVISION
        )
        keep = selected[KEY].apply(tuple, axis=1).isin(pool_keys)
        timeline = complete_timeline(selected[keep], events)
        for key, group in timeline.groupby(KEY, sort=True):
            reference = keyed(summaries, key).iloc[0]
            if (
                len(group) != reference.total_event_count
                or group.safe_action.sum() != reference.safe_action_count
                or group.validated_anchor.sum()
                != reference.validated_spatial_anchor_count
            ):
                raise ValueError(
                    "Bounded re-extraction disagrees with Phase 3A-1 evidence"
                )
            streams[key] = group.reset_index(drop=True)
        sources[mid] = (
            matches[mid],
            {e["index"]: e for e in events},
            {f["event_uuid"]: (i, f) for i, f in enumerate(frames)},
        )
        source_inventory.append(
            {
                "match_id": mid,
                "full_match_events_audited": len(events),
                "full_match_frames_audited": len(frames),
                "events_url": f"{loader.BASE_URL}/events/{mid}.json",
                "frames_url": f"{loader.BASE_URL}/three-sixty/{mid}.json",
            }
        )
    records = []
    for key, timeline in sorted(streams.items()):
        s = keyed(summaries, key).iloc[0]
        records.append(
            {**s.to_dict(), **category_matches(s, timeline, keyed(recoveries, key))}
        )
    pool = pd.DataFrame(records)
    manifest = select_cases(pool, prior_keys)
    sheets, contexts, timelines = [], [], []
    for _, case in manifest.iterrows():
        key = tuple(case[KEY])
        timeline = streams[key].copy()
        timeline["case_id"] = case.case_id
        sheet, context = candidate_moments(timeline, case.case_id)
        sheets.append(sheet)
        contexts.append(context)
        timelines.append(timeline)
    sheet = pd.concat(sheets, ignore_index=True)
    timeline = pd.concat(timelines, ignore_index=True)
    context = pd.concat(contexts, ignore_index=True)
    manifest["candidate_count"] = (
        manifest.case_id.map(sheet.groupby("case_id").size()).fillna(0).astype(int)
    )
    manifest["shot_count"] = (
        manifest.case_id.map(
            timeline[timeline.event_type.eq("Shot")].groupby("case_id").size()
        )
        .fillna(0)
        .astype(int)
    )
    manifest["restart_context"] = manifest.case_id.map(
        timeline.groupby("case_id").restart_context.agg(
            lambda s: ";".join(sorted(set(s) - {""}))
        )
    )
    manifest["out_event_count"] = manifest.case_id.map(
        timeline.assign(
            is_out=timeline.provider_context.str.contains("out:true", regex=False)
        )
        .groupby("case_id")
        .is_out.sum()
    )
    panel_candidates = select_panel_candidates(sheet, manifest)
    spatial = build_snapshot_tables(panel_candidates, timeline, sources)
    manifest = order_for_review(manifest)
    coverage = pd.DataFrame(
        [
            {
                "category": c,
                "review_sampling_criterion": criterion,
                "pool_count": int(pool[c].sum()),
                "selected_count": int(manifest[c].sum()),
                "case_ids": ";".join(manifest.loc[manifest[c], "case_id"]),
                "availability": "covered"
                if manifest[c].any()
                else "no clean example in bounded pool; not forced",
            }
            for c, criterion, _ in CATEGORIES
        ]
    )
    manifest["figure_path"] = manifest.case_id.map(
        lambda c: f"outputs/figures/phase3a2_{c}_progression.png"
    )
    manifest["timeline_path"] = manifest.case_id.map(
        lambda c: f"outputs/diagnostics/phase3a2_{c}_timeline.csv"
    )
    manifest["pitch_panel_available"] = manifest.case_id.isin(panel_candidates.case_id)
    manifest["notes"] = (
        "Review sampling only; full event context; endpoint times unavailable; geometry corroborative only"
    )
    tables = {
        "review_manifest": manifest,
        "category_coverage": coverage,
        "boundary_review_sheet": sheet,
        "candidate_context": context,
        "timelines": timeline,
        **spatial,
        "source_inventory": pd.DataFrame(source_inventory),
    }
    for name, table in tables.items():
        table["statsbomb_revision"] = loader.STATSBOMB_REVISION
        if name == "boundary_review_sheet":
            write_blank_sheet(table, sheet_path)
        else:
            table.to_csv(directory / f"phase3a2_{name}.csv", index=False)
    for case_id, group in timeline.groupby("case_id", sort=True):
        group.to_csv(directory / f"phase3a2_{case_id}_timeline.csv", index=False)
    progress(
        f"Assembled {len(manifest)} parents, {len(sheet)} candidate review moments, {len(panel_candidates)} snapshot triptychs"
    )
    return tables

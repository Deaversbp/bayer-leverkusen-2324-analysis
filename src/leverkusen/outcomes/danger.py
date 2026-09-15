"""Provider event outcomes restricted to exact locked control-spell membership."""

from math import isfinite
from numbers import Real

import numpy as np
import pandas as pd

from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.spatial.geometry import valid_point

SPELL = ["match_id", "attacking_control_spell_id"]
EVENT = ["match_id", "event_id"]
CONTEXT = [*SPELL, "event_id", "event_index", "period", "timestamp",
           "event_type", "event_team", "event_team_id"]
HORIZONS = ("5s", "10s", "15s", "rest_of_spell")
OUTCOME_COLUMNS = [*CONTEXT, "outcome_type", "start_x", "start_y",
                   "end_x", "end_y", "shot_xg"]


def box_point(value):
    """Accept finite, on-pitch 2D coordinates; never infer or clip endpoints."""
    point = valid_point(value)
    return point if point and 0 <= point[0] <= 120 and 0 <= point[1] <= 80 else None


def inside_box(point):
    return point[0] >= 102 and 18 <= point[1] <= 62


def is_box_entry(event):
    typ = field(event, "type", "name")
    if field(event, "team") != TEAM_ID or typ not in {"Pass", "Carry"}:
        return False
    action = event.get(typ.lower(), {})
    # Existing provider semantics: completed passes have no outcome value.
    if typ == "Pass" and action.get("outcome") is not None:
        return False
    start, end = box_point(event.get("location")), box_point(action.get("end_location"))
    return bool(start and end and not inside_box(start) and inside_box(end))


def detect_outcome_events(context, events):
    """Join one match's pinned records by UUID and verify source identity/order.

    Includes all eligible spell events, whether or not they have a trusted frame.
    Context contains the already locked membership; this function never segments.
    """
    by_id = {e["id"]: e for e in events}
    if len(by_id) != len(events) or len({e["index"] for e in events}) != len(events):
        raise ValueError("Duplicate provider event identity")
    if any(a["index"] >= b["index"] for a, b in zip(events, events[1:])):
        raise ValueError("Provider indices disagree with source order")
    selected_ids = {e["id"] for e in events if field(e, "possession_team") == TEAM_ID}
    if set(context.event_id) != selected_ids:
        raise ValueError("Pinned source / locked context inventory differs")
    rows = []
    for r in context.itertuples(index=False):
        event = by_id[r.event_id]
        actual = (event["index"], event["period"], event["timestamp"],
                  field(event, "type", "name"), field(event, "team", "name"),
                  field(event, "team"), event["possession"])
        expected = (r.event_index, r.period, r.timestamp, r.event_type,
                    r.event_team, r.event_team_id, r.provider_possession_id)
        if actual != expected or events[r.source_order]["id"] != r.event_id:
            raise ValueError(f"Pinned source context mismatch: {r.event_id}")
        if pd.isna(r.attacking_control_spell_id):
            continue
        shot = r.event_team_id == TEAM_ID and r.event_type == "Shot"
        entry = is_box_entry(event)
        if not (shot or entry):
            continue
        row = {c: getattr(r, c) for c in CONTEXT}
        row.update(outcome_type="shot" if shot else "box_entry",
                   start_x=np.nan, start_y=np.nan, end_x=np.nan, end_y=np.nan,
                   shot_xg=np.nan)
        if entry:
            row["start_x"], row["start_y"] = event["location"]
            row["end_x"], row["end_y"] = event[r.event_type.lower()]["end_location"]
        if shot:
            xg = event.get("shot", {}).get("statsbomb_xg")
            if xg is not None:
                if isinstance(xg, bool) or not isinstance(xg, Real) or not isfinite(xg) or not 0 <= xg <= 1:
                    raise ValueError(f"Invalid provider shot xG: {r.event_id}")
                row["shot_xg"] = xg
        rows.append(row)
    return pd.DataFrame(rows, columns=OUTCOME_COLUMNS)


def time_values(table):
    """Integer nanoseconds preserve inclusive horizon edges exactly."""
    values = pd.to_timedelta(table.timestamp)
    if values.isna().any() or values.lt(pd.Timedelta(0)).any():
        raise ValueError("Invalid timestamp")
    return values.to_numpy(dtype="timedelta64[ns]").astype(np.int64)


def columns_for(horizon):
    suffix = "before_spell_end" if horizon == "rest_of_spell" else f"within_{horizon}"
    return f"box_entry_{suffix}", f"shot_{suffix}", f"future_xg_{horizon}"


def check_inputs(anchors, outcomes):
    for table in (anchors, outcomes):
        if table[[*SPELL, "event_id", "event_index", "period"]].isna().any().any():
            raise ValueError("Missing event/spell identity")
        if table.duplicated(EVENT).any() or table.duplicated(["match_id", "event_index"]).any():
            raise ValueError("Duplicate event identity")
        time_values(table)
    both = pd.concat([anchors[CONTEXT], outcomes[CONTEXT]]).drop_duplicates(EVENT)
    for _, group in both.groupby(SPELL):
        if group.period.nunique() != 1 or np.any(np.diff(time_values(group.sort_values("event_index"))) < 0):
            raise ValueError("Spell crosses periods or has reversed timestamps")


def build_anchor_outcomes(anchors, outcomes):
    """One row per reference; inclusive reference event and horizon endpoints.

    Missing xG propagates to any horizon containing that Shot. Empty Shot sets
    have xG zero. Same-timestamp events before the reference are never selected.
    """
    check_inputs(anchors, outcomes)
    groups = {key: group.sort_values("event_index") for key, group in outcomes.groupby(SPELL)}
    empty = outcomes.iloc[:0]
    rows = []
    for key, group in anchors.sort_values(["match_id", "event_index"]).groupby(SPELL, sort=False):
        future = groups.get(key, empty)
        indices = future.event_index.to_numpy()
        times = time_values(future)
        ids = future.event_id.to_numpy()
        shot = future.outcome_type.eq("shot").to_numpy()
        box = future.outcome_type.eq("box_entry").to_numpy()
        xg = future.shot_xg.to_numpy(dtype=float)
        for r, reference_time in zip(group.itertuples(index=False), time_values(group)):
            elapsed = times - reference_time
            eligible = indices >= r.event_index
            if np.any(elapsed[eligible] < 0):
                raise ValueError("Outcome precedes reference timestamp")
            immediate = ids == r.event_id
            row = {"match_id": r.match_id, "attacking_control_spell_id": r.attacking_control_spell_id}
            row.update({f"reference_{c}": getattr(r, c) for c in
                        ("event_id", "event_index", "timestamp", "event_type", "event_team")})
            row.update(reference_is_box_entry=int(np.any(immediate & box)),
                       reference_is_shot=int(np.any(immediate & shot)),
                       reference_shot_xg=xg[immediate & shot][0] if np.any(immediate & shot) else np.nan)
            for name, kind in (("box_entry", box), ("shot", shot)):
                positions = np.flatnonzero(eligible & kind)
                pos = positions[0] if len(positions) else None
                row[f"seconds_to_next_{name}"] = elapsed[pos] / 1e9 if pos is not None else np.nan
                row[f"next_{name}_event_id"] = ids[pos] if pos is not None else None
                if name == "shot":
                    row["next_shot_xg"] = xg[pos] if pos is not None else np.nan
            for horizon in HORIZONS:
                mask = eligible if horizon == "rest_of_spell" else eligible & (elapsed <= int(horizon[:-1]) * 10**9)
                bcol, scol, xcol = columns_for(horizon)
                row[bcol], row[scol] = int(np.any(mask & box)), int(np.any(mask & shot))
                row[xcol] = np.sum(xg[mask & shot])
            rows.append(row)
    return pd.DataFrame(rows)


def validate_outcomes(anchors, outcomes, result):
    """Independently reconstruct all horizons with per-spell incidence matrices."""
    expected_ids = anchors[EVENT].rename(columns={"event_id": "reference_event_id"})
    if len(result) != len(anchors) or result.duplicated(["match_id", "reference_event_id"]).any():
        raise ValueError("Anchor row reconciliation failed")
    reconciled = expected_ids.merge(result, on=["match_id", "reference_event_id"], how="outer", indicator=True)
    if not reconciled._merge.eq("both").all():
        raise ValueError("Anchor identity reconciliation failed")
    for family in range(3):
        values = result[[columns_for(h)[family] for h in HORIZONS]].to_numpy()
        # Compare all available pairs, including across explicit missing-xG windows.
        for left in range(4):
            for right in range(left + 1, 4):
                if np.any(values[:, left] > values[:, right] + (1e-12 if family == 2 else 0)):
                    raise ValueError("Outcome nesting failed")
    grouped = {key: g.sort_values("event_index") for key, g in outcomes.groupby(SPELL)}
    result_index = result.set_index(["match_id", "reference_event_id"])
    for key, refs in anchors.groupby(SPELL):
        events = grouped.get(key, outcomes.iloc[:0])
        observed = result_index.loc[pd.MultiIndex.from_frame(refs[EVENT])]
        for col in ("event_index", "timestamp", "event_type", "event_team"):
            if not np.array_equal(observed[f"reference_{col}"].to_numpy(), refs[col].to_numpy()):
                raise ValueError(f"Reference context mismatch: {col}")
        if not observed.attacking_control_spell_id.eq(key[1]).all():
            raise ValueError("Reference spell mismatch")
        delta = time_values(events)[None, :] - time_values(refs)[:, None]
        future = events.event_index.to_numpy()[None, :] >= refs.event_index.to_numpy()[:, None]
        if np.any(delta[future] < 0):
            raise ValueError("Temporal ordering failed")
        shot = events.outcome_type.eq("shot").to_numpy()[None, :]
        box = events.outcome_type.eq("box_entry").to_numpy()[None, :]
        xg = events.shot_xg.to_numpy(dtype=float)[None, :]
        immediate = events.event_id.to_numpy()[None, :] == refs.event_id.to_numpy()[:, None]
        for name, kind in (("box_entry", box), ("shot", shot)):
            if not np.array_equal(observed[f"reference_is_{name}"], np.any(immediate & kind, axis=1)):
                raise ValueError("Immediate outcome mismatch")
        immediate_xg = np.where(np.any(immediate & shot, axis=1),
                                 np.sum(np.where(immediate & shot, xg, 0), axis=1), np.nan)
        if not np.allclose(observed.reference_shot_xg, immediate_xg, rtol=0, atol=1e-12, equal_nan=True):
            raise ValueError("Reference Shot xG mismatch")
        for horizon in HORIZONS:
            eligible = future if horizon == "rest_of_spell" else future & (delta <= int(horizon[:-1]) * 10**9)
            expected = (np.any(eligible & box, axis=1), np.any(eligible & shot, axis=1),
                        np.sum(np.where(eligible & shot, xg, 0), axis=1))
            for col, values in zip(columns_for(horizon), expected):
                if not np.allclose(observed[col], values, rtol=0, atol=1e-12, equal_nan=True):
                    raise ValueError(f"Same-spell horizon reconstruction failed: {col}")
        for name, kind in (("box_entry", box), ("shot", shot)):
            for n, (_, row) in enumerate(observed.iterrows()):
                candidates = np.flatnonzero(future[n] & kind[0])
                if not len(candidates):
                    if pd.notna(row[f"next_{name}_event_id"]) or pd.notna(row[f"seconds_to_next_{name}"]):
                        raise ValueError("Unexpected next outcome")
                    if name == "shot" and pd.notna(row.next_shot_xg):
                        raise ValueError("Unexpected next Shot xG")
                    continue
                pos = candidates[0]
                if row[f"next_{name}_event_id"] != events.event_id.iloc[pos] or row[f"seconds_to_next_{name}"] != delta[n, pos] / 1e9:
                    raise ValueError("Next-event identity/order/boundary failed")
                if name == "shot" and not np.isclose(row.next_shot_xg, events.shot_xg.iloc[pos], rtol=0, atol=1e-12, equal_nan=True):
                    raise ValueError("Next Shot xG mismatch")
    return {"nesting": "PASS", "temporal_ordering": "PASS", "same_spell_reconstruction": "PASS"}


def outcome_summary(result):
    rows = []
    for horizon in HORIZONS:
        box, shot, xg = (result[c] for c in columns_for(horizon))
        rows.append(dict(horizon=horizon, anchor_count=len(result),
                         box_entry_positive_anchors=int(box.sum()), box_entry_prevalence=box.mean(),
                         shot_positive_anchors=int(shot.sum()), shot_prevalence=shot.mean(),
                         mean_future_xg=xg.mean(), median_future_xg=xg.median(),
                         proportion_future_xg_positive=xg.dropna().gt(0).mean(),
                         missing_future_xg_anchors=int(xg.isna().sum())))
    return pd.DataFrame(rows)

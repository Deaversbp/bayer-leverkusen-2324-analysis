"""Event-stream-first attacking control spells; no soft-reset or spatial inputs."""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.sequences.progression_diagnostics import provider_signals
from leverkusen.sequences.readiness import (
    KEY,
    LOCKED_RECONCILIATION_REVISION,
    match_event_inventory,
)

RESTARTS = {"Kick Off", "Goal Kick", "Free Kick", "Corner", "Throw-in"}
ADMIN = {
    "Starting XI",
    "Half Start",
    "Half End",
    "Substitution",
    "Tactical Shift",
    "Player On",
    "Player Off",
}
ATTACK = {"Pass", "Carry", "Shot", "Dribble"}


def build_match_stream(match, events):
    """Reuse canonical full-match ordering/parent checks; never load 360 frames."""
    full = match_event_inventory(
        match, events, [], source_revision=loader.STATSBOMB_REVISION
    )
    raw = {e["index"]: e for e in events}
    selected = full[full.possession_team_id.eq(TEAM_ID)][
        [
            *KEY,
            "event_index",
            "timestamp",
            "event_type",
            "event_team_id",
            "period_seconds",
        ]
    ].copy()
    selected["event_team"] = [
        field(raw[i], "team", "name") for i in selected.event_index
    ]
    selected["provider_context"] = [
        ";".join(provider_signals(raw[i])) for i in selected.event_index
    ]
    selected["restart_context"] = [
        field(raw[i].get("pass", {}), "type", "name") or ""
        for i in selected.event_index
    ]
    selected["advantage"] = [
        any(
            raw[i].get(k, {}).get("advantage", False)
            for k in ("foul_won", "foul_committed")
        )
        for i in selected.event_index
    ]
    selected["keeper_type"] = [
        field(raw[i].get("goalkeeper", {}), "type", "name") or ""
        for i in selected.event_index
    ]
    selected["recovery_failure"] = [
        raw[i].get("ball_recovery", {}).get("recovery_failure", False)
        for i in selected.event_index
    ]
    selected["dribble_outcome"] = [
        field(raw[i].get("dribble", {}), "outcome", "name") or ""
        for i in selected.event_index
    ]
    return selected


def load_season(progress=print):
    if loader.STATSBOMB_REVISION != LOCKED_RECONCILIATION_REVISION:
        raise ValueError("Pinned source revision differs; stop reconciliation")
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
        raise ValueError("Expected 34 matches; stop reconciliation")

    def fetch(match):
        return build_match_stream(match, loader.load_events(match["match_id"]))

    with ThreadPoolExecutor(max_workers=4) as pool:
        tables = []
        for i, table in enumerate(pool.map(fetch, matches), 1):
            tables.append(table)
            if i % 5 == 0 or i == 34:
                progress(f"Read {i}/34 pinned matches (no raw cache)")
    stream = (
        pd.concat(tables, ignore_index=True)
        .sort_values([*KEY, "event_index"])
        .reset_index(drop=True)
    )
    inventory = (
        stream.match_id.nunique(),
        len(stream[KEY].drop_duplicates()),
        len(stream),
    )
    if inventory != (34, 2888, 86025):
        raise ValueError(
            f"Canonical inventory differs: {inventory}; expected (34, 2888, 86025). Stop."
        )
    return stream


def signals(row):
    return set(str(row.provider_context).split(";"))


def dead_reason(row):
    context = signals(row)
    if "out:true" in context or "pass.outcome:Out" in context:
        return "BALL_OUT"
    if row.event_type in {
        "Offside",
        "Injury Stoppage",
        "Referee Ball-Drop",
        "Half End",
    }:
        return "STOPPAGE"
    if row.event_type in {"Foul Won", "Foul Committed"} and not row.advantage:
        return "FOUL_STOPPAGE"
    if "pass.outcome:Pass Offside" in context:
        return "STOPPAGE"
    return ""


def control_evidence(row):
    """Return a control cue and whether it independently establishes distribution."""
    typ, context = row.event_type, signals(row)
    if typ == "Ball Recovery":
        return (not row.recovery_failure, False)
    if typ == "Interception":
        return ("interception.outcome:Won" in context, False)
    if typ == "Pass":
        completed = not any(s.startswith("pass.outcome:") for s in context)
        return completed, completed
    if typ == "Carry":
        return True, False
    if typ == "Ball Receipt*":
        return not any(s.startswith("ball_receipt.outcome:") for s in context), False
    if typ == "Dribble":
        return row.dribble_outcome == "Complete", False
    if typ == "Goal Keeper":
        held = row.keeper_type in {
            "Collected",
            "Keeper Sweeper",
            "Saved To Post",
            "Smother",
        }
        # Saved/parried contact by itself is not established goalkeeper control.
        return held, False
    return False, False


def control_changes(rows):
    """Corroborate recovery/contact by controlled actions; ignore pressure/duel alone."""
    owner = TEAM_ID
    pending_team, pending, cues = None, None, []
    changes, uncertain = [], []
    for pos, row in enumerate(rows):
        cue, distribution = control_evidence(row)
        if dead_reason(row) or row.restart_context in RESTARTS:
            pending_team, pending, cues = None, None, []
            owner = TEAM_ID
            continue
        if not cue:
            continue
        if row.event_team_id == owner:
            if pending_team is not None:
                uncertain.append(pending)
            pending_team, pending, cues = None, None, []
            continue
        if pending_team != row.event_team_id:
            pending_team, pending, cues = row.event_team_id, pos, []
        cues.append(row.event_type)
        corroborated = len(cues) >= 2 and any(
            t in {"Carry", "Pass", "Dribble"} for t in cues
        )
        if distribution or corroborated:
            changes.append((pending, pos, pending_team))
            owner = pending_team
            pending_team, pending, cues = None, None, []
    if pending_team is not None:
        uncertain.append(pending)
    return changes, uncertain


def segment_parent(parent):
    """Return event membership, spell summaries and detected boundary evidence."""
    data = parent.sort_values("event_index").reset_index(drop=True).copy()
    rows = list(data.itertuples(index=False))
    first = rows[0]
    identity = {k: getattr(first, k) for k in KEY}
    ids = pd.Series([None] * len(rows), dtype="object")
    before, after, reasons = [False] * len(rows), [False] * len(rows), [""] * len(rows)
    statuses = ["outside_control"] * len(rows)
    if not any(r.event_team_id == TEAM_ID and r.event_type in ATTACK for r in rows):
        status = (
            "administrative_no_spell"
            if all(r.event_type in ADMIN for r in rows)
            else "insufficient_context_no_spell"
        )
        data["attacking_control_spell_id"] = ids
        data["spell_event_order"] = pd.Series([pd.NA] * len(rows), dtype="Int64")
        data["boundary_before"], data["boundary_after"], data["boundary_reason"] = (
            False,
            False,
            "",
        )
        data["membership_status"] = status
        data["unconfirmed_control_cue"] = False
        return data, [], []
    changes, uncertain = control_changes(rows)
    changes_at = {p: (confirm, team) for p, confirm, team in changes}
    terminal_shots = set()
    for pos, row in enumerate(rows):
        if row.event_type != "Shot" or row.event_team_id != TEAM_ID:
            continue
        terminal = True  # parent termination if no further attacking control
        for nxt in range(pos + 1, len(rows)):
            r = rows[nxt]
            if dead_reason(r) or (nxt in changes_at and changes_at[nxt][1] != TEAM_ID):
                break
            if r.event_team_id == TEAM_ID and r.event_type in ATTACK:
                terminal = False
                break
        if terminal:
            terminal_shots.add(pos)
    start = next(i for i, r in enumerate(rows) if r.event_type not in ADMIN)
    start_reason, number = "PROVIDER_PARENT_START", 0
    summaries, boundaries = [], []
    pending_boundary = None

    def finish(end, reason):
        nonlocal start, number
        if start is None or end < start:
            start = None
            return
        number += 1
        spell = f"{first.match_id}-p{first.period}-pp{first.possession_id}-s{number}"
        ids.iloc[start : end + 1] = spell
        before[start], after[end] = True, True
        subset = data.iloc[start : end + 1]
        for j in range(start, end + 1):
            statuses[j] = "control_spell_context"
        summaries.append(
            dict(
                **identity,
                attacking_control_spell_id=spell,
                spell_number=number,
                start_event=rows[start].event_index,
                end_event=rows[end].event_index,
                duration_seconds=rows[end].period_seconds - rows[start].period_seconds,
                event_count=len(subset),
                leverkusen_event_count=int(subset.event_team_id.eq(TEAM_ID).sum()),
                opponent_context_event_count=int(
                    subset.event_team_id.ne(TEAM_ID).sum()
                ),
                start_reason=start_reason,
                end_reason=reason,
                hard_boundary_type=reason,
                spatial_anchor_status="not_attached_or_evaluated",
                statsbomb_revision=loader.STATSBOMB_REVISION,
            )
        )
        start = None

    for pos, row in enumerate(rows):
        restart = row.restart_context in RESTARTS
        reason = "TERMINAL_SHOT" if pos in terminal_shots else dead_reason(row)
        if reason:
            if start is not None:
                finish(pos - 1, reason)
                boundaries.append(
                    dict(
                        **identity,
                        onset_event=row.event_index,
                        confirmation_event=row.event_index,
                        resume_event=np.nan,
                        boundary_type="TERMINAL",
                        reason=reason,
                    )
                )
                pending_boundary = None
                reasons[pos] = reason
            statuses[pos] = "dead_or_terminal_context"
            continue
        if restart and row.event_team_id == TEAM_ID:
            if start is not None and pos > start:
                finish(pos - 1, "RESTART")
                boundaries.append(
                    dict(
                        **identity,
                        onset_event=row.event_index,
                        confirmation_event=row.event_index,
                        resume_event=row.event_index,
                        boundary_type="RESTART",
                        reason="RESTART",
                    )
                )
                reasons[pos] = "RESTART"
            start, start_reason = pos, "OPENING_RESTART" if number == 0 else "RESTART"
            pending_boundary = None
            continue
        if pos in changes_at:
            confirmation, team = changes_at[pos]
            if team != TEAM_ID and start is not None:
                finish(pos - 1, "OPPONENT_CONTROL")
                boundary = dict(
                    **identity,
                    onset_event=row.event_index,
                    confirmation_event=rows[confirmation].event_index,
                    resume_event=np.nan,
                    boundary_type="OPPONENT_CONTROL",
                    reason="OPPONENT_CONTROL",
                )
                boundaries.append(boundary)
                pending_boundary = boundary
                reasons[pos] = "OPPONENT_CONTROL"
            elif team == TEAM_ID and start is None:
                start, start_reason = pos, "LEVERKUSEN_REGAIN"
                if pending_boundary is not None:
                    pending_boundary["resume_event"] = row.event_index
                pending_boundary = None
    finish(len(rows) - 1, "PROVIDER_PARENT_END")
    data["attacking_control_spell_id"] = ids
    data["spell_event_order"] = (
        data.groupby("attacking_control_spell_id").cumcount() + 1
    ).astype("Int64")
    data["boundary_before"], data["boundary_after"], data["boundary_reason"] = (
        before,
        after,
        reasons,
    )
    data["membership_status"] = statuses
    data["unconfirmed_control_cue"] = [i in uncertain for i in range(len(rows))]
    return data, summaries, boundaries


def segment_stream(stream):
    memberships, summaries, boundaries = [], [], []
    for _, parent in stream.groupby(KEY, sort=True):
        m, s, b = segment_parent(parent)
        memberships.append(m)
        summaries.extend(s)
        boundaries.extend(b)
    membership = pd.concat(memberships, ignore_index=True)
    summary = pd.DataFrame(
        summaries,
        columns=[
            *KEY,
            "attacking_control_spell_id",
            "spell_number",
            "start_event",
            "end_event",
            "duration_seconds",
            "event_count",
            "leverkusen_event_count",
            "opponent_context_event_count",
            "start_reason",
            "end_reason",
            "hard_boundary_type",
            "spatial_anchor_status",
            "statsbomb_revision",
        ],
    )
    boundary = pd.DataFrame(
        boundaries,
        columns=[
            *KEY,
            "onset_event",
            "confirmation_event",
            "resume_event",
            "boundary_type",
            "reason",
        ],
    )
    assert summary.attacking_control_spell_id.is_unique
    assert (
        summary.event_count.sum() == membership.attacking_control_spell_id.notna().sum()
    )
    return membership, summary, boundary

"""Bounded C01-C28 replay of the supplied rule; never a production segmenter."""

import hashlib
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.sequences.action_progression import State, flag


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/calibration"
DIAG = ROOT / "outputs/diagnostics"
REPORT = ROOT / "report/phase3a3_reset_rule_replay.md"
INPUTS = [
    SOURCE / "phase3a3_reviewed_event_source.csv",
    SOURCE / "phase3a3_reviewed_parent_source.csv",
    SOURCE / "phase3a3_reviewed_boundaries.csv",
    DIAG / "phase3a3_episode_local_candidate_diagnostics.csv",
    DIAG / "phase3a3_reviewed_episode_map.csv",
]
HARD = {"OPPONENT_CONTROL", "TERMINAL"}
EXCLUDE = {"ADMINISTRATIVE_EXCLUDE", "INSUFFICIENT_CONTEXT_EXCLUDE"}


def replay(events, hard_ledger, version="v0.1", masks=()):
    """Replay without soft targets; v0.3 uses review masks only for censoring."""
    transitions, warnings, trace = [], [], []
    assert version in {"v0.1", "v0.2", "v0.3"}
    initial_mode = "ACTIVE" if version == "v0.3" else "DISARMED"
    state, mode, warning = State(), initial_mode, None
    rearm_reference = np.nan
    episode_start = int(events.event_index.min())
    suppressed_until = None
    hard_at = {int(b.onset_event): b for b in hard_ledger.itertuples()}
    history = []

    def emit(row, kind, **values):
        transitions.append(dict(event=int(row.event_index), kind=kind, **values))

    def end_warning(row, resolution):
        nonlocal warning
        warning.update(resolution=resolution, end_event=int(row.event_index))
        if resolution == "CANCELLED":
            warning["cancel_event"] = int(row.event_index)
        emit(row, resolution, warning_id=warning["warning_id"])
        warning = None

    for row in events.sort_values("event_index").itertuples():
        event = int(row.event_index)
        if event in hard_at:
            b = hard_at[event]
            if warning is not None:
                end_warning(row, "SUPERSEDED_HARD_BOUNDARY")
            emit(row, b.boundary_type, boundary_id=b.boundary_id, resume=b.resume_event)
            state, mode, history = State(), initial_mode, []
            rearm_reference = np.nan
            suppressed_until = (
                int(b.resume_event) if pd.notna(b.resume_event) else np.inf
            )
        if suppressed_until is not None:
            if event < suppressed_until:
                continue
            episode_start, suppressed_until = event, None
            emit(row, "HARD_REGAIN_START")
        history.append(row)
        masked = version == "v0.3" and bool(ambiguous(event, event, masks))
        if masked and warning is not None:
            end_warning(row, "CENSORED_REVIEW_MASK")
            mode = "ACTIVE"
        obs = state.observe(row)
        if obs is None:
            trace.append(
                dict(
                    event=event,
                    mode=mode,
                    eligible=False,
                    reason="unsupported_or_failed",
                )
            )
            continue
        arm = (mode == "DISARMED" and obs["dx"] > 0) or (
            mode == "REBUILD"
            and obs["forward_peak"]
            and (version == "v0.1" or row.end_x >= rearm_reference)
        )
        if arm and not state.relocation_affected:
            mode = "ACTIVE"
            emit(row, "ARMED", peak=state.peak)
        trace.append(
            dict(
                event=event,
                mode=mode,
                eligible=obs["eligible"],
                peak=state.peak,
                retreat=obs["retreat"],
                nonpositive=state.nonpositive,
                reason="restart"
                if obs["restart"]
                else (
                    "relocation_affected" if state.relocation_affected else "trusted"
                ),
            )
        )
        if not obs["eligible"] or masked:
            continue
        if (
            mode == "ACTIVE"
            and obs["retreat"] >= 10.0
            and (version != "v0.3" or obs["dx"] <= 0)
        ):
            warning = dict(
                warning_id=f"W{len(warnings) + 1:02d}",
                onset=event,
                onset_time=row.period_seconds,
                peak=state.peak,
                peak_time=state.peak_time,
                onset_retreat=obs["retreat"],
                maximum_retreat=obs["retreat"],
                pivot_event=np.nan,
                low=row.end_x,
                episode_start=episode_start,
                confirmation=np.nan,
                cancel_event=np.nan,
                resolution="OPEN",
                onset_run=state.nonpositive,
                onset_backward=max(state.recent, default=0),
                onset_elapsed=row.period_seconds - state.peak_time,
            )
            warnings.append(warning)
            mode = "WARNING"
            emit(row, "RESET_WARNING", warning_id=warning["warning_id"])
        if mode != "WARNING":
            continue
        retreat = max(0, warning["peak"] - row.end_x)
        warning["low"] = min(warning["low"], row.end_x)
        if version == "v0.3":
            warning["low"] = min(warning["low"], row.start_x)
        warning["maximum_retreat"] = max(
            warning["maximum_retreat"], warning["peak"] - warning["low"]
        )
        if version == "v0.3":
            if obs["dx"] <= 0 or event <= warning["onset"]:
                continue
            warning["pivot_event"] = event
            warning["pivot_elapsed"] = row.period_seconds - warning["peak_time"]
            confirm = (
                warning["maximum_retreat"] >= 20.0 or warning["pivot_elapsed"] >= 5.0
            )
            if not confirm:
                warning["resolution_retreat"] = retreat
                end_warning(row, "CANCELLED")
                mode = "ACTIVE"
                continue
        # Cancellation has priority over confirmation on the current trusted action.
        if version != "v0.3" and obs["dx"] > 0 and retreat < 10.0:
            warning["resolution_retreat"] = retreat
            end_warning(row, "CANCELLED")
            mode = "ACTIVE"
            continue
        magnitude = retreat >= 20.0 or max(state.recent, default=0) >= 10.0
        persistence = (
            row.period_seconds - warning["peak_time"] >= 5.0 or state.nonpositive >= 2
        )
        if (version == "v0.3" and confirm) or (
            version != "v0.3" and magnitude and persistence
        ):
            warning.update(
                confirmation=event,
                end_event=event,
                resolution="CONFIRMED",
                confirm_retreat=retreat,
                confirm_backward=max(state.recent, default=0),
                confirm_elapsed=row.period_seconds - warning["peak_time"],
                confirm_run=state.nonpositive,
            )
            emit(
                row,
                "CONFIRMED_RESET",
                warning_id=warning["warning_id"],
                split=warning["onset"],
            )
            episode_start = warning["onset"]
            rearm_reference = warning["peak"]
            # Replay measurements only from the retrospective onset; never detect
            # another warning while rebuilding this just-confirmed history.
            history = [r for r in history if r.event_index >= episode_start]
            state = State()
            for past in history:
                state.observe(past)
            warning, mode = None, "REBUILD"
    if warning is not None:
        end_warning(row, "CENSORED_PARENT_END")
    assert len({w["onset"] for w in warnings}) == len(warnings)
    return warnings, transitions, trace


def ambiguity_intervals(case, ledger, episode_map, first, last, candidates):
    """Unchanged scoring masks; v0.3 also censors pending warnings on entry."""
    if case in {"C15", "C17"}:
        return [(first, last, "partial case structure")]
    intervals = []
    for b in ledger.itertuples():
        if b.boundary_type == "REVIEW_DEFERRED":
            intervals.append((int(b.onset_event), last, "deferred review tail"))
        if b.boundary_type == "CLEAR_RESET" and pd.isna(b.onset_event):
            intervals.append(
                (int(b.onset_lower), int(b.confirmation_event), "unknown reset onset")
            )
    for e in episode_map.itertuples():
        if not flag(e.state_valid) and not flag(e.excluded):
            intervals.append(
                (
                    int(e.episode_start_event_index),
                    int(e.episode_end_event_index),
                    "provisional episode start",
                )
            )
    unresolved = candidates[
        candidates.warning_resolution.eq("not_confirmed_in_available_review")
        & candidates.candidate_role.eq("reset_warning")
    ]
    for c in unresolved.itertuples():
        if pd.notna(c.episode_end_event_index):
            intervals.append(
                (
                    int(c.candidate_event_index),
                    int(c.episode_end_event_index),
                    "unresolved warning outcome",
                )
            )
    return intervals


def ambiguous(lo, hi, intervals):
    return "; ".join(sorted({why for a, b, why in intervals if lo <= b and hi >= a}))


def compact(values):
    return ";".join(str(int(v)) for v in values if pd.notna(v))


def evaluate(events, parents, boundaries, candidates, episode_map, version="v0.1"):
    case_rows, details, all_runs = [], [], {}
    for parent in parents.sort_values("case_id").itertuples():
        case = parent.case_id
        ev = events[events.case_id.eq(case)].sort_values("event_index")
        ledger = boundaries[boundaries.case_id.eq(case)]
        cand = candidates[candidates.case_id.eq(case)]
        hard = ledger[ledger.boundary_type.isin(HARD)]
        exclusions = ledger[ledger.boundary_type.isin(EXCLUDE)]
        masks = ambiguity_intervals(
            case,
            ledger,
            episode_map[episode_map.case_id.eq(case)],
            parent.first_event_index,
            parent.last_event_index,
            cand,
        )
        if len(exclusions):
            warnings, transitions, trace = [], [], []
        else:
            warnings, transitions, trace = replay(ev, hard, version, masks=masks)
        all_runs[case] = (warnings, transitions, trace)
        records = []

        def add(kind, classification, **kwargs):
            records.append(
                dict(case_id=case, kind=kind, classification=classification, **kwargs)
            )

        # Hard boundaries are supplied constraints; comparison checks preservation.
        for b in hard.itertuples():
            pred = next(
                (t for t in transitions if t.get("boundary_id") == b.boundary_id), None
            )
            matches = pred is not None and pred["event"] == b.onset_event
            if pd.notna(b.resume_event):
                matches = matches and any(
                    t["kind"] == "HARD_REGAIN_START" and t["event"] == b.resume_event
                    for t in transitions
                )
            add(
                "HARD_BOUNDARY",
                "UNSCORED_AMBIGUOUS"
                if case in {"C15", "C17"}
                else ("MATCH" if matches else "HARD_BOUNDARY_MISMATCH"),
                reviewed_id=b.boundary_id,
                reviewed_onset=b.onset_event,
                predicted_onset=pred["event"] if pred else np.nan,
                reviewed_resume=b.resume_event,
                predicted_resume=pred["resume"] if pred else np.nan,
                explanation="Reviewed hard boundary passed through; not an independent detection benchmark.",
            )
        for b in exclusions.itertuples():
            add(
                "NO_EPISODE",
                "MATCH"
                if not warnings and not transitions
                else "HARD_BOUNDARY_MISMATCH",
                reviewed_id=b.boundary_id,
                explanation="Reviewed exclusion: zero predicted episodes.",
            )

        def segment(event):
            return sum(int(b.onset_event) <= event for b in hard.itertuples())

        scored_predictions = []
        for w in warnings:
            w["ambiguity"] = ambiguous(w["onset"], w["end_event"], masks)
            w["paired_id"] = ""
            if w["resolution"] == "CONFIRMED" and not w["ambiguity"]:
                scored_predictions.append(w)
        resets = ledger[ledger.boundary_type.eq("CLEAR_RESET")]
        for b in resets.itertuples():
            if pd.isna(b.onset_event) or case in {"C15", "C17"}:
                add(
                    "REVIEWED_RESET",
                    "UNSCORED_AMBIGUOUS",
                    reviewed_id=b.boundary_id,
                    reviewed_onset=b.onset_event,
                    reviewed_confirmation=b.confirmation_event,
                    explanation=f"Exact reviewed onset unresolved in {b.onset_lower:g}-{b.onset_upper:g}; no inferred target.",
                )
                continue
            # A later rebuilt CONTINUE is not a late detection of an old reset.
            # Use the reviewed excursion's last sample and preceding CONTINUE as
            # alignment bounds only, never as inferred football onset labels.
            before = cand[
                cand.human_label.eq("CONTINUE")
                & cand.candidate_role.eq("normal_active_episode_sample")
                & cand.candidate_event_index.lt(b.onset_event)
            ]
            lower = (
                before.candidate_event_index.max() + 1
                if len(before)
                else parent.first_event_index
            )
            possible = [
                w
                for w in scored_predictions
                if not w["paired_id"]
                and segment(w["onset"]) == segment(b.onset_event)
                and w["onset"] <= b.last_reset_sample
                and w["confirmation"] >= lower
            ]
            w = (
                min(
                    possible,
                    key=lambda w: (abs(w["onset"] - b.onset_event), w["onset"]),
                )
                if possible
                else None
            )
            classification = (
                "MISSED_RESET"
                if w is None
                else (
                    "MATCH"
                    if w["onset"] == b.onset_event
                    else ("EARLY_SPLIT" if w["onset"] < b.onset_event else "LATE_SPLIT")
                )
            )
            if w is not None:
                w["paired_id"] = b.boundary_id
                w["split_classification"] = classification
            add(
                "REVIEWED_RESET",
                classification,
                reviewed_id=b.boundary_id,
                reviewed_onset=b.onset_event,
                reviewed_confirmation=b.confirmation_event,
                predicted_onset=w["onset"] if w else np.nan,
                predicted_confirmation=w["confirmation"] if w else np.nan,
                explanation="No scored confirmation aligned with the reviewed excursion."
                if w is None
                else (
                    f"Nearest predicted onset {w['onset']} versus reviewed {int(b.onset_event)}; "
                    f"confirmation {int(w['confirmation'])} versus reviewed {int(b.confirmation_event)}."
                ),
            )
        cancelled_samples = cand[
            cand.warning_resolution.eq("cancelled_or_retained_continue")
        ]
        for w in warnings:
            overlap_cancel = cancelled_samples[
                cancelled_samples.candidate_event_index.between(
                    w["onset"], w["end_event"]
                )
            ]
            if w["ambiguity"]:
                classification = "UNSCORED_AMBIGUOUS"
            elif w["resolution"] == "CONFIRMED":
                classification = w.get("split_classification", "EXTRA_RESET")
            elif w["resolution"] == "CANCELLED":
                overlaps_reset = any(
                    pd.notna(b.onset_event)
                    and w["onset"] <= b.onset_event <= w["end_event"]
                    for b in resets.itertuples()
                )
                classification = (
                    "MISSED_RESET" if overlaps_reset else "CORRECT_WARNING_CANCEL"
                )
            else:
                classification = "FALSE_WARNING_ONLY"
            w["classification"] = classification
            add(
                "PREDICTED_WARNING",
                classification,
                warning_id=w["warning_id"],
                reviewed_id=w["paired_id"],
                predicted_onset=w["onset"],
                predicted_confirmation=w["confirmation"],
                predicted_cancellation=w["cancel_event"],
                end_event=w["end_event"],
                resolution=w["resolution"],
                stored_peak=w["peak"],
                stored_peak_time=w["peak_time"],
                warning_onset_time=w["onset_time"],
                predicted_parent_episode_start=w["episode_start"],
                onset_retreat=w["onset_retreat"],
                onset_elapsed=w["onset_elapsed"],
                onset_backward=w["onset_backward"],
                onset_run=w["onset_run"],
                warning_low=w["low"],
                maximum_warning_retreat=w["maximum_retreat"],
                pivot_event=w["pivot_event"],
                pivot_elapsed=w.get("pivot_elapsed"),
                confirm_retreat=w.get("confirm_retreat"),
                confirm_elapsed=w.get("confirm_elapsed"),
                confirm_run=w.get("confirm_run"),
                confirm_backward=w.get("confirm_backward"),
                cancellation_retreat=w.get("resolution_retreat"),
                reviewed_warning_samples=";".join(overlap_cancel.candidate_id),
                explanation=w["ambiguity"]
                or (
                    f"Forward pivot: maximum retreat {w['maximum_retreat']:.3f}, peak age {w.get('pivot_elapsed', np.nan):.3f}s; {w['resolution']}."
                    if version == "v0.3" and pd.notna(w["pivot_event"])
                    else ""
                )
                or (
                    "Warning at a reviewed reset onset was cancelled; the resulting split displacement is scored on the reviewed-reset row."
                    if classification == "MISSED_RESET"
                    else (
                        "Two evidence families met before any cancellation."
                        if w["resolution"] == "CONFIRMED"
                        else (
                            "Trusted forward action reduced frozen-reference retreat below 10."
                            if w["resolution"] == "CANCELLED"
                            else "Warning remained unresolved until a hard boundary or observation end; no split."
                        )
                    )
                ),
            )
        if masks:
            add(
                "REVIEW_SCOPE",
                "UNSCORED_AMBIGUOUS",
                explanation="; ".join(f"{a}-{b}: {why}" for a, b, why in masks),
            )
        rows = pd.DataFrame(records)

        def count(kind, label):
            if rows.empty:
                return 0
            return int((rows.kind.eq(kind) & rows.classification.eq(label)).sum())

        starts = [] if len(exclusions) else [parent.first_event_index]
        starts += [
            int(b.resume_event) for b in hard.itertuples() if pd.notna(b.resume_event)
        ]
        starts += [w["onset"] for w in warnings if w["resolution"] == "CONFIRMED"]
        case_rows.append(
            dict(
                version=version,
                case_id=case,
                reviewed_hard_boundaries=";".join(
                    f"{b.boundary_id}:{int(b.onset_event)}"
                    + (f"->{int(b.resume_event)}" if pd.notna(b.resume_event) else "")
                    for b in hard.itertuples()
                ),
                predicted_hard_boundaries=";".join(
                    str(t["event"]) for t in transitions if t["kind"] in HARD
                ),
                reviewed_episode_starts=compact(
                    episode_map.loc[
                        episode_map.case_id.eq(case), "episode_start_event_index"
                    ]
                ),
                opening_restart_events=compact(
                    ev.loc[ev.restart_context.notna(), "event_index"]
                ),
                reviewed_reset_onsets=";".join(
                    f"{b.boundary_id}:"
                    + (
                        str(int(b.onset_event))
                        if pd.notna(b.onset_event)
                        else f"unknown[{int(b.onset_lower)},{int(b.onset_upper)}]"
                    )
                    for b in resets.itertuples()
                ),
                predicted_warning_onsets=compact(w["onset"] for w in warnings),
                predicted_cancellations=compact(w["cancel_event"] for w in warnings),
                predicted_confirmations=compact(w["confirmation"] for w in warnings),
                predicted_reset_splits=compact(
                    w["onset"] for w in warnings if w["resolution"] == "CONFIRMED"
                ),
                predicted_episode_starts=compact(sorted(starts)),
                predicted_episode_count=len(starts),
                reviewed_scored_resets=sum(
                    pd.notna(b.onset_event) for b in resets.itertuples()
                ),
                matched_resets=count("REVIEWED_RESET", "MATCH"),
                early_splits=count("REVIEWED_RESET", "EARLY_SPLIT"),
                late_splits=count("REVIEWED_RESET", "LATE_SPLIT"),
                missed_resets=count("REVIEWED_RESET", "MISSED_RESET"),
                extra_final_splits=count("PREDICTED_WARNING", "EXTRA_RESET"),
                warning_count=len(warnings),
                predicted_confirmation_count=sum(
                    w["resolution"] == "CONFIRMED" for w in warnings
                ),
                predicted_cancellation_count=sum(
                    w["resolution"] == "CANCELLED" for w in warnings
                ),
                forward_pivot_count=sum(pd.notna(w["pivot_event"]) for w in warnings),
                terminated_before_pivot=sum(
                    w["resolution"] not in {"CONFIRMED", "CANCELLED"} for w in warnings
                ),
                warning_only_false_positives=count(
                    "PREDICTED_WARNING", "FALSE_WARNING_ONLY"
                ),
                correctly_cancelled_warnings=count(
                    "PREDICTED_WARNING", "CORRECT_WARNING_CANCEL"
                ),
                hard_boundary_mismatches=count(
                    "HARD_BOUNDARY", "HARD_BOUNDARY_MISMATCH"
                )
                + count("NO_EPISODE", "HARD_BOUNDARY_MISMATCH"),
                unscored_warnings=count("PREDICTED_WARNING", "UNSCORED_AMBIGUOUS"),
                unscored_ambiguous_case=bool(masks),
            )
        )
        details.extend(dict(version=version, **r) for r in records)
    return pd.DataFrame(case_rows), pd.DataFrame(details), all_runs


def focused_checks():
    """Small executable checks of transition ordering, reference scope and safeguards."""

    def sample(actions):
        return pd.DataFrame(
            [
                dict(
                    event_index=i + 1,
                    period_seconds=float(i),
                    start_x=a[0],
                    end_x=a[1],
                    provider_context="",
                    restart_context="",
                    safe_action=True,
                    event_team_id=904,
                    event_type="Pass",
                )
                for i, a in enumerate(actions)
            ]
        )

    hard = pd.DataFrame(
        columns=["onset_event", "boundary_id", "boundary_type", "resume_event"]
    )
    x = sample([(80, 100), (100, 86), (86, 60)])
    w, _, _ = replay(x, hard)
    assert len(w) == 1 and w[0]["onset"] == 2 and w[0]["confirmation"] == 3
    assert w[0]["onset_elapsed"] == 0  # zero elapsed onset still warns
    x = sample([(80, 100), (100, 85), (85, 96)])
    x.loc[2, "period_seconds"] = 10
    w, _, _ = replay(x, hard)
    assert w[0]["resolution"] == "CANCELLED" and w[0]["resolution_retreat"] == 4
    assert pd.isna(w[0]["confirmation"])  # cancellation before confirmation
    x = sample([(80, 100), (100, 85), (85, 60), (np.nan, np.nan)])
    x.loc[3, "safe_action"] = False
    h = pd.DataFrame(
        [
            dict(
                onset_event=3,
                boundary_id="H1",
                boundary_type="OPPONENT_CONTROL",
                resume_event=4,
            )
        ]
    )
    w, t, _ = replay(x, h)
    assert w[0]["resolution"] == "SUPERSEDED_HARD_BOUNDARY"
    assert any(e["kind"] == "HARD_REGAIN_START" and e["event"] == 4 for e in t)
    x = sample([(120, 40), (40, 20)])
    x.loc[0, "restart_context"] = "Kick Off"
    assert not replay(x, hard)[0]
    x = sample([(80, 100), (100, 115), (60, 40), (40, 50)])
    x.loc[1, "provider_context"] = "pass.outcome:Incomplete"
    assert not replay(x, hard)[0]  # failed endpoint and contest relocation suppressed
    x = sample([(80, 100), (90, 70), (70, 95), (95, 75), (75, 70)])
    x.loc[:, "period_seconds"] = [0, 6, 7, 8, 9]
    w1, _, _ = replay(x, hard, "v0.1")
    w2, _, trace = replay(x, hard, "v0.2")
    assert sum(w["resolution"] == "CONFIRMED" for w in w1) == 2
    assert sum(w["resolution"] == "CONFIRMED" for w in w2) == 1
    assert trace[2]["mode"] == "REBUILD" and trace[2]["peak"] == 95
    assert (
        trace[2]["peak"] != w2[0]["peak"]
    )  # old reference is a guard, not the new peak


def v3_checks():
    def sample(actions):
        return pd.DataFrame(
            [
                dict(
                    event_index=i + 1,
                    period_seconds=float(i),
                    start_x=a,
                    end_x=b,
                    provider_context="",
                    restart_context="",
                    safe_action=True,
                    event_team_id=904,
                    event_type="Pass",
                )
                for i, (a, b) in enumerate(actions)
            ]
        )

    hard = pd.DataFrame(
        columns=["onset_event", "boundary_id", "boundary_type", "resume_event"]
    )
    x = sample([(80, 50), (50, 40), (40, 60)])
    w, _, _ = replay(x, hard, "v0.3")
    assert len(w) == 1 and w[0]["onset"] == 1 and w[0]["confirmation"] == 3
    assert w[0]["maximum_retreat"] == 40 and w[0]["pivot_event"] == 3
    # Exact predicate boundaries, not candidate threshold alternatives.
    for retreat, pivot_time, expected in [
        (20, 1, "CONFIRMED"),
        (19, 5, "CONFIRMED"),
        (19, 4.999, "CANCELLED"),
    ]:
        x = sample([(80, 80 - retreat), (80 - retreat, 82 - retreat)])
        x.loc[1, "period_seconds"] = pivot_time
        w, _, _ = replay(x, hard, "v0.3")
        assert w[0]["resolution"] == expected
    x = sample([(50, 64), (64, 61.8), (61.8, 51.5), (51.5, 49.9), (49.9, 50.2)])
    w, _, _ = replay(x, hard, "v0.3")
    assert w[0]["resolution"] == "CANCELLED" and w[0]["resolution_retreat"] > 10
    x = sample([(80, 100), (100, 95), (70, 80)])
    assert not replay(x, hard, "v0.3")[0]  # no warning on forward restoration
    x = sample([(120, 40), (40, 39)])
    x.loc[0, "restart_context"] = "Kick Off"
    assert not replay(x, hard, "v0.3")[0]
    x = sample([(80, 100), (100, 115), (60, 40), (40, 50)])
    x.loc[1, "provider_context"] = "pass.outcome:Incomplete"
    assert not replay(x, hard, "v0.3")[0]
    x = sample([(80, 50), (50, 40), (40, 70), (np.nan, np.nan)])
    x.loc[3, "safe_action"] = False
    h = pd.DataFrame(
        [
            dict(
                onset_event=3,
                boundary_id="H1",
                boundary_type="OPPONENT_CONTROL",
                resume_event=4,
            )
        ]
    )
    w, _, _ = replay(x, h, "v0.3")
    assert w[0]["resolution"] == "SUPERSEDED_HARD_BOUNDARY" and pd.isna(
        w[0]["pivot_event"]
    )
    w, _, _ = replay(x.iloc[:3], hard, "v0.3", masks=[(2, 3, "deferred")])
    assert len(w) == 1 and w[0]["resolution"] == "CENSORED_REVIEW_MASK"
    assert pd.isna(w[0]["confirmation"])
    w, _, _ = replay(x.iloc[:2], hard, "v0.3")
    assert w[0]["resolution"] == "CENSORED_PARENT_END"
    x = sample([(80, 100), (90, 70), (70, 95), (95, 75), (75, 70), (70, 105)])
    w, transitions, trace = replay(x, hard, "v0.3")
    assert len(w) == 1 and w[0]["confirmation"] == 3
    assert trace[3]["mode"] == "REBUILD" and trace[3]["peak"] == 95
    assert [t["event"] for t in transitions if t["kind"] == "ARMED"] == [6]


def table(frame):
    def cell(v):
        if pd.isna(v):
            return "—"
        if isinstance(v, (float, np.floating)):
            return f"{v:g}"
        return str(v).replace("|", "/").replace("\n", " ")

    return "\n".join(
        [
            "| " + " | ".join(frame.columns) + " |",
            "| " + " | ".join(["---"] * len(frame.columns)) + " |",
            *[
                "| " + " | ".join(cell(v) for v in row) + " |"
                for row in frame.itertuples(index=False, name=None)
            ],
        ]
    )


def write_report(cases, details, hashes):
    metrics = [
        "reviewed_scored_resets",
        "matched_resets",
        "early_splits",
        "late_splits",
        "missed_resets",
        "extra_final_splits",
        "warning_count",
        "predicted_confirmation_count",
        "predicted_cancellation_count",
        "warning_only_false_positives",
        "correctly_cancelled_warnings",
        "hard_boundary_mismatches",
        "unscored_warnings",
        "unscored_ambiguous_case",
    ]
    totals = cases.groupby("version")[metrics].sum().T.reset_index(names="metric")
    reset_rows = details[
        details.version.eq("v0.1")
        & details.kind.eq("REVIEWED_RESET")
        & ~details.classification.eq("UNSCORED_AMBIGUOUS")
    ][
        [
            "case_id",
            "classification",
            "reviewed_onset",
            "predicted_onset",
            "reviewed_confirmation",
            "predicted_confirmation",
        ]
    ]
    extra = details[
        details.kind.eq("PREDICTED_WARNING") & details.classification.eq("EXTRA_RESET")
    ]
    extras = []
    for (case, onset), rows in extra.groupby(["case_id", "predicted_onset"]):
        r = rows.iloc[0]
        reason = (
            f"At {r.predicted_confirmation:g}: retreat {r.confirm_retreat:.1f}, "
            f"recent backward {r.confirm_backward:.1f}; "
            f"peak age {r.confirm_elapsed:.3f}s, run {r.confirm_run:g}."
        )
        extras.append(
            dict(
                case=case,
                split=int(onset),
                versions=", ".join(rows.version),
                evidence=reason,
            )
        )
    final = cases[cases.version.eq("v0.2")][
        [
            "case_id",
            "matched_resets",
            "early_splits",
            "late_splits",
            "missed_resets",
            "extra_final_splits",
            "warning_count",
            "unscored_warnings",
        ]
    ].rename(
        columns={
            "case_id": "case",
            "matched_resets": "match",
            "early_splits": "early",
            "late_splits": "late",
            "missed_resets": "miss",
            "extra_final_splits": "extra",
            "warning_count": "warnings",
            "unscored_warnings": "unscored warnings",
        }
    )
    source_hashes = "\n".join(
        f"- `{p.relative_to(ROOT).as_posix()}`: `{h}`" for p, h in hashes.items()
    )
    text = f"""# Phase 3A-3: Candidate Rule v0.1 and one v0.2 replay

Bounded C01–C28 replay. **NOT READY — ONE SPECIFIC MATERIAL FAILURE REMAINS.**
The blocking failure is false confirmation of reviewed continuation, particularly C16's
cancelled warning. The one re-arm revision removes four extra splits but does not fix that failure.
No production segmentation code, human labels, thresholds or earlier artifacts were changed.

## A. Rule replayed

Candidate Rule **v0.1**, with the supplied numerical settings unchanged:

1. **ACTIVE / ARMED:** arm only after trusted Leverkusen forward progression has established
   a valid episode-local attacking peak. Opening restart backward vectors cannot arm the detector.
   Failed/unknown pass endpoints and contest/relocation jumps cannot establish trusted progression.
2. **ACTIVE → WARNING:** on a trusted deliberate Leverkusen action, warn when retreat from the
   stored episode peak **>=10.0**. Store onset event/time/retreat, the pre-warning peak and its
   timestamp, and the current warning low. Do not split yet; freeze the warning reference.
3. **Magnitude evidence:** frozen-reference retreat **>=20.0 OR** largest relevant deliberate
   backward-action magnitude **>=10.0**.
4. **Persistence evidence:** time since the stored peak **>=5.0 seconds OR** current trusted
   nonpositive run **>=2 actions**. These are two evidence families, not four independent votes.
5. **WARNING → CONFIRMED RESET:** magnitude **AND** persistence, provided cancellation or a hard
   boundary has not superseded the warning. Create one excursion and one final split at its onset.
6. **WARNING → CANCEL:** before confirmation, trusted forward progression reducing frozen-reference
   retreat to **<10.0** cancels. Return to ACTIVE in the same episode; exact peak recovery is unnecessary.
7. **CONFIRMED RESET → REBUILD:** start the new episode retrospectively at the stored onset, clear
   old peak/run state and disarm. Backward/circulating reset-phase samples alone cannot create another cut.
8. **REBUILD → ACTIVE:** require a trusted forward action establishing a new episode-local peak
   after reset onset. Hard football boundaries always take precedence over all soft transitions.

Execution conventions resolve implementation details without a parameter search. Initial arming uses
the first trusted forward action with a valid local peak; only REBUILD requires exceeding the local peak.
A successful forward restart may arm from its endpoint, while all restart vectors are excluded from
reset evidence. Restart backward endpoints seed context without arming. The existing diagnostic's
three-trusted-action window defines “largest relevant backward action”; unsupported observations do not
supply vectors, failed passes break the nonpositive run, and contest-affected drawdown stays ineligible
until peak restoration. The latest equal-peak vertex supplies peak time, so onset can have zero age.
All four settings are fixed, with inclusive evidence comparisons and strict cancellation comparison.

Each eligible action updates state, checks cancellation first, then confirmation. Confirmation can
occur on the warning action itself if both families already hold; it is not artificially delayed.
On confirmation, only measurement history from the predicted onset through confirmation is rebuilt;
soft transitions are not replayed inside that history. Re-arming is evaluated on subsequent actions.
The old peak never becomes the new episode's measurement reference.

Inputs are the existing 1,960-row reviewed event snapshot, 28-parent source, human boundary ledger,
candidate diagnostics and episode map. Soft predictions never consume reviewed soft splits, labels or
episode membership. Hard boundaries/exclusions are supplied constraints: zero hard mismatches verifies
preservation, **not independent hard-boundary detection accuracy**. The 26 eligible parent starts and
15 reviewed regains are preserved, including starts lacking a spatial vector. Opening restarts are
start context rather than extra cuts; C27/C28 have no predicted episodes. No data were downloaded.

## B. Overall replay

{table(totals)}

The nine scored reset targets are the encoded onsets, including C09/C11 even though their pre-split
quantitative calibration references were unavailable. The three unknown onsets are never imputed.
Exact onset matches are counted separately from early/late splits. All confirmation timings remain
visible below; an exact split match does not assert an exact human-confirmation-time match.

Comparison is constrained to the same reviewed hard-control span and the same reviewed excursion:
the interval after its preceding reviewed ordinary CONTINUE through its last reset-phase sample.
Within that alignment window, nearest-onset pairing is one-to-one; there is no tolerance search.
A predicted cut after the last reset-phase sample is an extra cut, not a late match to an old reset.
No alignment limit becomes a newly inferred human onset. The ledger supplies continuation intervals;
absence of another cut inside a fully reviewed interval is the extra-split reference.

Unresolved onset windows and ensuing provisional membership, deferred tails, C14's unresolved warning
and all partial C15/C17 structure are **UNSCORED_AMBIGUOUS**. Predictions run through those intervals,
but any warning-to-resolution interval overlapping them is excluded from error counts. These masks
affect scoring only. The nine affected cases are C04, C09, C10, C11, C12, C14, C15, C16 and C17.
The partial C17 hard boundary is also unscored, while still preserved. The other 27 consolidated hard
boundaries and both no-episode exclusions match in both versions.

Warning counts include every firing, including immediate confirmations and unscored warnings.
The nine correct cancellations agree with reviewed continuation; only C22 overlaps an explicitly
reviewed cancelled-warning sample. They are not nine independently reviewed cancellation timestamps.
C18 additionally cancels the warning at its reviewed onset and later confirms a displaced onset;
that cancellation is not counted as correct. No scored warning merely expires or is superseded without
confirmation/cancellation, hence zero FALSE_WARNING_ONLY. Cancelled warnings do not add episode splits.
The CSV detail rows distinguish reviewed-target results from predicted-warning results to avoid
double-counting matches or C18's warning failure.

## C. Case-level mismatches

Both versions have the same nine reviewed-reset alignment results:

{table(reset_rows)}

- **C04:** magnitude and peak age already satisfy both families at 176, one event before reviewed
  onset 177. v0.1 re-arms at 180 below the abandoned peak and splits again at 185, before human
  confirmation 189. v0.2 removes the second cut; the early onset remains.
- **C09/C11:** failed corners supply no trusted forward arming action. Deep backward recycle
  actions 576/783 occur while disarmed, so both reviewed onsets are missed. Later forward actions
  579/791 arm against already accumulated local retreat and generate extra cuts. No failed endpoint
  or inferred onset is substituted to rescue those targets.
- **C10:** the opening throw-in lacks a safe vector and the early trusted actions all go backward.
  The detector remains disarmed at reviewed onset 2416. Forward action 2423 arms and immediately
  splits the reviewed rebuilt phase; v0.1 adds a further cut at 2442. v0.2 removes only the latter.
- **C12:** the backward opening corner does not arm. The subsequent clearance/recovery produces
  relocation-affected drawdown at 2438, which cannot supply reset evidence under the inherited
  safeguards. The known onset is missed; the later unknown onset remains unscored.
- **C18:** warning 1296 has retreat 10.2, backward magnitude 3.9 and peak age 9.980s. Persistence
  alone cannot confirm. Forward event 1297 reduces retreat to 8.5 and cancels; event 1300 starts
  a new warning, confirmed at 1304. The split is therefore late even though confirmation matches.
- **C07/C08:** split onsets match, but algorithm confirmation is 691 versus reviewed 694 and
  2770 versus reviewed 2768, respectively. C07 meets the run alternative earlier; C08 needs later
  retreat magnitude. These timing differences are visible rather than counted as extra cuts.

Every scored extra split is listed below. Each row meets the unchanged magnitude/persistence gate
inside an interval the review retains as one episode. Values are at algorithm confirmation, not
substituted onset features; versions absent from a row did not generate that extra split.

{table(pd.DataFrame(extras))}

C06's retained post-regain buildup is confirmed from retreat plus elapsed time. C13 and C14 show
ordinary recycling satisfying the backward-magnitude/run alternatives. C16's first extra is the
explicitly cancelled warning, while its 624 excursion is also inside reviewed continuation. C18's
four extras include forward arming within a post-regain recycle at 1439 and later backward runs;
the existence of two numerical families does not establish attack abandonment in these cases.

Final v0.2 case counts (all zero-error cases retained):

{table(final)}

## D. Named stress tests

| Case | Observed behavior |
| --- | --- |
| C05 | Forward free-kick endpoint arms; warning 3612 at zero peak age; confirmation 3614; exact onset match in both versions. |
| C18 | Modest backward magnitude cannot confirm 1296; cancellation 1297 shifts final onset to 1300; four other scored extra cuts remain. |
| C16 | Warning 541 immediately confirms: retreat 12.5, backward 10.3, run 2. The reviewed cancellation is lost in both versions. At renewed progression 544 retreat is still 13.8 from peak 64.0, so even a delayed decision would not meet the supplied <10 cancellation condition then. The later unknown reset stays unscored. |
| C25 | Recorded warning samples have retreat 7.9/8.9, below 10. No warning or split occurs despite the four-action run; no cancellation is invented. |
| C04 | Local forward progression reaches a new local peak below 97.2 before human confirmation. v0.1 creates an extra cut at 185; v0.2 suppresses it. |
| C09/C10 | Reviewed resets missed while disarmed; first forward rebound creates extra 579/2423. v0.2 removes later repeated cuts 585/600 and 2442, but cannot fix the first extra. |
| C20 | Zero warnings/splits; failed endpoints and relocation cannot establish reset evidence. |
| C22 | Warning 425 cancels at 427 with retreat 8.2, before exact peak restoration at 428. Zero split in both versions. |
| C24 | Opening backward kickoff supplies endpoint context only; zero warnings/splits. |
| C27/C28 | Explicit no-episode exclusions preserved; zero warnings and zero episodes. |

## E. One justified revision: v0.2

v0.1 has a repeated, generalizable re-entry failure: C04 re-arms below its abandoned 97.2 peak and
cuts the same reviewed excursion again; C09/C10 likewise generate repeated cuts in rebuilt phases.
This also violates the requirement to avoid repeated splits for an established reset excursion.

**The only change:** while REBUILD, the otherwise eligible forward action must additionally reach
the stored pre-warning peak before re-arming. This uses the already stored reference as a separate
re-arm guard, never as a new-episode peak or run value. Hard boundaries clear the guard. Initial arming,
warning, magnitude, persistence, cancellation, retrospective placement and all numeric settings are
unchanged. Cancellation still does not require full peak recovery. No new feature or case exception
is introduced. v0.2 was evaluated as one fixed revision, without threshold or alternative-rule search.

v0.2 removes exactly four scored extras: C04:185, C09:585/600 and C10:2442. One unscored C11 cut
also disappears. It creates no new scored mismatch; all remaining target timings and cancellations
are unchanged. Its stricter re-arm condition may suppress legitimate deeper attacks that never regain
the old peak; this bounded replay does not establish season-wide recall. No v0.3 is proposed or run.

## F. Lock readiness

**NOT READY — ONE SPECIFIC MATERIAL FAILURE REMAINS.**

The specific blocking failure is **confirmation of reviewed continuation as attack abandonment**.
C16:541 is a direct reviewed counterexample: the 10.3 backward action and two-action run immediately
confirm a warning the human review cancels. The same gate produces extra splits in C06, C13, C14 and
C18; it is not an isolated onset-timing discrepancy. v0.2 still has **13 scored extra final splits**.
This one blocker is sufficient to reject lock. The four missed known resets, early C04 onset and late
C18 onset are additional documented mismatches, not accepted limitations hidden by that decision label.

Stop here: the permitted revision has been used. Neither version is locked or promoted to production,
and this report does not open another analysis phase or propose another rule.

Reproduce with `.venv\\Scripts\\python.exe scripts/reset_rule_replay.py`.
Six focused executable transition/safeguard checks run before output, together with source completeness,
one-split-per-warning, retrospective-onset, no-episode, count-reconciliation and input-immutability checks.
Outputs are this report and exactly two CSVs: `phase3a3_reset_rule_replay_cases.csv` and
`phase3a3_reset_rule_replay_details.csv` under `outputs/diagnostics/`. No figure is necessary.
The case CSV compares hard/reset boundaries, warnings, cancellations, confirmations and final starts;
the detail CSV contains reference results and one row per predicted warning with its frozen evidence.

Input SHA-256 values:

{source_hashes}
"""
    REPORT.write_text(text, encoding="utf-8")


def append_v3_report(cases, details):
    metrics = [
        "matched_resets",
        "early_splits",
        "late_splits",
        "missed_resets",
        "extra_final_splits",
        "warning_count",
        "correctly_cancelled_warnings",
        "warning_only_false_positives",
        "hard_boundary_mismatches",
        "unscored_warnings",
        "unscored_ambiguous_case",
    ]
    comparison = (
        cases[cases.version.isin(["v0.2", "v0.3"])]
        .groupby("version")[metrics]
        .sum()
        .T.reset_index(names="metric")
    )
    d = details[details.version.eq("v0.3")]
    targets = d[
        d.kind.eq("REVIEWED_RESET") & ~d.classification.eq("UNSCORED_AMBIGUOUS")
    ][
        [
            "case_id",
            "classification",
            "reviewed_onset",
            "predicted_onset",
            "reviewed_confirmation",
            "predicted_confirmation",
        ]
    ]
    extras = d[d.kind.eq("PREDICTED_WARNING") & d.classification.eq("EXTRA_RESET")][
        [
            "case_id",
            "predicted_onset",
            "pivot_event",
            "maximum_warning_retreat",
            "pivot_elapsed",
        ]
    ].copy()
    extras["criterion"] = np.where(
        extras.maximum_warning_retreat.ge(20),
        np.where(extras.pivot_elapsed.ge(5), "retreat and time", "retreat"),
        "time",
    )
    extras["pivot_elapsed"] = extras.pivot_elapsed.round(3)
    extras["maximum_warning_retreat"] = extras.maximum_warning_retreat.round(3)
    counts = (
        cases[cases.version.eq("v0.3")][
            [
                "forward_pivot_count",
                "predicted_confirmation_count",
                "predicted_cancellation_count",
                "terminated_before_pivot",
            ]
        ]
        .sum()
        .reset_index()
    )
    counts.columns = ["v0.3 warning outcome", "count"]
    historical = REPORT.read_text(encoding="utf-8")
    text = f"""

# Candidate Rule v0.3 — final bounded replay

## A. v0.3 rule

The three detector states are ACTIVE, WARNING and REBUILD. ACTIVE initially has no measurement;
the first trustworthy controlled Leverkusen Pass/Carry supplies the local start/end reference,
including a backward action. No earlier forward action is required. A restart contributes only
its trusted endpoint and cannot itself trigger a warning. Failed endpoints, unsupported vectors
and contest-affected drawdown retain the v0.2 exclusions; missing coordinates are never filled.

ACTIVE enters WARNING only on a trusted **nonpositive** action with retreat **>=10.0**.
Freeze peak x/time and warning onset event/time/retreat. Track the maximum frozen-reference
retreat and lowest trusted action vertex (start or end), without interpolating between events.
Forward restoration below a peak cannot initiate a new warning.

WARNING does not confirm on backward magnitude, run length, retreat or elapsed time alone.
Wait for the first subsequent eligible trusted forward action. At this pivot, confirm if
**maximum warning retreat >=20.0 OR elapsed time since frozen peak >=5.0 seconds**;
otherwise cancel (both strictly below their limits). The clock runs from the frozen peak,
not from warning onset or the last backward action. Backward magnitude/run are diagnostics only.
Full or partial restoration on the pivot does not override confirmation if either criterion holds.

Confirmation creates one split at the stored warning onset, rebuilds measurements from that onset
through the pivot, clears old peak/run state and enters REBUILD. The pivot itself cannot immediately
re-arm. Thereafter preserve the exact v0.2 guard: a trusted forward action must establish a new local
peak and reach/exceed the stored pre-warning re-entry reference. That separate guard does not become
the new episode's peak. Cancellation preserves the current episode without requiring old-peak recovery.

Hard boundaries have priority even on a potential pivot event, supersede a warning without a soft split,
and clear state/reference. Observation end censors an unpivoted warning. Entering an existing review
mask also censors it, and soft decisions are suppressed while masked. Measurements can continue from
trusted observations, but no human soft boundary is inserted. Mask definitions and scored target
alignment are unchanged. This mandated mask behavior differs from the historical replays, which
logged unscored warnings inside masks; reduced unscored warning frequency is not an accuracy gain.

## B. v0.2 vs v0.3

{table(comparison)}

All nine encoded reset targets remain scored. The three unknown onsets remain unscored.
Each matched/early/late target appears once; warning rows must not be added again to target counts.

{table(counts)}

The sole warning without a pivot is C14:2503, censored at review-mask entry 2506. None ends at a hard
boundary or parent observation end in this particular replay; focused checks cover both mechanisms.
All 19 confirmations and 13 cancellations reach a pivot. Of the confirmations, eight align with
reviewed resets (seven exact, one early), and eleven are extra splits. Correct cancellations agree
with the reviewed continuation intervals; they are not thirteen separately reviewed pivot timestamps.

## C. Reviewed reset alignment

{table(targets)}

C09, C10 and C11 change from missed to exact onset matches. C18 changes from late to exact;
the elapsed criterion confirms its first pivot rather than cancelling its reviewed onset.
C05 also matches: the observed excursion reaches 47.9 before pivot 3617, despite zero peak age
at onset. No special case is used. C04 still opens one event early, at 176 instead of 177.
C12 remains missed because its recovery drawdown is relocation-affected after the corner/clearance;
the trust safeguard is not relaxed to match the human boundary. Pivot confirmation timings are
reported separately from the human confirmation events, without claiming they coincide.

## D. Remaining extra splits

Every scored v0.3 extra is shown below. All occur in reviewed continuation, including post-regain
and rebuilt episodes. The criterion column explains which fixed pivot test produced each cut.

{table(extras)}

The net change is only **13 to 11 extra splits**, not a broad removal of false fragmentation.
C04:168 is an ordinary retreat whose 21.3 maximum now confirms even though its pivot restores
progression. C04:201 and C06:448 begin in newly regained episodes. Time alone confirms five extras
(C04:201, C13:316/376, C14:2452, C16:616), even though their maximum retreat remains below 20.
Other extras meet magnitude or both criteria. Waiting for a pivot does not itself distinguish
ordinary circulation from attack abandonment under the supplied OR rule.

## E. Stress cases

| Case | v0.3 behavior and comparison |
| --- | --- |
| C05 | Exact onset 3612, pivot/confirmation 3617; maximum 47.9, peak age 5.774s. No exception required. |
| C09 | Miss becomes exact onset 576, pivot 579. Trusted backward recovery initializes reference; failed corner endpoint is excluded. No scored extra remains. |
| C10 | Miss becomes exact onset 2416, pivot 2423. Unsupported throw-in does not supply a peak; trusted backward action does. No scored extra remains. |
| C11 | Miss becomes exact onset 783, pivot 791. Failed corner remains excluded; later unknown onset is not inferred. No scored extra remains. |
| C13 | Former extra 309 cancels, but extras 316/376 confirm on elapsed time. Case extras increase from 1 to 2. |
| C14 | Former extras 2447/2461 cancel. New extra 2452 confirms on time: extras fall from 2 to 1. Warning 2503 is censored before entering unresolved review. |
| C16 | Primary failure fixed: warning 541 cancels at pivot 544, maximum 14.1 and peak age 3.305s, despite retreat still 13.8. Extra 624 also cancels, but new time-based extra 616 remains; case extras fall from 2 to 1. |
| C18 | Exact onset 1296 now confirms at pivot 1297: maximum 10.2, peak age 11.221s. Later extras remain at 1351/1389/1437/1462: four, unchanged in count. |
| C20 | Zero warnings and splits; failed-action/relocation safeguards remain intact. |
| C22 | Zero warnings/splits. Forward restoration 425 cannot initiate a warning; no fictitious cancellation is counted. |
| C24 | Zero warnings/splits; opening backward restart is endpoint context only. |
| C27 | No episode, warning or split. |
| C28 | No episode, warning or split. |

The re-arm guard prevents repeated splits while a rebuilt episode stays below the abandoned peak;
C09/C10's earlier repeated cuts disappear. Later re-entry can still generate false fragmentation,
as the extra-split table shows. This is not a claim that one cut per internal warning guarantees
one cut per human-reviewed attack.

## F. Final limitations

- The exact onsets of C11_R02, C12_R02 and C16_R01 remain unknown. Their windows and subsequent
  provisional membership are not new labels or negative examples.
- Partial C15/C17, deferred tails in C04/C09/C10 and C14's unresolved warning stay unscored.
  Nine cases have ambiguous portions; their valid portions retain their existing scoring.
- C12_R01 is the remaining missed encoded reset; C04_R01 is early. The eleven extra splits
  remain errors, not acceptable uncertainty masks. Human confirmation and pivot times differ.
- A warning ending before a trusted forward pivot cannot be confirmed by v0.3. Sparse trusted
  vectors can delay or censor a pivot; elapsed time does not establish continuously observed retreat.
- This bounded review does not establish season-wide stability or recall. Zero hard mismatches
  verifies preservation of the supplied hard ledger (27 scored boundaries plus two exclusions;
  partial C17 is unscored), not an independently validated hard-boundary detector.

## G. Final lock decision

**NOT READY — SEGMENTATION LOGIC REMAINS UNSTABLE**

v0.3 fixes C16's named warning and improves reset detectability, while preserving the hard boundaries
and C20/C24/C27/C28 safeguards. It does not sufficiently reduce false fragmentation: eleven extra
splits remain, C13 worsens, and C18 still has four later extras. Under the stated preference for
preserving coherent attacks, these are material failures rather than a small number of unusual
missed resets that could support a conservative lock. No v0.4, threshold variation, alternate rule,
new analysis phase or production change is proposed.

Validation is built into the same script: legacy transition checks, v0.3 pivot/threshold-edge,
cancellation-without-recovery, direction, trust, restart, censoring, hard-priority and re-arm checks;
unchanged historical case results; warning/pivot count reconciliation; source immutability.
The existing two CSVs now contain v0.1/v0.2/v0.3, with explicit pivot and maximum-retreat fields.
"""
    notice = "# Final replay status\n\n**NOT READY — SEGMENTATION LOGIC REMAINS UNSTABLE**\n\nThe v0.3 findings are appended below under **Candidate Rule v0.3 — final bounded replay**.\nThe following v0.1/v0.2 sections preserve the historical results and their then-current decisions.\n\n---\n\n"
    REPORT.write_text(notice + historical + text, encoding="utf-8")


def main():
    focused_checks()
    v3_checks()
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    events, parents, boundaries, candidates, episode_map = [
        pd.read_csv(p) for p in INPUTS
    ]
    assert set(parents.case_id) == {f"C{i:02d}" for i in range(1, 29)}
    assert not events.duplicated(["case_id", "event_index"]).any()
    for p in parents.itertuples():
        group = events[events.case_id.eq(p.case_id)]
        assert len(group) == p.total_event_count
        assert group.event_index.min() == p.first_event_index
        assert group.event_index.max() == p.last_event_index
    results = [
        evaluate(events, parents, boundaries, candidates, episode_map, version)
        for version in ("v0.1", "v0.2", "v0.3")
    ]
    cases = pd.concat([r[0] for r in results], ignore_index=True)
    details = pd.concat([r[1] for r in results], ignore_index=True)
    assert (
        cases.reviewed_scored_resets
        == cases[
            ["matched_resets", "early_splits", "late_splits", "missed_resets"]
        ].sum(axis=1)
    ).all()
    assert cases[cases.case_id.isin(["C27", "C28"])].predicted_episode_count.eq(0).all()
    for _, _, runs in results:
        for warnings, transitions, _ in runs.values():
            confirmed = [w for w in warnings if w["resolution"] == "CONFIRMED"]
            splits = [t["split"] for t in transitions if t["kind"] == "CONFIRMED_RESET"]
            assert splits == [w["onset"] for w in confirmed]
            assert len(splits) == len(set(splits))
    previous_path = DIAG / "phase3a3_reset_rule_replay_cases.csv"
    if previous_path.exists():
        previous = pd.read_csv(previous_path)
        keys = ["version", "case_id"]
        columns = [c for c in previous.columns if c in cases.columns]
        prior = (
            previous[previous.version.isin(["v0.1", "v0.2"])][columns]
            .sort_values(keys)
            .reset_index(drop=True)
        )
        serialized = pd.read_csv(StringIO(cases.to_csv(index=False)))
        current = (
            serialized[serialized.version.isin(["v0.1", "v0.2"])][columns]
            .sort_values(keys)
            .reset_index(drop=True)
        )
        # Match CSV missing-value representation before comparing historical rows.
        pd.testing.assert_frame_equal(
            prior.fillna(""), current.fillna(""), check_dtype=False
        )
    v3 = cases[cases.version.eq("v0.3")]
    assert (
        v3.warning_count == v3.forward_pivot_count + v3.terminated_before_pivot
    ).all()
    assert (
        v3.forward_pivot_count
        == v3.predicted_confirmation_count + v3.predicted_cancellation_count
    ).all()
    cases.to_csv(DIAG / "phase3a3_reset_rule_replay_cases.csv", index=False)
    details.to_csv(DIAG / "phase3a3_reset_rule_replay_details.csv", index=False)
    write_report(
        cases[~cases.version.eq("v0.3")], details[~details.version.eq("v0.3")], before
    )
    append_v3_report(cases, details)
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    print(
        cases.groupby("version")[
            [
                "reviewed_scored_resets",
                "matched_resets",
                "early_splits",
                "late_splits",
                "missed_resets",
                "extra_final_splits",
                "warning_count",
                "correctly_cancelled_warnings",
                "hard_boundary_mismatches",
            ]
        ]
        .sum()
        .to_string()
    )
    print(
        "Legacy/v0.3 transition checks, baseline comparison and integrity guards passed. Updated one report and two CSVs."
    )


if __name__ == "__main__":
    main()

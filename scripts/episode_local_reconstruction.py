"""Phase 3A-3B: bounded, reviewed episode reconstruction; no production segmenter."""

import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

if __package__:
    from .segmentation_calibration import (
        LABELS,
        ROOT,
        boolean,
        read_workbook,
    )
else:
    from segmentation_calibration import (
        LABELS,
        ROOT,
        boolean,
        read_workbook,
    )

INPUT = ROOT / "data/calibration"
PREFIX = "phase3a3_"
METRICS = (
    "running_peak_x",
    "retreat_from_peak",
    "largest_recent_negative_dx",
    "negative_run_length",
    "nonpositive_run_length",
    "time_since_peak",
    "events_since_peak",
    "observed_recovery",
    "time_to_recovery",
    "events_to_recovery",
    "new_peak_afterward",
)
SOURCE_FILES = (
    "phase3a3_reviewed_boundaries.csv",
    "phase3a3_reviewed_event_source.csv",
    "phase3a3_reviewed_candidate_source.csv",
    "phase3a3_reviewed_parent_source.csv",
    "Phase3A3_Segmentation_Calibration_Matrix.xlsx",
    "phase3a3_reconstruction_source_provenance.json",
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_sources(input_dir=INPUT):
    events = pd.read_csv(input_dir / SOURCE_FILES[1])
    candidates = pd.read_csv(input_dir / SOURCE_FILES[2])
    parents = pd.read_csv(input_dir / SOURCE_FILES[3])
    boundaries = pd.read_csv(input_dir / SOURCE_FILES[0])
    workbook = read_workbook(input_dir / SOURCE_FILES[4])
    for col in ("safe_action", "validated_anchor"):
        events[col] = events[col].map(boolean).astype("boolean")
    if events.duplicated(["case_id", "event_index"]).any():
        raise ValueError("Duplicate source event membership")
    if (
        candidates.candidate_id.duplicated().any()
        or boundaries.boundary_id.duplicated().any()
    ):
        raise ValueError("Duplicate candidate or boundary IDs")
    for parent in parents.itertuples():
        group = events[events.case_id.eq(parent.case_id)]
        if len(group) != parent.total_event_count:
            raise ValueError(f"Incomplete source timeline for {parent.case_id}")
        if (
            group.event_index.min() != parent.first_event_index
            or group.event_index.max() != parent.last_event_index
        ):
            raise ValueError(f"Parent limits disagree for {parent.case_id}")
        for col in ("match_id", "period", "possession_id"):
            if not group[col].eq(getattr(parent, col)).all():
                raise ValueError(f"Parent identity mismatch: {parent.case_id}/{col}")
    for boundary in boundaries.itertuples():
        indices = set(events.loc[events.case_id.eq(boundary.case_id), "event_index"])
        for col in (
            "onset_event",
            "confirmation_event",
            "resume_event",
            "onset_lower",
            "onset_upper",
        ):
            value = getattr(boundary, col)
            if pd.notna(value) and value not in indices:
                raise ValueError(
                    f"Boundary references missing event: {boundary.boundary_id}/{col}"
                )
    return events, candidates, parents, boundaries, workbook


def build_episode_map(parents, boundaries):
    """Compile authored review decisions, never discover cuts from numerical data.

    An unresolved onset leaves a membership gap from the last reviewed continuous
    sample to confirmation. A confirmation-start proxy is explicitly provisional.
    REVIEW_DEFERRED truncates known membership; it is not a football split.
    """
    rows = []
    for parent in parents.sort_values("case_id").itertuples():
        case = parent.case_id
        ledger = boundaries[boundaries.case_id.eq(case)].copy()
        excluded = ledger[ledger.boundary_type.str.endswith("EXCLUDE")]
        if len(excluded):
            b = excluded.iloc[0]
            rows.append(
                dict(
                    case_id=case,
                    match_id=parent.match_id,
                    period=parent.period,
                    provider_possession_id=parent.possession_id,
                    episode_id=None,
                    episode_start_event_index=np.nan,
                    episode_end_event_index=np.nan,
                    start_reason=b.boundary_type,
                    end_reason=b.boundary_type,
                    boundary_type=b.boundary_type,
                    excluded=True,
                    state_valid=False,
                    boundary_precision=b.precision,
                    lock_status="LOCKED",
                    confidence=3
                    if b.boundary_type == "ADMINISTRATIVE_EXCLUDE"
                    else np.nan,
                    review_source=b.source,
                    review_note=b.review_note,
                )
            )
            continue
        ledger["sort_event"] = ledger.onset_event.fillna(ledger.onset_lower)
        start = int(parent.first_event_index)
        start_reason, source, note = (
            "PARENT_START",
            "reviewed_parent_source;workbook_provenance",
            "Reviewed parent opening; no inferred earlier history.",
        )
        precision, start_valid, reset_onset, reset_confirm, start_boundary = (
            "observed_parent_limit",
            True,
            np.nan,
            np.nan,
            "",
        )
        number = 0
        partial = case in {"C15", "C17"}

        def emit(end, reason, boundary_id, end_precision):
            nonlocal number
            if start is None or end < start:
                return
            number += 1
            rows.append(
                dict(
                    case_id=case,
                    match_id=parent.match_id,
                    period=parent.period,
                    provider_possession_id=parent.possession_id,
                    episode_id=f"{case}_E{number:02d}",
                    episode_start_event_index=start,
                    episode_end_event_index=end,
                    start_reason=start_reason,
                    end_reason=reason,
                    boundary_type=start_reason,
                    start_boundary_id=start_boundary,
                    end_boundary_id=boundary_id,
                    reset_onset_event=reset_onset,
                    reset_confirmation_event=reset_confirm,
                    excluded=False,
                    state_valid=start_valid and not partial,
                    boundary_precision=precision,
                    end_boundary_precision=end_precision,
                    lock_status="PARTIAL_CASE_STRUCTURE"
                    if partial
                    else "ENCODED_REVIEW",
                    confidence=3 if not partial and start_boundary else np.nan,
                    review_source=source,
                    review_note=note,
                )
            )

        for b in ledger.sort_values(["sort_event", "boundary_id"]).itertuples():
            cut = int(b.sort_event)
            emit(cut - 1, b.boundary_type, b.boundary_id, b.precision)
            if b.boundary_type in {"TERMINAL", "REVIEW_DEFERRED"}:
                start = None
                continue
            start = int(b.resume_event)
            start_reason = (
                "CLEAR_RESET"
                if b.boundary_type == "CLEAR_RESET"
                else "HARD_BOUNDARY_REGAIN"
            )
            start_valid = b.precision != "unresolved_onset"
            source, note, precision, start_boundary = (
                b.source,
                b.review_note,
                b.precision,
                b.boundary_id,
            )
            reset_onset = b.onset_event if b.boundary_type == "CLEAR_RESET" else np.nan
            reset_confirm = (
                b.confirmation_event if b.boundary_type == "CLEAR_RESET" else np.nan
            )
        emit(
            int(parent.last_event_index),
            "PARENT_OBSERVATION_END",
            "",
            "observed_parent_limit",
        )
    result = pd.DataFrame(rows)
    result["attacking_episode_id"] = result.episode_id
    return result


def assign_membership(events, episode_map, boundaries):
    data = events.sort_values(["case_id", "event_index"]).copy().reset_index(drop=True)
    data["episode_id"] = pd.Series(pd.NA, index=data.index, dtype="object")
    data["episode_start_event_index"] = np.nan
    data["episode_end_event_index"] = np.nan
    data["episode_start_reason"] = ""
    data["episode_end_reason"] = ""
    data["episode_elapsed_seconds"] = np.nan
    data["episode_state_valid"] = False
    data["membership_status"] = "boundary_or_unresolved_context"
    for episode in episode_map.itertuples():
        case = data.case_id.eq(episode.case_id)
        if episode.excluded:
            data.loc[case, "membership_status"] = episode.start_reason
            continue
        mask = case & data.event_index.between(
            episode.episode_start_event_index, episode.episode_end_event_index
        )
        if data.loc[mask, "episode_id"].notna().any():
            raise ValueError("Overlapping reviewed episodes")
        data.loc[mask, "episode_id"] = episode.episode_id
        data.loc[mask, "episode_start_event_index"] = episode.episode_start_event_index
        data.loc[mask, "episode_end_event_index"] = episode.episode_end_event_index
        data.loc[mask, "episode_start_reason"] = episode.start_reason
        data.loc[mask, "episode_end_reason"] = episode.end_reason
        data.loc[mask, "episode_state_valid"] = episode.state_valid
        data.loc[mask, "membership_status"] = (
            "reviewed_episode_context"
            if episode.state_valid
            else "provisional_episode_context"
        )
        start_time = data.loc[
            case & data.event_index.eq(episode.episode_start_event_index),
            "period_seconds",
        ].item()
        data.loc[mask, "episode_elapsed_seconds"] = (
            data.loc[mask, "period_seconds"] - start_time
        )
    data["reviewed_boundary_id"] = ""
    for b in boundaries.itertuples():
        lo = b.onset_event if pd.notna(b.onset_event) else b.onset_lower
        hi = b.confirmation_event
        mask = data.case_id.eq(b.case_id) & data.event_index.between(lo, hi)
        data.loc[mask, "reviewed_boundary_id"] = b.boundary_id
    data["is_leverkusen_attacking_action"] = (
        data.episode_id.notna()
        & data.event_team_id.eq(904)
        & data.event_type.isin(["Pass", "Carry"])
    )
    data["hard_boundary_state_reset"] = data.event_index.eq(
        data.episode_start_event_index
    ) & data.episode_id.isin(
        episode_map.loc[
            episode_map.start_reason.eq("HARD_BOUNDARY_REGAIN"), "episode_id"
        ]
    )
    data["attacking_episode_id"] = data.episode_id
    return data


def progression(group):
    """State on trusted Pass/Carry vectors only; inter-action relocation is separate.

    Source action starts/ends share action-start timestamps (no endpoint timing).
    Missing vectors never create boundaries and never supply filled coordinates.
    Failed endpoints cannot establish a controlled peak or a recovery.
    """
    records, vertices = [], []
    peak, peak_time, peak_pos, previous_end = np.nan, np.nan, np.nan, np.nan
    negatives, nonpositive, recent = 0, 0, []
    relocation_pending, drawdown_relocation = False, False
    group = group.sort_values("event_index")
    for pos, row in enumerate(group.itertuples()):
        context = str(row.provider_context)
        safe = (
            bool(row.safe_action)
            and row.event_team_id == 904
            and row.event_type in {"Pass", "Carry"}
        )
        failed = row.event_type == "Pass" and "pass.outcome:" in context
        restart = pd.notna(row.restart_context) and str(row.restart_context) != ""
        trusted = safe and not failed
        if (
            row.event_type
            in {"Clearance", "Miscontrol", "Dispossessed", "Ball Recovery"}
            or failed
            or "ball_receipt.outcome:Incomplete" in context
        ):
            relocation_pending = True
        record = {f"episode_{metric}": np.nan for metric in METRICS}
        record.update(
            case_id=row.case_id,
            event_index=row.event_index,
            episode_recovery_status="unavailable_current_measurement",
            episode_recovery_censor_event=np.nan,
            episode_followup_seconds=np.nan,
            episode_trusted_progression_action=trusted and not restart,
            episode_opening_restart=restart,
            episode_recorded_delta_x=row.delta_x if safe else np.nan,
            episode_inter_action_dx=np.nan,
            episode_relocation_not_backward_progression=False,
            episode_drawdown_relocation_affected=drawdown_relocation,
            episode_action_exclusion_reason="",
            episode_peak_before_action=peak,
            episode_safe_observation_scope="validated_action_subsequence",
        )
        if not safe:
            record["episode_action_exclusion_reason"] = (
                "not_a_trusted_leverkusen_vector"
            )
            records.append(record)
            continue
        if failed:
            # The recorded failed endpoint is preserved above, never used as a
            # controlled ball observation. Prior state survives, without filling
            # current spatial diagnostics or treating failure as backward travel.
            negatives, nonpositive = 0, 0
            record["episode_action_exclusion_reason"] = (
                "failed_or_unknown_pass_endpoint"
            )
            records.append(record)
            continue
        if pd.notna(previous_end):
            jump = row.start_x - previous_end
            record["episode_inter_action_dx"] = jump
            if jump < -1e-9 and relocation_pending:
                drawdown_relocation = True
                record["episode_relocation_not_backward_progression"] = True
        relocation_pending = False
        # Opening restart establishes initial context, not abandonment of a prior
        # attack. Use its trusted endpoint to seed state; omit its backward vector.
        points = [row.end_x] if restart else [row.start_x, row.end_x]
        for x in points:
            if pd.isna(peak) or x >= peak:
                peak, peak_time, peak_pos = x, row.period_seconds, pos
                drawdown_relocation = False
            vertices.append((pos, row.event_index, row.period_seconds, x))
        if restart:
            negatives, nonpositive, recent = 0, 0, []
            record["episode_action_exclusion_reason"] = (
                "opening_restart_context_not_reset_evidence"
            )
        else:
            dx = row.end_x - row.start_x
            recent = (recent + [min(dx, 0)])[-3:]
            negatives = negatives + 1 if dx < 0 else 0
            nonpositive = nonpositive + 1 if dx <= 0 else 0
        record.update(
            episode_running_peak_x=peak,
            episode_retreat_from_peak=max(0, peak - row.end_x),
            episode_largest_recent_negative_dx=min(recent, default=0),
            episode_negative_run_length=negatives,
            episode_nonpositive_run_length=nonpositive,
            episode_time_since_peak=row.period_seconds - peak_time,
            episode_events_since_peak=pos - peak_pos,
            episode_drawdown_relocation_affected=drawdown_relocation,
            _position=pos,
            _seconds=row.period_seconds,
        )
        previous_end = row.end_x
        records.append(record)
    last = group.iloc[-1]
    for record in records:
        peak = record["episode_running_peak_x"]
        if pd.isna(peak):
            continue
        later = [v for v in vertices if v[0] > record["_position"]]
        record["episode_new_peak_afterward"] = (
            any(v[3] > peak for v in later) if later else np.nan
        )
        if record["episode_retreat_from_peak"] == 0:
            record["episode_recovery_status"] = "not_applicable_at_peak"
            continue
        recovered = next((v for v in later if v[3] >= peak), None)
        record["episode_observed_recovery"] = recovered is not None
        if recovered:
            record["episode_recovery_status"] = "observed_equal_or_higher_peak"
            record["episode_time_to_recovery"] = recovered[2] - record["_seconds"]
            record["episode_events_to_recovery"] = recovered[0] - record["_position"]
        else:
            record["episode_recovery_status"] = "censored_at_episode_observation_end"
            record["episode_recovery_censor_event"] = last.event_index
            record["episode_followup_seconds"] = (
                last.period_seconds - record["_seconds"]
            )
    return pd.DataFrame(records).drop(
        columns=["_position", "_seconds"], errors="ignore"
    )


def reconstruct(events, candidates, parents, boundaries, workbook):
    episode_map = build_episode_map(parents, boundaries)
    membership = assign_membership(events, episode_map, boundaries)
    measurements = pd.concat(
        [
            progression(group)
            for _, group in membership.dropna(subset=["episode_id"]).groupby(
                "episode_id", sort=True
            )
        ],
        ignore_index=True,
    )
    membership = membership.merge(
        measurements, on=["case_id", "event_index"], how="left", validate="one_to_one"
    )
    matrix = workbook["Calibration_Matrix"].set_index("candidate_id")
    hard = (
        workbook["Hard_Boundaries"]
        .dropna(subset=["candidate_id"])
        .set_index("candidate_id")
    )
    out = candidates.rename(
        columns={
            c: "provider_" + c
            for c in (
                "retreat_from_peak",
                "largest_recent_negative_dx",
                "negative_run_length",
                "nonpositive_run_length",
                "time_since_peak",
                "events_since_peak",
                "observed_recovery",
                "time_to_recovery",
                "events_to_recovery",
                "new_peak_afterward",
                "prior_peak_x",
            )
        }
    )
    out = out.merge(
        membership[
            ["case_id", "event_index", "episode_id", "membership_status"]
            + [c for c in membership if c.startswith("episode_") and c != "episode_id"]
        ],
        left_on=["case_id", "candidate_event_index"],
        right_on=["case_id", "event_index"],
        validate="one_to_one",
    )
    out["human_label"], out["lock_status"], out["review_note"] = None, "UNRECORDED", ""
    out["workbook_threshold_safe"] = pd.Series(pd.NA, index=out.index, dtype="object")
    out["workbook_provider_peak_contaminated"] = pd.Series(
        pd.NA, index=out.index, dtype="object"
    )
    out["episode_local_retreat_override"] = np.nan
    out["human_review_confidence"] = np.nan
    out["workbook_review_row"] = np.nan
    out["candidate_role"], out["warning_resolution"], out["reset_excursion_id"] = (
        "normal_active_episode_sample",
        "",
        "",
    )
    for i, row in out.iterrows():
        cid = row.candidate_id
        if cid in matrix.index:
            human = matrix.loc[cid]
            out.at[i, "human_review_confidence"] = human.review_confidence
            out.at[i, "workbook_review_row"] = human.workbook_row
            out.loc[i, ["human_label", "lock_status", "review_note"]] = [
                human.human_label,
                human.lock_status,
                human.review_note,
            ]
            out.at[i, "workbook_threshold_safe"] = boolean(human.threshold_safe)
            out.at[i, "workbook_provider_peak_contaminated"] = boolean(
                human.provider_peak_contaminated
            )
            out.at[i, "episode_local_retreat_override"] = (
                human.episode_local_retreat_override
            )
            if human.human_label == "POSSIBLE_RESET":
                out.loc[i, ["candidate_role", "warning_resolution"]] = [
                    "reset_warning",
                    "not_confirmed_in_available_review",
                ]
        elif cid in hard.index:
            out.at[i, "human_review_confidence"] = hard.loc[cid].review_confidence
            out.at[i, "workbook_review_row"] = hard.loc[cid].workbook_row
            out.loc[
                i, ["human_label", "lock_status", "review_note", "candidate_role"]
            ] = [
                "HARD_BOUNDARY",
                "LOCKED",
                hard.loc[cid].review_note,
                "hard_boundary_context",
            ]
        else:
            out.at[i, "candidate_role"] = "excluded_unrecorded_review"
        if pd.isna(row.episode_id):
            out.at[i, "candidate_role"] = (
                "hard_boundary_context"
                if cid in hard.index
                else "excluded_unresolved_membership"
            )
        for b in boundaries[
            boundaries.case_id.eq(row.case_id)
            & boundaries.boundary_type.eq("CLEAR_RESET")
        ].itertuples():
            onset = b.onset_event if pd.notna(b.onset_event) else b.confirmation_event
            if onset <= row.candidate_event_index <= b.last_reset_sample:
                role = "later_reset_phase_sample"
                if row.candidate_event_index == b.confirmation_event:
                    role = "reset_confirmation"
                if row.candidate_event_index == b.onset_event:
                    role = (
                        "reset_onset_and_confirmation"
                        if b.onset_event == b.confirmation_event
                        else "reset_onset"
                    )
                out.loc[
                    i, ["candidate_role", "reset_excursion_id", "warning_resolution"]
                ] = [role, b.boundary_id, "confirmed_excursion"]
        if cid in {"C16_M05", "C16_M06", "C22_M05", "C25_M06", "C25_M07"}:
            out.loc[i, ["candidate_role", "warning_resolution"]] = [
                "reset_warning",
                "cancelled_or_retained_continue",
            ]
    reasons = []
    for row in out.itertuples():
        why = []
        if row.human_label not in LABELS or row.lock_status not in {
            "LOCKED",
            "PARTIAL_LOCK",
        }:
            why.append("no_locked_reset_review_label")
        if pd.isna(row.episode_id):
            why.append("no_reviewed_episode_membership")
        elif not row.episode_state_valid:
            why.append("unresolved_episode_start_or_partial_case_structure")
        if pd.isna(row.episode_retreat_from_peak):
            why.append("no_trusted_current_progression_measurement")
        if pd.notna(row.episode_opening_restart) and row.episode_opening_restart:
            why.append("opening_restart_not_reset_evidence")
        if (
            pd.notna(row.episode_drawdown_relocation_affected)
            and row.episode_drawdown_relocation_affected
        ):
            why.append("drawdown_includes_contest_relocation")
        reasons.append(";".join(why))
    out["calibration_exclusion_reason"] = reasons
    out["episode_calibration_ready"] = out.calibration_exclusion_reason.eq("")
    out["calibration_scope"] = (
        "candidate_state_descriptions_stratify_by_role_not_onset_threshold_training"
    )
    out["attacking_episode_id"] = out.episode_id

    excursions = []
    for b in boundaries[boundaries.boundary_type.eq("CLEAR_RESET")].itertuples():
        case = membership[membership.case_id.eq(b.case_id)]
        confirmation = out[
            out.case_id.eq(b.case_id)
            & out.candidate_event_index.eq(b.confirmation_event)
        ]
        row = dict(
            reset_excursion_id=b.boundary_id,
            case_id=b.case_id,
            onset_event=b.onset_event,
            onset_lower=b.onset_lower,
            onset_upper=b.onset_upper,
            confirmation_event=b.confirmation_event,
            last_reset_sample=b.last_reset_sample,
            onset_precision=b.precision,
            reviewed_split_count=1,
            onset_status="unresolved"
            if pd.isna(b.onset_event)
            else "encoded_at_review_candidate_resolution",
            onset_candidate_id=";".join(
                out.loc[
                    out.case_id.eq(b.case_id)
                    & out.candidate_event_index.eq(b.onset_event),
                    "candidate_id",
                ]
            ),
            confirmation_candidate_id=";".join(confirmation.candidate_id),
            review_source=b.source,
            review_note=b.review_note,
        )
        for metric in METRICS:
            row["confirmation_episode_" + metric] = (
                confirmation["episode_" + metric].iloc[0]
                if len(confirmation)
                else np.nan
            )
            row["onset_pre_split_" + metric] = np.nan
            row["confirmation_unsplit_reference_" + metric] = np.nan
        # A separate, explicitly counterfactual bridge checks the recorded local
        # override at confirmation. It assumes the pre-window episode continued
        # until confirmation and never enters final membership or the cohort.
        before_window = case[
            case.event_index.lt(b.onset_lower) & case.episode_id.notna()
        ]
        if len(before_window):
            reference_id = before_window.episode_id.iloc[-1]
            reference_start = case.loc[
                case.episode_id.eq(reference_id), "event_index"
            ].min()
            bridge_group = case[
                case.event_index.between(reference_start, b.confirmation_event)
            ]
            bridge = progression(bridge_group).iloc[-1]
            for metric in METRICS:
                row["confirmation_unsplit_reference_" + metric] = bridge[
                    "episode_" + metric
                ]
            row["confirmation_unsplit_reference_status"] = (
                "counterfactual_no_reset_until_confirmation_not_calibration_ready"
            )
        if pd.notna(b.onset_event):
            preceding = case[
                case.event_index.lt(b.onset_event) & case.episode_id.notna()
            ]
            if len(preceding):
                previous_id = preceding.episode_id.iloc[-1]
                onset = case[case.event_index.eq(b.onset_event)]
                prior = case[case.episode_id.eq(previous_id)]
                bridge = progression(pd.concat([prior, onset], ignore_index=True)).iloc[
                    -1
                ]
                available = (
                    pd.notna(bridge.episode_peak_before_action)
                    and prior.episode_state_valid.all()
                )
                row["onset_pre_split_available"] = available
                if available:
                    for metric in METRICS:
                        row["onset_pre_split_" + metric] = bridge["episode_" + metric]
                row["onset_pre_split_recovery_status"] = (
                    "censored_at_final_reset_split"
                    if available
                    else "unavailable_prior_observed_peak"
                )
                row["onset_reference_episode_id"] = previous_id
                row["onset_prior_established_peak_x"] = (
                    bridge.episode_peak_before_action
                )
                row["onset_time_to_confirmation"] = (
                    case.loc[
                        case.event_index.eq(b.confirmation_event), "period_seconds"
                    ].item()
                    - onset.period_seconds.item()
                )
        excursions.append(row)
    excursions = pd.DataFrame(excursions)
    # Onset snapshots are transition evidence, never recovery measured across the
    # final split. Confirmation metrics are from the new episode and named so.
    excursions["onset_recovery_scope"] = (
        "censored_at_final_split_no_cross_boundary_return"
    )
    comparison_rows = []
    for row in out.itertuples():
        for metric in METRICS:
            source = (
                "provider_prior_peak_x"
                if metric == "running_peak_x"
                else "provider_" + metric
            )
            old, new = getattr(row, source), getattr(row, "episode_" + metric)
            if pd.isna(old) and pd.isna(new):
                changed, change_kind = False, "both_missing"
            elif pd.isna(old) or pd.isna(new):
                changed, change_kind = True, "availability_changed"
            else:
                changed = not np.isclose(float(old), float(new), rtol=0, atol=1e-9)
                change_kind = "value_changed" if changed else "unchanged"
            comparison_rows.append(
                dict(
                    candidate_id=row.candidate_id,
                    case_id=row.case_id,
                    human_label=row.human_label,
                    metric=metric,
                    provider_value=old,
                    episode_value=new,
                    changed=changed,
                    change_kind=change_kind,
                    episode_calibration_ready=row.episode_calibration_ready,
                )
            )
    comparison = pd.DataFrame(comparison_rows)
    summary = episode_map.copy()
    for i, row in summary.iterrows():
        group = (
            membership[membership.episode_id.eq(row.episode_id)]
            if pd.notna(row.episode_id)
            else membership.iloc[:0]
        )
        summary.loc[i, "context_events"] = len(group)
        summary.loc[i, "leverkusen_action_events"] = (
            group.is_leverkusen_attacking_action.sum()
        )
        summary.loc[i, "trusted_progression_actions"] = int(
            group.episode_trusted_progression_action.fillna(False).sum()
        )
        summary.loc[i, "maximum_episode_peak_x"] = group.episode_running_peak_x.max()
        summary.loc[i, "maximum_episode_retreat"] = (
            group.episode_retreat_from_peak.max()
        )
    ready = out[out.episode_calibration_ready]
    recovery_summary = []
    for label in LABELS:
        group = ready[ready.human_label.eq(label)]
        values = group.episode_time_to_recovery.dropna()
        recovery_summary.append(
            dict(
                human_label=label,
                candidate_count=len(group),
                observed_time_count=len(values),
                missing_time_count=int(group.episode_time_to_recovery.isna().sum()),
                conditional_mean_recovery_seconds=values.mean(),
                conditional_median_recovery_seconds=values.median(),
                censored_count=int(
                    group.episode_recovery_status.eq(
                        "censored_at_episode_observation_end"
                    ).sum()
                ),
                at_peak_count=int(
                    group.episode_recovery_status.eq("not_applicable_at_peak").sum()
                ),
            )
        )
    return {
        "reviewed_episode_map": episode_map,
        "episode_event_membership": membership,
        "episode_local_candidate_diagnostics": out,
        "reviewed_episode_summary": summary,
        "provider_vs_episode_diagnostics": comparison,
        "reset_excursion_diagnostics": excursions,
        "episode_local_recovery_summary": pd.DataFrame(recovery_summary),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=INPUT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs/diagnostics")
    args = parser.parse_args()
    hashes = {name: digest(args.input_dir / name) for name in SOURCE_FILES}
    tables = reconstruct(*read_sources(args.input_dir))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(args.output_dir / f"{PREFIX}{name}.csv", index=False)
    membership = tables["episode_event_membership"]
    candidates = tables["episode_local_candidate_diagnostics"]
    episodes = tables["reviewed_episode_map"]
    comparison = tables["provider_vs_episode_diagnostics"]
    metrics = {
        "reviewed_parents": int(episodes.case_id.nunique()),
        "reconstructed_episode_intervals": int(episodes.episode_id.notna().sum()),
        "valid_start_episode_intervals": int(episodes.state_valid.sum()),
        "no_episode_exclusions": int(episodes.excluded.sum()),
        "reset_excursions": len(tables["reset_excursion_diagnostics"]),
        "unresolved_reset_onsets": int(
            tables["reset_excursion_diagnostics"].onset_event.isna().sum()
        ),
        "event_count": len(membership),
        "candidate_count": len(candidates),
        "candidates_with_changed_available_values": int(
            comparison.loc[
                comparison.changed & comparison.change_kind.eq("value_changed"),
                "candidate_id",
            ].nunique()
        ),
        "candidates_with_any_value_or_availability_change": int(
            comparison.loc[comparison.changed, "candidate_id"].nunique()
        ),
        "calibration_ready_by_label": candidates[candidates.episode_calibration_ready]
        .human_label.value_counts()
        .to_dict(),
    }
    manifest = {
        "status": "REVIEWED CALIBRATION RECONSTRUCTION / NO PRODUCTION METHOD LOCK",
        "counts": metrics,
        "source_sha256": hashes,
        "script_sha256": digest(__file__),
        "workbook_reader_sha256": digest(ROOT / "scripts/segmentation_calibration.py"),
        "runtime": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "artifacts": {
            f"{PREFIX}{name}.csv": digest(args.output_dir / f"{PREFIX}{name}.csv")
            for name in tables
        },
    }
    (args.output_dir / "phase3a3_episode_local_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    if hashes != {name: digest(args.input_dir / name) for name in SOURCE_FILES}:
        raise RuntimeError("Source inputs changed during reconstruction")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

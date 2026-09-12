"""Bounded offline role-aware calibration: two questions, no fitted rules.

Reads only the reconstruction report and its three named diagnostic CSV inputs.
Writes one report, four figures and three compact CSVs. No reconstruction imports.
"""

import hashlib
from pathlib import Path
import platform
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "outputs/diagnostics"
FIG = ROOT / "outputs/figures"
REPORT = ROOT / "report/phase3a3_role_aware_reset_analysis.md"
INPUTS = [ROOT / "report/phase3a3_episode_local_reconstruction.md"] + [
    DIAG / f"phase3a3_{name}.csv"
    for name in (
        "episode_local_candidate_diagnostics",
        "reset_excursion_diagnostics",
        "episode_local_recovery_summary",
    )
]
FEATURES = {
    "retreat": "retreat_from_peak",
    "peak_time": "time_since_peak",
    "nonpositive_run": "nonpositive_run_length",
    "backward_magnitude": "largest_recent_negative_dx",
    "peak_events": "events_since_peak",
    "negative_run": "negative_run_length",
}
ROLES = [
    "ordinary_continuation",
    "cancelled_warning",
    "unresolved_warning",
    "confirmed_reset_onset",
]
NAMES = {
    "ordinary_continuation": "Ordinary continuation",
    "cancelled_warning": "Cancelled warning",
    "unresolved_warning": "Unresolved warning",
    "confirmed_reset_onset": "Confirmed reset onset",
}
COLORS = {
    "ordinary_continuation": "#0072B2",
    "cancelled_warning": "#D55E00",
    "unresolved_warning": "#777777",
    "confirmed_reset_onset": "#7B3294",
}
MARKERS = {
    "ordinary_continuation": "o",
    "cancelled_warning": "^",
    "unresolved_warning": "D",
    "confirmed_reset_onset": "s",
}


def truth(series):
    """Nullable CSV Boolean parsing; the text False must not become truthy."""
    values = series.astype("string").str.lower()
    if not values.dropna().isin(["true", "false"]).all():
        raise ValueError("Unexpected Boolean token")
    return values.eq("true").fillna(False)


def md(frame):
    def cell(value):
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.3f}".rstrip("0").rstrip(".")
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(frame.columns) + " |",
        "| " + " | ".join(["---"] * len(frame.columns)) + " |",
    ]
    return "\n".join(
        lines
        + [
            "| " + " | ".join(map(cell, row)) + " |"
            for row in frame.itertuples(index=False, name=None)
        ]
    )


def cohorts(candidates, resets):
    c = candidates.copy()
    c["source_ready"] = truth(c.episode_calibration_ready)
    c["analysis_role"] = c.candidate_role.replace(
        {
            "normal_active_episode_sample": "ordinary_continuation",
            "reset_onset": "confirmed_reset_onset",
            "reset_onset_and_confirmation": "confirmed_reset_onset",
        }
    )
    warning = c.candidate_role.eq("reset_warning")
    c.loc[
        warning & c.warning_resolution.eq("cancelled_or_retained_continue"),
        "analysis_role",
    ] = "cancelled_warning"
    c.loc[
        warning & c.warning_resolution.eq("not_confirmed_in_available_review"),
        "analysis_role",
    ] = "unresolved_warning"
    assert not c.analysis_role.eq("reset_warning").any(), (
        "Unrecognized warning resolution"
    )
    for feature, source in FEATURES.items():
        c[feature] = (
            c["episode_" + source].abs()
            if feature == "backward_magnitude"
            else c["episode_" + source]
        )
    c["measurement_reference"] = "current_episode"
    c["q1_included"] = c.source_ready & c.analysis_role.isin(ROLES[:3])
    assert (
        c.loc[
            c.q1_included & c.analysis_role.eq("ordinary_continuation"), "human_label"
        ]
        .eq("CONTINUE")
        .all()
    )
    r = resets.copy()
    r["quantitative_onset"] = (
        r.onset_event.notna()
        & truth(r.onset_pre_split_available)
        & r.onset_status.eq("encoded_at_review_candidate_resolution")
    )
    for feature, source in FEATURES.items():
        r[feature] = (
            r["onset_pre_split_" + source].abs()
            if feature == "backward_magnitude"
            else r["onset_pre_split_" + source]
        )
    r["quantitative_onset"] &= r[list(FEATURES)[:4]].notna().all(axis=1)
    assert not r.reset_excursion_id.duplicated().any()
    for reset in r.itertuples():
        if pd.isna(reset.onset_candidate_id):
            continue
        mask = c.candidate_id.eq(reset.onset_candidate_id)
        assert mask.sum() == 1
        assert c.loc[mask, "analysis_role"].item() == "confirmed_reset_onset"
        c.loc[mask, "measurement_reference"] = (
            "pre_split_onset"
            if reset.quantitative_onset
            else "unavailable_pre_split_onset"
        )
        c.loc[mask, "q1_included"] = reset.quantitative_onset
        for feature in FEATURES:
            c.loc[mask, feature] = (
                getattr(reset, feature) if reset.quantitative_onset else np.nan
            )
    assert (
        c.loc[c.q1_included & c.analysis_role.eq("confirmed_reset_onset")].shape[0]
        == r.quantitative_onset.sum()
    )
    assert not c.loc[
        c.candidate_role.isin(["reset_confirmation", "later_reset_phase_sample"]),
        "q1_included",
    ].any()
    return c, r


def warning_groups(c, r):
    """One row per confirmed excursion or recorded case/episode warning group.

    Unconfirmed rows have no excursion IDs. Group only by recorded case, episode
    and resolution; retain every member ID and sample count, never infer new cuts.
    """
    rows = []
    for reset in r[r.onset_event.lt(r.confirmation_event)].itertuples():
        first = c.loc[c.candidate_id.eq(reset.onset_candidate_id)].iloc[0]
        last = c.loc[c.candidate_id.eq(reset.confirmation_candidate_id)].iloc[0]
        rows.append(
            dict(
                warning_group_id=reset.reset_excursion_id,
                case_id=reset.case_id,
                resolution="confirmed",
                member_ids=";".join(
                    c.loc[
                        c.reset_excursion_id.eq(reset.reset_excursion_id),
                        "candidate_id",
                    ]
                ),
                representative_candidate_id=first.candidate_id,
                representative_event=first.candidate_event_index,
                warning_sample_count=int(
                    (
                        c.reset_excursion_id.eq(reset.reset_excursion_id)
                        & c.candidate_event_index.lt(reset.confirmation_event)
                    ).sum()
                ),
                q2_included=bool(
                    reset.quantitative_onset
                    and first.source_ready
                    and last.source_ready
                ),
                exclusion_reason=""
                if reset.quantitative_onset and first.source_ready and last.source_ready
                else "unavailable_onset_or_confirmation",
                time_to_confirmation=reset.onset_time_to_confirmation,
                onset_nonpositive_run=first.episode_nonpositive_run_length,
                later_nonpositive_run=last.episode_nonpositive_run_length,
                later_sample_definition="first_confirmation_in_new_episode",
                pre_split_recovery_status=reset.onset_pre_split_recovery_status,
                recovery_reference="new_episode_peak_at_onset_not_pre_split_peak",
                recovery_time=first.episode_time_to_recovery,
                recovery_events=first.episode_events_to_recovery,
                recovery_status=first.episode_recovery_status,
                followup_seconds=first.episode_followup_seconds,
                censor_reason=first.episode_end_reason,
                reference_peak=first.episode_running_peak_x,
                pre_split_reference_peak=reset.onset_pre_split_running_peak_x,
            )
        )
    warnings = c[c.analysis_role.isin(["cancelled_warning", "unresolved_warning"])]
    for (case, episode, role), group in warnings.groupby(
        ["case_id", "episode_id", "analysis_role"], dropna=False, sort=True
    ):
        group = group.sort_values("candidate_event_index")
        first = group.iloc[0]  # fixed earliest recorded warning, not fastest return
        rows.append(
            dict(
                warning_group_id=f"{case}_{episode}_{role}",
                case_id=case,
                resolution="cancelled" if role == "cancelled_warning" else "unresolved",
                member_ids=";".join(group.candidate_id),
                representative_candidate_id=first.candidate_id,
                representative_event=first.candidate_event_index,
                warning_sample_count=len(group),
                q2_included=bool(first.source_ready),
                exclusion_reason=first.calibration_exclusion_reason,
                time_to_confirmation=np.nan,
                onset_nonpositive_run=first.episode_nonpositive_run_length,
                later_nonpositive_run=group.iloc[-1].episode_nonpositive_run_length,
                later_sample_definition="last_recorded_warning_not_cancellation_event",
                pre_split_recovery_status="not_a_confirmed_split",
                recovery_reference="current_episode_peak_at_first_recorded_warning",
                recovery_time=first.episode_time_to_recovery,
                recovery_events=first.episode_events_to_recovery,
                recovery_status=first.episode_recovery_status,
                followup_seconds=first.episode_followup_seconds,
                censor_reason=first.episode_end_reason,
                reference_peak=first.episode_running_peak_x,
                pre_split_reference_peak=np.nan,
            )
        )
    result = pd.DataFrame(rows)
    assert not result.warning_group_id.duplicated().any()
    censored = result.recovery_status.str.startswith("censored", na=False)
    assert result.loc[censored, ["recovery_time", "recovery_events"]].isna().all().all()
    return result


def summaries(c):
    q1 = c[c.q1_included]
    rows = []
    for role in ROLES:
        for feature in list(FEATURES)[:4]:
            group = q1[q1.analysis_role.eq(role)]
            x = group[feature].dropna()
            rows.append(
                dict(
                    role=role,
                    feature=feature,
                    n=len(x),
                    missing=len(group) - len(x),
                    mean=x.mean(),
                    median=x.median(),
                    IQR=f"{x.quantile(0.25):.3f}–{x.quantile(0.75):.3f}",
                    range=f"{x.min():.3f}–{x.max():.3f}",
                )
            )
    probes = []
    for feature, values in {
        "retreat": [10, 20, 30],
        "peak_time": [3, 5, 10],
        "nonpositive_run": [2, 3],
    }.items():
        for value in values:
            row = {"illustrative probe": f"{feature} >= {value}"}
            for role in ROLES:
                g = q1[q1.analysis_role.eq(role)][feature].dropna()
                row[NAMES[role]] = f"{int(g.ge(value).sum())}/{len(g)}"
            probes.append(row)
    return pd.DataFrame(rows), pd.DataFrame(probes)


def figures(c, r, w):
    FIG.mkdir(parents=True, exist_ok=True)
    q1 = c[c.q1_included]
    paths = []

    def save(fig, name):
        path = FIG / f"phase3a3_role_aware_{name}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)

    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    for role in ROLES:
        g = q1[q1.analysis_role.eq(role)]
        ax.scatter(
            g.retreat,
            g.peak_time,
            label=f"{NAMES[role]} (n={len(g)})",
            c=COLORS[role],
            marker=MARKERS[role],
            s=45,
            alpha=0.8,
        )
        if role == "confirmed_reset_onset":
            for row in g.itertuples():
                ax.annotate(
                    row.candidate_id,
                    (row.retreat, row.peak_time),
                    xytext=(5, 6),
                    textcoords="offset points",
                    fontsize=8,
                )
    ax.set(
        xlabel="Retreat (StatsBomb x units)",
        ylabel="Time since relevant peak (seconds)",
        title="Onset versus continuation: individual reviewed observations",
    )
    ax.text(
        0.01,
        -0.15,
        "Confirmed onsets use pre-split measurements; other roles use current-episode measurements.",
        transform=ax.transAxes,
        fontsize=9,
    )
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8)
    save(fig, "onset_scatter")

    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    for i, role in enumerate(ROLES):
        g = q1[q1.analysis_role.eq(role)].sort_values("candidate_id")
        jitter = np.random.default_rng(40 + i).uniform(-0.12, 0.12, len(g))
        ax.scatter(
            g.retreat, i + jitter, c=COLORS[role], marker=MARKERS[role], s=36, alpha=0.8
        )
        ax.plot(
            [g.retreat.median()] * 2, [i - 0.23, i + 0.23], color="black", linewidth=2
        )
    ax.set_yticks(
        range(4),
        [f"{NAMES[role]} (n={int(q1.analysis_role.eq(role).sum())})" for role in ROLES],
    )
    ax.set(
        xlabel="Retreat (StatsBomb x units)",
        title="Raw retreat distributions; black tick = median",
        ylim=(-0.5, 3.5),
    )
    ax.grid(axis="x", alpha=0.2)
    save(fig, "retreat_distribution")

    primary = (
        w[w.q2_included].sort_values(["resolution", "case_id"]).reset_index(drop=True)
    )
    fig, (ax, status) = plt.subplots(
        1,
        2,
        figsize=(13, 6),
        gridspec_kw={"width_ratios": [1.1, 1.2]},
        layout="constrained",
    )
    for i, row in enumerate(primary.itertuples()):
        color = {
            "cancelled": "#D55E00",
            "confirmed": "#7B3294",
            "unresolved": "#777777",
        }[row.resolution]
        if pd.notna(row.recovery_time):
            ax.scatter(row.recovery_time, i, c=color, marker="o", s=40)
        if pd.notna(row.time_to_confirmation):
            ax.scatter(row.time_to_confirmation, i, c=color, marker="|", s=150)
        label = (
            "observed local return"
            if pd.notna(row.recovery_time)
            else "local return censored"
        )
        detail = (
            "; pre-split reference censored at split"
            if row.resolution == "confirmed"
            else ""
        )
        status.text(0, i, label + detail, va="center", fontsize=8, color=color)
    ax.set_yticks(
        range(len(primary)),
        [f"{x.case_id}: {x.resolution}" for x in primary.itertuples()],
    )
    ax.scatter([], [], c="black", marker="o", label="Observed local-peak return")
    ax.scatter([], [], c="black", marker="|", s=150, label="Warning → confirmation")
    ax.set(
        xlabel="Seconds from first recorded warning/onset sample",
        title="Observed durations only",
    )
    ax.set_ylim(-0.7, len(primary) + 1)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="x", alpha=0.2)
    status.set(
        xlim=(0, 1),
        ylim=ax.get_ylim(),
        title="Censoring shown as status, never duration",
    )
    status.axis("off")
    fig.suptitle(
        "Warning resolution: cancelled uses original episode peak; confirmed uses NEW episode peak",
        fontsize=11,
    )
    save(fig, "warning_resolution")

    usable = r[r.quantitative_onset]
    view = usable[
        [
            "reset_excursion_id",
            "onset_candidate_id",
            "retreat",
            "peak_time",
            "nonpositive_run",
            "backward_magnitude",
        ]
    ].copy()
    view.columns = [
        "Reset ID",
        "Onset ID",
        "Retreat\nx units",
        "Since peak\nseconds",
        "Nonpositive\nrun",
        "Largest backward\nx units",
    ]
    fig, ax = plt.subplots(figsize=(12, 4.5), layout="constrained")
    ax.axis("off")
    table = ax.table(
        cellText=view.round(3).astype(str).to_numpy(),
        colLabels=view.columns,
        loc="center",
        cellLoc="center",
        colWidths=[0.15, 0.15, 0.13, 0.18, 0.16, 0.20],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    for (row, _), cell in table.get_celld().items():
        cell.set_facecolor("#E8DDF0" if row == 0 else "#FAFAFA")
    ax.set_title(
        "Every quantitatively usable confirmed-reset onset: pre-split reference only",
        pad=15,
    )
    fig.text(
        0.5,
        0.02,
        "Seven observations; no confirmation substitutions. Three unknown onsets and two missing pre-split references excluded.",
        ha="center",
        fontsize=9,
    )
    save(fig, "onset_evidence")
    return paths


def report(c, r, w, stats, probes, hashes):
    q1 = c[c.q1_included]
    counts = (
        c.groupby("analysis_role", sort=True)
        .agg(
            source_rows=("candidate_id", "size"),
            source_ready=("source_ready", "sum"),
            Q1_used=("q1_included", "sum"),
        )
        .reset_index()
    )
    onset = r[r.quantitative_onset][
        [
            "reset_excursion_id",
            "onset_candidate_id",
            "retreat",
            "peak_time",
            "nonpositive_run",
            "backward_magnitude",
        ]
    ]
    primary = w[w.q2_included]
    warn = primary[
        [
            "case_id",
            "resolution",
            "representative_candidate_id",
            "warning_sample_count",
            "time_to_confirmation",
            "recovery_time",
            "recovery_status",
            "onset_nonpositive_run",
            "later_nonpositive_run",
        ]
    ]
    redundancy = []
    for role in ["ordinary_continuation", "confirmed_reset_onset"]:
        group = q1[q1.analysis_role.eq(role)]
        for a, b in [("peak_time", "peak_events"), ("nonpositive_run", "negative_run")]:
            pair = group[[a, b]].dropna()
            redundancy.append(
                dict(
                    role=role,
                    pair=f"{a} / {b}",
                    n=len(pair),
                    Spearman=pair.rank().corr().iloc[0, 1],
                )
            )
    pair = primary[["recovery_time", "recovery_events"]].dropna()
    redundancy.append(
        dict(
            role="recorded_warning_groups_local_return",
            pair="recovery_time / recovery_events",
            n=len(pair),
            Spearman=pair.rank().corr().iloc[0, 1],
        )
    )
    source_hashes = "\n".join(f"- `{p.name}`: `{value}`" for p, value in hashes.items())
    text = f"""# Phase 3A-3: role-aware reset analysis

**12 September 2026 — final descriptive pass; no fitted rule or production threshold.**
This analysis addresses two questions: what distinguishes onset from continuation,
and what distinguishes confirmation from cancellation once a warning exists.
**Yes: the evidence is sufficient to design one provisional deterministic rule
for replay against C01–C28.** It does not establish a final cutoff or a method lock.

## A. Cohorts used

Inputs are restricted to the reconstruction report and the three specified CSVs.
The existing role, resolution and validity fields are authoritative. No workbook,
raw events, boundary map or earlier methodology was reopened. No labels changed.
The 99 ready candidate states are not flattened into three human-label classes.

{md(counts)}

Q1 uses **69 ordinary continuation states, five cancelled-warning samples, one
unresolved warning and seven confirmed onsets: 82 observations**. The seven
positives come only from `onset_pre_split_*`, with an encoded event,
`onset_pre_split_available == True` and all four primary features available.
They replace the corresponding new-episode candidate measurements, not augment
them. Confirmation and later reset-phase samples contribute zero Q1 positives.
All four primary features are available in every included Q1 observation.

Nine onset locations are encoded; C09_R01 and C11_R01 lack a trusted pre-split
reference and are excluded from the quantitative onset comparison. C11_R02,
C12_R02 and C16_R01 retain unresolved onset windows. No confirmation-state or
counterfactual measurement substitutes for any of these five missing onsets.

The five cancelled-warning samples are C16_M05/M06, C22_M05 and C25_M06/M07.
C14_M09 is the one valid unresolved warning. C12_M02 has no trusted current
measurement; C15_M07 and C17_M04/M05 have partial episode structure. Those four
unresolved-warning samples remain in the audit table but outside quantitative cohorts.

Q2 has **six confirmed warning excursions, three cancelled warning groups and one
valid unresolved group**. Paired C16 and C25 samples each form one group using
recorded case/episode/resolution fields. The earliest recorded warning represents
each group; the fastest recovery is never selected. These grouping keys are not
new football boundaries. All member IDs survive in the CSV.
Three additional unresolved groups (C12, C15, C17) are retained as ineligible.
Three same-event onset/confirmation excursions have no observed warning interval;
their zero onset-to-confirmation values are not instantaneous warning-resolution evidence.

## B. Reset-onset evidence

Retreat is in StatsBomb x units; peak time is seconds; runs count trusted actions.
Largest backward magnitude is the absolute value of the signed source diagnostic.
The original signed fields are retained. Medians/IQRs and observed ranges follow;
quantiles use linear interpolation, with no smoothing or missing-value imputation.

{md(stats)}

Onsets show greater central retreat (median **20.1**, IQR **13.55–28.95**) than
ordinary continuation (**3.8**, IQR **0–11.4**). Cancelled warnings sit between them
(**12.5**, IQR **8.9–14.1**), but this is overlap, not a separable third class.
The ordinary/onset retreat range intersection is **10.2–40.8**; the
cancelled/onset intersection is **10.2–20.9**. Some ordinary states occur after
an earlier reset or regain, as recorded in their roles; they are not relabeled.

Time since the relevant peak has median **0** for ordinary states, **2.394** for
cancelled warnings and **6.116** for onsets. Yet C05/C07 begin at time zero:
requiring elapsed persistence before warning eligibility would miss those onsets.
Onset nonpositive runs are only **1–2 actions**; cancelled samples reach **4**.
Persistence can inform later confirmation without being a mandatory long-run onset test.

{md(onset)}

![Individual onset versus continuation observations](../outputs/figures/phase3a3_role_aware_onset_scatter.png)

![Raw retreat distributions](../outputs/figures/phase3a3_role_aware_retreat_distribution.png)

![Every usable onset](../outputs/figures/phase3a3_role_aware_onset_evidence.png)

The following fixed round-number probes are descriptive counts, not optimized
cutoffs. There is no accuracy ranking, parameter search or recommended number.

{md(probes)}

For example, retreat >=20 retains 4/7 onsets and also 9/69 ordinary states and
1/5 cancelled samples. Time >=5 retains 4/7 onsets but also misses three onsets.
A nonpositive-run requirement >=3 retains **none** of the usable onsets, while
including two cancelled samples. A large recent backward vector alone also fails:
onset magnitudes range 3.9–22.2, whereas ordinary samples reach 40.4.

Alternative counters are sensitivity checks, not independent reinforcement:

{md(pd.DataFrame(redundancy))}

These paired rank correlations are descriptive and case-dependent. Recovery pairs
use the local-reference durations shown below and do not validate a common old-peak
restoration measure. No model combines correlated variables as separate evidence.

## C. Warning confirmation versus cancellation

{md(warn)}

For confirmed excursions, `recovery_time` above is return to the **new episode's
peak at its onset sample**, while cancelled/unresolved groups use the original
current-episode peak at their first recorded warning. These durations are not
interchangeable measurements of restoration of the abandoned attack.
Pre-split recovery for all six confirmed warning excursions is structurally
censored at the retrospective split. That censoring is not evidence of failure
to restore the old peak before confirmation; the allowed artifacts do not measure
that future trajectory against a fixed pre-split reference.

Five of six confirmed groups have an observed **new-reference** return; C10 is
censored. Two of three cancelled groups have an observed current-peak return:
C22 at **3.853 s** and C25 at **6.691 s**, measured from its first warning sample.
C25_M07's 4.297 s is a later clock start for the same group's return, not another
independent cancellation. C16 is explicitly cancelled yet has no observed full
peak return: its follow-up is truncated after 1.305 s before an unresolved later
reset window. Renewed progression and complete peak restoration are different tests.

Confirmed warning-to-confirmation delays range **1.793–11.228 s**, median **4.1195 s**.
All six show new-episode nonpositive runs increasing from 1 at the onset sample
to 2–4 at first confirmation. These are observed action-subsequence counts, not
tracking or uninterrupted physical retreat. Cancellation samples can also reach
3 (C16) or 4 (C25); C22's recorded warning sample has run zero. The last warning
sample in a cancelled group is not asserted to be the exact cancellation event.

The seven ready later reset-phase samples labeled CLEAR_RESET and two later
warning-phase samples remain supporting context for established excursions.
They are not extra onsets, confirmations or independent warning-resolution trials.
One additional later-phase sample is ineligible because its episode start is unresolved.

![Warning timings with censoring separate](../outputs/figures/phase3a3_role_aware_warning_resolution.png)

In Figure 3, circles show observed local-reference returns and ticks show recorded
confirmation delays. No point is plotted for a missing/censored recovery time.
The unresolved C14 group is censored at parent observation end, with 19.178 s
of follow-up; it is neither a cancelled warning nor an inferred confirmed reset.

## D. Important counterexamples

- **C05_R01/C05_M02:** onset retreat 14.1, time zero, run 1; confirmation after
  2.799 s. Its new-episode peak returns after 5.774 s. An eventual quick return
  does not undo the reviewed reset; requiring long onset persistence misses it.
- **C18_R01/C18_M05:** onset retreat 10.2 with only 3.9 recent backward magnitude,
  but 9.980 s since peak. A large single backward-action requirement misses it.
- **C16_M05/M06:** cancellation without observed full peak return. Requiring a
  complete old-peak recovery to cancel would contradict the recorded resolution.
- **C25_M07:** cancelled-warning sample with four nonpositive actions. That run
  is longer than every usable onset run; length alone cannot confirm abandonment.
- **C04_R01:** the new-episode peak returns after 6.067 s, before confirmation
  at 11.228 s. Its new reference is 70.9 versus the pre-split 97.2. This defeats
  treating any local-peak return as restoration of the original attack.
- **C10_M07/C09_M03:** ordinary-role continuation with retreat 48.0/40.4 inside
  rebuilt episodes. A detector needs state/re-entry handling to avoid repeated cuts.
- **C14_M09:** unresolved warning with six nonpositive actions and retreat 21.1.
  An unresolved outcome cannot be converted to confirmation by a numerical rule here.

## E. Candidate state-machine ingredients

1. Retain the reviewed football/control and restart/relocation eligibility
   safeguards before numerical warning evidence; these are inherited constraints.
2. Permit a warning from meaningful retreat supported by the action context.
   Do not require a long negative run or elapsed delay at the onset itself.
3. Once warned, retain the warning's reference and accumulate persistence/
   reorganization evidence; use time or related event counters parsimoniously.
4. Allow restored forward progression to support cancellation without requiring
   complete peak recovery. A fast return is supporting context, not an unconditional veto.
5. Confirm only with reinforcing evidence, then associate one split with the
   recorded warning onset; suppress repeated cuts from later samples of that excursion.

These ingredients describe the next rule-design discussion. No numeric setting,
transition implementation or production policy is selected in this analysis.

## F. What remains unresolved

The three unknown onset windows, two unavailable pre-split references, partial
C15/C17 structure, and unmeasured exact cancellation times remain unresolved.
The seven positive onsets are selected, case-dependent review observations; paired
warnings and later samples are not independent. Censoring and changing peak
references prevent a clean common-reference confirmation-versus-cancellation
recovery distribution. The snapshot counters also cannot establish uninterrupted
progression between every event. None of these gaps is repaired by interpolation,
counterfactual substitution, outcome labels or numerical relabeling.

## G. Readiness decision

**Yes—design one provisional deterministic state-machine rule, then replay it
against C01–C28.** The evidence supports separating warning eligibility from
confirmation, preserving a reference while warned, and checking cancellation and
duplicate-cut behavior against the named counterexamples. Overlap is a reason
to assess a candidate rule in replay, not to add another descriptive research phase.
Keep unresolved intervals and partial reviews as explicit unscored/ambiguous
replay checks; they are not negative examples. The missing common-reference
recovery trajectory limits this report's conclusions but does not block a provisional
rule that can be inspected during replay. No material blocker prevents that next step.
After replay, revise once if materially necessary before considering a method lock.

Reproduction: `.venv\\Scripts\\python.exe scripts/role_aware_reset_analysis.py`.
The script writes only this report, four PNGs and three CSVs, using fixed plotting
jitter and deterministic grouping. The CSVs are `phase3a3_role_aware_cohort.csv`,
`phase3a3_role_aware_onset_comparison.csv` and
`phase3a3_role_aware_warning_resolution.csv` in `outputs/diagnostics/`.
Guard checks reconcile source readiness/recovery denominators, reject Boolean
ambiguity, enforce unique onset/group IDs, exclude later samples from Q1 and
preserve missing recovery times. No extra test suite or reconstruction changes.
Runtime: Python {platform.python_version()}, pandas {pd.__version__}, NumPy {np.__version__}, Matplotlib {matplotlib.__version__}.

Input SHA-256 values (provenance only):

{source_hashes}
"""
    # Keep prose compact without flattening Markdown tables, lists or figures.
    blocks = text.split("\n\n")
    text = "\n\n".join(
        block
        if block.lstrip().startswith(("#", "|", "!", "-", "1.", "2.", "3.", "4.", "5."))
        else textwrap.fill(
            " ".join(block.splitlines()),
            width=116,
            break_long_words=False,
            break_on_hyphens=False,
        )
        for block in blocks
    )
    REPORT.write_text(text + "\n", encoding="utf-8")


def main():
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    candidates, resets, old_summary = [pd.read_csv(path) for path in INPUTS[1:]]
    c, r = cohorts(candidates, resets)
    w = warning_groups(c, r)
    # Reconcile the allowed pre-existing summary as a source-integrity check only.
    for row in old_summary.itertuples():
        group = c[c.source_ready & c.human_label.eq(row.human_label)]
        assert len(group) == row.candidate_count
        times = group.episode_time_to_recovery.dropna()
        assert len(times) == row.observed_time_count
        assert np.isclose(times.mean(), row.conditional_mean_recovery_seconds)
    keep = [
        "candidate_id",
        "case_id",
        "episode_id",
        "human_label",
        "candidate_role",
        "analysis_role",
        "warning_resolution",
        "source_ready",
        "q1_included",
        "measurement_reference",
        "reset_excursion_id",
        "calibration_exclusion_reason",
        *FEATURES,
        "episode_largest_recent_negative_dx",
        "episode_time_to_recovery",
        "episode_events_to_recovery",
        "episode_recovery_status",
    ]
    c[keep].to_csv(DIAG / "phase3a3_role_aware_cohort.csv", index=False)
    reset_keep = [
        "reset_excursion_id",
        "case_id",
        "onset_candidate_id",
        "confirmation_candidate_id",
        "onset_event",
        "onset_lower",
        "onset_upper",
        "onset_precision",
        "quantitative_onset",
        *FEATURES,
        "onset_pre_split_largest_recent_negative_dx",
        "onset_pre_split_recovery_status",
        "onset_time_to_confirmation",
    ]
    r[reset_keep].to_csv(DIAG / "phase3a3_role_aware_onset_comparison.csv", index=False)
    w.to_csv(DIAG / "phase3a3_role_aware_warning_resolution.csv", index=False)
    figures(c, r, w)
    stats, probes = summaries(c)
    report(c, r, w, stats, probes, hashes)
    assert hashes == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
    print("Q1 roles:", c[c.q1_included].analysis_role.value_counts().to_dict())
    print("Q2 groups:", w[w.q2_included].resolution.value_counts().to_dict())
    print("Wrote one report, four figures, three CSVs. No production rule selected.")


if __name__ == "__main__":
    main()

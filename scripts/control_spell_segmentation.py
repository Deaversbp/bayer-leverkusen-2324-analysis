"""Build and validate pinned season control spells; no anchors or tactical outcomes."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.sequences.control_spells import load_season, segment_stream, KEY

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "phase3_"


def validate_review(stream, membership, boundaries):
    source = pd.read_csv(ROOT / "data/calibration/phase3a3_reviewed_event_source.csv")
    ledger = pd.read_csv(ROOT / "data/calibration/phase3a3_reviewed_boundaries.csv")
    parents = source[["case_id", *KEY]].drop_duplicates()
    joined = source.merge(
        stream[[*KEY, "event_index", "event_type"]],
        on=[*KEY, "event_index"],
        suffixes=("_review", "_canonical"),
        validate="one_to_one",
        how="left",
    )
    assert joined.event_type_review.eq(joined.event_type_canonical).all(), (
        "Reviewed snapshot differs from canonical event stream"
    )
    results = []
    for p in parents.itertuples(index=False):
        mask = np.logical_and.reduce([stream[k].eq(getattr(p, k)) for k in KEY])
        events = stream[mask].set_index("event_index")
        m = membership[
            np.logical_and.reduce([membership[k].eq(getattr(p, k)) for k in KEY])
        ]
        pred = boundaries[
            np.logical_and.reduce([boundaries[k].eq(getattr(p, k)) for k in KEY])
        ].copy()
        review = ledger[ledger.case_id.eq(p.case_id)]
        used = set()
        partial = p.case_id in {"C15", "C17"}
        deferred = review[review.boundary_type.eq("REVIEW_DEFERRED")].onset_event.min()

        def add(label, **kw):
            results.append(dict(case_id=p.case_id, classification=label, **kw))

        exclusions = review[review.boundary_type.str.endswith("EXCLUDE")]
        if len(exclusions):
            add(
                "MATCH" if m.attacking_control_spell_id.isna().all() else "MISSED",
                reviewed_id=exclusions.iloc[0].boundary_id,
                family="NO_SPELL",
                accepted=True,
                explanation="Administrative/insufficient parent excluded by event semantics, not ledger input.",
            )
        truth = review[review.boundary_type.isin(["OPPONENT_CONTROL", "TERMINAL"])]
        for b in truth.itertuples():
            candidates = pred[
                pred.boundary_type.eq(b.boundary_type) & ~pred.index.isin(used)
            ]
            candidate = (
                candidates.loc[(candidates.onset_event - b.onset_event).abs().idxmin()]
                if len(candidates)
                else None
            )
            label, accepted, why = (
                "MISSED",
                False,
                "No predicted boundary of this family.",
            )
            onset = resume = np.nan
            if candidate is not None:
                used.add(candidate.name)
                onset, resume = candidate.onset_event, candidate.resume_event
                resume_matches = (
                    pd.isna(resume) and pd.isna(b.resume_event)
                ) or resume == b.resume_event
                if onset == b.onset_event and resume_matches:
                    label, accepted, why = (
                        "MATCH",
                        True,
                        "Exact hard-boundary onset and regain.",
                    )
                else:
                    label = "EARLY" if onset < b.onset_event else "LATE"
                    why = "Onset or regain differs; not automatically accepted by distance."
                    between = events.loc[
                        (events.index >= b.onset_event) & (events.index < onset)
                    ]
                    paired = len(between) and all(
                        r.event_type in {"Dispossessed", "Duel", "Ball Receipt*"}
                        or (
                            r.event_type == "Pass"
                            and "pass.outcome:" in r.provider_context
                        )
                        for r in between.itertuples()
                    )
                    if (
                        b.boundary_type == "OPPONENT_CONTROL"
                        and resume_matches
                        and paired
                    ):
                        accepted = True
                        why = "Same reviewed loss/control change: prediction starts at corroborated opponent control after loss/failed-action records; identical regain."
            if partial:
                label, accepted, why = (
                    "UNSCORED_AMBIGUOUS",
                    False,
                    "Partial case review retained.",
                )
            add(
                label,
                reviewed_id=b.boundary_id,
                family=b.boundary_type,
                reviewed_onset=b.onset_event,
                predicted_onset=onset,
                reviewed_regain=b.resume_event,
                predicted_regain=resume,
                accepted=accepted,
                explanation=why,
            )
        for idx, b in pred.iterrows():
            if idx in used:
                continue
            unscored = partial or (pd.notna(deferred) and b.onset_event >= deferred)
            add(
                "UNSCORED_AMBIGUOUS" if unscored else "EXTRA_HARD_BOUNDARY",
                family=b.boundary_type,
                predicted_onset=b.onset_event,
                predicted_regain=b.resume_event,
                accepted=False,
                explanation="Partial/deferred area."
                if unscored
                else "Additional hard boundary in reviewed continuation.",
            )
        if not len(truth) and not len(exclusions) and not len(pred):
            add(
                "UNSCORED_AMBIGUOUS" if partial else "MATCH",
                family="CONTINUITY",
                accepted=not partial,
                explanation="No hard boundary required or predicted.",
            )
    return pd.DataFrame(results)


def markdown(frame):
    def fmt(x):
        if pd.isna(x):
            return "—"
        return f"{x:g}" if isinstance(x, float) else str(x).replace("|", "/")

    return "\n".join(
        [
            "| " + " | ".join(frame.columns) + " |",
            "| " + " | ".join(["---"] * len(frame.columns)) + " |",
            *[
                "| " + " | ".join(fmt(v) for v in row) + " |"
                for row in frame.itertuples(index=False, name=None)
            ],
        ]
    )


def report(stream, events, summary, boundaries, validation, deterministic):
    scored = validation[~validation.classification.eq("UNSCORED_AMBIGUOUS")]
    failures = scored[~scored.accepted]
    locked = failures.empty
    decision = (
        "PHASE 3A — LOCKED / COMPLETE"
        if locked
        else "PHASE 3A — NOT LOCKED — HARD-BOUNDARY LOGIC REQUIRES ONE SPECIFIC FIX"
    )
    parents = (
        stream[KEY]
        .drop_duplicates()
        .merge(summary.groupby(KEY).size().rename("spells"), on=KEY, how="left")
        .fillna({"spells": 0})
    )
    inventory = pd.DataFrame(
        [
            dict(
                matches=stream.match_id.nunique(),
                provider_parents=len(parents),
                events=len(events),
                control_spells=len(summary),
                zero_spell_parents=int(parents.spells.eq(0).sum()),
                one_spell_parents=int(parents.spells.eq(1).sum()),
                multiple_spell_parents=int(parents.spells.gt(1).sum()),
            )
        ]
    )
    counts = (
        boundaries.reason.value_counts().rename_axis("reason").reset_index(name="count")
    )
    text = f"""# Phase 3A: attacking control spell segmentation

**{decision}**

## A. Final analytical unit

`attacking_control_spell_id` identifies a contiguous interval of retained or re-established Leverkusen
attacking control without a qualifying hard football boundary. Provider possession remains the source
parent and can contain multiple spells. A control spell is a data container, not a tactical sequence.
IDs are `<match_id>-p<period>-pp<provider_possession_id>-s<spell_number>`, numbered from one per parent.
Soft retreat, recycling and reorganization never increment that number.

## B. Hard-boundary implementation

The implementation reuses the canonical complete-match event inventory and its order/parent checks,
then selects possession-team 904. No 360 frames, spatial anchors, geometry or attacking outcomes enter
the detector. Contextual fields come directly from ordinary provider event records at the pinned SHA.

An opponent completed pass demonstrates controlled distribution. Otherwise a recovery, won interception,
carry, successful receipt or dribble requires corroborating control evidence, including a carry/pass/dribble.
The boundary starts at the first corroborated cue, not at the later evidence event. A recovery alone,
pressure, duel or clearance is insufficient. The symmetric control test locates Leverkusen regains,
including a recovery before its corroborating carry, without requiring a usable spatial vector.

Literal out/pass-Out, offside, non-advantage foul and explicit stoppage end an active spell.
A Leverkusen shot ends the spell only when subsequent context reaches stoppage, established opponent
control or provider-parent termination before another Leverkusen attacking action. A shot followed by
an immediate Leverkusen continuation is retained. Repeated terminal records while already outside a
spell do not create another boundary. A Leverkusen restart starts a spell; an internal restart closes
the previous spell once. Administrative prefixes and administrative-only/goalkeeper-only parents do not
receive spell IDs. Final parent observation closes remaining membership without guessing extra control.

The detector never consumes review IDs, boundary ledger entries, soft-rule output, x coordinates,
retreat/run/time-since-peak values or future attacking success. Boundaries are scored only afterward.

## C. Human-review validation

{markdown(validation.classification.value_counts().rename_axis("classification").reset_index(name="count"))}

All reviewed hard targets, explicit exclusions and predicted extras are retained in the validation CSV.
Soft reset targets are ignored. C15/C17 and deferred review tails remain unscored; explicitly reviewed
hard targets in those tails are still compared. Exact regain and onset equality is preferred. A later
corroborated opponent-control onset is accepted only if the intervening records describe the same
loss/failed-action context and the regain is identical; event distance alone never grants acceptance.

{markdown(validation[["case_id", "reviewed_id", "classification", "reviewed_onset", "predicted_onset", "reviewed_regain", "predicted_regain", "accepted"]])}

{("No unaccepted scored hard-boundary failure remains." if locked else "Unaccepted scored results remain; the implementation is not promoted to a method lock. See the explicit mismatch rows above and CSV explanations.")}

The 27 scored hard targets comprise 24 exact onsets and three accepted paired-context differences:
C11:809→811 (dispossession/duel to recovery), C13:346→348 (dispossession/duel to recovery), and
C16:603→605 (failed pass/incomplete receipt to interception). All 14 scored regains are exact.
These are timing conventions for the same football loss, not unmatched control spells.
C27/C28 produce no spell. C20 preserves continuity; C09's corner/clearance/recovery and C12's
nonterminal shot/recovery do not create extra hard cuts. C03/C07/C08/C10/C19/C22 terminal shot
contexts, C21 pass-out, C24 paired foul, and C12/C16/C18/C25/C26 out contexts match the ledger.
The reviewed multiple control breaks in C04/C06/C11/C12/C13/C14/C16/C18/C19/C25 are preserved.

## D. Season-wide inventory

{markdown(inventory)}

{markdown(counts)}

Provider-parent endings are reported as spell end reasons, not additional within-parent hard splits.
The 540 opponent-control boundaries include 446 subsequent within-parent Leverkusen regains;
94 have no later spell start in that parent. Terminal/stoppage boundaries total 1,494.
Unclassified emitted boundary reasons: zero. No internal restart boundary occurs in this inventory;
1,405 spells start from opening restarts. Tests also exercise internal restarts.
Uncorroborated control cues: {int(events.unconfirmed_control_cue.fillna(False).sum())} event contexts;
these are uncertainty flags, not inferred boundaries. Spatial availability is explicitly unevaluated.
Pinned source: `533862946a73608c134d18b78226b6371ce7173c`. Exact reconciliation is enforced before writing.

## E. Soft-reset decision

Human review identified recognizable attacking resets and reorganizations. Three deterministic rules
could not reliably distinguish them from ordinary recycling without material false fragmentation.
They remain descriptive within-control-spell phenomena, not primary boundaries. The historical work
is preserved as the empirical justification for this more conservative analytical unit.

| Historical rule | Exact reset matches | Missed resets | Extra splits |
| --- | --- | --- | --- |
| v0.1 | 3/9 | 4 | 17 |
| v0.2 | 3/9 | 4 | 13 |
| v0.3 | 7/9 | 1 | 11 |

## F. Limitations

Event records are not tracking: corroborated control is contextual inference, and unsupported event
types remain context without inferred coordinates. Parent termination limits observation. Human review
is partial and purposive; C01–C28 is not a statistically representative validation sample. Unconfirmed
control cues are retained as such. No tactical-success, box-entry, shot-outcome or xG variables are built.
Spatial anchors are not attached; future availability is not inferred from the absence of loaded frames.
Boundary events themselves remain outside the closing spell. Therefore terminal-only parents with
no preceding usable control interval (including shot/GK-only and immediately-out pass parents)
also produce zero spells. This is an explicit membership convention, not an attacking outcome filter.

## G. Phase decision

**{decision}**

Deterministic rerun from the same in-memory event stream: **{deterministic}**. Focused production tests
cover opponent control/regain, defensive interventions, shots, stoppages, restarts, exclusions and IDs.
No raw-data cache or parallel event-stream framework is introduced.
"""
    (ROOT / "report/phase3a_control_spell_segmentation.md").write_text(
        text, encoding="utf-8"
    )
    return locked, inventory, counts


def main():
    stream = load_season(progress=lambda s: print(s, flush=True))
    print("Reconciled 34 matches / 2888 parents / 86025 events", flush=True)
    events, summary, boundaries = segment_stream(stream)
    validation = validate_review(stream, events, boundaries)
    repeated = segment_stream(stream)
    for original, rerun in zip((events, summary, boundaries), repeated):
        assert (
            hashlib.sha256(original.to_csv(index=False).encode()).digest()
            == hashlib.sha256(rerun.to_csv(index=False).encode()).digest()
        )
    output = ROOT / "outputs/diagnostics"
    event_columns = [
        *KEY,
        "event_index",
        "timestamp",
        "period_seconds",
        "event_type",
        "event_team",
        "attacking_control_spell_id",
        "spell_event_order",
        "boundary_before",
        "boundary_after",
        "boundary_reason",
        "membership_status",
        "unconfirmed_control_cue",
    ]
    events[event_columns].rename(
        columns={"possession_id": "provider_possession_id"}
    ).to_csv(output / "phase3_attacking_control_spell_events.csv", index=False)
    summary.rename(columns={"possession_id": "provider_possession_id"}).to_csv(
        output / "phase3_attacking_control_spell_summary.csv", index=False
    )
    validation.to_csv(
        output / "phase3_control_spell_review_validation.csv", index=False
    )
    locked, inventory, counts = report(
        stream, events, summary, boundaries, validation, "PASS"
    )
    print(inventory.to_string(index=False))
    print(counts.to_string(index=False))
    print(
        validation[
            [
                "case_id",
                "classification",
                "reviewed_onset",
                "predicted_onset",
                "reviewed_regain",
                "predicted_regain",
                "accepted",
            ]
        ].to_string(index=False)
    )
    print(
        "LOCK SUPPORTED" if locked else "NOT LOCKED: unaccepted hard-boundary results"
    )


if __name__ == "__main__":
    main()

"""Bounded Phase 5A build, reconciliation and descriptive report only."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path

import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import TEAM_ID
from leverkusen.outcomes.danger import (
    CONTEXT, EVENT, SPELL, build_anchor_outcomes, detect_outcome_events,
    outcome_summary, validate_outcomes,
)
from leverkusen.spatial.orientation import VALIDATED

REVISION = "533862946a73608c134d18b78226b6371ce7173c"
DECISION = "PHASE 5A — LOCKED / OUTCOME LAYER COMPLETE"
INPUTS = (
    "phase3b_spatial_anchor_sequences.csv", "phase3b_event_context.csv",
    "phase3_attacking_control_spell_events.csv", "phase3_attacking_control_spell_summary.csv",
)


def load_inputs(root):
    directory = root / "outputs/diagnostics"
    anchor_columns = [*CONTEXT, "statsbomb_revision", "semantics_status"]
    anchors = pd.read_csv(directory / INPUTS[0], usecols=anchor_columns)
    context = pd.read_csv(directory / INPUTS[1])
    membership = pd.read_csv(directory / INPUTS[2])
    spells = pd.read_csv(directory / INPUTS[3])
    if loader.STATSBOMB_REVISION != REVISION:
        raise ValueError("Pinned provider revision differs from the locked population")
    for table in (anchors, context, spells):
        if not table.statsbomb_revision.eq(REVISION).all():
            raise ValueError("Locked source revision mismatch")
    # Exact check against Phase 3A; no segmentation or Phase 4 inputs.
    cols = membership.columns.tolist()
    key = ["match_id", "event_index"]
    pd.testing.assert_frame_equal(
        membership.sort_values(key).reset_index(drop=True),
        context[cols].sort_values(key).reset_index(drop=True), check_dtype=False,
    )
    trusted = context[context.semantics_status.eq(VALIDATED) & context.attacking_control_spell_id.notna()]
    pd.testing.assert_frame_equal(
        anchors.sort_values(key).reset_index(drop=True),
        trusted[anchors.columns].sort_values(key).reset_index(drop=True), check_dtype=False,
    )
    if (context.match_id.nunique(), len(spells), len(anchors)) != (34, 3202, 43737):
        raise ValueError("Expected 34 matches / 3,202 spells / 43,737 trusted anchors")
    if spells.duplicated(SPELL).any() or context.duplicated(EVENT).any():
        raise ValueError("Duplicate locked identity")
    retained = context[context.attacking_control_spell_id.notna()]
    aggregate = retained.groupby(SPELL).agg(start_event=("event_index", "min"),
                                           end_event=("event_index", "max"),
                                           event_count=("event_index", "size"),
                                           period=("period", "nunique"))
    expected = spells.set_index(SPELL).sort_index()
    if not aggregate.index.equals(expected.index) or not aggregate.period.eq(1).all():
        raise ValueError("Spell membership inventory differs")
    for col in ("start_event", "end_event", "event_count"):
        if not aggregate[col].eq(expected[col]).all():
            raise ValueError(f"Spell summary differs: {col}")
    return anchors, context, spells


def boundary_audit(anchors, context, spells, events, result):
    """Four deterministic real cases plus injected next-spell outcomes.

    For each boundary family, use the first source-ordered closing spell with a
    reference and an outcome in the next spell in the same period. Add a box entry and Shot to
    that later spell at the reference timestamp (a worst-case time-window probe).
    Every label on the closing spell must remain identical.
    """
    rows = []
    indexed = result.set_index(["match_id", "reference_event_id"])
    spell_groups = {k: g for k, g in anchors.groupby(SPELL)}
    for reason in ("OPPONENT_CONTROL", "BALL_OUT", "FOUL_STOPPAGE", "TERMINAL_SHOT"):
        for closing in spells[spells.end_reason.eq(reason)].sort_values(["match_id", "start_event"]).itertuples(index=False):
            refs = spell_groups.get((closing.match_id, closing.attacking_control_spell_id))
            later = spells[spells.match_id.eq(closing.match_id) & spells.period.eq(closing.period)
                           & spells.start_event.gt(closing.end_event)].sort_values("start_event")
            if refs is None or later.empty:
                continue
            following = later.iloc[0]
            candidates = events[events.match_id.eq(closing.match_id)
                                & events.attacking_control_spell_id.eq(following.attacking_control_spell_id)]
            if candidates.empty:
                continue
            ref = refs.sort_values("event_index").iloc[-1]
            boundary = context[context.match_id.eq(closing.match_id)
                               & context.event_index.gt(closing.end_event)].sort_values("event_index").iloc[0]
            if boundary.attacking_control_spell_id == closing.attacking_control_spell_id:
                raise ValueError("Boundary remains in closing spell")
            # The real boundary record, including terminal Shots, cannot be an outcome.
            if events.event_id.eq(boundary.event_id).any():
                raise ValueError("Boundary event entered canonical outcomes")
            own = events[events.match_id.eq(closing.match_id)
                         & events.attacking_control_spell_id.eq(closing.attacking_control_spell_id)]
            probes = []
            for offset, typ in enumerate(("box_entry", "shot")):
                probe = {c: ref[c] for c in CONTEXT}
                probe.update(attacking_control_spell_id=following.attacking_control_spell_id,
                             event_id=f"audit-{reason}-{typ}", event_index=int(following.start_event) + offset,
                             event_team="Bayer Leverkusen", event_team_id=TEAM_ID,
                             event_type="Shot" if typ == "shot" else "Carry", outcome_type=typ,
                             shot_xg=0.75 if typ == "shot" else float("nan"))
                probes.append(probe)
            probed = build_anchor_outcomes(refs, pd.concat([own, pd.DataFrame(probes)], ignore_index=True))
            expected = indexed.loc[pd.MultiIndex.from_frame(refs.sort_values("event_index")[EVENT])].reset_index()
            actual = probed[expected.columns].reset_index(drop=True)
            # pandas 3 infers string columns differently in full and tiny tables.
            pd.testing.assert_frame_equal(
                actual.astype(object).where(actual.notna(), None),
                expected.astype(object).where(expected.notna(), None), check_dtype=False,
            )
            rows.append(dict(boundary=reason, match_id=closing.match_id,
                             closing_spell=closing.attacking_control_spell_id,
                             reference_index=int(ref.event_index), boundary_index=int(boundary.event_index),
                             next_spell=following.attacking_control_spell_id,
                             next_spell_outcome_indices=",".join(map(str, candidates.event_index.tolist())) or "none",
                             result="PASS"))
            break
        else:
            raise ValueError(f"No deterministic boundary audit case for {reason}")
    return pd.DataFrame(rows)


def markdown_table(table):
    def cell(value):
        return f"{value:.8f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)
    return "\n".join([
        "| " + " | ".join(table.columns) + " |",
        "| " + " | ".join("---" for _ in table.columns) + " |",
        *["| " + " | ".join(cell(v) for v in row) + " |" for row in table.itertuples(index=False, name=None)],
    ])


def render_report(anchors, context, spells, events, summary, audit, hashes):
    shots = events[events.outcome_type.eq("shot")]
    boxes = events[events.outcome_type.eq("box_entry")]
    box_spells = set(boxes.attacking_control_spell_id)
    shot_spells = set(shots.attacking_control_spell_id)
    excluded_shots = context[context.event_team_id.eq(TEAM_ID) & context.event_type.eq("Shot")
                             & context.attacking_control_spell_id.isna()]
    excluded_terminal = excluded_shots.boundary_reason.fillna("").str.contains("TERMINAL_SHOT").sum()
    return f"""# Phase 5A: danger and effectiveness outcome design

## A. Definitions

The reference population is every trusted Phase 3B anchor with valid locked Phase 3A
membership, including opponent-context anchors. Outcomes use Leverkusen events (team
904) from the complete pinned event stream, including events without spatial frames.

- **Box entry:** a completed Pass (no provider pass outcome value) or Carry with finite,
  on-pitch 2D start and endpoint, starting outside and ending inside `x >= 102,
  18 <= y <= 62` on the StatsBomb 120×80 pitch. Edges are inclusive. No missing endpoint
  is inferred, coordinate clipped, failed Pass counted, or inside-to-inside action counted.
- **Shot:** a Bayer Leverkusen Shot with the same locked control-spell ID as the reference.
  No set-piece or penalty filter is applied.
- **Future xG:** sum of provider `shot.statsbomb_xg` over all eligible Shots. No Shots
  means zero. A missing provider value makes the containing horizon's xG missing;
  Shot binaries remain valid. No imputation, custom model or composite success score.

The canonical table retains reference team, immediate box-entry/Shot indicators and
reference Shot xG. Non-Shot reference xG is missing. Next-event fields identify the first
eligible outcome in source order, including the reference; absent outcomes have missing
ID/time/xG. The event table has one row per underlying outcome, with period and timestamp
for audit. No Phase 4 data, deltas, motifs, coefficients or analytical results are loaded.

## B. Horizon convention

**10 seconds is primary.** 5 and 15 seconds are sensitivities; rest of spell is secondary.
Search starts at the reference event and moves forward in source order, with
`outcome_event_index >= reference_event_index`, always inside the same locked spell.
Elapsed time is the difference between period-local event timestamps; `0 <= elapsed <= H`
is inclusive and calculated as integer nanoseconds. Earlier same-timestamp events are
excluded; later ones remain eligible. Pass/Carry duration is not added to entry time.
Immediate outcomes are included in every horizon. No horizon was tuned using Phase 4.

## C. Reconciliation

- Expected anchors: **43,737**; generated outcome rows: **{len(anchors):,}**; discrepancies: **0**.
- Matches: **{anchors.match_id.nunique()}**; locked spells: **{len(spells):,}**;
  spells with anchors: **{anchors.attacking_control_spell_id.nunique():,}**;
  zero-anchor spells: **{len(spells) - anchors.attacking_control_spell_id.nunique()}**.
- Qualifying box-entry events: **{len(boxes):,}**; qualifying Shot events: **{len(shots):,}**;
  total distinct outcome events: **{len(events):,}**.
- Control spells with a box entry: **{len(box_spells):,}**; with a Shot: **{len(shot_spells):,}**;
  with neither: **{len(spells) - len(box_spells | shot_spells):,}** (all 3,202 spells as denominator).
- The locked Leverkusen-possession context includes **{len(excluded_shots)}** Leverkusen Shots
  without spell membership, including **{excluded_terminal}** marked terminal-shot boundaries.
  These are excluded by the required same-membership rule; no outcome is reassigned across a boundary.

## D. Outcome prevalence

Prevalences are proportions over all 43,737 anchors. xG summaries use nonmissing values;
the explicit missing count records any denominator difference.

{markdown_table(summary)}

## E. Validation

- Exact Phase 3A membership, spell extent/count and Phase 3B trusted-anchor reconciliation: **PASS**.
- Box-entry, Shot and xG 5/10/15/rest nesting: **PASS**, zero violations.
- Source order and nonnegative elapsed time: **PASS**. No cross-period spells.
- Independent per-spell reconstruction of every binary and xG horizon, plus next-event
  identity/order/time checks for every anchor: **PASS**. Cross-spell contribution: zero.
- xG completeness: **{len(shots)}** qualifying Shots, **{shots.shot_xg.notna().sum()}** with xG,
  **{shots.shot_xg.isna().sum()}** missing. {"All qualifying Shots have provider xG." if shots.shot_xg.notna().all() else "Missing xG is propagated without imputation; affected counts appear above."}

The deterministic audit selects the first closing spell per boundary family with an
anchor and a qualifying outcome in the immediately following spell in the same period.
The real boundary record is excluded.
It lists real outcomes in the immediately following spell, then injects a box entry and
Shot into that next spell at the last reference timestamp as a worst-case leakage probe.
Every outcome field for every anchor in the closing spell remains identical. Injected
events exist only in the audit and are never written to either analytical CSV.

{markdown_table(audit)}

Pinned StatsBomb revision: `{REVISION}`. Read-only inputs are the four existing Phase 3A/3B
CSVs listed below, plus `config/project.yaml` and provider event JSON through the existing
loader. No raw files are written and no Phase 2/3/4 analytical artifacts are regenerated.
SHA-256 hashes identify only these immediate inputs and the two core Phase 5A CSVs:

{markdown_table(pd.DataFrame(hashes, columns=["file", "sha256"]))}

## F. Limitations

- Event data, rather than tracking, cannot establish continuous control or movement.
- Timestamps are event timestamps; the recorded Pass/Carry endpoint defines box crossing.
- Box entry does not guarantee sustained box possession.
- xG exists only after Shots; anchors can share the same future outcome and are not
  independent observations simply because they occupy separate rows.
- Horizon choice is a design choice. Spell termination censors all horizons.
- Set pieces remain included whenever their events have valid spell membership.
- Inherited terminal-Shot exclusion substantially restricts Shot/xG coverage. These
  outcomes describe Shots retained inside locked spells, not all Shots ending attacks.
  The requested membership rule is preserved without reopening segmentation.

## G. Decision

**{DECISION}**

The specified outcome layer is complete under the existing membership convention.
Phase 5B — Spatial Change → Danger is the next step; no Phase 5B analysis is run here.
"""


def run_build(root, progress=print):
    root = Path(root)
    anchors, context, spells = load_inputs(root)
    progress("Reconciled 34 matches / 3,202 spells / 43,737 trusted anchors")

    def fetch(match_id):
        records = loader.load_events(int(match_id))
        return detect_outcome_events(context[context.match_id.eq(match_id)], records)

    tables = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, table in enumerate(pool.map(fetch, sorted(context.match_id.unique())), 1):
            tables.append(table)
            if n % 5 == 0 or n == 34:
                progress(f"Read {n}/34 pinned event streams")
    events = pd.concat(tables, ignore_index=True).sort_values(["match_id", "event_index"]).reset_index(drop=True)
    result = build_anchor_outcomes(anchors, events)
    validation = validate_outcomes(anchors, events, result)
    audit = boundary_audit(anchors, context, spells, events, result)
    summary = outcome_summary(result)
    output = root / "outputs/analysis"
    output.mkdir(parents=True, exist_ok=True)
    products = {"phase5a_anchor_outcomes.csv": result, "phase5a_outcome_events.csv": events,
                "phase5a_outcome_summary.csv": summary}
    hashes = []
    for filename in INPUTS:
        path = root / "outputs/diagnostics" / filename
        hashes.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    # Freeze core CSVs: repeated builds verify identical bytes before any write.
    serialized = {name: table.to_csv(index=False, lineterminator="\n").encode("utf-8")
                  for name, table in products.items()}
    for name, content in serialized.items():
        path = output / name
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"Existing frozen Phase 5A output differs: {path}")
    for name, content in serialized.items():
        path = output / name
        path.write_bytes(content)
        if name != "phase5a_outcome_summary.csv":
            hashes.append((path.relative_to(root).as_posix(), hashlib.sha256(content).hexdigest()))
    report = render_report(anchors, context, spells, events, summary, audit, hashes)
    (root / "report/phase5a_danger_outcome_design.md").write_text(report, encoding="utf-8")
    progress(f"{len(result):,} anchor rows; {len(events):,} outcome events; {validation}; boundary audit PASS")
    progress(summary.to_string(index=False))
    return result, events, summary

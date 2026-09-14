"""Season construction, explicit reconciliation and compact observational audit."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time

import pandas as pd
import requests

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.sequences.spatial_sequences import (
    EVENT, METRICS, PARENT, SIDES, SPELL, VALIDATED, attach_membership,
    construct_sequences, event_context, require_revision, spell_readiness,
)

PREFIX = "phase3b_"
DECISION = "READY WITH ANALYSIS-SPECIFIC SUPPORT REQUIREMENTS"


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def record_hash(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fetch_pinned(operation, *args):
    """Retry transient read failures without changing revision or source loader."""
    for attempt in range(3):
        try:
            return operation(*args)
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 2:
                raise


def write_identical(path, content):
    """Re-execution verifies identical bytes; changed artifacts require a new path."""
    path = Path(path)
    data = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite different existing artifact: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def reconcile(context, anchors, transitions):
    old = context[context.semantics_status.eq(VALIDATED)].copy()
    composition = old.event_type.value_counts().to_dict()
    if (len(old), composition, int(old.event_team_id.ne(TEAM_ID).sum())) != (
        46143, {"Pass": 20921, "Carry": 18525, "Pressure": 6109, "Shot": 588}, 6846
    ):
        raise ValueError(f"Phase 2C anchor reconciliation differs: {len(old)}, {composition}")
    old["previous_event_id"] = old.groupby(PARENT).event_id.shift(1)
    intervals = old[old.previous_event_id.notna()]
    if len(intervals) != 43431:
        raise ValueError("Prior provider-parent interval count differs")
    excluded = old[old.attacking_control_spell_id.isna()]
    if len(anchors) + len(excluded) != len(old):
        raise ValueError("Unexplained anchor attrition")
    retained_ids = set(anchors[EVENT].itertuples(index=False, name=None))
    old_pairs = set(intervals[["match_id", "previous_event_id", "event_id"]].itertuples(index=False, name=None))
    new_pairs = set(transitions[["match_id", "from_event_id", "to_event_id"]].itertuples(index=False, name=None))
    if new_pairs - old_pairs:
        raise ValueError("New interval bridges excluded anchors or mismatched identities")
    missing_endpoint = sum((m, a) not in retained_ids or (m, b) not in retained_ids for m, a, b in old_pairs - new_pairs)
    split_pair = len(old_pairs - new_pairs) - missing_endpoint
    if len(transitions) != len(anchors) - anchors.groupby(SPELL).ngroups:
        raise ValueError("Within-spell transition count mismatch")
    return dict(prior_anchors=len(old), excluded_anchors=len(excluded), prior_intervals=len(old_pairs),
                removed_intervals_missing_endpoint=missing_endpoint,
                removed_intervals_different_spells=split_pair, unexplained_discrepancies=0), excluded


def aggregate_tables(context, anchors, transitions, readiness, reconciliation, excluded):
    metrics = []
    for side in SIDES:
        for metric in METRICS:
            name = f"{side}_{metric}"
            for status, count in anchors[f"{name}_status"].value_counts().sort_index().items():
                metrics.append(dict(side=side, metric=metric, mathematical_status=status,
                                    anchor_count=int(count), trusted_anchor_denominator=len(anchors),
                                    primary_available_count=int(anchors[f"{name}_available"].sum()),
                                    primary_available_pct=100 * anchors[f"{name}_available"].mean(),
                                    available_transition_count=int(transitions[f"delta_{name}_status"].eq("ok").sum()),
                                    transition_denominator=len(transitions)))
    match_rows = []
    for mid, r in readiness.groupby("match_id", sort=True):
        a = anchors[anchors.match_id.eq(mid)]
        match_rows.append(dict(match_id=mid, spell_count=len(r), anchor_count=len(a),
                               zero_anchor_spells=int(r.has_0_anchors.sum()),
                               three_plus_anchor_spells=int(r.has_3_plus_anchors.sum()),
                               five_plus_anchor_spells=int(r.has_5_plus_anchors.sum()),
                               opponent_anchor_count=int(a.event_team_id.ne(TEAM_ID).sum())))
    rows = []

    def add(section, label, value, denominator=None):
        rows.append(dict(section=section, label=label, value=value, denominator=denominator,
                         percent=100 * value / denominator if denominator else None))

    for label in ("0", "1", "2", "3_plus", "5_plus"):
        add("anchor_count", label, int(readiness[f"has_{label}_anchors"].sum()), len(readiness))
    gap = transitions.seconds_from_previous_anchor
    for name, q in (("median", .5), ("p75", .75), ("p90", .9), ("p95", .95)):
        add("anchor_gap_seconds", name, gap.quantile(q))
    add("anchor_gap_seconds", "maximum", gap.max())
    for threshold in (1, 3, 5):
        add("anchor_gap_landmark", f"le_{threshold}_seconds", int(gap.le(threshold).sum()), len(gap))
    add("anchor_gap_landmark", "gt_5_seconds", int(gap.gt(5).sum()), len(gap))
    for (typ, role), count in anchors.groupby(["event_type", "anchor_role"]).size().items():
        add("composition", f"{typ}/{role}", int(count), len(anchors))
    for (status, typ), count in excluded.groupby(["membership_status", "event_type"]).size().items():
        add("excluded_prior_anchor", f"{status}/{typ}", int(count), len(excluded))
    for label, count in reconciliation.items():
        add("reconciliation", label, count)
    for status, count in context.semantics_status.value_counts().sort_index().items():
        add("full_context_semantics", status, int(count), len(context))
    for flag in ("frame_oob", "frame_coincident"):
        add("support", flag, int(anchors[flag].sum()), len(anchors))
    for name, q in (("p05", .05), ("median", .5), ("p95", .95)):
        add("visible_area_fraction", name, anchors.visible_area_fraction.quantile(q))
    return pd.DataFrame(match_rows), pd.DataFrame(metrics), pd.DataFrame(rows)


def markdown(frame):
    def fmt(value):
        if pd.isna(value):
            return "—"
        return f"{value:.3f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value).replace("|", "/")
    return "\n".join(["| " + " | ".join(frame.columns) + " |",
                       "| " + " | ".join(["---"] * len(frame.columns)) + " |",
                       *["| " + " | ".join(fmt(v) for v in row) + " |" for row in frame.itertuples(index=False, name=None)]])


def render_report(tables, reconciliation):
    a, t, r = (tables[k] for k in ("spatial_anchor_sequences", "spatial_anchor_transitions", "spell_spatial_readiness"))
    audit = tables["readiness_summary"]
    coverage = audit[audit.section.eq("anchor_count")][["label", "value", "percent"]]
    gaps = audit[audit.section.isin(["anchor_gap_seconds", "anchor_gap_landmark"])][["label", "value", "percent"]]
    composition = a.groupby(["event_type", "anchor_role"]).size().unstack(fill_value=0).reset_index()
    excluded = audit[audit.section.eq("excluded_prior_anchor")][["label", "value"]]
    availability = tables["metric_availability"].drop_duplicates(["side", "metric"])
    available = availability.pivot(index="metric", columns="side", values="primary_available_count").reset_index()
    support = audit[audit.section.isin(["support", "visible_area_fraction"])][["section", "label", "value", "percent"]]
    return f"""# Phase 3B: spatial-state sequence construction

**PHASE 3B — CONSTRUCTION COMPLETE / READY FOR METHOD-SPECIFIC SPATIAL ANALYSIS**

## A. Purpose and locked inputs

Construct spell-level spatial observations from the full ordered event stream, the existing
`attacking_control_spell_id` membership, trusted Phase 2C anchors and locked Phase 2B geometry.
Phase 3A remains **LOCKED / COMPLETE**, unchanged: 34 matches, 2,888 provider parents,
86,025 context events and 3,202 control spells. The source revision is
`{loader.STATSBOMB_REVISION}`. No soft resets or new boundaries enter this build.

The existing Phase 3A event CSV has no UUID. Exact `(match_id, event_index)` equality against
the pinned complete stream recovers it, with one-to-one checks of period, parent, possession
team, timestamp, elapsed time, event type and event team. This is exact provider identity,
never nearest order or timestamp matching. All subsequent joins use `(match_id, event_id)`.
The Phase 3A summary revision, Phase 2C source inventory and every selected geometry revision
must agree. The full historical geometry file must match its Phase 2B protected SHA-256.
The manifest records input, code, canonical fetched-record and analytical output hashes.

## B. Construction method

Re-run the existing complete-match Phase 2C semantic audit, including both directions of
explicit related-event evidence. Only `validated_core_event_team_scope` supplies states.
Unsupported and missing frames remain in `phase3b_event_context.csv`, including events outside
spells with their original membership status. No outcomes are exported or used; outcome-bearing
provider payloads are removed before invoking the shared event inventory validator.

Each anchor inherits its spell; `spatial_anchor_order` is one-based and follows source order.
`events_from_previous_anchor` is the difference in complete-stream positions (adjacent events
have gap 1); `intervening_event_count` subtracts one. `events_from_spell_start` is zero-based.
Seconds use actual period-local provider timestamps, including stoppage time, without endpoint
arrival estimates. First-anchor previous IDs/gaps and last-anchor next IDs remain missing.

The geometry source is the locked `phase2a_frame_geometry.csv`, under the Phase 2B contract.
The existing Phase 2C point-team mapper assigns literal event-team and other-team subsets to
`lev_` and `opp_`; `all_` denotes all visible. Original subset names remain as source metadata.
These primary fields exclude keepers; keeper-included counts remain alongside them and all six
original geometry variants remain linkable by match/event/frame index. Event-team identity
determines the mapping independently of possession team. The existing normalizer retains
Leverkusen-event centroids and rotates opponent-event centroids `(120-x, 80-y)`. Width/depth,
hull area and spacing are invariant under that rotation and retain their original values.
No home/away or period flip is applied. Units remain StatsBomb coordinate units (area squared).

The Phase 2B `D_primary` eligibility utility supplies each metric's availability: mathematical
status `ok` and actor status single/none, without a count, coverage, OOB or coincidence cutoff.
Each metric retains value, original status and availability, with side-specific selected count,
keeper policy, OOB/coincidence and measurement flags, and shared actor/visible-area support.
Whole-original-frame anomaly flags are carried separately from selected-outfield flags.

Transitions join consecutive trusted anchors within the same match and spell. Only two
available endpoints produce a delta; otherwise the delta is missing, with from/to/both-endpoint
status and original endpoint metric statuses. Endpoint support accompanies the transition.
These deltas are **differences between two event-aligned partial observations**, not continuous
movement or rates. Pressure is an observation of spatial structure, not an automatic ball or
progression action. Opponent anchors remain explicitly labeled as context.

## C. Anchor reconciliation

The old population reproduces exactly **46,143** trusted anchors: Pass 20,921; Carry 18,525;
Pressure 6,109; Shot 588; opponent-event anchors 6,846. Old provider-parent intervals reproduce
exactly **43,431**. The spell build contains **{len(a):,} anchors**, **{len(t):,} transitions**
and **{int(a.event_team_id.ne(TEAM_ID).sum()):,} opponent-event anchors**.

Exactly **{reconciliation['excluded_anchors']:,}** prior trusted anchors have no locked spell
membership. These are excluded solely by Phase 3A's existing membership convention; terminal
boundary records belong outside the closing spell. Geometry availability causes no anchor loss.
The event-context output retains each excluded UUID and membership/boundary reason for inspection.

{markdown(excluded)}

The {43431-len(t):,} removed old intervals comprise
**{reconciliation['removed_intervals_missing_endpoint']:,}** with at least one excluded endpoint and
**{reconciliation['removed_intervals_different_spells']:,}** whose retained endpoints belong to different
spells. No new pair bridges an excluded prior anchor. Transition count also equals retained
anchors minus spells with at least one anchor. **Unexplained discrepancies: 0.**

{markdown(composition)}

## D. Control-spell spatial coverage

All **{len(r):,}** spells remain in the readiness inventory, including zero-anchor spells.
Percentages use all 3,202 spells. The 5+ group is nested within 3+.

{markdown(coverage)}

The spell table also retains event count/duration, anchor proportions, per-type/team counts,
transition count, first/last anchor offsets, median/p90/maximum gaps and metric availability
counts. Single-anchor spells have no gap statistics. Sparse-spell quantiles are descriptive
and can be determined by very few pairs; their transition counts make that support explicit.

## E. Anchor-gap structure

Seconds across the {len(t):,} within-spell pairs; quantiles use linear interpolation of the
observed gap distribution. Landmark percentages use the number of observed transitions.

{markdown(gaps)}

Long gaps do not invalidate endpoints, split spells or create exclusions. Consecutive spatial
anchors need not be consecutive football actions. No interpolation, forward fill or synthetic
anchors are used.

## F. Metric availability

Available primary keeper-excluded measurements out of **{len(a):,}** trusted anchors per side:

{markdown(available)}

`phase3b_metric_availability.csv` gives exact mathematical statuses, primary percentages and
available transition counts for every metric/side. Semantic trust does not certify every
geometry metric, full-team observation or comparable point composition at two endpoints.

{markdown(support)}

Visible-area fractions describe supplied on-pitch coverage, not complete player observation.
No new sensitivity analysis or exclusion policy is applied. Later comparisons can apply the
locked whole-frame OOB/coincidence checks using retained endpoint metadata.

## G. Match-level consistency

All 34 matches contribute anchors and control spells. Coverage varies; every match remains
visible in the season denominator. Counts below impose no match or spell exclusion.

{markdown(tables['match_coverage'])}

## H. Limitations

These are event-aligned partial observations, with no continuous tracking. Ordinary off-ball
players are anonymous; endpoint records do not establish persistent player identity. Missing
and unsupported frames, variable visible area, changing selected counts/composition and gaps
between anchors limit comparisons. Metric-specific support remains necessary even when both
endpoint values exist. No interpolation or continuous-movement inference is made. This phase
constructs no outcomes, tactical labels, sequence archetypes or effectiveness analysis.

## I. Readiness decision

**{DECISION}**

Exact joins and source reconciliation succeed, all matches are represented, and
{int(r.has_3_plus_anchors.sum()):,} spells contain at least three observations; however,
{int(r.has_0_anchors.sum()):,} have none and {int(r.has_1_anchors.sum()):,} have only one.
Variable observation density and metric/visibility support require an explicit support strategy
for the chosen analysis. Anchor counts can describe the observations available for before/after
or richer ordered comparisons, but this audit approves no universal minimum-anchor or maximum-gap
threshold. Successful CSV reruns verify byte-identical outputs and preserve historical artifacts.

Phase 3B construction is complete; Phase 3 as a whole is not declared complete. Next authorized
discussion: **select the first within-control-spell spatial-change analysis**.
"""


def run_construction(root, progress=print):
    root = Path(root)
    started = time.perf_counter()
    out = root / "outputs/diagnostics"
    inputs = ["outputs/diagnostics/phase3_attacking_control_spell_events.csv",
              "outputs/diagnostics/phase3_attacking_control_spell_summary.csv",
              "outputs/diagnostics/phase2c2_source_inventory.csv",
              "outputs/diagnostics/phase2a_frame_geometry.csv",
              "outputs/diagnostics/phase2b_lock_protected_hashes.json",
              "docs/phase2b3_metric_calibration_matrix.csv", "config/project.yaml"]
    hashes = {p: sha256(root / p) for p in inputs}
    geometry_path = inputs[3]
    protected = json.loads((root / inputs[4]).read_text())
    if hashes[geometry_path] != protected[geometry_path]:
        raise ValueError("Historical Phase 2B geometry hash differs")
    membership = pd.read_csv(root / inputs[0])
    summary = pd.read_csv(root / inputs[1])
    inventory = pd.read_csv(root / inputs[2])
    require_revision(summary.statsbomb_revision)
    require_revision(inventory.statsbomb_revision)
    matches = sorted([m for m in fetch_pinned(loader.load_matches) if TEAM_ID in (
        field(m, "home_team", "home_team_id"), field(m, "away_team", "away_team_id"))], key=lambda m: m["match_id"])
    if len(matches) != 34 or set(inventory.match_id) != {m["match_id"] for m in matches}:
        raise ValueError("Season match inventory differs")

    def fetch(match):
        mid = match["match_id"]
        events = fetch_pinned(loader.load_events, mid)
        frames = fetch_pinned(loader.load_360, mid)
        context = event_context(match, events, frames, source_revision=loader.STATSBOMB_REVISION)
        source = dict(match_id=mid, events_url=f"{loader.BASE_URL}/events/{mid}.json",
                      frames_url=f"{loader.BASE_URL}/three-sixty/{mid}.json",
                      canonical_events_sha256=record_hash(events), canonical_frames_sha256=record_hash(frames))
        return context, source

    contexts, sources = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, (context, source) in enumerate(pool.map(fetch, matches), 1):
            contexts.append(context)
            sources.append(source)
            progress(f"Audited pinned semantic sources: {i}/34 matches")
    canonical = pd.concat(contexts, ignore_index=True)
    context = attach_membership(membership, canonical)
    if (len(context), len(context[PARENT].drop_duplicates()), len(summary)) != (86025, 2888, 3202):
        raise ValueError("Phase 3A inventory differs")
    selected = context[context.attacking_control_spell_id.notna() & context.semantics_status.eq(VALIDATED)][EVENT]
    geometry = []
    for chunk in pd.read_csv(root / geometry_path, chunksize=60000, low_memory=False):
        require_revision(chunk.statsbomb_revision)
        geometry.append(chunk.merge(selected, on=EVENT, how="inner", validate="many_to_one"))
    geometry = pd.concat(geometry, ignore_index=True)
    progress(f"Attaching {len(selected):,} trusted member anchors to locked geometry")
    anchors, transitions = construct_sequences(context, geometry)
    readiness = spell_readiness(context, anchors, summary)
    reconciliation, excluded = reconcile(context, anchors, transitions)
    match_coverage, metric_availability, aggregate = aggregate_tables(context, anchors, transitions, readiness, reconciliation, excluded)
    if match_coverage.anchor_count.eq(0).any():
        raise ValueError("Material observability problem: a match has no anchors")
    tables = dict(event_context=context, spatial_anchor_sequences=anchors,
                  spatial_anchor_transitions=transitions, spell_spatial_readiness=readiness,
                  match_coverage=match_coverage, metric_availability=metric_availability,
                  readiness_summary=aggregate)
    # Independent construction replay from the same reconciled inputs, including ordering.
    again_a, again_t = construct_sequences(context, geometry)
    again_r = spell_readiness(context, again_a, summary)
    for original, again in ((anchors, again_a), (transitions, again_t), (readiness, again_r)):
        if original.to_csv(index=False, lineterminator="\n") != again.to_csv(index=False, lineterminator="\n"):
            raise ValueError("Nondeterministic analytical construction")
    output_hashes = {}
    for name, table in tables.items():
        path = out / f"{PREFIX}{name}.csv"
        output_hashes[str(path.relative_to(root)).replace("\\", "/")] = write_identical(path, table.to_csv(index=False, lineterminator="\n"))
    report = root / "report/phase3b_spatial_sequence_construction.md"
    output_hashes[str(report.relative_to(root)).replace("\\", "/")] = write_identical(report, render_report(tables, reconciliation))
    code = ["src/leverkusen/sequences/spatial_sequences.py", "src/leverkusen/sequences/spatial_readiness.py",
            "scripts/spatial_sequence_construction.py", "src/leverkusen/sequences/control_spells.py",
            "src/leverkusen/sequences/readiness.py", "src/leverkusen/data/semantic_diagnostics.py",
            "src/leverkusen/spatial/orientation.py", "src/leverkusen/spatial/geometry.py",
            "src/leverkusen/spatial/calibration.py", "src/leverkusen/data/loader.py"]
    manifest = dict(statsbomb_revision=loader.STATSBOMB_REVISION, input_sha256=hashes,
                    code_sha256={p: sha256(root / p) for p in code},
                    matches_canonical_sha256=record_hash(matches), sources=sources,
                    output_sha256=output_hashes, reconciliation=reconciliation,
                    deterministic_construction_replay="PASS", readiness_decision=DECISION)
    manifest_path = out / f"{PREFIX}manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        for key, value in manifest.items():
            if previous[key] != value:
                raise ValueError(f"Rerun manifest reconciliation differs: {key}")
        progress("Independent execution: all analytical CSV, input/source and code hashes identical")
    else:
        manifest.update(generated_at_utc=datetime.now(timezone.utc).isoformat(),
                        runtime_seconds=round(time.perf_counter() - started, 3),
                        python_version=platform.python_version(), pandas_version=pd.__version__)
        write_identical(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    if hashes != {p: sha256(root / p) for p in inputs}:
        raise ValueError("Historical input changed during construction")
    progress(f"Anchors: {len(anchors):,}; transitions: {len(transitions):,}; {DECISION}")
    return tables

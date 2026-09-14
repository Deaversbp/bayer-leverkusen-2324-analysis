# Bayer Leverkusen 2023/24 Spatial Sequence Analysis

Analyze how Bayer Leverkusen created dangerous attacking space during the unbeaten
2023/24 Bundesliga season using StatsBomb event and 360 data.

**Phase 2C = LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE, 10 September 2026.**
**Phase 3A = LOCKED / COMPLETE — attacking control spells, 13 September 2026.**
The primary unit is `attacking_control_spell_id`, constructed from hard football/control
boundaries in the full event stream. The pinned season contains 3,202 spells from
2,888 provider parents. Soft-reset replays remain historical development evidence;
recycling does not create new spells. See the [implementation and validation report](report/phase3a_control_spell_segmentation.md)
and [locked method](docs/methods_specification.md#43-phase-3a-attacking-control-spell-lock).
Next: attach Phase 2C trusted spatial anchors to attacking control spells and construct
spatial-state sequences. Anchor attachment is not implemented by this lock.
Phase 1/1B, locked Phase 2A and human-approved Phase 2B remain complete. The
34-match semantic audit supports a conservative 72,596-frame core scope;
45,985 frames remain unsupported for operational team/orientation mapping.
Phase 2C-2 readiness audit (10 September 2026) finds **READY — WITH RESTRICTIONS**:
2,888 Leverkusen possessions contain 46,143 validated anchors; 84.07% have at
least three, across all 34 matches. Human review approved Recommendation A:
the existing `validated_core_event_team_scope` is locked for **validated
spatial-anchor sequence analysis**. **Phase 3 — Possession and Spatial-Sequence
Method Design is now authorized** within that scope.
Linked-cloud contradictions and mixed event-type orientation remain unresolved
outside that scope. Final sequence construction and tactical work remain later
gates. See the [readiness findings](docs/methods_specification.md#39-phase-2c-2-validated-spatial-anchor-coverage-and-sequence-readiness), the
[Phase 2C approval and locked boundary](docs/methods_specification.md#40-human-approved-phase-2c-restricted-semantic-scope-lock),
the Phase 2B
[approved contract](docs/methods_specification.md#37-human-approved-phase-2b-lock-and-operational-research-scope)
and [calibration matrix](docs/phase2b3_metric_calibration_matrix.csv).

## Research objective and dataset

How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24
Bundesliga season, and which recurring attacking sequences were most effective
against different defensive structures?

This football-facing primary question is preserved. Its operational analytical
formulation, defining what event + 360 data can directly support, is:

> How did Bayer Leverkusen’s attacking sequences alter the event-aligned visible spatial structure around possession, and which recurring structural changes preceded dangerous attacking outcomes?

Both formulations remain active; observed change and precedence do not establish
causation or continuous movement.

The project uses [StatsBomb Open Data](https://github.com/hudl/open-data):
competition 9, season 281, team Bayer Leverkusen (904), on a 120 × 80 coordinate
grid. The pinned audit confirmed 34 Leverkusen matches, 137,765 events and 118,581
frames, all linked to events (86.074838% event coverage), with zero orphan frames
or duplicate event/frame IDs. Phase 2B comparison eligibility is now locked;
comparison-specific observational support and downstream semantics still require review.
See [research questions](docs/research_questions.md).

## Methodological scope

StatsBomb 360 supplies **event-aligned partial spatial observations**. Prioritize
observed spatial structure, visible outfield structure and spatial-state changes
around possession. Use visible width/depth, centroid, pairwise/nearest-neighbor
spacing and the **observed outfield convex-hull footprint**. Hull is a secondary,
observation-sensitive measure; structural claims should triangulate relevant
measures and context rather than rely on hull alone. No composite is required.

The project cannot faithfully reproduce continuous velocity, acceleration,
continuous player trajectories, true time-to-intercept models, full dynamic pitch
control, continuous EPV tracking models, or named off-ball trajectories when
player identity is unavailable. Do not claim complete 22-player state, complete
defensive shape, actual occupied area, true controlled space, continuous team-shape
reconstruction or reconstructed tracking. Team/orientation semantics are locked
only for frames passing every existing Phase 2C gate. Full-sample normalization
remains unsupported; sequence construction and outcome definitions remain later
gates. See the
[methods specification](docs/methods_specification.md) and
[metric registry](docs/metric_registry.md).

## Approved Phase 2B calibration

D-primary requires only the metric's existing status `ok` and actor status
`single` or `none`. No universal n/coverage minimum, polygon-containment gate,
edge-distance cutoff or automatic OOB exclusion is approved. Null visibility
minima mean **no universal hard cutoff approved**, not pending calibration or zero.
Primary eligibility does not permit naive pooling: every structural comparison
must report count, coverage, subset, keeper policy, OOB/coincidence flags and actor
status, and document a common-support strategy when needed. No adjustment or
weighting method is selected now.

Keeper-excluded geometry is primary for observed outfield centroid, width/depth,
hull and spacing. Keeper-included geometry remains for an explicitly named full
visible footprint and sensitivity; count inventories report both. Every future
headline spatial finding routinely receives **OOB-B whole-frame exclusion** as a
robustness comparison. Coincidence exclusion is sensitivity for count, centroid
and spacing; records are never deduplicated. Hull n>=14/7/7 and NN n>=11/10/5/4
landmarks apply **only in the exact subset/keeper sensitivity rules in the matrix**.
Finite supplied coordinates and both measurement variants remain preserved.

## Revised roadmap

Phase 3A control-spell segmentation is locked. The next authorized step attaches the
validated Phase 2C anchors to these event-stream containers and constructs spatial-state
sequences, retaining Phase 2B metric-specific eligibility/support. Tactical sequence
units, minimum anchors, maximum gaps and analytical windows remain later decisions.
The development order remains:

1. Reliable possession and sequence construction.
2. Event-aligned spatial-state sequences.
3. Descriptive spatial-state change.
4. Success/failure outcome definitions.
5. Comparisons of evolution preceding box entries, shots and future xG.
6. Recurring interpretable attacking mechanisms.

Inferred defensive lines, high/mid/deep regimes, compactness composites, Voronoi,
valuable-space composites, graphs, clustering and learned spatial representations
are **OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION**. Each must answer a
specific need, fit the observation model, add interpretable value over simpler
geometry, permit validation and materially improve the football analysis.
They are not globally rejected; existing tracking-dependent rejections stand.
No downstream method is implemented by this documentation lock.

## Setup (PowerShell / VS Code)

The working environment was verified with Python 3.14 on Windows. Package syntax
requires Python 3.10 or later; other environments have not been verified.

```powershell
python -m venv .venv  # Only when an environment does not already exist
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Select `.venv/Scripts/python.exe` as the VS Code interpreter and notebook kernel.
Editable installation makes `leverkusen` importable from the root or notebooks
directory. Do not add more notebook path hacks.

`requirements.in` lists direct dependencies for current code, notebooks, YAML and
development. `requirements-lock.txt` is a freeze of the verified local environment,
including added test/lint/build tools, not a cross-platform solver lock. It contains
Windows dependencies. The original `requirements.txt` is retained unchanged as a
historical snapshot. To resolve a fresh environment on another platform, install
`requirements.in` and validate it before freezing. No broad upgrade is part of this
migration.

## Data access

```python
from leverkusen.data.loader import load_matches, load_events, load_360
from leverkusen.data.transforms import normalize_events, build_team_event_dataset

matches = load_matches()  # Nested list[dict], unchanged source order/fields
events = normalize_events(load_events(3895292))  # pandas DataFrame
frames = load_360(3895292)  # Event-aligned nested records
passes = build_team_event_dataset(matches, "Bayer Leverkusen", event_type="Pass")
```

The new loader fetches individual Open Data resources through `requests`, already
used in this repository. It retains original nested records so normalization and
notebook columns remain stable; statsbombpy is not required. There is no database,
persistent raw-data storage or automatic disk cache. Reuse DataFrames in a session
to avoid repeated requests.

All four loaders use the original Leverkusen release revision
`533862946a73608c134d18b78226b6371ce7173c` (May 21, 2024), configured once in
`config/project.yaml`. Matches, events, lineups and 360 use that same immutable SHA;
no match is special-cased. The revision is read when the loader is imported, so
restart Python/notebook kernels after changing it. Branch names and short SHAs are
rejected. The editable research package requires the repository's config file.

Pinning addresses the observed incompatibility between event IDs and 360 UUIDs in
three matches under later upstream `master`. It does not repair or heuristically
relink identifiers. Existing local files have unverified revision provenance;
`raw_data_dir` remains a separate legacy option and is never used by the pinned audit.

Missing resources (including unavailable 360) raise `FileNotFoundError`; transport
and other HTTP failures propagate from `requests`. Invalid match IDs raise
`ValueError`. An absent frame is not evidence of zero visible players.

Existing ignored `data/raw/` files are preserved. For read-only offline use, pass
`raw_data_dir=Path("data/raw")` to package loaders or `build_team_event_dataset`.
The old `src.data_loader` and `src.transforms` imports remain compatibility wrappers
with their original local-file behavior, after editable installation. Updated
notebooks use the new on-demand API. Old saved outputs are retained historical
outputs, not evidence of a new live execution.

`scripts/download_data.py` is retained unchanged solely for legacy compatibility.
It writes raw files and is **outside the new workflow**; do not run it for Phase 1.
No new pipeline calls it. See [data notes](data/README.md).

## Repository structure

```text
config/                 Constants, provisional zones, documented visibility policy
docs/                   Methods, source foundation, metrics, research questions
notebooks/              00 observability audit through 07 effectiveness scaffolds
                        Existing 00_data_audit and 01_pass_eda are preserved
src/leverkusen/
  data/                 Loader and migrated normalization/context transforms
  spatial/              Basic geometry and diagnostics; later spatial modules reserved
  sequences/            Temporary possession/anchor readiness diagnostics;
                        analytical sequences and outcomes remain reserved
  tactics/              Reserved defensive structures and attacking patterns
  models/               Reserved baselines and validation
  visualization/        Geometry diagnostics; pitch and sequence figures reserved
scripts/                Observability and geometry diagnostics; future analysis CLIs
tests/                  Offline regression tests and marked live checks
outputs/                Ignored diagnostics, figures, tables
report/                 Article and technical appendix scaffolds
```

Basic geometry, semantics and possession-readiness diagnostics are implemented;
analytical sequence, tactical and model modules remain reserved. Feature and analysis script entry
points still exit with status 2.

## Phase 1 observability audit

```powershell
.\.venv\Scripts\python.exe scripts/audit_data.py
```

The command uses existing on-demand loaders, verifies 34 unique Leverkusen matches,
and writes only these derived files under `outputs/diagnostics/`:

- `phase1_match_summary.csv`: inventory, event/frame ID integrity, 360 load errors,
  actor-distance statistics, retrieval time and upstream source URL.
- `phase1_frame_summary.csv`: one row per original frame, including orphan and
  ambiguous links, raw player flags, polygon checks, actor distance and review rank.
- `phase1_attrition.csv`: season, match, event-type and event-team partitions, with
  independent coverage counts and explicitly named cumulative mechanical checks.
- `phase1_actor_distance_by_event_type.csv`: count, mean, median, p75/p90/p95/p99
  and maximum direct distance for each event type with measurable pairs.
- `phase1_coordinate_semantics_by_event_type.csv`: direct/mirrored medians, p95s
  and percentages closer under each hypothesis, using measurable pairs only.
- `phase1_multiple_actor_frames.csv`: all actor locations and the linked event
  location for multiple-actor frames; no actor is chosen as correct.

`actor_distance` remains the direct distance, also named `actor_distance_direct`.
`actor_distance_mirrored` compares the actor with the diagnostic point
`(120-x, 80-y)`. These comparisons never mutate coordinates, normalize direction,
or create event-type rules. The closer hypothesis can still be a poor match.

`notebooks/00_data_observability_audit.ipynb` presents these tables and diagnostic
distributions. It reads existing derived CSVs first; when absent it runs the audit
in memory. Re-run the CLI to refresh the outputs. Shapely is required specifically
for visible-area polygon validity and intersection with the pitch.

Missing 360 files and load failures are recorded separately; an event-load failure
aborts because the season denominator cannot be inferred. Missing/invalid IDs never
join. Duplicate event IDs leave linked frame metadata ambiguous, and duplicate
frames retain separate rows. Missing frames are not represented as zero-player
frames. Null calibration thresholds remain untouched.

The historical unpinned audit found 108,394 linked events out of 137,765 (78.68%),
with 118,607 frames and 10,213 orphans in three UUID-incompatible matches. The
pinned rerun resolved those joins: all 118,581 frames link to events across all
34 matches. Four frames retain two identical actor locations and are excluded
from single-actor diagnostics. Coordinate hypotheses remain diagnostic; neither
automatic mirroring nor direction-dependent tactical interpretation is justified
by a closer distance alone. See the [Phase 1B findings](report/technical_appendix.md#phase-1b-pinned-revision-and-coordinate-semantics)
and [Phase 2A scope](docs/methods_specification.md#28-analysis-phases-and-immediate-phase-2a-boundary).

## Phase 2A geometry diagnostics

```powershell
.\.venv\Scripts\python.exe scripts/geometry_diagnostics.py
```

The CLI fetches the pinned release in memory and writes nine derived CSVs under
`outputs/diagnostics/`: `phase2a_frame_geometry.csv`, `phase2a_match_summary.csv`,
`phase2a_inventory.csv`, `phase2a_metric_summary.csv`, `phase2a_metric_status.csv`,
`phase2a_histograms.csv`, `phase2a_by_valid_points.csv`,
`phase2a_goalkeeper_sensitivity.csv` and `phase2a_anomalies.csv`.
These generated files are ignored by Git; no raw JSON or full frames are saved.

`build_frame_geometry(match_id, events, frames, source_revision=...)` in
`leverkusen.spatial.geometry` emits six rows per original frame: all-visible and
literal teammate True/False subsets, each with keepers included/excluded. Each
numeric field has its own status, with observability and record-quality metadata.
Excluded retains only literal keeper False. Native coordinates and coincident
record weights remain unchanged; the measurement layer applies no research
eligibility filter. The separately documented Phase 2B D-primary rule is locked.

Open `notebooks/03_spatial_geometry.ipynb` after running the CLI. It reads compact
derived summaries, validates their source revision and presents distributions,
keeper sensitivity and exact point-count strata. See the
[implementation results](report/technical_appendix.md#phase-2a-implementation-and-initial-diagnostics).

## Verification and reproducibility

Offline tests use synthetic records and mocked HTTP, not repeated downloads.
Run optional live checks explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest -m network tests/test_loader.py
```

Keep raw data out of Git and write only derived diagnostics, tables and figures
under `outputs/`. Record retrieval time, upstream revision, match IDs, software
versions, missingness, exclusions and configuration with future analytical outputs.
The loader pins the data release independently of the dependency lock. The match
summary records the exact SHA, source URL and retrieval time. The audit reads
project constants; visibility and analysis configs
remain research specifications. Visibility nulls mean no universal hard cutoff
approved; outcome-window nulls still mean uncalibrated later definitions, not zero.

Keep reusable logic in the package and exploration in notebooks. Document source
provenance and operational definitions before locking methods, and perform
sensitivity analysis before conclusions. Credit StatsBomb and follow the
[Open Data attribution guidance](https://github.com/hudl/open-data#terms--conditions)
when sharing work.

## Phase 2B-2 observation quality and edge review

Run `python scripts/observation_quality.py` in the existing virtual environment
after Phase 2A diagnostics exist. It reads the pinned derived geometry, retrieves
360 records in memory, and writes 18 compact CSVs plus three diagnostic figures
and seven representative contact sheets. Raw records are never persisted. Review
the Phase 2B-2 section of [notebook 03](notebooks/03_spatial_geometry.ipynb) and the
[technical appendix](report/technical_appendix.md#phase-2b-2--observation-quality-and-edge-validation)
for empirical findings, limitations and calibration readiness.

## Phase 2B calibration evidence and decision record

`python scripts/calibration.py` evaluates the historical candidate grid from
existing derived geometry offline. It does not apply production filters or lock
every evaluated alternative. Earlier saved notebook/candidate outputs retain
their pre-approval labels; the current methods contract and versioned calibration
matrix control the human-approved decision. No expensive diagnostic rerun is
required for this lock.

The 9 September 2026 decision is **not a scientific version bump**: calibration
followed the pre-specified validation process, no population/outcome changed after
effectiveness analysis, and scope was narrowed before tactical/outcome analysis.
The football question and Phase 2A formulas/data are unchanged. See the
[decision record](report/technical_appendix.md#phase-2b-human-approval-and-research-scope-lock--9-september-2026).

## Phase 2C semantics and orientation review

Run `.venv/Scripts/python scripts/semantics_orientation.py` to audit pinned
events, 360 and lineups across the season in memory. It writes compact
`outputs/diagnostics/phase2c_*.csv` tables and 27 deterministic native/normalized
figures under `outputs/figures/`. Generated outputs remain ignored by Git.
No raw JSON or duplicate frame dataset is saved. For presentation-only refreshes,
`--figures-only` reuses the completed audit manifest and retrieves only its
selected matches; rerun the full audit if semantic rules or source change.

Open [notebook 04](notebooks/04_semantics_orientation.ipynb) after the CLI. It
reads derived evidence offline, checks provenance and presents teammate,
event/possession, orientation, exceptions, normalization and representative
plots. It does not rerun downloads or overload the locked geometry notebook.
The existing `04_defensive_structures.ipynb` scaffold is unchanged.

Within the explicit validated scope, True/False map to event team/other team.
Native coordinates already place the event team's attack toward +x. Choosing
Leverkusen as target records identity for its events and rotates both axes for
opponent events. Unsupported cases return missing normalized coordinates.
This additional layer does not change raw coordinates, Phase 2A geometry or
Phase 2B eligibility. The [style guide](docs/visualization_style_guide.md) applies
Leverkusen red, opponent charcoal and gold action markers only to that scope.
See the [results and blockers](report/technical_appendix.md#phase-2c-semantic-and-orientation-audit--9-september-2026).

## Phase 2C-2 sequence-readiness audit

```powershell
.\.venv\Scripts\python.exe scripts/sequence_readiness.py
```

The CLI retrieves the pinned match/event/360 resources in memory and reapplies
the unchanged Phase 2C frame gates, including complete-match incoming/outgoing
related-cloud conflict checks. It writes 18 derived `phase2c2_*.csv` files in
`outputs/diagnostics/` and three neutral aggregate figures in `outputs/figures/`.
No raw JSON, full-season event table or final analytical sequence dataset is
persisted. Outputs remain ignored by Git.

Open [notebook 05](notebooks/05_sequence_readiness.ipynb) for offline review of
the possession inventory, count/gap distributions, all 34 matches, duration and
shot groups, event-team/type composition, candidate windows and ten complete
representative timelines. The existing sequence-construction scaffold is unchanged.

The audit retains all 86,025 events in provider Leverkusen possessions, including
opponent, unsupported, unlinked and administrative events. Match + period +
provider possession ID + possession-team ID defines each diagnostic unit.
The median possession supplies 10 validated anchors; median/p90 consecutive gaps
are 1.103/3.214 seconds. Among 571 shot-containing possessions, 87.74% have at
least three anchors. Opponent events supply 14.84% of validated anchors.

The audit originally recommended A, pending human review. **Human approval on
10 September 2026 now locks the restricted semantic scope** for validated
spatial-anchor sequence analysis. More unsupported-type semantic work is not
necessary before restricted sequence design. No anchor minimum, maximum gap,
temporal window or outcome is selected by this lock.
See the [complete evidence and limitations](report/technical_appendix.md#phase-2c-2-sequence-readiness-audit--10-september-2026).

## Approved Phase 2C scope and change control

Historical progression is preserved: the initial Phase 2C audit was **VALIDATED
PARTIALLY — NOT LOCKED**; Phase 2C-2 found **READY — WITH RESTRICTIONS**; human
review then approved **LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE**.
Saved audit tables, notebooks and dated findings retain their original status;
the [approval record](docs/methods_specification.md#40-human-approved-phase-2c-restricted-semantic-scope-lock)
controls current authorization. No scientific version bump is required: the
decision follows pre-outcome semantic validation and the pre-specified readiness
audit, without changing raw data, Phase 2A/2B methods or research questions.

Only Pass, Carry, Shot and Pressure frames passing **all** existing frame-level
gates qualify. Within that scope, literal teammate True/False maps to event
team/other known match team. Event team remains separate from possession team,
including the 6,846 opponent anchors in Leverkusen possessions. Native event-team
attack is +x; the Leverkusen reference uses identity for its events and
`(120-x, 80-y)` for opponent events, preserving raw coordinates. No half, venue,
possession-team or x-only flip is approved. Pressure is a spatial anchor, not
automatically a ball location or a Leverkusen possession action.

Unsupported events remain full-stream context; their frames supply no trusted
normalized spatial state, team-color mapping, interpolation or forward fill.
The style guide is locked only within validated scope. This approval does not
resolve unsupported-type semantics or off-ball identities, authorize unrestricted
full-sample spatial analysis, or create final sequences, outcomes or tactics.

## Phase 3A-1 progression and reset diagnostics

```powershell
.\.venv\Scripts\python.exe scripts/progression_diagnostics.py
```

The CLI retrieves the pinned match/event/360 resources in memory, reuses the
locked semantic/orientation functions, and writes 28 derived `phase3a1_*.csv`
files plus four figures under ignored `outputs/`. It retains the complete
86,025-event context and reconciles all 2,888 groups, 46,143 anchors and 43,431
anchor intervals with Phase 2C-2. Raw records and previous outputs are preserved.

Open [notebook 06](notebooks/06_progression_reset_diagnostics.ipynb) for offline
review. Reusable code lives in `leverkusen.sequences.progression_diagnostics`;
existing pattern-discovery and sequence scaffolds remain unchanged.

The action layer contains **37,984 Leverkusen Pass/Carry vectors** with explicit
valid endpoints and validated Phase 2C frames. Another 5,713 otherwise explicit
vectors remain context without normalized action coordinates. Opponent and
Pressure anchors remain separate from Leverkusen action vectors. Among 2,662
measurable possessions, median net progression is **31.0 x-units**, cumulative
forward/backward medians are **57.75/18.1**, and median/p90 maximum peak retreat
are **16.8/53.2**. The 226 groups without safe actions remain in the inventory.

Retreat/recovery use ordered action start/end vertices, not additional independent
360 states or inferred endpoint arrival times. Inter-action jumps, skipped context,
initial field position and censoring need review. Both plotted extreme examples
begin with provider Corner events at x=120; a running peak initialized there can
remain unrecovered throughout subsequent play.

Outputs cover sign runs, three temporal layers, observed/censored peak recovery,
literal provider termination context, candidate prevalence/overlap sweeps, a
50-possession extreme inventory and **26 complete deterministic review timelines**.
No reset setting is selected. Phase 3A-2 review precedes Phase 3A-3 segmentation
calibration and method lock. See [methods section 41](docs/methods_specification.md#41-phase-3a-1-progression-and-reset-diagnostics)
and the [measured findings](report/technical_appendix.md#phase-3a-1-progression-and-reset-diagnostics--10-september-2026).


## Phase 3A-2A human review pack

**Phase 3A-2A = REVIEW PACK READY ? HUMAN LABELING PENDING.** Phase 3A-1
remains **DIAGNOSTIC / NOT A METHOD LOCK**; Phase 3A is not complete.

Open [07_boundary_review.ipynb](notebooks/07_boundary_review.ipynb) or the generated
[static review pack](outputs/review/phase3a2_boundary_review.html). The pack contains
28 possessions (all 26 earlier representatives plus two), 181 neutral candidate
review moments, 28 complete timelines and progression figures, and 17 spatial
triptychs. All 25 requested case categories have descriptive examples. The 51
snapshot slots contain 37 validated panels and 14 explicit unavailable states.

Annotate [phase3a2_boundary_review_sheet.csv](outputs/diagnostics/phase3a2_boundary_review_sheet.csv)
manually. All five human fields are blank, including confidence. Use the manifest's
`review_order` for the intended reading order; case IDs remain stable. No boundary
labels, segmentation rule/threshold, outcome or model was introduced. Numeric
screens are review sampling criteria only. Geometry is corroborative evidence;
missing spatial observations and endpoint arrival times remain unresolved.

```powershell
.\.venv\Scripts\python.exe scripts/boundary_review.py
# Offline rendering from existing derived review CSVs:
.\.venv\Scripts\python.exe scripts/boundary_review.py --render-only
```

The builder reuses Phase 3A-1 evidence and audits only the nine representative
matches, fetching pinned events/360 once per match in a normal build. It writes
only derived `phase3a2_` outputs and refuses to overwrite human annotations. The
notebook reads derived outputs offline. Next: **human Phase 3A-2B review**, then
separately authorized Phase 3A-3 calibration and method lock after labels exist.
See [methods section 42](docs/methods_specification.md#42-phase-3a-2a-representative-possession--boundary-review-pack).

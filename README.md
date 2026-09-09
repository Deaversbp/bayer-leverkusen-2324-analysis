# Bayer Leverkusen 2023/24 Spatial Sequence Analysis

Analyze how Bayer Leverkusen created dangerous attacking space during the unbeaten
2023/24 Bundesliga season using StatsBomb event and 360 data.

**Current phase: Phase 2B = LOCKED / COMPLETE — human approval, 9 September 2026.**
Phase 1/1B and locked Phase 2A geometry are complete. Human review approved
D-primary, keeper conventions and metric-specific robustness challenges after
the Phase 2B diagnostics. The immediate next gate is **team/role semantics and
attacking-orientation validation**; tactical spatial interpretation remains
blocked until it passes. Existing event/passing EDA is preserved. See the
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
reconstruction or reconstructed tracking. Team/role semantics, orientation,
sequence construction and outcome definitions remain later gates. See the
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

The next gate is **team/role semantics and attacking-orientation validation**.
After that, prioritize:

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
  sequences/            Reserved possessions, event states, outcomes
  tactics/              Reserved defensive structures and attacking patterns
  models/               Reserved baselines and validation
  visualization/        Geometry diagnostics; pitch and sequence figures reserved
scripts/                Observability and geometry diagnostics; future analysis CLIs
tests/                  Offline regression tests and marked live checks
outputs/                Ignored diagnostics, figures, tables
report/                 Article and technical appendix scaffolds
```

Basic geometry and its diagnostic plots are implemented; other spatial, sequence,
tactical and model modules remain reserved. Feature and analysis script entry
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

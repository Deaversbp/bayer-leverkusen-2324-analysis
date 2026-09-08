# Bayer Leverkusen 2023/24 Spatial Sequence Analysis

Analyze how Bayer Leverkusen created dangerous attacking space during the unbeaten
2023/24 Bundesliga season using StatsBomb event and 360 data.

**Current phase: Phase 2B-2 observation quality and edge validation complete.**
Phase 2A basic geometry remains locked and implemented. Phase 1/1B
observability, revision pinning and coordinate diagnostics are complete. Phase 2A
provides the eight locked within-frame geometry families and descriptive diagnostics;
model selection and tactical interpretation remain deferred. Existing event/passing
EDA is preserved. Final visibility thresholds and analytical eligibility remain
open. Phase 2B-1/2B-2 provide empirical count, coverage, keeper, boundary and
record-quality diagnostics, including 28 representative frames. Evidence is ready
for human-reviewed Phase 2B-3 calibration; no rules have been selected. See the
[current methodology contract](docs/methods_specification.md).

## Research objective and dataset

How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24
Bundesliga season, and which recurring attacking sequences were most effective
against different defensive structures?

The project uses [StatsBomb Open Data](https://github.com/hudl/open-data):
competition 9, season 281, team Bayer Leverkusen (904), on a 120 × 80 coordinate
grid. The pinned audit confirmed 34 Leverkusen matches, 137,765 events and 118,581
frames, all linked to events (86.074838% event coverage), with zero orphan frames
or duplicate event/frame IDs. Metric-specific eligibility remains to be locked
before analysis.
See [research questions](docs/research_questions.md).

## Methodological scope

StatsBomb 360 is event-aligned freeze-frame spatial context, **not continuous
22-player tracking**. Planned measurements include visible-player coordinates,
teammate/opponent structure, visible defensive width/depth, centroids, convex
hulls, pairwise spacing, zone occupation, local overloads, visible-area-clipped
Voronoi, and changes between event-aligned spatial states.

The project cannot faithfully reproduce continuous velocity, acceleration,
continuous player trajectories, true time-to-intercept models, full dynamic pitch
control, continuous EPV tracking models, or named off-ball trajectories when
player identity is unavailable. Use “visible defensive width” rather than an
unsupported full-team estimate. Orientation, visibility selection, outcome windows
and defensive-regime definitions require audit and calibration. See the
[methods specification](docs/methods_specification.md) and
[metric registry](docs/metric_registry.md).

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
config/                 Constants, provisional zones, null calibration values
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
record weights remain unchanged; there is no final eligibility filter.

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
remain research specifications. Null thresholds mean uncalibrated, not zero.

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

# Bayer Leverkusen 2023/24 Spatial Sequence Analysis

Analyze how Bayer Leverkusen created dangerous attacking space during the unbeaten
2023/24 Bundesliga season using StatsBomb event and 360 data.

**Current phase: Phase 1 — Data & Observability Audit.** Model selection and
tactical conclusions have NOT yet been performed. Existing event and passing EDA
is preserved. The implemented observability audit exposes coverage and integrity
issues; it does not select final visibility thresholds or a final usable sample.

## Research objective and dataset

How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24
Bundesliga season, and which recurring attacking sequences were most effective
against different defensive structures?

The project uses [StatsBomb Open Data](https://github.com/hudl/open-data):
competition 9, season 281, team Bayer Leverkusen (904), on a 120 × 80 coordinate
grid. The existing release contains 34 Leverkusen matches. The first audit must
reconfirm the match sample and qualify event/360 coverage before modeling.
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
  spatial/              Reserved geometry, visibility, zones, Voronoi modules
  sequences/            Reserved possessions, event states, outcomes
  tactics/              Reserved defensive structures and attacking patterns
  models/               Reserved baselines and validation
  visualization/        Reserved pitch and sequence figures
scripts/                Working observability audit; future features/analysis CLIs
tests/                  Offline regression tests and marked live checks
outputs/                Ignored diagnostics, figures, tables
report/                 Article and technical appendix scaffolds
```

Spatial, sequence, tactical and model modules remain reserved. Feature and analysis
script entry points still exit with status 2; the observability audit is implemented.

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

`notebooks/00_data_observability_audit.ipynb` presents these tables and diagnostic
distributions. It reads existing derived CSVs first; when absent it runs the audit
in memory. Re-run the CLI to refresh the outputs. Shapely is required specifically
for visible-area polygon validity and intersection with the pitch.

Missing 360 files and load failures are recorded separately; an event-load failure
aborts because the season denominator cannot be inferred. Missing/invalid IDs never
join. Duplicate event IDs leave linked frame metadata ambiguous, and duplicate
frames retain separate rows. Missing frames are not represented as zero-player
frames. Null calibration thresholds remain untouched.

The first live audit found 108,394 linked events out of 137,765 (78.68%), with
118,607 frames loaded across all 34 matches. Three matches have no event/frame UUID
overlap, accounting for 10,213 orphan frames. Actor-coordinate discrepancies also
require review before general spatial analysis. See the
[Phase 1 results and limitations](report/technical_appendix.md#phase-1-live-observability-results).

## Verification and reproducibility

Offline tests use synthetic records and mocked HTTP, not repeated downloads.
Run optional live checks explicitly:

```powershell
.\.venv\Scripts\python.exe -m pytest -m network tests/test_loader.py
```

Keep raw data out of Git and write only derived diagnostics, tables and figures
under `outputs/`. Record retrieval time, upstream revision, match IDs, software
versions, missingness, exclusions and configuration with future analytical outputs.
The loader uses upstream `master`, so a dependency freeze alone does not freeze the
data release. The audit reads project constants; visibility and analysis configs
remain research specifications. Null thresholds mean uncalibrated, not zero.

Keep reusable logic in the package and exploration in notebooks. Document source
provenance and operational definitions before locking methods, and perform
sensitivity analysis before conclusions. Credit StatsBomb and follow the
[Open Data attribution guidance](https://github.com/hudl/open-data#terms--conditions)
when sharing work.

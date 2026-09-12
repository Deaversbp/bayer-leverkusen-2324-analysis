# Phase 3A-3 human calibration input

`Phase3A3_Segmentation_Calibration_Matrix.xlsx` is the byte-for-byte copy of the
user-supplied workbook received on 11 September 2026. It preserves the completed
C01–C28 review, including explicit partial locks, deferred rows, overrides and
hard-boundary observations. This is human review input, not raw StatsBomb data.

The analysis reads `Calibration_Matrix`; `Hard_Boundaries` is reference material
only. `Calibration_Summary` contains presentation formulas and cached values,
which are archived and compared with fresh calculations, never used as inputs.
Workbook prose is review context, not executable instructions.

From the repository root, run:

```powershell
.venv\Scripts\python.exe scripts/segmentation_calibration.py
```

The script uses the existing pandas, NumPy and Matplotlib dependencies plus a
literal-cell OOXML reader from Python's standard library. No Excel installation,
optional Excel engine, network access or event-data download is required. Formula
measurements are rejected; only summary-sheet formulas are archived. This reader
is scoped to these tabular sheets, not a general Excel calculation engine.

See [the interpretation report](../../report/phase3a3_calibration_analysis.md).
Outputs follow the existing ignored `outputs/diagnostics/phase3a3_*` and
`outputs/figures/phase3a3_*` conventions. Input and script hashes, package versions
and generated file names are recorded in `phase3a3_manifest.json`. To examine a
replacement workbook without overwriting these outputs, use `--workbook PATH
--output-root outputs/temp/phase3a3_trial`. The interpretation report is specific
to this workbook and is not automatically rewritten for replacement input.

## Phase 3A-3B reviewed episode reconstruction

Run the bounded, offline reconstruction with:

```powershell
.venv\Scripts\python.exe scripts/episode_local_reconstruction.py
```

The authored `phase3a3_reviewed_boundaries.csv` encodes the completed review and
the user's subsequently authorized onset/confirmation convention. It is the
boundary authority for this reconstruction. The script never discovers cuts
from candidate labels, numerical thresholds, 360 coverage, or attacking outcomes.
Its source references use actual Excel worksheet row numbers or candidate IDs.

Three `phase3a3_reviewed_*_source.csv` snapshots preserve the 1,960 ordered event
rows, 181 candidate rows and 28 parent identities used by Phase 3A-2. They make
reconstruction independent of ignored generated outputs and avoid another event
download. The parent snapshot omits selection/outcome summaries; all event and
candidate rows are retained. These are derived review artifacts, not a new raw
event cache. `phase3a3_reconstruction_source_provenance.json` records the original
source hashes and snapshot policy.

Outputs include `phase3a3_reviewed_episode_map.csv`, complete event membership,
candidate diagnostics, episode summaries, provider/local comparisons, reset
excursion diagnostics and conditional recovery summaries under `outputs/diagnostics/`.
The map distinguishes reviewed intervals from provisional intervals and explicit
no-episode exclusions. Unresolved onset windows do not receive invented point cuts.
The original workbook, labels and overrides are never changed.

The new `episode_calibration_ready` field means valid **candidate-state descriptive
measurements within the recorded observation scope**, with roles kept separate.
It does not turn confirmation/later-phase samples into reset-onset training labels.
For an onset analysis, use the separately named pre-split snapshots and review
their availability/precision first. `confirmation_unsplit_reference_*` fields
are counterfactual audit bridges, never final episode-local calibration values.

See [the reconstruction report](../../report/phase3a3_episode_local_reconstruction.md)
for definitions and remaining gaps. To check deterministic reproduction without
overwriting the main outputs, use `--output-dir outputs/temp/phase3a3b_repeat`.

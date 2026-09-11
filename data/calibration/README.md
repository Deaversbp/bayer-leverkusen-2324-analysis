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

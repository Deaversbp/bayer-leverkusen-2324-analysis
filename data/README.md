# Data policy

Fetch StatsBomb Open Data on demand with `leverkusen.data.loader` and work in
pandas DataFrames. No database or new persistent raw-data cache is used.

The pre-migration `raw/` directory contains 34 event files, 34 lineup files,
34 360 files and one season match file. These user files were inspected and left
untouched; they remain ignored by Git. Existing empty `interim/` and `processed/`
directories were also left untouched.

For explicit read-only compatibility, use `raw_data_dir=Path("data/raw")` with
package loaders or the dataset builder. Missing local files raise an error; this
option does not silently fetch or write replacements. Legacy `src` wrappers retain
local-file behavior. `scripts/download_data.py` is historical working code, retained
for compatibility, and is not part of the new workflow.

Write derived figures, tables and diagnostics under `outputs/`. Do not commit raw
match, event, lineup or 360 JSON, and do not clone the full Open Data repository here.

"""Run pinned Phase 3A-1 progression/reset diagnostics; no episode segmentation."""

from pathlib import Path

from leverkusen.sequences.progression_diagnostics import run_progression_diagnostics
from leverkusen.visualization.progression import write_progression_figures


def main():
    root = Path(__file__).resolve().parents[1]
    tables = run_progression_diagnostics(
        root / "outputs/diagnostics", progress=lambda s: print(s, flush=True)
    )
    paths = write_progression_figures(tables, root / "outputs/figures")
    print(tables["action_displacement_summary"].to_string(index=False))
    print(tables["temporal_gap_summary"].to_string(index=False))
    print(
        f"Wrote {len(tables)} CSVs and {len(paths)} figures. DIAGNOSTIC / NOT A METHOD LOCK."
    )


if __name__ == "__main__":
    main()

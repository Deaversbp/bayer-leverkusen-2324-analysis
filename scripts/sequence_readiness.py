"""Run the pinned Phase 2C-2 possession/anchor audit without constructing a dataset."""

from pathlib import Path

from leverkusen.sequences.readiness import run_readiness
from leverkusen.spatial.orientation import PHASE2C_STATUS
from leverkusen.visualization.readiness import write_readiness_figures


def main():
    root = Path(__file__).resolve().parents[1]
    tables = run_readiness(root / "outputs/diagnostics")
    paths = write_readiness_figures(tables, root / "outputs/figures")
    print(tables["sequence_readiness_summary"].to_string(index=False))
    print(f"Wrote {len(tables)} diagnostic CSVs and {len(paths)} figures.")
    print(f"Phase 2C: {PHASE2C_STATUS}. Phase 3 method design is authorized.")


if __name__ == "__main__":
    main()

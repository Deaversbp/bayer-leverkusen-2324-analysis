"""Summarize existing Phase 2A observations; no retrieval or calibration."""

import argparse
from pathlib import Path

from leverkusen.spatial.observation_sensitivity import run_observation_sensitivity


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "outputs/diagnostics"
    summaries = run_observation_sensitivity(
        output_dir / "phase2a_frame_geometry.csv", output_dir
    )
    print(summaries["run_summary"].to_string(index=False))
    print(summaries["visible_area_bins"].to_string(index=False))
    print("Wrote seven compact phase2b1_*.csv files from existing geometry.")


if __name__ == "__main__":
    main()

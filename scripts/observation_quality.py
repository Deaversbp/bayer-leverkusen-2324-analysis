"""Run pinned Phase 2B-2 empirical observation-quality and edge diagnostics."""

import argparse
from pathlib import Path

from leverkusen.spatial.observation_quality import run_observation_quality


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    summaries = run_observation_quality(
        root / "outputs/diagnostics/phase2a_frame_geometry.csv",
        root / "outputs/diagnostics",
        root / "outputs/figures",
    )
    print(summaries["run_summary"].to_string(index=False))


if __name__ == "__main__":
    main()

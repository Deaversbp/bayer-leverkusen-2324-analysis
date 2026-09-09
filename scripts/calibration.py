"""Compare Phase 2B-3 proposals offline; never apply calibration permanently."""

import argparse
from pathlib import Path

from leverkusen.spatial.calibration import run_calibration


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    output = Path(__file__).resolve().parents[1] / "outputs/diagnostics"
    summaries = run_calibration(output / "phase2a_frame_geometry.csv", output)
    print(summaries["run_summary"].to_string(index=False))


if __name__ == "__main__":
    main()

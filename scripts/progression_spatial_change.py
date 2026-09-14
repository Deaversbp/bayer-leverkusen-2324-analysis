"""Run Phase 4A; --offline verifies and reuses the derived action dataset."""

import argparse
from pathlib import Path

from leverkusen.spatial.progression_change_runner import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], offline=args.offline, build_only=args.build_only)

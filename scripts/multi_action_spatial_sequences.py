"""Build fixed overlapping two/three-action spatial windows from frozen inputs."""

import argparse
from pathlib import Path

from leverkusen.sequences.multi_action_runner import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[1], build_only=args.build_only)

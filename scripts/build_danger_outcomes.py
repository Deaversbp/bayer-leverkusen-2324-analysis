"""Build and validate the frozen Phase 5A outcome layer; no Phase 5B analysis."""

from pathlib import Path

from leverkusen.outcomes.runner import run_build


if __name__ == "__main__":
    run_build(Path(__file__).resolve().parents[1])

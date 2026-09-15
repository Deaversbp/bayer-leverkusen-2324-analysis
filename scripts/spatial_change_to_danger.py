"""Run Phase 5B from the frozen Phase 4A and Phase 5A analytical datasets."""

from pathlib import Path

from leverkusen.spatial.danger_runner import run


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])

"""Run Phase 5C from frozen Phase 4B windows and Phase 5A terminal outcomes."""

from pathlib import Path

from leverkusen.sequences.effectiveness_runner import run


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])

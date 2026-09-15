"""Run only Phase 6A from frozen Phase 3B/5B/5C tables and Phase 4B identities."""

from pathlib import Path

from leverkusen.tactics.context_runner import run


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])

"""Construct Phase 3B sequences from pinned sources and existing locked artifacts."""

from pathlib import Path

from leverkusen.sequences.spatial_readiness import run_construction


if __name__ == "__main__":
    run_construction(Path(__file__).resolve().parents[1])

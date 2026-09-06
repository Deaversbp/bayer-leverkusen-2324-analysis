"""Legacy local-file API; new callers should use leverkusen.data.loader.

Wrappers preserve the original offline workflow using existing raw files.
Install the package with python -m pip install -e . before using these imports.
"""

from pathlib import Path

from leverkusen.data import loader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def _load_json(path: Path) -> list[dict]:
    """Read an existing JSON file with the legacy missing-file error."""
    return loader._load_json(path)


def load_matches() -> list[dict]:
    """Load existing local 2023/24 Bundesliga match records."""
    return loader.load_matches(raw_data_dir=RAW_DATA_DIR)


def load_events(match_id: int) -> list[dict]:
    """Load existing local event records for one match."""
    return loader.load_events(match_id, raw_data_dir=RAW_DATA_DIR)


def load_lineups(match_id: int) -> list[dict]:
    """Load existing local lineup records for one match."""
    return loader.load_lineups(match_id, raw_data_dir=RAW_DATA_DIR)


def load_360(match_id: int) -> list[dict]:
    """Load existing local 360 records for one match."""
    return loader.load_360(match_id, raw_data_dir=RAW_DATA_DIR)

"""Load raw StatsBomb JSON files for the Bayer Leverkusen project."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def _load_json(path: Path) -> list[dict]:
    """Read a JSON file and return its parsed list of dictionaries."""
    if not path.is_file():
        raise FileNotFoundError(f"StatsBomb JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_matches() -> list[dict]:
    """Load the raw 2023/24 Bundesliga matches JSON."""
    path = RAW_DATA_DIR / "matches" / "9" / "281.json"
    return _load_json(path)


def load_events(match_id: int) -> list[dict]:
    """Load the raw event JSON for one match."""
    path = RAW_DATA_DIR / "events" / f"{match_id}.json"
    return _load_json(path)


def load_lineups(match_id: int) -> list[dict]:
    """Load the raw lineup JSON for one match."""
    path = RAW_DATA_DIR / "lineups" / f"{match_id}.json"
    return _load_json(path)


def load_360(match_id: int) -> list[dict]:
    """Load the raw StatsBomb 360 JSON for one match."""
    path = RAW_DATA_DIR / "three-sixty" / f"{match_id}.json"
    return _load_json(path)

"""Fetch StatsBomb Open Data as nested records without writing raw files.

An explicit ``raw_data_dir`` supports read-only use of pre-migration files.
No disk or in-memory cache is maintained by this module.
"""

import json
import re
from numbers import Integral
from pathlib import Path

import requests
import yaml

COMPETITION_ID = 9
SEASON_ID = 281
REQUEST_TIMEOUT = 30
PROJECT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "project.yaml"


def load_source_revision(config_path: Path = PROJECT_CONFIG) -> str:
    """Read the repository's immutable source SHA; reject branches and short SHAs.

    The editable research package uses config/project.yaml as its single source
    of truth. Restart the Python process after changing this configuration.
    """
    project = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    revision = project.get("statsbomb_revision") if isinstance(project, dict) else None
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError(
            "statsbomb_revision must be a full lowercase 40-character commit SHA"
        )
    return revision


# Snapshot once: every resource fetched in this process uses the same revision.
STATSBOMB_REVISION = load_source_revision()
BASE_URL = f"https://raw.githubusercontent.com/hudl/open-data/{STATSBOMB_REVISION}/data"


def _load_json(path: Path) -> list[dict]:
    """Read an existing JSON file, preserving the legacy missing-file error."""
    if not path.is_file():
        raise FileNotFoundError(f"StatsBomb JSON file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_records(relative_path: str, raw_data_dir: Path | None) -> list[dict]:
    if raw_data_dir is not None:
        return _load_json(Path(raw_data_dir) / relative_path)
    url = f"{BASE_URL}/{relative_path}"
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    if response.status_code == 404:
        raise FileNotFoundError(f"StatsBomb JSON file not found: {url}")
    response.raise_for_status()
    records = response.json()
    if not isinstance(records, list) or any(
        not isinstance(record, dict) for record in records
    ):
        raise ValueError(f"Expected a list of StatsBomb records from {url}")
    return records


def _match_path(data_type: str, match_id: int) -> str:
    # pandas/numpy integer scalars occur in the original audit notebook.
    if isinstance(match_id, bool) or not isinstance(match_id, Integral):
        raise ValueError("match_id must be a positive integer")
    if match_id <= 0:
        raise ValueError("match_id must be a positive integer")
    return f"{data_type}/{match_id}.json"


def load_matches(*, raw_data_dir: Path | None = None) -> list[dict]:
    """Return the unfiltered 2023/24 Bundesliga release as nested match records."""
    return _load_records(f"matches/{COMPETITION_ID}/{SEASON_ID}.json", raw_data_dir)


def load_events(match_id: int, *, raw_data_dir: Path | None = None) -> list[dict]:
    """Return nested event records for one match, in source order."""
    return _load_records(_match_path("events", match_id), raw_data_dir)


def load_lineups(match_id: int, *, raw_data_dir: Path | None = None) -> list[dict]:
    """Return the original list of team lineups for one match."""
    return _load_records(_match_path("lineups", match_id), raw_data_dir)


def load_360(match_id: int, *, raw_data_dir: Path | None = None) -> list[dict]:
    """Return event-aligned frames; missing coverage raises FileNotFoundError."""
    return _load_records(_match_path("three-sixty", match_id), raw_data_dir)

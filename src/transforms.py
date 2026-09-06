"""Compatibility entry points preserving the original local-file workflow."""

import pandas as pd

from leverkusen.data.transforms import (
    build_team_event_dataset as _build_team_event_dataset,
)
from leverkusen.data.transforms import (
    get_team_match_context as get_team_match_context,
    normalize_events as normalize_events,
)
from src import data_loader


def build_team_event_dataset(
    matches: list[dict],
    team_name: str,
    event_type: str | None = None,
) -> pd.DataFrame:
    """Build the legacy team dataset using existing local raw files."""
    return _build_team_event_dataset(
        matches, team_name, event_type, raw_data_dir=data_loader.RAW_DATA_DIR
    )

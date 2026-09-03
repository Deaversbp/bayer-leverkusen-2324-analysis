"""Build analysis-ready event datasets from raw StatsBomb data."""

import pandas as pd

from src.data_loader import load_events


def normalize_events(events: list[dict]) -> pd.DataFrame:
    """Flatten a raw list of StatsBomb events into a DataFrame."""
    return pd.json_normalize(events, sep="_")


def get_team_match_context(match: dict, team_name: str) -> tuple[str, str]:
    """Return the opponent and venue for a team in one match."""
    home_team = match["home_team"]["home_team_name"]
    away_team = match["away_team"]["away_team_name"]

    if team_name == home_team:
        return away_team, "Home"

    if team_name == away_team:
        return home_team, "Away"

    raise ValueError(
        f"Team {team_name!r} is not the home or away team for "
        f"match {match['match_id']}."
    )


def build_team_event_dataset(
    matches: list[dict],
    team_name: str,
    event_type: str | None = None,
) -> pd.DataFrame:
    """Build one team event DataFrame across the supplied matches.

    If no events match the filters, return an empty DataFrame containing only
    the four match-context columns.
    """
    match_dataframes = []

    for match in matches:
        match_id = match["match_id"]
        opponent, venue = get_team_match_context(match, team_name)

        events = load_events(match_id)
        event_dataframe = normalize_events(events)

        if event_dataframe.empty:
            continue

        team_events = event_dataframe.loc[
            event_dataframe["team_name"] == team_name
        ].copy()

        if event_type is not None:
            team_events = team_events.loc[
                team_events["type_name"] == event_type
            ].copy()

        if team_events.empty:
            continue

        team_events["match_id"] = match_id
        team_events["match_date"] = pd.to_datetime(match["match_date"])
        team_events["opponent"] = opponent
        team_events["venue"] = venue

        match_dataframes.append(team_events)

    if not match_dataframes:
        return pd.DataFrame(
            columns=["match_id", "match_date", "opponent", "venue"]
        )

    return pd.concat(match_dataframes, ignore_index=True)

"""Download Bayer Leverkusen's 2023/24 StatsBomb Open Data JSON files."""

from __future__ import annotations

import json
from pathlib import Path

import requests


COMPETITION_ID = 9
SEASON_ID = 281
TEAM_NAME = "Bayer Leverkusen"
REQUEST_TIMEOUT = 30
BASE_URL = "https://raw.githubusercontent.com/hudl/open-data/master/data"


def create_data_directories(project_root: Path) -> dict[str, Path]:
    """Create and return the directories used to store raw JSON files."""
    raw_data_directory = project_root / "data" / "raw"
    directories = {
        "matches": raw_data_directory / "matches" / str(COMPETITION_ID),
        "events": raw_data_directory / "events",
        "lineups": raw_data_directory / "lineups",
        "three-sixty": raw_data_directory / "three-sixty",
    }

    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    return directories


def download_season_matches(session: requests.Session, destination: Path) -> list[dict]:
    """Download the season matches file unchanged, save it, and parse its JSON."""
    url = f"{BASE_URL}/matches/{COMPETITION_ID}/{SEASON_ID}.json"
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    # Write the response bytes directly so the source JSON is not reformatted.
    destination.write_bytes(response.content)
    print(f"Downloaded season matches file: {destination}")

    return json.loads(response.content)


def find_team_match_ids(matches: list[dict]) -> list[int]:
    """Return match IDs where Bayer Leverkusen is the home or away team."""
    match_ids = []

    for match in matches:
        home_team = match["home_team"]["home_team_name"]
        away_team = match["away_team"]["away_team_name"]

        if home_team == TEAM_NAME or away_team == TEAM_NAME:
            match_ids.append(match["match_id"])

    return match_ids


def download_match_file(
    session: requests.Session,
    data_type: str,
    match_id: int,
    destination_directory: Path,
    *,
    allow_missing: bool = False,
) -> str:
    """Download one match file, returning its downloaded/skipped status."""
    destination = destination_directory / f"{match_id}.json"

    if destination.exists():
        print(f"Skipped existing {data_type} file: {destination.name}")
        return "skipped"

    url = f"{BASE_URL}/{data_type}/{match_id}.json"
    response = session.get(url, timeout=REQUEST_TIMEOUT)

    if allow_missing and response.status_code == 404:
        print(f"360 file unavailable for match {match_id}")
        return "unavailable"

    response.raise_for_status()
    destination.write_bytes(response.content)
    print(f"Downloaded {data_type} file: {destination.name}")
    return "downloaded"


def print_summary(match_count: int, counts: dict[str, dict[str, int]]) -> None:
    """Print a concise summary of the files handled during this run."""
    print("\nDownload summary")
    print(f"Bayer Leverkusen matches identified: {match_count}")
    print(
        "Event files: "
        f"{counts['events']['downloaded']} downloaded, "
        f"{counts['events']['skipped']} skipped"
    )
    print(
        "Lineup files: "
        f"{counts['lineups']['downloaded']} downloaded, "
        f"{counts['lineups']['skipped']} skipped"
    )
    print(
        "360 files: "
        f"{counts['three-sixty']['downloaded']} downloaded, "
        f"{counts['three-sixty']['skipped']} skipped, "
        f"{counts['three-sixty']['unavailable']} unavailable"
    )


def main() -> None:
    """Download the season file and match-level files for Bayer Leverkusen."""
    project_root = Path(__file__).resolve().parents[1]
    directories = create_data_directories(project_root)
    matches_path = directories["matches"] / f"{SEASON_ID}.json"

    counts = {
        "events": {"downloaded": 0, "skipped": 0},
        "lineups": {"downloaded": 0, "skipped": 0},
        "three-sixty": {"downloaded": 0, "skipped": 0, "unavailable": 0},
    }

    with requests.Session() as session:
        matches = download_season_matches(session, matches_path)
        match_ids = find_team_match_ids(matches)

        for match_id in match_ids:
            event_status = download_match_file(
                session, "events", match_id, directories["events"]
            )
            counts["events"][event_status] += 1

            lineup_status = download_match_file(
                session, "lineups", match_id, directories["lineups"]
            )
            counts["lineups"][lineup_status] += 1

            three_sixty_status = download_match_file(
                session,
                "three-sixty",
                match_id,
                directories["three-sixty"],
                allow_missing=True,
            )
            counts["three-sixty"][three_sixty_status] += 1

    print_summary(len(match_ids), counts)


if __name__ == "__main__":
    main()

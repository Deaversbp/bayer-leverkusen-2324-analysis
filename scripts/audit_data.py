"""Run the pinned Phase 1/1B audit and write six derived diagnostic CSVs."""

import argparse
from pathlib import Path

import yaml

from leverkusen.data import loader
from leverkusen.data.observability import audit_season, write_audit_outputs


def main() -> None:
    """Read project constants, run the audit and report season coverage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = yaml.safe_load((root / "config/project.yaml").read_text(encoding="utf-8"))
    if project["statsbomb_revision"] != loader.STATSBOMB_REVISION:
        parser.error("Source revision changed after loader import; restart the process")
    if (project["competition_id"], project["season_id"]) != (
        loader.COMPETITION_ID,
        loader.SEASON_ID,
    ):
        parser.error("Project competition/season differs from the existing loader")
    matches, frames, attrition = audit_season(
        team_name=project["team_name"],
        pitch_length=project["coordinate_length"],
        pitch_width=project["coordinate_width"],
        progress=lambda done, total, match_id: print(
            f"Audited {done}/{total}: match {match_id}", flush=True
        ),
    )
    write_audit_outputs(matches, frames, attrition, root / "outputs/diagnostics")
    print(attrition.loc[attrition["scope"].eq("season")].to_string(index=False))
    print(f"360 load status: {matches['frames_load_status'].value_counts().to_dict()}")
    print("Wrote six phase1_*.csv diagnostic tables under outputs/diagnostics/")
    print(f"StatsBomb revision: {loader.STATSBOMB_REVISION}")


if __name__ == "__main__":
    main()

"""Run the locked Phase 2A geometry and write derived diagnostics only."""

import argparse
from pathlib import Path

import yaml

from leverkusen.data import loader
from leverkusen.spatial.diagnostics import run_geometry_diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = yaml.safe_load((root / "config/project.yaml").read_text(encoding="utf-8"))
    if project["statsbomb_revision"] != loader.STATSBOMB_REVISION:
        parser.error("Source revision changed after import; restart process")
    if (project["coordinate_length"], project["coordinate_width"]) != (120, 80):
        parser.error("Phase 2A contract requires native 120 x 80 coordinates")
    summaries = run_geometry_diagnostics(
        root / "outputs/diagnostics",
        team_name=project["team_name"],
        progress=lambda done, total, match_id, rows: print(
            f"Geometry {done}/{total}: match {match_id}, {rows} variant rows",
            flush=True,
        ),
    )
    print(summaries["inventory"].to_string(index=False))
    print(summaries["anomalies"].to_string(index=False))
    print("Wrote derived phase2a_*.csv diagnostics; no raw records persisted.")


if __name__ == "__main__":
    main()

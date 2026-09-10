"""Validate pinned team/coordinate semantics; never construct sequences."""

import argparse
from pathlib import Path

import pandas as pd

from leverkusen.data import loader
from leverkusen.data.semantic_diagnostics import inspect_event, run_semantic_diagnostics
from leverkusen.spatial.orientation import PHASE2C_STATUS, frame_semantics
from leverkusen.visualization.semantics_orientation import write_representatives


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="Refresh selected pinned frames using the prior complete audit manifest",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.figures_only:
        manifest = pd.read_csv(
            root / "outputs/diagnostics/phase2c_representative_frames.csv"
        )
        if (
            not manifest.statsbomb_revision.eq(loader.STATSBOMB_REVISION).all()
            or manifest.event_id.duplicated().any()
        ):
            raise ValueError(
                "Invalid or stale representative manifest; run the full audit"
            )
        matches = {m["match_id"]: m for m in loader.load_matches()}
        representatives = {}
        for mid, group in manifest.groupby("match_id"):
            events = {e["id"]: e for e in loader.load_events(int(mid))}
            frames = {f["event_uuid"]: f for f in loader.load_360(int(mid))}
            for record in group.to_dict("records"):
                event, frame, match = (
                    events[record["event_id"]],
                    frames[record["event_id"]],
                    matches[mid],
                )
                checked = frame_semantics(
                    event,
                    frame,
                    match,
                    source_revision=loader.STATSBOMB_REVISION,
                    related_team_conflict=bool(record["paired_label_conflict"]),
                )
                if checked["semantics_status"] != record["semantics_status"]:
                    raise ValueError("Semantic rule changed; rerun the complete audit")
                row = {**record, **inspect_event(event, frame, match, {})}
                for rule in record["selection_rules"].split(";"):
                    representatives[rule] = (frame, event, match, row)
        write_representatives(
            representatives, root / "outputs/diagnostics", root / "outputs/figures"
        )
        print(
            f"Refreshed {len(manifest)} figures from the existing full-audit manifest."
        )
        return
    table, representatives, summaries = run_semantic_diagnostics(
        root / "outputs/diagnostics"
    )
    manifest = write_representatives(
        representatives, root / "outputs/diagnostics", root / "outputs/figures"
    )
    print(summaries["normalization_validation"].to_string(index=False))
    print(
        f"Wrote {len(manifest)} representative native/normalized figures. Phase 2C: {PHASE2C_STATUS}."
    )
    return table, representatives, summaries


if __name__ == "__main__":
    main()

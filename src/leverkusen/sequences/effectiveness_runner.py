"""Bounded Phase 5C orchestration from two frozen analytical tables."""

import hashlib
from pathlib import Path

import pandas as pd

from leverkusen.sequences.effectiveness import CENTROID, SOURCE_COLUMNS, analyze, join_terminal_outcomes
from leverkusen.sequences.effectiveness_report import render_report
from leverkusen.visualization.sequence_effectiveness import write_figures


def run(root, progress=print):
    root = Path(root)
    directory = root / "outputs/analysis"
    paths = [directory / "phase4b_spatial_sequence_windows.csv", directory / "phase5a_anchor_outcomes.csv"]
    windows = pd.read_csv(paths[0], usecols=SOURCE_COLUMNS, low_memory=False)
    outcomes = pd.read_csv(paths[1])
    if windows.groupby("window_length").size().to_dict() != {2: 24273, 3: 19651} or len(outcomes) != 43737:
        raise ValueError("Frozen analytical source counts differ")
    if not windows.statsbomb_revision.eq("533862946a73608c134d18b78226b6371ce7173c").all():
        raise ValueError("Frozen source revision differs")
    if not windows[CENTROID].notna().eq(windows[f"{CENTROID}_status"].eq("ok")).all():
        raise ValueError("Frozen centroid availability differs")
    data = join_terminal_outcomes(windows, outcomes)
    progress("24,273/24,273 two-action and 19,651/19,651 three-action exact terminal joins; 0 unmatched")
    summary, sensitivity = analyze(data)
    products = {"phase5c_sequence_effectiveness_dataset.csv": data,
                "phase5c_motif_effectiveness_summary.csv": summary,
                "phase5c_sensitivity_summary.csv": sensitivity}
    serialized = {name: table.to_csv(index=False, lineterminator="\n").encode("utf-8") for name, table in products.items()}
    for name, content in serialized.items():
        path = directory / name
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"Existing Phase 5C core output differs: {name}")
    for name, content in serialized.items():
        (directory / name).write_bytes(content)
    hashes = [(path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
    figures = write_figures(summary, root / "outputs/figures")
    report = render_report(data, summary, sensitivity, hashes)
    (root / "report/phase5c_sequence_effectiveness.md").write_text(report, encoding="utf-8")
    progress(summary[summary.record_type.isin(["model", "contrast"])][["window_length", "outcome", "motif", "model_N",
             "odds_ratio", "or_ci_low", "or_ci_high", "model_status"]].to_string(index=False))
    progress(f"Wrote three core CSVs, {len(figures)} figures and report; no Phase 6 analysis")
    return products

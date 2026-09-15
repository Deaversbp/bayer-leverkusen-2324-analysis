"""Read two frozen tables and run only the bounded Phase 5B analysis."""

import hashlib
from pathlib import Path

import pandas as pd

from leverkusen.spatial.danger_analysis import METRICS, SOURCE_COLUMNS, analyze, join_to_outcomes
from leverkusen.spatial.danger_report import render_report
from leverkusen.visualization.spatial_danger import write_figures


def run(root, progress=print):
    root = Path(root)
    directory = root / "outputs/analysis"
    paths = [directory / "phase4a_progression_spatial_change.csv",
             directory / "phase5a_anchor_outcomes.csv"]
    source = pd.read_csv(paths[0], usecols=[*SOURCE_COLUMNS, "action_status", "statsbomb_revision",
                                          *[f"{metric}_status" for metric in METRICS]])
    outcomes = pd.read_csv(paths[1])
    if (len(source), len(outcomes)) != (30375, 43737):
        raise ValueError("Frozen source row counts differ")
    if source.groupby("action_type").size().to_dict() != {"Pass": 14848, "Carry": 15527}:
        raise ValueError("Frozen Pass/Carry population differs")
    if not source.action_status.eq("eligible").all() or not source.statsbomb_revision.eq(
            "533862946a73608c134d18b78226b6371ce7173c").all():
        raise ValueError("Frozen eligibility or provider revision differs")
    for metric in METRICS:
        if not source[metric].notna().eq(source[f"{metric}_status"].eq("ok")).all():
            raise ValueError(f"Frozen metric availability differs: {metric}")
    data = join_to_outcomes(source, outcomes)
    progress(f"{len(source):,} Phase 4A rows -> {len(data):,} exact TO outcomes; 0 unmatched")
    summary, sensitivity = analyze(data)
    products = {"phase5b_spatial_danger_dataset.csv": data,
                "phase5b_spatial_danger_summary.csv": summary,
                "phase5b_sensitivity_summary.csv": sensitivity}
    serialized = {name: table.to_csv(index=False, lineterminator="\n").encode("utf-8")
                  for name, table in products.items()}
    for name, content in serialized.items():
        path = directory / name
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"Existing Phase 5B core output differs: {name}")
    for name, content in serialized.items():
        (directory / name).write_bytes(content)
    input_hashes = [(path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
    figures = write_figures(summary, sensitivity, root / "outputs/figures")
    report = render_report(data, summary, sensitivity, input_hashes)
    (root / "report/phase5b_spatial_change_to_danger.md").write_text(report, encoding="utf-8")
    progress(summary[summary.record_type.eq("model")][["action_type", "spatial_metric", "outcome", "model", "N",
                                                     "coefficient", "odds_ratio_1sd", "or_1sd_ci_low", "or_1sd_ci_high", "model_status"]].to_string(index=False))
    progress(f"Wrote three core CSVs, {len(figures)} figures and report")
    return products

"""Phase 6A orchestration; frozen joins only, without upstream reconstruction."""

from pathlib import Path

import pandas as pd

from leverkusen.tactics.context import (
    ANCHOR_COLUMNS, analyze_contexts, analyze_motifs, construct_motifs, construct_transitions,
)


def load_inputs(root):
    root = Path(root)
    source = pd.read_csv(root / "outputs/analysis/phase5b_spatial_danger_dataset.csv")
    anchors = pd.read_csv(root / "outputs/diagnostics/phase3b_spatial_anchor_sequences.csv", usecols=ANCHOR_COLUMNS)
    if len(source) != 30375 or source.groupby("action_type").size().to_dict() != {"Pass": 14848, "Carry": 15527}:
        raise ValueError("Frozen Phase 5B population differs")
    if len(anchors) != 43737 or not anchors.statsbomb_revision.eq("533862946a73608c134d18b78226b6371ce7173c").all():
        raise ValueError("Frozen Phase 3B source differs")
    data, cuts = construct_transitions(source, anchors)
    windows = pd.read_csv(root / "outputs/analysis/phase4b_spatial_sequence_windows.csv",
                          usecols=["window_id", "match_id", "attacking_control_spell_id", "window_length", "anchor_0_event_id",
                                   "anchor_0_event_index", "anchor_2_event_id", "total_progression", "action_type_motif"])
    sequences = pd.read_csv(root / "outputs/analysis/phase5c_sequence_effectiveness_dataset.csv")
    motifs = construct_motifs(sequences, windows, anchors, cuts)
    if len(motifs) != 24273:
        raise ValueError("Frozen two-action population differs")
    return data, cuts, motifs


def run(root, progress=print):
    from leverkusen.tactics.context_report import render_report
    from leverkusen.visualization.defensive_context import write_figures

    root = Path(root)
    data, cuts, motifs = load_inputs(root)
    progress("30,375 exact FROM-context joins; 24,273 exact two-action START-context joins")
    summary, interactions = analyze_contexts(data, cuts)
    motif_summary = analyze_motifs(motifs)
    products = {"phase6a_defensive_context_dataset.csv": data, "phase6a_context_summary.csv": summary,
                "phase6a_context_interactions.csv": interactions, "phase6a_motif_context_summary.csv": motif_summary}
    directory = root / "outputs/analysis"
    serialized = {name: frame.to_csv(index=False, lineterminator="\n").encode("utf-8") for name, frame in products.items()}
    for name, content in serialized.items():
        path = directory / name
        if path.exists() and path.read_bytes() != content:
            raise ValueError(f"Existing Phase 6A core CSV differs: {name}")
    for name, content in serialized.items():
        (directory / name).write_bytes(content)
    figures = write_figures(data, summary, interactions, motif_summary, root / "outputs/figures")
    (root / "report/phase6a_defensive_context_analysis.md").write_text(render_report(data, summary, interactions, motif_summary, motifs), encoding="utf-8")
    progress(f"Wrote four core CSVs, {len(figures)} figures and Phase 6A report; no final synthesis")
    return products

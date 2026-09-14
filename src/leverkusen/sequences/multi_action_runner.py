"""Phase 4B runner: read frozen derived inputs, never fetch or inspect outcomes."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from leverkusen.sequences.multi_action import construct_windows
from leverkusen.sequences.spatial_readiness import sha256
from leverkusen.spatial.motif_analysis import analyze_windows


def run(root, *, build_only=False):
    root = Path(root)
    output = root / "outputs/analysis"
    b = json.loads((root / "outputs/diagnostics/phase3b_manifest.json").read_text())
    a = json.loads((output / "phase4a_manifest.json").read_text())
    source = json.loads((output / "phase4a_source_manifest.json").read_text())
    protected = {**b["input_sha256"], **b["output_sha256"], **source["protected_input_sha256"], **a["output_sha256"], **a["code_sha256"]}
    for path in ("outputs/diagnostics/phase3b_manifest.json", "outputs/analysis/phase4a_manifest.json", "outputs/analysis/phase4a_source_manifest.json"):
        protected[path] = sha256(root / path)
    if any(sha256(root / p) != digest for p, digest in protected.items()):
        raise ValueError("Protected Phase 2/3/4A artifacts or measurement code changed")
    anchors = pd.read_csv(root / "outputs/diagnostics/phase3b_spatial_anchor_sequences.csv")
    transitions = pd.read_csv(root / "outputs/diagnostics/phase3b_spatial_anchor_transitions.csv")
    eligible = pd.read_csv(output / "phase4a_progression_spatial_change.csv")
    if (len(anchors), len(transitions), eligible.action_type.value_counts().to_dict()) != (
        43737, 40638, {"Carry": 15527, "Pass": 14848}
    ):
        raise ValueError("Frozen Phase 3B/4A population differs")
    windows, audit = construct_windows(anchors, transitions, eligible)
    print("Candidate-chain reconciliation:", flush=True)
    print(audit.to_string(index=False), flush=True)
    window_path = output / "phase4b_spatial_sequence_windows.csv"
    windows.to_csv(window_path, index=False, lineterminator="\n")
    # Analyze persisted floats so independent CLI replays use the same representation.
    windows = pd.read_csv(window_path, low_memory=False)
    manifest = dict(statsbomb_revision=b["statsbomb_revision"], protected_input_sha256=protected,
        source_anchors=len(anchors), source_transitions=len(transitions),
        source_eligible_actions=eligible.action_type.value_counts().to_dict(),
        candidate_chain_audit=audit.to_dict("records"),
        output_sha256={str(window_path.relative_to(root)).replace("\\", "/"): sha256(window_path)})
    if build_only:
        (output / "phase4b_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return windows, audit
    del anchors, transitions, eligible
    tables = analyze_windows(windows)
    for name, table in tables.items():
        path = output / f"phase4b_{name}.csv"
        table.to_csv(path, index=False, lineterminator="\n")
        manifest["output_sha256"][str(path.relative_to(root)).replace("\\", "/")] = sha256(path)
    from leverkusen.visualization.multi_action import write_figures
    from leverkusen.sequences.multi_action_report import DECISION, render_report
    figures = write_figures(windows, tables, root / "outputs/figures")
    report_path = root / "report/phase4b_multi_action_spatial_sequences.md"
    report_path.write_text(render_report(windows, audit, tables), encoding="utf-8", newline="")
    for path in [*figures, report_path]:
        manifest["output_sha256"][str(path.relative_to(root)).replace("\\", "/")] = sha256(path)
    code = ["src/leverkusen/sequences/multi_action.py", "src/leverkusen/sequences/multi_action_runner.py",
            "src/leverkusen/sequences/multi_action_report.py", "src/leverkusen/spatial/motif_analysis.py",
            "src/leverkusen/visualization/multi_action.py", "scripts/multi_action_spatial_sequences.py"]
    manifest.update(code_sha256={p: sha256(root / p) for p in code}, generated_at_utc=datetime.now(timezone.utc).isoformat(), phase_decision=DECISION)
    if any(sha256(root / p) != digest for p, digest in protected.items()):
        raise ValueError("Protected artifact changed during Phase 4B")
    manifest["protected_inputs_unchanged"] = True
    (output / "phase4b_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return windows, audit, tables

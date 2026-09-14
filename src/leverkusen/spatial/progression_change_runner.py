"""Pinned-source construction and reproducible Phase 4A artifact orchestration."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

import pandas as pd

from leverkusen.data import loader
from leverkusen.sequences.spatial_readiness import fetch_pinned, record_hash, sha256
from leverkusen.spatial.progression_change import action_inventory, distribution, select_transitions, summarize

PREFIX = "phase4a_"


def sample_audit(data, selection):
    rows = []
    for reason, count in selection.selection_reason.value_counts().sort_index().items():
        rows.append(dict(section="selection", action_type="all_source_transitions", label=reason, N=count))
    for action, group in data.groupby("action_type", sort=True):
        for col in ("action_delta_x", "anchor_gap_seconds", "intervening_event_count", "events_from_previous_anchor"):
            rows.append(dict(section="distribution", action_type=action, label=col, N=len(group), **distribution(group[col], "value")))
        for (typ, team), count in group.assign(to_team=group.to_event_team_id.eq(904).map({True: "Leverkusen", False: "opponent"})).groupby(["to_event_type", "to_team"]).size().items():
            rows.append(dict(section="to_anchor", action_type=action, label=f"{typ}/{team}", N=count))
    return pd.DataFrame(rows)


def run(root, *, offline=False, build_only=False):
    root = Path(root)
    output = root / "outputs/analysis"
    output.mkdir(parents=True, exist_ok=True)
    phase3b = json.loads((root / "outputs/diagnostics/phase3b_manifest.json").read_text())
    # Protect every original Phase 3B output and all recorded upstream inputs.
    protected = {**phase3b["input_sha256"], **phase3b["output_sha256"]}
    if any(sha256(root / p) != digest for p, digest in protected.items()):
        raise ValueError("Locked Phase 2/3 artifacts no longer match the Phase 3B manifest")
    path = output / f"{PREFIX}progression_spatial_change.csv"
    source_path = output / f"{PREFIX}source_manifest.json"
    if offline:
        source = json.loads(source_path.read_text())
        if source["protected_input_sha256"] != protected or source["dataset_sha256"] != sha256(path):
            raise ValueError("Offline dataset provenance differs")
        data = pd.read_csv(path)
        audit = pd.read_csv(output / f"{PREFIX}sample_audit.csv")
        if source["audit_sha256"] != sha256(output / f"{PREFIX}sample_audit.csv"):
            raise ValueError("Offline sample audit provenance differs")
    else:
        context = pd.read_csv(root / "outputs/diagnostics/phase3b_event_context.csv")
        anchors = pd.read_csv(root / "outputs/diagnostics/phase3b_spatial_anchor_sequences.csv")
        transitions = pd.read_csv(root / "outputs/diagnostics/phase3b_spatial_anchor_transitions.csv")
        if (len(context), len(anchors), len(transitions)) != (86025, 43737, 40638):
            raise ValueError("Locked Phase 3B population differs")
        expected_sources = {s["match_id"]: s for s in phase3b["sources"]}

        def fetch(mid):
            events = fetch_pinned(loader.load_events, mid)
            if record_hash(events) != expected_sources[mid]["canonical_events_sha256"]:
                raise ValueError("Pinned raw action source differs from Phase 3B source")
            selected = context[context.match_id.eq(mid)]
            actions = action_inventory(selected, events)
            repeated = action_inventory(selected, events)
            if actions.to_csv(index=False) != repeated.to_csv(index=False):
                raise ValueError("Action construction is nondeterministic")
            return actions

        actions = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i, table in enumerate(pool.map(fetch, sorted(expected_sources)), 1):
                actions.append(table)
                print(f"Checked pinned action vectors: {i}/34 matches", flush=True)
        data, selection = select_transitions(transitions, anchors, pd.concat(actions, ignore_index=True))
        audit = sample_audit(data, selection)
        data.to_csv(path, index=False, lineterminator="\n")
        audit.to_csv(output / f"{PREFIX}sample_audit.csv", index=False, lineterminator="\n")
        source = dict(statsbomb_revision=loader.STATSBOMB_REVISION, protected_input_sha256=protected,
            action_sources=phase3b["sources"], dataset_sha256=sha256(path),
            audit_sha256=sha256(output / f"{PREFIX}sample_audit.csv"),
            source_transition_count=len(transitions), action_construction_replay="PASS")
        source_path.write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Subsequent execution always analyzes the same persisted float representation.
        data = pd.read_csv(path)
    print(data.action_type.value_counts().to_string(), flush=True)
    if build_only:
        return data
    tables = summarize(data)
    repeat = summarize(data.sample(frac=1, random_state=41).sort_values(["match_id", "from_event_index"]))
    for name, table in tables.items():
        text = table.to_csv(index=False, lineterminator="\n")
        if text != repeat[name].to_csv(index=False, lineterminator="\n"):
            raise ValueError(f"Summary determinism failure: {name}")
        (output / f"{PREFIX}{name}.csv").write_text(text, encoding="utf-8", newline="")
    from leverkusen.visualization.progression_change import write_figures
    from leverkusen.spatial.progression_change_report import report
    figures = write_figures(data, tables, root / "outputs/figures")
    report_path = root / "report/phase4a_progression_linked_spatial_change.md"
    report_path.write_text(report(data, audit, tables), encoding="utf-8", newline="")
    if any(sha256(root / p) != digest for p, digest in protected.items()):
        raise ValueError("Locked artifact changed during Phase 4A")
    code = ["src/leverkusen/spatial/progression_change.py", "src/leverkusen/spatial/progression_change_runner.py",
            "src/leverkusen/visualization/progression_change.py", "src/leverkusen/sequences/action_progression.py",
            "src/leverkusen/sequences/progression_diagnostics.py", "scripts/progression_spatial_change.py",
            "src/leverkusen/spatial/progression_change_report.py"]
    manifest = dict(statsbomb_revision=loader.STATSBOMB_REVISION,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        code_sha256={p: sha256(root / p) for p in code}, source_manifest_sha256=sha256(source_path),
        output_sha256={str(p.relative_to(root)).replace("\\", "/"): sha256(p)
            for p in [*sorted(output.glob(f"{PREFIX}*.csv")), *figures, report_path]},
        summary_replay="PASS", protected_inputs_unchanged=True,
        uncertainty="match-clustered CR1; 95% t interval with G-1 degrees of freedom; no p-values")
    (output / f"{PREFIX}manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return data, audit, tables

"""Offline Phase 3A-3 exploration of human review; never constructs episodes.

Run: python scripts/segmentation_calibration.py
The small OOXML reader avoids adding an Excel engine to the project's environment.
It reads literal measurements and archives presentation formulas without using caches.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import platform
import posixpath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = (
    ROOT / "data/calibration/Phase3A3_Segmentation_Calibration_Matrix.xlsx"
)
LABELS = ("CONTINUE", "POSSIBLE_RESET", "CLEAR_RESET")
PARTIAL_CONFIRMED = {"C15_M07", "C17_M04", "C17_M05"}
METRICS = (
    "retreat_from_peak",
    "largest_recent_negative_dx",
    "largest_recent_backward_magnitude",
    "negative_run_length",
    "nonpositive_run_length",
    "time_since_peak",
    "events_since_peak",
    "time_to_recovery",
    "events_to_recovery",
)
BOOLS = (
    "threshold_safe",
    "provider_peak_contaminated",
    "observed_recovery",
    "new_peak_afterward",
)
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
COLORS = ("#0072B2", "#D55E00", "#7B3294")
MARKERS = ("o", "^", "s")


def read_workbook(path):
    """Read rectangular literal-cell sheets; preserve blanks and sheet row numbers."""
    sheets = {}
    with ZipFile(path) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = [
                "".join(node.itertext())
                for node in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                    "m:si", NS
                )
            ]
        relationships = {
            node.attrib["Id"]: node.attrib["Target"]
            for node in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        }
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall(
            "m:sheets/m:sheet", NS
        ):
            target = relationships[sheet.attrib[f"{{{REL}}}id"]]
            member = (
                target.lstrip("/")
                if target.startswith("/")
                else posixpath.normpath(posixpath.join("xl", target))
            )
            rows = []
            for row in ET.fromstring(archive.read(member)).findall(
                "m:sheetData/m:row", NS
            ):
                values = {"workbook_row": int(row.attrib["r"])}
                for cell in row.findall("m:c", NS):
                    formula = cell.find("m:f", NS)
                    if formula is not None:
                        if sheet.attrib["name"] != "Calibration_Summary":
                            raise ValueError(
                                f"Formula unsupported: {sheet.attrib['name']} {cell.attrib['r']}"
                            )
                        # Presentation formulas are archived, never evaluated or
                        # consumed as calibration measurements.
                        values[re.sub(r"\d", "", cell.attrib["r"]) + "_formula"] = (
                            formula.text
                        )
                    value = cell.find("m:v", NS)
                    kind = cell.attrib.get("t", "n")
                    if kind == "inlineStr":
                        inline = cell.find("m:is", NS)
                        parsed = (
                            "".join(inline.itertext()) if inline is not None else None
                        )
                    elif value is None or value.text is None:
                        parsed = None
                    elif kind == "s":
                        parsed = strings[int(value.text)]
                    elif kind == "b":
                        parsed = bool(int(value.text))
                    elif kind == "n":
                        parsed = float(value.text)
                    elif kind == "e":
                        raise ValueError(
                            f"Excel error: {cell.attrib['r']}: {value.text}"
                        )
                    else:
                        parsed = value.text
                    values[re.sub(r"\d", "", cell.attrib["r"])] = parsed
                rows.append(values)
            # The summary is a presentation sheet with a title row. Preserve cell
            # coordinates there rather than inventing duplicate/blank column names.
            name = sheet.attrib["name"]
            if name == "Calibration_Summary":
                sheets[name] = pd.DataFrame(rows)
            else:
                header = rows[0].copy()
                header.pop("workbook_row")
                sheets[name] = pd.DataFrame(rows[1:]).rename(columns=header)
    return sheets


def boolean(value):
    if pd.isna(value) or value == "":
        return pd.NA
    if str(value).strip().lower() in {"true", "1", "1.0"}:
        return True
    if str(value).strip().lower() in {"false", "0", "0.0"}:
        return False
    raise ValueError(f"Unrecognized Boolean: {value!r}")


def prepare(matrix):
    data = matrix.copy()
    required = set(METRICS) - {"largest_recent_backward_magnitude"}
    required |= set(BOOLS) | {
        "candidate_id",
        "case_id",
        "human_label",
        "lock_status",
        "episode_local_retreat_override",
        "review_note",
    }
    if missing := required - set(data.columns):
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data.candidate_id.isna().any() or data.candidate_id.duplicated().any():
        raise ValueError("Candidate IDs must be present and unique")
    for column in BOOLS:
        data[column] = data[column].map(boolean).astype("boolean")
    for column in (*METRICS[:2], *METRICS[3:], "episode_local_retreat_override"):
        data[column] = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(data[column].dropna()).all():
            raise ValueError(f"Non-finite measurement: {column}")
    if data.largest_recent_negative_dx.gt(0).any():
        raise ValueError("Expected nonpositive largest_recent_negative_dx")
    for column in set(METRICS) - {
        "largest_recent_negative_dx",
        "largest_recent_backward_magnitude",
    }:
        if data[column].lt(0).any():
            raise ValueError(f"Negative value in {column}")
    data["largest_recent_backward_magnitude"] = data.largest_recent_negative_dx.abs()
    confirmed = (
        data.lock_status.eq("PARTIAL_LOCK")
        & data.candidate_id.isin(PARTIAL_CONFIRMED)
        & data.human_label.eq("POSSIBLE_RESET")
    )
    data["explicit_partial_confirmation"] = confirmed
    reasons = []
    for row in data.itertuples():
        why = []
        if pd.isna(row.threshold_safe) or not row.threshold_safe:
            why.append("threshold_safe_not_true")
        if row.human_label not in LABELS:
            why.append("not_a_reset_review_label")
        if row.lock_status != "LOCKED" and not row.explicit_partial_confirmation:
            why.append("not_locked_or_explicitly_confirmed")
        if pd.isna(row.provider_peak_contaminated) or row.provider_peak_contaminated:
            why.append("contaminated_or_unknown_provider_peak")
        reasons.append(";".join(why))
    data["exclusion_reasons"] = reasons
    data["primary_included"] = data.exclusion_reasons.eq("")
    data["measurement_scope"] = (
        "as_supplied_provider_parent_diagnostic_not_verified_episode_local"
    )
    # Do not fill missing runs with zero or missing recovery with failure.
    data["recovery_status"] = "unavailable"
    data.loc[data.observed_recovery.eq(False).fillna(False), "recovery_status"] = (
        "not_observed_censored"
    )
    data.loc[
        data.observed_recovery.isna() & data.retreat_from_peak.eq(0), "recovery_status"
    ] = "not_applicable_at_peak"
    data.loc[data.observed_recovery.eq(True).fillna(False), "recovery_status"] = (
        "observed"
    )
    data["observed_recovery_time"] = data.time_to_recovery.where(
        data.observed_recovery.eq(True)
    )
    data["observed_recovery_events"] = data.events_to_recovery.where(
        data.observed_recovery.eq(True)
    )
    return data


def descriptive(data, metrics=METRICS):
    rows = []
    for label in LABELS:
        group = data[data.human_label.eq(label)]
        for metric in metrics:
            values = group[metric].dropna()
            quantiles = values.quantile([0.1, 0.25, 0.5, 0.75, 0.9])
            rows.append(
                dict(
                    human_label=label,
                    metric=metric,
                    total_count=len(group),
                    count=len(values),
                    missing_count=int(group[metric].isna().sum()),
                    mean=values.mean(),
                    median=values.median(),
                    std=values.std(ddof=1),
                    minimum=values.min(),
                    p10=quantiles.loc[0.1],
                    p25=quantiles.loc[0.25],
                    p50=quantiles.loc[0.5],
                    p75=quantiles.loc[0.75],
                    p90=quantiles.loc[0.9],
                    maximum=values.max(),
                    iqr=quantiles.loc[0.75] - quantiles.loc[0.25],
                )
            )
    return pd.DataFrame(rows)


def overlap(data):
    rows = []
    for metric in METRICS:
        for a, b in itertools.combinations(LABELS, 2):
            x = data.loc[data.human_label.eq(a), metric].dropna()
            y = data.loc[data.human_label.eq(b), metric].dropna()
            for interval, bounds in [
                ("range", (0, 1)),
                ("p10_p90", (0.1, 0.9)),
                ("iqr", (0.25, 0.75)),
            ]:
                lo = max(x.quantile(bounds[0]), y.quantile(bounds[0]))
                hi = min(x.quantile(bounds[1]), y.quantile(bounds[1]))
                valid = len(x) > 0 and len(y) > 0
                intersects = valid and lo <= hi
                rows.append(
                    dict(
                        metric=metric,
                        class_a=a,
                        class_b=b,
                        interval=interval,
                        n_a=len(x),
                        n_b=len(y),
                        overlaps=intersects if valid else pd.NA,
                        overlap_low=lo if intersects else np.nan,
                        overlap_high=hi if intersects else np.nan,
                        overlap_width=max(0, hi - lo) if valid else np.nan,
                        a_in_overlap=int(x.between(lo, hi).sum()) if valid else np.nan,
                        b_in_overlap=int(y.between(lo, hi).sum()) if valid else np.nan,
                    )
                )
    return pd.DataFrame(rows)


def condition_counts(data, name, conditions):
    """Missing measurements are unknown, never false/zero or infinitely delayed."""
    known = pd.Series(True, index=data.index)
    selected = known.copy()
    for metric, operator, value in conditions:
        known &= data[metric].notna()
        compared = (
            data[metric].ge(value) if operator == ">=" else data[metric].le(value)
        )
        selected &= compared.fillna(False)
    rows = []
    for label in LABELS:
        group = data.human_label.eq(label)
        hit = group & known & selected
        rows.append(
            dict(
                diagnostic=name,
                human_label=label,
                total=int(group.sum()),
                evaluable=int((group & known).sum()),
                matched=int(hit.sum()),
                not_matched=int((group & known & ~selected).sum()),
                missing=int((group & ~known).sum()),
                candidate_ids=";".join(data.loc[hit, "candidate_id"]),
            )
        )
    return rows


def diagnostic_tables(data):
    sweeps = []
    grids = {
        "retreat_from_peak": [10, 20, 30, 40, 60],
        "time_since_peak": [3, 5, 10, 20],
        "nonpositive_run_length": [2, 3, 4],
        "observed_recovery_time": [1, 3, 5, 10, 30],
        "observed_recovery_events": [1, 3, 5, 10],
    }
    for metric, values in grids.items():
        op = "<=" if metric.startswith("observed_recovery") else ">="
        for value in values:
            sweeps.extend(
                condition_counts(data, f"{metric} {op} {value}", [(metric, op, value)])
            )
    combinations = []
    specs = [
        [("retreat_from_peak", ">=", 20)],
        [("retreat_from_peak", ">=", 20), ("time_since_peak", ">=", 5)],
        [("retreat_from_peak", ">=", 20), ("nonpositive_run_length", ">=", 3)],
        [("retreat_from_peak", ">=", 20), ("observed_recovery_time", ">=", 10)],
        [("time_since_peak", ">=", 5), ("observed_recovery", ">=", True)],
        [("time_since_peak", ">=", 5), ("observed_recovery", "<=", False)],
        [
            ("retreat_from_peak", ">=", 20),
            ("time_since_peak", ">=", 5),
            ("observed_recovery_time", ">=", 10),
        ],
    ]
    for spec in specs:
        name = " & ".join(f"{metric} {op} {value}" for metric, op, value in spec)
        combinations.extend(condition_counts(data, name, spec))
    correlations = []
    for label, group in [
        ("ALL", data),
        *[(label, data[data.human_label.eq(label)]) for label in LABELS],
    ]:
        for a, b in itertools.combinations(
            [m for m in METRICS if m != "largest_recent_negative_dx"], 2
        ):
            pair = group[[a, b]].dropna()
            rho = (
                pair.rank().corr().iloc[0, 1]
                if len(pair) > 1 and pair[a].nunique() > 1 and pair[b].nunique() > 1
                else np.nan
            )
            correlations.append(
                dict(
                    human_label=label,
                    metric_a=a,
                    metric_b=b,
                    paired_n=len(pair),
                    spearman=rho,
                )
            )
    return {
        "threshold_sweeps": pd.DataFrame(sweeps),
        "combinations": pd.DataFrame(combinations),
        "correlations": pd.DataFrame(correlations),
    }


def recovery_table(data):
    rows = []
    for label in LABELS:
        group = data[data.human_label.eq(label)]
        statuses = group.recovery_status.value_counts()
        observed = group[group.recovery_status.eq("observed")]
        rows.append(
            dict(
                human_label=label,
                total=len(group),
                observed=len(observed),
                not_observed_censored=int(statuses.get("not_observed_censored", 0)),
                not_applicable_at_peak=int(statuses.get("not_applicable_at_peak", 0)),
                unavailable=int(statuses.get("unavailable", 0)),
                observed_with_time=int(observed.time_to_recovery.notna().sum()),
                observed_with_event_count=int(
                    observed.events_to_recovery.notna().sum()
                ),
                recovery_time_median=observed.time_to_recovery.median(),
                recovery_events_median=observed.events_to_recovery.median(),
                new_peak_true=int(group.new_peak_afterward.eq(True).sum()),
                new_peak_false=int(group.new_peak_afterward.eq(False).sum()),
                new_peak_missing=int(group.new_peak_afterward.isna().sum()),
            )
        )
    return pd.DataFrame(rows)


def make_figures(data, output):
    output.mkdir(parents=True, exist_ok=True)
    pretty = {
        "retreat_from_peak": "Retreat from provider peak (StatsBomb x units)",
        "time_since_peak": "Time since provider peak (seconds)",
        "nonpositive_run_length": "Nonpositive run length (safe actions)",
        "observed_recovery_time": "Observed time to provider-peak recovery (seconds)",
    }
    paths = []
    for metric, title in pretty.items():
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
        for i, (label, color, marker) in enumerate(zip(LABELS, COLORS, MARKERS)):
            group = data[data.human_label.eq(label)].sort_values("candidate_id")
            values = group[metric].dropna().sort_values().to_numpy()
            jitter = np.random.default_rng(17 + i).uniform(-0.16, 0.16, len(values))
            axes[0].scatter(
                values,
                i + jitter,
                color=color,
                marker=marker,
                s=28,
                alpha=0.8,
                label=f"{label}: n={len(values)}, missing={len(group) - len(values)}",
            )
            if len(values):
                axes[0].plot(
                    [np.median(values)] * 2,
                    [i - 0.23, i + 0.23],
                    color="black",
                    linewidth=2,
                )
                axes[1].step(
                    np.r_[values[0], values],
                    np.r_[0, np.arange(1, len(values) + 1) / len(values)],
                    where="post",
                    color=color,
                    label=label,
                )
        axes[0].set_yticks(range(3), LABELS)
        axes[0].set_ylim(-0.5, 3)
        axes[0].set_xlabel(title)
        axes[0].set_title("Individual reviewed candidates; black tick = median")
        axes[0].legend(fontsize=7, loc="upper right")
        axes[1].set(
            xlabel=title,
            ylabel="Fraction of available class observations",
            ylim=(0, 1.02),
            title="Empirical cumulative distribution",
        )
        axes[1].legend(fontsize=8)
        for ax in axes:
            ax.grid(alpha=0.2)
        fig.suptitle(
            "Phase 3A-3 exploratory / as-supplied diagnostics / no method lock",
            fontsize=11,
        )
        path = output / f"phase3a3_{metric}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)
    for y in ("time_since_peak", "observed_recovery_time"):
        fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
        for label, color, marker in zip(LABELS, COLORS, MARKERS):
            group = data[data.human_label.eq(label)].dropna(
                subset=["retreat_from_peak", y]
            )
            ax.scatter(
                group.retreat_from_peak,
                group[y],
                c=color,
                marker=marker,
                label=f"{label} (n={len(group)})",
                alpha=0.8,
            )
            for row in group.itertuples():
                if row.candidate_id in {
                    "C09_M02",
                    "C09_M03",
                    "C05_M03",
                    "C05_M04",
                    "C22_M05",
                    "C08_M07",
                    "C04_M04",
                }:
                    ax.annotate(
                        row.candidate_id,
                        (row.retreat_from_peak, getattr(row, y)),
                        xytext=(4, 5),
                        textcoords="offset points",
                        fontsize=8,
                    )
        ax.set(
            xlabel=pretty["retreat_from_peak"],
            ylabel=pretty[y],
            title="Phase 3A-3 reviewed candidates / as-supplied diagnostics / no method lock",
        )
        ax.grid(alpha=0.2)
        ax.legend()
        path = output / f"phase3a3_retreat_vs_{y}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        paths.append(path)
    return paths


def markdown(table):
    """Small Markdown serializer, without optional tabulate dependency."""

    def fmt(value):
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.3f}".rstrip("0").rstrip(".")
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(map(str, table.columns)) + " |",
        "| " + " | ".join(["---"] * len(table.columns)) + " |",
    ]
    lines.extend(
        "| " + " | ".join(fmt(v) for v in row) + " |"
        for row in table.itertuples(index=False, name=None)
    )
    return "\n".join(lines)


def build_tables(sheets):
    audit = prepare(sheets["Calibration_Matrix"])
    primary = audit[audit.primary_included].copy()
    strict = primary[primary.lock_status.eq("LOCKED")]
    tables = {
        "inclusion_audit": audit,
        "primary_candidates": primary,
        "descriptive_statistics": descriptive(primary),
        "overlap": overlap(primary),
        "recovery": recovery_table(primary),
        "strict_locked_statistics": descriptive(strict),
        "strict_locked_recovery": recovery_table(strict),
        "overrides_excluded": audit[audit.episode_local_retreat_override.notna()],
        "hard_boundaries_reference": sheets["Hard_Boundaries"],
        "workbook_summary_reference": sheets["Calibration_Summary"],
        "workbook_provenance": sheets["Provenance"],
    }
    tables.update(diagnostic_tables(primary))
    tables["strict_locked_combinations"] = diagnostic_tables(strict)["combinations"]
    tables["case_label_summary"] = primary.groupby(
        ["case_id", "human_label"], as_index=False
    ).agg(
        candidates=("candidate_id", "size"),
        retreat_median=("retreat_from_peak", "median"),
        time_since_peak_median=("time_since_peak", "median"),
        recovery_time_median=("observed_recovery_time", "median"),
    )
    # Every case gets one median per label; this checks repeated-candidate influence,
    # without interpreting a case/parent as one episode or inventing reset cuts.
    case_medians = primary.groupby(["case_id", "human_label"], as_index=False)[
        list(METRICS)
    ].median()
    tables["case_median_statistics"] = descriptive(case_medians)
    first_clear = (
        primary[primary.human_label.eq("CLEAR_RESET")]
        .sort_values(["case_id", "candidate_event_index"])
        .groupby("case_id", as_index=False)
        .head(1)
    )
    tables["first_clear_per_case"] = first_clear
    case_ids = set(
        primary[primary.human_label.eq("CONTINUE")]
        .nlargest(6, "retreat_from_peak")
        .candidate_id
    )
    case_ids |= set(
        primary[primary.human_label.eq("CLEAR_RESET")]
        .nsmallest(4, "retreat_from_peak")
        .candidate_id
    )
    case_ids |= {
        "C04_M03",
        "C04_M04",
        "C05_M03",
        "C05_M04",
        "C09_M02",
        "C09_M03",
        "C22_M05",
        "C25_M07",
        "C07_M06",
        "C15_M07",
        "C17_M04",
        "C17_M05",
    }
    tables["overlap_cases"] = primary[primary.candidate_id.isin(case_ids)]
    pairs = []
    for a in primary[primary.human_label.eq("CONTINUE")].itertuples():
        for b in primary[primary.human_label.eq("CLEAR_RESET")].itertuples():
            if abs(a.retreat_from_peak - b.retreat_from_peak) <= 3:
                pairs.append(
                    dict(
                        continue_id=a.candidate_id,
                        clear_id=b.candidate_id,
                        retreat_difference=abs(
                            a.retreat_from_peak - b.retreat_from_peak
                        ),
                        continue_retreat=a.retreat_from_peak,
                        clear_retreat=b.retreat_from_peak,
                        continue_time=a.time_since_peak,
                        clear_time=b.time_since_peak,
                        continue_recovery=a.observed_recovery_time,
                        clear_recovery=b.observed_recovery_time,
                    )
                )
    tables["similar_retreat_pairs"] = pd.DataFrame(pairs)
    reconciliation = []
    for row in sheets["Calibration_Summary"].itertuples():
        if row.A in LABELS:
            group = primary[primary.human_label.eq(row.A)]
            for metric, column in [
                ("retreat_from_peak", "C"),
                ("largest_recent_backward_magnitude", "D"),
                ("time_since_peak", "E"),
                ("time_to_recovery", "F"),
            ]:
                cached = float(getattr(row, column))
                calculated = group[metric].mean()
                reconciliation.append(
                    dict(
                        human_label=row.A,
                        metric=metric,
                        nonmissing_count=int(group[metric].notna().sum()),
                        workbook_cached_mean=cached,
                        recomputed_mean=calculated,
                        difference=calculated - cached,
                        agrees=bool(np.isclose(cached, calculated)),
                    )
                )
    tables["summary_reconciliation"] = pd.DataFrame(reconciliation)
    # Cell-level inconsistency is retained for review, not silently repaired.
    tables["recovery_consistency_audit"] = audit.loc[
        (audit.observed_recovery.ne(True).fillna(True) & audit.time_to_recovery.notna())
        | (
            audit.observed_recovery.eq(True).fillna(False)
            & audit.time_to_recovery.isna()
        )
    ]
    return tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--output-root", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    sheets = read_workbook(args.workbook)
    tables = build_tables(sheets)
    diagnostics = args.output_root / "diagnostics"
    diagnostics.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(diagnostics / f"phase3a3_{name}.csv", index=False)
    paths = make_figures(tables["primary_candidates"], args.output_root / "figures")
    manifest = {
        "status": "EXPLORATORY / ANALYSIS ONLY / NO METHOD LOCK",
        "workbook": args.workbook.name,
        "sha256": hashlib.sha256(args.workbook.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "sheet_row_counts": {name: len(table) for name, table in sheets.items()},
        "primary_counts": tables["primary_candidates"]
        .human_label.value_counts()
        .to_dict(),
        "partial_confirmed_candidates": sorted(PARTIAL_CONFIRMED),
        "numeric_features": list(METRICS),
        "tables": [f"phase3a3_{name}.csv" for name in tables],
        "figures": [p.name for p in paths],
    }
    (diagnostics / "phase3a3_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    # Numeric appendix regenerates with the workbook. The interpretation is a
    # reviewed, source-specific report kept separately under report/.
    parts = [
        "# Phase 3A-3 generated numerical appendix",
        "Analysis only; no production cutoffs.",
        f"Workbook SHA-256: `{manifest['sha256']}`.",
    ]
    for name in ("descriptive_statistics", "overlap", "recovery", "combinations"):
        table = tables[name].drop(columns=["candidate_ids"], errors="ignore")
        parts.extend([f"## {name.replace('_', ' ').title()}", markdown(table)])
    (diagnostics / "phase3a3_numerical_appendix.md").write_text(
        "\n\n".join(parts) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "primary_counts": manifest["primary_counts"],
                "tables": len(tables),
                "figures": len(paths),
                "excluded": int((~tables["inclusion_audit"].primary_included).sum()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

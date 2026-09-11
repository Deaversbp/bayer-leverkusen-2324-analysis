"""Guard the human-review cohort, provenance, and missing-data semantics."""

from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from scripts.segmentation_calibration import (
    DEFAULT_WORKBOOK,
    METRICS,
    boolean,
    build_tables,
    condition_counts,
    descriptive,
    overlap,
    prepare,
    read_workbook,
)


@pytest.fixture(scope="module")
def tables():
    return build_tables(read_workbook(DEFAULT_WORKBOOK))


def test_authoritative_cohort_and_partial_locks(tables):
    data = tables["primary_candidates"]
    assert data.human_label.value_counts().to_dict() == {
        "CONTINUE": 62,
        "CLEAR_RESET": 18,
        "POSSIBLE_RESET": 11,
    }
    assert set(data.loc[data.explicit_partial_confirmation, "candidate_id"]) == {
        "C15_M07",
        "C17_M04",
        "C17_M05",
    }
    assert len(tables["inclusion_audit"]) == 127
    assert len(tables["hard_boundaries_reference"]) == 46
    assert data.threshold_safe.all()
    assert not data.provider_peak_contaminated.any()
    assert not data.candidate_id.isin(
        tables["hard_boundaries_reference"].candidate_id.dropna()
    ).any()


def test_filter_cannot_admit_deferred_hard_boundary_or_override(tables):
    base = tables["primary_candidates"].iloc[[0]].copy()
    rows = pd.concat([base] * 6, ignore_index=True)
    rows["candidate_id"] = [
        "deferred",
        "hard",
        "override",
        "partial",
        "unsafe",
        "unknown_peak",
    ]
    rows.loc[0, "lock_status"] = "DEFERRED"
    rows.loc[1, "human_label"] = "HARD_BOUNDARY"
    rows.loc[2, "provider_peak_contaminated"] = True
    rows.loc[2, "episode_local_retreat_override"] = 12
    rows.loc[3, "lock_status"] = "PARTIAL_LOCK"
    rows.loc[3, "human_label"] = "POSSIBLE_RESET"
    rows.loc[4, "threshold_safe"] = False
    rows.loc[5, "provider_peak_contaminated"] = pd.NA
    result = prepare(rows)
    assert not result.primary_included.any()
    assert result.exclusion_reasons.str.len().gt(0).all()
    overrides = tables["overrides_excluded"]
    assert overrides.episode_local_retreat_override.tolist() == [21, 14, 33]
    assert not overrides.primary_included.any()
    assert overrides.retreat_from_peak.tolist() == [41.2, 35.6, 43]


def test_recovery_censoring_and_correct_denominators(tables):
    data = tables["primary_candidates"].set_index("candidate_id")
    assert data.loc["C02_M01", "recovery_status"] == "not_applicable_at_peak"
    assert data.loc["C09_M03", "recovery_status"] == "not_observed_censored"
    assert pd.isna(data.loc["C09_M03", "observed_recovery_time"])
    recovery = tables["recovery"].set_index("human_label")
    assert recovery.observed.to_dict() == {
        "CONTINUE": 32,
        "POSSIBLE_RESET": 11,
        "CLEAR_RESET": 13,
    }
    stats = tables["descriptive_statistics"]
    mean = stats.loc[
        stats.human_label.eq("CONTINUE") & stats.metric.eq("time_to_recovery"), "mean"
    ].item()
    assert mean == pytest.approx(15.25178125)
    assert tables["summary_reconciliation"].agrees.eq(False).sum() == 2
    assert tables["recovery_consistency_audit"].empty


def test_missing_values_not_imputed_in_stats_or_conjunctions():
    frame = pd.DataFrame(
        {
            "human_label": ["CONTINUE"] * 3,
            "candidate_id": ["a", "b", "c"],
            "x": [0, 2, np.nan],
            "y": [3, np.nan, 4],
        }
    )
    stats = descriptive(frame, ["x"]).iloc[0]
    assert (
        stats["count"],
        stats.missing_count,
        stats["mean"],
        stats["std"],
        stats.iqr,
    ) == (
        2,
        1,
        1,
        pytest.approx(np.sqrt(2)),
        1,
    )
    counts = condition_counts(frame, "diagnostic", [("x", ">=", 0), ("y", ">=", 3)])[0]
    assert (
        counts["matched"],
        counts["evaluable"],
        counts["missing"],
        counts["candidate_ids"],
    ) == (1, 1, 2, "a")


def test_overlap_touching_endpoint_is_not_disjoint():
    frame = pd.DataFrame(
        {"human_label": ["CONTINUE", "CONTINUE", "POSSIBLE_RESET", "POSSIBLE_RESET"]}
    )
    for metric in METRICS:
        frame[metric] = [0, 2, 2, 4]
    result = overlap(frame)
    row = result.iloc[0]
    assert row.overlaps
    assert (row.overlap_low, row.overlap_high, row.overlap_width) == (2, 2, 0)
    assert (row.a_in_overlap, row.b_in_overlap) == (1, 1)


def test_boolean_strings_do_not_treat_false_as_truthy():
    assert boolean("False") is False
    assert boolean("0") is False
    assert boolean("TRUE") is True
    assert pd.isna(boolean(None))
    with pytest.raises(ValueError, match="Unrecognized Boolean"):
        boolean("maybe")


def test_formula_in_measurement_is_rejected(tmp_path):
    modified = tmp_path / "formula.xlsx"
    with ZipFile(DEFAULT_WORKBOOK) as source, ZipFile(modified, "w") as target:
        for name in source.namelist():
            content = source.read(name)
            if name == "xl/worksheets/sheet1.xml":
                content = content.replace(b"<x:v>", b"<x:f>1+1</x:f><x:v>", 1)
            target.writestr(name, content)
    with pytest.raises(ValueError, match="Formula unsupported: Calibration_Matrix"):
        read_workbook(modified)

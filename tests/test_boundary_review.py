"""Offline safeguards for a human-only, full-context review packet."""

import ast
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences import boundary_review as review
from leverkusen.sequences.progression_diagnostics import enrich_match
from leverkusen.sequences.readiness import KEY
from leverkusen.spatial.orientation import VALIDATED
from test_progression_diagnostics import example as example


def timeline(example):
    selected = enrich_match(*example, source_revision=STATSBOMB_REVISION)[1]
    return review.complete_timeline(selected, example[1])


def first_parent(example):
    return review.keyed(timeline(example), (1, 1, 1, 904)).reset_index(drop=True)


def test_case_selection_deterministic_and_prior_preference():
    records = []
    for i in range(1, 36):
        records.append(
            dict(zip(KEY, (1, 1, i, 904)))
            | {c: i % 2 == 0 for c, _, _ in review.CATEGORIES}
        )
    pool = pd.DataFrame(records)
    prior = {(1, 1, 32, 904)}
    expected = review.select_cases(pool, prior)
    actual = review.select_cases(pool.sample(frac=1, random_state=3), prior)
    pd.testing.assert_frame_equal(actual, expected)
    assert len(actual) == 28
    assert actual.possession_id.eq(32).any()
    assert not actual[KEY].duplicated().any()


def test_full_timeline_actor_and_missingness(example):
    match, events, frames = example
    events[0]["player"] = {"name": "Named actor"}
    frames[:] = [f for f in frames if f["event_uuid"] != events[1]["id"]]
    result = timeline(example)
    assert len(result) == len(events)
    assert result.event_index.tolist() == [e["index"] for e in events]
    assert result.player_name.iloc[0] == "Named actor"
    assert set(result.spatial_state_status) == {
        "validated_spatial_anchor",
        "linked_360_unsupported_semantics",
        "no_360_frame",
    }
    assert (
        result.loc[
            ~result.safe_action,
            ["start_x", "end_x", "delta_x", "running_peak_x", "retreat_from_peak"],
        ]
        .isna()
        .all()
        .all()
    )
    assert result.loc[~result.validated_anchor, "anchor_x"].isna().all()


def test_coordinates_runs_and_actual_time_gaps_reused(example):
    result = first_parent(example)
    extracted = enrich_match(*example, source_revision=STATSBOMB_REVISION)[1]
    expected = review.keyed(extracted, (1, 1, 1, 904)).reset_index(drop=True)
    pd.testing.assert_frame_equal(
        result[["start_x", "end_x", "delta_x", "anchor_x"]],
        expected[["start_x", "end_x", "delta_x", "anchor_x"]],
    )
    assert result[result.event_type.eq("Pressure")].anchor_x.iloc[0] == 105
    assert pd.isna(result.prior_event_gap_seconds.iloc[0])
    assert result.prior_event_gap_seconds.iloc[2] == 0.5
    negative = result[result.delta_x.lt(0)]
    assert negative.negative_run_length_so_far.tolist() == [1, 2, 3]
    assert negative.negative_run_id.nunique() == 1


def test_candidates_neutral_with_five_blank_fields(example):
    sheet, context = review.candidate_moments(first_parent(example), "C01")
    assert len(sheet) > 0 and len(context) > 0
    assert sheet[review.HUMAN_COLUMNS].eq("").all().all()
    assert sheet.candidate_reason.str.contains(
        "review sampling criterion", regex=False
    ).all()
    assert (
        not sheet.candidate_reason.str.lower()
        .str.contains("reset|boundary|attack start|attack end")
        .any()
    )
    assert sheet.candidate_id.is_unique


def test_context_never_crosses_parent_and_is_exact_rows(example):
    parent = first_parent(example)
    sheet, context = review.candidate_moments(parent, "C01")
    for candidate in sheet.itertuples(index=False):
        group = context[context.candidate_id.eq(candidate.candidate_id)]
        assert len(group) <= 7
        assert group[KEY].drop_duplicates().values.tolist() == [[1, 1, 1, 904]]
        pos = parent.index[parent.event_index.eq(candidate.candidate_event_index)][0]
        assert (
            group.event_index.tolist()
            == parent.iloc[max(0, pos - 3) : pos + 4].event_index.tolist()
        )
    with pytest.raises(ValueError, match="one provider parent"):
        review.candidate_moments(timeline(example), "C01")


def test_anchor_neighbors_strict_and_parent_bounded(example):
    parent = first_parent(example)
    first, last = parent.event_index.iloc[0], parent.event_index.iloc[-1]
    assert review.anchor_neighbors(parent, first)["before"] is None
    assert review.anchor_neighbors(parent, last)["after"] is None
    assert review.anchor_neighbors(parent, first)["candidate"] == first
    unsupported = parent.loc[~parent.validated_anchor, "event_index"].iloc[0]
    assert review.anchor_neighbors(parent, unsupported)["candidate"] is None
    with pytest.raises(ValueError, match="one complete provider parent"):
        review.anchor_neighbors(timeline(example), first)


def test_corner_at_120_preserved_without_classification(example):
    match, events, frames = example
    events[0]["location"] = [120, 20]
    events[0]["pass"]["type"] = {"name": "Corner"}
    frames[0]["freeze_frame"][0]["location"] = [120, 20]
    parent = first_parent(example)
    sheet, _ = review.candidate_moments(parent, "C01")
    corner = sheet[sheet.restart_context.eq("Corner")].iloc[0]
    assert parent.start_x.iloc[0] == 120
    assert corner.prior_peak_x == 120
    assert corner.retreat_from_peak == 62
    assert sheet[review.HUMAN_COLUMNS].eq("").all().all()


def test_shot_retains_later_same_parent_context_without_outcome_selection(example):
    match, events, frames = example
    event = events[1]
    event["type"]["name"] = "Shot"
    event["shot"] = {"outcome": {"name": "Goal"}, "statsbomb_xg": 0.99}
    first_sheet, first_context = review.candidate_moments(first_parent(example), "C01")
    shot_id = first_sheet.loc[
        first_sheet.candidate_event_type.eq("Shot"), "candidate_id"
    ].iloc[0]
    assert (
        first_context[first_context.candidate_id.eq(shot_id)]
        .event_index.gt(event["index"])
        .any()
    )
    event["shot"] = {"outcome": {"name": "Saved"}, "statsbomb_xg": 0.001}
    second_sheet, _ = review.candidate_moments(first_parent(example), "C01")
    pd.testing.assert_frame_equal(first_sheet, second_sheet)
    assert first_sheet[review.HUMAN_COLUMNS].eq("").all().all()
    assert "is_goal" not in timeline(example)


def test_recovery_uses_observed_action_start_references(example):
    sheet, _ = review.candidate_moments(first_parent(example), "C01")
    observed = sheet[sheet.observed_recovery.eq(True)]
    assert len(observed)
    assert observed.time_to_recovery.ge(0).all()
    assert observed.events_to_recovery.gt(0).all()
    no_action = sheet[sheet.current_x_reference.eq("unavailable_no_safe_action_vector")]
    assert (
        no_action[["attacking_x", "retreat_from_peak", "time_to_recovery"]]
        .isna()
        .all()
        .all()
    )


def test_normalized_snapshot_uses_locked_rotation_and_no_named_points(example):
    match, events, frames = example
    parent = first_parent(example)
    row = parent[parent.event_type.eq("Pressure")].iloc[0]
    event = next(e for e in events if e["index"] == row.event_index)
    frame = next(f for f in frames if f["event_uuid"] == event["id"])
    points, polygon, end = review.normalized_snapshot(event, frame, match, row)
    assert points[0]["x_attacking"] == 105 and points[0]["y_attacking"] == 60
    assert points[0]["side"] == "opponent" and "player_name" not in points[0]
    assert end["vector_end_x"] is None
    row["semantics_status"] = "unsupported_event_type"
    with pytest.raises(ValueError, match="Unsupported"):
        review.normalized_snapshot(event, frame, match, row)


def test_geometry_keeps_native_support_and_metric_statuses(example):
    match, events, frames = example
    row = first_parent(example).iloc[0]
    result = review.snapshot_geometry(events[0], frames[0], 0, match, row)
    assert len(result) == 6
    assert {
        "visible_area_fraction",
        "selected_subset",
        "goalkeeper_policy",
        "actor_status",
        "n_valid_points_used",
        "frame_oob",
        "frame_coincident",
        "centroid_x",
        "centroid_x_attacking",
    } <= set(result.columns)
    assert result.semantics_status.eq(VALIDATED).all()
    assert not result.mean_nearest_neighbor_distance_d_primary_eligible.any()
    assert result.mean_nearest_neighbor_distance.isna().all()


def test_raw_inputs_unchanged_by_review_and_geometry(example):
    before = deepcopy(example)
    parent = first_parent(example)
    review.candidate_moments(parent, "C01")
    review.normalized_snapshot(example[1][0], example[2][0], example[0], parent.iloc[0])
    review.snapshot_geometry(
        example[1][0], example[2][0], 0, example[0], parent.iloc[0]
    )
    assert example == before


def test_blank_sheet_refuses_prefill_and_preserves_human_annotations(example, tmp_path):
    sheet, _ = review.candidate_moments(first_parent(example), "C01")
    path = tmp_path / "review.csv"
    review.write_blank_sheet(sheet, path)
    assert pd.read_csv(path)[review.HUMAN_COLUMNS].isna().all().all()
    changed = sheet.copy()
    changed.loc[0, "review_label"] = "CONTINUE"
    with pytest.raises(ValueError, match="leave all human fields blank"):
        review.write_blank_sheet(changed, tmp_path / "new.csv")
    changed.to_csv(path, index=False)
    original = path.read_bytes()
    with pytest.raises(ValueError, match="human annotations"):
        review.write_blank_sheet(sheet, path)
    assert path.read_bytes() == original


def test_no_interpolation_or_machine_learning_dependencies():
    tree = ast.parse(Path(review.__file__).read_text(encoding="utf-8"))
    imports = [
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    imports += [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert not any(
        name.startswith(("sklearn", "scipy.cluster", "hdbscan", "ruptures", "hmmlearn"))
        for name in imports
    )
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    assert not set(calls) & {
        "interpolate",
        "resample",
        "ffill",
        "bfill",
        "fit",
        "fit_predict",
    }


def test_unsupported_candidate_slot_preserves_event_context_without_coordinates(
    example,
):
    parent = first_parent(example)
    r = parent[~parent.validated_anchor].iloc[0]
    candidates = pd.DataFrame(
        [
            {
                **{k: r[k] for k in KEY},
                "case_id": "C01",
                "candidate_id": "C01_M01",
                "candidate_event_index": r.event_index,
            }
        ]
    )
    parent["case_id"] = "C01"
    match, events, frames = example
    sources = {
        1: (
            match,
            {e["index"]: e for e in events},
            {f["event_uuid"]: (i, f) for i, f in enumerate(frames)},
        )
    }
    tables = review.build_snapshot_tables(candidates, parent, sources)
    slot = tables["spatial_slots"].loc[lambda t: t.slot.eq("candidate")].iloc[0]
    assert not slot.spatial_state_available
    assert slot.event_type == "Ball Receipt*"
    assert slot.event_id == r.event_id
    assert slot.spatial_state_status == "linked_360_unsupported_semantics"
    assert pd.isna(slot.anchor_x)
    assert not tables["spatial_points"].slot_id.eq(slot.slot_id).any()

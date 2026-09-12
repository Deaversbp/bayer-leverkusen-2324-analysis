"""Human boundary authority, episode state, missingness and input immutability."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.episode_local_reconstruction import (
    INPUT,
    SOURCE_FILES,
    build_episode_map,
    progression,
    read_sources,
    reconstruct,
)


@pytest.fixture(scope="module")
def tables():
    before = {
        name: hashlib.sha256((INPUT / name).read_bytes()).hexdigest()
        for name in SOURCE_FILES
    }
    result = reconstruct(*read_sources())
    assert before == {
        name: hashlib.sha256((INPUT / name).read_bytes()).hexdigest()
        for name in SOURCE_FILES
    }
    return result


def synthetic(actions):
    rows = []
    for i, (start, end, context, event_type) in enumerate(actions):
        rows.append(
            dict(
                case_id="T01",
                event_index=i + 1,
                period_seconds=float(i),
                start_x=start,
                end_x=end,
                delta_x=end - start,
                safe_action=event_type in {"Pass", "Carry"},
                event_type=event_type,
                event_team_id=904,
                provider_context=context,
                restart_context=np.nan,
            )
        )
    return pd.DataFrame(rows)


def test_hard_boundary_resets_peak_and_starts_before_spatial_anchor(tables):
    events = tables["episode_event_membership"].set_index(["case_id", "event_index"])
    first = events.loc[("C13", 353)]
    assert first.hard_boundary_state_reset
    assert first.episode_running_peak_x == pytest.approx(74.3)
    assert first.episode_retreat_from_peak == pytest.approx(0.4)
    assert events.loc[("C13", 344), "episode_id"] != first.episode_id
    regain = events.loc[("C25", 1264)]
    assert regain.episode_start_event_index == 1264
    assert pd.isna(regain.episode_running_peak_x)  # no filled spatial observation
    assert events.loc[("C25", 1269), "episode_running_peak_x"] == pytest.approx(83)
    assert events.loc[("C25", 1269), "episode_elapsed_seconds"] > 0


def test_one_split_per_excursion_and_retrospective_onset(tables):
    episodes = tables["reviewed_episode_map"]
    resets = tables["reset_excursion_diagnostics"]
    assert len(resets) == 12
    assert resets.reviewed_split_count.eq(1).all()
    assert episodes.start_reason.eq("CLEAR_RESET").sum() == 12
    events = tables["episode_event_membership"].set_index(["case_id", "event_index"])
    assert (
        events.loc[("C10", 2416), "episode_id"]
        == events.loc[("C10", 2422), "episode_id"]
    )
    assert (
        events.loc[("C10", 2414), "episode_id"]
        != events.loc[("C10", 2416), "episode_id"]
    )
    r = resets.set_index("reset_excursion_id").loc["C10_R01"]
    assert (r.onset_event, r.confirmation_event) == (2416, 2420)
    assert (
        r.onset_pre_split_retreat_from_peak != r.confirmation_episode_retreat_from_peak
    )
    for reset_id in ["C09_R01", "C11_R01"]:
        snapshot = resets.set_index("reset_excursion_id").loc[reset_id]
        assert not snapshot.onset_pre_split_available
        assert pd.isna(snapshot.onset_pre_split_retreat_from_peak)


def test_cancelled_warnings_do_not_split(tables):
    candidates = tables["episode_local_candidate_diagnostics"].set_index("candidate_id")
    assert (
        candidates.loc["C16_M05", "episode_id"]
        == candidates.loc["C16_M07", "episode_id"]
    )
    assert candidates.loc["C22_M05", "human_label"] == "CONTINUE"
    assert (
        candidates.loc["C22_M05", "warning_resolution"]
        == "cancelled_or_retained_continue"
    )
    assert (
        candidates.loc["C25_M06", "episode_id"]
        == candidates.loc["C25_M08", "episode_id"]
    )
    assert len(tables["reviewed_episode_map"].query("case_id == 'C22'")) == 1


def test_backward_opening_restart_is_context_not_reset_evidence(tables):
    kickoff = (
        tables["episode_event_membership"]
        .query("case_id == 'C24' and event_index == 1937")
        .iloc[0]
    )
    assert kickoff.episode_recorded_delta_x == pytest.approx(-19.8)
    assert kickoff.episode_running_peak_x == pytest.approx(41.2)
    assert kickoff.episode_largest_recent_negative_dx == 0
    assert kickoff.episode_negative_run_length == 0
    assert not kickoff.episode_trusted_progression_action
    assert not tables["reset_excursion_diagnostics"].case_id.eq("C24").any()


def test_failed_endpoint_and_relocation_not_deliberate_backward_vector(tables):
    source = synthetic(
        [
            (80, 100, "", "Pass"),
            (100, 115, "pass.outcome:Incomplete", "Pass"),
            (np.nan, np.nan, "type:Clearance", "Clearance"),
            (90, 95, "", "Pass"),
        ]
    )
    result = progression(source)
    assert pd.isna(result.iloc[1].episode_running_peak_x)
    assert result.iloc[-1].episode_running_peak_x == 100  # excludes failed endpoint 115
    assert result.iloc[-1].episode_retreat_from_peak == 5
    assert result.iloc[-1].episode_largest_recent_negative_dx == 0
    assert result.iloc[-1].episode_negative_run_length == 0
    assert result.iloc[-1].episode_relocation_not_backward_progression
    assert result.iloc[-1].episode_drawdown_relocation_affected
    c20 = (
        tables["episode_local_candidate_diagnostics"]
        .query("candidate_id == 'C20_M01'")
        .iloc[0]
    )
    assert c20.episode_recorded_delta_x > 0
    assert not c20.episode_calibration_ready
    assert pd.isna(c20.episode_retreat_from_peak)


def test_no_episode_exclusions_and_opponent_context(tables):
    episodes = tables["reviewed_episode_map"]
    assert set(episodes.loc[episodes.excluded, "case_id"]) == {"C27", "C28"}
    events = tables["episode_event_membership"]
    assert events.loc[events.case_id.isin(["C27", "C28"]), "episode_id"].isna().all()
    assert not events.loc[
        events.event_team_id.ne(904), "is_leverkusen_attacking_action"
    ].any()
    assert (
        events.loc[
            events.case_id.eq("C13") & events.event_index.between(346, 352),
            "episode_id",
        ]
        .isna()
        .all()
    )


def test_recovery_cannot_cross_hard_boundary_and_missing_not_zero():
    source = synthetic(
        [(90, 100, "", "Pass"), (100, 80, "", "Pass"), (80, 105, "", "Pass")]
    )
    uncut = progression(source)
    assert uncut.iloc[1].episode_observed_recovery
    cut = progression(source.iloc[:2])
    assert cut.iloc[1].episode_observed_recovery == False  # noqa: E712
    assert pd.isna(cut.iloc[1].episode_time_to_recovery)
    assert pd.isna(cut.iloc[1].episode_events_to_recovery)
    assert cut.iloc[1].episode_recovery_status == "censored_at_episode_observation_end"
    assert cut.iloc[1].episode_recovery_censor_event == 2
    assert cut.iloc[0].episode_recovery_status == "not_applicable_at_peak"


def test_equal_peak_and_higher_peak_recovery_definitions():
    source = synthetic(
        [(90, 100, "", "Pass"), (100, 80, "", "Pass"), (80, 100, "", "Pass")]
    )
    result = progression(source)
    assert result.iloc[1].episode_observed_recovery
    assert result.iloc[1].episode_time_to_recovery == 1
    assert not result.iloc[1].episode_new_peak_afterward
    source.loc[2, "end_x"] = 101
    assert progression(source).iloc[1].episode_new_peak_afterward


def test_uncertain_onsets_remain_unassigned_and_ineligible(tables):
    reset = tables["reset_excursion_diagnostics"]
    assert set(reset.loc[reset.onset_event.isna(), "reset_excursion_id"]) == {
        "C11_R02",
        "C12_R02",
        "C16_R01",
    }
    candidates = tables["episode_local_candidate_diagnostics"].set_index("candidate_id")
    for cid in [
        "C11_M07",
        "C12_M06",
        "C12_M07",
        "C16_M08",
        "C15_M07",
        "C17_M04",
        "C17_M05",
    ]:
        assert not candidates.loc[cid, "episode_calibration_ready"]
    events = tables["episode_event_membership"]
    assert (
        events.loc[
            events.case_id.eq("C16") & events.event_index.between(545, 573),
            "episode_id",
        ]
        .isna()
        .all()
    )
    bridge = reset.set_index("reset_excursion_id").loc["C16_R01"]
    assert bridge.confirmation_unsplit_reference_retreat_from_peak == pytest.approx(
        32.8
    )
    assert bridge.confirmation_episode_retreat_from_peak == pytest.approx(5.4)


def test_local_overrides_and_new_suitability_not_old_safe_flag(tables):
    candidates = tables["episode_local_candidate_diagnostics"].set_index("candidate_id")
    assert candidates.loc["C14_M09", "episode_retreat_from_peak"] == pytest.approx(21.1)
    assert candidates.loc["C16_M06", "episode_retreat_from_peak"] == pytest.approx(14.1)
    assert not candidates.loc["C14_M09", "workbook_threshold_safe"]
    assert candidates.loc["C14_M09", "episode_calibration_ready"]
    assert candidates.loc["C20_M01", "workbook_threshold_safe"]
    assert not candidates.loc["C20_M01", "episode_calibration_ready"]


def test_conditional_recovery_summary_uses_available_denominator(tables):
    candidates = tables["episode_local_candidate_diagnostics"]
    for row in tables["episode_local_recovery_summary"].itertuples():
        group = candidates[
            candidates.episode_calibration_ready
            & candidates.human_label.eq(row.human_label)
        ]
        times = group.episode_time_to_recovery.dropna()
        assert row.observed_time_count == len(times)
        assert row.conditional_mean_recovery_seconds == pytest.approx(
            times.sum() / len(times)
        )


def test_all_source_events_candidates_and_workbook_preserved(tables):
    assert len(tables["episode_event_membership"]) == 1960
    assert len(tables["episode_local_candidate_diagnostics"]) == 181
    workbook = INPUT / "Phase3A3_Segmentation_Calibration_Matrix.xlsx"
    assert (
        hashlib.sha256(workbook.read_bytes()).hexdigest()
        == "683a232989f9956c788815299b9f9c4577ad91007c219e0a50af5142ec7b4006"
    )
    snapshot = pd.read_csv(INPUT / "phase3a3_reviewed_event_source.csv")
    original_path = Path("outputs/diagnostics/phase3a2_timelines.csv")
    if original_path.exists():
        pd.testing.assert_frame_equal(pd.read_csv(original_path), snapshot)


def test_map_is_independent_of_candidate_labels_and_numeric_thresholds():
    events, candidates, parents, boundaries, workbook = read_sources()
    before = build_episode_map(parents, boundaries)
    events["end_x"] = 999
    candidates["retreat_from_peak"] = 999
    workbook["Calibration_Matrix"]["human_label"] = "CONTINUE"
    pd.testing.assert_frame_equal(before, build_episode_map(parents, boundaries))

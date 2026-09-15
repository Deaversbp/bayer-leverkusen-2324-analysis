"""Twelve focused Phase 5B join, scope, reporting and estimation checks."""

import numpy as np
import pandas as pd
import pytest
from scipy.special import logit
from scipy.stats import t as student_t

from leverkusen.models.clustered_logistic import fit_logistic, standardize
from leverkusen.spatial.danger_analysis import (
    FLAGS, METRICS, OUTCOMES, PRIMARY, SOURCE_COLUMNS, analyze,
    join_to_outcomes, select_scope,
)
from leverkusen.spatial.progression_change import starting_third


@pytest.fixture
def inputs():
    rng = np.random.default_rng(31)
    n = 320
    transitions = pd.DataFrame({c: np.zeros(n) for c in SOURCE_COLUMNS})
    transitions["match_id"] = np.repeat(np.arange(1, 9), 40)
    transitions["attacking_control_spell_id"] = [f"s{i // 5}" for i in range(n)]
    transitions["from_event_id"] = [f"f{i}" for i in range(n)]
    transitions["to_event_id"] = [f"t{i}" for i in range(n)]
    transitions["from_event_index"] = np.arange(n) * 2
    transitions["to_event_index"] = np.arange(n) * 2 + 1
    transitions["action_type"] = np.tile(["Pass", "Carry"], n // 2)
    transitions["to_event_type"] = "Pass"
    transitions["action_start_x"] = rng.uniform(0, 120, n)
    transitions["action_delta_x"] = rng.normal(0, 8, n)
    transitions["anchor_gap_seconds"] = rng.uniform(0, 8, n)
    transitions["starting_third"] = starting_third(transitions.action_start_x)
    for col in (*METRICS, "delta_opp_visible_player_count"):
        transitions[col] = rng.normal(0, 2, n)
    for col in FLAGS:
        transitions[col] = False
    outcomes = transitions[["match_id", "attacking_control_spell_id", "to_event_id",
                            "to_event_index", "to_event_type"]].rename(columns={
                                "to_event_id": "reference_event_id", "to_event_index": "reference_event_index",
                                "to_event_type": "reference_event_type"})
    outcomes["reference_is_box_entry"] = (np.arange(n) % 10 == 0).astype(int)
    outcomes["reference_is_shot"] = (np.arange(n) % 15 == 0).astype(int)
    for col in OUTCOMES:
        outcomes[col] = rng.binomial(1, .25, n) * (.2 if col.startswith("future_xg") else 1)
    return transitions, outcomes


def test_exact_to_join_and_context_guards(inputs):
    transitions, outcomes = inputs
    data = join_to_outcomes(transitions, outcomes.iloc[::-1])
    assert len(data) == len(transitions)
    assert data.box_entry_within_10s.tolist() == outcomes.box_entry_within_10s.tolist()
    with pytest.raises(ValueError, match="Missing exact TO"):
        join_to_outcomes(transitions, outcomes.iloc[1:])
    changed = outcomes.copy()
    changed.loc[0, "attacking_control_spell_id"] = "different"
    with pytest.raises(ValueError, match="TO context"):
        join_to_outcomes(transitions, changed)
    with pytest.raises(ValueError, match="Duplicate Phase 5A"):
        join_to_outcomes(transitions, pd.concat([outcomes, outcomes.iloc[:1]]))


def test_from_outcome_is_never_used(inputs):
    transitions, outcomes = inputs
    from_outcomes = outcomes.copy()
    from_outcomes["reference_event_id"] = transitions.from_event_id
    from_outcomes[OUTCOMES] = 99
    expected = join_to_outcomes(transitions, outcomes)
    actual = join_to_outcomes(transitions, pd.concat([outcomes, from_outcomes]))
    pd.testing.assert_frame_equal(actual, expected)


def test_pass_carry_separate_and_primary_is_10_seconds(inputs):
    data = join_to_outcomes(*inputs)
    summary, sensitivity = analyze(data)
    models = summary[summary.record_type.eq("model")]
    assert set(models.action_type) == {"Pass", "Carry"}
    assert models.N.eq(160).all() and models.horizon.eq(10).all()
    assert set(sensitivity.horizon) == {5, 10, 15}
    assert models[models.outcome.eq("shot")].spatial_metric.eq(PRIMARY).all()
    later_xg = sensitivity[sensitivity.outcome.eq("future_xg")]
    assert len(later_xg) == 8 and later_xg.scope.eq("exclude_immediate").all()
    assert later_xg.N.sum() == data.reference_is_shot.eq(0).sum()


def test_immediate_exclusion_is_outcome_specific(inputs):
    data = join_to_outcomes(*inputs)
    box = select_scope(data, "exclude_immediate", "box_entry_within_10s")
    shot = select_scope(data, "exclude_immediate", "shot_within_10s")
    xg = select_scope(data, "exclude_immediate", "future_xg_10s")
    assert box.reference_is_box_entry.eq(0).all()
    assert shot.reference_is_shot.eq(0).all() and len(shot) == len(xg)
    assert len(box) != len(shot) and len(select_scope(data, "all", "shot_within_10s")) == len(data)


def test_gap_5_is_inclusive(inputs):
    data = join_to_outcomes(*inputs).iloc[:3].copy()
    data["anchor_gap_seconds"] = [4.999, 5, 5.001]
    assert len(select_scope(data, "gap_le_5", "box_entry_within_10s")) == 2


def test_gap_3_is_inclusive(inputs):
    data = join_to_outcomes(*inputs).iloc[:3].copy()
    data["anchor_gap_seconds"] = [2.999, 3, 3.001]
    assert len(select_scope(data, "gap_le_3", "box_entry_within_10s")) == 2


def test_sd_is_sample_sd_and_raw_values_unchanged(inputs):
    data = join_to_outcomes(*inputs)
    before = data[PRIMARY].copy()
    z, mean, sd = standardize(before)
    assert mean == pytest.approx(before.mean()) and sd == pytest.approx(before.std(ddof=1))
    assert np.mean(z) == pytest.approx(0, abs=1e-12)
    assert np.std(z, ddof=1) == pytest.approx(1)
    fit = fit_logistic(data, "box_entry_within_10s", PRIMARY, reporting_sd=3)
    assert fit["odds_ratio_1sd"] == pytest.approx(np.exp(3 * fit["coefficient"]))
    pd.testing.assert_series_equal(before, data[PRIMARY])


def test_starting_thirds_are_inherited(inputs):
    assert starting_third(pd.Series([0, 39.9, 40, 79.9, 80, 120])).tolist() == [
        "defensive_third", "defensive_third", "middle_third", "middle_third", "attacking_third", "attacking_third"]
    transitions, outcomes = inputs
    transitions.loc[0, "starting_third"] = "wrong"
    with pytest.raises(ValueError, match="starting third"):
        join_to_outcomes(transitions, outcomes)


def test_no_motif_or_composite_fields_required_or_exported(inputs):
    transitions, outcomes = inputs
    baseline = join_to_outcomes(transitions, outcomes)
    transitions["motif"] = "irrelevant"
    transitions["success"] = 42
    outcomes["danger_score"] = 999
    pd.testing.assert_frame_equal(join_to_outcomes(transitions, outcomes), baseline)
    assert not any(c in baseline for c in ("motif", "success", "danger_score"))


def test_whole_frame_flags_and_unknowns_use_both_endpoints(inputs):
    data = join_to_outcomes(*inputs).iloc[:4].copy()
    data.loc[0, "from_frame_oob"] = True
    data.loc[1, "to_frame_oob_unknown"] = True
    data.loc[2, "from_frame_coincident_unknown"] = True
    data.loc[3, "to_frame_coincident"] = True
    assert len(select_scope(data, "exclude_oob", "box_entry_within_10s")) == 2
    assert len(select_scope(data, "exclude_coincidence", "box_entry_within_10s")) == 2


def test_logistic_against_closed_form_log_odds_and_cluster_contrast():
    rows = []
    counts = [(2, 4), (4, 8), (3, 5), (5, 7)]
    for match, (a, b) in enumerate(counts):
        for x, successes in ((0, a), (1, b)):
            rows.extend({"match_id": match, "x": x, "y": int(i < successes)} for i in range(10))
    data = pd.DataFrame(rows)
    fit = fit_logistic(data, "y", "x")
    p0, p1 = np.mean([a for a, _ in counts]) / 10, np.mean([b for _, b in counts]) / 10
    assert fit["model_status"] == "ok"
    assert fit["coefficient"] == pytest.approx(logit(p1) - logit(p0), abs=1e-8)
    influence = [(b - 10 * p1) / (40 * p1 * (1 - p1)) -
                 (a - 10 * p0) / (40 * p0 * (1 - p0)) for a, b in counts]
    expected_se = np.sqrt(np.sum(np.square(influence)) * 4 / 3 * 79 / 78)
    assert expected_se > 0
    assert fit["cluster_se"] == pytest.approx(expected_se, abs=1e-8)
    assert fit["coefficient_ci_low"] == pytest.approx(fit["coefficient"] - student_t.ppf(.975, 3) * expected_se)
    separated = data.assign(y=data.x)
    assert fit_logistic(separated, "y", "x")["model_status"] != "ok"


def test_deterministic_summaries_and_metric_specific_missingness(inputs):
    data = join_to_outcomes(*inputs)
    data.loc[0, "delta_opp_visible_width"] = np.nan
    first = analyze(data)
    second = analyze(data.sample(frac=1, random_state=7))
    for left, right in zip(first, second):
        assert left.to_csv(index=False) == right.to_csv(index=False)
    models = first[0].query("record_type == 'model' and action_type == 'Pass'")
    assert models[models.spatial_metric.eq("delta_opp_visible_width")].N.item() == 159
    assert models[models.spatial_metric.eq(PRIMARY)].N.eq(160).all()

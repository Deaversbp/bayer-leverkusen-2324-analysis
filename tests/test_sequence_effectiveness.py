"""Twelve focused terminal-join, categorical-model and sensitivity checks."""

import numpy as np
import pandas as pd
import pytest
from scipy.special import logit

from leverkusen.sequences.effectiveness import (
    CENTROID, CONTROLS, FLAGS, OUTCOMES, analyze, contrast, encode_motifs,
    fit_design, join_terminal_outcomes, model_rows, select_scope,
)
from leverkusen.sequences.multi_action import motif_labels
from leverkusen.spatial.progression_change import starting_third


@pytest.fixture
def inputs():
    rng = np.random.default_rng(15)
    windows, outcomes = [], []
    for length in (2, 3):
        for match in range(1, 5):
            for motif in motif_labels(length):
                for repeat in range(10):
                    eid = f"{length}-{match}-{motif}-{repeat}"
                    start = rng.uniform(0, 120)
                    gaps = rng.uniform(.1, 6, length).round(3)
                    times = np.r_[0, np.cumsum(gaps)]
                    row = dict(window_id=eid, match_id=match, attacking_control_spell_id=f"s{match}",
                               window_length=length, action_type_motif=motif, direction_profile="F" * length,
                               carry_action_count=motif.count("C"), total_progression=rng.normal(5, 8),
                               first_action_start_x=start, duration_seconds=gaps.sum(), maximum_leg_gap=gaps.max(),
                               mean_leg_gap=gaps.mean(), net_opp_centroid_x=rng.normal(2, 4),
                               starting_third=starting_third(pd.Series([start])).iloc[0], terminal_event_type="Carry")
                    row.update({flag: False for flag in FLAGS})
                    for i in range(4):
                        row.update({f"anchor_{i}_event_id": f"{eid}-a{i}" if i <= length else None,
                                    f"anchor_{i}_event_index": 100 * repeat + i if i <= length else np.nan,
                                    f"anchor_{i}_period_seconds": times[i] if i <= length else np.nan})
                    for i in (1, 2, 3):
                        row[f"leg_{i}_gap_seconds"] = gaps[i - 1] if i <= length else np.nan
                    windows.append(row)
                    outcome = dict(match_id=match, attacking_control_spell_id=f"s{match}",
                                   reference_event_id=f"{eid}-a{length}", reference_event_index=100 * repeat + length,
                                   reference_event_type="Carry", reference_timestamp=str(pd.Timedelta(milliseconds=round(times[-1] * 1000))),
                                   reference_is_box_entry=int(repeat == 0), reference_is_shot=int(repeat == 1))
                    for name in OUTCOMES:
                        outcome[name] = int(repeat < 2) * (.2 if name.startswith("future_xg") else 1)
                    outcomes.append(outcome)
    return pd.DataFrame(windows), pd.DataFrame(outcomes)


def test_exact_terminal_join_and_conflicting_context(inputs):
    windows, outcomes = inputs
    data = join_terminal_outcomes(windows, outcomes.iloc[::-1])
    assert len(data) == len(windows)
    for length in (2, 3):
        assert data.loc[data.window_length.eq(length), "terminal_anchor_event_id"].str.endswith(f"a{length}").all()
    changed = outcomes.copy()
    changed.loc[0, "attacking_control_spell_id"] = "other"
    with pytest.raises(ValueError, match="crosses spell"):
        join_terminal_outcomes(windows, changed)
    with pytest.raises(ValueError, match="Missing exact terminal"):
        join_terminal_outcomes(windows, outcomes.iloc[1:])
    with pytest.raises(ValueError, match="Ambiguous Phase 5A"):
        join_terminal_outcomes(windows, pd.concat([outcomes, outcomes.iloc[:1]]))


def test_start_and_intermediate_outcomes_never_used(inputs):
    windows, outcomes = inputs
    extra = []
    for i in (0, 1):
        table = outcomes.copy()
        table["reference_event_id"] = windows[f"anchor_{i}_event_id"]
        table[OUTCOMES] = 99
        extra.append(table)
    pd.testing.assert_frame_equal(join_terminal_outcomes(windows, pd.concat([outcomes, *extra])),
                                  join_terminal_outcomes(windows, outcomes))


def test_lengths_separate_and_pp_reference_encoding(inputs):
    data = join_terminal_outcomes(*inputs)
    for length in (2, 3):
        group = data[data.window_length.eq(length)]
        design = encode_motifs(group, length)
        reference = "P" * length
        dummy = [c for c in design if c.startswith("motif_")]
        assert f"motif_{reference}" not in dummy
        assert design.loc[group.action_type_motif.eq(reference), dummy].eq(0).all().all()
        rows = model_rows(data, length)
        assert all(row["model_N"] == len(group) for row in rows)
        assert all(row["reference_motif"] == reference for row in rows)
    with pytest.raises(ValueError, match="separately"):
        encode_motifs(data, 2)


def test_motifs_progression_and_start_thirds_preserved(inputs):
    windows, outcomes = inputs
    data = join_terminal_outcomes(windows, outcomes).set_index("window_id")
    for col in ("action_type_motif", "direction_profile", "total_progression", "starting_third"):
        pd.testing.assert_series_equal(data[col].sort_index(), windows.set_index("window_id")[col].sort_index())


def test_five_second_rule_requires_every_leg(inputs):
    data = join_terminal_outcomes(*inputs).iloc[:3].copy()
    data["maximum_leg_gap"] = [5., 5.001, 4.]
    data["mean_leg_gap"] = [2.5, 2.6, 4.]
    assert select_scope(data, "gap_le_5").index.tolist() == [0, 2]
    windows, outcomes = inputs
    windows.loc[0, "maximum_leg_gap"] = 0
    with pytest.raises(ValueError, match="gap metadata"):
        join_terminal_outcomes(windows, outcomes)


def test_three_second_rule_requires_every_leg(inputs):
    data = join_terminal_outcomes(*inputs).iloc[:3].copy()
    data["maximum_leg_gap"] = [3., 3.001, 2.]
    data["mean_leg_gap"] = [1.5, 1.6, 2.]
    assert select_scope(data, "gap_le_3").index.tolist() == [0, 2]


def test_immediate_exclusion_specific_to_outcome(inputs):
    data = join_terminal_outcomes(*inputs)
    box = select_scope(data, "exclude_immediate", "box_entry")
    shot = select_scope(data, "exclude_immediate", "shot")
    xg = select_scope(data, "exclude_immediate", "future_xg")
    assert box.reference_is_box_entry.eq(0).all() and shot.reference_is_shot.eq(0).all()
    assert not set(box.window_id) == set(shot.window_id)
    assert set(shot.window_id) == set(xg.window_id)


def test_centroid_adjustment_uses_net_sequence_value(inputs):
    data = join_terminal_outcomes(*inputs)
    data = data[data.window_length.eq(2)].copy()
    data["leg_1_delta_opp_centroid_x"] = 999
    design = encode_motifs(data, 2, centroid=True)
    assert design[CENTROID].equals(data[CENTROID])
    assert "leg_1_delta_opp_centroid_x" not in design
    assert CENTROID not in encode_motifs(data, 2)


def test_no_defensive_context_or_composite_fields(inputs):
    windows, outcomes = inputs
    base = join_terminal_outcomes(windows, outcomes)
    windows["defensive_class"] = "unused"
    windows["success_score"] = 99
    pd.testing.assert_frame_equal(base, join_terminal_outcomes(windows, outcomes))
    assert "defensive_class" not in base and "success_score" not in base


def test_full_covariance_contrast_and_probability_against_closed_form():
    # Balanced control patterns make controls orthogonal to outcome/motif cells.
    rows = []
    for match in range(4):
        for motif, successes in zip(motif_labels(2), [2, 3, 4, 5]):
            for pattern in range(8):
                for i in range(10):
                    rows.append(dict(match_id=match, window_length=2, action_type_motif=motif,
                                     total_progression=(-1) ** (pattern & 1), first_action_start_x=40 + 10 * (-1) ** ((pattern >> 1) & 1),
                                     duration_seconds=2 + (-1) ** ((pattern >> 2) & 1), y=int(i < successes)))
    group = pd.DataFrame(rows)
    fit = fit_design(group, 2, "y")
    assert fit["model_status"] == "ok"
    vector = np.zeros(len(fit["terms"]))
    vector[fit["terms"].index("motif_PC")] = 1
    vector[fit["terms"].index("motif_CP")] = -1
    assert contrast(fit, vector)["coefficient"] == pytest.approx(logit(.3) - logit(.4), abs=1e-7)
    group["box_entry_within_10s"] = group.y
    models = pd.DataFrame(model_rows(group, 2, medians=group[list(CONTROLS)].median()))
    assert models.loc[models.record_type.eq("model"), "predicted_probability"].tolist() == pytest.approx([.2, .3, .4, .5])


def test_sparse_cells_and_support_sensitivities(inputs):
    data = join_terminal_outcomes(*inputs)
    data.loc[data.action_type_motif.eq("CCC"), "box_entry_within_10s"] = 0
    rows = pd.DataFrame(model_rows(data, 3))
    assert rows.loc[rows.motif.eq("CCC"), "model_status"].item() == "separated_motif_cell"
    assert rows.loc[rows.motif.eq("CCC"), "odds_ratio"].isna().all()
    data.loc[0, "any_frame_oob_unknown"] = True
    data.loc[1, "any_frame_coincident"] = True
    assert len(select_scope(data, "exclude_oob")) == len(data) - 1
    assert len(select_scope(data, "exclude_coincidence")) == len(data) - 1


def test_core_determinism(inputs):
    data = join_terminal_outcomes(*inputs)
    first, second = analyze(data), analyze(data.sample(frac=1, random_state=7))
    for a, b in zip(first, second):
        assert a.to_csv(index=False) == b.to_csv(index=False)

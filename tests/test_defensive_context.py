"""Ten focused checks for frozen starting context and bounded interactions."""

import numpy as np
import pandas as pd
import pytest

from leverkusen.spatial.danger_analysis import CONTROLS, FLAGS, OUTCOMES, PRIMARY, REFERENCE
from leverkusen.spatial.progression_change import scope_mask, starting_third
from leverkusen.tactics import context as ctx


@pytest.fixture
def inputs():
    rng = np.random.default_rng(61)
    rows, anchors = [], []
    for i in range(360):
        third = i % 3
        action = "Pass" if i % 2 else "Carry"
        start = third*40 + rng.uniform(1, 39)
        row = dict(match_id=i % 12, attacking_control_spell_id=f"s{i}", from_event_id=f"f{i}", to_event_id=f"t{i}",
                   from_event_index=i*2, to_event_index=i*2+1, action_type=action, to_event_type="Carry",
                   action_start_x=start, action_delta_x=rng.normal(3, 8), anchor_gap_seconds=rng.uniform(.1, 7),
                   starting_third=starting_third(pd.Series([start])).iloc[0], delta_opp_centroid_x=rng.normal(1, 5),
                   delta_opp_visible_width=0., delta_opp_visible_depth=0., delta_opp_mean_nearest_neighbor_distance=0.,
                   delta_lev_centroid_x=0., delta_opp_visible_player_count=0.)
        row.update({c: False for c in [*FLAGS, *REFERENCE]})
        row.update({c: float(rng.random() < .25) for c in OUTCOMES})
        rows.append(row)
        for offset, eid in enumerate((f"f{i}", f"t{i}")):
            anchor = dict(match_id=row["match_id"], attacking_control_spell_id=f"s{i}", event_id=eid,
                          event_index=i*2+offset, event_type=action if offset == 0 else "Carry", statsbomb_revision="fixture")
            for col in ctx.GEOMETRY:
                anchor[col] = 5 + rng.uniform(0, 15) + third*25 + offset*30
                anchor[f"{col}_available"] = True
                anchor[f"{col}_status"] = "ok"
            anchors.append(anchor)
    return pd.DataFrame(rows), pd.DataFrame(anchors)


def windows_for(source):
    sequences, windows = [], []
    for i, row in enumerate(source.itertuples()):
        common = dict(window_id=f"w{i}", match_id=row.match_id, attacking_control_spell_id=row.attacking_control_spell_id,
                      window_length=2, total_progression=row.action_delta_x, action_type_motif=("PP", "PC", "CP", "CC")[i % 4])
        sequences.append(dict(common, first_action_start_x=row.action_start_x, starting_third=row.starting_third,
                              duration_seconds=row.anchor_gap_seconds, terminal_anchor_event_id=row.to_event_id,
                              box_entry_within_10s=row.box_entry_within_10s))
        windows.append(dict(common, anchor_0_event_id=row.from_event_id, anchor_0_event_index=row.from_event_index,
                            anchor_2_event_id=row.to_event_id))
    sequences.append(dict(sequences[0], window_id="three", window_length=3))
    windows.append(dict(windows[0], window_id="three", window_length=3))
    return pd.DataFrame(sequences), pd.DataFrame(windows)


def test_context_uses_exact_from_and_preserves_terminal_outcomes(inputs):
    source, anchors = inputs
    data, _ = ctx.construct_transitions(source, anchors.iloc[::-1])
    expected = anchors.set_index(["match_id", "event_id"])
    for row in data.itertuples():
        assert row.opp_centroid_x_from == expected.loc[(row.match_id, row.from_event_id), "opp_centroid_x"]
    pd.testing.assert_frame_equal(data.set_index("from_event_id")[OUTCOMES].sort_index(), source.set_index("from_event_id")[OUTCOMES].sort_index())
    bad = anchors.copy()
    bad.loc[0, "attacking_control_spell_id"] = "wrong"
    with pytest.raises(ValueError, match="crosses locked spell"):
        ctx.construct_transitions(source, bad)


def test_to_geometry_cannot_change_context_or_cutpoints(inputs):
    source, anchors = inputs
    expected, cuts = ctx.construct_transitions(source, anchors)
    changed = anchors.copy()
    changed.loc[changed.event_id.str.startswith("t"), ctx.GEOMETRY] = 999.
    actual, new_cuts = ctx.construct_transitions(source, changed)
    pd.testing.assert_frame_equal(expected, actual)
    pd.testing.assert_frame_equal(cuts, new_cuts)


def test_within_third_tertiles_and_ties_are_deterministic(inputs):
    source, anchors = inputs
    data, cuts = ctx.construct_transitions(source, anchors)
    shuffled, new_cuts = ctx.construct_transitions(source.sample(frac=1, random_state=2), anchors)
    pd.testing.assert_frame_equal(data, shuffled)
    pd.testing.assert_frame_equal(cuts, new_cuts)
    for row in cuts.itertuples():
        raw = ctx.DIMENSIONS[row.context_dimension][1]
        values = data.loc[data.starting_third.eq(row.starting_third), raw]
        np.testing.assert_allclose([row.lower_cut, row.upper_cut], values.quantile([1/3, 2/3]))
    points = data.iloc[:3].copy()
    cut = cuts.query("context_dimension == 'centroid'").iloc[0]
    points["starting_third"] = cut.starting_third
    points["opp_centroid_x_from"] = [cut.lower_cut, cut.upper_cut, np.nextafter(cut.upper_cut, np.inf)]
    assert ctx.assign_contexts(points, cuts).centroid_context.tolist() == [1, 2, 3]


def test_context_cuts_do_not_consume_outcomes_and_missing_stays_missing(inputs):
    source, anchors = inputs
    data, cuts = ctx.construct_transitions(source, anchors)
    changed = data.drop(columns=OUTCOMES)
    pd.testing.assert_frame_equal(cuts, ctx.fit_cutpoints(changed))
    changed.loc[0, "opp_centroid_x_from_available"] = False
    result = ctx.assign_contexts(changed, cuts)
    assert pd.isna(result.loc[0, "centroid_context"])
    assert result.loc[0, "opp_centroid_x_from"] == data.loc[0, "opp_centroid_x_from"]


def capture_fit(monkeypatch):
    calls = []

    def fit(design, data, target):
        calls.append((design.copy(), data.copy(), target))
        return dict(model_status="insufficient_data", mcfadden_r2=np.nan, max_score=np.nan, information_condition=np.nan)

    monkeypatch.setattr(ctx, "fit_frame", fit)
    return calls


def test_pass_carry_are_separate_with_fixed_action_sd(inputs, monkeypatch):
    source, anchors = inputs
    data, _ = ctx.construct_transitions(source, anchors)
    calls = capture_fit(monkeypatch)
    for action in ("Pass", "Carry"):
        rows = ctx.model_context(data, action, "centroid", scope="gap_le_3")
        design, group, target = calls[-1]
        assert set(group.action_type) == {action}
        sd = data.loc[data.action_type.eq(action), PRIMARY].std(ddof=1)
        np.testing.assert_allclose(design.centroid_per_sd, group[PRIMARY]/sd)
        assert rows[0]["predictor_sd"] == sd
        assert target == "box_entry_within_10s"


def test_prespecified_design_and_one_dimension_per_model(inputs):
    source, anchors = inputs
    data, _ = ctx.construct_transitions(source, anchors)
    for dimension in ctx.DIMENSIONS:
        design = ctx.build_context_design(data, dimension, 5)
        assert design.columns.tolist() == ["centroid_per_sd", "context_T2", "context_T3", "centroid_x_T2", "centroid_x_T3", *CONTROLS]
        np.testing.assert_allclose(design.centroid_x_T3, data[PRIMARY]/5*data[f"{dimension}_context"].eq(3).astype(float))
        augmented = ctx.build_context_design(data, dimension, 5, visible_count=True)
        assert augmented.columns.tolist() == [*design.columns, ctx.COUNT]


def test_motif_context_uses_sequence_start_with_terminal_identity_check(inputs):
    source, anchors = inputs
    data, cuts = ctx.construct_transitions(source, anchors)
    sequences, windows = windows_for(source)
    motifs = ctx.construct_motifs(sequences, windows, anchors, cuts)
    expected = data.set_index("from_event_id")
    for row in motifs.itertuples():
        assert row.opp_centroid_x_from == expected.loc[row.anchor_0_event_id, "opp_centroid_x_from"]
        assert row.centroid_context == expected.loc[row.anchor_0_event_id, "centroid_context"]
    bad = windows.copy()
    bad.loc[0, "anchor_2_event_id"] = "wrong"
    with pytest.raises(ValueError, match="terminal identity"):
        ctx.construct_motifs(sequences, bad, anchors, cuts)


def test_three_action_excluded_and_only_one_centroid_motif_model(inputs, monkeypatch):
    source, anchors = inputs
    _, cuts = ctx.construct_transitions(source, anchors)
    sequences, windows = windows_for(source)
    motifs = ctx.construct_motifs(sequences, windows, anchors, cuts)
    assert len(motifs) == len(source) and motifs.window_length.eq(2).all()
    calls = capture_fit(monkeypatch)
    ctx.analyze_motifs(motifs)
    assert len(calls) == 1
    design = calls[0][0]
    assert len(design.columns) == 14
    assert set(design.columns) == {"motif_PC", "motif_CP", "motif_CC", "context_T2", "context_T3",
                                   "PC_x_T2", "PC_x_T3", "CP_x_T2", "CP_x_T3", "CC_x_T2", "CC_x_T3",
                                   "total_progression", "first_action_start_x", "duration_seconds"}
    with pytest.raises(ValueError, match="Only two-action"):
        ctx.analyze_motifs(motifs.assign(window_length=3))


def test_inherited_gap_and_whole_frame_masks(inputs, monkeypatch):
    source, anchors = inputs
    data, _ = ctx.construct_transitions(source, anchors)
    data.loc[data.index[:20], "from_frame_oob"] = True
    data.loc[data.index[20:40], "to_frame_coincident_unknown"] = True
    calls = capture_fit(monkeypatch)
    for scope in ("all", "gap_le_5", "gap_le_3", "exclude_oob", "exclude_coincidence"):
        ctx.model_context(data, "Pass", "centroid", scope=scope)
        expected = data[data.action_type.eq("Pass") & scope_mask(data, scope)]
        assert calls[-1][1].from_event_id.tolist() == expected.from_event_id.tolist()


def test_deterministic_four_core_frames(inputs):
    source, anchors = inputs
    products = []
    for _ in range(2):
        data, cuts = ctx.construct_transitions(source, anchors)
        summary, interactions = ctx.analyze_contexts(data, cuts)
        sequences, windows = windows_for(source)
        motifs = ctx.analyze_motifs(ctx.construct_motifs(sequences, windows, anchors, cuts))
        products.append([f.to_csv(index=False, lineterminator="\n").encode() for f in (data, summary, interactions, motifs)])
    assert products[0] == products[1]

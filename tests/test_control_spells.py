"""Football control, context, ID and outcome-independence contract."""

import pandas as pd
import pytest

from leverkusen.sequences.control_spells import segment_parent, segment_stream


def stream(actions):
    rows = []
    for i, action in enumerate(actions, 1):
        typ, team, *context = action
        rows.append(
            dict(
                match_id=1,
                period=1,
                possession_id=7,
                possession_team_id=904,
                event_index=i,
                period_seconds=float(i),
                timestamp=f"00:00:{i:02}.000",
                event_type=typ,
                event_team_id=team,
                event_team=str(team),
                provider_context=context[0] if context else "",
                restart_context="",
                advantage=False,
                keeper_type="",
                recovery_failure=False,
                dribble_outcome="",
            )
        )
    return pd.DataFrame(rows)


def test_opponent_control_and_regain_before_spatial_anchor():
    x = stream(
        [
            ("Pass", 904),
            ("Ball Recovery", 10),
            ("Carry", 10),
            ("Pass", 10),
            ("Ball Recovery", 904),
            ("Carry", 904),
        ]
    )
    m, s, b = segment_parent(x)
    assert len(s) == 2 and b[0]["onset_event"] == 2 and b[0]["resume_event"] == 5
    assert m.iloc[1:4].attacking_control_spell_id.isna().all()
    assert m.iloc[4].attacking_control_spell_id.endswith("-s2")
    assert s[1]["start_event"] == 5


@pytest.mark.parametrize(
    "typ", ["Pressure", "Ball Recovery", "Clearance", "Duel", "Block"]
)
def test_single_defensive_intervention_is_not_control(typ):
    _, s, b = segment_parent(stream([("Pass", 904), (typ, 10), ("Pass", 904)]))
    assert len(s) == 1 and not b


def test_clearance_second_ball_preserves_spell():
    _, s, b = segment_parent(
        stream(
            [("Pass", 904), ("Clearance", 10), ("Ball Recovery", 904), ("Carry", 904)]
        )
    )
    assert len(s) == 1 and not b


def test_completed_distribution_is_control_without_three_event_template():
    _, s, b = segment_parent(stream([("Pass", 904), ("Pass", 10), ("Pass", 904)]))
    assert len(s) == 2 and b[0]["resume_event"] == 3


def test_failed_interception_does_not_reestablish_control():
    _, s, b = segment_parent(
        stream(
            [
                ("Pass", 904),
                ("Pass", 10),
                ("Interception", 904, "interception.outcome:Lost In Play"),
                ("Pass", 10),
                ("Pass", 904),
            ]
        )
    )
    assert len(s) == 2 and b[0]["resume_event"] == 5


def test_pass_out_then_restart():
    x = stream(
        [
            ("Pass", 904),
            ("Pass", 904, "pass.outcome:Out"),
            ("Ball Receipt*", 904, "ball_receipt.outcome:Incomplete"),
            ("Pass", 904),
            ("Carry", 904),
        ]
    )
    x.loc[3, "restart_context"] = "Throw-in"
    m, s, b = segment_parent(x)
    assert len(s) == 2 and len(b) == 1 and b[0]["reason"] == "BALL_OUT"
    assert m.iloc[1:3].attacking_control_spell_id.isna().all()
    assert s[1]["start_reason"] == "RESTART"


def test_internal_restart_and_paired_administrative_start():
    x = stream(
        [
            ("Half Start", 904),
            ("Half Start", 10),
            ("Pass", 904),
            ("Carry", 904),
            ("Pass", 904),
        ]
    )
    x.loc[2, "restart_context"] = "Kick Off"
    x.loc[4, "restart_context"] = "Free Kick"
    m, s, b = segment_parent(x)
    assert len(s) == 2 and len(b) == 1
    assert m.iloc[:2].attacking_control_spell_id.isna().all()
    assert s[0]["start_event"] == 3 and s[1]["start_event"] == 5


def test_nonterminal_shot_and_reflex_keeper_contact():
    x = stream(
        [
            ("Pass", 904),
            ("Shot", 904),
            ("Goal Keeper", 10),
            ("Clearance", 10),
            ("Pass", 904),
        ]
    )
    x.loc[2, "keeper_type"] = "Shot Saved"
    _, s, b = segment_parent(x)
    assert len(s) == 1 and not b


def test_shot_opponent_control_or_parent_end():
    _, s, b = segment_parent(
        stream([("Pass", 904), ("Shot", 904), ("Goal Keeper", 10), ("Pass", 10)])
    )
    assert len(s) == 1 and len(b) == 1 and b[0]["reason"] == "TERMINAL_SHOT"
    assert b[0]["onset_event"] == 2
    _, s, b = segment_parent(stream([("Pass", 904), ("Shot", 904)]))
    assert len(s) == 1 and b[0]["onset_event"] == 2


@pytest.mark.parametrize("advantage,expected", [(False, 1), (True, 0)])
def test_paired_foul_stoppage_and_advantage(advantage, expected):
    x = stream(
        [("Pass", 904), ("Foul Committed", 904), ("Foul Won", 10), ("Pass", 904)]
    )
    x.loc[1:2, "advantage"] = advantage
    _, _, b = segment_parent(x)
    assert len(b) == expected


@pytest.mark.parametrize(
    "actions,status",
    [
        ([("Starting XI", 904), ("Half Start", 10)], "administrative_no_spell"),
        ([("Goal Keeper", 904)], "insufficient_context_no_spell"),
    ],
)
def test_no_spell_parents(actions, status):
    m, s, b = segment_parent(stream(actions))
    assert not s and not b and m.attacking_control_spell_id.isna().all()
    assert m.membership_status.eq(status).all()


def test_terminal_only_parent_has_no_preboundary_interval():
    m, s, _ = segment_parent(stream([("Shot", 904), ("Goal Keeper", 10)]))
    assert not s and m.attacking_control_spell_id.isna().all()


def test_all_excluded_stream_has_stable_empty_summary_schema():
    m, s, b = segment_stream(stream([("Half Start", 904)]))
    assert s.empty and b.empty and m.attacking_control_spell_id.isna().all()
    assert "attacking_control_spell_id" in s and "boundary_type" in b


def test_ids_stable_and_reset_in_each_provider_parent():
    x = stream([("Pass", 904), ("Pass", 10), ("Pass", 904)])
    y = x.copy()
    y["possession_id"] = 8
    y["event_index"] += 3
    combined = pd.concat([x, y])
    a = segment_stream(combined)
    b = segment_stream(combined.sample(frac=1, random_state=12))
    for left, right in zip(a, b):
        pd.testing.assert_frame_equal(left, right)
    assert a[1].attacking_control_spell_id.tolist() == [
        "1-p1-pp7-s1",
        "1-p1-pp7-s2",
        "1-p1-pp8-s1",
        "1-p1-pp8-s2",
    ]


def test_soft_recycling_missing_geometry_and_outcomes_cannot_split():
    x = stream([("Pass", 904), ("Carry", 904), ("Pass", 904), ("Carry", 904)])
    baseline = segment_parent(x)
    x["retreat_from_peak"] = [0, 60, 80, 10]
    x["nonpositive_run"] = [0, 20, 30, 0]
    x["reset_confirmation"] = [False, True, True, False]
    x["validated_anchor"] = False
    x["future_xg"] = 99
    x["start_x"] = [100, 40, 20, 90]
    _, s, b = segment_parent(x)
    assert s == baseline[1] and b == baseline[2] and len(s) == 1

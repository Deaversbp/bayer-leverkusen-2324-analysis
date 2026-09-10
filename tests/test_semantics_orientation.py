"""Offline semantic contracts: uncertainty, frame links, and geometry preservation."""

from copy import deepcopy

import numpy as np
import pytest
from shapely.geometry import MultiPoint

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.data.semantic_diagnostics import (
    codec_alignment,
    related_conflict_ids,
    related_evidence,
    team_context,
)
from leverkusen.spatial.orientation import (
    VALIDATED,
    frame_semantics,
    normalize_attacking_point,
    point_team_label,
)
from leverkusen.visualization import style


@pytest.fixture
def example():
    event = {
        "id": "a",
        "team": {"id": 904, "name": "Bayer Leverkusen"},
        "possession_team": {"id": 100, "name": "Opponent"},
        "type": {"name": "Pass"},
        "location": [12, 23],
        "period": 2,
    }
    frame = {
        "event_uuid": "a",
        "freeze_frame": [
            {"location": [12, 23], "actor": True, "teammate": True, "keeper": False},
            {"location": [100, 45], "actor": False, "teammate": False, "keeper": True},
        ],
    }
    match = {"home_team": {"home_team_id": 100}, "away_team": {"away_team_id": 904}}
    return event, frame, match


def decision(example, **kwargs):
    return frame_semantics(
        *example,
        source_revision=STATSBOMB_REVISION,
        related_team_conflict=False,
        **kwargs,
    )


@pytest.mark.parametrize(
    "event_team,flag,expected",
    [(904, True, 904), (904, False, 100), (100, True, 100), (100, False, 904)],
)
def test_team_mapping_uses_event_team(event_team, flag, expected):
    result = point_team_label(flag, event_team, (904, 100), semantics_status=VALIDATED)
    assert result["team_id"] == expected
    assert result["is_leverkusen"] is (expected == 904)
    assert result["is_opponent"] is (expected != 904)


def test_context_preserves_possession_and_unknown(example):
    event, _, match = example
    context = team_context(event, match)
    assert context["team_agreement"] == "different"
    assert context["event_team_is_leverkusen"] is True
    assert context["possession_team_is_leverkusen"] is False
    assert context["attacking_context"] == "leverkusen_event_in_opponent_possession"
    event["team"]["id"], event["possession_team"]["id"] = 100, 904
    assert (
        team_context(event, match)["attacking_context"]
        == "opponent_event_in_leverkusen_possession"
    )
    event.pop("team")
    assert (
        team_context(event, match)["attacking_context"]
        == "ambiguous_possession_context"
    )
    event.pop("possession_team")
    assert team_context(event, match)["team_agreement"] == "missing_both"


def test_scope_requires_real_evidence_and_does_not_mutate(example):
    original = deepcopy(example)
    assert decision(example)["semantics_status"] == VALIDATED
    assert example == original
    event, frame, match = example
    for conflict in (True, None):
        assert (
            frame_semantics(
                event,
                frame,
                match,
                source_revision=STATSBOMB_REVISION,
                related_team_conflict=conflict,
            )["semantics_status"]
            != VALIDATED
        )
    assert (
        frame_semantics(
            event, frame, match, source_revision="master", related_team_conflict=False
        )["semantics_status"]
        == "unsupported_source_revision"
    )


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda e, f: e["type"].update(name="Duel"), "unsupported_event_type"),
        (lambda e, f: f.update(event_uuid="other"), "invalid_event_frame_join"),
        (lambda e, f: f.update(freeze_frame=None), "actor_status_unresolved"),
        (
            lambda e, f: f["freeze_frame"][1].update(actor=True),
            "actor_status_unresolved",
        ),
        (lambda e, f: f["freeze_frame"][0].update(actor=1), "actor_status_unresolved"),
        (
            lambda e, f: f["freeze_frame"][0].update(teammate=False),
            "actor_team_flag_unresolved",
        ),
        (
            lambda e, f: f["freeze_frame"][1].update(teammate=None),
            "point_flags_unresolved",
        ),
        (
            lambda e, f: f["freeze_frame"][0].update(location=[12.000001, 23]),
            "actor_encoding_unresolved",
        ),
        (
            lambda e, f: f["freeze_frame"][0].update(location=[108, 57]),
            "actor_encoding_unresolved",
        ),
    ],
)
def test_fail_closed_scope(example, mutation, reason):
    mutation(*example[:2])
    assert decision(example)["semantics_status"] == reason


def test_encoding_fingerprint_is_exact_not_nearness():
    original = [12.3, 48.7]
    encoded = [float(v) for v in np.asarray(original, dtype=np.float32)]
    assert codec_alignment(original, encoded) == "exact_float32"
    assert codec_alignment(original, [12.3000000001, 48.7]) == "not_exact"
    assert codec_alignment(None, encoded) == "unavailable"


@pytest.mark.parametrize(
    "reference,expected,status",
    [(904, [20, 13], "identity_explicit"), (100, [100, 67], "rotated_180")],
)
def test_normalization_both_axes_and_raw_nonmutation(reference, expected, status):
    location = [20, 13]
    result = normalize_attacking_point(
        location,
        reference_team_id=reference,
        target_team_id=904,
        match_team_ids=(904, 100),
        semantics_status=VALIDATED,
    )
    assert [result["x_attacking"], result["y_attacking"]] == expected
    assert result["orientation_status"] == status
    assert [result["x_raw"], result["y_raw"]] == location == [20, 13]


def test_rotation_preserves_handedness_distances_and_footprint():
    native = np.array([[-1, 3], [26, 8], [18, 67], [130, 82]], dtype=float)
    rotated = np.array(
        [
            [
                normalize_attacking_point(
                    p.tolist(),
                    reference_team_id=100,
                    target_team_id=904,
                    match_team_ids=(100, 904),
                    semantics_status=VALIDATED,
                )[k]
                for k in ("x_attacking", "y_attacking")
            ]
            for p in native
        ]
    )
    assert np.allclose(
        np.linalg.norm(native[:, None] - native, axis=-1),
        np.linalg.norm(rotated[:, None] - rotated, axis=-1),
    )
    assert MultiPoint(native).convex_hull.area == pytest.approx(
        MultiPoint(rotated).convex_hull.area
    )
    assert np.linalg.det(
        np.stack([native[1] - native[0], native[2] - native[0]])
    ) == pytest.approx(
        np.linalg.det(np.stack([rotated[1] - rotated[0], rotated[2] - rotated[0]]))
    )
    assert np.allclose(native, np.array([120, 80]) - rotated)
    assert rotated[0, 0] == 121  # OOB is preserved, not clipped.


def test_unsupported_never_produces_football_labels():
    result = normalize_attacking_point(
        [10, 20],
        reference_team_id=904,
        target_team_id=904,
        match_team_ids=(904, 100),
        semantics_status="mixed_semantics",
    )
    assert result["x_attacking"] is result["y_attacking"] is None
    assert result["orientation_status"] == "unsupported"
    label = point_team_label(True, 904, (904, 100), semantics_status="mixed_semantics")
    assert label["frame_player_side"] == "unresolved"
    assert label["team_id"] is label["is_leverkusen"] is None
    assert "defending_team" not in label and "formation" not in label
    for flag in (None, 1, "True"):
        assert (
            point_team_label(flag, 904, (904, 100), semantics_status=VALIDATED)[
                "team_id"
            ]
            is None
        )


def test_related_clouds_reveal_conflict_without_assigning_identity(example):
    event, frame, _ = example
    event["related_events"] = ["b"]
    other = deepcopy(event)
    other.update(id="b", team={"id": 100}, related_events=[])
    other_frame = deepcopy(frame)
    other_frame["event_uuid"] = "b"
    edges = related_evidence(
        event, frame, {"a": event, "b": other}, {"a": frame, "b": other_frame}
    )
    assert edges[0]["equal_cloud_team_label_conflict"] is True
    assert edges[0]["related_event_id"] == "b"
    for point in other_frame["freeze_frame"]:
        point["teammate"] = not point["teammate"]
    edges = related_evidence(
        event, frame, {"a": event, "b": other}, {"a": frame, "b": other_frame}
    )
    assert edges[0]["expected_team_labels_agree"] is True
    assert "player_id" not in edges[0]


def test_central_style_has_noncolor_cues_and_distinct_arrow_meanings():
    assert style.LEVERKUSEN_COLOR != style.OPPONENT_COLOR != style.ACTION_COLOR
    assert style.KEEPER_MARKER != style.OUTFIELD_MARKER
    assert style.TEAM_LABELS["leverkusen"] != style.TEAM_LABELS["opponent"]
    assert style.PROVIDER_ACTION_ARROW["linestyle"] == "-"
    assert style.EVENT_TRANSITION_ARROW["linestyle"] == "--"
    assert "physical path unknown" in style.EVENT_TRANSITION_MEANING


def test_nonreciprocal_conflict_blocks_both_endpoints(example):
    event, frame, match = example
    event["related_events"] = ["b"]
    other, other_frame = deepcopy(event), deepcopy(frame)
    other.update(id="b", team={"id": 100}, related_events=[])
    other_frame["event_uuid"] = "b"
    edges = related_evidence(
        event, frame, {"a": event, "b": other}, {"a": frame, "b": other_frame}
    )
    conflicts = related_conflict_ids({"a": edges, "b": []})
    assert conflicts == {"a", "b"}
    for e, f in [(event, frame), (other, other_frame)]:
        result = frame_semantics(
            e,
            f,
            match,
            source_revision=STATSBOMB_REVISION,
            related_team_conflict=e["id"] in conflicts,
        )
        assert result["semantics_status"] == "related_team_label_conflict"


def test_missing_audit_is_distinct_from_observed_conflict(example):
    result = frame_semantics(
        *example, source_revision=STATSBOMB_REVISION, related_team_conflict=None
    )
    assert result["semantics_status"] == "related_team_audit_unresolved"
    context = team_context({}, {})
    assert context["event_team_valid"] is False
    assert context["event_team_is_leverkusen"] is None
    assert context["possession_team_is_leverkusen"] is None

"""Regression tests for the existing normalization and context behavior."""

from copy import deepcopy

import pandas as pd
import pytest

from leverkusen.data import transforms


def match(match_id=3895292):
    return {
        "match_id": match_id,
        "match_date": "2024-04-06",
        "home_team": {"home_team_name": "Union Berlin"},
        "away_team": {"away_team_name": "Bayer Leverkusen"},
    }


@pytest.mark.parametrize(
    ("team", "expected"),
    [("Bayer Leverkusen", ("Union Berlin", "Away")),
     ("Union Berlin", ("Bayer Leverkusen", "Home"))],
)
def test_team_match_context(team, expected):
    assert transforms.get_team_match_context(match(), team) == expected


def test_unknown_team_is_explicit():
    with pytest.raises(ValueError, match="3895292"):
        transforms.get_team_match_context(match(), "Unknown")


def test_normalize_preserves_nested_columns_and_input():
    records = [{"id": "synthetic", "team": {"name": "Bayer Leverkusen"},
                "pass": {"end_location": [70, 30]}}]
    original = deepcopy(records)
    result = transforms.normalize_events(records)
    assert list(result.columns) == ["id", "team_name", "pass_end_location"]
    assert result.loc[0, "pass_end_location"] == [70, 30]
    assert records == original


@pytest.mark.parametrize("event_type,expected_ids", [(None, ["p", "s"]), ("Pass", ["p"])])
def test_dataset_filter_context_order_and_no_mutation(monkeypatch, event_type, expected_ids):
    records = [
        {"id": "p", "index": 9, "team": {"name": "Bayer Leverkusen"}, "type": {"name": "Pass"}},
        {"id": "o", "index": 10, "team": {"name": "Union Berlin"}, "type": {"name": "Pass"}},
        {"id": "s", "index": 1, "team": {"name": "Bayer Leverkusen"}, "type": {"name": "Shot"}},
    ]
    original = deepcopy(records)
    calls = []

    def load(match_id):
        calls.append(match_id)
        return records

    monkeypatch.setattr(transforms, "load_events", load)
    result = transforms.build_team_event_dataset(
        [match(), match(2)], "Bayer Leverkusen", event_type
    )
    assert calls == [3895292, 2]
    assert result["id"].tolist() == expected_ids * 2
    assert result["match_id"].tolist() == [3895292] * len(expected_ids) + [2] * len(expected_ids)
    assert result["opponent"].eq("Union Berlin").all()
    assert result["venue"].eq("Away").all()
    assert result["match_date"].eq(pd.Timestamp("2024-04-06")).all()
    assert result.index.tolist() == list(range(len(result)))
    assert records == original


@pytest.mark.parametrize("case", ["no_matches", "no_events", "other_team", "other_type"])
def test_empty_result_keeps_only_context_columns(monkeypatch, case):
    records = [] if case == "no_events" else [
        {"team": {"name": "Union Berlin" if case == "other_team" else "Bayer Leverkusen"},
         "type": {"name": "Shot"}}
    ]
    monkeypatch.setattr(transforms, "load_events", lambda match_id: records)
    result = transforms.build_team_event_dataset(
        [] if case == "no_matches" else [match()], "Bayer Leverkusen", "Pass"
    )
    pd.testing.assert_frame_equal(
        result, pd.DataFrame(columns=["match_id", "match_date", "opponent", "venue"])
    )

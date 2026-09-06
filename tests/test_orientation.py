"""Verify the current normalization contract without inventing orientation."""

from leverkusen.data.transforms import normalize_events


def test_normalization_leaves_coordinates_unchanged_across_periods():
    records = [
        {"period": 1, "location": [10, 20], "pass": {"end_location": [35, 70]}},
        {"period": 2, "location": [110, 60], "pass": {"end_location": [85, 10]}},
    ]
    result = normalize_events(records)
    assert result["location"].tolist() == [[10, 20], [110, 60]]
    assert result["pass_end_location"].tolist() == [[35, 70], [85, 10]]
    # No direction/period flip is currently part of event normalization.

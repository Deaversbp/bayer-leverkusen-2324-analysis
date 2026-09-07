"""Offline loader contracts plus explicitly selected live-data checks."""

import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest
import requests
import yaml

from leverkusen.data import loader


@pytest.fixture(autouse=True)
def no_unexpected_network(monkeypatch, request):
    if request.node.get_closest_marker("network"):
        return

    def unexpected(*args, **kwargs):
        pytest.fail("Unit tests must mock HTTP or use explicit existing files")

    monkeypatch.setattr(loader.requests, "get", unexpected)


@pytest.mark.parametrize(
    ("name", "args", "path", "records"),
    [
        (
            "load_matches",
            (),
            "matches/9/281.json",
            [
                {
                    "match_id": 3895292,
                    "home_team": {"home_team_name": "Union Berlin"},
                    "away_team": {"away_team_name": "Bayer Leverkusen"},
                }
            ],
        ),
        (
            "load_events",
            (3895292,),
            "events/3895292.json",
            [
                {
                    "id": "synthetic-event",
                    "index": 2,
                    "type": {"name": "Pass"},
                    "pass": {"end_location": [90, 40]},
                }
            ],
        ),
        (
            "load_lineups",
            (3895292,),
            "lineups/3895292.json",
            [{"team_id": 904, "lineup": []}],
        ),
        (
            "load_360",
            (3895292,),
            "three-sixty/3895292.json",
            [{"event_uuid": "synthetic-event", "freeze_frame": [], "visible_area": []}],
        ),
    ],
)
def test_on_demand_preserves_nested_records(
    monkeypatch, tmp_path, name, args, path, records
):
    monkeypatch.chdir(tmp_path)
    response = Mock(status_code=200)
    response.json.return_value = records
    get = Mock(return_value=response)
    monkeypatch.setattr(loader.requests, "get", get)

    assert getattr(loader, name)(*args) == records
    get.assert_called_once_with(
        f"{loader.BASE_URL}/{path}", timeout=loader.REQUEST_TIMEOUT
    )
    assert f"/{loader.STATSBOMB_REVISION}/data/" in get.call_args.args[0]
    assert "/master/" not in get.call_args.args[0]
    response.raise_for_status.assert_called_once()
    assert list(tmp_path.iterdir()) == []  # No raw data or cache written.


@pytest.mark.parametrize("match_id", [0, -1, True, None, "3895292", 3895292.0, "../x"])
@pytest.mark.parametrize("name", ["load_events", "load_lineups", "load_360"])
def test_invalid_match_ids_fail_before_io(name, match_id):
    with pytest.raises(ValueError, match="positive integer"):
        getattr(loader, name)(match_id)


def test_numpy_integer_match_id(monkeypatch):
    response = Mock(status_code=200)
    response.json.return_value = []
    monkeypatch.setattr(loader.requests, "get", Mock(return_value=response))
    assert loader.load_events(np.int64(3895292)) == []


def test_missing_360_is_explicit(monkeypatch):
    monkeypatch.setattr(
        loader.requests, "get", Mock(return_value=Mock(status_code=404))
    )
    with pytest.raises(FileNotFoundError, match="three-sixty/3895292.json"):
        loader.load_360(3895292)


def test_http_failure_is_not_empty_data(monkeypatch):
    response = Mock(status_code=503)
    response.raise_for_status.side_effect = requests.HTTPError("503 unavailable")
    monkeypatch.setattr(loader.requests, "get", Mock(return_value=response))
    with pytest.raises(requests.HTTPError, match="503"):
        loader.load_matches()


def test_timeout_propagates(monkeypatch):
    monkeypatch.setattr(
        loader.requests, "get", Mock(side_effect=requests.Timeout("timeout"))
    )
    with pytest.raises(requests.Timeout):
        loader.load_events(3895292)


@pytest.mark.parametrize("payload", [{"error": "unexpected"}, [1], None])
def test_invalid_remote_structure(monkeypatch, payload):
    response = Mock(status_code=200)
    response.json.return_value = payload
    monkeypatch.setattr(loader.requests, "get", Mock(return_value=response))
    with pytest.raises(ValueError, match="list of StatsBomb records"):
        loader.load_matches()


def test_explicit_local_read_and_legacy_wrapper(monkeypatch, tmp_path):
    from src import data_loader as legacy

    records = [{"id": "synthetic", "location": [4, 9]}]
    directory = tmp_path / "events"
    directory.mkdir()
    (directory / "3895292.json").write_text(json.dumps(records), encoding="utf-8")
    monkeypatch.setattr(legacy, "RAW_DATA_DIR", tmp_path)
    assert loader.load_events(3895292, raw_data_dir=tmp_path) == records
    assert legacy.load_events(3895292) == records
    with pytest.raises(FileNotFoundError, match="StatsBomb JSON file not found"):
        legacy.load_events(1)


def test_configuration_revision_is_single_source_of_truth():
    project = yaml.safe_load(Path("config/project.yaml").read_text(encoding="utf-8"))
    assert project["statsbomb_revision"] == "533862946a73608c134d18b78226b6371ce7173c"
    assert loader.STATSBOMB_REVISION == project["statsbomb_revision"]
    assert (
        loader.BASE_URL
        == f"https://raw.githubusercontent.com/hudl/open-data/{project['statsbomb_revision']}/data"
    )


def test_revision_can_be_configured_as_another_immutable_sha(tmp_path):
    config = tmp_path / "project.yaml"
    config.write_text("statsbomb_revision: '" + "a" * 40 + "'\n", encoding="utf-8")
    assert loader.load_source_revision(config) == "a" * 40


@pytest.mark.parametrize(
    "revision", ["master", "main", "5338629", None, 123, "A" * 40, "../data"]
)
def test_mutable_or_invalid_revision_is_rejected(tmp_path, revision):
    config = tmp_path / "project.yaml"
    config.write_text(
        yaml.safe_dump({"statsbomb_revision": revision}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="40-character commit SHA"):
        loader.load_source_revision(config)


@pytest.mark.network
def test_live_release_has_34_leverkusen_matches():
    matches = loader.load_matches()
    team_matches = [
        match
        for match in matches
        if "Bayer Leverkusen"
        in (
            match["home_team"]["home_team_name"],
            match["away_team"]["away_team_name"],
        )
    ]
    assert len(matches) == len(team_matches) == 34
    assert len({match["match_id"] for match in team_matches}) == 34


@pytest.mark.network
def test_live_known_match_events():
    records = loader.load_events(3895292)
    assert isinstance(records, list) and records
    assert all({"id", "index", "type"} <= record.keys() for record in records)
    assert any(record["type"]["name"] == "Pass" for record in records)

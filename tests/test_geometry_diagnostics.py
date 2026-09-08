"""Offline integration: original-frame pairing, denominators and raw-free outputs."""

from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from leverkusen.spatial import diagnostics as d
from leverkusen.spatial.geometry import build_frame_geometry


def records():
    players = [
        dict(location=[0, 0], teammate=True, keeper=False, actor=True),
        dict(location=[3, 0], teammate=True, keeper=False, actor=False),
        dict(location=[0, 4], teammate=True, keeper=True, actor=False),
        dict(location=[10, 10], teammate=False, keeper=None, actor=False),
    ]
    return [{"event_uuid": "e", "freeze_frame": players}]


def table():
    return build_frame_geometry(
        1, [{"id": "e"}], records(), source_revision="synthetic"
    )


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setattr(
        d.loader.requests, "get", Mock(side_effect=AssertionError("Unexpected HTTP"))
    )


def test_summaries_pair_original_frames_and_disclose_missingness():
    frames = table()
    result = d.summarize_geometry(frames)
    assert result["inventory"].iloc[0]["variant_rows"] == 6
    summary = result["metric_summary"].set_index(
        ["selected_subset", "goalkeeper_policy", "metric"]
    )
    assert (
        summary.loc[("teammate_false", "excluded", "visible_player_count"), "mean"] == 0
    )
    assert (
        summary.loc[("teammate_false", "excluded", "visible_width"), "na_percent"]
        == 100
    )
    sensitivity = result["goalkeeper_sensitivity"].set_index(
        ["selected_subset", "scope", "metric"]
    )
    assert (
        sensitivity.loc[
            ("teammate_true", "all_pairs", "mean_pairwise_distance"), "mean"
        ]
        == -1
    )
    assert (
        sensitivity.loc[("teammate_true", "all_pairs", "convex_hull_area"), "available"]
        == 0
    )
    assert (
        sensitivity.loc[("all_visible", "all_pairs", "visible_player_count"), "mean"]
        == -2
    )
    assert (
        sensitivity.loc[
            ("all_visible", "all_pairs", "visible_player_count"),
            "pairs_with_unknown_keeper_removal",
        ]
        == 1
    )
    assert (
        result["histograms"]
        .groupby(["selected_subset", "goalkeeper_policy", "metric"])["rows"]
        .sum()
        .equals(summary["available"].sort_index())
    )
    assert set(result["by_valid_points"]["n_valid_points_used"]) == {0, 1, 2, 3, 4}


@pytest.mark.parametrize("corruption", ["duplicate", "missing", "unknown"])
def test_six_variant_validation(corruption):
    frames = table()
    if corruption == "duplicate":
        frames = pd.concat([frames, frames.iloc[:1]])
    elif corruption == "missing":
        frames = frames.iloc[:-1]
    else:
        frames.loc[0, "selected_subset"] = "attacker"
    with pytest.raises(ValueError):
        d.validate_variants(frames)


def configure_loader(monkeypatch, frame_loader):
    matches = [
        {"match_id": n, "home_team": {"home_team_name": "Bayer Leverkusen"}}
        for n in (1, 2)
    ]
    monkeypatch.setattr(d.loader, "load_matches", Mock(return_value=matches))
    monkeypatch.setattr(d.loader, "load_events", Mock(return_value=[{"id": "e"}]))
    monkeypatch.setattr(d.loader, "load_360", frame_loader)


def test_offline_season_writes_derived_tables_and_revision(monkeypatch, tmp_path):
    configure_loader(monkeypatch, Mock(side_effect=[records(), records()]))
    result = d.run_geometry_diagnostics(tmp_path, expected_matches=2)
    output = pd.read_csv(tmp_path / "phase2a_frame_geometry.csv")
    assert len(output) == 12
    assert len(list(tmp_path.glob("*.csv"))) == 9
    assert not list(tmp_path.glob("*.json"))
    assert not {
        "freeze_frame",
        "location",
        "visible_area",
        "multiple_actor_locations",
    } & set(output)
    assert result["match_summary"]["frames_load_status"].eq("loaded").all()
    assert (
        result["match_summary"]["statsbomb_revision"]
        .eq(d.loader.STATSBOMB_REVISION)
        .all()
    )
    assert d.loader.load_events.call_count == d.loader.load_360.call_count == 2
    assert (
        d.read_geometry_diagnostics(tmp_path)["inventory"].iloc[0]["variant_rows"] == 12
    )
    inventory = pd.read_csv(tmp_path / "phase2a_inventory.csv")
    inventory["statsbomb_revision"] = "unknown"
    inventory.to_csv(tmp_path / "phase2a_inventory.csv", index=False)
    with pytest.raises(ValueError, match="revision"):
        d.read_geometry_diagnostics(tmp_path)


@pytest.mark.parametrize(
    "error,status",
    [
        (FileNotFoundError("missing"), "missing"),
        (requests.ConnectionError("offline"), "error"),
    ],
)
def test_missing_resource_is_inventoried_not_fabricated(
    monkeypatch, tmp_path, error, status
):
    configure_loader(monkeypatch, Mock(side_effect=[records(), error]))
    result = d.run_geometry_diagnostics(tmp_path, expected_matches=2)
    assert result["inventory"].iloc[0]["variant_rows"] == 6
    missing = result["match_summary"].iloc[1]
    assert missing["frames_load_status"] == status
    assert pd.isna(missing["original_frames"])


def test_event_failure_aborts(monkeypatch, tmp_path):
    configure_loader(monkeypatch, Mock(return_value=records()))
    monkeypatch.setattr(
        d.loader, "load_events", Mock(side_effect=requests.ConnectionError("offline"))
    )
    with pytest.raises(requests.ConnectionError):
        d.run_geometry_diagnostics(tmp_path, expected_matches=2)
    assert not list(tmp_path.iterdir())


def test_no_frames_writes_only_failure_inventory(monkeypatch, tmp_path):
    configure_loader(monkeypatch, Mock(return_value=[]))
    with pytest.raises(ValueError, match="No original frames"):
        d.run_geometry_diagnostics(tmp_path, expected_matches=2)
    assert [p.name for p in tmp_path.iterdir()] == ["phase2a_match_summary.csv"]

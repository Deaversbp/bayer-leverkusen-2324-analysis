"""Descriptive Phase 2A summaries and a pinned, raw-free season execution."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from leverkusen.data import loader
from leverkusen.spatial.geometry import (
    KEEPER_POLICIES,
    METRICS,
    SUBSETS,
    build_frame_geometry,
)

VARIANT = ["selected_subset", "goalkeeper_policy"]
FRAME = ["match_id", "frame_index"]


def validate_variants(table: pd.DataFrame) -> None:
    """Reject incomplete/duplicated variants; the original ordinal is the key."""
    if table.empty:
        return
    if table.duplicated(FRAME + VARIANT).any():
        raise ValueError("Duplicate original-frame variant")
    if not table.groupby(FRAME).size().eq(6).all():
        raise ValueError("Each original frame requires six variants")
    if (
        not table["selected_subset"].isin(SUBSETS).all()
        or not table["goalkeeper_policy"].isin(KEEPER_POLICIES).all()
    ):
        raise ValueError("Unknown subset or goalkeeper policy")


def _distribution(values: pd.Series) -> dict:
    observed = values.dropna()
    return {
        "rows": len(values),
        "available": len(observed),
        "na": values.isna().sum(),
        "na_percent": 100 * values.isna().mean() if len(values) else None,
        "mean": observed.mean(),
        "std": observed.std(),
        "min": observed.min(),
        "p05": observed.quantile(0.05),
        "p25": observed.quantile(0.25),
        "median": observed.median(),
        "p75": observed.quantile(0.75),
        "p95": observed.quantile(0.95),
        "max": observed.max(),
    }


def summarize_geometry(table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """All-row descriptive distributions; no primary-sample or eligibility filter.

    GK deltas are excluded minus included, paired on original frame and subset.
    Paired availability is explicit. Affected-only summaries require removal of
    at least one keeper/unknown-keeper record, and disclose both removal types.
    Histogram bins serve display only and do not filter measurements.
    """
    validate_variants(table)
    distributions, statuses, histograms, stratified, sensitivities = [], [], [], [], []
    # Shared edges per metric allow comparison of all six observed distributions.
    edges = {
        metric: np.histogram_bin_edges(table[metric].dropna(), bins=30)
        for metric in METRICS
    }
    for variant, group in table.groupby(VARIANT, sort=False):
        context = dict(zip(VARIANT, variant))
        for metric in METRICS:
            distributions.append(
                {**context, "metric": metric, **_distribution(group[metric])}
            )
            for status, count in (
                group[f"{metric}_status"].value_counts(dropna=False).items()
            ):
                statuses.append(
                    {**context, "metric": metric, "status": status, "rows": count}
                )
            counts, bins = np.histogram(group[metric].dropna(), bins=edges[metric])
            for left, right, count in zip(bins[:-1], bins[1:], counts):
                histograms.append(
                    {
                        **context,
                        "metric": metric,
                        "bin_left": left,
                        "bin_right": right,
                        "rows": count,
                    }
                )
        for n, stratum in group.groupby("n_valid_points_used", dropna=False):
            for metric in METRICS:
                stratified.append(
                    {
                        **context,
                        "n_valid_points_used": n,
                        "metric": metric,
                        **_distribution(stratum[metric]),
                    }
                )
    for subset in SUBSETS:
        group = table.loc[table["selected_subset"].eq(subset)]
        included = group.loc[group["goalkeeper_policy"].eq("included")].set_index(FRAME)
        excluded = group.loc[group["goalkeeper_policy"].eq("excluded")].set_index(FRAME)
        included = included.reindex(excluded.index)
        removed = (
            excluded["n_keeper_true_excluded"] + excluded["n_keeper_unknown_excluded"]
        )
        for scope, selection in (
            ("all_pairs", pd.Series(True, index=excluded.index)),
            ("records_removed", removed.gt(0)),
        ):
            for metric in METRICS:
                delta = (excluded[metric] - included[metric]).loc[selection]
                sensitivities.append(
                    {
                        "selected_subset": subset,
                        "scope": scope,
                        "metric": metric,
                        "delta_direction": "excluded_minus_included",
                        **_distribution(delta),
                        "pairs_with_keeper_removal": (
                            excluded.loc[selection, "n_keeper_true_excluded"] > 0
                        ).sum(),
                        "pairs_with_unknown_keeper_removal": (
                            excluded.loc[selection, "n_keeper_unknown_excluded"] > 0
                        ).sum(),
                        "changed_pairs": delta.dropna().ne(0).sum(),
                        "mean_absolute_delta": delta.abs().mean(),
                    }
                )
    frame_rows = table.drop_duplicates(FRAME)
    anomaly_rows = []
    flags = table["measurement_flags"].fillna("").str.split("|").explode()
    for flag in sorted(set(flags) - {""}):
        selected = (
            table["measurement_flags"]
            .fillna("")
            .str.split("|")
            .map(lambda values: flag in values)
        )
        anomaly_rows.append(
            {
                "flag": flag,
                "variant_rows": selected.sum(),
                "original_frames": len(table.loc[selected].drop_duplicates(FRAME)),
            }
        )
    return {
        "metric_summary": pd.DataFrame(distributions),
        "metric_status": pd.DataFrame(statuses),
        "histograms": pd.DataFrame(histograms),
        "by_valid_points": pd.DataFrame(stratified),
        "goalkeeper_sensitivity": pd.DataFrame(sensitivities),
        "anomalies": pd.DataFrame(
            anomaly_rows, columns=["flag", "variant_rows", "original_frames"]
        ),
        "inventory": pd.DataFrame(
            [
                {
                    "original_frames": len(frame_rows),
                    "variant_rows": len(table),
                    "matches_with_frames": frame_rows["match_id"].nunique(),
                }
            ]
        ),
    }


def run_geometry_diagnostics(
    output_dir: Path,
    *,
    team_name: str = "Bayer Leverkusen",
    expected_matches: int = 34,
    progress=None,
) -> dict[str, pd.DataFrame]:
    """Fetch pinned events/360 once per match, writing derived CSVs only.

    Missing/error 360 resources are inventoried without fabricated frames. Event
    failures abort. Unknown-revision legacy raw files are never used. No raw
    coordinates or full frames are serialized into any diagnostic artifact.
    """
    matches = [
        m
        for m in loader.load_matches()
        if team_name
        in (
            m.get("home_team", {}).get("home_team_name"),
            m.get("away_team", {}).get("away_team_name"),
        )
    ]
    identifiers = [m["match_id"] for m in matches]
    if len(matches) != expected_matches or len(set(identifiers)) != expected_matches:
        raise ValueError(f"Expected {expected_matches} unique {team_name} matches")
    tables, inventory = [], []
    for done, match in enumerate(matches, 1):
        match_id = match["match_id"]
        events = loader.load_events(match_id)
        status, error, frames = "loaded", None, None
        try:
            frames = loader.load_360(match_id)
        except FileNotFoundError as exc:
            status, error = "missing", str(exc)
        except (requests.RequestException, ValueError) as exc:
            status, error = "error", f"{type(exc).__name__}: {exc}"
        table = build_frame_geometry(
            match_id, events, frames or [], source_revision=loader.STATSBOMB_REVISION
        )
        validate_variants(table)
        inventory.append(
            {
                "match_id": match_id,
                "events": len(events),
                "original_frames": len(frames) if frames is not None else None,
                "variant_rows": len(table),
                "frames_load_status": status,
                "frames_load_error": error,
                "statsbomb_revision": loader.STATSBOMB_REVISION,
                "source_base_url": loader.BASE_URL,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        if not table.empty:
            tables.append(table)
        if progress:
            progress(done, len(matches), match_id, len(table))
    if not tables:
        # Preserve a useful failure inventory without pretending geometry ran.
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(inventory).to_csv(
            output_dir / "phase2a_match_summary.csv", index=False
        )
        raise ValueError("No original frames available for geometry")
    table = pd.concat(tables, ignore_index=True)
    summaries = summarize_geometry(table)
    summaries["match_summary"] = pd.DataFrame(inventory)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_dir / "phase2a_frame_geometry.csv", index=False)
    for name, summary in summaries.items():
        summary["statsbomb_revision"] = loader.STATSBOMB_REVISION
        summary.to_csv(output_dir / f"phase2a_{name}.csv", index=False)
    return summaries


def read_geometry_diagnostics(output_dir: Path) -> dict[str, pd.DataFrame]:
    """Read compact derived summaries only; reject unknown/mixed source revisions."""
    names = (
        "metric_summary",
        "metric_status",
        "histograms",
        "by_valid_points",
        "goalkeeper_sensitivity",
        "anomalies",
        "inventory",
        "match_summary",
    )
    summaries = {
        name: pd.read_csv(Path(output_dir) / f"phase2a_{name}.csv") for name in names
    }
    for name, table in summaries.items():
        if "statsbomb_revision" not in table or (
            not table.empty
            and not table["statsbomb_revision"].eq(loader.STATSBOMB_REVISION).all()
        ):
            raise ValueError(
                f"Unknown or different source revision in {name}; rerun geometry CLI"
            )
    return summaries

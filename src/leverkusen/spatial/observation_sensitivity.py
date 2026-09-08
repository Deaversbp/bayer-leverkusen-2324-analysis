"""Phase 2B-1 descriptive summaries of existing Phase 2A measurements.

No geometry recomputation, eligibility selection or calibration. Missing metrics
stay missing; each statistic names its observed denominator. All frame flags remain
in the input population, including actor ambiguity and finite out-of-bounds points.
"""

import hashlib
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.spatial.diagnostics import FRAME, VARIANT, validate_variants
from leverkusen.spatial.geometry import SUBSETS

SENSITIVITY_METRICS = (
    "visible_width",
    "visible_depth",
    "convex_hull_area",
    "mean_pairwise_distance",
    "median_pairwise_distance",
    "mean_nearest_neighbor_distance",
)
SUMMARY_NAMES = (
    "metric_by_valid_point_count",
    "metric_by_visible_area",
    "visibility_vs_player_count",
    "goalkeeper_sensitivity",
    "visible_area_bins",
    "player_count_context",
)


def _describe(values: pd.Series) -> dict:
    """Sample std (ddof=1), pandas linear quantiles; NA-only groups stay NA."""
    observed = values.dropna()
    summary = {
        name: None
        for name in ("mean", "median", "std", "p05", "p25", "p75", "p95", "min", "max")
    }
    if len(observed):
        summary.update(
            mean=observed.mean(),
            median=observed.median(),
            std=observed.std(ddof=1),
            min=observed.min(),
            max=observed.max(),
            **{f"p{q:02}": observed.quantile(q / 100) for q in (5, 25, 75, 95)},
        )
    return {
        "frame_count": len(values),
        "denominator": len(observed),
        "na_count": len(values) - len(observed),
        **summary,
    }


def _metric_groups(table: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    rows = []
    for values, group in table.groupby(groups, dropna=False, sort=True):
        context = dict(zip(groups, values))
        for metric in SENSITIVITY_METRICS:
            rows.append({**context, "metric": metric, **_describe(group[metric])})
    return pd.DataFrame(rows)


def summarize_by_point_count(table: pd.DataFrame) -> pd.DataFrame:
    """Summarize exact n, retaining denominator-only rows for undefined metrics."""
    return _metric_groups(table, [*VARIANT, "n_valid_points_used"])


def bin_visible_area(
    table: pd.DataFrame, bins: int = 5
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Shared quantile edges from original frames, each weighted exactly once.

    Intervals are right closed; the first also includes its minimum. Tied values
    stay together; duplicate edges collapse without jitter or ordinal tie breaks.
    Constant observed coverage forms one bin. Missing coverage has its own
    'unavailable' category. Binning changes no values and excludes no frames.
    """
    if not isinstance(bins, int) or isinstance(bins, bool) or bins < 1:
        raise ValueError("bins must be a positive integer")
    if table.groupby(FRAME)["visible_area_fraction"].nunique(dropna=False).gt(1).any():
        raise ValueError("Visible area must agree across original-frame variants")
    frames = table[[*FRAME, "visible_area_fraction"]].drop_duplicates(FRAME).copy()
    observed = frames["visible_area_fraction"].dropna()
    if not all(isfinite(value) for value in observed):
        raise ValueError("Nonfinite observed visible-area fraction")
    edges = (
        np.unique(observed.quantile(np.linspace(0, 1, bins + 1)))
        if len(observed)
        else np.array([])
    )
    bounds = []
    frames["visible_area_bin"] = "unavailable"
    if len(edges):
        if len(edges) == 1:
            codes = pd.Series(0.0, index=observed.index)
            edges = np.repeat(edges, 2)
        else:
            codes = pd.cut(
                observed, edges, labels=False, include_lowest=True, right=True
            )
        frames.loc[observed.index, "visible_area_bin"] = codes.map(
            lambda code: f"B{int(code) + 1}"
        )
        for i, (lower, upper) in enumerate(zip(edges[:-1], edges[1:]), 1):
            label = f"B{i}"
            bounds.append(
                {
                    "visible_area_bin": label,
                    "bin_order": i,
                    "lower": lower,
                    "upper": upper,
                    "lower_inclusive": i == 1,
                    "upper_inclusive": True,
                    "requested_bins": bins,
                    "effective_bins": len(edges) - 1,
                    "original_frame_count": frames["visible_area_bin"].eq(label).sum(),
                }
            )
    if frames["visible_area_bin"].eq("unavailable").any():
        bounds.append(
            {
                "visible_area_bin": "unavailable",
                "bin_order": None,
                "lower": None,
                "upper": None,
                "lower_inclusive": False,
                "upper_inclusive": False,
                "requested_bins": bins,
                "effective_bins": max(len(edges) - 1, 0),
                "original_frame_count": frames["visible_area_bin"]
                .eq("unavailable")
                .sum(),
            }
        )
    labeled = table.merge(
        frames[[*FRAME, "visible_area_bin"]],
        on=FRAME,
        how="left",
        validate="many_to_one",
        sort=False,
    )
    return labeled, pd.DataFrame(bounds)


def summarize_goalkeeper_pairs(table: pd.DataFrame) -> pd.DataFrame:
    """Excluded minus included on match, original ordinal and literal subset.

    'all_frames' and actual 'keeper_removed' scopes have separate denominators.
    Unknown keeper omissions are disclosed separately, never called GK removal.
    Numerical change means exact nonzero delta, without a tolerance decision.
    """
    validate_variants(table)
    rows = []
    for subset in SUBSETS:
        group = table.loc[table["selected_subset"].eq(subset)]
        included = group.loc[group["goalkeeper_policy"].eq("included")].set_index(FRAME)
        excluded = group.loc[group["goalkeeper_policy"].eq("excluded")].set_index(FRAME)
        included = included.reindex(excluded.index)
        removed = excluded["n_keeper_true_excluded"].gt(0)
        unknown_removed = excluded["n_keeper_unknown_excluded"].gt(0)
        for scope, selection in (
            ("all_frames", pd.Series(True, index=excluded.index)),
            ("keeper_removed", removed),
        ):
            for metric in SENSITIVITY_METRICS:
                jointly_defined = (
                    included[metric].notna() & excluded[metric].notna() & selection
                )
                delta = (
                    excluded.loc[jointly_defined, metric]
                    - included.loc[jointly_defined, metric]
                )
                description = _describe(delta)
                rows.append(
                    {
                        "selected_subset": subset,
                        "scope": scope,
                        "metric": metric,
                        "delta_direction": "excluded_minus_included",
                        "total_frames": len(group) // 2,
                        "keeper_removed_frames": removed.sum(),
                        "unknown_keeper_removed_frames": unknown_removed.sum(),
                        "keeper_removal_status_unavailable_frames": excluded[
                            "n_keeper_true_excluded"
                        ]
                        .isna()
                        .sum(),
                        "scope_frames": selection.sum(),
                        "jointly_defined_count": len(delta),
                        "na_pair_count": selection.sum() - len(delta),
                        "jointly_defined_keeper_removed_count": (
                            jointly_defined & removed
                        ).sum(),
                        **{
                            key: description[key]
                            for key in (
                                "mean",
                                "median",
                                "std",
                                "p05",
                                "p25",
                                "p75",
                                "p95",
                                "min",
                                "max",
                            )
                        },
                        "mean_absolute_delta": delta.abs().mean(),
                        "numerically_changed_count": delta.ne(0).sum(),
                        "proportion_numerically_changed": delta.ne(0).mean()
                        if len(delta)
                        else None,
                    }
                )
    return pd.DataFrame(rows)


def summarize_observation_sensitivity(
    table: pd.DataFrame, bins: int = 5
) -> dict[str, pd.DataFrame]:
    """Return compact count/coverage/GK summaries without changing Phase 2A input."""
    if table.empty or table[FRAME + VARIANT].isna().any().any():
        raise ValueError("Expected nonempty geometry with complete original-frame keys")
    validate_variants(table)
    for metric in SENSITIVITY_METRICS:
        if not table[metric].notna().equals(table[f"{metric}_status"].eq("ok")):
            raise ValueError(f"Phase 2A value/status inconsistency: {metric}")
        if not all(isfinite(value) for value in table[metric].dropna()):
            raise ValueError(f"Nonfinite Phase 2A value: {metric}")
    labeled, bounds = bin_visible_area(table, bins)
    coverage_groups = [*VARIANT, "visible_area_bin"]
    joint, point_context = [], []
    for values, group in labeled.groupby(coverage_groups, dropna=False, sort=True):
        joint.append(
            {
                **dict(zip(coverage_groups, values)),
                **_describe(group["n_valid_points_used"]),
            }
        )
    for values, group in table.groupby(VARIANT, sort=True):
        point_context.append(
            {**dict(zip(VARIANT, values)), **_describe(group["n_valid_points_used"])}
        )
    return {
        "metric_by_valid_point_count": summarize_by_point_count(table),
        "metric_by_visible_area": _metric_groups(labeled, coverage_groups),
        "visibility_vs_player_count": pd.DataFrame(joint),
        "goalkeeper_sensitivity": summarize_goalkeeper_pairs(table),
        "visible_area_bins": bounds,
        "player_count_context": pd.DataFrame(point_context),
    }


def run_observation_sensitivity(
    source: Path, output_dir: Path
) -> dict[str, pd.DataFrame]:
    """Read only the existing derived CSV; no network or geometry recomputation."""
    columns = [
        *FRAME,
        *VARIANT,
        "statsbomb_revision",
        "n_valid_points_used",
        "visible_area_fraction",
        "n_keeper_true_excluded",
        "n_keeper_unknown_excluded",
        *SENSITIVITY_METRICS,
        *(f"{metric}_status" for metric in SENSITIVITY_METRICS),
    ]
    source, output_dir = Path(source), Path(output_dir)
    table = pd.read_csv(source, usecols=columns)
    if not table["statsbomb_revision"].eq(STATSBOMB_REVISION).all():
        raise ValueError("Unknown or different Phase 2A source revision")
    summaries = summarize_observation_sensitivity(table)
    with source.open("rb") as file:
        source_hash = hashlib.sha256()
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            source_hash.update(chunk)
    summaries["run_summary"] = pd.DataFrame(
        [
            {
                "source_file": source.name,
                "source_sha256": source_hash.hexdigest(),
                "original_frames": len(table.drop_duplicates(FRAME)),
                "variant_rows": len(table),
                "matches": table["match_id"].nunique(),
                "requested_area_bins": 5,
                "effective_area_bins": summaries["visible_area_bins"][
                    "effective_bins"
                ].max(),
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, summary in summaries.items():
        summary["statsbomb_revision"] = STATSBOMB_REVISION
        summary.to_csv(output_dir / f"phase2b1_{name}.csv", index=False)
    return summaries


def read_observation_sensitivity(output_dir: Path) -> dict[str, pd.DataFrame]:
    """Read compact summaries and provenance, checking upstream source revisions."""
    summaries = {
        name: pd.read_csv(Path(output_dir) / f"phase2b1_{name}.csv")
        for name in (*SUMMARY_NAMES, "run_summary")
    }
    for name, table in summaries.items():
        if (
            "statsbomb_revision" not in table
            or not table["statsbomb_revision"].eq(STATSBOMB_REVISION).all()
        ):
            raise ValueError(f"Unknown/different source revision in {name}")
    return summaries

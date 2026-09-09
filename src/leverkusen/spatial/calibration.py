"""Offline Phase 2B-3 candidate evaluation; never a production eligibility gate.

Every mask is explicit, metric-specific and temporary. Inputs are derived Phase
2A values, never point lists. No rule is loaded from or written to configuration.
"""

from dataclasses import asdict, dataclass
import hashlib
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.spatial.diagnostics import FRAME, VARIANT, validate_variants
from leverkusen.spatial.geometry import METRICS
from leverkusen.spatial.observation_sensitivity import bin_visible_area

PROPOSED = "PROPOSED — REQUIRES HUMAN APPROVAL"
STATS = ("mean", "median", "std", "p05", "p25", "p75", "p95")
MULTIPLICITY = ("visible_player_count", "centroid_x", "centroid_y", *METRICS[6:])
# Phase 2B-2 upper-tail OOB enrichment, not a claim of coordinate invalidity.
OOB_METRICS = ("visible_width", "convex_hull_area", "mean_pairwise_distance")
COUNT_QUANTILES = (5, 25, 50, 75)
AREA_QUANTILES = (20, 40, 60, 80)


@dataclass(frozen=True)
class Candidate:
    candidate: str
    family: str
    role: str
    paired_primary: str
    count_quantile: int | None = None
    area_quantile: int | None = None
    anomaly_policy: str = "none"
    actor_clear: bool = False
    metric_count: bool = False


def candidate_definitions() -> tuple[Candidate, ...]:
    """Fixed review grid; thresholds come from the sample, never metric outcomes."""
    return (
        Candidate("A", "A", "permissive baseline", "A"),
        *(
            Candidate(f"B_q{q:02}", "B", "count comparison", "A", count_quantile=q)
            for q in COUNT_QUANTILES
        ),
        *(
            Candidate(f"C_q{q:02}", "C", "coverage comparison", "A", area_quantile=q)
            for q in AREA_QUANTILES
        ),
        Candidate("D_primary", "D", "proposed primary", "D_primary", actor_clear=True),
        Candidate(
            "D_sensitivity",
            "D",
            "metric-specific sensitivity",
            "D_primary",
            anomaly_policy="metric",
            actor_clear=True,
            metric_count=True,
        ),
        Candidate(
            "E_q25_q20",
            "E",
            "conservative sensitivity",
            "D_primary",
            count_quantile=25,
            area_quantile=20,
            anomaly_policy="all",
            actor_clear=True,
        ),
        Candidate(
            "E_q50_q40",
            "E",
            "stricter conservative sensitivity",
            "D_primary",
            count_quantile=50,
            area_quantile=40,
            anomaly_policy="all",
            actor_clear=True,
        ),
        Candidate("OOB_A", "OOB", "primary retain flagged", "A"),
        Candidate("OOB_B_primary", "OOB", "primary retain flagged", "A"),
        Candidate(
            "OOB_B_sensitivity",
            "OOB",
            "whole-frame OOB sensitivity",
            "OOB_B_primary",
            anomaly_policy="oob",
        ),
        Candidate("OOB_C_primary", "OOB", "primary retain flagged", "A"),
        Candidate(
            "OOB_C_sensitivity",
            "OOB",
            "metric OOB sensitivity",
            "OOB_C_primary",
            anomaly_policy="metric_oob",
        ),
        Candidate(
            "coincidence_sensitivity",
            "coincidence",
            "multiplicity sensitivity",
            "A",
            anomaly_policy="coincidence",
        ),
        Candidate(
            "actor_unique",
            "actor",
            "actor-dependent analysis only",
            "A",
            anomaly_policy="unique_actor",
        ),
    )


def prepare(table: pd.DataFrame) -> pd.DataFrame:
    """Validate derived grain/status and propagate original-frame anomaly flags."""
    if table.empty or table[FRAME + VARIANT].isna().any().any():
        raise ValueError("Nonempty complete original-frame keys required")
    validate_variants(table)
    if not table.statsbomb_revision.eq(STATSBOMB_REVISION).all():
        raise ValueError("Different source revision")
    for metric in METRICS:
        if not table[metric].notna().equals(table[f"{metric}_status"].eq("ok")):
            raise ValueError(f"Value/status mismatch: {metric}")
        if not all(isfinite(value) for value in table[metric].dropna()):
            raise ValueError(f"Nonfinite metric: {metric}")
    for field in ("visible_area_fraction", "actor_status", "event_type"):
        if table.groupby(FRAME)[field].nunique(dropna=False).gt(1).any():
            raise ValueError(f"Frame metadata disagreement: {field}")
    if not all(isfinite(value) for value in table.visible_area_fraction.dropna()):
        raise ValueError("Nonfinite coverage")
    result = table.copy(deep=True)
    original = table.loc[
        table.selected_subset.eq("all_visible") & table.goalkeeper_policy.eq("included")
    ]
    flags = original[FRAME].copy()
    flags["frame_oob"] = original.n_out_of_bounds_points.gt(0)
    flags["frame_coincident"] = original.n_coincident_records.gt(0)
    flags["frame_oob_unknown"] = original.n_out_of_bounds_points.isna()
    flags["frame_coincident_unknown"] = original.n_coincident_records.isna()
    return result.merge(flags, on=FRAME, validate="many_to_one", sort=False)


def empirical_thresholds(table: pd.DataFrame) -> pd.DataFrame:
    """Observed integer count quantiles (higher); linear original-frame area quantiles.

    The grid samples sparse-tail, lower-quartile, median and upper-quartile
    support. Repeated integer cutoffs are disclosed, not jittered. These are
    distribution landmarks, not independently validated stability thresholds.
    """
    rows = []
    for variant, group in table.groupby(VARIANT, sort=True):
        n = group.n_valid_points_used.dropna()
        if n.empty:
            raise ValueError("No count support for a variant")
        for q in COUNT_QUANTILES:
            threshold = int(n.quantile(q / 100, interpolation="higher"))
            rows.append(
                {
                    **dict(zip(VARIANT, variant)),
                    "variable": "count",
                    "quantile": q,
                    "threshold": threshold,
                    "observed_at_threshold": n.eq(threshold).sum(),
                    "observed_below_threshold": n.lt(threshold).sum(),
                    "observed_denominator": len(n),
                    "interpolation": "higher",
                }
            )
    frames = table.drop_duplicates(FRAME)
    area = frames.visible_area_fraction.dropna()
    if area.empty:
        raise ValueError("No observed coverage for candidate grid")
    for q in AREA_QUANTILES:
        threshold = area.quantile(q / 100)
        rows.append(
            {
                "selected_subset": "all",
                "goalkeeper_policy": "both",
                "variable": "area",
                "quantile": q,
                "threshold": threshold,
                "observed_at_threshold": area.eq(threshold).sum(),
                "observed_below_threshold": area.lt(threshold).sum(),
                "observed_denominator": len(area),
                "interpolation": "linear",
            }
        )
    return pd.DataFrame(rows)


def resolve_rule(
    candidate: Candidate, metric: str, variant: tuple, thresholds: pd.DataFrame
) -> dict:
    """Resolve a candidate visibly; hull q25 and NN q05 differ in D sensitivity."""
    if metric not in METRICS:
        raise ValueError("Unknown metric")
    q = candidate.count_quantile
    if candidate.metric_count:
        q = (
            25
            if metric == "convex_hull_area"
            else (5 if metric == "mean_nearest_neighbor_distance" else None)
        )

    def lookup(variable, quantile):
        selected = thresholds.loc[
            thresholds.variable.eq(variable) & thresholds["quantile"].eq(quantile)
        ]
        if variable == "count":
            selected = selected.loc[
                selected.selected_subset.eq(variant[0])
                & selected.goalkeeper_policy.eq(variant[1])
            ]
        if len(selected) != 1:
            raise ValueError("Missing or duplicate empirical threshold")
        return float(selected.threshold.iloc[0])

    policy = candidate.anomaly_policy
    return {
        "minimum_n": lookup("count", q) if q is not None else None,
        "count_quantile": q,
        "minimum_area": lookup("area", candidate.area_quantile)
        if candidate.area_quantile is not None
        else None,
        "exclude_oob": policy in ("oob", "all")
        or (policy in ("metric", "metric_oob") and metric in OOB_METRICS),
        "exclude_coincidence": policy == "all"
        or (policy in ("metric", "coincidence") and metric in MULTIPLICITY),
        "actor_clear": candidate.actor_clear,
        "unique_actor": policy == "unique_actor",
    }


def eligibility(group: pd.DataFrame, metric: str, rule: dict) -> pd.Series:
    """Return a mask only; status is the exact locked mathematical eligibility."""
    mask = group[f"{metric}_status"].eq("ok") & group[metric].notna()
    if rule["minimum_n"] is not None:
        mask &= group.n_valid_points_used.ge(rule["minimum_n"])
    if rule["minimum_area"] is not None:
        mask &= group.visible_area_fraction.ge(rule["minimum_area"])
    for name, field in (
        ("exclude_oob", "frame_oob"),
        ("exclude_coincidence", "frame_coincident"),
    ):
        if rule[name]:
            mask &= ~group[field] & ~group[f"{field}_unknown"]
    if rule["actor_clear"]:
        mask &= group.actor_status.isin(("single", "none"))
    if rule["unique_actor"]:
        mask &= group.actor_status.eq("single") & group.event_join_status.eq("unique")
    return mask


def describe(values: pd.Series) -> dict:
    values = values.dropna()
    if values.empty:
        return dict.fromkeys(STATS, np.nan)
    quantiles = values.quantile([0.05, 0.25, 0.75, 0.95])
    return {
        "mean": values.mean(),
        "median": values.median(),
        "std": values.std(ddof=1),
        **{f"p{int(q * 100):02}": v for q, v in quantiles.items()},
    }


def compare_distributions(full: pd.Series, retained: pd.Series) -> dict:
    a, b = describe(full), describe(retained)
    return {
        **{f"full_{k}": a[k] for k in STATS},
        **{f"retained_{k}": b[k] for k in STATS},
        **{f"delta_{k}": b[k] - a[k] for k in STATS},
        **{
            f"relative_delta_{k}": (b[k] - a[k]) / abs(a[k])
            if pd.notna(a[k]) and a[k] != 0
            else np.nan
            for k in STATS
        },
    }


def composition(group, mask, metric, field):
    """Include zero-retained groups and both inventory/defined denominators."""
    work = pd.DataFrame(
        {
            field: group[field].fillna("unavailable"),
            "defined": group[f"{metric}_status"].eq("ok"),
            "eligible": mask,
        }
    )
    result = (
        work.groupby(field, sort=True)
        .agg(
            population_frames=("defined", "size"),
            defined_frames=("defined", "sum"),
            eligible_frames=("eligible", "sum"),
        )
        .reset_index()
    )
    result["retained_percent"] = 100 * result.eligible_frames / result.population_frames
    result["full_share"] = result.defined_frames / result.defined_frames.sum()
    total = result.eligible_frames.sum()
    result["retained_share"] = result.eligible_frames / total if total else np.nan
    result["share_change_pp"] = 100 * (result.retained_share - result.full_share)
    return result


def summarize_retention(group, mask, metric, match_composition):
    retained = group.loc[mask]
    defined = group[f"{metric}_status"].eq("ok").sum()
    m = match_composition
    result = {
        "population_frames": len(group),
        "mathematically_defined_frames": defined,
        "eligible_frames": int(mask.sum()),
        "eligible_percent": 100 * mask.mean(),
        "eligible_percent_of_defined": 100 * mask.sum() / defined
        if defined
        else np.nan,
        "frames_removed": int((~mask).sum()),
        "filter_removed_defined_frames": int(defined - mask.sum()),
        "affected_matches": int(m.eligible_frames.lt(m.population_frames).sum()),
        "filter_affected_matches": int(m.eligible_frames.lt(m.defined_frames).sum()),
        "retained_matches": int(m.eligible_frames.gt(0).sum()),
        "minimum_retained_per_match": int(m.eligible_frames.min()),
        "median_retained_per_match": m.eligible_frames.median(),
        "minimum_match_retained_percent": m.retained_percent.min(),
        "maximum_match_retained_percent": m.retained_percent.max(),
    }
    for field in ("n_valid_points_used", "visible_area_fraction"):
        result.update(
            {f"retained_{field}_{k}": v for k, v in describe(retained[field]).items()}
        )
    return result


def threshold_stability(distributions, definitions):
    """Successive changes, with no invented stable/not-stable tolerance."""
    rows = []
    for variant_metric, group in distributions.groupby([*VARIANT, "metric"]):
        subset, keeper, metric = variant_metric
        for family in ("B", "C", "E"):
            candidates = [d for d in definitions if d.family == family]
            previous = group.loc[group.candidate.eq("A")].iloc[0]
            for candidate in candidates:
                current = group.loc[group.candidate.eq(candidate.candidate)].iloc[0]
                row = dict(zip([*VARIANT, "metric"], (subset, keeper, metric)))
                row.update(
                    family=family,
                    previous_candidate=previous.candidate,
                    candidate=current.candidate,
                    eligible_frames=current.eligible_frames,
                    successive_frames_removed=previous.eligible_frames
                    - current.eligible_frames,
                )
                for stat in STATS:
                    old, new = previous[f"retained_{stat}"], current[f"retained_{stat}"]
                    row[f"successive_delta_{stat}"] = new - old
                    row[f"successive_relative_change_{stat}"] = (
                        (new - old) / abs(old) if pd.notna(old) and old != 0 else np.nan
                    )
                rows.append(row)
                previous = current
    return pd.DataFrame(rows)


def goalkeeper_comparison(table):
    """Same-frame differences, including centroid/count and actual-removal scope."""
    rows = []
    for subset, group in table.groupby("selected_subset"):
        inc = group.loc[group.goalkeeper_policy.eq("included")].set_index(FRAME)
        exc = group.loc[group.goalkeeper_policy.eq("excluded")].set_index(FRAME)
        inc = inc.reindex(exc.index)
        for metric in METRICS:
            for scope in ("all_frames", "keeper_removed"):
                selection = (
                    exc.n_keeper_true_excluded.gt(0)
                    if scope == "keeper_removed"
                    else pd.Series(True, index=exc.index)
                )
                valid_i = inc[f"{metric}_status"].eq("ok") & selection
                valid_e = exc[f"{metric}_status"].eq("ok") & selection
                delta = (
                    exc.loc[valid_i & valid_e, metric]
                    - inc.loc[valid_i & valid_e, metric]
                )
                rows.append(
                    {
                        "selected_subset": subset,
                        "metric": metric,
                        "scope": scope,
                        "scope_frames": int(selection.sum()),
                        "included_defined": int(valid_i.sum()),
                        "excluded_defined": int(valid_e.sum()),
                        "jointly_defined": len(delta),
                        "lost_defined_on_exclusion": int((valid_i & ~valid_e).sum()),
                        "unknown_keeper_removed_frames": int(
                            (selection & exc.n_keeper_unknown_excluded.gt(0)).sum()
                        ),
                        "delta_direction": "excluded_minus_included",
                        "mean_absolute_delta": delta.abs().mean(),
                        "changed_percent": 100 * delta.ne(0).mean(),
                        **describe(delta),
                    }
                )
    return pd.DataFrame(rows)


def count_coverage_support(table):
    """Joint descriptive strata expose support without estimating adjusted effects."""
    labeled, _ = bin_visible_area(table)
    groups = [*VARIANT, "n_valid_points_used", "visible_area_bin"]
    rows = []
    for key, group in labeled.groupby(groups, sort=True, dropna=False):
        row = {
            **dict(zip(groups, key)),
            "frames": len(group),
            "matches": group.match_id.nunique(),
            "coverage_median": group.visible_area_fraction.median(),
        }
        for metric in METRICS:
            row[f"{metric}_defined"] = group[metric].notna().sum()
            row[f"{metric}_median"] = (
                group[metric].median() if group[metric].notna().any() else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_candidates(table, progress=lambda message: None):
    table = prepare(table)
    thresholds = empirical_thresholds(table)
    definitions = candidate_definitions()
    retention, distributions, rules, matches, events = [], [], [], [], []
    for variant, group in table.groupby(VARIANT, sort=True):
        progress(f"Evaluating {variant[0]} / {variant[1]}")
        context = dict(zip(VARIANT, variant))
        for metric in METRICS:
            baseline = group.loc[group[f"{metric}_status"].eq("ok"), metric]
            for candidate in definitions:
                key = {**context, "metric": metric, "candidate": candidate.candidate}
                rule = resolve_rule(candidate, metric, variant, thresholds)
                rules.append({**key, **rule, "status": PROPOSED})
                mask = eligibility(group, metric, rule)
                mc = composition(group, mask, metric, "match_id")
                ec = composition(group, mask, metric, "event_type")
                matches.append(mc.assign(**key))
                events.append(ec.assign(**key))
                r = summarize_retention(group, mask, metric, mc)
                retention.append({**key, **r})
                distributions.append(
                    {
                        **key,
                        "eligible_frames": r["eligible_frames"],
                        **compare_distributions(baseline, group.loc[mask, metric]),
                    }
                )
    dist = pd.DataFrame(distributions)
    primary_ids = {c.candidate: c.paired_primary for c in definitions}
    dist["paired_primary"] = dist.candidate.map(primary_ids)
    references = dist[
        [
            *VARIANT,
            "metric",
            "candidate",
            "eligible_frames",
            *(f"retained_{s}" for s in STATS),
        ]
    ].rename(
        columns={
            "candidate": "paired_primary",
            "eligible_frames": "primary_eligible_frames",
            **{f"retained_{s}": f"primary_{s}" for s in STATS},
        }
    )
    dist = dist.merge(
        references,
        on=[*VARIANT, "metric", "paired_primary"],
        validate="many_to_one",
        sort=False,
    )
    for stat in STATS:
        dist[f"delta_from_primary_{stat}"] = (
            dist[f"retained_{stat}"] - dist[f"primary_{stat}"]
        )
    ret = pd.DataFrame(retention)
    oob = ret.loc[ret.candidate.str.startswith("OOB_")].merge(
        dist,
        on=[*VARIANT, "metric", "candidate", "eligible_frames"],
        validate="one_to_one",
    )
    return {
        "candidate_definitions": pd.DataFrame([asdict(d) for d in definitions]),
        "empirical_thresholds": thresholds,
        "resolved_rules": pd.DataFrame(rules),
        "candidate_retention": ret,
        "candidate_distribution_effects": dist,
        "threshold_stability": threshold_stability(dist, definitions),
        "filter_event_type_composition": pd.concat(events, ignore_index=True),
        "filter_match_composition": pd.concat(matches, ignore_index=True),
        "goalkeeper_policy_comparison": goalkeeper_comparison(table),
        "count_coverage_support": count_coverage_support(table),
        "oob_policy_comparison": oob,
    }


def sha256(path):
    with Path(path).open("rb") as handle:
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest()


def run_calibration(source, output_dir, progress=print):
    """Read existing derived values only; persist compact aggregate candidates."""
    source, output_dir = Path(source), Path(output_dir)
    digest = sha256(source)
    evidence = []
    for path in sorted(output_dir.glob("phase2b[12]_*.csv")):
        prior = pd.read_csv(path, float_precision="round_trip")
        if (
            "statsbomb_revision" not in prior
            or not prior.statsbomb_revision.eq(STATSBOMB_REVISION).all()
        ):
            raise ValueError(f"Different evidence revision: {path.name}")
        if (
            path.name.endswith("run_summary.csv")
            and not prior.source_sha256.eq(digest).all()
        ):
            raise ValueError(f"Evidence used a different geometry file: {path.name}")
        evidence.append(
            {
                "source_file": path.name,
                "source_sha256": sha256(path),
                "rows": len(prior),
            }
        )
    if not {"phase2b1_run_summary.csv", "phase2b2_run_summary.csv"}.issubset(
        {r["source_file"] for r in evidence}
    ):
        raise ValueError("Both prior diagnostic run summaries required")
    columns = [
        *FRAME,
        *VARIANT,
        "statsbomb_revision",
        "event_type",
        "event_join_status",
        "actor_status",
        "n_valid_points_used",
        "visible_area_fraction",
        "n_out_of_bounds_points",
        "n_coincident_records",
        "n_keeper_true_excluded",
        "n_keeper_unknown_excluded",
        *METRICS,
        *(f"{m}_status" for m in METRICS),
    ]
    table = pd.read_csv(source, usecols=columns, float_precision="round_trip")
    summaries = evaluate_candidates(table, progress)
    summaries["evidence_inventory"] = pd.DataFrame(evidence)
    summaries["run_summary"] = pd.DataFrame(
        [
            {
                "source_file": source.name,
                "source_sha256": digest,
                "original_frames": len(table.drop_duplicates(FRAME)),
                "variant_rows": len(table),
                "matches": table.match_id.nunique(),
                "candidate_count": len(candidate_definitions()),
                "status": PROPOSED,
                "permanent_configuration_changed": False,
                "csv_float_precision": "round_trip",
            }
        ]
    )
    # Source-backed narrative matrix is versioned, while generated outputs are ignored.
    matrix_path = (
        Path(__file__).resolve().parents[3]
        / "docs/phase2b3_metric_calibration_matrix.csv"
    )
    summaries["metric_calibration_matrix"] = pd.read_csv(matrix_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, summary in summaries.items():
        summary["statsbomb_revision"] = STATSBOMB_REVISION
        summary.to_csv(output_dir / f"phase2b3_{name}.csv", index=False)
    return summaries


def read_calibration(output_dir):
    paths = sorted(Path(output_dir).glob("phase2b3_*.csv"))
    if not paths:
        raise FileNotFoundError("Run python scripts/calibration.py first")
    results = {p.stem.removeprefix("phase2b3_"): pd.read_csv(p) for p in paths}
    for name, table in results.items():
        if (
            "statsbomb_revision" not in table
            or not table.statsbomb_revision.eq(STATSBOMB_REVISION).all()
        ):
            raise ValueError(f"Different calibration revision: {name}")
    return results

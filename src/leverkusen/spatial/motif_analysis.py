"""Fixed symbolic-motif descriptions and match-clustered adjusted contrasts."""

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from leverkusen.sequences.multi_action import LENGTHS, SCOPES, motif_labels, window_scope
from leverkusen.spatial.progression_change import RESPONSES


def describe(values, name):
    values = values.dropna()
    return {f"{name}_N": len(values), f"{name}_median": values.median(),
            f"{name}_q25": values.quantile(.25), f"{name}_q75": values.quantile(.75),
            f"{name}_iqr": values.quantile(.75) - values.quantile(.25), f"{name}_mean": values.mean()}


def group_summary(group):
    result = dict(N=len(group), matches=group.match_id.nunique(),
                  spells=len(group[["match_id", "attacking_control_spell_id"]].drop_duplicates()))
    for col in ("total_progression", "duration_seconds"):
        result.update(describe(group[col], col))
    for response in RESPONSES:
        values = group.loc[group[f"net_{response}_status"].eq("ok"), f"net_{response}"]
        result.update(describe(values, f"net_{response}"))
    for i in (1, 2, 3):
        col = f"leg_{i}_delta_opp_centroid_x"
        result.update(describe(group.loc[group[f"{col}_status"].eq("ok"), col], col))
    return result


def motif_summary(data, *, system, scope="all"):
    field = "action_type_motif" if system == "action" else "direction_profile"
    rows = []
    for length in LENGTHS:
        population = data[data.window_length.eq(length) & window_scope(data, scope)]
        for motif in motif_labels(length, system):
            selected = population[population[field].eq(motif)]
            rows.append(dict(window_length=length, motif_system=system, motif=motif, scope=scope,
                **group_summary(selected), share_of_windows=len(selected) / len(population) if len(population) else np.nan,
                scope_windows=len(population)))
    return pd.DataFrame(rows)


def fit_clustered(design, y, matches):
    """General-design OLS CR1, matching Phase 4A's one-way match convention.

    No p-values. Coefficients are descriptive contrasts, not causal estimates.
    Rank-deficient designs fail explicitly rather than imposing a pseudo-solution.
    """
    x, y = np.asarray(design, float), np.asarray(y, float)
    n, p = x.shape
    g = len(np.unique(matches))
    if n <= p or np.linalg.matrix_rank(x) < p:
        return None
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    total = ((y - y.mean()) ** 2).sum()
    se = np.full(p, np.nan)
    if g > 1:
        bread = np.linalg.inv(x.T @ x)
        scores = pd.DataFrame(x * residual[:, None]).groupby(np.asarray(matches), sort=True).sum().to_numpy()
        covariance = bread @ (scores.T @ scores) @ bread * (g / (g - 1)) * ((n - 1) / (n - p))
        se = np.sqrt(np.maximum(0, np.diag(covariance)))
    margin = student_t.ppf(.975, g - 1) * se if g > 1 else se
    return dict(beta=beta, se=se, low=beta-margin, high=beta+margin,
                r_squared=1 - (residual @ residual) / total if total else np.nan,
                N=n, clusters=g, parameters=p)


def adjusted_centroid(data):
    rows = []
    for length in LENGTHS:
        for scope in SCOPES:
            group = data[data.window_length.eq(length) & window_scope(data, scope) & data.net_opp_centroid_x_status.eq("ok")]
            present = [m for m in motif_labels(length) if group.action_type_motif.eq(m).any()]
            if not present:
                continue
            reference = present[0]  # PP/PPP when present; explicit fallback otherwise.
            for model in ("progression_only", "progression_plus_motif", "progression_motif_start_x"):
                # Starting-x is a fixed supplementary context model, not feature selection.
                if model == "progression_motif_start_x" and scope != "all":
                    continue
                columns = {"intercept": np.ones(len(group)), "total_progression": group.total_progression.to_numpy()}
                if model != "progression_only":
                    columns.update({f"motif_{m}": group.action_type_motif.eq(m).to_numpy().astype(float) for m in present[1:]})
                if model == "progression_motif_start_x":
                    columns["first_action_start_x"] = group.first_action_start_x.to_numpy()
                design = pd.DataFrame(columns)
                fit = fit_clustered(design, group.net_opp_centroid_x, group.match_id)
                for i, term in enumerate(columns):
                    rows.append(dict(window_length=length, scope=scope, model=model, reference_motif=reference,
                        term=term, coefficient=fit["beta"][i] if fit else np.nan,
                        cluster_se=fit["se"][i] if fit else np.nan,
                        ci_low=fit["low"][i] if fit else np.nan, ci_high=fit["high"][i] if fit else np.nan,
                        r_squared=fit["r_squared"] if fit else np.nan, N=len(group),
                        matches=group.match_id.nunique(), status="ok" if fit else "insufficient_or_rank_deficient",
                        motif_N=int(group.action_type_motif.eq(term[6:]).sum()) if term.startswith("motif_") else np.nan))
    return pd.DataFrame(rows)


def analyze_windows(data):
    data = data.sort_values(["window_length", "match_id", "first_anchor_source_order"]).reset_index(drop=True)
    action = motif_summary(data, system="action")
    direction = motif_summary(data, system="direction")
    sensitivity = pd.concat([motif_summary(data, system=system, scope=scope)
                             for system in ("action", "direction") for scope in SCOPES[1:]], ignore_index=True)
    baseline = pd.concat([action, direction])[['window_length', 'motif_system', 'motif', 'N', 'net_opp_centroid_x_median']]
    sensitivity = sensitivity.merge(baseline.rename(columns={"N": "primary_N", "net_opp_centroid_x_median": "primary_centroid_median"}),
        on=["window_length", "motif_system", "motif"], validate="many_to_one")
    sensitivity["centroid_median_difference"] = sensitivity.net_opp_centroid_x_median - sensitivity.primary_centroid_median
    sensitivity["centroid_sign_preserved"] = np.where(sensitivity.net_opp_centroid_x_N.gt(0),
        np.sign(sensitivity.net_opp_centroid_x_median) == np.sign(sensitivity.primary_centroid_median), None)
    support = []
    for length in LENGTHS:
        for motif in motif_labels(length):
            group = data[data.window_length.eq(length) & data.action_type_motif.eq(motif)]
            counts = group.groupby("match_id").size()
            support.append(dict(window_length=length, motif=motif, N=len(group), matches=len(counts),
                median_windows_per_represented_match=counts.median(), minimum_windows_per_represented_match=counts.min(),
                maximum_windows_per_represented_match=counts.max(),
                control_spells=len(group[["match_id", "attacking_control_spell_id"]].drop_duplicates())))
    return dict(motif_summary=action, direction_profile_summary=direction,
        centroid_adjusted_summary=adjusted_centroid(data), sequence_sensitivity=sensitivity,
        motif_match_support=pd.DataFrame(support))

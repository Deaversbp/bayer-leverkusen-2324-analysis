"""Descriptive Phase 2A plots from compact derived summary tables."""

import matplotlib.pyplot as plt

from leverkusen.spatial.geometry import METRICS, SUBSETS, KEEPER_POLICIES


def plot_distributions(histograms):
    """Shared-bin counts, with every literal subset and keeper policy shown."""
    figure, axes = plt.subplots(3, 3, figsize=(15, 11), constrained_layout=True)
    for metric, axis in zip(METRICS, axes.flat):
        for subset, color in zip(SUBSETS, ("#0072B2", "#D55E00", "#009E73")):
            for policy, style in zip(KEEPER_POLICIES, ("-", "--")):
                values = histograms.loc[
                    histograms["metric"].eq(metric)
                    & histograms["selected_subset"].eq(subset)
                    & histograms["goalkeeper_policy"].eq(policy)
                ]
                axis.stairs(
                    values["rows"],
                    [*values["bin_left"], values["bin_right"].iloc[-1]],
                    color=color,
                    linestyle=style,
                    label=f"{subset} / {policy}",
                )
        axis.set(
            title=metric.replace("_", " "),
            ylabel="Variant rows",
            xlabel="Records"
            if metric == "visible_player_count"
            else "Native units²"
            if metric == "convex_hull_area"
            else "Native units",
        )
    axes.flat[0].legend(fontsize=7)
    figure.suptitle("Observed geometry distributions — all diagnostic rows")
    return figure


def plot_by_valid_points(stratified):
    """Show descriptive means by exact selected n; no visibility cutoff."""
    figure, axes = plt.subplots(3, 3, figsize=(15, 11), constrained_layout=True)
    for metric, axis in zip(METRICS, axes.flat):
        for subset, color in zip(SUBSETS, ("#0072B2", "#D55E00", "#009E73")):
            for policy, style in zip(KEEPER_POLICIES, ("-", "--")):
                values = stratified.loc[
                    stratified["metric"].eq(metric)
                    & stratified["selected_subset"].eq(subset)
                    & stratified["goalkeeper_policy"].eq(policy)
                ].sort_values("n_valid_points_used")
                axis.plot(
                    values["n_valid_points_used"],
                    values["mean"],
                    style,
                    color=color,
                    label=f"{subset} / {policy}",
                )
        axis.set(
            title=metric.replace("_", " "),
            xlabel="Selected valid records (n)",
            ylabel="Observed mean",
        )
    axes.flat[0].legend(fontsize=7)
    figure.suptitle(
        "Geometry by selected point count — descriptive means; see table for denominators"
    )
    return figure


def plot_goalkeeper_sensitivity(sensitivity):
    """Paired mean deltas among frames where a record was removed."""
    figure, axes = plt.subplots(3, 3, figsize=(15, 10), constrained_layout=True)
    for metric, axis in zip(METRICS, axes.flat):
        values = sensitivity.loc[
            sensitivity["metric"].eq(metric)
            & sensitivity["scope"].eq("records_removed")
        ]
        axis.bar(
            values["selected_subset"],
            values["mean"],
            color=["#0072B2", "#D55E00", "#009E73"],
        )
        axis.axhline(0, color="black", linewidth=0.6)
        axis.set(title=metric.replace("_", " "), ylabel="Mean paired delta")
        axis.tick_params(axis="x", labelrotation=20)
    figure.suptitle(
        "Excluded minus included — paired defined results where records were removed"
    )
    return figure

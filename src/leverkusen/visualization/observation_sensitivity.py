"""Three bounded Phase 2B-1 figures from derived summary tables only."""

import matplotlib.pyplot as plt

from leverkusen.spatial.geometry import KEEPER_POLICIES, SUBSETS

MAJOR_METRICS = (
    "visible_width",
    "visible_depth",
    "convex_hull_area",
    "mean_pairwise_distance",
    "mean_nearest_neighbor_distance",
)
COLORS = ("#0072B2", "#D55E00", "#009E73")


def _central_tendency(table, x, title, xlabel, ticks=None):
    figure, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    for metric, axis in zip(MAJOR_METRICS, axes.flat):
        for subset, color in zip(SUBSETS, COLORS):
            for policy, style in zip(KEEPER_POLICIES, ("-", "--")):
                values = table.loc[
                    table["metric"].eq(metric)
                    & table["selected_subset"].eq(subset)
                    & table["goalkeeper_policy"].eq(policy)
                ].sort_values(x)
                axis.plot(
                    values[x],
                    values["median"],
                    linestyle=style,
                    marker="o",
                    markersize=3,
                    color=color,
                    label=f"{subset} / {policy}",
                )
        axis.set(
            title=metric.replace("_", " "),
            xlabel=xlabel,
            ylabel="Observed median (native units²)"
            if metric == "convex_hull_area"
            else "Observed median (native units)",
        )
        if ticks is not None:
            axis.set_xticks(ticks[0], ticks[1])
    axes.flat[-1].axis("off")
    axes.flat[-1].legend(
        *axes.flat[0].get_legend_handles_labels(), loc="center", fontsize=10
    )
    figure.suptitle(
        title + "\nAll diagnostic rows; metric denominators in supporting tables"
    )
    return figure


def plot_count_dependence(summary):
    return _central_tendency(
        summary,
        "n_valid_points_used",
        "A — Geometry by selected valid-player count",
        "Selected valid records (n)",
    )


def plot_visible_area_dependence(summary, bounds):
    ordered = bounds.dropna(subset=["bin_order"]).sort_values("bin_order")
    values = summary.merge(
        ordered[["visible_area_bin", "bin_order"]],
        on="visible_area_bin",
        how="inner",
        validate="many_to_one",
    )
    return _central_tendency(
        values,
        "bin_order",
        "B — Geometry by visible-area coverage",
        "Shared original-frame quantile bin",
        (ordered["bin_order"], ordered["visible_area_bin"]),
    )


def plot_keeper_deltas(summary):
    """Median dot, IQR thick line, p05–p95 thin line; two explicit paired scopes."""
    figure, axes = plt.subplots(2, 2, figsize=(15, 8), constrained_layout=True)
    for metric, axis in zip(MAJOR_METRICS[1:], axes.flat):
        labels, positions = [], []
        for i, (subset, color) in enumerate(zip(SUBSETS, COLORS)):
            for j, scope in enumerate(("all_frames", "keeper_removed")):
                row = summary.loc[
                    summary["selected_subset"].eq(subset)
                    & summary["metric"].eq(metric)
                    & summary["scope"].eq(scope)
                ].iloc[0]
                position = i * 3 + j
                axis.hlines(position, row["p05"], row["p95"], color=color, linewidth=1)
                axis.hlines(position, row["p25"], row["p75"], color=color, linewidth=5)
                axis.plot(row["median"], position, "o", color=color, markersize=5)
                positions.append(position)
                labels.append(
                    f"{subset} / {'all frames' if j == 0 else 'keeper removed'}"
                )
        axis.set_yticks(positions, labels, fontsize=8)
        axis.invert_yaxis()
        axis.axvline(0, color="black", linewidth=0.6, linestyle="--")
        axis.set(
            title=metric.replace("_", " "),
            xlabel="Excluded − included (native units²)"
            if metric == "convex_hull_area"
            else "Excluded − included (native units)",
        )
    figure.suptitle(
        "C — Paired goalkeeper sensitivity\nDot: median; thick line: p25–p75; thin line: p05–p95; jointly defined pairs only"
    )
    return figure

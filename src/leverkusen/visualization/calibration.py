"""Review plots from compact Phase 2B-3 candidate summaries only."""

import matplotlib.pyplot as plt


def plot_calibration_tradeoffs(retention, distributions):
    """All-visible outfield example; remaining variants stay in review tables."""
    data = retention.merge(
        distributions,
        on=[
            "selected_subset",
            "goalkeeper_policy",
            "metric",
            "candidate",
            "eligible_frames",
        ],
        validate="one_to_one",
    )
    data = data.loc[
        data.selected_subset.eq("all_visible") & data.goalkeeper_policy.eq("excluded")
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for axis, metric, title in zip(
        axes,
        ("convex_hull_area", "mean_nearest_neighbor_distance"),
        ("Observed hull area", "Observed nearest-neighbor distance"),
    ):
        group = data.loc[data.metric.eq(metric)]
        for prefix, label, color in (
            ("B_", "Count landmarks", "#2667a0"),
            ("C_", "Coverage landmarks", "#d46b25"),
        ):
            points = group.loc[group.candidate.str.startswith(prefix)]
            axis.plot(
                points.eligible_percent,
                100 * points.relative_delta_median,
                "o-",
                color=color,
                label=label,
            )
            for row in points.itertuples():
                axis.annotate(
                    row.candidate.split("_")[1],
                    (row.eligible_percent, 100 * row.relative_delta_median),
                    xytext=(4, 5),
                    textcoords="offset points",
                    fontsize=8,
                )
        for name, marker, color in (
            ("D_primary", "s", "#333333"),
            ("D_sensitivity", "D", "#a12643"),
        ):
            point = group.loc[group.candidate.eq(name)].iloc[0]
            axis.scatter(
                point.eligible_percent,
                100 * point.relative_delta_median,
                marker=marker,
                color=color,
                label=name.replace("_", " "),
            )
        axis.axhline(0, color="#999999", linewidth=0.7)
        axis.set(
            title=title,
            xlabel="Original frames retained (%)",
            ylabel="Median change from A (%)",
            xlim=(0, 105),
        )
        axis.grid(alpha=0.2)
    axes[0].legend(fontsize=8)
    fig.suptitle(
        "Phase 2B-3 candidates: all-visible, keepers excluded\n"
        "PROPOSED — REQUIRES HUMAN APPROVAL; marginal distributions"
    )
    return fig


def plot_threshold_stability(stability):
    data = stability.loc[
        stability.selected_subset.eq("all_visible")
        & stability.goalkeeper_policy.eq("excluded")
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for axis, metric, title in zip(
        axes,
        ("convex_hull_area", "mean_nearest_neighbor_distance"),
        ("Observed hull area", "Observed nearest-neighbor distance"),
    ):
        for family, label in (
            ("B", "Count q05 / q25 / q50 / q75"),
            ("C", "Coverage q20 / q40 / q60 / q80"),
        ):
            points = data.loc[data.metric.eq(metric) & data.family.eq(family)]
            axis.plot(
                range(1, 5),
                100 * points.successive_relative_change_median,
                "o-",
                label=label,
            )
        axis.axhline(0, color="#999999", linewidth=0.7)
        axis.set(
            title=title,
            xlabel="Successive landmark (first versus A)",
            ylabel="Successive median change (%)",
            xticks=range(1, 5),
        )
        axis.grid(alpha=0.2)
    axes[0].legend(fontsize=8)
    fig.suptitle("No stable/not-stable tolerance is selected")
    return fig

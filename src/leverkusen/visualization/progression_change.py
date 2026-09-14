"""Six compact Phase 4A figures of partial-observation associations."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from leverkusen.visualization.style import ACTION_COLOR, OPPONENT_COLOR, PITCH_BACKGROUND

LABELS = {
    "centroid_x": "Visible opponent centroid x",
    "centroid_y": "Visible opponent centroid y",
    "visible_width": "Visible opponent width",
    "visible_depth": "Visible opponent depth",
    "convex_hull_area": "Observed outfield convex-hull footprint",
    "mean_pairwise_distance": "Mean opponent pairwise spacing",
    "visible_player_count": "Visible opponent record count",
}


def write_figures(data, tables, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": PITCH_BACKGROUND, "axes.facecolor": PITCH_BACKGROUND})

    def save(fig, stem, caption):
        fig.text(.5, .02, caption, ha="center", va="bottom", fontsize=9)
        fig.tight_layout(rect=(0, .08, 1, .95))
        path = output / f"phase4a_{stem}.png"
        fig.savefig(path, dpi=180, metadata={"Software": "Leverkusen Phase 4A"})
        plt.close(fig)
        paths.append(path)

    def trend(ax, action, metric, *, raw=True):
        response = f"opp_{metric}"
        g = data[data.action_type.eq(action) & data[f"delta_{response}_status"].eq("ok")]
        b = tables["descriptive_quantiles"]
        b = b[b.action_type.eq(action) & b.response_metric.eq(response)]
        if raw:
            ax.scatter(g.action_delta_x, g[f"delta_{response}"], s=5, alpha=.035, color=OPPONENT_COLOR, rasterized=True)
        ax.plot(b.progression_median, b.response_median, "o-", color=ACTION_COLOR, lw=2, label="Decile medians")
        ax.fill_between(b.progression_median, b.response_q25, b.response_q75, color=ACTION_COLOR, alpha=.12, label="Within-decile response IQR")
        ax.axhline(0, color="#777777", lw=.7)
        ax.axvline(0, color="#777777", lw=.7)
        ax.set_title(f"{action} · N={len(g):,}")
        ax.set_xlabel("Action delta x (StatsBomb units)")
        ax.set_ylabel("Next minus FROM: " + LABELS[metric].lower())
        return b

    for action in ("Pass", "Carry"):
        fig, (ax, counts) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [4, 1]})
        b = trend(ax, action, "centroid_x")
        ax.legend(loc="upper left", fontsize=9)
        counts.bar(b.progression_decile, b.N, color=ACTION_COLOR, alpha=.7)
        counts.set_xticks(b.progression_decile)
        counts.set_xlabel(f"Descriptive {action} progression decile (ties may reduce bin count)")
        counts.set_ylabel("Raw N")
        for r in b.itertuples():
            counts.text(r.progression_decile, r.N, str(r.N), ha="center", va="bottom", fontsize=8)
        counts.set_ylim(0, b.N.max() * 1.28)
        fig.suptitle(f"{action} progression and the next visible opponent centroid", fontsize=15)
        save(fig, f"{action.lower()}_centroid", "Event-aligned partial observations · all eligible gaps · deciles are presentation aids, not thresholds")

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for i, action in enumerate(("Pass", "Carry")):
        for j, metric in enumerate(("visible_width", "visible_depth", "convex_hull_area")):
            trend(axes[i, j], action, metric)
            axes[i, j].set_ylabel(f"Delta {metric.replace('_', ' ')}" + (" (units²)" if j == 2 else " (units)"))
    fig.suptitle("Progression and observed opponent extent changes", fontsize=16)
    save(fig, "opponent_extent", "Hull footprint is secondary · no complete-team area interpretation · shared action-specific deciles; raw bin N in the quantile CSV")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, action in zip(axes, ("Pass", "Carry")):
        trend(ax, action, "mean_pairwise_distance")
        ax.set_ylabel("Delta mean pairwise distance (units)")
    fig.suptitle("Progression and observed opponent spacing", fontsize=16)
    save(fig, "opponent_spacing", "One representative spacing measure · correlated metrics remain in the tables · gold: decile median and response IQR")

    metrics = ("centroid_x", "centroid_y", "visible_width", "visible_depth", "mean_pairwise_distance", "visible_player_count")
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    main = tables["metric_summary"]
    for ax, metric in zip(axes.flat, metrics):
        for y, action in enumerate(("Pass", "Carry")):
            r = main[main.action_type.eq(action) & main.response_metric.eq(f"opp_{metric}")].iloc[0]
            ax.errorbar(r.slope, y, xerr=np.array([[r.slope-r.ci_low], [r.ci_high-r.slope]]), fmt="o", capsize=4, color=OPPONENT_COLOR)
            ax.annotate(f"{r.slope:.3f}", (r.slope, y), xytext=(0, 10), textcoords="offset points", ha="center")
        ax.axvline(0, color="#888888", lw=.8)
        ax.set_yticks([0, 1], ["Pass", "Carry"])
        ax.set_ylim(-.6, 1.6)
        ax.set_title(LABELS[metric])
        ax.set_xlabel("Response units per action x-unit")
    fig.suptitle("Pass and Carry: descriptive regression slopes", fontsize=16)
    save(fig, "coefficient_comparison", "95% match-clustered CR1 intervals, t(G−1) · separate panel scales · associations, not causal effects")

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    sensitivity = tables["gap_sensitivity"]
    for i, action in enumerate(("Pass", "Carry")):
        for j, metric in enumerate(("centroid_x", "visible_depth", "mean_pairwise_distance")):
            ax = axes[i, j]
            for x, scope in enumerate(("all", "gap_le_5", "gap_le_3")):
                table = main if scope == "all" else sensitivity
                r = table[table.action_type.eq(action) & table.response_metric.eq(f"opp_{metric}") & table.gap_scope.eq(scope)].iloc[0]
                ax.errorbar(x, r.slope, yerr=np.array([[r.slope-r.ci_low], [r.ci_high-r.slope]]), fmt="o", capsize=4, color=ACTION_COLOR)
                ax.annotate(f"N={r.N:,}", (x, r.slope), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=8)
            ax.axhline(0, color="#888888", lw=.8)
            ax.set_xticks([0, 1, 2], ["All gaps", "≤5 seconds", "≤3 seconds"])
            ax.set_xlim(-.6, 2.6)
            ax.margins(y=.3)
            ax.set_title(f"{action}: {metric.replace('_', ' ')}")
            ax.set_ylabel("Slope per action x-unit")
    fig.suptitle("Do associations persist at shorter observation gaps?", fontsize=16)
    save(fig, "gap_sensitivity", "95% match-clustered intervals · gap restrictions are sensitivity comparisons, not quality thresholds")
    return paths

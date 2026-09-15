"""Three compact Phase 5B association figures with match-clustered intervals."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullLocator
import numpy as np

from leverkusen.spatial.danger_analysis import PRIMARY
from leverkusen.visualization.style import ACTION_COLOR, OPPONENT_COLOR, PITCH_BACKGROUND


def write_figures(summary, sensitivity, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = []
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": PITCH_BACKGROUND, "axes.facecolor": PITCH_BACKGROUND})
    colors = {"Pass": OPPONENT_COLOR, "Carry": ACTION_COLOR}

    def save(fig, name, caption):
        fig.text(.5, .02, caption, ha="center", va="bottom", fontsize=9)
        fig.tight_layout(rect=(0, .10, 1, .95))
        path = output / f"phase5b_{name}.png"
        fig.savefig(path, dpi=180, metadata={"Software": "Leverkusen Phase 5B"})
        plt.close(fig)
        paths.append(path)

    bins = summary[summary.record_type.eq("quartile") & summary.spatial_metric.eq(PRIMARY)]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for action in ("Pass", "Carry"):
        rows = bins[bins.action_type.eq(action)].sort_values("quartile")
        ax.plot(rows.quartile, rows.box_entry_rate * 100, "o-", label=action, color=colors[action])
    ax.set(xticks=[1, 2, 3, 4], xlabel="Opponent-centroid change quartile within action type",
           ylabel="10-second box-entry prevalence (%)", title="Observed spatial change and near-term box entry")
    ax.legend()
    save(fig, "centroid_quartiles", "Inclusive TO outcomes · action-specific presentation bins, not tactical thresholds · unadjusted rates")

    models = summary[summary.record_type.eq("model") & summary.spatial_metric.eq(PRIMARY)
                     & summary.outcome.eq("box_entry") & summary.model.eq("adjusted")]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for y, action in enumerate(("Pass", "Carry")):
        row = models[models.action_type.eq(action)].iloc[0]
        if row.model_status == "ok":
            ax.errorbar(row.odds_ratio_1sd, y, xerr=np.array([[row.odds_ratio_1sd - row.or_1sd_ci_low],
                         [row.or_1sd_ci_high - row.odds_ratio_1sd]]), fmt="o", color=colors[action], capsize=4)
            ax.annotate(f"OR {row.odds_ratio_1sd:.2f} [{row.or_1sd_ci_low:.2f}, {row.or_1sd_ci_high:.2f}]",
                        (row.odds_ratio_1sd, y), xytext=(0, 13), textcoords="offset points", ha="center")
        else:
            ax.text(1, y, "Model unstable", ha="center")
    ax.axvline(1, color="#777777", linewidth=.8)
    ax.set(xscale="log", yticks=[0, 1], yticklabels=["Pass", "Carry"], ylim=(-.6, 1.6),
           xlabel="Adjusted odds ratio per +1 SD opponent-centroid x change",
           title="Opponent-centroid displacement and 10-second box entry")
    ax.set_xticks([1, 1.1, 1.2, 1.3, 1.4])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.xaxis.set_minor_locator(NullLocator())
    save(fig, "adjusted_centroid", "Controls: action delta x, starting x, observation gap · 95% match-cluster CR1 t(33) intervals")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax, outcome, label in zip(axes, ("box_entry", "shot"), ("Box entry", "Shot")):
        rows = sensitivity[sensitivity.scope.eq("all") & sensitivity.outcome.eq(outcome)]
        for offset, action in zip((-.08, .08), ("Pass", "Carry")):
            selected = rows[rows.action_type.eq(action) & rows.model_status.eq("ok")].sort_values("horizon")
            ax.errorbar(selected.horizon + offset, selected.odds_ratio_1sd,
                        yerr=np.vstack([selected.odds_ratio_1sd - selected.or_1sd_ci_low,
                                        selected.or_1sd_ci_high - selected.odds_ratio_1sd]),
                        fmt="o-", capsize=4, label=action, color=colors[action])
        ax.axhline(1, color="#777777", linewidth=.8)
        ax.set(xticks=[5, 10, 15], xlabel="Outcome horizon (seconds; 10s primary)",
               ylabel="Adjusted odds ratio per +1 SD", title=label, yscale="log")
        ax.set_yticks([1, 1.2, 1.4, 1.6] if outcome == "box_entry" else [1, 1.5, 2, 2.5])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.legend()
    fig.suptitle("Centroid association across the pre-specified horizons")
    save(fig, "horizon_sensitivity", "95% match-cluster intervals · fixed full-action SD across horizons · sparse Shot outcomes warrant caution")
    return paths

"""Four bounded Phase 5C motif-effectiveness figures."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullLocator
import numpy as np

from leverkusen.sequences.multi_action import motif_labels
from leverkusen.visualization.style import ACTION_COLOR, OPPONENT_COLOR, PITCH_BACKGROUND


def write_figures(summary, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": PITCH_BACKGROUND, "axes.facecolor": PITCH_BACKGROUND})
    paths = []

    def save(fig, name, caption):
        fig.text(.5, .02, caption, ha="center", va="bottom", fontsize=9)
        fig.tight_layout(rect=(0, .09, 1, .95))
        path = output / f"phase5c_{name}.png"
        fig.savefig(path, dpi=180, metadata={"Software": "Leverkusen Phase 5C"})
        plt.close(fig)
        paths.append(path)

    def rows(kind, length):
        selected = summary[summary.record_type.eq(kind) & summary.window_length.eq(length)
                           & summary.outcome.eq("box_entry")]
        return selected.set_index("motif").loc[motif_labels(length)]

    raw, adjusted = rows("raw_motif", 2), rows("model", 2)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(raw.index, raw.box_entry_rate * 100, color=OPPONENT_COLOR, width=.65)
    for i, r in enumerate(raw.itertuples()):
        ax.text(i, r.box_entry_rate * 100 + .3, f"{r.box_entry_rate:.2%}\nN={int(r.N):,}", ha="center")
    ax.set(ylim=(0, 15), ylabel="10-second box-entry rate (%)", xlabel="Locked two-action motif",
           title="Raw box-entry rates across two-action windows")
    save(fig, "two_action_raw", "Overlapping fixed windows · inclusive terminal-anchor outcomes · raw rates are not an adjusted ranking")

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, r in enumerate(adjusted.itertuples()):
        if r.model_status == "ok":
            ax.errorbar(r.odds_ratio, i, xerr=np.array([[r.odds_ratio-r.or_ci_low], [r.or_ci_high-r.odds_ratio]]),
                        fmt="o", capsize=4, color=ACTION_COLOR)
    ax.axvline(1, color="#777777", lw=.8)
    ax.set(yticks=range(4), yticklabels=adjusted.index, ylim=(-.5, 3.5),
           xlabel="Adjusted 10-second box-entry odds ratio vs PP", title="Two-action motif contrasts after context adjustment")
    save(fig, "two_action_adjusted_or", "Controls: total progression, starting x, duration · 95% match-clustered intervals · PP fixed at 1")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(np.arange(4), adjusted.predicted_probability * 100,
                yerr=np.vstack([adjusted.predicted_probability-adjusted.probability_ci_low,
                                adjusted.probability_ci_high-adjusted.predicted_probability]) * 100,
                fmt="o", capsize=5, color=ACTION_COLOR)
    for i, r in enumerate(adjusted.itertuples()):
        ax.annotate(f"{r.predicted_probability:.2%}", (i, r.predicted_probability * 100),
                    xytext=(12, 0), textcoords="offset points", va="center")
    ax.set(xticks=range(4), xticklabels=adjusted.index, xlim=(-.4, 3.65),
           ylabel="Model-based box-entry probability (%)", title="Two-action probabilities at common median context")
    save(fig, "two_action_probabilities", "Median progression, starting x and duration within two-action windows · descriptive probabilities, not interventions")

    raw3, model3 = rows("raw_motif", 3), rows("model", 3)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    positions = np.arange(8)
    axes[0].barh(positions, raw3.box_entry_rate * 100, color=OPPONENT_COLOR)
    axes[0].set(yticks=positions, yticklabels=[f"{m} (N={int(n):,})" for m, n in zip(raw3.index, raw3.N)],
                xlabel="Raw 10-second box-entry rate (%)", title="Three-action raw rates")
    for i, r in enumerate(model3.itertuples()):
        if r.model_status == "ok":
            axes[1].errorbar(r.odds_ratio, i, xerr=np.array([[r.odds_ratio-r.or_ci_low], [r.or_ci_high-r.odds_ratio]]),
                            fmt="o", capsize=4, color=ACTION_COLOR)
    axes[1].axvline(1, color="#777777", lw=.8)
    axes[1].set(yticks=positions, yticklabels=model3.index, xscale="log",
                xlabel="Adjusted odds ratio vs PPP (log scale)", title="Three-action adjusted uncertainty")
    axes[1].set_xticks([.03, .1, .3, 1, 3])
    axes[1].xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    axes[1].xaxis.set_minor_locator(NullLocator())
    for ax in axes:
        ax.set_ylim(-.6, 7.6)
        ax.invert_yaxis()
    save(fig, "three_action_summary", "95% match-clustered intervals · PPP: 121 windows / 15 positives · CCC: 17 windows / 1 positive")
    return paths

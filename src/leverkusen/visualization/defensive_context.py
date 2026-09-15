"""Five bounded Phase 6A figures of observed starting geometry."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

from leverkusen.spatial.progression_change import THIRDS
from leverkusen.tactics.context import PRIMARY
from leverkusen.visualization.style import ACTION_COLOR, OPPONENT_COLOR, PITCH_BACKGROUND

COLORS = [ACTION_COLOR, "#587E8B", OPPONENT_COLOR]
CONTEXTS = ["Advanced", "Middle", "Deep"]


def write_figures(data, summary, interactions, motifs, directory):
    directory.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name, note):
        fig.set_facecolor(PITCH_BACKGROUND)
        fig.text(.5, .015, note, ha="center", fontsize=9)
        fig.tight_layout(rect=(0, .055, 1, .95))
        path = directory / f"phase6a_{name}.png"
        fig.savefig(path, dpi=170, facecolor=fig.get_facecolor())
        plt.close(fig)
        paths.append(path)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, action in zip(axes, ("Pass", "Carry")):
        group = data[data.action_type.eq(action)]
        bottom = np.zeros(3)
        for code, color, label in zip((1, 2, 3), COLORS, CONTEXTS):
            values = np.array([int((group.starting_third.eq(t) & group.centroid_context.eq(code)).sum()) for t in THIRDS])
            ax.bar(np.arange(3), values, bottom=bottom, color=color, label=label)
            for x, value, base in zip(range(3), values, bottom):
                ax.text(x, base+value/2, f"{value:,}", ha="center", va="center", color="white", fontsize=9)
            bottom += values
        ax.set(title=action, xticks=range(3), xticklabels=["0–40", "40–80", "80–120"], xlabel="Action-start x third")
    axes[0].set_ylabel("Transitions with available starting centroid")
    axes[1].legend(loc="upper left", fontsize=8)
    fig.suptitle("Starting visible-centroid context by field third")
    save(fig, "context_distribution", "Shared within-third tertiles across Pass and Carry; three starting centroids unavailable.")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    for offset, action, color in [(-.18, "Pass", ACTION_COLOR), (.18, "Carry", OPPONENT_COLOR)]:
        groups = [data.loc[data.action_type.eq(action) & data.centroid_context.eq(c), PRIMARY].dropna() for c in (1, 2, 3)]
        box = ax.boxplot(groups, positions=np.arange(3)+offset, widths=.28, showfliers=False, patch_artist=True,
                         medianprops={"color": "white"})
        for patch in box["boxes"]:
            patch.set_facecolor(color)
        ax.plot([], [], color=color, linewidth=8, label=action)
    ax.axhline(0, color="gray", linestyle=":")
    ax.set(xticks=range(3), xticklabels=CONTEXTS, ylabel="Opponent centroid x: TO − FROM", xlabel="Starting visible-centroid context")
    ax.legend()
    fig.suptitle("Observed displacement declines as the starting visible centroid deepens")
    save(fig, "centroid_displacement", "Boxes: median and IQR; whiskers: 1.5 IQR. Outliers remain in analysis. Event observations, not tracked movement.")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
    predicted = interactions[interactions.record_type.eq("prediction")]
    for ax, action in zip(axes, ("Pass", "Carry")):
        for code, color, label in zip((1, 2, 3), COLORS, CONTEXTS):
            rows = predicted[predicted.action_type.eq(action) & predicted.context.eq(code)].sort_values("displacement_sd")
            ax.plot(rows.displacement_sd, rows.probability, "o-", color=color, label=label)
            ax.fill_between(rows.displacement_sd, rows.probability_ci_low, rows.probability_ci_high, color=color, alpha=.12)
        ax.set(title=action, xticks=[-1, 0, 1], xlabel="Centroid displacement (action-specific SD)")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].set_ylabel("Predicted 10s box-entry probability")
    axes[1].legend(fontsize=8)
    fig.suptitle("Conditional danger across starting visible-centroid contexts")
    save(fig, "context_probabilities", "Common action-specific median controls; match-clustered 95% CIs. Lines connect three representative model points.")

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.8), sharex=True, sharey=True)
    rows = interactions.query("scope == 'all' and horizon == 10 and record_type == 'coefficient'")
    rows = rows[rows.term.isin(["centroid_x_T2", "centroid_x_T3"])]
    labels = []
    for ax, action in zip(axes, ("Pass", "Carry")):
        selected = rows[rows.action_type.eq(action)]
        labels = [f"{r.context_dimension.title()}: T{r.term[-1]} vs T1" for r in selected.itertuples()]
        for y, row in enumerate(selected.itertuples()):
            ax.errorbar(row.odds_ratio, y, xerr=[[row.odds_ratio-row.or_ci_low], [row.or_ci_high-row.odds_ratio]],
                        fmt="o", color=ACTION_COLOR if action == "Pass" else OPPONENT_COLOR, capsize=3)
        ax.axvline(1, color="gray", linestyle=":")
        ax.set(title=action, xlabel="Interaction OR (ratio of displacement ORs)", xscale="log")
    axes[0].set_yticks(range(len(labels)), labels)
    axes[0].invert_yaxis()
    fig.suptitle("Starting visible context: moderation of the same centroid–danger relationship")
    save(fig, "interaction_effects", "T1/T2/T3 increase within each dimension and starting third. Match-clustered 95% CIs; exploratory, unadjusted for multiplicity.")

    fig, ax = plt.subplots(figsize=(10, 5))
    raw = motifs[motifs.record_type.eq("raw")]
    for code, color, label in zip((1, 2, 3), COLORS, CONTEXTS):
        selected = raw[raw.context.eq(code)].set_index("motif").loc[["PP", "PC", "CP", "CC"]]
        positions = np.arange(4) + (code-2)*.24
        ax.bar(positions, selected.box_entry_rate, width=.23, color=color, label=label)
        for x, row in zip(positions, selected.itertuples()):
            ax.text(x, row.box_entry_rate+.003, f"{int(row.N):,}", ha="center", fontsize=8)
    ax.set(xticks=range(4), xticklabels=["PP", "PC", "CP", "CC"], ylabel="Raw 10s box-entry rate", ylim=(0, .185))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(title="Starting visible centroid", ncols=3, fontsize=8)
    fig.suptitle("Two-action motifs by starting visible-centroid context")
    save(fig, "motif_context", "Labels show cell N. Raw rates are unadjusted; CC cells have only 21–24 positives. Three windows lack starting centroid.")
    return paths

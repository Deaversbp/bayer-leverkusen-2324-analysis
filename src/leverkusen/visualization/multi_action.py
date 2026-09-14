"""Seven descriptive fixed-motif figures, without outcomes or tracking paths."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from leverkusen.visualization.style import ACTION_COLOR, OPPONENT_COLOR, PITCH_BACKGROUND


def write_figures(windows, tables, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": PITCH_BACKGROUND, "axes.facecolor": PITCH_BACKGROUND})
    paths = []
    main, direction, adjusted, sensitivity = [tables[k] for k in (
        "motif_summary", "direction_profile_summary", "centroid_adjusted_summary", "sequence_sensitivity")]

    def save(fig, name, caption):
        fig.text(.5, .018, caption, ha="center", va="bottom", fontsize=9)
        fig.tight_layout(rect=(0, .065, 1, .95))
        path = output / f"phase4b_{name}.png"
        fig.savefig(path, dpi=170, metadata={"Software": "Leverkusen Phase 4B"})
        plt.close(fig)
        paths.append(path)

    def intervals(ax, group, metric):
        for i, r in enumerate(group.itertuples(index=False)):
            lo, med, hi = [getattr(r, f"{metric}_{q}") for q in ("q25", "median", "q75")]
            if np.isfinite(med):
                ax.errorbar(i, med, yerr=[[med-lo], [hi-med]], fmt="o", color=ACTION_COLOR, capsize=4)
            ax.text(i, .97, f"N={r.N:,}", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=8)
        ax.axhline(0, color="#888888", lw=.8)
        ax.set_xticks(range(len(group)), group.motif)
        ax.margins(y=.2)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    two = main[main.window_length.eq(2)]
    axes[0].bar(two.motif, two.N, color=OPPONENT_COLOR)
    for i, r in enumerate(two.itertuples()):
        axes[0].text(i, r.N, f"{r.N:,}\n{100*r.share_of_windows:.1f}%", ha="center", va="bottom", fontsize=9)
    axes[0].set_ylim(0, two.N.max()*1.25)
    axes[0].set_ylabel("Overlapping windows")
    intervals(axes[1], two, "total_progression")
    axes[1].set_ylabel("Summed signed action progression (x-units)")
    fig.suptitle("Two-action motifs: frequency and progression", fontsize=15)
    save(fig, "two_action_frequency", "P = Pass · C = Carry · markers/whiskers: median/IQR · overlapping windows are dependent observations")

    for length in (2, 3):
        fig, ax = plt.subplots(figsize=(11, 5))
        intervals(ax, main[main.window_length.eq(length)], "net_opp_centroid_x")
        ax.set_ylabel("Final minus initial visible opponent centroid x")
        fig.suptitle(f"{length}-action motifs: observed opponent centroid change", fontsize=15)
        save(fig, f"{length}_action_centroid", "Median and response IQR, not confidence intervals · event-aligned partial observations · no independent-window inference")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, length in zip(axes, (2, 3)):
        intervals(ax, direction[direction.window_length.eq(length)], "net_opp_centroid_x")
        ax.set_title(f"{length}-action direction profiles")
        ax.set_ylabel("Net visible opponent centroid x (units)")
    fig.suptitle("Forward/nonpositive action order and observed centroid change", fontsize=15)
    save(fig, "direction_profiles", "F: action delta x > 0 · R: delta x ≤ 0 · symbolic direction codes, not tactical labels · median/IQR")

    fig, axes = plt.subplots(3, 4, figsize=(16, 11))
    for ax, row in zip(axes.flat, main.itertuples(index=False)):
        g = windows[windows.window_length.eq(row.window_length) & windows.action_type_motif.eq(row.motif) & windows.net_opp_centroid_x_status.eq("ok")]
        ax.scatter(g.total_progression, g.net_opp_centroid_x, s=4, alpha=.06, color=OPPONENT_COLOR, rasterized=True)
        fit = adjusted[adjusted.window_length.eq(row.window_length) & adjusted.scope.eq("all") & adjusted.model.eq("progression_plus_motif")].set_index("term")
        if len(g) and len(fit) and fit.status.eq("ok").all():
            xs = np.array([g.total_progression.min(), g.total_progression.max()])
            intercept = fit.loc["intercept", "coefficient"] + (fit.loc[f"motif_{row.motif}", "coefficient"] if f"motif_{row.motif}" in fit.index else 0)
            ax.plot(xs, intercept + xs * fit.loc["total_progression", "coefficient"], color=ACTION_COLOR, lw=1.5)
        ax.axhline(0, color="#888888", lw=.5)
        ax.set_title(f"{row.window_length} actions · {row.motif} · N={len(g):,}")
        ax.set_xlabel("Total signed progression")
        ax.set_ylabel("Net opponent centroid x")
    fig.suptitle("Progression and observed centroid change within action motifs", fontsize=16)
    save(fig, "progression_by_motif", "Gold: descriptive common-progression-slope model plus motif contrast · panel scales vary · no causal effect interpretation")

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, length in zip(axes, (2, 3)):
        g = adjusted[adjusted.window_length.eq(length) & adjusted.scope.eq("all") & adjusted.model.eq("progression_plus_motif") & adjusted.term.str.startswith("motif_")]
        for i, r in enumerate(g.itertuples(index=False)):
            ax.errorbar(r.coefficient, i, xerr=[[r.coefficient-r.ci_low], [r.ci_high-r.coefficient]], fmt="o", color=OPPONENT_COLOR, capsize=4)
        ax.axvline(0, color="#777777", lw=.8)
        ax.set_yticks(range(len(g)), g.term.str.replace("motif_", ""))
        ax.set_xlabel("Adjusted contrast in net opponent centroid x (units)")
        ax.set_title(f"{length} actions · reference {'P'*length}")
        ax.set_ylim(-.6, len(g)-.4)
    fig.suptitle("Motif contrasts after adjustment for summed progression", fontsize=16)
    save(fig, "adjusted_motif_contrasts", "95% match-clustered CR1 intervals · common progression slope · contrasts are descriptive, not causal")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, length in zip(axes, (2, 3)):
        for scope, offset, color, label in (("all", -.20, OPPONENT_COLOR, "All legs"),
                                           ("gap_le_5", 0, ACTION_COLOR, "Every leg ≤5 s"),
                                           ("gap_le_3", .20, "#446E87", "Every leg ≤3 s")):
            g = main[main.window_length.eq(length)] if scope == "all" else sensitivity[sensitivity.window_length.eq(length) & sensitivity.motif_system.eq("action") & sensitivity.scope.eq(scope)]
            ax.plot(np.arange(len(g)) + offset, g.net_opp_centroid_x_median, "o", color=color, label=label)
        ax.axhline(0, color="#888888", lw=.8)
        ax.set_xticks(range(len(g)), g.motif)
        ax.set_title(f"{length}-action motifs")
        ax.set_ylabel("Median net observed opponent centroid x")
        ax.legend(fontsize=9)
    fig.suptitle("Motif signatures under shorter leg gaps", fontsize=16)
    save(fig, "gap_sensitivity", "Every leg must satisfy the stated sensitivity · no canonical gap cutoff · sample counts are retained in the sensitivity table")
    return paths

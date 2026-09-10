"""Neutral, aggregate readiness plots: event observations, never tracking."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from leverkusen.visualization.style import (
    ACTION_COLOR,
    PITCH_BACKGROUND,
    POLYGON_COLOR,
    UNRESOLVED_COLOR,
)


def write_readiness_figures(tables, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        fig.get_layout_engine().set(rect=(0, 0.07, 1, 0.93))
        fig.text(
            0.01,
            0.01,
            "StatsBomb Open Data | pinned 533862946a73 | Phase 2C-2 audit; no eligibility threshold",
            fontsize=8,
            color=UNRESOLVED_COLOR,
        )
        path = output_dir / f"phase2c2_{name}.png"
        fig.savefig(path, dpi=160, facecolor=PITCH_BACKGROUND, bbox_inches="tight")
        plt.close(fig)
        paths.append(path)

    p = tables["possession_anchor_coverage"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for ax, label, group in (
        (axes[0], "All Leverkusen possessions", p),
        (axes[1], "Shot-containing possessions", p[p.has_shot]),
    ):
        counts = [
            len(group),
            *[
                int(group.validated_spatial_anchor_count.ge(n).sum())
                for n in range(1, 6)
            ],
        ]
        ax.barh(range(6), counts, color=POLYGON_COLOR)
        for i, count in enumerate(counts):
            pct = 100 * count / len(group) if len(group) else 0
            ax.text(count, i, f" {count:,} ({pct:.1f}%)", va="center", fontsize=9)
        ax.set(
            yticks=range(6),
            yticklabels=["All", *[f"≥{n} anchors" for n in range(1, 6)]],
            title=label,
            xlabel="Possessions",
            xlim=(0, max(counts, default=1) * 1.55),
        )
        ax.invert_yaxis()
    fig.suptitle("Coverage attrition inventory — candidate state counts")
    save(fig, "sequence_readiness_waterfall")

    gaps = tables["anchor_gap_summary"].elapsed_seconds.to_numpy(dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), layout="constrained")
    if len(gaps):
        x = np.sort(gaps)
        y = np.arange(1, len(x) + 1) / len(x)
        for ax in axes:
            ax.step(x, y, where="post", color=UNRESOLVED_COLOR)
            for q, label, linestyle in ((0.5, "Median", "--"), (0.9, "p90", ":")):
                value = np.quantile(x, q)
                ax.axvline(
                    value,
                    color=ACTION_COLOR,
                    linestyle=linestyle,
                    label=f"{label}: {value:.2f} s",
                )
            ax.set(
                xlabel="Consecutive-anchor time gap (seconds)",
                ylabel="Cumulative fraction of intervals",
                ylim=(0, 1.02),
            )
            ax.legend(fontsize=8, loc="lower right")
        axes[0].set(xlim=(0, max(15, np.quantile(x, 0.95))), title="Detail (same ECDF)")
        axes[1].set(xlim=(0, max(x) * 1.02), title="Full range, including long gaps")
    fig.suptitle(
        "Trusted event-aligned observations — spacing is not tracking resolution"
    )
    save(fig, "anchor_time_gaps")

    m = tables["match_coverage"].sort_values(["match_date", "match_id"])
    fig, ax = plt.subplots(figsize=(10, 10), layout="constrained")
    ax.barh(range(len(m)), m.pct_ge_3_anchors, color=POLYGON_COLOR)
    labels = [f"{r.match_date}  {r.opponent}  [{r.match_id}]" for r in m.itertuples()]
    ax.set(
        yticks=range(len(m)),
        yticklabels=labels,
        xlabel="Possessions with ≥3 validated anchors (%)",
        title="Match-level sequence readiness — descriptive inventory",
        xlim=(0, 100),
    )
    ax.invert_yaxis()
    for i, value in enumerate(m.pct_ge_3_anchors):
        ax.text(value + 0.6, i, f"{value:.1f}%", va="center", fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    save(fig, "match_coverage")
    return paths

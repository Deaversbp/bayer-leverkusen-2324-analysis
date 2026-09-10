"""Four small Phase 3A-1 diagnostics; no tactical or tracking visuals."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from leverkusen.sequences.readiness import KEY
from leverkusen.visualization.style import (
    ACTION_COLOR,
    PITCH_BACKGROUND,
    POLYGON_COLOR,
    UNRESOLVED_COLOR,
)


def write_progression_figures(tables, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(fig, name):
        fig.get_layout_engine().set(rect=(0, 0.09, 1, 0.91))
        fig.text(
            0.01,
            0.015,
            "StatsBomb pinned 533862946a73 | Phase 3A-1: diagnostic, no reset rule",
            fontsize=8,
            color=UNRESOLVED_COLOR,
        )
        path = output_dir / f"phase3a1_{name}.png"
        fig.savefig(path, dpi=140, bbox_inches="tight", facecolor=PITCH_BACKGROUND)
        plt.close(fig)
        paths.append(path)

    bins = tables["action_displacement_bins"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for ax, typ in zip(axes, ["Pass", "Carry"]):
        g = bins[bins.event_type.eq(typ)]
        ax.bar(range(len(g)), g.percentage, color=POLYGON_COLOR)
        ax.set(
            xticks=range(len(g)),
            xticklabels=g.displacement_bin.astype(str),
            ylabel="Actions (%)",
            title=typ,
            xlabel="Attacking delta-x (native units; presentation bins)",
        )
        ax.tick_params(axis="x", rotation=30, labelsize=8)
    fig.suptitle("Explicit Leverkusen action vectors with validated frames")
    save(fig, "action_displacement")
    p = tables["possession_progression_summary"]
    values = np.sort(p.maximum_retreat_from_peak.dropna().to_numpy())
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    if len(values):
        ax.step(
            values,
            np.arange(1, len(values) + 1) / len(values),
            where="post",
            color=UNRESOLVED_COLOR,
        )
    ax.set(
        xlabel="Maximum observed retreat from running peak (native x-units)",
        ylabel="Fraction of measurable possessions",
        title="Retreat from action-ordered start/end vertices",
    )
    save(fig, "maximum_retreat_ecdf")
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    ax.scatter(
        p.possession_duration_seconds,
        p.maximum_retreat_from_peak,
        s=9,
        alpha=0.3,
        color=UNRESOLVED_COLOR,
    )
    ax.set(
        xlabel="Provider possession timestamp span (seconds)",
        ylabel="Maximum observed retreat (native x-units)",
        title="Duration and retreat; no possessions excluded by length",
    )
    save(fig, "duration_retreat")
    manifest = tables["representative_possessions"]
    chosen = manifest.sort_values("maximum_retreat_from_peak", ascending=False).head(1)
    other = manifest.sort_values(
        "validated_spatial_anchor_count", ascending=False
    ).head(1)
    chosen = pd.concat([chosen, other]).drop_duplicates(KEY)
    fig, axes = plt.subplots(
        len(chosen),
        1,
        figsize=(11, 3.2 * len(chosen)),
        squeeze=False,
        layout="constrained",
    )
    vertices = tables["representative_path_vertices"]
    for ax, (_, r) in zip(axes[:, 0], chosen.iterrows()):
        g = vertices[(vertices[KEY] == r[KEY]).all(axis=1)]
        ax.plot(
            np.arange(len(g)),
            g.attacking_x,
            "o--",
            color=ACTION_COLOR,
            markersize=2,
            linewidth=0.7,
            label="Ordered action vertices; connecting line is not a ball trajectory",
        )
        ax.set(
            xlabel="Action-ordered start/end vertex number",
            ylabel="Attacking x",
            title=f"Match {r.match_id}, period {r.period}, possession {r.possession_id}",
        )
        ax.legend(fontsize=8)
    save(fig, "representative_progression_traces")
    return paths

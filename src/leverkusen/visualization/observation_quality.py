"""Bounded diagnostic charts and native-coordinate representative contact sheets."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon as PolygonPatch, Rectangle
import numpy as np
from shapely.geometry import MultiPoint

from leverkusen.spatial.diagnostics import FRAME
from leverkusen.spatial.observation_quality import (
    RELATIONSHIPS,
    excursion,
    polygon_diagnostics,
    selected_records,
)


def plot_representative(axis, frame, row, rules):
    """Show every finite record with literal flags; selected geometry is overlaid."""
    polygon, _ = polygon_diagnostics(frame.get("visible_area"))
    records = selected_records(frame)
    points = [p for _, _, p in records]
    selected = selected_records(frame, row["selected_subset"], row["goalkeeper_policy"])
    selected_indices = {i for i, _, _ in selected}
    selected_points = [p for _, _, p in selected]
    axis.add_patch(
        Rectangle(
            (0, 0),
            120,
            80,
            facecolor="#f4f7f0",
            edgecolor="#222222",
            linewidth=1.2,
            zorder=0,
        )
    )
    axis.plot([60, 60], [0, 80], color="gray", lw=0.6)
    axis.add_patch(Circle((60, 40), 9.15, fill=False, edgecolor="gray", lw=0.6))
    for x in (0, 102):
        axis.add_patch(Rectangle((x, 18), 18, 44, fill=False, edgecolor="gray", lw=0.6))
    if polygon is not None:
        axis.add_patch(
            PolygonPatch(
                np.asarray(polygon.exterior.coords),
                facecolor="#a6bddb",
                alpha=0.35,
                edgecolor="#225ea8",
                linewidth=1.6,
                zorder=1,
            )
        )
    if len(selected_points) >= 3:
        hull = MultiPoint(selected_points).convex_hull
        if hull.geom_type == "Polygon":
            axis.add_patch(
                PolygonPatch(
                    np.asarray(hull.exterior.coords),
                    fill=False,
                    edgecolor="#6a3d9a",
                    lw=1.4,
                    zorder=2,
                )
            )
    for i, record, point in records:
        x, y = point
        color = (
            "#0072B2"
            if record.get("teammate") is True
            else "#D55E00"
            if record.get("teammate") is False
            else "gray"
        )
        axis.scatter(
            x,
            y,
            c=color,
            marker="s" if record.get("keeper") is True else "o",
            s=32,
            alpha=1 if i in selected_indices else 0.3,
            zorder=4,
        )
        if record.get("actor") is True:
            axis.scatter(
                x,
                y,
                marker="*",
                s=110,
                facecolors="none",
                edgecolors="black",
                linewidths=1.1,
                zorder=6,
            )
        if excursion(point)["sides_violated"]:
            axis.scatter(
                x,
                y,
                marker="o",
                s=105,
                facecolors="none",
                edgecolors="crimson",
                linewidths=1.3,
                zorder=5,
            )
    # Coincident records cannot be separated without moving coordinates: label multiplicity.
    for point in set(points):
        count = points.count(point)
        if count > 1:
            axis.annotate(
                f"x{count}",
                point,
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                zorder=7,
            )
    extents = points + [(0, 0), (120, 80)]
    if polygon is not None:
        extents += list(polygon.exterior.coords)
    xs, ys = zip(*extents)
    axis.set(
        xlim=(min(xs) - 4, max(xs) + 4),
        ylim=(max(ys) + 4, min(ys) - 4),
        aspect="equal",
        xlabel="Native x",
        ylabel="Native y",
    )
    axis.tick_params(labelsize=7)
    axis.set_title(
        f"M {int(row['match_id'])} | frame {int(row['frame_index'])} | {row['event_type']}\n"
        f"{row['event_id']}\n"
        f"{row['selected_subset']} / GK {row['goalkeeper_policy']} | n={row['n_valid_points_used']} / total={row['total_visible_players']}\n"
        f"coverage={row['visible_area_fraction']:.4f} | OOB selected={row['n_out_of_bounds_points']} / total={sum(excursion(p)['sides_violated'] > 0 for p in points)}\n"
        f"W={row['visible_width']:.2f} D={row['visible_depth']:.2f} H={row['convex_hull_area']:.2f} "
        f"PD={row['mean_pairwise_distance']:.2f} NN={row['mean_nearest_neighbor_distance']:.2f}\n"
        + "\n".join(rules),
        fontsize=7.5,
    )


def write_quality_figures(
    summaries, diagnostics, representatives, candidates, figure_dir
):
    figure_dir = Path(figure_dir)
    figure_dir.mkdir(parents=True, exist_ok=True)

    def save(figure, name):
        figure.savefig(figure_dir / f"phase2b2_{name}.png", dpi=160)
        plt.close(figure)

    oob = diagnostics["out_of_bounds_records"]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    values = np.sort(oob.pitch_distance)
    axes[0].plot(values, np.arange(1, len(values) + 1) / len(values))
    axes[0].set(
        xscale="log",
        xlabel="Distance to pitch rectangle (native units, log)",
        ylabel="Empirical cumulative fraction",
    )
    for status, group in oob.groupby("polygon_status"):
        values = np.sort(group.pitch_distance)
        axes[1].plot(
            values,
            np.arange(1, len(values) + 1) / len(values),
            label=f"{status} (n={len(values):,})",
        )
    axes[1].set(
        xscale="log",
        xlabel="Pitch excursion (native units, log)",
        ylabel="Within-status cumulative fraction",
    )
    axes[1].legend()
    figure.suptitle(
        "Out-of-bounds player records: excursion and visible-polygon consistency"
    )
    save(figure, "out_of_bounds_excursions")

    polygons = diagnostics["polygon_frames"]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    labels = ("Contained", "Extends outside", "Invalid/unavailable")
    axes[0].bar(
        labels,
        [
            polygons.contained_in_pitch.eq(True).sum(),
            polygons.extends_outside_pitch.eq(True).sum(),
            (~polygons.visible_area_valid).sum(),
        ],
    )
    axes[0].set(ylabel="Original frames")
    outside_fraction = polygons.fraction_outside_pitch.dropna()
    if outside_fraction.nunique() == 1:
        value = outside_fraction.iloc[0]
        axes[1].bar([value], [len(outside_fraction)], width=0.02)
        axes[1].set_xticks([value], [f"{value:g} (all valid polygons)"])
    else:
        axes[1].hist(outside_fraction, bins=30)
    axes[1].set(
        xlabel="Fraction of supplied polygon area outside pitch",
        ylabel="Original frames",
    )
    figure.suptitle(
        "Supplied visible polygons: exact predicates, unchanged coordinates"
    )
    save(figure, "visible_polygon_bounds")

    figure, axes = plt.subplots(2, 3, figsize=(14, 8), constrained_layout=True)
    relation = summaries["metric_edge_relationship"]
    for axis, (metric, edge) in zip(axes.flat, RELATIONSHIPS):
        part = relation.loc[relation.metric.eq(metric) & relation.edge_measure.eq(edge)]
        for (subset, policy), group in part.groupby(
            ["selected_subset", "goalkeeper_policy"]
        ):
            group = group.sort_values("edge_median")
            axis.plot(
                group.edge_median,
                group["median"],
                marker="o",
                ms=3,
                linestyle="-" if policy == "included" else "--",
                label=f"{subset}/{policy}",
            )
        axis.set(
            title=f"{metric}\nvs {edge}",
            xlabel="Median edge distance in empirical quintile",
            ylabel="Median metric (native units or units²)",
        )
    axes.flat[-1].axis("off")
    axes.flat[-1].legend(
        *axes.flat[0].get_legend_handles_labels(), loc="center", fontsize=8
    )
    figure.suptitle(
        "Geometry and visible-boundary distances: descriptive bins, no eligibility cutoff"
    )
    save(figure, "metric_edge_relationship")

    write_representative_figures(representatives, candidates, figure_dir)


def write_representative_figures(representatives, candidates, figure_dir):
    """Render the same review set, allowing layout-only regeneration in memory."""
    figure_dir = Path(figure_dir)
    figure_dir.mkdir(parents=True, exist_ok=True)
    grouped = list(representatives.groupby(FRAME, sort=True))
    legend = [
        Line2D([], [], color="#225ea8", label="supplied visible polygon"),
        Line2D([], [], color="#222222", label="nominal pitch boundary"),
        Line2D([], [], marker="o", ls="", color="#0072B2", label="teammate=True"),
        Line2D([], [], marker="o", ls="", color="#D55E00", label="teammate=False"),
        Line2D([], [], marker="s", ls="", color="gray", label="keeper=True"),
        Line2D([], [], marker="*", ls="", color="black", label="actor=True"),
        Line2D(
            [],
            [],
            marker="o",
            ls="",
            markerfacecolor="none",
            color="crimson",
            label="out of bounds",
        ),
        Line2D([], [], color="#6a3d9a", label="selected hull; faded points unselected"),
    ]
    for page in range(0, len(grouped), 4):
        figure, axes = plt.subplots(2, 2, figsize=(16, 16))
        figure.subplots_adjust(
            top=0.87, bottom=0.08, left=0.06, right=0.98, hspace=0.55, wspace=0.12
        )
        for axis, (key, rows) in zip(axes.flat, grouped[page : page + 4]):
            row = rows.iloc[0]
            rules = [
                f"{r.selection_rule}: {r.selected_subset}/{r.goalkeeper_policy} = {r.selection_value:.3g}"
                for r in rows.itertuples()
            ]
            plot_representative(axis, candidates[key], row, rules)
        for axis in list(axes.flat)[len(grouped[page : page + 4]) :]:
            axis.axis("off")
        figure.suptitle(
            f"Deterministic representative review | page {page // 4 + 1}\nNative provider axes; no direction inference"
        )
        figure.legend(handles=legend, loc="outside lower center", ncol=4, fontsize=9)
        figure.savefig(
            figure_dir / f"phase2b2_representative_{page // 4 + 1:02d}.png", dpi=160
        )
        plt.close(figure)

"""Bounded deterministic native/normalized validation figures, not sequence plots."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon, Rectangle
import numpy as np
import pandas as pd

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.data.semantic_diagnostics import TEAM_ID, field, points
from leverkusen.spatial.geometry import valid_point
from leverkusen.spatial.orientation import (
    VALIDATED,
    normalize_attacking_point,
    point_team_label,
)
from leverkusen.visualization import style


def _pitch(ax):
    ax.set_facecolor(style.PITCH_BACKGROUND)
    for x, y, width, height in [
        (0, 0, 120, 80),
        (0, 18, 18, 44),
        (102, 18, 18, 44),
        (0, 30, 6, 20),
        (114, 30, 6, 20),
    ]:
        ax.add_patch(
            Rectangle(
                (x, y),
                width,
                height,
                fill=False,
                edgecolor=style.PITCH_LINE_COLOR,
                linewidth=0.7,
            )
        )
    ax.plot([60, 60], [0, 80], color=style.PITCH_LINE_COLOR, linewidth=0.7)
    ax.add_patch(
        Circle(
            (60, 40), 10, fill=False, edgecolor=style.PITCH_LINE_COLOR, linewidth=0.7
        )
    )
    ax.set(
        xlim=(-4, 124),
        ylim=(84, -4),
        aspect="equal",
        xlabel="x (StatsBomb units)",
        ylabel="y (downward)",
    )
    ax.set_xticks([0, 30, 60, 90, 120])
    ax.set_yticks([0, 20, 40, 60, 80])


def plot_frame(frame, event, match, row, path):
    """Unsupported panel stays empty; raw unsupported flags use literal T/F text."""
    status = row["semantics_status"]
    valid = status == VALIDATED
    teams = (
        field(match, "home_team", "home_team_id"),
        field(match, "away_team", "away_team_id"),
    )

    def transform(p, normalized):
        if not normalized:
            return p
        result = normalize_attacking_point(
            p,
            reference_team_id=field(event, "team"),
            target_team_id=TEAM_ID,
            match_team_ids=teams,
            semantics_status=status,
        )
        return result["x_attacking"], result["y_attacking"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    for normalized, ax in enumerate(axes):
        _pitch(ax)
        ax.set_title(
            "Leverkusen attacking view (+x)"
            if normalized and valid
            else "Normalized view unavailable"
            if normalized
            else "Native supplied coordinates"
        )
        if normalized and not valid:
            ax.text(60, 34, "NORMALIZATION UNSUPPORTED", ha="center", fontsize=12)
            ax.text(
                60, 44, status.replace("_", " "), ha="center", fontsize=10, wrap=True
            )
            continue
        bounds = [(0, 0), (120, 80)]
        polygon = frame.get("visible_area", [])
        if isinstance(polygon, list) and len(polygon) >= 6 and len(polygon) % 2 == 0:
            vertices = [
                valid_point(polygon[i : i + 2]) for i in range(0, len(polygon), 2)
            ]
            if all(p is not None for p in vertices):
                vertices = [transform(p, normalized) for p in vertices]
                ax.add_patch(
                    Polygon(
                        vertices,
                        facecolor=style.POLYGON_COLOR,
                        alpha=style.POLYGON_ALPHA,
                        edgecolor=style.POLYGON_COLOR,
                        linewidth=0.7,
                    )
                )
                bounds.extend(vertices)
        for p in points(frame):
            location = transform(p["location"], normalized)
            bounds.append(location)
            side = point_team_label(
                p.get("teammate"), field(event, "team"), teams, semantics_status=status
            )["frame_player_side"]
            color = {
                "leverkusen": style.LEVERKUSEN_COLOR,
                "opponent": style.OPPONENT_COLOR,
            }.get(side, style.UNRESOLVED_COLOR)
            marker = (
                style.KEEPER_MARKER
                if p.get("keeper") is True
                else style.OUTFIELD_MARKER
            )
            if p.get("actor") is True:
                ax.scatter(
                    *location,
                    s=220,
                    marker=marker,
                    facecolors="none",
                    edgecolors=style.ACTOR_EDGE_COLOR,
                    linewidths=style.ACTOR_HALO_LINEWIDTH,
                    zorder=4,
                )
            ax.scatter(
                *location,
                s=100,
                color=color,
                marker=marker,
                edgecolors=style.TEAM_TEXT_COLOR,
                linewidths=0.6,
                zorder=5,
            )
            label = (
                style.TEAM_LABELS[side]
                if valid
                else "T"
                if p.get("teammate") is True
                else "F"
                if p.get("teammate") is False
                else "?"
            )
            ax.text(
                *location,
                label,
                color=style.TEAM_TEXT_COLOR,
                fontsize=6,
                ha="center",
                va="center",
                zorder=6,
            )
        start = valid_point(event.get("location"))
        end = valid_point([row["end_x"], row["end_y"]])
        if start:
            start = transform(start, normalized)
            bounds.append(start)
            ax.scatter(
                *start,
                marker=style.EVENT_MARKER,
                s=170,
                facecolors="none",
                edgecolors=style.ACTION_COLOR,
                linewidths=1.7,
                zorder=7,
            )
        if end:
            end = transform(end, normalized)
            bounds.append(end)
            ax.scatter(*end, marker="x", s=36, color=style.ACTION_COLOR, zorder=7)
        if start and end and row["event_type"] in ("Pass", "Carry", "Shot"):
            ax.annotate(
                "",
                xy=end,
                xytext=start,
                arrowprops=style.PROVIDER_ACTION_ARROW,
                zorder=3,
            )
        xs, ys = np.asarray(bounds).T
        ax.set(xlim=(min(xs) - 4, max(xs) + 4), ylim=(max(ys) + 4, min(ys) - 4))
    labels = (
        "L = Leverkusen; O = opponent"
        if valid
        else "T/F = literal teammate True/False; team mapping unsupported"
    )
    handles = [
        Line2D(
            [],
            [],
            marker=style.OUTFIELD_MARKER,
            linestyle="none",
            color=style.UNRESOLVED_COLOR,
            label="outfield",
        ),
        Line2D(
            [],
            [],
            marker=style.KEEPER_MARKER,
            linestyle="none",
            color=style.UNRESOLVED_COLOR,
            label="keeper",
        ),
        Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markerfacecolor="none",
            color=style.ACTOR_EDGE_COLOR,
            label="actor halo",
        ),
        Line2D(
            [],
            [],
            marker=style.EVENT_MARKER,
            linestyle="none",
            color=style.ACTION_COLOR,
            label="event start (end = x)",
        ),
        Line2D(
            [],
            [],
            color=style.ACTION_COLOR,
            linestyle=style.PROVIDER_ACTION_ARROW["linestyle"],
            label="recorded action vector",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.04),
        ncol=5,
        fontsize=8,
    )
    fig.suptitle(
        f"{row['event_type']} | event: {row['event_team_name']} | possession: {row['possession_team_name']}\n"
        f"match {row['match_id']} | period {row['period']} | Leverkusen {'home' if row['leverkusen_home'] else 'away'}\n"
        f"{status} | {row['orientation_status']}",
        fontsize=11,
    )
    fig.text(
        0.5,
        0.032,
        f"{labels}; supplied partial observation; no tracked trajectory.",
        ha="center",
        fontsize=8,
    )
    fig.text(
        0.5,
        0.008,
        f"StatsBomb Open Data | {event['id']} | pinned {STATSBOMB_REVISION[:12]}",
        ha="center",
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.17, 1, 0.90))
    fig.savefig(path, dpi=150, facecolor=style.PITCH_BACKGROUND)
    plt.close(fig)


def write_representatives(representatives, output_dir, figure_dir):
    """Deduplicate rules by event; save only a compact manifest and rendered figures."""
    figure_dir = Path(figure_dir)
    figure_dir.mkdir(parents=True, exist_ok=True)
    grouped = {}
    for rule, values in representatives.items():
        key = values[1]["id"]
        if key not in grouped:
            grouped[key] = {"values": values, "rules": []}
        grouped[key]["rules"].append(rule)
    records = []
    for index, (_, item) in enumerate(sorted(grouped.items()), 1):
        frame, event, match, row = item["values"]
        filename = f"phase2c_frame_{index:02}_{event['id']}.png"
        plot_frame(frame, event, match, row, figure_dir / filename)
        records.append(
            {
                k: row[k]
                for k in (
                    "match_id",
                    "event_id",
                    "event_type",
                    "period",
                    "event_team_name",
                    "possession_team_name",
                    "team_agreement",
                    "leverkusen_home",
                    "actor_status",
                    "actor_codec",
                    "paired_label_conflict",
                    "semantics_status",
                    "orientation_status",
                )
            }
            | {
                "selection_rules": ";".join(sorted(item["rules"])),
                "figure": filename,
                "statsbomb_revision": STATSBOMB_REVISION,
            }
        )
    manifest = pd.DataFrame(records)
    manifest.to_csv(Path(output_dir) / "phase2c_representative_frames.csv", index=False)
    return manifest

"""Human review visuals; ordered observations are never tracked trajectories."""

from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pandas as pd

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.sequences.boundary_review import HUMAN_COLUMNS, LABELS, STATUS
from leverkusen.sequences.progression_diagnostics import action_path
from leverkusen.visualization import style
from leverkusen.visualization.semantics_orientation import _pitch

TRACE_CAPTION = "Lines connect ordered event observations for review; they are not tracked trajectories."
SUMMARY_FIELDS = [
    "possession_duration_seconds",
    "total_event_count",
    "validated_spatial_anchor_count",
    "safe_action_count",
    "first_safe_action_x",
    "max_attacking_x_reached",
    "last_safe_action_x",
    "net_x_progression",
    "cumulative_forward_x",
    "cumulative_backward_x",
    "maximum_retreat_from_peak",
    "maximum_single_backward_action",
    "maximum_negative_run_actions",
    "maximum_nonpositive_run_actions",
    "retreat_excursion_count",
    "observed_recovery_count",
    "shot_count",
    "restart_context",
    "out_event_count",
    "candidate_count",
]


def load_review_tables(root):
    """Reload only derived review outputs for offline inspection or rendering."""
    names = (
        "review_manifest",
        "category_coverage",
        "boundary_review_sheet",
        "candidate_context",
        "timelines",
        "spatial_slots",
        "spatial_points",
        "spatial_polygons",
        "spatial_geometry",
        "source_inventory",
    )
    directory = Path(root) / "outputs/diagnostics"
    tables = {name: pd.read_csv(directory / f"phase3a2_{name}.csv") for name in names}
    for table in tables.values():
        if not table.statsbomb_revision.eq(STATSBOMB_REVISION).all():
            raise ValueError("Different review artifact source revision")
        for column in (
            "restart_context",
            "possession_restart_context",
            "provider_context",
        ):
            if column in table:
                table[column] = table[column].fillna("")
    return tables


def number(value):
    return "unavailable" if pd.isna(value) else f"{value:.1f}"


def plot_progression(case, timeline, sheet, path):
    vertices = action_path(timeline[timeline.safe_action])
    fig, (ax, context_ax) = plt.subplots(
        2, 1, figsize=(13, 6.5), sharex=True, gridspec_kw={"height_ratios": [4, 1]}
    )
    if len(vertices):
        ax.plot(
            vertices.elapsed_possession_time,
            vertices.attacking_x,
            color=style.ACTION_COLOR,
            linewidth=0.8,
            linestyle="--",
            alpha=0.6,
        )
        for vertex, marker in (("start", "D"), ("end", "x")):
            points = vertices[vertices.vertex.eq(vertex)]
            ax.scatter(
                points.elapsed_possession_time,
                points.attacking_x,
                marker=marker,
                s=19,
                color=style.ACTION_COLOR,
                label=f"safe action {vertex}",
                zorder=4,
            )
    else:
        ax.text(
            0.5,
            0.5,
            "No safe Pass/Carry vectors; progression unavailable",
            transform=ax.transAxes,
            ha="center",
        )
    anchors = timeline[timeline.validated_anchor & ~timeline.safe_action]
    if len(anchors):
        ax.scatter(
            anchors.elapsed_possession_time,
            anchors.anchor_x,
            marker="+",
            color=style.UNRESOLVED_COLOR,
            s=25,
            label="other validated actor/event x (not ball)",
        )
    for r in sheet.itertuples(index=False):
        ax.axvline(
            r.candidate_elapsed_seconds,
            color=style.PITCH_LINE_COLOR,
            linewidth=0.5,
            alpha=0.35,
        )
        context_ax.scatter(
            r.candidate_elapsed_seconds,
            3,
            color=style.PITCH_LINE_COLOR,
            s=15,
            marker="|",
        )
    ax.plot(
        [],
        [],
        color=style.PITCH_LINE_COLOR,
        linewidth=0.7,
        label="candidate review moment",
    )
    for level, state in enumerate(
        ("no_360_frame", "linked_360_unsupported_semantics", "validated_spatial_anchor")
    ):
        rows = timeline[timeline.spatial_state_status.eq(state)]
        context_ax.scatter(
            rows.elapsed_possession_time,
            [level] * len(rows),
            s=12,
            marker="|",
            color=style.UNRESOLVED_COLOR,
        )
    football = timeline[
        timeline.event_type.isin(["Shot", "Foul Won", "Foul Committed"])
        | timeline.restart_context.ne("")
        | timeline.provider_context.str.contains("out:true", regex=False)
    ]
    for i, r in enumerate(football.itertuples(index=False)):
        text = r.restart_context or r.event_type
        if "out:true" in r.provider_context:
            text += "/out"
        ax.annotate(
            text,
            (r.elapsed_possession_time, 123 + (i % 2) * 9),
            fontsize=7,
            rotation=30,
            color=style.ACTION_COLOR,
        )
    ax.set(ylabel="Leverkusen attacking x", ylim=(-5, 150))
    ax.set_yticks([0, 30, 60, 90, 120])
    ax.grid(alpha=0.15)
    ax.legend(loc="lower right", fontsize=7, ncol=2)
    context_ax.set(
        yticks=[0, 1, 2, 3],
        yticklabels=[
            "no 360",
            "linked / unsupported",
            "validated anchor",
            "review moment",
        ],
        xlabel="Possession elapsed seconds (action-start timestamp references)",
        ylim=(-0.6, 3.6),
    )
    context_ax.tick_params(axis="y", labelsize=7)
    for panel in (ax, context_ax):
        panel.set_facecolor(style.PITCH_BACKGROUND)
    fig.suptitle(
        f"{case.case_id} | match {case.match_id} / period {case.period} / possession {case.possession_id} / team 904\n"
        f"{case.total_event_count} events; {case.validated_spatial_anchor_count} anchors; {case.safe_action_count} safe actions | restart_context = {case.restart_context or 'none supplied'}",
        fontsize=11,
    )
    fig.text(0.5, 0.045, TRACE_CAPTION, ha="center", fontsize=9)
    fig.text(
        0.5,
        0.019,
        f"End coordinates share action-start timestamps; arrival times unavailable. StatsBomb Open Data {STATSBOMB_REVISION[:12]}",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.065, 1, 0.91))
    fig.savefig(path, dpi=125, facecolor=style.PITCH_BACKGROUND)
    plt.close(fig)


def plot_snapshots(candidate_id, slots, points, polygons, geometry, path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 8))
    for ax, slot in zip(axes, ("before", "candidate", "after")):
        _pitch(ax)
        row = slots[slots.slot.eq(slot)].iloc[0]
        ax.set_title(
            ("At" if slot == "candidate" else slot.capitalize())
            + " candidate review moment",
            fontsize=10,
        )
        if not row.spatial_state_available:
            ax.text(
                60,
                37,
                "Validated spatial state unavailable\nwithin this provider possession",
                ha="center",
                fontsize=10,
            )
            if slot == "candidate":
                ax.text(
                    0,
                    -0.17,
                    f"{row.elapsed_seconds:.3f}s | index {int(row.event_index)} | {row.event_type}\n"
                    f"event team: {row.event_team}\nattacking x / retreat unavailable\n"
                    f"{row.semantics_status}\n{row.spatial_state_status}\nUUID: {row.event_id}",
                    transform=ax.transAxes,
                    fontsize=7,
                    va="top",
                )
            continue
        cloud = points[points.slot_id.eq(row.slot_id)]
        polygon = polygons[polygons.slot_id.eq(row.slot_id)].sort_values("vertex_order")
        if len(polygon):
            ax.add_patch(
                Polygon(
                    polygon[["x_attacking", "y_attacking"]].to_numpy(),
                    color=style.POLYGON_COLOR,
                    alpha=style.POLYGON_ALPHA,
                    linewidth=0.7,
                )
            )
        for p in cloud.itertuples(index=False):
            color = (
                style.LEVERKUSEN_COLOR
                if p.side == "leverkusen"
                else style.OPPONENT_COLOR
            )
            marker = style.KEEPER_MARKER if p.keeper else style.OUTFIELD_MARKER
            if p.actor:
                ax.scatter(
                    p.x_attacking,
                    p.y_attacking,
                    s=190,
                    marker=marker,
                    facecolors="none",
                    edgecolors=style.ACTOR_EDGE_COLOR,
                    linewidths=style.ACTOR_HALO_LINEWIDTH,
                    zorder=4,
                )
            ax.scatter(
                p.x_attacking, p.y_attacking, s=80, marker=marker, color=color, zorder=5
            )
            ax.text(
                p.x_attacking,
                p.y_attacking,
                style.TEAM_LABELS[p.side],
                color=style.TEAM_TEXT_COLOR,
                fontsize=6,
                ha="center",
                va="center",
                zorder=6,
            )
        ax.scatter(
            row.anchor_x,
            row.anchor_y,
            s=125,
            marker=style.EVENT_MARKER,
            facecolors="none",
            edgecolors=style.ACTION_COLOR,
            zorder=7,
        )
        if pd.notna(row.vector_end_x):
            ax.annotate(
                "",
                xy=(row.vector_end_x, row.vector_end_y),
                xytext=(row.anchor_x, row.anchor_y),
                arrowprops=style.PROVIDER_ACTION_ARROW,
            )
        xs = [0, 120, *cloud.x_attacking, *polygon.x_attacking, row.anchor_x]
        ys = [0, 80, *cloud.y_attacking, *polygon.y_attacking, row.anchor_y]
        if pd.notna(row.vector_end_x):
            xs.append(row.vector_end_x)
            ys.append(row.vector_end_y)
        ax.set(xlim=(min(xs) - 4, max(xs) + 4), ylim=(max(ys) + 4, min(ys) - 4))
        detail = (
            f"{row.elapsed_seconds:.3f}s | index {int(row.event_index)} | {row.event_type}\n"
            f"event team: {row.event_team}\nactor/event x={number(row.anchor_x)}; action-end retreat={number(row.retreat_from_peak)}\n"
            f"{row.semantics_status}\n{row.spatial_state_status}\nUUID: {row.event_id}"
        )
        ax.text(0, -0.17, detail, transform=ax.transAxes, fontsize=7, va="top")
        g = geometry[
            geometry.slot_id.eq(row.slot_id) & geometry.goalkeeper_policy.eq("excluded")
        ]
        lines = []
        for side in ("opponent", "leverkusen"):
            r = g[g.semantic_side.eq(side)].iloc[0]

            def eligible(metric):
                return (
                    number(r[metric])
                    if r[f"{metric}_d_primary_eligible"]
                    else f"unavailable ({r[f'{metric}_status']})"
                )

            line = f"{side} outfield: n={r.n_valid_points_used}; width={eligible('visible_width')}; depth={eligible('visible_depth')}"
            if side == "opponent":
                line += f"\ncentroid x={number(r.centroid_x_attacking)}; pairwise={eligible('mean_pairwise_distance')}; NN={eligible('mean_nearest_neighbor_distance')}"
                line += f"\nhull footprint (secondary)={eligible('convex_hull_area')}"
            lines.append(line)
        r = g.iloc[0]
        lines.append(
            f"coverage={number(r.visible_area_fraction)}; frame OOB={r.frame_oob}; coincidence={r.frame_coincident}; actor={r.actor_status}"
        )
        ax.text(
            0, -0.49, "\n".join(lines), transform=ax.transAxes, fontsize=7, va="top"
        )
    first = slots.iloc[0]
    fig.suptitle(
        f"{candidate_id} | match {first.match_id} / period {first.period} / possession {first.possession_id} / team 904\nLeverkusen attacking +x | nearest validated before / exact candidate / nearest validated after",
        fontsize=12,
    )
    fig.text(
        0.5,
        0.055,
        "L red = Leverkusen; O charcoal = opponent; square = keeper; halo = actor; gold solid arrow = explicit provider vector. Pressure actor is not ball.",
        ha="center",
        fontsize=8,
    )
    fig.text(
        0.5,
        0.033,
        "Partial event-aligned observations; no formation or trajectory inference. Geometry is corroborative only; all support/status variants accompany this figure.",
        ha="center",
        fontsize=8,
    )
    fig.text(
        0.5,
        0.012,
        f"StatsBomb Open Data {STATSBOMB_REVISION} | UUIDs in spatial_slots.csv",
        ha="center",
        fontsize=7,
    )
    fig.subplots_adjust(top=0.85, bottom=0.45, left=0.035, right=0.99, wspace=0.22)
    fig.savefig(path, dpi=130, facecolor=style.PITCH_BACKGROUND)
    plt.close(fig)


def write_review_visuals(tables, root):
    root = Path(root)
    figures, review = root / "outputs/figures", root / "outputs/review"
    figures.mkdir(parents=True, exist_ok=True)
    review.mkdir(parents=True, exist_ok=True)
    manifest, timeline, sheet = (
        tables[n] for n in ("review_manifest", "timelines", "boundary_review_sheet")
    )
    if not sheet[HUMAN_COLUMNS].fillna("").eq("").all().all():
        raise ValueError(
            "Human annotations exist; refusing to regenerate the blank review artifact"
        )
    slots = tables["spatial_slots"]
    for case in manifest.itertuples(index=False):
        plot_progression(
            case,
            timeline[timeline.case_id.eq(case.case_id)],
            sheet[sheet.case_id.eq(case.case_id)],
            root / case.figure_path,
        )
    for candidate_id, group in slots.groupby("candidate_id", sort=True):
        plot_snapshots(
            candidate_id,
            group,
            tables["spatial_points"],
            tables["spatial_polygons"],
            tables["spatial_geometry"],
            figures / f"phase3a2_{candidate_id}_spatial.png",
        )
    body = [
        f"<h1>Phase 3A-2A: {STATUS}</h1>",
        "<p>Human calibration only. No labels, boundary decisions, segmentation rules or outcomes are supplied. Inspect full context and missing observations before annotating the CSV. Confidence: 1 low, 2 moderate, 3 high. All five human fields are blank.</p>",
        "<ul>"
        + "".join(
            f"<li><b>{label}</b>: {escape(definition)}</li>"
            for label, definition in LABELS.items()
        )
        + "</ul>",
        '<p><a href="../diagnostics/phase3a2_boundary_review_sheet.csv">Blank human review worksheet</a> · <a href="../diagnostics/phase3a2_spatial_geometry.csv">All geometry variants, statuses and support</a></p>',
        tables["category_coverage"].to_html(index=False, escape=True),
        "<ol>"
        + "".join(
            f'<li><a href="#{c.case_id}">{c.case_id}: {escape(c.selection_reason)}</a></li>'
            for c in manifest.itertuples(index=False)
        )
        + "</ol>",
    ]
    for _, case in manifest.iterrows():
        cid = case.case_id
        body.extend(
            [
                f'<section id="{cid}"><h2>{cid} — {escape(case.review_group)}</h2>',
                f"<p>{escape(case.selection_reason)}. Restart context: <b>{escape(case.restart_context or 'none supplied')}</b>. These are review sampling descriptions, not human judgments.</p>",
                case[SUMMARY_FIELDS]
                .to_frame("value")
                .to_html(escape=True, na_rep="unavailable"),
                f'<img loading="lazy" src="../figures/phase3a2_{cid}_progression.png" alt="{cid} ordered observations">',
                f"<p>{TRACE_CAPTION} End vertices use action-start timestamps, not arrival times.</p>",
            ]
        )
        for candidate_id in slots.loc[slots.case_id.eq(cid), "candidate_id"].unique():
            body.append(
                f'<img loading="lazy" src="../figures/phase3a2_{candidate_id}_spatial.png" alt="{candidate_id} spatial snapshots">'
            )
        candidates = sheet[sheet.case_id.eq(cid)]
        body.extend(
            [
                "<details><summary>Candidate diagnostics and blank human fields</summary><div class=scroll>",
                candidates.to_html(index=False, escape=True, na_rep="unavailable"),
                "</div></details>",
                f'<p><a href="../diagnostics/phase3a2_{cid}_timeline.csv">Complete timeline CSV</a></p>',
                "<details><summary>Complete ordered event timeline</summary><div class=scroll>",
                timeline[timeline.case_id.eq(cid)].to_html(
                    index=False, escape=True, na_rep="unavailable"
                ),
                "</div></details></section>",
            ]
        )
    body.append(
        "<p>Next: human Phase 3A-2B review. Phase 3A-3 considers calibration and method lock only after human labels are supplied; no sampling criterion is approved for production.</p>"
    )
    html = (
        "<!doctype html><html lang=en><meta charset=utf-8><title>Phase 3A-2A review pack</title><style>body{font:15px system-ui;margin:2rem;max-width:1500px}img{width:100%;height:auto}table{border-collapse:collapse;font-size:12px}td,th{padding:5px;border:1px solid #ddd}.scroll{overflow:auto;max-height:600px}section{border-top:2px solid #999;margin-top:3rem}details{margin:1rem 0}a{color:#8e4010}</style><body>"
        + "\n".join(body)
        + "</body></html>"
    )
    (review / "phase3a2_boundary_review.html").write_text(html, encoding="utf-8")
    assert sheet[HUMAN_COLUMNS].fillna("").eq("").all().all()
    return len(manifest), slots.candidate_id.nunique()

"""Phase 5B: exact TO outcomes, fixed descriptive bins and bounded associations."""

import numpy as np
import pandas as pd

from leverkusen.models.clustered_logistic import fit_logistic
from leverkusen.spatial.progression_change import THIRDS, scope_mask, starting_third

PRIMARY = "delta_opp_centroid_x"
METRICS = (PRIMARY, "delta_opp_visible_width", "delta_opp_visible_depth",
           "delta_opp_mean_nearest_neighbor_distance", "delta_lev_centroid_x")
LABELS = {PRIMARY: "Opponent centroid x", "delta_opp_visible_width": "Opponent width",
          "delta_opp_visible_depth": "Opponent depth",
          "delta_opp_mean_nearest_neighbor_distance": "Opponent NN spacing",
          "delta_lev_centroid_x": "Leverkusen centroid x"}
CONTROLS = ("action_delta_x", "action_start_x", "anchor_gap_seconds")
COUNT = "delta_opp_visible_player_count"
FLAGS = tuple(f"{end}_frame_{flag}{unknown}" for end in ("from", "to")
              for flag in ("oob", "coincident") for unknown in ("", "_unknown"))
SOURCE_COLUMNS = ["match_id", "attacking_control_spell_id", "from_event_id", "to_event_id",
                  "from_event_index", "to_event_index", "action_type", "to_event_type",
                  *CONTROLS, "starting_third", *METRICS, COUNT, *FLAGS]
OUTCOMES = [f"{family}_{h}s" for h in (5, 10, 15)
            for family in ("box_entry_within", "shot_within", "future_xg")]
REFERENCE = ["reference_is_box_entry", "reference_is_shot"]


def join_to_outcomes(transitions, outcomes):
    """Join by match + exact TO UUID; fail on missing/ambiguous/conflicting identity."""
    source = transitions[SOURCE_COLUMNS].copy()
    if source.duplicated(["match_id", "from_event_id", "to_event_id"]).any():
        raise ValueError("Duplicate Phase 4A transition")
    key = ["match_id", "reference_event_id"]
    if outcomes.duplicated(key).any():
        raise ValueError("Duplicate Phase 5A reference")
    selected = outcomes[[*key, "attacking_control_spell_id", "reference_event_index",
                         "reference_event_type", *REFERENCE, *OUTCOMES]].rename(
                             columns={"attacking_control_spell_id": "outcome_spell_id"})
    joined = source.merge(selected, left_on=["match_id", "to_event_id"], right_on=key,
                          how="left", validate="many_to_one", indicator=True)
    missing = joined[~joined._merge.eq("both")]
    if len(missing):
        raise ValueError("Missing exact TO outcome: " + missing[["match_id", "to_event_id"]].to_json(orient="records"))
    for left, right in (("attacking_control_spell_id", "outcome_spell_id"),
                        ("to_event_index", "reference_event_index"),
                        ("to_event_type", "reference_event_type")):
        if not joined[left].eq(joined[right]).all():
            raise ValueError(f"TO context mismatch: {left}")
    if not joined.from_event_index.lt(joined.to_event_index).all():
        raise ValueError("Transition source ordering failed")
    if not joined.action_type.isin(["Pass", "Carry"]).all():
        raise ValueError("Unexpected action type")
    if not joined.starting_third.eq(starting_third(joined.action_start_x)).all():
        raise ValueError("Inherited starting third differs")
    if not np.isfinite(joined[list(CONTROLS)]).all().all() or joined.anchor_gap_seconds.lt(0).any():
        raise ValueError("Invalid progression/start/gap context")
    for col in [*REFERENCE, *[c for c in OUTCOMES if not c.startswith("future_xg")]]:
        if not joined[col].isin([0, 1]).all():
            raise ValueError(f"Missing/nonbinary outcome: {col}")
    for col in FLAGS:
        if not joined[col].isin([True, False]).all():
            raise ValueError(f"Invalid inherited frame flag: {col}")
    return joined[[*SOURCE_COLUMNS, *REFERENCE, *OUTCOMES]].sort_values(
        ["match_id", "from_event_index", "to_event_index"]).reset_index(drop=True)


def select_scope(data, scope, outcome):
    if scope == "exclude_immediate":
        flag = "reference_is_box_entry" if outcome.startswith("box_entry") else "reference_is_shot"
        return data[data[flag].eq(0)]
    if scope == "visible_count_adjustment":
        return data
    return data[scope_mask(data, scope)]


def describe(data, horizon=10):
    box, shot, xg = (data[f"{name}_{horizon}s"] for name in
                     ("box_entry_within", "shot_within", "future_xg"))
    return dict(N=len(data), match_count=data.match_id.nunique(),
                spell_count=data.attacking_control_spell_id.nunique(),
                box_entry_positive_N=int(box.sum()), box_entry_rate=box.mean(),
                shot_positive_N=int(shot.sum()), shot_rate=shot.mean(),
                mean_future_xg=xg.mean(), proportion_positive_xg=xg.dropna().gt(0).mean(),
                positive_xg_median=xg[xg.gt(0)].median(), missing_xg_N=int(xg.isna().sum()))


def quartiles(values):
    """Action/metric-specific descriptive quartiles; tied values are never split."""
    bins, edges = pd.qcut(values, 4, labels=False, duplicates="drop", retbins=True)
    return bins + 1, edges


def analyze(data):
    """Five geometry metrics, primary centroid sensitivities; no motif inputs.

    Leverkusen centroid receives one comparison box-entry model per action.
    Shot modeling is confined to opponent centroid. xG stays descriptive.
    """
    data = data.sort_values(["match_id", "from_event_index", "to_event_index"]).reset_index(drop=True)
    summary, sensitivity = [], []
    for action_type in ("Pass", "Carry"):
        action = data[data.action_type.eq(action_type)]
        sd = {metric: action[metric].std(ddof=1) for metric in METRICS}
        for h in (5, 10, 15):
            summary.append(dict(record_type="population", action_type=action_type,
                                horizon=h, scope="all", **describe(action, h)))
        for metric in METRICS:
            valid = action[action[metric].notna()]
            bins, edges = quartiles(valid[metric])
            for q in range(1, len(edges)):
                group = valid[bins.eq(q)]
                summary.append(dict(record_type="quartile", action_type=action_type, spatial_metric=metric,
                                    horizon=10, scope="all", quartile=q, lower_edge=edges[q - 1], upper_edge=edges[q],
                                    median_spatial_change=group[metric].median(), **describe(group)))
            if metric == PRIMARY:
                # xG's primary analysis is descriptive, so repeat its quartiles
                # after excluding immediate Shots, keeping the canonical edges.
                for q in range(1, len(edges)):
                    group = valid[bins.eq(q) & valid.reference_is_shot.eq(0)]
                    sensitivity.append(dict(record_type="quartile", action_type=action_type,
                                            spatial_metric=metric, outcome="future_xg", horizon=10,
                                            scope="exclude_immediate", quartile=q,
                                            median_spatial_change=group[metric].median(), **describe(group)))
                for third in THIRDS:
                    for q in range(1, len(edges)):
                        group = valid[valid.starting_third.eq(third) & bins.eq(q)]
                        summary.append(dict(record_type="starting_third", action_type=action_type,
                                            spatial_metric=metric, horizon=10, scope="all", starting_third=third,
                                            quartile=q, median_spatial_change=group[metric].median(), **describe(group)))
            for model in ("unadjusted", "adjusted") if metric == PRIMARY else ("adjusted",):
                controls = () if model == "unadjusted" else CONTROLS
                summary.append(dict(record_type="model", action_type=action_type, spatial_metric=metric,
                                    outcome="box_entry", horizon=10, scope="all", model=model,
                                    **fit_logistic(action, "box_entry_within_10s", metric, controls, reporting_sd=sd[metric])))
        summary.append(dict(record_type="model", action_type=action_type, spatial_metric=PRIMARY,
                            outcome="shot", horizon=10, scope="all", model="adjusted",
                            **fit_logistic(action, "shot_within_10s", PRIMARY, CONTROLS, reporting_sd=sd[PRIMARY])))
        # All primary rows are copied into sensitivities, not fitted a second time.
        for outcome in ("box_entry", "shot"):
            primary = next(row for row in summary if row.get("record_type") == "model"
                           and row["action_type"] == action_type and row["spatial_metric"] == PRIMARY
                           and row["outcome"] == outcome and row["model"] == "adjusted")
            sensitivity.append(dict(primary, scope_N=len(action),
                                    **{k: v for k, v in describe(action).items() if k not in primary}))
            specs = [(scope, 10) for scope in ("gap_le_5", "gap_le_3", "exclude_immediate",
                                              "exclude_oob", "exclude_coincidence")]
            specs += [("all", 5), ("all", 15)]
            if outcome == "box_entry":
                specs.append(("visible_count_adjustment", 10))
            for scope, h in specs:
                target = f"{outcome}_within_{h}s"
                group = select_scope(action, scope, target)
                controls = (*CONTROLS, COUNT) if scope == "visible_count_adjustment" else CONTROLS
                fit = fit_logistic(group, target, PRIMARY, controls, reporting_sd=sd[PRIMARY])
                desc = describe(group, h)
                sensitivity.append(dict(record_type="model", action_type=action_type, spatial_metric=PRIMARY, scope_N=len(group),
                                        outcome=outcome, horizon=h, scope=scope, model="adjusted",
                                        **{k: v for k, v in desc.items() if k not in fit}, **fit))
    return pd.DataFrame(summary), pd.DataFrame(sensitivity)

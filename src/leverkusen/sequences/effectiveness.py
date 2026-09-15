"""Frozen Phase 4B motifs joined to terminal-anchor Phase 5A outcomes."""

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import t as student_t

from leverkusen.models.clustered_logistic import fit_logistic
from leverkusen.sequences.multi_action import motif_labels, window_scope
from leverkusen.spatial.danger_analysis import OUTCOMES, REFERENCE
from leverkusen.spatial.progression_change import THIRDS, starting_third

CONTROLS = ("total_progression", "first_action_start_x", "duration_seconds")
CENTROID = "net_opp_centroid_x"
FLAGS = [f"any_frame_{flag}{suffix}" for flag in ("oob", "coincident") for suffix in ("", "_unknown")]
KEEP = ["window_id", "match_id", "attacking_control_spell_id", "window_length",
        "action_type_motif", "direction_profile", "carry_action_count", *CONTROLS,
        "starting_third", "maximum_leg_gap", "mean_leg_gap", *[f"leg_{i}_gap_seconds" for i in (1, 2, 3)],
        CENTROID, *FLAGS]
SOURCE_COLUMNS = [*KEEP, "statsbomb_revision", "terminal_event_type", "terminal_event_team_id",
                  f"{CENTROID}_status", *[f"anchor_{i}_{c}" for i in range(4)
                                        for c in ("event_id", "event_index", "period_seconds")]]


def join_terminal_outcomes(windows, outcomes):
    """Terminal means anchor_k, not action_k or any earlier reference."""
    if windows.window_id.isna().any() or windows.window_id.duplicated().any():
        raise ValueError("Missing/duplicate window ID")
    if not windows.window_length.isin([2, 3]).all():
        raise ValueError("Unsupported window length")
    data = windows[KEEP].copy()
    for length in (2, 3):
        mask = windows.window_length.eq(length)
        selected = windows.loc[mask]
        if not selected.action_type_motif.isin(motif_labels(length)).all():
            raise ValueError("Unknown locked action motif")
        if not selected.direction_profile.isin(motif_labels(length, "direction")).all():
            raise ValueError("Unknown locked direction profile")
        if not selected.carry_action_count.eq(selected.action_type_motif.str.count("C")).all():
            raise ValueError("Carry count differs from frozen motif")
        gaps = selected[[f"leg_{i}_gap_seconds" for i in range(1, length + 1)]]
        if not np.isfinite(gaps).all().all() or gaps.lt(0).any().any():
            raise ValueError("Invalid leg gaps")
        for observed, expected in ((selected.maximum_leg_gap, gaps.max(axis=1)),
                                   (selected.mean_leg_gap, gaps.mean(axis=1)),
                                   (selected.duration_seconds, gaps.sum(axis=1))):
            if not np.allclose(observed, expected, rtol=0, atol=1e-9):
                raise ValueError("Frozen strict-chain gap metadata differs")
        indices = selected[[f"anchor_{i}_event_index" for i in range(length + 1)]].to_numpy()
        if not np.isfinite(indices).all() or not (np.diff(indices, axis=1) > 0).all():
            raise ValueError("Invalid anchor source ordering")
        if not np.allclose(selected[f"anchor_{length}_period_seconds"] - selected.anchor_0_period_seconds,
                           selected.duration_seconds, rtol=0, atol=1e-9):
            raise ValueError("Window duration disagrees with terminal clock")
        data.loc[mask, "terminal_anchor_event_id"] = selected[f"anchor_{length}_event_id"]
        data.loc[mask, "terminal_anchor_event_index"] = selected[f"anchor_{length}_event_index"]
        data.loc[mask, "terminal_seconds"] = selected[f"anchor_{length}_period_seconds"]
    if not np.isfinite(data[list(CONTROLS)]).all().all():
        raise ValueError("Nonfinite frozen context")
    if not data.starting_third.eq(starting_third(data.first_action_start_x)).all():
        raise ValueError("Inherited starting-third mismatch")
    for flag in FLAGS:
        if not data[flag].isin([True, False]).all():
            raise ValueError("Invalid inherited whole-window support flag")
    key = ["match_id", "reference_event_id"]
    if outcomes[key].isna().any().any() or outcomes.duplicated(key).any():
        raise ValueError("Ambiguous Phase 5A reference identity")
    selected = outcomes[[*key, "attacking_control_spell_id", "reference_event_index",
                         "reference_timestamp", "reference_event_type", *REFERENCE, *OUTCOMES]].rename(
                             columns={"attacking_control_spell_id": "outcome_spell_id"})
    data = data.merge(selected, left_on=["match_id", "terminal_anchor_event_id"],
                      right_on=key, how="left", validate="many_to_one", indicator=True)
    missing = data[~data._merge.eq("both")]
    if not missing.empty:
        raise ValueError("Missing exact terminal outcome: " + missing[["window_id", "terminal_anchor_event_id"]].to_json(orient="records"))
    if not data.attacking_control_spell_id.eq(data.outcome_spell_id).all():
        raise ValueError("Terminal outcome crosses spell")
    if not data.terminal_anchor_event_index.eq(data.reference_event_index).all():
        raise ValueError("Terminal event index mismatch")
    expected_type = data.window_id.map(windows.set_index("window_id").terminal_event_type)
    if not data.reference_event_type.eq(expected_type).all():
        raise ValueError("Terminal event type mismatch")
    if not np.allclose(pd.to_timedelta(data.reference_timestamp).dt.total_seconds(), data.terminal_seconds, rtol=0, atol=1e-9):
        raise ValueError("Terminal outcome clock mismatch")
    for col in [*REFERENCE, *[c for c in OUTCOMES if not c.startswith("future_xg")]]:
        if not data[col].isin([0, 1]).all():
            raise ValueError(f"Invalid binary outcome: {col}")
    return data[[*KEEP, "terminal_anchor_event_id", "terminal_anchor_event_index",
                 *REFERENCE, *OUTCOMES]].sort_values(["window_length", "match_id", "window_id"]).reset_index(drop=True)


def select_scope(data, scope, outcome="box_entry"):
    if scope == "exclude_immediate":
        flag = "reference_is_box_entry" if outcome == "box_entry" else "reference_is_shot"
        return data[data[flag].eq(0)]
    if scope == "centroid_adjusted":
        return data[data[CENTROID].notna()]
    return data[window_scope(data, scope)]


def description(group, horizon=10):
    box, shot, xg = (group[f"{name}_{horizon}s"] for name in ("box_entry_within", "shot_within", "future_xg"))
    return dict(N=len(group), matches=group.match_id.nunique(),
                median_total_progression=group.total_progression.median(),
                median_start_x=group.first_action_start_x.median(),
                median_duration=group.duration_seconds.median(),
                box_entry_N=int(box.sum()), box_entry_rate=box.mean(), shot_N=int(shot.sum()), shot_rate=shot.mean(),
                mean_future_xg=xg.mean(), proportion_positive_xg=xg.dropna().gt(0).mean(),
                mean_positive_xg=xg[xg.gt(0)].mean(), missing_xg_N=int(xg.isna().sum()))


def encode_motifs(data, length, *, include_motifs=True, centroid=False):
    """Treatment coding in the locked PP/PPP-first ordering, with raw controls."""
    if not data.window_length.eq(length).all():
        raise ValueError("Window lengths must be modeled separately")
    labels = motif_labels(length)
    columns = {}
    if include_motifs:
        columns.update({f"motif_{m}": data.action_type_motif.eq(m).astype(float) for m in labels[1:]
                        if data.action_type_motif.eq(m).any()})
    columns.update({c: data[c] for c in CONTROLS})
    if centroid:
        columns[CENTROID] = data[CENTROID]
    return pd.DataFrame(columns, index=data.index)


def fit_design(group, length, target, *, include_motifs=True, centroid=False):
    design = encode_motifs(group, length, include_motifs=include_motifs, centroid=centroid)
    columns = design.columns.tolist()
    frame = design.assign(match_id=group.match_id, response=group[target])
    return fit_logistic(frame, "response", columns[0], columns[1:], return_parameters=True)


def contrast(fit, vector):
    if fit["model_status"] != "ok":
        return dict(coefficient=np.nan, cluster_se=np.nan, odds_ratio=np.nan, or_ci_low=np.nan, or_ci_high=np.nan)
    beta = float(vector @ fit["parameters"])
    se = np.sqrt(max(0, vector @ fit["covariance"] @ vector))
    margin = student_t.ppf(.975, fit["cluster_count"] - 1) * se
    return dict(coefficient=beta, cluster_se=se, odds_ratio=np.exp(beta),
                or_ci_low=np.exp(beta - margin), or_ci_high=np.exp(beta + margin))


def model_rows(data, length, *, outcome="box_entry", horizon=10, scope="all", medians=None):
    group = select_scope(data[data.window_length.eq(length)], scope, outcome)
    centroid = scope == "centroid_adjusted"
    controls = [*CONTROLS, *([CENTROID] if centroid else [])]
    target = f"{outcome}_within_{horizon}s"
    group = group.dropna(subset=[target, *controls]).copy()
    labels = motif_labels(length)
    reference = labels[0]
    # Pure-outcome motif cells make an unpenalized dummy coefficient diverge.
    # Keep their descriptive rows, but do not force an OR for them.
    cells = group.groupby("action_type_motif")[target].agg(["size", "sum"])
    separated = cells.index[(cells["sum"] == 0) | (cells["sum"] == cells["size"])].tolist()
    model_group = group[~group.action_type_motif.isin(separated)]
    if reference not in set(model_group.action_type_motif):
        fit = dict(model_status="reference_missing_or_separated", N=len(model_group), cluster_count=model_group.match_id.nunique())
        baseline = fit
    else:
        fit = fit_design(model_group, length, target, centroid=centroid)
        baseline = (fit_design(model_group, length, target, include_motifs=False)
                    if scope == "all" and outcome == "box_entry" and horizon == 10 else {})
    common = dict(record_type="model", window_length=length, scope=scope, horizon=horizon, outcome=outcome,
                  reference_motif=reference, model_N=len(model_group), model_matches=model_group.match_id.nunique(),
                  excluded_separated_N=len(group) - len(model_group),
                  separated_motifs=";".join(separated), mcfadden_r2=fit.get("mcfadden_r2", np.nan),
                  delta_mcfadden_r2=fit.get("mcfadden_r2", np.nan) - baseline.get("mcfadden_r2", np.nan),
                  max_score=fit.get("max_score", np.nan), information_condition=fit.get("information_condition", np.nan))
    medians = medians if medians is not None else data.loc[data.window_length.eq(length), list(CONTROLS)].median()
    rows = []
    for motif in labels:
        sample = group[group.action_type_motif.eq(motif)]
        status = "separated_motif_cell" if motif in separated else "absent_motif" if sample.empty else fit["model_status"]
        row = dict(common, motif=motif, motif_N=len(sample), motif_positive_N=int(sample[target].sum()),
                   motif_matches=sample.match_id.nunique(), model_status=status,
                   predicted_probability=np.nan, probability_ci_low=np.nan, probability_ci_high=np.nan,
                   **{f"at_{c}": medians[c] for c in CONTROLS})
        if centroid:
            row[f"at_{CENTROID}"] = group[CENTROID].median()
        if status == "ok":
            vector = np.zeros(len(fit["terms"]))
            if motif != reference:
                vector[fit["terms"].index(f"motif_{motif}")] = 1
            row.update(contrast(fit, vector))
            prediction = vector.copy()
            prediction[0] = 1
            for control in CONTROLS:
                prediction[fit["terms"].index(control)] = medians[control]
            if centroid:
                prediction[fit["terms"].index(CENTROID)] = group[CENTROID].median()
            eta = float(prediction @ fit["parameters"])
            se = np.sqrt(max(0, prediction @ fit["covariance"] @ prediction))
            margin = student_t.ppf(.975, fit["cluster_count"] - 1) * se
            row.update(predicted_probability=expit(eta), probability_ci_low=expit(eta - margin), probability_ci_high=expit(eta + margin))
        else:
            row.update(contrast(dict(model_status=status), None))
        rows.append(row)
    if length == 2:
        row = dict(common, record_type="contrast", motif="PC_vs_CP", model_status=fit["model_status"])
        if fit["model_status"] == "ok" and all(f"motif_{m}" in fit["terms"] for m in ("PC", "CP")):
            vector = np.zeros(len(fit["terms"]))
            vector[fit["terms"].index("motif_PC")] = 1
            vector[fit["terms"].index("motif_CP")] = -1
            row.update(contrast(fit, vector))
        else:
            row["model_status"] = "contrast_not_estimable"
            row.update(contrast(row, None))
        rows.append(row)
    return rows


def raw_motifs(data, length, *, horizon=10, scope="all", outcome="box_entry", system="action"):
    group = select_scope(data[data.window_length.eq(length)], scope, outcome)
    column = "action_type_motif" if system == "action" else "direction_profile"
    return [dict(record_type="raw_motif" if system == "action" else "direction", window_length=length,
                 scope=scope, horizon=horizon, outcome=outcome, motif=motif,
                 share_of_windows=group[column].eq(motif).mean(),
                 **description(group[group[column].eq(motif)], horizon)) for motif in motif_labels(length, system)]


def analyze(data):
    data = data.sort_values(["window_length", "match_id", "window_id"]).reset_index(drop=True)
    main, sensitivity = [], []
    for length in (2, 3):
        main.extend(raw_motifs(data, length))
        main.extend(model_rows(data, length))
        main.extend(raw_motifs(data, length, system="direction"))
        for third in THIRDS:
            for row in raw_motifs(data[data.starting_third.eq(third)], length):
                main.append(dict(row, record_type="starting_third", starting_third=third))
    for count in range(4):
        group = data[data.window_length.eq(3) & data.carry_action_count.eq(count)]
        main.append(dict(record_type="carry_count", window_length=3, scope="all", horizon=10,
                         carry_count=count, **description(group)))
    main.extend(model_rows(data, 2, outcome="shot"))
    for scope, horizon in [("all", 5), ("all", 15), ("gap_le_5", 10), ("gap_le_3", 10),
                           ("exclude_immediate", 10), ("exclude_oob", 10), ("exclude_coincidence", 10)]:
        sensitivity.extend(model_rows(data, 2, scope=scope, horizon=horizon))
        sensitivity.extend(raw_motifs(data, 3, scope=scope, horizon=horizon))
    sensitivity.extend(model_rows(data, 2, scope="exclude_immediate", outcome="shot"))
    for length in (2, 3):
        sensitivity.extend(raw_motifs(data, length, scope="exclude_immediate", outcome="shot"))
    # Explanatory spatial adjustment follows the primary models; no other geometry.
    sensitivity.extend(model_rows(data, 2, scope="centroid_adjusted"))
    return pd.DataFrame(main), pd.DataFrame(sensitivity)

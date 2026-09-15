"""Phase 6A relative visible context; no formation or block inference."""

import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.stats import t as student_t

from leverkusen.models.clustered_logistic import fit_logistic
from leverkusen.sequences.effectiveness import contrast
from leverkusen.spatial.danger_analysis import CONTROLS, FLAGS, OUTCOMES, PRIMARY, REFERENCE
from leverkusen.spatial.progression_change import THIRDS, clustered_regression, scope_mask, starting_third

DIMENSIONS = {"centroid": ("opp_centroid_x", "opp_centroid_x_from"),
              "width": ("opp_visible_width", "opp_width_from"),
              "depth": ("opp_visible_depth", "opp_depth_from"),
              "spacing": ("opp_mean_nearest_neighbor_distance", "opp_mean_nearest_neighbor_distance_from")}
LABELS = {"centroid": ("advanced visible centroid", "middle visible centroid", "deep visible centroid"),
          "width": ("narrow visible structure", "medium visible width", "wide visible structure"),
          "depth": ("shallow visible extent", "medium visible depth", "deep visible extent"),
          "spacing": ("tight visible spacing", "medium visible spacing", "loose visible spacing")}
COUNT = "opp_visible_count_from"
GEOMETRY = [*[pair[0] for pair in DIMENSIONS.values()], "opp_visible_player_count"]
ANCHOR_COLUMNS = ["match_id", "event_id", "event_index", "event_type", "attacking_control_spell_id", "statsbomb_revision",
                  *GEOMETRY, *[f"{c}_{s}" for c in GEOMETRY for s in ("status", "available")]]
BASE_COLUMNS = ["match_id", "attacking_control_spell_id", "from_event_id", "to_event_id", "from_event_index", "to_event_index",
                "action_type", "to_event_type", *CONTROLS, "starting_third", PRIMARY, "delta_opp_visible_width", "delta_opp_visible_depth",
                "delta_opp_mean_nearest_neighbor_distance", "delta_lev_centroid_x", "delta_opp_visible_player_count", *FLAGS, *REFERENCE, *OUTCOMES]


def attach_start_geometry(data, anchors, *, id_column, index_column=None, type_column=None):
    """Use only the exact starting UUID; never fall back to TO geometry."""
    if anchors.duplicated(["match_id", "event_id"]).any():
        raise ValueError("Ambiguous anchor identity")
    renamed = anchors.rename(columns={"event_id": "context_event_id", "event_index": "context_event_index",
                                       "event_type": "context_event_type", "attacking_control_spell_id": "context_spell_id"})
    joined = data.merge(renamed, left_on=["match_id", id_column], right_on=["match_id", "context_event_id"],
                        how="left", validate="many_to_one", indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Missing exact starting anchor geometry")
    if not joined.attacking_control_spell_id.eq(joined.context_spell_id).all():
        raise ValueError("Starting anchor crosses locked spell")
    for reference, actual in ((index_column, "context_event_index"), (type_column, "context_event_type")):
        if reference and not joined[reference].eq(joined[actual]).all():
            raise ValueError(f"Starting anchor context mismatch: {reference}")
    output = joined[data.columns].copy()
    names = {source: target for source, target in DIMENSIONS.values()}
    names["opp_visible_player_count"] = COUNT
    for source, target in names.items():
        available = joined[f"{source}_available"]
        if not available.isin([True, False]).all():
            raise ValueError("Invalid inherited metric availability")
        if (available & (~joined[f"{source}_status"].eq("ok") | ~np.isfinite(joined[source]))).any():
            raise ValueError("Available context geometry is invalid")
        # Preserve supplied values; availability determines whether a bin can exist.
        output[target] = joined[source]
        output[f"{target}_available"] = available.astype(bool)
    return output


def fit_cutpoints(data):
    """Pooled-action, within-start-third tertiles; no outcome columns consumed."""
    rows = []
    for dimension, (_, column) in DIMENSIONS.items():
        for third in THIRDS:
            values = data.loc[data.starting_third.eq(third) & data[f"{column}_available"], column].dropna()
            if values.empty:
                raise ValueError(f"No context support: {dimension}/{third}")
            low, high = values.quantile([1 / 3, 2 / 3]).to_numpy()
            if low >= high:
                raise ValueError("Tied tertile boundaries cannot identify three relative contexts")
            rows.append(dict(record_type="cutpoints", context_dimension=dimension, starting_third=third,
                             N=len(values), lower_cut=low, upper_cut=high, raw_min=values.min(), raw_max=values.max()))
    return pd.DataFrame(rows)


def assign_contexts(data, cutpoints):
    output = data.copy()
    for dimension, (_, column) in DIMENSIONS.items():
        codes = pd.Series(pd.NA, index=output.index, dtype="Int64")
        for row in cutpoints[cutpoints.context_dimension.eq(dimension)].itertuples(index=False):
            selected = output.starting_third.eq(row.starting_third) & output[f"{column}_available"] & output[column].notna()
            # Right-closed quantiles keep equal values together at exact cut points.
            codes.loc[selected] = 1 + output.loc[selected, column].gt(row.lower_cut).astype(int) + output.loc[selected, column].gt(row.upper_cut).astype(int)
        output[f"{dimension}_context"] = codes
        output[f"{dimension}_context_label"] = codes.map(dict(enumerate(LABELS[dimension], start=1)))
    return output


def construct_transitions(source, anchors):
    if source.duplicated(["match_id", "from_event_id", "to_event_id"]).any():
        raise ValueError("Duplicate frozen transition")
    if not source.starting_third.eq(starting_third(source.action_start_x)).all():
        raise ValueError("Inherited action-start thirds differ")
    data = attach_start_geometry(source[BASE_COLUMNS], anchors, id_column="from_event_id", index_column="from_event_index", type_column="action_type")
    cuts = fit_cutpoints(data)
    return assign_contexts(data, cuts).sort_values(["match_id", "from_event_index"]).reset_index(drop=True), cuts


def construct_motifs(source, windows, anchors, cuts):
    """Only k=2, with its frozen anchor_0 identity; outcomes stay terminal-aligned."""
    data = source[source.window_length.eq(2)].copy()
    identity = windows[windows.window_length.eq(2)][["window_id", "match_id", "attacking_control_spell_id", "anchor_0_event_id", "anchor_0_event_index",
                                                   "anchor_2_event_id", "total_progression", "action_type_motif"]]
    joined = data.merge(identity, on=["window_id", "match_id"], how="left", validate="one_to_one", suffixes=("", "_source"), indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Missing frozen two-action start identity")
    for col in ("attacking_control_spell_id", "action_type_motif"):
        if not joined[col].eq(joined[f"{col}_source"]).all():
            raise ValueError("Phase 5C / Phase 4B context differs")
    if not np.allclose(joined.total_progression, joined.total_progression_source, rtol=0, atol=1e-9):
        raise ValueError("Phase 5C / Phase 4B progression differs")
    if not joined.terminal_anchor_event_id.eq(joined.anchor_2_event_id).all():
        raise ValueError("Frozen terminal identity differs")
    selected = joined[[*data.columns, "anchor_0_event_id", "anchor_0_event_index"]].copy()
    if not selected.starting_third.eq(starting_third(selected.first_action_start_x)).all():
        raise ValueError("Window starting third differs")
    return assign_contexts(attach_start_geometry(selected, anchors, id_column="anchor_0_event_id", index_column="anchor_0_event_index"), cuts)


def context_description(group):
    xg = group.future_xg_10s
    return dict(N=len(group), matches=group.match_id.nunique(), positive_N=int(group.box_entry_within_10s.sum()),
                centroid_response_N=int(group[PRIMARY].notna().sum()), shot_positive_N=int(group.shot_within_10s.sum()),
                progression_median=group.action_delta_x.median(), centroid_delta_median=group[PRIMARY].median(),
                centroid_delta_mean=group[PRIMARY].mean(), box_entry_rate=group.box_entry_within_10s.mean(),
                shot_rate=group.shot_within_10s.mean(), mean_future_xg=xg.mean(), proportion_positive_xg=xg.dropna().gt(0).mean(),
                visible_count_median=group[COUNT].median())


def build_context_design(data, dimension, sd, *, visible_count=False):
    codes = data[f"{dimension}_context"]
    delta = data[PRIMARY] / sd
    design = pd.DataFrame({"centroid_per_sd": delta,
                           "context_T2": codes.eq(2).astype(float), "context_T3": codes.eq(3).astype(float)}, index=data.index)
    for code in (2, 3):
        design[f"centroid_x_T{code}"] = delta * design[f"context_T{code}"]
    for col in CONTROLS:
        design[col] = data[col]
    if visible_count:
        design[COUNT] = data[COUNT]
    return design


def fit_frame(design, data, target):
    columns = design.columns.tolist()
    return fit_logistic(design.assign(match_id=data.match_id, response=data[target]), "response", columns[0], columns[1:], return_parameters=True)


def term_results(fit, common, terms):
    rows = []
    for name in terms:
        row = dict(common, record_type="coefficient", term=name)
        if fit["model_status"] == "ok":
            vector = np.zeros(len(fit["terms"]))
            vector[fit["terms"].index(name)] = 1
            row.update(contrast(fit, vector))
            row.update(coefficient_ci_low=np.log(row["or_ci_low"]), coefficient_ci_high=np.log(row["or_ci_high"]))
        rows.append(row)
    return rows


def model_context(data, action, dimension, *, horizon=10, scope="all"):
    base = data[data.action_type.eq(action)]
    sd = base[PRIMARY].std(ddof=1)
    selected = base if scope == "visible_count" else base[scope_mask(base, scope)]
    target = f"box_entry_within_{horizon}s"
    cols = [f"{dimension}_context", PRIMARY, *CONTROLS, target, *([COUNT] if scope == "visible_count" else [])]
    group = selected.dropna(subset=cols)
    design = build_context_design(group, dimension, sd, visible_count=scope == "visible_count")
    fit = fit_frame(design, group, target)
    common = dict(action_type=action, context_dimension=dimension, horizon=horizon, scope=scope, N=len(group),
                  missing_N=len(selected)-len(group), matches=group.match_id.nunique(), positive_N=int(group[target].sum()),
                  predictor_sd=sd, model_status=fit["model_status"], mcfadden_r2=fit["mcfadden_r2"],
                  max_score=fit["max_score"], information_condition=fit["information_condition"])
    terms = ["centroid_per_sd", "context_T2", "context_T3", "centroid_x_T2", "centroid_x_T3"]
    rows = term_results(fit, common, terms)
    medians = base[list(CONTROLS)].median()
    for code in (1, 2, 3):
        counts = group[group[f"{dimension}_context"].eq(code)]
        base_row = dict(common, context=code, context_label=LABELS[dimension][code-1], context_N=len(counts), context_positive_N=int(counts[target].sum()))
        if fit["model_status"] != "ok":
            rows.append(dict(base_row, record_type="context_slope"))
            continue
        vector = np.zeros(len(fit["terms"]))
        vector[fit["terms"].index("centroid_per_sd")] = 1
        if code > 1:
            vector[fit["terms"].index(f"centroid_x_T{code}")] = 1
        rows.append(dict(base_row, record_type="context_slope", **contrast(fit, vector)))
        if scope == "all" and horizon == 10 and dimension == "centroid":
            for delta_sd in (-1, 0, 1):
                point = pd.DataFrame({PRIMARY: [delta_sd * sd], f"{dimension}_context": [code], **{c: [medians[c]] for c in CONTROLS}})
                prediction = np.r_[1., build_context_design(point, dimension, sd).iloc[0].to_numpy()]
                eta = prediction @ fit["parameters"]
                se = np.sqrt(max(0, prediction @ fit["covariance"] @ prediction))
                margin = student_t.ppf(.975, fit["cluster_count"]-1) * se
                rows.append(dict(base_row, record_type="prediction", displacement_sd=delta_sd, displacement_raw=delta_sd*sd,
                                 probability=expit(eta), probability_ci_low=expit(eta-margin), probability_ci_high=expit(eta+margin),
                                 **{f"at_{c}": medians[c] for c in CONTROLS}))
    return rows


def analyze_contexts(data, cuts):
    summary = cuts.to_dict("records")
    models = []
    for action in ("Pass", "Carry"):
        base = data[data.action_type.eq(action)]
        quantiles = pd.qcut(base[PRIMARY], 4, labels=False, duplicates="drop") + 1
        for dimension in DIMENSIONS:
            for code in (1, 2, 3):
                group = base[base[f"{dimension}_context"].eq(code)]
                row = dict(record_type="context", action_type=action, context_dimension=dimension, context=code,
                           context_label=LABELS[dimension][code-1], **context_description(group))
                if dimension == "centroid":
                    valid = group.dropna(subset=[PRIMARY])
                    fit = clustered_regression(valid.action_delta_x, valid[PRIMARY], valid.match_id)
                    row.update(progression_response_slope=fit["slope"], progression_response_ci_low=fit["ci_low"],
                               progression_response_ci_high=fit["ci_high"], progression_response_rho=valid.action_delta_x.corr(valid[PRIMARY], method="spearman"))
                    for q in (1, 2, 3, 4):
                        part = group[quantiles.reindex(group.index).eq(q)]
                        summary.append(dict(record_type="displacement_quartile", action_type=action, context_dimension=dimension,
                                            context=code, quartile=q, **context_description(part)))
                summary.append(row)
            models.extend(model_context(data, action, dimension))
        for scope, horizon in [("all", 5), ("all", 15), ("gap_le_5", 10), ("gap_le_3", 10),
                               ("exclude_oob", 10), ("exclude_coincidence", 10), ("visible_count", 10)]:
            models.extend(model_context(data, action, "centroid", scope=scope, horizon=horizon))
    return pd.DataFrame(summary), pd.DataFrame(models)


def analyze_motifs(data):
    """Exactly one k=2 motif × starting-centroid interaction model."""
    if not data.window_length.eq(2).all():
        raise ValueError("Only two-action motif-context analysis is authorized")
    rows = []
    for motif in ("PP", "PC", "CP", "CC"):
        for code in (1, 2, 3):
            group = data[data.action_type_motif.eq(motif) & data.centroid_context.eq(code)]
            rows.append(dict(record_type="raw", motif=motif, context=code, N=len(group), matches=group.match_id.nunique(),
                             positive_N=int(group.box_entry_within_10s.sum()), box_entry_rate=group.box_entry_within_10s.mean()))
    controls = ("total_progression", "first_action_start_x", "duration_seconds")
    group = data.dropna(subset=["centroid_context", *controls, "box_entry_within_10s"])
    design = pd.DataFrame(index=group.index)
    for motif in ("PC", "CP", "CC"):
        design[f"motif_{motif}"] = group.action_type_motif.eq(motif).astype(float)
    for code in (2, 3):
        design[f"context_T{code}"] = group.centroid_context.eq(code).astype(float)
        for motif in ("PC", "CP", "CC"):
            design[f"{motif}_x_T{code}"] = design[f"motif_{motif}"] * design[f"context_T{code}"]
    for col in controls:
        design[col] = group[col]
    fit = fit_frame(design, group, "box_entry_within_10s")
    common = dict(model_N=len(group), model_matches=group.match_id.nunique(), model_status=fit["model_status"],
                  mcfadden_r2=fit["mcfadden_r2"], max_score=fit["max_score"])
    rows.extend(term_results(fit, common, [c for c in design if c not in controls]))
    if fit["model_status"] == "ok":
        for code in (1, 2, 3):
            for motif in ("PC", "CP", "CC", "PC_vs_CP"):
                vector = np.zeros(len(fit["terms"]))
                for label, sign in ([("PC", 1), ("CP", -1)] if motif == "PC_vs_CP" else [(motif, 1)]):
                    vector[fit["terms"].index(f"motif_{label}")] = sign
                    if code > 1:
                        vector[fit["terms"].index(f"{label}_x_T{code}")] = sign
                rows.append(dict(common, record_type="contrast", motif=motif, context=code, **contrast(fit, vector)))
    return pd.DataFrame(rows)

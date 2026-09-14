"""Single-action progression and next-observation associations, without outcomes."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from leverkusen.data.loader import STATSBOMB_REVISION
from leverkusen.data.semantic_diagnostics import TEAM_ID, field
from leverkusen.sequences.action_progression import State
from leverkusen.sequences.progression_diagnostics import provider_signals, trusted_action_vector
from leverkusen.sequences.spatial_sequences import EVENT, SPELL, require_revision
from leverkusen.spatial.calibration import MULTIPLICITY
from leverkusen.spatial.geometry import METRICS
from leverkusen.spatial.orientation import VALIDATED

RESPONSES = tuple(f"{side}_{metric}" for side in ("opp", "lev") for metric in METRICS)
HEADLINES = ("centroid_x", "centroid_y", "visible_width", "visible_depth",
             "convex_hull_area", "mean_pairwise_distance", "visible_player_count")
THIRDS = ("defensive_third", "middle_third", "attacking_third")
SCOPES = ("all", "gap_le_5", "gap_le_3", "to_leverkusen", "exclude_oob", "exclude_coincidence")


def starting_third(values):
    """Descriptive [0,40), [40,80), [80,120]; do not drop OOB starts."""
    return pd.Series(np.select([values.between(0, 40, inclusive="left"),
                               values.between(40, 80, inclusive="left"),
                               values.between(80, 120)], THIRDS, default="outside_pitch"), index=values.index)


def action_inventory(context, events):
    """Exact UUID attachment, reusing both inherited progression checks.

    State is reset only at existing spells. Historical reset replay is never run.
    The predictor remains the current action's end minus start, never relocation.
    """
    require_revision(context.statsbomb_revision)
    raw = {e.get("id"): e for e in events}
    if len(raw) != len(events) or None in raw:
        raise ValueError("Duplicate/missing raw event identity")
    members = context[context.attacking_control_spell_id.notna()].sort_values(["match_id", "source_order"])
    output = []
    for _, group in members.groupby(SPELL, sort=True):
        state = State()
        for r in group.itertuples(index=False):
            event = raw.get(r.event_id)
            if event is None or (event["index"], event["period"], event["timestamp"],
                                  field(event, "team"), field(event, "type", "name")) != (
                                      r.event_index, r.period, r.timestamp, r.event_team_id, r.event_type):
                raise ValueError("Pinned action event disagrees with Phase 3B identity/context")
            # Only action endpoint and explicit control-context fields reach measurement.
            safe = {k: event[k] for k in ("id", "type", "location", "pass", "carry", "ball_receipt") if k in event}
            vector = trusted_action_vector(safe, event_type=r.event_type, event_team_id=r.event_team_id,
                validated_anchor=r.semantics_status == VALIDATED, semantics_status=r.semantics_status,
                teams=(r.home_team_id, r.away_team_id))
            provider_context = ";".join(provider_signals(safe))
            # This is the exact inherited pass-type/restart convention.
            restart_context = field(safe.get("pass", {}), "type", "name") or ""
            row = SimpleNamespace(**{**r._asdict(), **vector, "provider_context": provider_context,
                                     "restart_context": restart_context})
            observed = state.observe(row)
            reason = (
                "not_leverkusen_pass_carry" if not vector["action_candidate"] else
                vector["action_status"] if not vector["safe_action"] else
                "failed_or_unknown_pass_endpoint" if observed is None else
                "inherited_restart_context" if observed["restart"] else
                "inherited_relocation_affected" if not observed["eligible"] else "eligible"
            )
            output.append(dict(match_id=r.match_id, event_id=r.event_id,
                action_status=reason, action_start_x=vector["start_x"], action_end_x=vector["end_x"],
                action_delta_x=vector["delta_x"], statsbomb_revision=STATSBOMB_REVISION))
    return pd.DataFrame(output)


def select_transitions(transitions, anchors, actions):
    """One explicit reconciliation reason per source pair; metric N stays separate."""
    require_revision(transitions.statsbomb_revision)
    require_revision(anchors.statsbomb_revision)
    require_revision(actions.statsbomb_revision)
    table = transitions.copy()
    if table.duplicated(["match_id", "from_event_id", "to_event_id"]).any():
        raise ValueError("Duplicate transition identity")
    cols = [*EVENT, "attacking_control_spell_id", "spatial_anchor_order", "semantics_status",
            "orientation_status", "event_type", "event_team_id", "period"]
    for endpoint in ("from", "to"):
        selected = anchors[cols].rename(columns={c: f"{endpoint}_anchor_{c}" for c in cols if c != "match_id"})
        table = table.merge(selected, left_on=["match_id", f"{endpoint}_event_id"],
            right_on=["match_id", f"{endpoint}_anchor_event_id"], how="left", validate="many_to_one")
    table = table.merge(actions.drop(columns="statsbomb_revision").rename(columns={"event_id": "from_event_id"}),
                         on=["match_id", "from_event_id"], how="left", validate="many_to_one")
    same = table.from_anchor_attacking_control_spell_id.eq(table.to_anchor_attacking_control_spell_id) & table.attacking_control_spell_id.eq(table.from_anchor_attacking_control_spell_id)
    trusted = table.from_anchor_semantics_status.eq(VALIDATED) & table.to_anchor_semantics_status.eq(VALIDATED)
    orientation = table.from_anchor_orientation_status.eq("identity_explicit") & table.to_anchor_orientation_status.isin(["identity_explicit", "rotated_180"])
    finite = np.isfinite(table[["action_start_x", "action_end_x", "action_delta_x"]]).all(axis=1)
    reasons = np.select([
        table.from_anchor_event_id.isna() | table.to_anchor_event_id.isna(), ~same,
        table.from_anchor_period.ne(table.to_anchor_period),
        table.to_anchor_spatial_anchor_order.ne(table.from_anchor_spatial_anchor_order + 1),
        table.from_anchor_event_team_id.ne(TEAM_ID), ~table.from_anchor_event_type.isin(["Pass", "Carry"]),
        ~trusted, ~orientation, table.action_status.isna(), table.action_status.ne("eligible"), ~finite,
    ], ["missing_exact_anchor", "cross_spell", "cross_period", "not_next_trusted_anchor",
        "opponent_from_anchor", "not_pass_carry_from_anchor", "unsupported_semantics",
        "invalid_orientation", "missing_exact_action", table.action_status.fillna("missing_exact_action"),
        "invalid_progression_vector"], default="eligible")
    audit = table[["match_id", "from_event_id", "to_event_id"]].assign(selection_reason=reasons)
    data = table.loc[audit.selection_reason.eq("eligible")].copy()
    if not np.allclose(data.action_delta_x, data.action_end_x - data.action_start_x, rtol=0, atol=1e-12):
        raise ValueError("Progression delta disagrees with explicit action vector")
    # Phase 3B deltas are consumed verbatim; metric-specific missingness is retained.
    support = [f"{end}_{c}" for end in ("from", "to") for c in (
        "visible_area_fraction", "actor_status", "frame_oob", "frame_oob_unknown",
        "frame_coincident", "frame_coincident_unknown",
        "opp_n_valid_points_used", "lev_n_valid_points_used", "opp_goalkeeper_policy", "lev_goalkeeper_policy")]
    keep = ["match_id", "period", "provider_possession_id", "attacking_control_spell_id",
            "from_event_id", "to_event_id", "from_event_index", "to_event_index",
            "from_event_type", "to_event_type", "to_event_team_id", "action_status",
            "action_start_x", "action_end_x", "action_delta_x", "seconds_from_previous_anchor",
            "events_from_previous_anchor", "intervening_event_count", "statsbomb_revision", *support,
            *[f"delta_{r}{s}" for r in RESPONSES for s in ("", "_status")]]
    data = data[keep].rename(columns={"from_event_type": "action_type", "seconds_from_previous_anchor": "anchor_gap_seconds"})
    data["action_abs_delta_x"] = data.action_delta_x.abs()
    data["starting_third"] = starting_third(data.action_start_x)
    for response in RESPONSES:
        value, status = data[f"delta_{response}"], data[f"delta_{response}_status"]
        if not (value.notna().eq(status.eq("ok"))).all():
            raise ValueError(f"Phase 3B metric delta/status mismatch: {response}")
    return data.sort_values(["match_id", "from_event_index"]).reset_index(drop=True), audit


def scope_mask(data, scope):
    if scope == "all":
        return pd.Series(True, index=data.index)
    if scope in ("gap_le_5", "gap_le_3"):
        return data.anchor_gap_seconds.le(int(scope[-1]))
    if scope == "to_leverkusen":
        return data.to_event_team_id.eq(TEAM_ID)
    if scope in ("exclude_oob", "exclude_coincidence"):
        flag = "oob" if scope == "exclude_oob" else "coincident"
        return ~data[[f"{end}_frame_{flag}{suffix}" for end in ("from", "to") for suffix in ("", "_unknown")]].any(axis=1)
    raise ValueError(f"Unknown scope: {scope}")


def clustered_regression(x, y, matches):
    """OLS y ~ 1 + x with one-way match CR1 covariance; no iid p-values.

    Sandwich correction G/(G-1)*(N-1)/(N-2); 95% t interval uses G-1 df.
    Same one-cluster covariance convention as statsmodels cov_cluster.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    n, g = len(x), len(np.unique(matches))
    result = dict(slope=np.nan, intercept=np.nan, cluster_se=np.nan, ci_low=np.nan,
                  ci_high=np.nan, r_squared=np.nan, cluster_count=g, regression_status="insufficient_or_constant_x")
    if n < 3 or np.ptp(x) == 0:
        return result
    design = np.column_stack([np.ones(n), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    residual = y - design @ beta
    total = np.sum((y - y.mean()) ** 2)
    result.update(slope=beta[1], intercept=beta[0], r_squared=1 - residual @ residual / total if total else np.nan,
                  regression_status="insufficient_match_clusters" if g < 2 else "ok")
    if g >= 2:
        bread = np.linalg.inv(design.T @ design)
        scores = pd.DataFrame(design * residual[:, None]).groupby(np.asarray(matches), sort=True).sum().to_numpy()
        covariance = bread @ (scores.T @ scores) @ bread * g / (g - 1) * (n - 1) / (n - 2)
        se = np.sqrt(max(0, covariance[1, 1]))
        margin = student_t.ppf(.975, g - 1) * se
        result.update(cluster_se=se, ci_low=beta[1] - margin, ci_high=beta[1] + margin)
    return result


def distribution(values, prefix):
    return {f"{prefix}_{name}": operation(values) for name, operation in {
        "median": lambda s: s.median(), "q25": lambda s: s.quantile(.25),
        "q75": lambda s: s.quantile(.75), "iqr": lambda s: s.quantile(.75) - s.quantile(.25),
        "p90": lambda s: s.quantile(.90), "p95": lambda s: s.quantile(.95),
        "min": lambda s: s.min(), "max": lambda s: s.max(),
    }.items()}


def metric_statistics(data, response):
    group = data[data[f"delta_{response}_status"].eq("ok")]
    x, y = group.action_delta_x, group[f"delta_{response}"]
    varying = len(group) >= 3 and x.nunique() > 1 and y.nunique() > 1
    return dict(N=len(group), action_eligible_N=len(data), missing_metric_N=len(data) - len(group),
        spell_count=group.attacking_control_spell_id.nunique(),
        **distribution(x, "progression"), **distribution(y, "response"),
        spearman_rho=x.corr(y, method="spearman") if varying else np.nan,
        pearson_r=x.corr(y) if varying else np.nan,
        **clustered_regression(x, y, group.match_id))


def summarize(data):
    """Fixed analyses; Pass/Carry never enter a common primary estimate."""
    data = data.sort_values(["match_id", "from_event_index"]).reset_index(drop=True)
    main, sensitivities, thirds, bins = [], [], [], []
    for action_type in ("Pass", "Carry"):
        action = data[data.action_type.eq(action_type)]
        # One nonlinear check: action-specific deciles, frozen for all responses.
        labels, edges = pd.qcut(action.action_delta_x, 10, duplicates="drop", retbins=True)
        for response in RESPONSES:
            base = dict(action_type=action_type, response_metric=response)
            primary = metric_statistics(action, response)
            main.append(dict(**base, gap_scope="all", **primary))
            for scope in SCOPES[1:]:
                if scope == "exclude_coincidence" and response.split("_", 1)[1] not in MULTIPLICITY:
                    continue
                stats = metric_statistics(action[scope_mask(action, scope)], response)
                sensitivities.append(dict(**base, gap_scope=scope, **stats,
                    primary_N=primary["N"], primary_slope=primary["slope"], primary_rho=primary["spearman_rho"],
                    slope_difference=stats["slope"] - primary["slope"],
                    rho_difference=stats["spearman_rho"] - primary["spearman_rho"],
                    slope_sign_preserved=np.sign(stats["slope"]) == np.sign(primary["slope"]),
                    rho_sign_preserved=np.sign(stats["spearman_rho"]) == np.sign(primary["spearman_rho"])))
            for third in (*THIRDS, "outside_pitch"):
                selected = action[action.starting_third.eq(third)]
                if not selected.empty or third in THIRDS:
                    thirds.append(dict(**base, starting_third=third, **metric_statistics(selected, response)))
            for index, interval in enumerate(labels.cat.categories):
                selected = action[labels.eq(interval) & action[f"delta_{response}_status"].eq("ok")]
                bins.append(dict(**base, progression_decile=index + 1, lower_edge=edges[index], upper_edge=edges[index + 1],
                    N=len(selected), progression_median=selected.action_delta_x.median(),
                    response_median=selected[f"delta_{response}"].median(),
                    response_q25=selected[f"delta_{response}"].quantile(.25),
                    response_q75=selected[f"delta_{response}"].quantile(.75)))
    return {"metric_summary": pd.DataFrame(main), "gap_sensitivity": pd.DataFrame(sensitivities),
            "starting_third_summary": pd.DataFrame(thirds), "descriptive_quantiles": pd.DataFrame(bins)}

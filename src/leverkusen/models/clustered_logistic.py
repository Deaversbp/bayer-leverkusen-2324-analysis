"""Unpenalized logistic MLE with the Phase 4A match-cluster CR1 convention."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit, logit
from scipy.stats import t as student_t


def standardize(values):
    """Sample SD (ddof=1); raw analytical columns are never overwritten."""
    values = np.asarray(values, dtype=float)
    mean, sd = values.mean(axis=0), values.std(axis=0, ddof=1)
    if not np.isfinite(sd).all() or np.any(sd <= 0):
        raise ValueError("Constant or unavailable predictor")
    return (values - mean) / sd, mean, sd


def fit_logistic(data, outcome, predictor, controls=(), *, reporting_sd=None):
    """Fit one geometry metric; no iid p-values or automatic model selection.

    Bread = inverse observed information; meat = outer products of match-level
    summed Bernoulli scores. CR1 factor G/(G-1)*(N-1)/(N-K), t(G-1) intervals.
    Scaling is numerical only. A fixed full-action SD can be used for reporting
    every sensitivity so odds ratios remain on the same scale.
    """
    columns = [predictor, *controls]
    frame = data.replace([np.inf, -np.inf], np.nan).dropna(subset=[outcome, "match_id", *columns])
    y = frame[outcome].to_numpy(dtype=float)
    n, k, g = len(frame), len(columns) + 1, frame.match_id.nunique()
    result = dict(N=n, excluded_missing_N=len(data) - n, positive_N=int(y.sum()),
                  outcome_prevalence=y.mean() if n else np.nan, cluster_count=g,
                  positive_clusters=frame.loc[frame[outcome].eq(1), "match_id"].nunique(),
                  predictor_sd=reporting_sd if reporting_sd is not None else frame[predictor].std(ddof=1),
                  coefficient=np.nan, cluster_se=np.nan, coefficient_ci_low=np.nan,
                  coefficient_ci_high=np.nan, odds_ratio=np.nan, or_ci_low=np.nan,
                  or_ci_high=np.nan, odds_ratio_1sd=np.nan, or_1sd_ci_low=np.nan,
                  or_1sd_ci_high=np.nan, log_likelihood=np.nan, mcfadden_r2=np.nan,
                  max_score=np.nan, information_condition=np.nan, iterations=0,
                  model_status="insufficient_data")
    if n <= k or g < 2 or len(np.unique(y)) < 2:
        return result
    if not np.isin(y, [0, 1]).all():
        raise ValueError("Logistic response must be binary")
    try:
        scaled, _, scales = standardize(frame[columns])
    except ValueError:
        result["model_status"] = "constant_predictor"
        return result
    design = np.column_stack([np.ones(n), scaled])
    if np.linalg.matrix_rank(design) < k:
        result["model_status"] = "rank_deficient"
        return result

    def objective(beta):
        eta = design @ beta
        return np.sum(np.logaddexp(0, eta) - y * eta)

    def score(beta):
        return design.T @ (expit(design @ beta) - y)

    def information(beta):
        prob = expit(design @ beta)
        return design.T @ ((prob * (1 - prob))[:, None] * design)

    initial = np.zeros(k)
    initial[0] = logit(y.mean())
    fit = minimize(objective, initial, jac=score, hess=information, method="trust-exact",
                   options={"gtol": 1e-7, "maxiter": 100})
    # Near the optimum the likelihood can round to identical values before the
    # score tolerance is met. A few ordinary Newton steps resolve that precision
    # limit; they do not penalize the likelihood or rescue separated models.
    polish_steps = 0
    for _ in range(3):
        if np.abs(score(fit.x)).max() < 1e-7:
            break
        try:
            candidate = fit.x - np.linalg.solve(information(fit.x), score(fit.x))
        except np.linalg.LinAlgError:
            break
        tolerance = 8 * np.finfo(float).eps * max(1, abs(objective(fit.x)))
        if objective(candidate) > objective(fit.x) + tolerance:
            break
        fit.x = candidate
        polish_steps += 1
    fit.fun = objective(fit.x)
    hessian = information(fit.x)
    condition = np.linalg.cond(hessian)
    maximum_score = np.abs(score(fit.x)).max()
    result.update(max_score=maximum_score, information_condition=condition, iterations=fit.nit + polish_steps)
    separated = np.all((design @ fit.x > 0) == y)
    if (not np.isfinite(fit.x).all() or maximum_score > 1e-5 or separated
            or np.linalg.eigvalsh(hessian).min() < 1e-8
            or condition > 1e10 or np.abs(fit.x).max() > 25):
        result["model_status"] = "unstable_or_separated"
        return result
    try:
        bread = np.linalg.inv(hessian)
    except np.linalg.LinAlgError:
        result["model_status"] = "singular_information"
        return result
    scores = design * (y - expit(design @ fit.x))[:, None]
    summed = pd.DataFrame(scores).groupby(frame.match_id.to_numpy(), sort=True).sum().to_numpy()
    covariance = bread @ (summed.T @ summed) @ bread * g / (g - 1) * (n - 1) / (n - k)
    coefficient = fit.x[1] / scales[0]
    se = np.sqrt(max(0, covariance[1, 1])) / scales[0]
    margin = student_t.ppf(.975, g - 1) * se
    low, high = coefficient - margin, coefficient + margin
    sd = result["predictor_sd"]
    null_ll = np.sum(y * np.log(y.mean()) + (1 - y) * np.log1p(-y.mean()))
    result.update(coefficient=coefficient, cluster_se=se, coefficient_ci_low=low,
                  coefficient_ci_high=high, odds_ratio=np.exp(coefficient),
                  or_ci_low=np.exp(low), or_ci_high=np.exp(high),
                  odds_ratio_1sd=np.exp(coefficient * sd), or_1sd_ci_low=np.exp(low * sd),
                  or_1sd_ci_high=np.exp(high * sd), log_likelihood=-fit.fun,
                  mcfadden_r2=1 - (-fit.fun) / null_ll, model_status="ok")
    return result

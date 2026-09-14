"""Measured Phase 4A report; interpretation is restricted to this pinned audit."""

import pandas as pd

from leverkusen.sequences.spatial_readiness import markdown
from leverkusen.spatial.progression_change import scope_mask

DECISION = "PHASE 4A — COMPLETE / STABLE SINGLE-ACTION SPATIAL RELATIONSHIPS IDENTIFIED"


def compact(frame):
    result = frame[["action_type", "response_metric", "N", "spearman_rho", "pearson_r", "slope", "r_squared"]].copy()
    result["slope_95pct_CI"] = [f"[{lo:.4f}, {hi:.4f}]" for lo, hi in zip(frame.ci_low, frame.ci_high)]
    return markdown(result)


def report(data, audit, tables):
    main, sensitivity, thirds = (tables[k] for k in ("metric_summary", "gap_sensitivity", "starting_third_summary"))
    selection = audit[audit.section.eq("selection")][["label", "N"]]
    distributions = audit[audit.section.eq("distribution")][["action_type", "label", "N", "value_median", "value_q25", "value_q75", "value_p90", "value_p95", "value_min", "value_max"]]
    composition = audit[audit.section.eq("to_anchor")][["action_type", "label", "N"]]
    gap = pd.concat([main, sensitivity[sensitivity.gap_scope.isin(["gap_le_5", "gap_le_3"])]])
    gap = gap[gap.response_metric.str.startswith("opp_")]
    slopes = gap.pivot(index=["action_type", "response_metric"], columns="gap_scope", values="slope").reset_index()
    thirds_selected = thirds[thirds.response_metric.isin(["opp_centroid_x", "opp_visible_width", "opp_visible_depth", "opp_mean_pairwise_distance"])]
    robustness = sensitivity[sensitivity.response_metric.isin(["opp_centroid_x", "opp_visible_width", "opp_mean_pairwise_distance", "opp_mean_nearest_neighbor_distance"]) & ~sensitivity.gap_scope.isin(["gap_le_5", "gap_le_3"])][["action_type", "response_metric", "gap_scope", "N", "spearman_rho", "slope"]]
    consistency, examples = [], []
    for action, group in data.groupby("action_type", sort=True):
        valid = group[group.delta_opp_centroid_x_status.eq("ok")]
        rhos = valid.groupby("match_id").apply(lambda g: g.action_delta_x.corr(g.delta_opp_centroid_x, method="spearman"), include_groups=False)
        consistency.append(dict(action_type=action, matches=len(rhos), positive_rho_matches=int(rhos.gt(0).sum()),
            minimum_rho=rhos.min(), median_rho=rhos.median(), maximum_rho=rhos.max()))
        candidates = valid[scope_mask(valid, "gap_le_3") & scope_mask(valid, "exclude_oob") &
            scope_mask(valid, "exclude_coincidence") & valid.from_opp_n_valid_points_used.eq(valid.to_opp_n_valid_points_used)]
        chosen = candidates.sort_values(["action_delta_x", "match_id", "from_event_index"], ascending=[False, True, True]).iloc[0]
        examples.append(chosen[["action_type", "match_id", "attacking_control_spell_id", "from_event_id", "to_event_id",
            "action_delta_x", "anchor_gap_seconds", "intervening_event_count", "delta_opp_centroid_x",
            "from_opp_n_valid_points_used", "to_opp_n_valid_points_used", "from_visible_area_fraction", "to_visible_area_fraction"]].to_dict())
    examples_table = pd.DataFrame(examples)
    return f"""# Phase 4A: progression-linked spatial change

**{DECISION}**

## A. Question

When a trusted Leverkusen Pass or Carry progresses toward increasing x within an attacking
control spell, how does the visible opponent structure differ at the **next trusted spatial
observation**? Corresponding Leverkusen structure is secondary. The unit is one FROM action
and its existing next anchor, not an action chain. The response is geometry(TO) minus
geometry(FROM), and the predictor is the FROM action's explicit end x minus start x.

**The clearest association is longitudinal visible-centroid change for both Pass and Carry.**
Its direction and rank association persist across the requested checks, while slope magnitude
depends on observation gap. Extent and spacing are substantially weaker and more context-dependent.
These are associations between event-aligned partial observations, not continuous player movement.

## B. Analytical sample

The frozen Phase 3B source has **40,638** within-spell transitions. The analysis retains
**14,848 Pass** and **15,527 Carry** transitions, **30,375** total, covering all **34 matches**
for each action type. Every remaining source transition has one explicit exclusion reason:

{markdown(selection)}

The vector extractor is the existing Phase 3A-1 implementation, exposed as a shared helper.
The existing `State.observe` measurement guards were moved unchanged from the historical
reset-replay script into reusable package code; no reset replay, boundary detector or ledger is
called. State starts afresh at each **locked control spell** and consumes its full ordered event
context. Failed/unknown pass endpoints cannot supply trusted progression. The inherited named
pass-type/restart convention excludes 1,391 transitions; the inherited relocation-affected
state excludes 3,012 until its previous trusted peak is restored. These are conservative inherited
eligibility restrictions, not newly fitted rules. The predictor never uses an inter-action jump,
retreat-from-peak or displacement between anchor locations.

The explicit exclusion of failed/unknown FROM endpoints implements the requested progression
validity contract. It does not condition on later shots, goals, xG, box entries or success.
No such outcome columns enter the analysis. Valid signed backward and zero progression remain.

Exact match/UUID joins recover the FROM action at pinned revision
`533862946a73608c134d18b78226b6371ce7173c`. Fetched event-record hashes must match Phase 3B's
canonical source hashes; all frozen Phase 2/3 inputs and outputs are verified unchanged.
The existing next anchor is never skipped to locate a different event. The Leverkusen-TO
sensitivity restricts existing pairs; it does not build new pairs.

### Progression and observation context

{markdown(distributions)}

Units are StatsBomb coordinate units and seconds. Full-event gap is source-position difference;
intervening-event count subtracts one. Pass typically has one intervening event, Carry zero.
That difference confers no causal interpretation. Carry progression is concentrated near zero
(median 0.2, IQR 3.4); Pass is more broadly signed (median 1.7, IQR 15.6).
The next observation need not represent arrival at the recorded action endpoint.

{markdown(composition)}

Opponent TO anchors remain: **1,224 Pass pairs (8.24%)** and **2,996 Carry pairs (19.30%)**,
mostly Pressure. Pressure supplies spatial structure, not a ball/progression variable.
Shot TO anchors are event identity only, never outcomes.

### Estimation and support

Each response uses only its existing Phase 3B delta with status `ok`, inheriting both endpoints'
Phase 2B eligibility and keeper-excluded measurements. Metric-specific N, progression and
response median/IQR/quantiles/range are in the main CSV; no imputation occurs. Endpoint
point counts, keeper policy, actor status, visible-area fractions and whole-frame anomaly
flags remain in the dataset. Unequal visible populations are not adjusted away.

Spearman rho is the primary association summary. Pearson r and OLS
`spatial_delta ~ 1 + action_delta_x` are secondary descriptive summaries. Slopes are response
units per one x-unit; hull uses squared units and counts use visible records. Standard errors
use a one-way match-clustered CR1 sandwich, with correction
`G/(G-1) × (N-1)/(N-2)`, and 95% t intervals with `G-1` degrees of freedom. Clustering by match
also contains repeated spells within matches. No naive iid p-values or significance-based
model selection are used. This follows the
[statsmodels single-cluster covariance convention](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html);
the implementation uses the explicit two-column linear algebra and a focused numerical test.

## C. Opponent structural change

{compact(main[main.response_metric.str.startswith('opp_')])}

**Position.** Opponent centroid-x is the clearest response: Pass rho **0.622**, slope **0.349**
(95% CI **0.330–0.368**, R² **0.422**); Carry rho **0.648**, slope **0.831**
(**0.798–0.865**, R² **0.604**). A 10-unit difference in progression corresponds to roughly
3.49 and 8.31 units in the fitted observed-centroid difference, respectively. This is an
association across transitions, not the measured consequence of intervening on progression.
Positive centroid-x delta means farther toward the opponent's own goal in Leverkusen's
normalized attacking direction. It does **not** measure a defensive-line retreat.
Centroid-y associations are effectively absent; no lateral tactical shift is inferred.

{markdown(pd.DataFrame(consistency))}

**Extent.** Pass progression has a modest positive width association (rho **0.169**, slope
**0.077**), much weaker depth association (rho **0.073**), and weak positive observed outfield
convex-hull footprint association (rho **0.146**). Carry width is near null (rho **−0.006**);
depth is weakly negative (rho **−0.038**). Carry hull has rho **0.008** despite a negative
linear slope: this is not a robust monotonic footprint finding. Hull remains secondary,
not complete team area or a defensive block measurement.

**Spacing.** Mean and median pairwise spacing are a correlated family, not independent effects.
Pass mean-pairwise rho is **0.111** with slope **0.019**; Carry is **−0.075** with slope **−0.056**.
Carry nearest-neighbor spacing has a somewhat clearer negative rank association (**−0.145**),
but it weakens at shorter gaps. Pass nearest-neighbor spacing is also weakly negative
(**−0.070**) even though pairwise spacing is positive, precluding a single expansion claim.

**Visible count.** Progression is positively associated with the change in visible opponent
record count (Pass rho **0.194**, Carry **0.150**). This is observation composition, not an
increase in the actual number of opponents. It reinforces the caution about missing players
and the changing view when interpreting centroid, extent and spacing together.

![Pass progression and centroid change](../outputs/figures/phase4a_pass_centroid.png)
![Carry progression and centroid change](../outputs/figures/phase4a_carry_centroid.png)
![Opponent extent changes](../outputs/figures/phase4a_opponent_extent.png)
![Opponent spacing changes](../outputs/figures/phase4a_opponent_spacing.png)

### One descriptive nonlinearity check

Action-specific progression deciles are fixed across responses; ties yield **10 Pass bins** and
**9 Carry bins**. These are presentation aids, not eligibility thresholds or tactical bins.
The figures display raw observations, decile medians and within-bin response IQR, not confidence
bands. Exact boundaries and raw metric-specific N are in `phase4a_descriptive_quantiles.csv`.
Carry's near-zero bin contains 4,252 centroid observations, versus 464 in the adjacent bin;
unequal counts are shown rather than jittered into artificial equal-sized bins.

Centroid medians are ordered in both action types, with stronger slopes at the extremes:
Pass's first/last bins have median progression −15.1/+20.1 and centroid delta −3.63/+7.54;
Carry's first/last bins are −4.7/+14.5 and −2.98/+12.38. The linear coefficient summarizes
this nonlinear monotonic pattern rather than supplying a constant local relationship.
Carry width/spacing medians show substantial plateaus near zero and decreases among more
forward actions; global slopes should not be read as uniform responses over all progression.

## D. Leverkusen structural change

{compact(main[main.response_metric.isin(['lev_centroid_x', 'lev_centroid_y', 'lev_visible_width', 'lev_visible_depth', 'lev_mean_pairwise_distance', 'lev_visible_player_count'])])}

Leverkusen centroid-x closely parallels the opponent result: Pass rho **0.612**, slope **0.368**;
Carry rho **0.661**, slope **0.869**. Both visible centroids change longitudinal position
between observations, consistent with a changing view around the event as well as possible
football reorganization. This dataset cannot separate those contributions. Leverkusen width,
depth, hull and spacing associations are mostly weak and negative; centroid-y is near null.
All nine secondary metrics, including hull and alternative spacing, remain in the main table.

## E. Pass versus Carry

The longitudinal centroid association is shared, with a larger Carry slope and stronger linear
fit. These are separate observational samples with different progression distributions, timing,
intervening events and TO-team composition; the slope contrast is **not** a controlled comparison
of the two action types. Pass has weak positive opponent width/pairwise associations, while Carry
has weak negative spacing/depth and no clear global width relationship.

![Separate descriptive slopes](../outputs/figures/phase4a_coefficient_comparison.png)

## F. Starting-position context

Only broad equal thirds are used: defensive `[0,40)`, middle `[40,80)`, attacking `[80,120]`.
These labels describe normalized starting position, not tactical zones. No eligible start lies
outside the pitch; the implementation retains such starts as `outside_pitch` if present.

{markdown(thirds_selected[['action_type', 'response_metric', 'starting_third', 'N', 'spearman_rho', 'slope']])}

Centroid direction persists in all thirds, with lower slopes nearer the attacking end.
Pass width's positive association weakens toward the attacking third. Pass depth and pairwise
spacing become negative or near null there. Carry width is positive in the defensive third,
near null/negative in the middle and negative in the attacking third; depth and pairwise
spacing also differ by third. These extent/spacing differences are material descriptive
heterogeneity. A pooled global coefficient should not become a universal football statement.

## G. Robustness

All primary pairs remain in the canonical dataset. Gap restrictions below are sensitivity
comparisons, not observation-quality thresholds. Slopes for every opponent response:

{markdown(slopes)}

**Gap sensitivity.** Centroid signs and substantial rank association persist. Pass slope changes
**0.349 → 0.306 → 0.278** (all/≤5/≤3 s), while rho is **0.622 → 0.619 → 0.608**.
Carry slope changes **0.831 → 0.733 → 0.612**, rho **0.648 → 0.627 → 0.581**.
Direction is stable; magnitude attenuates appreciably, so neither coefficient is gap-invariant.
Pass width remains broadly similar (**0.077 → 0.085 → 0.084**). Its depth, hull and spacing
retain signs but remain weak. Carry mean-pairwise slope approaches zero
(**−0.056 → −0.046 → −0.016**), as does nearest-neighbor spacing (**−0.049 → −0.039 → −0.024**).
Carry width and hull linear slopes reverse at ≤3 s, while their rank associations remain
near null; these are unstable extent summaries. Carry centroid-y's tiny sign changes do not
establish a relationship. Opponent visible-count signs persist, with some magnitude change.
No arbitrary numerical stability cutoff is introduced.

![Gap sensitivity](../outputs/figures/phase4a_gap_sensitivity.png)

**TO-team, OOB and coincidence checks.** The table compares existing next anchors and whole-frame
sensitivities. Either endpoint with the original whole-frame OOB flag (or unknown flag) excludes
the pair from OOB sensitivity only. Coincidence analogously uses original whole-frame flags;
no points are removed or deduplicated. The locked coincidence treatment is applied to counts,
centroids and spacing. Hull/width/depth remain invariant to exact repetitions under their
existing mathematical gates and receive no new coincidence treatment.

{markdown(robustness)}

Restricting existing TO anchors to Leverkusen events preserves centroid direction; Carry's
slope increases to **0.943** (Pass **0.341**), demonstrating composition-related magnitude
dependence without selecting a preferred TO-team definition. OOB exclusion leaves centroid
slopes close to primary: Pass **0.348**, Carry **0.837**. Modest Pass width and weak spacing
directions also persist. The near-zero Carry hull rho changes sign under OOB exclusion,
another reason not to elevate it. Coincidence exclusions remove only **13 Pass** and
**18 Carry** candidate pairs and negligibly alter the substantive results; tiny near-zero
lateral coefficients can change sign without becoming substantive findings.

## H. Football interpretation

**Observed result:** more forward signed Pass/Carry progression is consistently associated
with a next visible opponent centroid farther toward its own goal. Carry shows the larger
descriptive coefficient; Leverkusen's visible centroid shows a similar pattern. This is the
strongest positional baseline, whereas global extent and spacing relationships are weak,
gap-dependent or starting-position-dependent.

**Interpretive hypothesis:** the observations may reflect teams reorganizing longitudinally
as play advances, together with changes in which players and pitch area are visible around
the event. The analysis does not distinguish these explanations, identify defensive lines,
or show that an action forced a defensive response. No tactical category is assigned.

### Two illustrative transitions, without outcome selection

Rule fixed for illustration: for each action type, choose the largest positive progression
among eligible pairs with gap ≤3 s, no whole-frame OOB/coincidence flags and equal opponent
selected counts at both endpoints; ties use match and source index. Equal counts do not
establish the same players. Selection never reads downstream outcomes or the response sign.
These examples illustrate observation timing and variability, not proof of a general mechanism.

{markdown(examples_table)}

The Carry example has 49.4 x-units of recorded action progression but a next observation only
0.119 s later, with opponent centroid delta −2.17. The next event-aligned frame need not
represent the carry endpoint. It remains in the authorized all-gap sample; a short gap is
not a certificate that the full action has unfolded. The Pass example has delta x 47.5 and
centroid change +27.64 over 1.864 s. Neither is a tracked player path.

## I. Limitations

Event-aligned partial observations are not tracking. Ordinary off-ball players are anonymous;
equal endpoint counts do not identify the same individuals. Variable visible area and selected
composition can affect all geometry. Intervening events and variable timing prevent a clean
action-isolated or causal interpretation. The recorded action endpoint is not necessarily
observed by the next anchor. Match clustering accounts for within-match dependence in the
linear uncertainty estimate, not confounding, observability bias or generalization to other
seasons. Thirty-four match clusters remain a finite sample.

Metric redundancy means correlated extent/spacing measures are not independent findings.
Hull is an observed outfield convex-hull footprint and stays secondary. Inherited restart,
failed-endpoint and relocation exclusions delimit the analyzed action population. Missing
metric endpoints remain missing. No outcomes, tactical effectiveness, defensive blocks,
formations, clustering or multi-action patterns are constructed or used for conditioning.

## J. Phase decision

**{DECISION}**

The stable finding is **longitudinal visible-centroid association**, for both Pass and Carry,
with gap-dependent magnitude. Pass width offers a weaker, directionally robust extent baseline;
Carry spacing is weaker and attenuates at short gaps. There is no general robust claim of
opponent structural expansion or compression across all metrics and starting positions.

**Which aspects are clearest and most robust?** Opponent centroid-x for both action types;
modest Pass width is secondary. Carry's negative nearest-neighbor/pairwise associations are
less robust in magnitude, and its extent findings should not be promoted.

**Are these stable enough to move to multi-action spatial sequences?** Yes, as an observational
baseline: retain explicit timing, metric support and starting-position context, and do not
carry forward a universal response coefficient or defensive mechanism. The next authorized
step is **Phase 4B — Multi-Action Spatial Sequence Patterns**. This implementation stops at
Phase 4A and does not begin that work.

Reproduction: run `scripts/progression_spatial_change.py`; use `--offline` to verify and reuse
the derived action dataset without downloading raw events. The compact output family contains
the action dataset, metric summary, sensitivity summary, starting-third summary, sample audit,
descriptive quantiles, provenance manifests and six figures. Analytical CSV/figure hashes and
code/source identifiers are recorded; repeated calculations must be byte-identical. Phase 3A
segmentation, Phase 3B sequences and all locked Phase 2/3 artifacts remain unchanged.
"""

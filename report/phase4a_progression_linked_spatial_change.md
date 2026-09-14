# Phase 4A: progression-linked spatial change

**PHASE 4A — COMPLETE / STABLE SINGLE-ACTION SPATIAL RELATIONSHIPS IDENTIFIED**

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

| label | N |
| --- | --- |
| eligible | 30375 |
| failed_or_unknown_pass_endpoint | 768 |
| inherited_relocation_affected | 3012 |
| inherited_restart_context | 1391 |
| not_pass_carry_from_anchor | 194 |
| opponent_from_anchor | 4898 |

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

| action_type | label | N | value_median | value_q25 | value_q75 | value_p90 | value_p95 | value_min | value_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Carry | action_delta_x | 15527 | 0.2 | -0.3 | 3.1 | 8.84 | 14.5 | -28.1 | 77.8 |
| Carry | anchor_gap_seconds | 15527 | 1.201 | 0.559 | 2.249 | 3.871 | 5.176 | 0 | 22.126 |
| Carry | intervening_event_count | 15527 | 0 | 0 | 0 | 0 | 2 | 0 | 17 |
| Carry | events_from_previous_anchor | 15527 | 1 | 1 | 1 | 1 | 3 | 1 | 18 |
| Pass | action_delta_x | 14848 | 1.7 | -6.3 | 9.3 | 15.2 | 20.1 | -56.9 | 72.5 |
| Pass | anchor_gap_seconds | 14848 | 1.113 | 0.831 | 1.507 | 2.145 | 3.383 | 0.001 | 19.98 |
| Pass | intervening_event_count | 14848 | 1 | 1 | 1 | 1 | 2 | 0 | 21 |
| Pass | events_from_previous_anchor | 14848 | 2 | 2 | 2 | 2 | 3 | 1 | 22 |

Units are StatsBomb coordinate units and seconds. Full-event gap is source-position difference;
intervening-event count subtracts one. Pass typically has one intervening event, Carry zero.
That difference confers no causal interpretation. Carry progression is concentrated near zero
(median 0.2, IQR 3.4); Pass is more broadly signed (median 1.7, IQR 15.6).
The next observation need not represent arrival at the recorded action endpoint.

| action_type | label | N |
| --- | --- | --- |
| Carry | Carry/Leverkusen | 614 |
| Carry | Carry/opponent | 12 |
| Carry | Pass/Leverkusen | 11811 |
| Carry | Pass/opponent | 16 |
| Carry | Pressure/Leverkusen | 71 |
| Carry | Pressure/opponent | 2968 |
| Carry | Shot/Leverkusen | 35 |
| Pass | Carry/Leverkusen | 12157 |
| Pass | Carry/opponent | 1 |
| Pass | Pass/Leverkusen | 1435 |
| Pass | Pass/opponent | 6 |
| Pass | Pressure/Leverkusen | 15 |
| Pass | Pressure/opponent | 1217 |
| Pass | Shot/Leverkusen | 17 |

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

| action_type | response_metric | N | spearman_rho | pearson_r | slope | r_squared | slope_95pct_CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | opp_visible_player_count | 14848 | 0.194 | 0.195 | 0.017 | 0.038 | [0.0135, 0.0206] |
| Pass | opp_centroid_x | 14845 | 0.622 | 0.65 | 0.349 | 0.422 | [0.3296, 0.3684] |
| Pass | opp_centroid_y | 14845 | 0.011 | 0.016 | 0.007 | 0 | [-0.0046, 0.0192] |
| Pass | opp_visible_width | 14845 | 0.169 | 0.17 | 0.077 | 0.029 | [0.0616, 0.0930] |
| Pass | opp_visible_depth | 14845 | 0.073 | 0.069 | 0.028 | 0.005 | [0.0142, 0.0414] |
| Pass | opp_convex_hull_area | 14793 | 0.146 | 0.147 | 1.92 | 0.022 | [1.4359, 2.4038] |
| Pass | opp_mean_pairwise_distance | 14834 | 0.111 | 0.109 | 0.019 | 0.012 | [0.0134, 0.0247] |
| Pass | opp_median_pairwise_distance | 14834 | 0.092 | 0.094 | 0.018 | 0.009 | [0.0124, 0.0243] |
| Pass | opp_mean_nearest_neighbor_distance | 14834 | -0.07 | -0.118 | -0.013 | 0.014 | [-0.0158, -0.0103] |
| Carry | opp_visible_player_count | 15527 | 0.15 | 0.157 | 0.025 | 0.025 | [0.0162, 0.0335] |
| Carry | opp_centroid_x | 15525 | 0.648 | 0.777 | 0.831 | 0.604 | [0.7977, 0.8648] |
| Carry | opp_centroid_y | 15525 | -0.006 | 0 | 0 | 0 | [-0.0217, 0.0220] |
| Carry | opp_visible_width | 15525 | -0.006 | -0.029 | -0.024 | 0.001 | [-0.0550, 0.0069] |
| Carry | opp_visible_depth | 15525 | -0.038 | -0.098 | -0.073 | 0.01 | [-0.1031, -0.0429] |
| Carry | opp_convex_hull_area | 15433 | 0.008 | -0.057 | -1.347 | 0.003 | [-2.3867, -0.3077] |
| Carry | opp_mean_pairwise_distance | 15502 | -0.075 | -0.165 | -0.056 | 0.027 | [-0.0678, -0.0439] |
| Carry | opp_median_pairwise_distance | 15502 | -0.069 | -0.155 | -0.057 | 0.024 | [-0.0699, -0.0440] |
| Carry | opp_mean_nearest_neighbor_distance | 15502 | -0.145 | -0.223 | -0.049 | 0.05 | [-0.0556, -0.0422] |

**Position.** Opponent centroid-x is the clearest response: Pass rho **0.622**, slope **0.349**
(95% CI **0.330–0.368**, R² **0.422**); Carry rho **0.648**, slope **0.831**
(**0.798–0.865**, R² **0.604**). A 10-unit difference in progression corresponds to roughly
3.49 and 8.31 units in the fitted observed-centroid difference, respectively. This is an
association across transitions, not the measured consequence of intervening on progression.
Positive centroid-x delta means farther toward the opponent's own goal in Leverkusen's
normalized attacking direction. It does **not** measure a defensive-line retreat.
Centroid-y associations are effectively absent; no lateral tactical shift is inferred.

| action_type | matches | positive_rho_matches | minimum_rho | median_rho | maximum_rho |
| --- | --- | --- | --- | --- | --- |
| Carry | 34 | 34 | 0.527 | 0.645 | 0.752 |
| Pass | 34 | 34 | 0.513 | 0.622 | 0.738 |

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

| action_type | response_metric | N | spearman_rho | pearson_r | slope | r_squared | slope_95pct_CI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | lev_visible_player_count | 14848 | -0.078 | -0.141 | -0.013 | 0.02 | [-0.0159, -0.0094] |
| Pass | lev_centroid_x | 14848 | 0.612 | 0.655 | 0.368 | 0.429 | [0.3489, 0.3862] |
| Pass | lev_centroid_y | 14848 | 0.009 | 0.018 | 0.008 | 0 | [-0.0032, 0.0195] |
| Pass | lev_visible_width | 14848 | -0.067 | -0.087 | -0.049 | 0.008 | [-0.0659, -0.0329] |
| Pass | lev_visible_depth | 14848 | -0.047 | -0.061 | -0.027 | 0.004 | [-0.0388, -0.0145] |
| Pass | lev_mean_pairwise_distance | 14847 | -0.02 | -0.026 | -0.005 | 0.001 | [-0.0106, 0.0004] |
| Carry | lev_visible_player_count | 15527 | -0.035 | -0.129 | -0.02 | 0.017 | [-0.0274, -0.0130] |
| Carry | lev_centroid_x | 15527 | 0.661 | 0.789 | 0.869 | 0.622 | [0.8379, 0.8994] |
| Carry | lev_centroid_y | 15527 | -0.014 | -0.014 | -0.01 | 0 | [-0.0319, 0.0126] |
| Carry | lev_visible_width | 15527 | -0.005 | -0.048 | -0.051 | 0.002 | [-0.0826, -0.0187] |
| Carry | lev_visible_depth | 15527 | -0.115 | -0.168 | -0.135 | 0.028 | [-0.1653, -0.1051] |
| Carry | lev_mean_pairwise_distance | 15524 | -0.06 | -0.074 | -0.028 | 0.006 | [-0.0415, -0.0152] |

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

| action_type | response_metric | starting_third | N | spearman_rho | slope |
| --- | --- | --- | --- | --- | --- |
| Pass | opp_centroid_x | defensive_third | 2440 | 0.63 | 0.42 |
| Pass | opp_centroid_x | middle_third | 8952 | 0.613 | 0.35 |
| Pass | opp_centroid_x | attacking_third | 3453 | 0.632 | 0.279 |
| Pass | opp_visible_width | defensive_third | 2440 | 0.223 | 0.143 |
| Pass | opp_visible_width | middle_third | 8952 | 0.158 | 0.058 |
| Pass | opp_visible_width | attacking_third | 3453 | 0.09 | 0.025 |
| Pass | opp_visible_depth | defensive_third | 2440 | 0.174 | 0.104 |
| Pass | opp_visible_depth | middle_third | 8952 | 0.067 | 0.019 |
| Pass | opp_visible_depth | attacking_third | 3453 | -0.034 | -0.061 |
| Pass | opp_mean_pairwise_distance | defensive_third | 2434 | 0.17 | 0.045 |
| Pass | opp_mean_pairwise_distance | middle_third | 8948 | 0.111 | 0.013 |
| Pass | opp_mean_pairwise_distance | attacking_third | 3452 | 0.009 | -0.006 |
| Carry | opp_centroid_x | defensive_third | 2836 | 0.705 | 0.931 |
| Carry | opp_centroid_x | middle_third | 8746 | 0.656 | 0.809 |
| Carry | opp_centroid_x | attacking_third | 3943 | 0.593 | 0.682 |
| Carry | opp_visible_width | defensive_third | 2836 | 0.159 | 0.135 |
| Carry | opp_visible_width | middle_third | 8746 | -0.011 | -0.085 |
| Carry | opp_visible_width | attacking_third | 3943 | -0.151 | -0.244 |
| Carry | opp_visible_depth | defensive_third | 2836 | 0.112 | 0.046 |
| Carry | opp_visible_depth | middle_third | 8746 | -0.084 | -0.146 |
| Carry | opp_visible_depth | attacking_third | 3943 | -0.085 | -0.159 |
| Carry | opp_mean_pairwise_distance | defensive_third | 2823 | 0.053 | 0.001 |
| Carry | opp_mean_pairwise_distance | middle_third | 8736 | -0.092 | -0.082 |
| Carry | opp_mean_pairwise_distance | attacking_third | 3943 | -0.163 | -0.122 |

Centroid direction persists in all thirds, with lower slopes nearer the attacking end.
Pass width's positive association weakens toward the attacking third. Pass depth and pairwise
spacing become negative or near null there. Carry width is positive in the defensive third,
near null/negative in the middle and negative in the attacking third; depth and pairwise
spacing also differ by third. These extent/spacing differences are material descriptive
heterogeneity. A pooled global coefficient should not become a universal football statement.

## G. Robustness

All primary pairs remain in the canonical dataset. Gap restrictions below are sensitivity
comparisons, not observation-quality thresholds. Slopes for every opponent response:

| action_type | response_metric | all | gap_le_3 | gap_le_5 |
| --- | --- | --- | --- | --- |
| Carry | opp_centroid_x | 0.831 | 0.612 | 0.733 |
| Carry | opp_centroid_y | 0 | -0.008 | 0.003 |
| Carry | opp_convex_hull_area | -1.347 | 0.646 | -0.823 |
| Carry | opp_mean_nearest_neighbor_distance | -0.049 | -0.024 | -0.039 |
| Carry | opp_mean_pairwise_distance | -0.056 | -0.016 | -0.046 |
| Carry | opp_median_pairwise_distance | -0.057 | -0.02 | -0.047 |
| Carry | opp_visible_depth | -0.073 | -0.034 | -0.062 |
| Carry | opp_visible_player_count | 0.025 | 0.02 | 0.02 |
| Carry | opp_visible_width | -0.024 | 0.018 | -0.027 |
| Pass | opp_centroid_x | 0.349 | 0.278 | 0.306 |
| Pass | opp_centroid_y | 0.007 | 0.002 | 0.003 |
| Pass | opp_convex_hull_area | 1.92 | 2.376 | 2.242 |
| Pass | opp_mean_nearest_neighbor_distance | -0.013 | -0.01 | -0.011 |
| Pass | opp_mean_pairwise_distance | 0.019 | 0.023 | 0.023 |
| Pass | opp_median_pairwise_distance | 0.018 | 0.023 | 0.023 |
| Pass | opp_visible_depth | 0.028 | 0.034 | 0.034 |
| Pass | opp_visible_player_count | 0.017 | 0.019 | 0.018 |
| Pass | opp_visible_width | 0.077 | 0.084 | 0.085 |

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

| action_type | response_metric | gap_scope | N | spearman_rho | slope |
| --- | --- | --- | --- | --- | --- |
| Pass | opp_centroid_x | to_leverkusen | 13621 | 0.625 | 0.341 |
| Pass | opp_centroid_x | exclude_oob | 12300 | 0.623 | 0.348 |
| Pass | opp_centroid_x | exclude_coincidence | 14832 | 0.622 | 0.349 |
| Pass | opp_visible_width | to_leverkusen | 13621 | 0.18 | 0.085 |
| Pass | opp_visible_width | exclude_oob | 12300 | 0.165 | 0.078 |
| Pass | opp_mean_pairwise_distance | to_leverkusen | 13610 | 0.124 | 0.021 |
| Pass | opp_mean_pairwise_distance | exclude_oob | 12291 | 0.106 | 0.02 |
| Pass | opp_mean_pairwise_distance | exclude_coincidence | 14821 | 0.111 | 0.019 |
| Pass | opp_mean_nearest_neighbor_distance | to_leverkusen | 13610 | -0.058 | -0.012 |
| Pass | opp_mean_nearest_neighbor_distance | exclude_oob | 12291 | -0.078 | -0.013 |
| Pass | opp_mean_nearest_neighbor_distance | exclude_coincidence | 14821 | -0.07 | -0.013 |
| Carry | opp_centroid_x | to_leverkusen | 12529 | 0.683 | 0.944 |
| Carry | opp_centroid_x | exclude_oob | 13076 | 0.641 | 0.837 |
| Carry | opp_centroid_x | exclude_coincidence | 15507 | 0.648 | 0.833 |
| Carry | opp_visible_width | to_leverkusen | 12529 | 0.017 | -0.007 |
| Carry | opp_visible_width | exclude_oob | 13076 | -0.018 | -0.031 |
| Carry | opp_mean_pairwise_distance | to_leverkusen | 12511 | -0.057 | -0.058 |
| Carry | opp_mean_pairwise_distance | exclude_oob | 13054 | -0.082 | -0.059 |
| Carry | opp_mean_pairwise_distance | exclude_coincidence | 15484 | -0.075 | -0.056 |
| Carry | opp_mean_nearest_neighbor_distance | to_leverkusen | 12511 | -0.145 | -0.057 |
| Carry | opp_mean_nearest_neighbor_distance | exclude_oob | 13054 | -0.144 | -0.05 |
| Carry | opp_mean_nearest_neighbor_distance | exclude_coincidence | 15484 | -0.145 | -0.049 |

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

| action_type | match_id | attacking_control_spell_id | from_event_id | to_event_id | action_delta_x | anchor_gap_seconds | intervening_event_count | delta_opp_centroid_x | from_opp_n_valid_points_used | to_opp_n_valid_points_used | from_visible_area_fraction | to_visible_area_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Carry | 3895060 | 3895060-p1-pp85-s2 | 9aa52cce-99e1-49a7-ab45-dda78aeb0470 | e331db52-677c-4698-bb38-43b8caf2261a | 49.4 | 0.119 | 0 | -2.165 | 5 | 5 | 0.375 | 0.354 |
| Pass | 3895292 | 3895292-p1-pp46-s1 | ab5477dd-dff4-4b92-98af-e37d17f5011f | 3c72125f-bd44-47eb-8dc3-a05e08a6f48c | 47.5 | 1.864 | 0 | 27.644 | 6 | 6 | 0.223 | 0.226 |

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

**PHASE 4A — COMPLETE / STABLE SINGLE-ACTION SPATIAL RELATIONSHIPS IDENTIFIED**

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

# Phase 4B: multi-action spatial sequence patterns

**PHASE 4B — COMPLETE / MIXED SEQUENCE SIGNAL**

## A. Question and fixed-window definition

Which short Leverkusen Pass/Carry patterns recur within the locked control spells, and how
does visible spatial structure differ across them? This phase uses **fixed overlapping
2- and 3-action windows**, not new tactical-sequence boundaries. For two actions, A/B/C must
be consecutive trusted anchors; A and B supply eligible Phase 4A actions and C is the next
observation. Three actions require A/B/C/D, with A/B/C eligible and D the next observation.
No trusted anchor is skipped, no control spell is split, and no 4+ window is constructed.

Phase 3B supplies order, geometry values and metric-specific support. The exact frozen Phase
4A dataset supplies membership in its trusted progression population and its explicit action
vectors, already produced by the shared progression helper. Eligibility is not redefined or
recomputed. Joins require exact match/event IDs and the original adjacent TO ID. The construction
reads only derived, outcome-free inputs; no raw outcome records are loaded or inspected.

The primary response is final minus first **visible opponent centroid x**. Positive means that
the final visible centroid is farther toward the opponent's own goal in the normalized
Leverkusen reference. It does not measure a defensive line, full-team retreat or player
displacement. Every per-leg delta is retained exactly from Phase 3B.

Action motifs use P=Pass, C=Carry. Direction profiles are separate: F means strictly positive
action delta-x; R means zero or negative, an observational nonpositive direction code rather
than an inferred recycling action. No optimized threshold, joint motif classifier or clustering
is used. Counts of the cross-product appear only as support audits below.

## B. Analytical sample

Inputs reconcile to **43,737 trusted anchors**, **40,638 Phase 3B transitions**, **14,848 eligible
Phase 4A Pass legs** and **15,527 eligible Carry legs** at pinned revision
`533862946a73608c134d18b78226b6371ce7173c`.

| actions | candidate_chains | eligible_windows | matches | control_spells | centroid_endpoint_N | duration_median | duration_q25 | duration_q75 | duration_p90 | duration_p95 | duration_max | maximum_leg_gap_median | maximum_leg_gap_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 37732 | 24273 | 34 | 2410 | 24267 | 2.571 | 1.749 | 3.95 | 6.024 | 7.511 | 23.407 | 1.613 | 6.022 |
| 3 | 34993 | 19651 | 34 | 2109 | 19646 | 4.176 | 2.979 | 6.094 | 8.447 | 10.155 | 24.399 | 2.047 | 6.783 |

The candidate denominator includes every contiguous three- or four-anchor tuple within each
spell, regardless of action eligibility: **37,732 two-action candidates** and **34,993 three-action
candidates**. The following disjoint first-failure categories account for every candidate;
geometry missingness does not exclude windows.

| window_length | selection_reason | N |
| --- | --- | --- |
| 2 | eligible | 24273 |
| 2 | non_pass_carry_from_anchor | 223 |
| 2 | not_eligible_under_phase4a_progression_rules | 5227 |
| 2 | opponent_from_anchor | 8009 |
| 3 | eligible | 19651 |
| 3 | non_pass_carry_from_anchor | 238 |
| 3 | not_eligible_under_phase4a_progression_rules | 5073 |
| 3 | opponent_from_anchor | 10031 |

`not_eligible_under_phase4a_progression_rules` inherits Phase 4A's failed/unknown endpoint,
named pass-type/restart and relocation-affected measurement exclusions. This frozen downstream
population is not relabeled with a new vector-validity test. No unexplained chain loss remains.
Unsupported ordinary events between anchors remain full-stream context, as in the locked method.

Duration is first to final **anchor timestamp**, not first to last inferred action completion.
Each action's signed progression, summed positive progression and backward magnitude are retained.
Summed action dx may differ from final action endpoint minus first start because intervening
recorded endpoints/starts need not coincide. Neither difference supplies new control boundaries.

Window IDs contain match, existing spell, action count and first within-spell anchor order.
All action/anchor IDs, per-leg seconds and intervening-event counts remain available. Full-span
count includes both endpoint anchors; summed intervening counts exclude the trusted anchors.
**Windows overlap and are correlated observations, not independent tactical possessions.**
Counts describe observed recurrence, not independent replication.

## C. Recurring action-type motifs

Medians with [q25,q75]; lengths have separate denominators. All motifs remain visible, including
rare CCC. No frequency threshold decides whether a motif exists.

| window_length | motif | N | matches | share_pct | progression_median_[q25,q75] | seconds_median_[q25,q75] | opponent_centroid_x_median_[q25,q75] | opp_width_median | opp_pairwise_median | lev_centroid_x_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP | 1232 | 34 | 5.076 | 1.950 [-4.725, 10.900] | 2.461 [1.814, 4.774] | 1.662 [-1.652, 7.226] | -0.507 | -0.169 | 1.79 |
| 2 | PC | 11800 | 34 | 48.614 | 2.300 [-6.300, 10.700] | 2.512 [1.698, 3.785] | 0.959 [-2.168, 5.341] | -0.258 | -0.171 | 1.105 |
| 2 | CP | 10679 | 34 | 43.995 | 4.100 [-5.300, 12.700] | 2.577 [1.759, 3.887] | 1.113 [-2.007, 5.497] | -0.116 | -0.136 | 1.202 |
| 2 | CC | 562 | 34 | 2.315 | 4.200 [-0.100, 12.900] | 5.388 [3.613, 7.511] | 5.234 [-0.215, 16.169] | -0.048 | -0.324 | 6.094 |
| 3 | PPP | 121 | 32 | 0.616 | -0.200 [-7.300, 11.100] | 4.448 [3.012, 7.016] | 2.243 [-2.343, 7.123] | -1.314 | -0.234 | 2.75 |
| 3 | PPC | 932 | 34 | 4.743 | 2.450 [-4.700, 12.600] | 4.283 [2.974, 7.040] | 2.196 [-2.184, 9.395] | -0.283 | -0.367 | 2.516 |
| 3 | PCP | 8365 | 34 | 42.568 | 3.000 [-6.100, 14.000] | 3.927 [2.918, 5.419] | 1.458 [-2.615, 6.979] | 0.059 | -0.112 | 1.69 |
| 3 | PCC | 385 | 34 | 1.959 | 8.600 [-1.200, 20.000] | 6.781 [5.243, 8.624] | 6.650 [-1.105, 18.065] | 0.596 | -0.135 | 7.503 |
| 3 | CPP | 873 | 34 | 4.443 | 5.300 [-2.700, 14.200] | 4.455 [3.024, 7.294] | 2.448 [-1.892, 10.233] | 0.234 | -0.202 | 3 |
| 3 | CPC | 8588 | 34 | 43.703 | 4.800 [-5.100, 14.000] | 4.268 [2.955, 6.190] | 1.778 [-2.476, 8.279] | -0.275 | -0.272 | 2.057 |
| 3 | CCP | 370 | 34 | 1.883 | 7.750 [-4.100, 17.700] | 6.836 [5.183, 9.168] | 6.124 [-1.721, 17.276] | 0.52 | -0.47 | 6.195 |
| 3 | CCC | 17 | 12 | 0.087 | 13.200 [7.600, 16.200] | 8.945 [5.937, 12.900] | 13.467 [9.053, 18.781] | 0.715 | -0.158 | 14.962 |

**PC (11,800; 48.61%) and CP (10,679; 44.00%)** dominate two-action windows; together they account
for 92.61%. **CPC (8,588; 43.70%) and PCP (8,365; 42.57%)** dominate three-action windows (86.27%
together). These alternations also reflect the provider's event/Carry representation and
strict-anchor sampling, not independently identified football combinations.

CC has the largest broadly represented two-action opponent-centroid median, **+5.234**.
Among three-action motifs with wider support, **PCC +6.650** and **CCP +6.124** exceed the common
alternating motifs. CCC's raw median is +13.467, but only **17 windows in 12 matches** support it;
it is retained without strong general interpretation. PP/PPP also show positive raw medians,
so there is no simple monotonic rule that more Carry symbols imply more observed change.

| window_length | motif | N | matches | median_windows_per_represented_match | minimum_windows_per_represented_match | maximum_windows_per_represented_match | control_spells |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | PP | 1232 | 34 | 33.5 | 7 | 91 | 772 |
| 2 | PC | 11800 | 34 | 348.5 | 174 | 551 | 2249 |
| 2 | CP | 10679 | 34 | 319.5 | 142 | 533 | 2190 |
| 2 | CC | 562 | 34 | 16.5 | 3 | 41 | 473 |
| 3 | PPP | 121 | 32 | 2.5 | 1 | 19 | 98 |
| 3 | PPC | 932 | 34 | 25 | 6 | 62 | 667 |
| 3 | PCP | 8365 | 34 | 247 | 100 | 462 | 1801 |
| 3 | PCC | 385 | 34 | 10 | 2 | 28 | 336 |
| 3 | CPP | 873 | 34 | 25.5 | 5 | 53 | 628 |
| 3 | CPC | 8588 | 34 | 253 | 104 | 471 | 1964 |
| 3 | CCP | 370 | 34 | 10.5 | 2 | 28 | 326 |
| 3 | CCC | 17 | 12 | 1 | 1 | 3 | 17 |

![Two-action frequency and progression](../outputs/figures/phase4b_two_action_frequency.png)
![Two-action opponent centroid](../outputs/figures/phase4b_2_action_centroid.png)
![Three-action opponent centroid](../outputs/figures/phase4b_3_action_centroid.png)

## D. Progression-direction profiles

| window_length | motif | N | matches | share_pct | progression_median_[q25,q75] | seconds_median_[q25,q75] | opponent_centroid_x_median_[q25,q75] | opp_width_median | opp_pairwise_median | lev_centroid_x_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | FF | 7596 | 34 | 31.294 | 13.900 [8.400, 21.400] | 3.156 [2.176, 4.821] | 6.135 [1.920, 13.616] | 0.433 | -0.054 | 6.576 |
| 2 | FR | 5024 | 34 | 20.698 | 3.500 [-0.900, 8.800] | 2.242 [1.463, 3.725] | 1.597 [-0.862, 4.969] | -0.056 | -0.165 | 1.645 |
| 2 | RF | 5632 | 34 | 23.203 | 1.300 [-4.300, 7.300] | 2.618 [1.818, 3.943] | 0.133 [-2.740, 3.193] | -0.313 | -0.186 | 0.272 |
| 2 | RR | 6021 | 34 | 24.805 | -8.800 [-13.700, -4.900] | 2.217 [1.577, 3.092] | -2.254 [-5.527, 0.110] | -0.782 | -0.218 | -2.187 |
| 3 | FFF | 3355 | 34 | 17.073 | 21.600 [14.300, 31.650] | 5.269 [3.754, 7.314] | 11.864 [5.152, 22.827] | 1.263 | -0.04 | 12.792 |
| 3 | FFR | 2401 | 34 | 12.218 | 9.900 [4.200, 16.500] | 4.627 [3.160, 6.559] | 5.184 [0.932, 11.559] | 0.481 | -0.16 | 5.374 |
| 3 | FRF | 1798 | 34 | 9.15 | 8.500 [1.400, 15.775] | 4.111 [2.899, 6.356] | 3.943 [0.049, 9.277] | -0.122 | -0.38 | 4.216 |
| 3 | FRR | 2302 | 34 | 11.714 | -1.600 [-7.175, 2.600] | 3.523 [2.425, 5.161] | 0.734 [-2.448, 4.304] | -0.193 | -0.244 | 0.632 |
| 3 | RFF | 2865 | 34 | 14.579 | 7.800 [1.600, 14.600] | 4.562 [3.385, 6.429] | 2.698 [-1.124, 8.785] | 0.375 | -0.104 | 3.257 |
| 3 | RFR | 1732 | 34 | 8.814 | 1.000 [-5.525, 7.000] | 3.712 [2.614, 5.492] | -0.612 [-4.018, 2.839] | -0.085 | -0.153 | -0.343 |
| 3 | RRF | 2741 | 34 | 13.948 | -3.500 [-8.900, 1.700] | 3.951 [2.915, 5.478] | -1.538 [-5.170, 1.961] | -0.671 | -0.315 | -1.266 |
| 3 | RRR | 2457 | 34 | 12.503 | -12.900 [-19.000, -7.600] | 3.514 [2.640, 4.753] | -4.045 [-8.436, -0.811] | -1.165 | -0.235 | -4.128 |

FF and FFF have the clearest positive endpoint-centroid medians (**+6.135**, **+11.864**), whereas
RR and RRR are negative (**−2.254**, **−4.045**). FR exceeds RF (**+1.597** versus **+0.133**).
Among profiles with two forward actions, **FFR > FRF > RFF** in median centroid change
(**5.184 > 3.943 > 2.698**); this ordering persists under the shorter-gap sensitivities.
However their median total progressions also differ (**9.9 > 8.5 > 7.8**), as do type composition
and observation timing. These are descriptive ordering signatures, not isolated order effects
at matched progression. RF's near-zero positive median becomes slightly negative at shorter
gaps; its sign is not a robust signature. Zero and backward actions share R without further bins.

![Direction-profile signatures](../outputs/figures/phase4b_direction_profiles.png)

The following cross-tables are **counts only**. No full-cross-product response model or joint
pattern labels are fitted; sparse cells remain visible.

### 2-action count cross-table

| action_type_motif | FF | FR | RF | RR |
| --- | --- | --- | --- | --- |
| CC | 238 | 130 | 97 | 97 |
| CP | 3725 | 1543 | 2527 | 2884 |
| PC | 3373 | 2796 | 2734 | 2897 |
| PP | 260 | 555 | 274 | 143 |
### 3-action count cross-table

| action_type_motif | FFF | FFR | FRF | FRR | RFF | RFR | RRF | RRR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CCC | 8 | 5 | 1 | 2 | 0 | 1 | 0 | 0 |
| CCP | 94 | 43 | 44 | 49 | 46 | 16 | 34 | 44 |
| CPC | 1621 | 1220 | 682 | 656 | 961 | 936 | 1200 | 1312 |
| CPP | 117 | 253 | 49 | 34 | 79 | 173 | 119 | 49 |
| PCC | 94 | 71 | 35 | 40 | 51 | 26 | 33 | 35 |
| PCP | 1317 | 716 | 724 | 1285 | 1615 | 468 | 1296 | 944 |
| PPC | 97 | 81 | 230 | 221 | 101 | 89 | 51 | 62 |
| PPP | 7 | 12 | 33 | 15 | 12 | 23 | 8 | 11 |

## E. Opponent structural evolution

Centroid-x has narrative priority because Phase 4A established its clearest single-action
association. Width, depth, observed outfield convex-hull footprint and spacing remain secondary.

| window_length | motif | net_opp_visible_width_median | net_opp_visible_depth_median | net_opp_convex_hull_area_median | net_opp_mean_pairwise_distance_median | net_lev_centroid_x_median |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | PP | -0.507 | -0.143 | -8.714 | -0.169 | 1.79 |
| 2 | PC | -0.258 | -0.137 | -4.819 | -0.171 | 1.105 |
| 2 | CP | -0.116 | -0.118 | -1.824 | -0.136 | 1.202 |
| 2 | CC | -0.048 | 0.129 | -3.233 | -0.324 | 6.094 |
| 3 | PPP | -1.314 | 0.054 | -17.882 | -0.234 | 2.75 |
| 3 | PPC | -0.283 | -0.267 | -12.669 | -0.367 | 2.516 |
| 3 | PCP | 0.059 | -0.116 | 0.184 | -0.112 | 1.69 |
| 3 | PCC | 0.596 | 0.242 | 3.711 | -0.135 | 7.503 |
| 3 | CPP | 0.234 | -0.344 | -1.81 | -0.202 | 3 |
| 3 | CPC | -0.275 | -0.108 | -2.679 | -0.272 | 2.057 |
| 3 | CCP | 0.52 | 0.184 | 12.231 | -0.47 | 6.195 |
| 3 | CCC | 0.715 | 2.011 | 38.376 | -0.158 | 14.962 |

The common PC/CP and PCP/CPC motifs have mostly small extent/spacing medians compared with
their centroid changes. PCC and CCP have positive width/footprint medians but slightly negative
pairwise medians; these are not a single coherent expansion measure. Metric families are
dependent, so correlated spacing measures are not separate discoveries. The full motif tables
retain all nine opponent and all nine Leverkusen responses with metric-specific N and IQR.
No extent/spacing result is promoted as a robust tactical signature from its raw median alone.

Each window retains first/final metric values and statuses, net change, every individual leg
delta/status, available-state count, and observed min/max/range. Max/min/range use only available
states and explicitly mark incomplete support as `partial_available_states`. A missing interior
metric can leave net endpoint change available while making its adjacent leg deltas missing.
No geometry is filled. Centroid-x advancement/reversal from start are observed extrema relative
to an available first state, never movement rates or unobserved excursions.

| window_length | motif | leg_1_delta_opp_centroid_x_median | leg_2_delta_opp_centroid_x_median | leg_3_delta_opp_centroid_x_median |
| --- | --- | --- | --- | --- |
| 2 | PP | 0.952 | 0.481 | — |
| 2 | PC | 0.422 | 0.3 | — |
| 2 | CP | 0.169 | 0.597 | — |
| 2 | CC | 3.619 | 1.003 | — |
| 3 | PPP | 0.714 | 0.652 | 0.397 |
| 3 | PPC | 0.956 | 0.356 | 0.137 |
| 3 | PCP | 0.256 | 0.192 | 0.598 |
| 3 | PCC | 1.204 | 3.836 | 0.631 |
| 3 | CPP | 0.061 | 1.17 | 0.385 |
| 3 | CPC | 0.175 | 0.497 | 0.327 |
| 3 | CCP | 3.236 | 0.534 | 0.572 |
| 3 | CCC | 6.06 | 4.984 | 0.266 |

For example, PCC's largest **median leg** centroid change is on leg 2 (+3.836), while CCP's is
on leg 1 (+3.236). These locate where the observations differ most at group level; they do not
identify the strongest leg in every window. Leg medians do not add to the median net change.

## F. Leverkusen structural evolution

Leverkusen's visible centroid broadly parallels the opponent centroid: medians are +1.105/+1.202
for PC/CP, +6.094 for CC, +1.690/+2.057 for PCP/CPC and +7.503/+6.195 for PCC/CCP.
This is consistent with changes in the event-aligned view and possible longitudinal
reorganization of both sides. Those contributions cannot be separated here. Secondary own-team
extent, spacing and counts remain in the tables; no causal team-response interpretation follows.

## G. Progression-adjusted motif comparison

Models are fitted separately for each window length and use only available endpoint centroid-x.
The baseline is `net_opp_centroid_x ~ 1 + total_progression`; the primary adjusted model adds
action-type motif indicators, with PP/PPP references. A pre-specified supplementary version adds
the first action's start x. There are no interactions, feature selection or tuned models.
The common slope imposes a linear additive summary; it does not test every possible relation
between progression and Carry composition. Individual motif progression distributions and
sample support remain visible rather than claiming matched or randomized comparisons.

OLS standard errors use one-way **match-clustered CR1** with correction
`G/(G−1) × (N−1)/(N−p)` and 95% t intervals with G−1 degrees of freedom, the same convention as
Phase 4A. Match clustering contains overlapping windows and repeated spells within matches.
No naive iid p-values or multiple-comparison selection are reported. A focused numerical test
reproduces Phase 4A's covariance when the model has only an intercept and progression.

| window_length | model | N | matches | r_squared |
| --- | --- | --- | --- | --- |
| 2 | progression_only | 24267 | 34 | 0.536 |
| 2 | progression_plus_motif | 24267 | 34 | 0.541 |
| 2 | progression_motif_start_x | 24267 | 34 | 0.541 |
| 3 | progression_only | 19646 | 34 | 0.595 |
| 3 | progression_plus_motif | 19646 | 34 | 0.599 |
| 3 | progression_motif_start_x | 19646 | 34 | 0.601 |

Progression alone gives R² **0.5358** for two-action and **0.5950** for three-action windows.
Motif terms raise these to **0.5412** and **0.5992**: gains of **0.0053** and **0.0042**, respectively.
Thus most modeled window-level variation is associated with progression, while the extra
global contribution of these additive motif labels is small.

To distinguish overall fit from **between-motif differences**, the next table compares the
window-weighted variance of motif mean centroid changes before and after subtracting the
progression-only fitted value. These are descriptive reductions, not causal explained shares.

| actions | raw_weighted_between_motif_mean_variance | progression_residual_between_motif_mean_variance | descriptive_reduction_pct |
| --- | --- | --- | --- |
| 2 | 1.032 | 0.545 | 47.15 |
| 3 | 1.685 | 0.65 | 61.428 |

That reduction is about **47%** for two-action and **61%** for three-action motif means. It would
be inaccurate to say progression eliminates all motif differences, or explains most two-action
between-motif variation. Raw medians and adjusted mean contrasts are different summaries.

| window_length | term | reference_motif | coefficient | cluster_se | ci_low | ci_high | motif_N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | motif_PC | PP | -1.237 | 0.264 | -1.774 | -0.7 | 11797 |
| 2 | motif_CP | PP | -1.591 | 0.237 | -2.073 | -1.11 | 10676 |
| 2 | motif_CC | PP | 2.986 | 0.533 | 1.902 | 4.07 | 562 |
| 3 | motif_PPC | PPP | -1.17 | 1.094 | -3.397 | 1.056 | 932 |
| 3 | motif_PCP | PPP | -2.894 | 1.099 | -5.131 | -0.657 | 8362 |
| 3 | motif_PCC | PPP | 0.365 | 1.392 | -2.468 | 3.197 | 385 |
| 3 | motif_CPP | PPP | -1.331 | 1.004 | -3.374 | 0.712 | 873 |
| 3 | motif_CPC | PPP | -2.655 | 1.104 | -4.9 | -0.409 | 8586 |
| 3 | motif_CCP | PPP | 0.51 | 1.301 | -2.137 | 3.156 | 370 |
| 3 | motif_CCC | PPP | 5.942 | 3.095 | -0.354 | 12.238 | 17 |

**CC retains a positive adjusted contrast:** +2.986 relative to PP (95% CI 1.902–4.070).
PC and CP are lower than PP at the model's common progression by 1.237 and 1.591 units.
This is composition-related residual association, not an independent effect of inserting a Carry.
For three actions, PCC and CCP contrasts to PPP are small and uncertain; CCC is highly uncertain.
CPC has two Carries but differs little from one-Carry PCP in adjusted coefficient (about 0.239
units between them). Hence **more Carries is not a general adjusted ordering rule**.

Adding first start x barely changes the CC contrast (2.987); the supplementary three-action
motif contrasts are also similar. Starting-position context matters descriptively without
establishing a new universal spatial mechanism.

![Progression within motifs](../outputs/figures/phase4b_progression_by_motif.png)
![Adjusted motif contrasts](../outputs/figures/phase4b_adjusted_motif_contrasts.png)

## H. Starting-position context

Only the inherited equal thirds are used: [0,40), [40,80), [80,120] of the **first action start**.
Frequencies below are shares within each length/third, not tactical zones.

| actions | motif | starting_third | N | share_within_third_pct | centroid_N | centroid_median |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | CC | attacking_third | 134 | 2.529 | 134 | 3.284 |
| 2 | CC | defensive_third | 158 | 3.788 | 158 | 11.725 |
| 2 | CC | middle_third | 270 | 1.824 | 270 | 4.763 |
| 2 | CP | attacking_third | 2276 | 42.952 | 2276 | 0.459 |
| 2 | CP | defensive_third | 1924 | 46.128 | 1922 | 3.517 |
| 2 | CP | middle_third | 6479 | 43.768 | 6478 | 0.927 |
| 2 | PC | attacking_third | 2682 | 50.613 | 2682 | -0.006 |
| 2 | PC | defensive_third | 1851 | 44.378 | 1849 | 3.09 |
| 2 | PC | middle_third | 7267 | 49.091 | 7266 | 0.998 |
| 2 | PP | attacking_third | 207 | 3.906 | 207 | 1.053 |
| 2 | PP | defensive_third | 238 | 5.706 | 238 | 4.967 |
| 2 | PP | middle_third | 787 | 5.316 | 787 | 1.449 |
| 3 | CCC | attacking_third | 5 | 0.125 | 5 | 6.181 |
| 3 | CCC | defensive_third | 4 | 0.121 | 4 | 36.393 |
| 3 | CCC | middle_third | 8 | 0.065 | 8 | 12.708 |
| 3 | CCP | attacking_third | 77 | 1.932 | 77 | 0.884 |
| 3 | CCP | defensive_third | 108 | 3.276 | 108 | 14.088 |
| 3 | CCP | middle_third | 185 | 1.496 | 185 | 5.038 |
| 3 | CPC | attacking_third | 1791 | 44.932 | 1791 | -0.166 |
| 3 | CPC | defensive_third | 1501 | 45.526 | 1500 | 7.118 |
| 3 | CPC | middle_third | 5296 | 42.82 | 5295 | 1.78 |
| 3 | CPP | attacking_third | 134 | 3.362 | 134 | 0.392 |
| 3 | CPP | defensive_third | 178 | 5.399 | 178 | 8.488 |
| 3 | CPP | middle_third | 561 | 4.536 | 561 | 1.755 |
| 3 | PCC | attacking_third | 57 | 1.43 | 57 | 0.306 |
| 3 | PCC | defensive_third | 80 | 2.426 | 80 | 15.16 |
| 3 | PCC | middle_third | 248 | 2.005 | 248 | 6.307 |
| 3 | PCP | attacking_third | 1755 | 44.029 | 1755 | -0.65 |
| 3 | PCP | defensive_third | 1226 | 37.185 | 1224 | 6.742 |
| 3 | PCP | middle_third | 5384 | 43.532 | 5383 | 1.541 |
| 3 | PPC | attacking_third | 146 | 3.663 | 146 | 0.319 |
| 3 | PPC | defensive_third | 179 | 5.429 | 179 | 7.407 |
| 3 | PPC | middle_third | 607 | 4.908 | 607 | 1.85 |
| 3 | PPP | attacking_third | 21 | 0.527 | 21 | 1.066 |
| 3 | PPP | defensive_third | 21 | 0.637 | 21 | 9.257 |
| 3 | PPP | middle_third | 79 | 0.639 | 79 | 1.978 |

Larger raw centroid changes generally occur from earlier starting positions. CC remains
positive in all thirds (medians 11.725, 4.763, 3.284); PCC/CCP medians are much larger in the
defensive third (15.160/14.088) than the attacking third (0.306/0.884). Common PCP/CPC medians
are slightly negative in the attacking third. These differences prevent a field-position-free
interpretation of raw motif medians; low counts in rare motif/third cells require caution.

## I. Robustness

### Every-leg gap sensitivity

Every one of the two or three leg gaps must be ≤5 or ≤3 seconds. Total window duration is not
the gate: a three-action window can last nine seconds and meet the ≤3-per-leg comparison.
The primary dataset remains unchanged. Counts and centroid medians:

| window_length | motif | N_all | N_gap_le_3 | N_gap_le_5 | net_opp_centroid_x_median_all | net_opp_centroid_x_median_gap_le_3 | net_opp_centroid_x_median_gap_le_5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | CC | 562 | 183 | 383 | 5.234 | 3.244 | 3.891 |
| 2 | CP | 10679 | 8402 | 9822 | 1.113 | 0.494 | 0.844 |
| 2 | PC | 11800 | 9517 | 11019 | 0.959 | 0.494 | 0.775 |
| 2 | PP | 1232 | 874 | 1033 | 1.662 | 0.653 | 1.093 |
| 3 | CCC | 17 | 4 | 9 | 13.467 | 6.849 | 9.286 |
| 3 | CCP | 370 | 98 | 237 | 6.124 | 2.964 | 3.915 |
| 3 | CPC | 8588 | 5711 | 7577 | 1.778 | 0.519 | 1.256 |
| 3 | CPP | 873 | 514 | 686 | 2.448 | 0.486 | 1.344 |
| 3 | PCC | 385 | 113 | 273 | 6.65 | 5.325 | 5.866 |
| 3 | PCP | 8365 | 6339 | 7581 | 1.458 | 0.683 | 1.117 |
| 3 | PPC | 932 | 571 | 746 | 2.196 | 0.63 | 1.155 |
| 3 | PPP | 121 | 73 | 97 | 2.243 | 0.848 | 1.978 |

CC remains the largest broadly represented two-action median (**5.234 → 3.891 → 3.244**), but
support falls **562 → 383 → 183**. PCC and CCP retain positive and relatively larger three-action
medians (**6.650 → 5.866 → 5.325** and **6.124 → 3.915 → 2.964**), with ≤3 s N **113** and **98**.
These are attenuated signatures, not fixed magnitudes. CCC falls to nine/four windows and is
too sparsely supported for a strong sensitivity conclusion despite remaining in the tables.
Among the common motifs, the small PCP/CPC median ordering changes at ≤3 s; their ordering is
not robust. All raw action-type motif medians remain positive at the season level.

CC's progression-adjusted contrast persists across all/≤5/≤3 (**2.986, 2.857, 1.888**), with
95% intervals **[1.902,4.070]**, **[1.593,4.121]**, **[0.719,3.058]**. PC/CP adjusted contrasts
attenuate substantially; three-action contrasts depend on gap scope and the small PPP reference.
All adjusted sensitivity rows, including uncertainty and N, remain in the adjusted CSV.
No numerical stability threshold is used.

FF/FFF stay positive and RR/RRR negative. FFR > FRF > RFF persists under both gap comparisons;
their ≤3 medians are 3.416 > 2.826 > 1.699. RF changes from +0.133 to −0.025/−0.159, while
FR remains positive. This small RF sign change limits any strong forward-last interpretation.

![Every-leg gap comparisons](../outputs/figures/phase4b_gap_sensitivity.png)

### Terminal team, full-event context and coordinate sensitivities

Leverkusen-terminal-only selection restricts the original final observation; it does not skip
to a later anchor. It preserves the broad raw CC/PCC/CCP patterns (medians **5.217/6.109/6.072**).
CC's adjusted contrast remains positive (**2.266**), but three-action adjusted contrasts are
less stable, including PCC's reference contrast changing sign near zero. The final observation
can otherwise be an opponent event, Pressure or Shot; terminal event type is stored as identity
only and is never used as an attacking outcome or motif definition.

| actions | context | N | share_pct | intervening_events_median | intervening_events_p95 | full_span_count_median | centroid_median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | zero_between_every_anchor | 709 | 2.921 | 0 | 0 | 3 | 1.125 |
| 2 | one_or_more_intervening_events | 23564 | 97.079 | 1 | 4 | 4 | 1.119 |
| 3 | zero_between_every_anchor | 0 | 0 | — | — | — | — |
| 3 | one_or_more_intervening_events | 19651 | 100 | 2 | 5 | 6 | 1.79 |

Only **709 two-action windows** have zero intervening full-stream events on every leg; **no
three-action windows** do. This comparison is an observability audit, not an inclusion rule or
a claim of greater causal isolation. Intervening events remain counted, with no inferred
trajectories across them.

The locked OOB sensitivity excludes a window if **any constituent anchor frame** has whole-frame
OOB or unknown OOB status. Coincidence sensitivity analogously checks every frame for the
headline centroid (a multiplicity-sensitive metric). No points are removed or deduplicated,
and no anomalies are removed from the primary data. These whole-window masks preserve the
original whole-frame conditions; they include interior observations, not only endpoints.

OOB exclusion retains CC/PCC/CCP medians at **5.741/7.775/6.114**; CC's adjusted contrast is
**3.456**, with direction unchanged. Coincidence exclusion changes the corresponding medians
to **5.217/6.650/6.100** and CC's adjusted contrast to **2.960**. Main conclusions therefore do
not rely on these flagged frames. Rare CCC remains sensitive to very small changes in support.
The sensitivity CSV includes N, matches, metric-specific counts and medians for both motif
systems; no robustness claim is inferred solely from preserving a point-estimate sign.

## J. Football interpretation

### Observed evidence

Alternating Pass/Carry symbols dominate the strict windows. Larger summed progression is
associated with larger positive net changes in visible opponent centroid x. CC and sequences
containing adjacent Carries show larger raw positional medians, with a residual CC contrast
after progression adjustment. However, additive motif terms contribute little extra global
fit, three-action contrasts are less stable, and a simple count of Carries does not order
adjusted responses. Direction-profile ordering is descriptive and intertwined with progression.

### Plausible football interpretation

The patterns may reflect longitudinal changes in play together with changes in the portion
of each team visible around events. They do not establish that a symbolic motif forces a
defensive response, identifies a defensive line, or describes a recognized tactical category.
No motif is ranked by danger, success or effectiveness.

### Representative windows

For CC, PCC and the common CPC motif, examples are restricted to complete centroid support,
every leg ≤3 s and no whole-frame OOB/coincidence flags. Among those candidates, require minimum
within-window opponent count and minimum visible-area fraction at least their motif-specific
candidate medians; these are **illustration-only support landmarks**, not analysis thresholds.
Choose the nearest candidate to its primary motif medians in total progression and net
centroid change, using summed absolute IQR-scaled distances; ties use match and source order.
No future outcome or terminal event type influences selection. Counts and coverage below
describe partial states, not complete teams or persistent player identity.

**CC: `3895210:3895210-p1-pp19-s1:k2:a19`**, match 3895210. Action dx: [-0.400, 5.100]; summed progression 4.700; net opponent centroid-x 5.712; individual observed leg deltas [-0.377, 6.089]. Duration 0.446 s, largest leg gap 0.243 s. Opponent selected counts [10, 10, 10], supplied visible-area fractions [0.387, 0.411, 0.439].

Anchors: `de483125-8b19-4ed6-ae73-52190eb18ff6` → `1a1a7016-02b8-4c95-9051-5a9497f2d1a7` → `adfccc92-0c87-411d-935a-5540a8095a61`.

**PCC: `3895107:3895107-p1-pp52-s1:k3:a17`**, match 3895107. Action dx: [6.500, 1.300, 1.000]; summed progression 8.800; net opponent centroid-x 7.180; individual observed leg deltas [5.055, 1.175, 0.950]. Duration 4.633 s, largest leg gap 2.347 s. Opponent selected counts [10, 10, 10, 10], supplied visible-area fractions [0.412, 0.459, 0.397, 0.393].

Anchors: `9042cf22-9ef6-46a2-aa8f-793c67dbc9e2` → `6288c4b1-a399-4318-8992-dcfcf9b427b6` → `701c1f11-8031-4428-9852-8e57db00efcc` → `5440e12f-1e4e-4bcb-a4f5-4a6a0788008c`.

**CPC: `3895180:3895180-p2-pp138-s1:k3:a11`**, match 3895180. Action dx: [6.200, 1.800, -3.200]; summed progression 4.800; net opponent centroid-x 1.719; individual observed leg deltas [4.088, -0.053, -2.316]. Duration 3.552 s, largest leg gap 1.331 s. Opponent selected counts [10, 10, 10, 9], supplied visible-area fractions [0.301, 0.374, 0.406, 0.410].

Anchors: `0ae11b04-5668-4c16-9b44-05340173a8ba` → `dc4a59dd-5db3-4ee5-9137-43aec6feeb36` → `c1d63c93-2ace-4588-9998-1337f3252516` → `214bfe00-662d-4f6d-acca-a8ee7a6f6198`.

Examples illustrate representative observations rather than prove a mechanism. Their individual
leg deltas are differences between partial event-aligned states, not player paths.

## K. Limitations

Overlapping windows are dependent; raw counts do not measure independent replication. Match
clustering is a limited uncertainty convention, not a remedy for observability bias or confounding.
Frames are partial event-aligned observations with no tracking and anonymous ordinary off-ball
players. Variable visible area, changing selected player counts, anchor gaps and intervening
events can all affect comparisons. The next observation need not represent the previous
action's endpoint arrival. Metric families are dependent; hull is an observed outfield
convex-hull footprint and stays secondary.

Fixed windows are descriptive motifs, not natural tactical boundaries. The inherited Phase 4A
eligibility and provider Pass/Carry representation shape their frequency. Rare CCC and the
small PPP reference constrain three-action comparisons; narrow-looking intervals from a tiny
motif are not sufficient evidence. The adjusted model uses a common linear progression slope,
not exhaustive control for progression shape, timing, visibility or composition. No outcomes,
effectiveness, tactical archetypes, sequence embeddings or clustering are used.

## L. Phase decision and required answers

**PHASE 4B — COMPLETE / MIXED SEQUENCE SIGNAL**

1. **Most frequent motifs:** PC/CP for two actions, CPC/PCP for three, broadly represented in all
   34 matches. Their counts describe recurrence of symbols, not independent tactical sequences.
2. **Largest robust observed centroid changes:** CC for two actions and PCC/CCP among better
   supported three-action motifs. CCC is numerically largest but too sparse for a strong claim.
3. **How much is progression?** It supplies most modeled window-level variation (R² about
   0.536/0.595); motif additions are only 0.0053/0.0042. Between-motif mean dispersion falls
   roughly 47%/61% after progression-only residualization, so residual differences remain.
4. **Composition/order after adjustment:** CC retains a positive, gap-sensitive contrast.
   Three-action results do not support a general more-Carries rule or stable ordering of
   all motifs. No causal composition effect is identified.
5. **Forward/nonpositive ordering:** FF/FFF versus RR/RRR is clearest; FFR > FRF > RFF persists
   descriptively, with different total progressions and compositions. Order alone is not isolated.
6. **Ready for Phase 5?** Yes, for **Danger and Effectiveness Outcome Design**, retaining explicit
   support, timing, overlap and rare-motif limitations. This supports designing the outcome
   layer; it does not establish that any motif is better or dangerous. No outcome work begins here.

Reproduce with `.venv\Scripts\python.exe scripts/multi_action_spatial_sequences.py`.
Six CSVs, seven figures and this report form the analytical output family; the manifest records
input/code/output hashes and the full candidate-chain reconciliation. Protected Phase 2/3/4A
artifacts and measurement code remain unchanged. Deterministic reruns compare analytical bytes;
generation timestamps are provenance metadata only.

# Phase 6A: defensive context analysis

## A. Question

Does the established association between progression, observed opponent-centroid displacement
and subsequent danger differ with the opponent geometry visible at the starting anchor?
Observed defensive context describes the available event-aligned 360 frame. It does not
identify a formation or reconstruct a defensive block. Box entry within 10 seconds remains primary.

## B. Context construction

**30,375 frozen Phase 5B transitions: 14,848 Pass and 15,527 Carry, across 34 matches.**
Existing Phase 3B geometry joins at exact match/FROM UUID, with spell, event index and action
type checked. Spatial response remains TO minus FROM; frozen Phase 5A outcomes remain at TO.
An anchor is the next trusted observation, not necessarily the instant of action completion.
The inherited inclusive reference-anchor outcome convention remains in force.

Within each existing action-start third, pool Pass and Carry and calculate the empirical
1/3 and 2/3 quantiles using pandas linear interpolation, independently for each dimension.
Thirds are [0,40), [40,80), [80,120]. No outcomes enter cut construction. Pooling gives
both actions common definitions; the same frozen cuts apply to two-action window starts.
Raw geometry and inherited availability remain in the export. Missing context is not imputed.
All 30,375 source rows remain, including missing geometry/response rows; models use their complete cases.

T1 includes values ≤ the lower cut; T2 includes lower < value ≤ upper; T3 includes values > upper.
Ties stay together. Labels describe **relative visible** geometry within a starting third:

- Centroid: advanced / middle / deep visible centroid (increasing normalized x).
- Width: narrow / medium / wide visible structure.
- Depth: shallow / medium / deep visible extent.
- Spacing: tight / medium / loose visible nearest-neighbor spacing.

These are descriptive bins, not universal football thresholds. Width and depth use the existing
visible extents; spacing uses the existing opponent mean nearest-neighbor distance. No new geometry
formula is introduced. Visible player count is support metadata, never a context category.

### Exact cut points (round-trip precision; normalized provider coordinates)

| context_dimension | starting_third | N | lower_cut | upper_cut |
| --- | --- | --- | --- | --- |
| centroid | defensive_third | 5278 | 32.071943837212729 | 43.149538336285282 |
| centroid | middle_third | 17698 | 66.37819412459001 | 77.72410075607651 |
| centroid | attacking_third | 7396 | 92.513566015465557 | 98.956146948697096 |
| width | defensive_third | 5278 | 29.206370560219742 | 38.218772013140935 |
| width | middle_third | 17698 | 34.530191190137387 | 40.496790586670841 |
| width | attacking_third | 7396 | 30.317361030105303 | 36.566441493177308 |
| depth | defensive_third | 5278 | 19.833451592688604 | 26.602204660261023 |
| depth | middle_third | 17698 | 22.246329817380413 | 26.733599995092248 |
| depth | attacking_third | 7396 | 17.12218031100025 | 22.283193220851519 |
| spacing | defensive_third | 5258 | 10.168128547887999 | 12.097327237076383 |
| spacing | middle_third | 17687 | 8.9081516116843051 | 10.112170073579408 |
| spacing | attacking_third | 7396 | 6.8073727753784157 | 8.2162797199964483 |

### Observability support

| action_type | N | centroid_missing_N | width_missing_N | depth_missing_N | spacing_missing_N | visible_count_min | visible_count_median | visible_count_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | 14848 | 2 | 2 | 2 | 10 | 0 | 9 | 11 |
| Carry | 15527 | 1 | 1 | 1 | 24 | 0 | 9 | 10 |

Centroid, width and depth each have three unavailable starts; spacing has 34.
The primary model additionally excludes two rows with missing centroid response.
Tertile assignment weights eligible transitions, not matches equally.

![Context distribution](../outputs/figures/phase6a_context_distribution.png)

## C. Starting defensive depth

### Descriptive progression, response and danger

Rates below are proportions. Context is starting visible-centroid T1/T2/T3. `N` counts all
context rows; `centroid_response_N` is the available response denominator.

| action_type | context | N | centroid_response_N | progression_median | centroid_delta_median | centroid_delta_mean | box_entry_rate | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | 4834 | 4834 | 1.8 | 1.149442 | 2.474316 | 0.086885 | 0.009516 | 0.001282 |
| Pass | 2 | 5069 | 5069 | 1.9 | 0.520612 | 1.149888 | 0.106727 | 0.008088 | 0.000745 |
| Pass | 3 | 4943 | 4942 | 1.5 | 0.081287 | 0.289664 | 0.115112 | 0.019017 | 0.001565 |
| Carry | 1 | 5292 | 5292 | 0.4 | 1.204159 | 3.941534 | 0.095994 | 0.010393 | 0.001548 |
| Carry | 2 | 5054 | 5054 | 0.2 | 0.256447 | 1.630501 | 0.106846 | 0.012268 | 0.001014 |
| Carry | 3 | 5180 | 5179 | 0 | -0.177726 | 0.111896 | 0.122008 | 0.02027 | 0.001655 |

Raw box-entry rates increase with starting visible-centroid depth for both actions, while
median/mean subsequent centroid displacement declines. These raw differences also reflect
field position and action composition; they are not adjusted context effects.

### Prespecified interaction model

Fit separately for Pass and Carry:

```text
box_entry_within_10s ~ delta + context + delta:context
                      + action_delta_x + action_start_x + anchor_gap_seconds
```

`delta` is opponent-centroid-x displacement divided by the full-action sample SD:
Pass 6.273044 and Carry 7.132492 coordinate units. It is scaled, not mean-centered;
zero means zero observed displacement. The same action SD applies to all sensitivities.
T1 is the reference. `centroid_per_sd` is its displacement slope; `context_T2/T3`
compare context at zero displacement; `centroid_x_T2/T3` are ratios of displacement ORs
relative to T1. They measure moderation, not the within-context displacement OR itself.

Reuse unpenalized logistic MLE and match-clustered CR1 covariance, with t(33) 95% intervals.
No feature selection, joint four-context model, p-value search or multiplicity correction.
Reported coefficient intervals are available in the interaction CSV; tables pair log-odds
coefficients with their exponentiated 95% intervals.

| action_type | context_dimension | N | missing_N | positive_N | matches | model_status | mcfadden_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | centroid | 14845 | 3 | 1530 | 34 | ok | 0.082301 |
| Pass | width | 14845 | 3 | 1530 | 34 | ok | 0.08298 |
| Pass | depth | 14845 | 3 | 1530 | 34 | ok | 0.082079 |
| Pass | spacing | 14837 | 11 | 1530 | 34 | ok | 0.081877 |
| Carry | centroid | 15525 | 2 | 1680 | 34 | ok | 0.067553 |
| Carry | width | 15525 | 2 | 1680 | 34 | ok | 0.069806 |
| Carry | depth | 15525 | 2 | 1680 | 34 | ok | 0.06795 |
| Carry | spacing | 15503 | 24 | 1680 | 34 | ok | 0.069479 |

| action_type | term | N | coefficient | OR [95% CI] |
| --- | --- | --- | --- | --- |
| Pass | centroid_per_sd | 14845 | 0.171825 | 1.187 [1.106, 1.275] |
| Pass | context_T2 | 14845 | -0.021273 | 0.979 [0.829, 1.156] |
| Pass | context_T3 | 14845 | -0.151452 | 0.859 [0.712, 1.037] |
| Pass | centroid_x_T2 | 14845 | 0.035324 | 1.036 [0.926, 1.158] |
| Pass | centroid_x_T3 | 14845 | -0.084786 | 0.919 [0.819, 1.031] |
| Carry | centroid_per_sd | 15525 | 0.2575 | 1.294 [1.187, 1.410] |
| Carry | context_T2 | 15525 | 0.045603 | 1.047 [0.863, 1.269] |
| Carry | context_T3 | 15525 | 0.040566 | 1.041 [0.888, 1.221] |
| Carry | centroid_x_T2 | 15525 | 0.025275 | 1.026 [0.923, 1.139] |
| Carry | centroid_x_T3 | 15525 | -0.042557 | 0.958 [0.848, 1.083] |

### Displacement OR within each starting visible-centroid context

| action_type | context | context_N | context_positive_N | coefficient | OR [95% CI] |
| --- | --- | --- | --- | --- | --- |
| Pass | 1 | 4834 | 420 | 0.171825 | 1.187 [1.106, 1.275] |
| Pass | 2 | 5069 | 541 | 0.207149 | 1.230 [1.113, 1.360] |
| Pass | 3 | 4942 | 569 | 0.087039 | 1.091 [0.973, 1.223] |
| Carry | 1 | 5292 | 508 | 0.2575 | 1.294 [1.187, 1.410] |
| Carry | 2 | 5054 | 540 | 0.282775 | 1.327 [1.175, 1.498] |
| Carry | 3 | 5179 | 632 | 0.214943 | 1.240 [1.080, 1.423] |

The primary full-sample interactions do **not clearly distinguish** starting visible-centroid
contexts: all four interaction intervals include 1. Pass has a weaker point estimate in T3
(1.091 [0.973, 1.223]) than T1 (1.187 [1.106, 1.275]); the T3:T1 interaction is
0.919 [0.819, 1.031]. Carry remains positive in all three contexts, with T3:T1 interaction
0.958 [0.848, 1.083]. An interval excluding 1 in one context and including it in another
does not establish a difference between contexts.

### Representative predicted probabilities

Hold controls at common medians within action: Pass progression 1.7, start x 63.65, gap 1.113s;
Carry progression 0.2, start x 63.7, gap 1.201s. These are conditional model illustrations,
not marginal observed rates, tactical thresholds or treatment effects. Probability intervals
use the full clustered coefficient covariance on the logit scale and are exported.

| action_type | context | minus_1_SD | zero_delta | plus_1_SD |
| --- | --- | --- | --- | --- |
| Carry | 1 | 0.066026 | 0.083792 | 0.105798 |
| Carry | 2 | 0.06729 | 0.08736 | 0.112693 |
| Carry | 3 | 0.07134 | 0.086959 | 0.105609 |
| Pass | 1 | 0.074178 | 0.086876 | 0.101509 |
| Pass | 2 | 0.070383 | 0.085203 | 0.102798 |
| Pass | 3 | 0.069727 | 0.075589 | 0.0819 |

![Predicted probabilities](../outputs/figures/phase6a_context_probabilities.png)

### Shot and future xG: descriptive only

Use action-wide centroid-displacement quartiles, shared across starting-centroid contexts,
without outcome-driven cuts. Q4 has higher Shot rates and mean future xG than Q1 in every
action/context cell, but the intermediate pattern is not consistently monotone. Deep visible
centroid contexts have the highest overall Shot rate for both actions. These are sparse,
overlapping future observations, not independent shots or adjusted Shot effects.
No Shot interaction models are fitted.

| action_type | context | quartile | N | shot_positive_N | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | 1 | 1024 | 1 | 0.000977 | 0.000256 |
| Pass | 1 | 2 | 1020 | 5 | 0.004902 | 0.00025 |
| Pass | 1 | 3 | 1185 | 15 | 0.012658 | 0.001528 |
| Pass | 1 | 4 | 1605 | 25 | 0.015576 | 0.002411 |
| Pass | 2 | 1 | 1240 | 5 | 0.004032 | 0.000322 |
| Pass | 2 | 2 | 1308 | 5 | 0.003823 | 0.000388 |
| Pass | 2 | 3 | 1280 | 9 | 0.007031 | 0.000751 |
| Pass | 2 | 4 | 1241 | 22 | 0.017728 | 0.001538 |
| Pass | 3 | 1 | 1448 | 20 | 0.013812 | 0.000888 |
| Pass | 3 | 2 | 1383 | 28 | 0.020246 | 0.001255 |
| Pass | 3 | 3 | 1246 | 22 | 0.017657 | 0.001331 |
| Pass | 3 | 4 | 865 | 24 | 0.027746 | 0.003535 |
| Carry | 1 | 1 | 892 | 2 | 0.002242 | 0.000385 |
| Carry | 1 | 2 | 1161 | 7 | 0.006029 | 0.000619 |
| Carry | 1 | 3 | 1382 | 14 | 0.01013 | 0.001837 |
| Carry | 1 | 4 | 1857 | 32 | 0.017232 | 0.002473 |
| Carry | 2 | 1 | 1223 | 6 | 0.004906 | 0.000261 |
| Carry | 2 | 2 | 1342 | 9 | 0.006706 | 0.000298 |
| Carry | 2 | 3 | 1296 | 16 | 0.012346 | 0.000895 |
| Carry | 2 | 4 | 1193 | 31 | 0.025985 | 0.00272 |
| Carry | 3 | 1 | 1767 | 21 | 0.011885 | 0.000959 |
| Carry | 3 | 2 | 1381 | 26 | 0.018827 | 0.001185 |
| Carry | 3 | 3 | 1200 | 36 | 0.03 | 0.002274 |
| Carry | 3 | 4 | 831 | 22 | 0.026474 | 0.003024 |

## D. Width, depth and spacing context

Each secondary dimension gets one 10s interaction model per action with the **same centroid
displacement response mechanism** and the same three controls. Context T1/T2/T3 always
increases that dimension, relative to actions starting in the same third.

| action_type | context_dimension | context | N | progression_median | centroid_delta_mean | box_entry_rate |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | width | 1 | 4999 | 2.8 | 1.774398 | 0.122825 |
| Pass | width | 2 | 5019 | 1.9 | 1.332544 | 0.097231 |
| Pass | width | 3 | 4828 | 0.5 | 0.759045 | 0.08865 |
| Pass | depth | 1 | 5002 | 2.2 | 1.35469 | 0.109756 |
| Pass | depth | 2 | 5026 | 1.2 | 0.96746 | 0.093713 |
| Pass | depth | 3 | 4818 | 1.7 | 1.574073 | 0.105853 |
| Pass | spacing | 1 | 5029 | 1.3 | 1.316178 | 0.12249 |
| Pass | spacing | 2 | 5061 | 2 | 1.138127 | 0.100178 |
| Pass | spacing | 3 | 4748 | 2 | 1.415714 | 0.08572 |
| Carry | width | 1 | 5127 | 0.3 | 2.25443 | 0.12717 |
| Carry | width | 2 | 5105 | 0.2 | 1.592086 | 0.105191 |
| Carry | width | 3 | 5294 | 0 | 1.887958 | 0.092747 |
| Carry | depth | 1 | 5124 | 0.3 | 1.684496 | 0.11534 |
| Carry | depth | 2 | 5097 | 0.1 | 1.552122 | 0.09947 |
| Carry | depth | 3 | 5305 | 0.2 | 2.476496 | 0.109708 |
| Carry | spacing | 1 | 5086 | 0.2 | 1.342106 | 0.127802 |
| Carry | spacing | 2 | 5051 | 0.2 | 1.663677 | 0.103148 |
| Carry | spacing | 3 | 5366 | 0.3 | 2.658043 | 0.094857 |

| action_type | context_dimension | term | N | coefficient | OR [95% CI] |
| --- | --- | --- | --- | --- | --- |
| Pass | width | centroid_per_sd | 14845 | 0.140343 | 1.151 [1.050, 1.261] |
| Pass | width | context_T2 | 14845 | -0.227497 | 0.797 [0.683, 0.929] |
| Pass | width | context_T3 | 14845 | -0.255084 | 0.775 [0.640, 0.939] |
| Pass | width | centroid_x_T2 | 14845 | 0.059474 | 1.061 [0.933, 1.208] |
| Pass | width | centroid_x_T3 | 14845 | 0.126152 | 1.134 [1.007, 1.278] |
| Pass | depth | centroid_per_sd | 14845 | 0.167342 | 1.182 [1.055, 1.324] |
| Pass | depth | context_T2 | 14845 | -0.056207 | 0.945 [0.792, 1.128] |
| Pass | depth | context_T3 | 14845 | 0.100496 | 1.106 [0.908, 1.347] |
| Pass | depth | centroid_x_T2 | 14845 | -0.014815 | 0.985 [0.829, 1.170] |
| Pass | depth | centroid_x_T3 | 14845 | 0.032318 | 1.033 [0.901, 1.184] |
| Pass | spacing | centroid_per_sd | 14837 | 0.167207 | 1.182 [1.067, 1.310] |
| Pass | spacing | context_T2 | 14837 | -0.121313 | 0.886 [0.762, 1.030] |
| Pass | spacing | context_T3 | 14837 | -0.161336 | 0.851 [0.683, 1.060] |
| Pass | spacing | centroid_x_T2 | 14837 | 0.072538 | 1.075 [0.928, 1.246] |
| Pass | spacing | centroid_x_T3 | 14837 | 0.029891 | 1.030 [0.902, 1.177] |
| Carry | width | centroid_per_sd | 15525 | 0.211875 | 1.236 [1.140, 1.340] |
| Carry | width | context_T2 | 15525 | -0.218814 | 0.803 [0.711, 0.908] |
| Carry | width | context_T3 | 15525 | -0.342746 | 0.710 [0.599, 0.841] |
| Carry | width | centroid_x_T2 | 15525 | 0.06835 | 1.071 [0.966, 1.187] |
| Carry | width | centroid_x_T3 | 15525 | 0.077344 | 1.080 [0.979, 1.192] |
| Carry | depth | centroid_per_sd | 15525 | 0.240946 | 1.272 [1.155, 1.401] |
| Carry | depth | context_T2 | 15525 | -0.150325 | 0.860 [0.735, 1.007] |
| Carry | depth | context_T3 | 15525 | -0.089974 | 0.914 [0.755, 1.106] |
| Carry | depth | centroid_x_T2 | 15525 | 0.00342 | 1.003 [0.900, 1.118] |
| Carry | depth | centroid_x_T3 | 15525 | 0.03002 | 1.030 [0.919, 1.156] |
| Carry | spacing | centroid_per_sd | 15503 | 0.214371 | 1.239 [1.094, 1.403] |
| Carry | spacing | context_T2 | 15503 | -0.237282 | 0.789 [0.686, 0.907] |
| Carry | spacing | context_T3 | 15503 | -0.297387 | 0.743 [0.634, 0.870] |
| Carry | spacing | centroid_x_T2 | 15503 | 0.125651 | 1.134 [0.997, 1.289] |
| Carry | spacing | centroid_x_T3 | 15503 | 0.07225 | 1.075 [0.959, 1.205] |

**The strongest secondary moderation signal is Pass width:** wide versus narrow visible
structure interaction OR 1.134 [1.007, 1.278]; corresponding displacement ORs are
1.305 [1.154, 1.477] versus 1.151 [1.050, 1.261]. This survives progression adjustment
within the prescribed model, but its lower bound is close to 1 among several exploratory
interactions. It is tentative and has no authorized secondary robustness family.
Carry's corresponding width interaction is 1.080 [0.979, 1.192]. Visible longitudinal extent
shows little moderation for either action. Carry's medium versus tight visible spacing
interaction is 1.134 [0.997, 1.289], also uncertain. Context main effects at zero displacement
must not be mistaken for moderation of displacement.

![Interaction effects](../outputs/figures/phase6a_interaction_effects.png)

## E. Pass versus Carry

Descriptive progression–centroid-response slopes use the inherited match-clustered OLS
implementation, plus Spearman correlation. They describe the progression-linked mechanism,
without adding danger regressions or a pooled Pass/Carry interaction model.

| action_type | context | progression_response_slope | progression_response_ci_low | progression_response_ci_high | progression_response_rho |
| --- | --- | --- | --- | --- | --- |
| Pass | 1 | 0.415651 | 0.391882 | 0.43942 | 0.643097 |
| Pass | 2 | 0.340556 | 0.31666 | 0.364453 | 0.654788 |
| Pass | 3 | 0.265904 | 0.24547 | 0.286338 | 0.589894 |
| Carry | 1 | 0.88549 | 0.838124 | 0.932856 | 0.678928 |
| Carry | 2 | 0.794771 | 0.745399 | 0.844142 | 0.653599 |
| Carry | 3 | 0.677481 | 0.629436 | 0.725526 | 0.625849 |

Carry has the larger descriptive progression–response slope in every visible-centroid context:
0.885, 0.795, 0.677 versus Pass 0.416, 0.341, 0.266. Both decline from advanced to deep
starting visible centroid. Thus Carry's stronger spatial response persists, but the primary
danger model does not establish that Carry benefits especially from advanced visible
structures: its displacement ORs remain similar across contexts. Pass's full-sample deep
context estimate is weaker and uncertain. Separate models and different action SDs do not
constitute a formal test of a Pass-versus-Carry difference.

![Observed displacement](../outputs/figures/phase6a_centroid_displacement.png)

## F. Motifs under different contexts

Retain only **24,273 frozen two-action windows**, with exact Phase 4B `anchor_0_event_id`
recovered by window/match identity. Check spell, motif, progression and terminal UUID;
progression equality permits only 1e-9 CSV round-trip tolerance. Geometry joins at the
START anchor, while Phase 5C danger outcomes remain terminal-aligned. Apply the transition
cut points using the first action's starting third. Three starts lack centroid context,
leaving **24,270 windows across 34 matches** for the single adjusted model.

| motif | context | N | matches | positive_N | box_entry_rate |
| --- | --- | --- | --- | --- | --- |
| PP | 1 | 450 | 34 | 44 | 0.097778 |
| PP | 2 | 390 | 34 | 31 | 0.079487 |
| PP | 3 | 392 | 34 | 44 | 0.112245 |
| PC | 1 | 3684 | 34 | 332 | 0.090119 |
| PC | 2 | 4107 | 34 | 438 | 0.106647 |
| PC | 3 | 4007 | 34 | 489 | 0.122036 |
| CP | 1 | 3313 | 34 | 330 | 0.099608 |
| CP | 2 | 3587 | 34 | 359 | 0.100084 |
| CP | 3 | 3778 | 34 | 430 | 0.113817 |
| CC | 1 | 230 | 34 | 23 | 0.1 |
| CC | 2 | 169 | 34 | 24 | 0.142012 |
| CC | 3 | 163 | 33 | 21 | 0.128834 |

```text
box_entry_10s ~ motif + starting_centroid_context + motif:starting_centroid_context
               + total_progression + first_action_start_x + duration_seconds
```

Reference: PP in T1. One model only; no three-action or secondary-geometry motif interactions.

| term | model_N | model_matches | coefficient | OR [95% CI] |
| --- | --- | --- | --- | --- |
| motif_PC | 24270 | 34 | -0.197495 | 0.821 [0.587, 1.148] |
| motif_CP | 24270 | 34 | -0.11279 | 0.893 [0.637, 1.252] |
| motif_CC | 24270 | 34 | -0.264851 | 0.767 [0.454, 1.297] |
| context_T2 | 24270 | 34 | -0.485521 | 0.615 [0.350, 1.081] |
| PC_x_T2 | 24270 | 34 | 0.460108 | 1.584 [0.918, 2.735] |
| CP_x_T2 | 24270 | 34 | 0.3141 | 1.369 [0.815, 2.301] |
| CC_x_T2 | 24270 | 34 | 0.747784 | 2.112 [0.906, 4.923] |
| context_T3 | 24270 | 34 | -0.266486 | 0.766 [0.453, 1.294] |
| PC_x_T3 | 24270 | 34 | 0.177306 | 1.194 [0.706, 2.019] |
| CP_x_T3 | 24270 | 34 | 0.034277 | 1.035 [0.622, 1.722] |
| CC_x_T3 | 24270 | 34 | 0.387642 | 1.474 [0.757, 2.867] |

Adjusted within-context contrasts below are derived from that same model and its full
clustered covariance; PC/CP/CC compare with PP, while PC_vs_CP compares action order.

| context | motif | coefficient | OR [95% CI] |
| --- | --- | --- | --- |
| 1 | PC | -0.197495 | 0.821 [0.587, 1.148] |
| 1 | CP | -0.11279 | 0.893 [0.637, 1.252] |
| 1 | CC | -0.264851 | 0.767 [0.454, 1.297] |
| 1 | PC_vs_CP | -0.084705 | 0.919 [0.814, 1.037] |
| 2 | PC | 0.262613 | 1.300 [0.838, 2.017] |
| 2 | CP | 0.201311 | 1.223 [0.795, 1.882] |
| 2 | CC | 0.482933 | 1.621 [0.867, 3.029] |
| 2 | PC_vs_CP | 0.061302 | 1.063 [0.951, 1.188] |
| 3 | PC | -0.020189 | 0.980 [0.702, 1.368] |
| 3 | CP | -0.078512 | 0.924 [0.676, 1.264] |
| 3 | CC | 0.122791 | 1.131 [0.624, 2.048] |
| 3 | PC_vs_CP | 0.058324 | 1.060 [0.972, 1.156] |

All motif-interaction and within-context contrast intervals include 1. The apparent raw CC
advantage in middle visible-centroid context (14.20%) has only N=169 and 24 positive windows;
its adjusted CC:PP OR is 1.621 [0.867, 3.029]. CC cells overall have N=163–230 and just
21–24 positives; PP cells have N=390–450 and 31–44 positives. No categories are merged.
These wide intervals cannot establish equivalence, but give no clear reason to overturn
Phase 5C's conclusion that motif identity adds little reliable independent danger information.

![Motif context](../outputs/figures/phase6a_motif_context.png)

## G. Robustness

Only primary starting-centroid interactions are repeated. All 22 transition model fits
and the single motif model report `ok`. The table shows the deep-versus-advanced visible
centroid interaction; the companion middle-context coefficients and all within-context
slopes remain in the compact interaction CSV.

| action_type | scope | horizon | N | coefficient | OR [95% CI] |
| --- | --- | --- | --- | --- | --- |
| Pass | all | 10 | 14845 | -0.084786 | 0.919 [0.819, 1.031] |
| Pass | all | 5 | 14845 | -0.040496 | 0.960 [0.817, 1.128] |
| Pass | all | 15 | 14845 | -0.122984 | 0.884 [0.774, 1.010] |
| Pass | gap_le_5 | 10 | 14419 | -0.214954 | 0.807 [0.724, 0.898] |
| Pass | gap_le_3 | 10 | 13970 | -0.336675 | 0.714 [0.599, 0.851] |
| Pass | exclude_oob | 10 | 12300 | -0.13042 | 0.878 [0.756, 1.019] |
| Pass | exclude_coincidence | 10 | 14832 | -0.080518 | 0.923 [0.824, 1.033] |
| Pass | visible_count | 10 | 14845 | -0.085644 | 0.918 [0.818, 1.030] |
| Carry | all | 10 | 15525 | -0.042557 | 0.958 [0.848, 1.083] |
| Carry | all | 5 | 15525 | -0.121777 | 0.885 [0.720, 1.088] |
| Carry | all | 15 | 15525 | -0.060846 | 0.941 [0.839, 1.055] |
| Carry | gap_le_5 | 10 | 14673 | -0.19133 | 0.826 [0.688, 0.991] |
| Carry | gap_le_3 | 10 | 12962 | -0.405245 | 0.667 [0.525, 0.847] |
| Carry | exclude_oob | 10 | 13076 | -0.032756 | 0.968 [0.837, 1.120] |
| Carry | exclude_coincidence | 10 | 15507 | -0.040895 | 0.960 [0.850, 1.085] |
| Carry | visible_count | 10 | 15525 | -0.041958 | 0.959 [0.848, 1.084] |

- **Horizon:** 5s and 15s retain uncertain full-sample deep-versus-advanced moderation
  for both actions; 10s remains primary.
- **Gap:** the interpretation strengthens in the short-gap subsets. At ≤5s, deep-versus-advanced
  interaction ORs are Pass 0.807 [0.724, 0.898] and Carry 0.826 [0.688, 0.991]. At ≤3s,
  they are Pass 0.714 [0.599, 0.851] and Carry 0.667 [0.525, 0.847]. This is a weaker
  displacement–danger association in the deepest visible-centroid context relative to T1,
  not necessarily a negative within-context association. Fixed cuts and SDs do not change.
  These are nested, selected populations; gap-dependent observation/composition prevents
  promotion of the result to an unconditional defensive-context finding.
- **Visible count:** adding FROM visible count once per action barely changes the primary
  interactions (Pass 0.918, Carry 0.959). This does not recover players outside the frame.
- **OOB/coincidence:** use the inherited whole-frame exclusion masks at both endpoints,
  including unknown flags. Neither changes the cautious full-sample interpretation.

## H. Football interpretation

### Observed evidence

The progression-linked centroid response is stronger for Carry than Pass descriptively in
all starting visible-centroid contexts and is attenuated when the starting visible centroid
is already deeper. Centroid displacement remains associated with danger across much of the
context range. There is limited evidence for sharply different full-sample danger slopes by
starting centroid depth; shorter observation gaps reveal stronger depth moderation in both
actions. Pass width is the clearest, tentative secondary signal. Motif context yields no
reliable independent motif advantage.

### Tactical hypotheses

An already deeper visible opponent structure may leave less longitudinal room for a large
next-observed shift. Wider visible structures might coincide with Pass situations where
longitudinal reorganization is more informative about subsequent danger. These are hypotheses
for later tactical interpretation or video checking, not evidence of deliberate exploitation,
tracked defensive retreat, a recognized formation or a causal mechanism.

## I. Limitations

- StatsBomb 360 is a partial event-aligned observation; ordinary off-ball players are anonymous.
- Visible count varies and frame composition can change between anchors. A count covariate
  cannot remove all visibility bias.
- Context tertiles are relative descriptive bins, not tactical categories. Within-third
  binning and linear start-x adjustment cannot remove all residual field-position confounding.
- No true formation recognition or continuous defender movement is available.
- All results are observational associations, conditional on the frozen population and model.
- Starting centroid also appears with a minus sign in TO-minus-FROM displacement. Mathematical
  coupling, regression to the mean and longitudinal room can contribute to context patterns.
- Interaction estimates may be noisy. Multiple exploratory comparisons have no multiplicity
  correction; one interval just above 1 is tentative. Clustered inference uses 34 matches.
- Fixed motifs overlap; windows and future outcomes are reused. Match clustering addresses
  within-match dependence for model uncertainty, not causal identification or sparse support.
- Shot/xG are sparse descriptive outcomes. The locked spell boundary excludes many terminal
  Shot anchors; these rates describe the retained outcome layer, not all Leverkusen shooting.
- Gap sensitivities select different action populations and observation delays. The stronger
  short-gap interactions cannot be treated as independent replications of the full sample.

## J. Decision

**PHASE 6A — COMPLETE / LIMITED DEFENSIVE-CONTEXT MODERATION**

Ready for the later synthesis: carry forward the persistent progression-linked response,
the generally positive displacement–danger association, and the lack of a reliable motif
advantage. Starting-depth moderation must retain its gap qualification; Pass width is a
tentative secondary observation, not a tactical rule. No strong universal starting-depth
preference is established. This resolves all five required questions within Phase 6A's scope.

### Artifacts and reproducibility

Four core CSVs are in `outputs/analysis/`: `phase6a_defensive_context_dataset.csv`,
`phase6a_context_summary.csv`, `phase6a_context_interactions.csv`, and
`phase6a_motif_context_summary.csv`. Five figures above are in `outputs/figures/`.
The CSVs retain cut points, support, model status, coefficients/intervals, context slopes,
representative probabilities and the bounded sensitivities. No historical analysis is rebuilt.

```powershell
.venv\Scripts\python.exe scripts/defensive_context_analysis.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m pytest -q
```

Next authorized step: **Phase 6B — Final Tactical Synthesis and Research Report**.
Phase 6B is not started here.

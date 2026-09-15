# Phase 5B: spatial change to danger

## A. Question and temporal alignment

Does observed spatial change retain an association with near-term attacking danger
after adjustment for action progression, starting position and observation gap?

```text
FROM → action → TO spatial change → future danger
```

The frozen Phase 4A `to_event_id` joins exactly to Phase 5A `reference_event_id`,
with match, spell, event index and type checked. FROM outcomes are never joined.
Geometry is TO minus FROM. The existing next trusted anchor is used without rebuilding
transitions or assuming it records physical action completion. Inclusive TO outcomes
mean the transition can culminate at danger; the immediate-exclusion sensitivity
separately asks about danger developing afterward. **10s is primary; 5/15s are sensitivities.**
Box entry, Shot and provider xG retain their locked separate definitions.

## B. Analytical sample

**30,375 Phase 4A source rows → 30,375 exact TO joins**, with **0 unmatched rows**
and no identity or spell conflicts. Pass: **14,848**; Carry: **15,527**. Both cover
34 matches. Geometry missingness is handled per metric, never by dropping a whole
transition from the exported dataset. All rates below are proportions.

| action_type | N | box_entry_positive_N | box_entry_rate | shot_positive_N | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- |
| All | 30375 | 3210 | 0.105679 | 403 | 0.013267 | 0.001304 |
| Carry | 15527 | 1680 | 0.108199 | 222 | 0.014298 | 0.00141 |
| Pass | 14848 | 1530 | 0.103044 | 181 | 0.01219 | 0.001193 |

Available spatial-predictor rows:

| action_type | Opponent centroid x | Opponent width | Opponent depth | Opponent NN spacing | Leverkusen centroid x |
| --- | --- | --- | --- | --- | --- |
| Carry | 15525 | 15525 | 15525 | 15502 | 15527 |
| Pass | 14845 | 14845 | 14845 | 14834 | 14848 |

Immediate TO events retained in the canonical analysis:

| action_type | reference_is_box_entry | reference_is_shot |
| --- | --- | --- |
| Carry | 289 | 35 |
| Pass | 198 | 17 |

## C. Opponent centroid-x → danger

**Greater opponent-centroid x displacement is followed by higher 10s box-entry
rates for both actions, and the association remains after the specified adjustment.**

### Descriptive quartiles

Quartiles use the full available predictor distribution separately for each action
type, with tied values kept together. Boundaries are presentation bins, not tactical
thresholds. The same centroid bins are retained for the starting-third descriptions.

| action_type | quartile | N | median_spatial_change | box_entry_rate | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- |
| Pass | 1 | 3712 | -3.179227 | 0.065194 | 0.007004 | 0.000524 |
| Pass | 2 | 3711 | -0.382659 | 0.089733 | 0.01024 | 0.000673 |
| Pass | 3 | 3711 | 1.492433 | 0.103207 | 0.012396 | 0.001194 |
| Pass | 4 | 3711 | 5.518492 | 0.154136 | 0.019132 | 0.002381 |
| Carry | 1 | 3882 | -2.705341 | 0.077022 | 0.00747 | 0.000607 |
| Carry | 2 | 3884 | -0.241445 | 0.101957 | 0.010814 | 0.000709 |
| Carry | 3 | 3878 | 1.30006 | 0.113461 | 0.017019 | 0.001657 |
| Carry | 4 | 3881 | 6.946388 | 0.140428 | 0.021902 | 0.002667 |

Box-entry prevalence rises monotonically from Q1 to Q4: **6.52% → 15.41% for Pass**
and **7.70% → 14.04% for Carry**. The corresponding Shot rates and mean xG also rise
across these descriptive quartiles.

![Centroid quartiles](../outputs/figures/phase5b_centroid_quartiles.png)

### Unadjusted versus adjusted association

Each adjusted logistic model uses one spatial delta plus `action_delta_x`,
`action_start_x` and `anchor_gap_seconds`. Pass and Carry are fitted separately.
Raw coefficients are log odds per StatsBomb coordinate unit. The OR compares a
**+1 sample SD** spatial change within action type. That full-action SD is fixed
across sensitivities; the analytical CSV keeps raw units. The core summary also
retains raw-unit OR/CI, predictor SD, missing-row count and model diagnostics.

| action_type | spatial_metric | model | N | positive_N | coefficient | odds_ratio_1sd | mcfadden_r2 | model_status | OR_1SD_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | Opponent centroid x | unadjusted | 14845 | 1530 | 0.043767 | 1.315941 | 0.014902 | ok | [1.266, 1.368] |
| Pass | Opponent centroid x | adjusted | 14845 | 1530 | 0.030893 | 1.213842 | 0.081325 | ok | [1.141, 1.292] |
| Carry | Opponent centroid x | unadjusted | 15525 | 1680 | 0.033271 | 1.267824 | 0.011044 | ok | [1.202, 1.338] |
| Carry | Opponent centroid x | adjusted | 15525 | 1680 | 0.035391 | 1.287144 | 0.067421 | ok | [1.188, 1.394] |

- **Pass:** the +1 SD OR falls from **1.316** unadjusted to **1.214 [1.141, 1.292]**
  adjusted. The raw coefficient falls from 0.04377 to 0.03089, about 29% attenuation.
  Progression/start/gap account for part of the association, but do not remove it.
- **Carry:** the OR is **1.268** unadjusted and **1.287 [1.188, 1.394]** adjusted;
  the raw coefficient changes from 0.03327 to 0.03539. It does not attenuate here.
- The reporting SD is **6.273** units for Pass and **7.132** for Carry. Carry has
  the larger adjusted point estimate, but the intervals overlap substantially.
  These separate fits do **not** establish a material between-action difference.
  The much larger Carry spatial-response slope in Phase 4A does not by itself
  imply a correspondingly larger conditional danger association.

Intervals use match-clustered Bernoulli-score sandwich covariance with the inherited
CR1 correction `G/(G−1) × (N−1)/(N−K)` and `t(G−1)` critical values (34 matches).
There are no iid p-values. McFadden pseudo-R² is a basic likelihood fit summary,
not predictive validation. Models are unpenalized logistic maximum likelihood,
using [SciPy's optimizer](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html);
the one-cluster small-sample correction follows the existing Phase 4A convention and
[the sandwich-covariance convention](https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html).
The implementation has an analytic log-odds and clustered-variance unit check.

![Adjusted centroid odds ratios](../outputs/figures/phase5b_adjusted_centroid.png)

### Starting-position context

Inherited thirds are `[0,40)`, `[40,80)`, `[80,120]`. No interaction model is fitted.

| action_type | starting_third | quartile | N | box_entry_rate |
| --- | --- | --- | --- | --- |
| Pass | defensive_third | 1 | 616 | 0.030844 |
| Pass | defensive_third | 2 | 447 | 0.040268 |
| Pass | defensive_third | 3 | 516 | 0.044574 |
| Pass | defensive_third | 4 | 861 | 0.072009 |
| Pass | middle_third | 1 | 2246 | 0.04675 |
| Pass | middle_third | 2 | 2287 | 0.060341 |
| Pass | middle_third | 3 | 2322 | 0.076227 |
| Pass | middle_third | 4 | 2097 | 0.147353 |
| Pass | attacking_third | 1 | 850 | 0.138824 |
| Pass | attacking_third | 2 | 977 | 0.181167 |
| Pass | attacking_third | 3 | 873 | 0.209622 |
| Pass | attacking_third | 4 | 753 | 0.266932 |
| Carry | defensive_third | 1 | 810 | 0.024691 |
| Carry | defensive_third | 2 | 547 | 0.042048 |
| Carry | defensive_third | 3 | 583 | 0.049743 |
| Carry | defensive_third | 4 | 896 | 0.071429 |
| Carry | middle_third | 1 | 2219 | 0.061289 |
| Carry | middle_third | 2 | 2293 | 0.068469 |
| Carry | middle_third | 3 | 2170 | 0.081567 |
| Carry | middle_third | 4 | 2064 | 0.145833 |
| Carry | attacking_third | 1 | 853 | 0.167644 |
| Carry | attacking_third | 2 | 1044 | 0.206897 |
| Carry | attacking_third | 3 | 1125 | 0.208 |
| Carry | attacking_third | 4 | 921 | 0.19544 |

The gradient appears across all three Pass starting thirds and the defensive/middle
Carry thirds. Carry's attacking-third rates plateau and dip in Q4 (16.76%, 20.69%,
20.80%, 19.54%). Thus the aggregate gradient is not universally monotonic within
every context. This descriptive qualification is retained without adding an
interaction-model family.

## D. Secondary spatial structure

Opponent width, depth and NN spacing each enter a separate adjusted box-entry model.
Leverkusen centroid x is the sole team-structure comparison. There is no joint
geometry model, additional spacing family, hull analysis or feature selection.
Quartile descriptions for all five metrics are in the compact summary CSV.

| action_type | spatial_metric | model | N | positive_N | coefficient | odds_ratio_1sd | mcfadden_r2 | model_status | OR_1SD_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | Opponent width | adjusted | 14845 | 1530 | -0.015426 | 0.921309 | 0.079406 | ok | [0.874, 0.971] |
| Pass | Opponent depth | adjusted | 14845 | 1530 | -0.018092 | 0.918164 | 0.079537 | ok | [0.866, 0.974] |
| Pass | Opponent NN spacing | adjusted | 14834 | 1530 | -0.032944 | 0.958468 | 0.078742 | ok | [0.903, 1.018] |
| Pass | Leverkusen centroid x | adjusted | 14848 | 1530 | 0.028516 | 1.20556 | 0.081271 | ok | [1.128, 1.288] |
| Carry | Opponent width | adjusted | 15525 | 1680 | -0.011153 | 0.939678 | 0.064479 | ok | [0.874, 1.011] |
| Carry | Opponent depth | adjusted | 15525 | 1680 | -0.005806 | 0.971541 | 0.064098 | ok | [0.923, 1.023] |
| Carry | Opponent NN spacing | adjusted | 15502 | 1680 | -0.025771 | 0.962954 | 0.06388 | ok | [0.893, 1.038] |
| Carry | Leverkusen centroid x | adjusted | 15527 | 1680 | 0.038805 | 1.329768 | 0.068371 | ok | [1.214, 1.456] |

The clearest **secondary opponent** signals are modest negative Pass extent
associations: +1 SD depth OR **0.918 [0.866, 0.974]**, and width OR
**0.921 [0.874, 0.971]**. Smaller observed width/depth changes are associated with
higher box-entry odds under these controls. Carry width/depth intervals cross 1;
NN spacing crosses 1 for both actions. There is no consistent broad spacing result.
These weaker secondary associations receive no additional model/robustness family.

The Leverkusen-centroid comparison is positive: Pass **1.206 [1.128, 1.288]** and
Carry **1.330 [1.214, 1.456]**. This similarity cautions against interpreting the
opponent-centroid result as a uniquely opponent-specific mechanism. Each metric's
association is adjusted for basic context, not for the other geometry metrics.

## E. Shot and future xG

Shot models are restricted to opponent centroid x. The small number of underlying
Shots and repeated references to them limit the evidence even when positive anchor
counts are larger. The locked Phase 5A population contains only 110 eligible Shots:
terminal boundary Shots remain outside spell membership. These outcomes therefore
describe danger retained inside spells, not all attack-ending attempts.

| action_type | spatial_metric | model | N | positive_N | coefficient | odds_ratio_1sd | mcfadden_r2 | model_status | OR_1SD_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | Opponent centroid x | adjusted | 14845 | 181 | 0.074368 | 1.594426 | 0.145205 | ok | [1.345, 1.891] |
| Carry | Opponent centroid x | adjusted | 15525 | 222 | 0.047445 | 1.402702 | 0.135315 | ok | [1.161, 1.695] |

Adjusted Shot ORs are **1.594 [1.345, 1.891] for Pass** and
**1.403 [1.161, 1.695] for Carry**, per +1 SD. The canonical modeled samples contain
181 and 222 positive reference rows, spread over only 27 and 28 matches respectively;
they do not represent that many distinct Shots.

Future xG stays descriptive: quartile means above, and positive proportions and
positive-only medians below. No distributional or linear xG model is fitted.

| action_type | quartile | N | mean_future_xg | proportion_positive_xg | positive_xg_median |
| --- | --- | --- | --- | --- | --- |
| Pass | 1 | 3712 | 0.000524 | 0.007004 | 0.05274 |
| Pass | 2 | 3711 | 0.000673 | 0.01024 | 0.051361 |
| Pass | 3 | 3711 | 0.001194 | 0.012396 | 0.056193 |
| Pass | 4 | 3711 | 0.002381 | 0.019132 | 0.074157 |
| Carry | 1 | 3882 | 0.000607 | 0.00747 | 0.055555 |
| Carry | 2 | 3884 | 0.000709 | 0.010814 | 0.046677 |
| Carry | 3 | 3878 | 0.001657 | 0.017019 | 0.056894 |
| Carry | 4 | 3881 | 0.002667 | 0.021902 | 0.073265 |

Mean 10s xG rises from **0.000524 to 0.002381** across Pass quartiles and from
**0.000607 to 0.002667** across Carry quartiles. This is an unadjusted descriptive
pattern, not evidence of an independently adjusted xG association. The joined
population has no missing horizon xG values.

The immediate-Shot exclusion also repeats the xG quartile descriptions using the
same canonical centroid-bin boundaries, so it tests the spatial pattern for danger
developing afterward rather than only reporting a change in overall mean:

| action_type | quartile | N | mean_future_xg | proportion_positive_xg | positive_xg_median |
| --- | --- | --- | --- | --- | --- |
| Pass | 1 | 3709 | 0.000483 | 0.006201 | 0.053495 |
| Pass | 2 | 3706 | 0.000578 | 0.008904 | 0.051804 |
| Pass | 3 | 3706 | 0.001008 | 0.011063 | 0.056193 |
| Pass | 4 | 3707 | 0.002161 | 0.018074 | 0.074157 |
| Carry | 1 | 3877 | 0.000564 | 0.00619 | 0.056193 |
| Carry | 2 | 3879 | 0.000664 | 0.009539 | 0.046677 |
| Carry | 3 | 3868 | 0.001475 | 0.014478 | 0.056918 |
| Carry | 4 | 3866 | 0.002091 | 0.018107 | 0.065433 |

## F. Robustness

Only the headline opponent-centroid models receive gap, horizon, immediate-event,
OOB and coincidence sensitivities. Visible-count adjustment is limited to centroid /
box entry. Gap masks and whole-frame flags at both endpoints, including unknown
flags, are reused verbatim from Phase 4A. No new cleaning thresholds are introduced.

- **Gaps:** the box-entry direction persists. Pass ORs increase to **1.286 (≤5s)**
  and **1.346 (≤3s)**; Carry attenuates to **1.273** and **1.202**. All box-entry
  intervals remain above 1. Shorter gaps change magnitude, not the main conclusion.
- **Horizons:** box-entry ORs for 5/10/15s are **1.288/1.214/1.142 (Pass)** and
  **1.433/1.287/1.225 (Carry)**. The association is strongest near term and weakens
  with horizon while retaining its direction and intervals above 1.
- **Immediate exclusions:** removing 198 Pass and 289 Carry immediate box entries
  lowers the ORs to **1.144 [1.077, 1.216]** and **1.190 [1.094, 1.295]**. The
  transition's culmination at danger explains part, but not all, of the association.
  Removing 17/35 immediate Shots leaves Shot ORs **1.561/1.369**, both intervals above 1.
  On those Shot-excluded scopes, mean xG is **0.001057/0.001198**, respectively.
- **Visible-count adjustment:** box-entry ORs are **1.215/1.287**, essentially unchanged
  from **1.214/1.287**. Changing count does not explain the centroid coefficient;
  unchanged counts still do not imply an unchanged set of observed players.
- **OOB/coincidence:** box-entry ORs are **1.255/1.281** after whole-frame OOB exclusion
  and **1.214/1.286** after coincidence exclusion. Directions and intervals persist.
  Coincidence affects only 13 Pass and 18 Carry centroid-complete rows, so this is
  a limited perturbation rather than strong additional evidence.
- **Sparse Shots:** direction persists across the requested scopes/horizons, but
  Pass at gap ≤3s has **1.425 [0.988, 2.055]**. The Shot signal is less precise
  than the box-entry result and is not uniformly distinguishable from OR=1.

In the sensitivity CSV, `N`/`outcome_prevalence` refer to complete model rows;
`scope_N` and the descriptive rates/xG summaries use all rows in that scope.

| action_type | scope | horizon | outcome | N | positive_N | coefficient | odds_ratio_1sd | mcfadden_r2 | model_status | OR_1SD_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | all | 10 | box_entry | 14845 | 1530 | 0.030893 | 1.213842 | 0.081325 | ok | [1.141, 1.292] |
| Pass | gap_le_5 | 10 | box_entry | 14419 | 1469 | 0.040107 | 1.286074 | 0.08079 | ok | [1.158, 1.429] |
| Pass | gap_le_3 | 10 | box_entry | 13970 | 1423 | 0.047332 | 1.345698 | 0.083094 | ok | [1.203, 1.505] |
| Pass | exclude_immediate | 10 | box_entry | 14647 | 1332 | 0.021464 | 1.14413 | 0.056608 | ok | [1.077, 1.216] |
| Pass | exclude_oob | 10 | box_entry | 12300 | 1291 | 0.036225 | 1.25513 | 0.084941 | ok | [1.179, 1.336] |
| Pass | exclude_coincidence | 10 | box_entry | 14832 | 1530 | 0.030901 | 1.213909 | 0.081382 | ok | [1.141, 1.292] |
| Pass | all | 5 | box_entry | 14845 | 886 | 0.040358 | 1.288101 | 0.153978 | ok | [1.192, 1.392] |
| Pass | all | 15 | box_entry | 14845 | 2040 | 0.021231 | 1.142461 | 0.055924 | ok | [1.078, 1.211] |
| Pass | visible_count_adjustment | 10 | box_entry | 14845 | 1530 | 0.031086 | 1.215319 | 0.081332 | ok | [1.144, 1.291] |
| Carry | all | 10 | box_entry | 15525 | 1680 | 0.035391 | 1.287144 | 0.067421 | ok | [1.188, 1.394] |
| Carry | gap_le_5 | 10 | box_entry | 14673 | 1580 | 0.033848 | 1.273052 | 0.065889 | ok | [1.154, 1.405] |
| Carry | gap_le_3 | 10 | box_entry | 12962 | 1381 | 0.025771 | 1.201792 | 0.063758 | ok | [1.075, 1.344] |
| Carry | exclude_immediate | 10 | box_entry | 15236 | 1391 | 0.024384 | 1.189959 | 0.04336 | ok | [1.094, 1.295] |
| Carry | exclude_oob | 10 | box_entry | 13076 | 1459 | 0.034734 | 1.281124 | 0.068806 | ok | [1.187, 1.382] |
| Carry | exclude_coincidence | 10 | box_entry | 15507 | 1679 | 0.035223 | 1.285599 | 0.067509 | ok | [1.187, 1.392] |
| Carry | all | 5 | box_entry | 15525 | 1023 | 0.050416 | 1.432739 | 0.123878 | ok | [1.287, 1.595] |
| Carry | all | 15 | box_entry | 15525 | 2215 | 0.028447 | 1.224949 | 0.046574 | ok | [1.134, 1.324] |
| Carry | visible_count_adjustment | 10 | box_entry | 15525 | 1680 | 0.035359 | 1.286852 | 0.067423 | ok | [1.190, 1.392] |

| action_type | scope | horizon | outcome | N | positive_N | coefficient | odds_ratio_1sd | mcfadden_r2 | model_status | OR_1SD_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | all | 10 | shot | 14845 | 181 | 0.074368 | 1.594426 | 0.145205 | ok | [1.345, 1.891] |
| Pass | gap_le_5 | 10 | shot | 14419 | 175 | 0.050252 | 1.370577 | 0.146708 | ok | [1.009, 1.861] |
| Pass | gap_le_3 | 10 | shot | 13970 | 169 | 0.056477 | 1.425162 | 0.152893 | ok | [0.988, 2.055] |
| Pass | exclude_immediate | 10 | shot | 14828 | 164 | 0.070946 | 1.560562 | 0.127956 | ok | [1.289, 1.889] |
| Pass | exclude_oob | 10 | shot | 12300 | 153 | 0.085078 | 1.705228 | 0.148009 | ok | [1.459, 1.992] |
| Pass | exclude_coincidence | 10 | shot | 14832 | 181 | 0.074297 | 1.593712 | 0.145195 | ok | [1.344, 1.889] |
| Pass | all | 5 | shot | 14845 | 118 | 0.098715 | 1.85752 | 0.238696 | ok | [1.426, 2.420] |
| Pass | all | 15 | shot | 14845 | 264 | 0.056098 | 1.421775 | 0.074214 | ok | [1.199, 1.686] |
| Carry | all | 10 | shot | 15525 | 222 | 0.047445 | 1.402702 | 0.135315 | ok | [1.161, 1.695] |
| Carry | gap_le_5 | 10 | shot | 14673 | 214 | 0.049893 | 1.427406 | 0.134779 | ok | [1.121, 1.818] |
| Carry | gap_le_3 | 10 | shot | 12962 | 184 | 0.058404 | 1.516739 | 0.133892 | ok | [1.104, 2.085] |
| Carry | exclude_immediate | 10 | shot | 15490 | 187 | 0.044081 | 1.369448 | 0.11241 | ok | [1.115, 1.681] |
| Carry | exclude_oob | 10 | shot | 13076 | 192 | 0.043246 | 1.361313 | 0.126744 | ok | [1.122, 1.652] |
| Carry | exclude_coincidence | 10 | shot | 15507 | 222 | 0.047326 | 1.401514 | 0.135365 | ok | [1.159, 1.695] |
| Carry | all | 5 | shot | 15525 | 150 | 0.075087 | 1.708394 | 0.232086 | ok | [1.230, 2.373] |
| Carry | all | 15 | shot | 15525 | 295 | 0.039455 | 1.325004 | 0.077791 | ok | [1.100, 1.596] |

Unstable model rows across the main and sensitivity tables: **0**.
Nonconvergence, singular information or large/separated coefficients are flagged
instead of introducing a rare-event modeling framework. xG sensitivity means are
retained descriptively in the sensitivity CSV, with Shot-reference exclusion for xG.

![Horizon comparisons](../outputs/figures/phase5b_horizon_sensitivity.png)

## G. Football interpretation

### Observed finding

For Pass and Carry, greater observed opponent-centroid displacement toward increasing
attacking x retains a positive box-entry association beyond the specified progression,
start-position and gap controls. This survives later-only outcome exclusion and all
headline observation sensitivities. The Shot pattern points in the same direction
with greater uncertainty; xG evidence is descriptive. Width/depth findings are modest
and Pass-specific, with no clear NN-spacing relationship. This does not establish
that a spatial metric improves prediction out of sample.

### Plausible tactical interpretation

A visible opponent centroid shifting farther toward the attacked goal could be
consistent with defenders retreating or with territorial pressure around the advancing
action. The modest Pass extent result could also reflect a more compact visible group
near the box. These are possible explanations, not established mechanisms: the subset
of defenders in view can change, and no defensive-context classification is available.
The positive Leverkusen-centroid comparison also supports considering shared spatial
context rather than attributing the entire association to an opponent response.

## H. Limitations

- Observational association; no causal attribution to spatial change.
- Event-aligned partial observations, not tracking; changing visible populations.
- Anchor timing gaps can span intervening actions; TO need not be physical arrival.
- Repeated observations within spells/matches and shared future outcomes. Match
  clustering addresses within-match dependence, with only 34 independent clusters.
- Sparse Shots and zero-heavy xG; terminal-Shot exclusion inherited from Phase 3A/5A.
- Immediate outcomes may occur at TO; their exclusion changes the analyzed population.
- No defensive-context classification; basic linear logit controls may leave residual
  context differences. Progression and centroid displacement are related predictors.
- Secondary and sensitivity models are correlated comparisons, not independent
  discoveries. No multiplicity-adjusted confirmatory claim or causal claim is made.
- Separate Pass/Carry fits describe differing associations; no formal between-action
  interaction test is performed. Horizon choice remains pre-specified.

## I. Decision

**PHASE 5B — COMPLETE / ROBUST SPATIAL-DANGER ASSOCIATIONS IDENTIFIED**

The decision rests on the primary centroid / box-entry association surviving basic
adjustment and every requested headline sensitivity for both actions. It does not
classify all secondary metrics or sparse Shot/xG outcomes as equally robust.

Phase 5C — Sequence Effectiveness is the next step. No Phase 4B motif data or motif
outcomes are read, and no Phase 5C analysis is performed.

### Reproducibility

Run `.venv/Scripts/python.exe scripts/spatial_change_to_danger.py`. It reads only the
two frozen analytical inputs below and writes the three Phase 5B CSVs, this report
and three figures. Existing core CSVs must reproduce byte-for-byte on rerun.
No prior pipeline or artifact inventory is recomputed. Pinned provider revision:
`533862946a73608c134d18b78226b6371ce7173c`.

| input | sha256 |
| --- | --- |
| outputs/analysis/phase4a_progression_spatial_change.csv | 0e08e7066d15296b1e9ddcc6ab49c16336ef29e4364c70bec6ea69ed02f5660b |
| outputs/analysis/phase5a_anchor_outcomes.csv | 60a4dcc5d56549f7df8d264d43ede468839d8ec58179d230f7fec2d3346e1d40 |

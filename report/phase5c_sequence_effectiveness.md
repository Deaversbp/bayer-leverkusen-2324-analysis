# Phase 5C: sequence effectiveness

## A. Question and terminal-anchor alignment

Do the locked Pass/Carry compositions differ in danger after progression, starting
position and timing adjustment?

```text
start state → action 1 → intermediate state(s) → final action
→ TERMINAL spatial anchor → future danger
```

The frozen Phase 4B window of length **k** uses **anchor_k_event_id** (anchor 2 or 3)
as `terminal_anchor_event_id`, joined by match + UUID to Phase 5A `reference_event_id`.
Spell, index, event type and terminal timestamp must agree. No start/intermediate
outcome or sequence-start clock is used. Total progression, duration, motifs and
support flags are consumed from Phase 4B, without rebuilding windows.

**10s box entry is primary.** Shots and provider future xG remain separate secondary
outcomes. Canonical outcomes include danger at the terminal event itself; exclusion
sensitivities distinguish later danger. No motifs are redefined using Phase 5B.

## B. Analytical sample

**24,273 / 24,273 two-action** and **19,651 / 19,651 three-action** windows join exactly:
**43,924 rows, 0 unmatched, 0 context conflicts**, across 34 matches. These are
overlapping fixed windows, not independent attacking sequences. Lengths are modeled
separately. Rates in all tables are proportions unless marked as percentages.

| window_length | N | matches | box_entry_N | box_entry_rate | shot_N | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 24273 | 34 | 2565 | 0.105673 | 310 | 0.012771 | 0.00123 |
| 3 | 19651 | 34 | 2095 | 0.10661 | 240 | 0.012213 | 0.00118 |

Each motif's matches, sample share and covariate medians appear below. PP has 1,232
windows and 119 positive box-entry rows. PPP has 121 windows in 32 matches and 15
positives. CCC has only 17 windows in 12 matches and one positive: estimable here,
but extremely uncertain. The model uses all 34 matches as covariance clusters.

## C. Two-action effectiveness

### Raw composition

| motif | N | share_of_windows | matches | median_total_progression | median_start_x | median_duration | box_entry_rate | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP | 1232 | 0.050756 | 34 | 1.95 | 58 | 2.4615 | 0.096591 | 0.007305 | 0.000872 |
| PC | 11800 | 0.486137 | 34 | 2.3 | 63.7 | 2.512 | 0.106695 | 0.012966 | 0.001211 |
| CP | 10679 | 0.439954 | 34 | 4.1 | 62.8 | 2.577 | 0.104785 | 0.012735 | 0.001235 |
| CC | 562 | 0.023153 | 34 | 4.2 | 56.25 | 5.388 | 0.120996 | 0.021352 | 0.002327 |

**CC has the highest raw 10s box-entry rate (12.10%)**, followed by PC (10.67%),
CP (10.48%) and PP (9.66%). That is a descriptive ranking with differing contexts.

![Raw two-action rates](../outputs/figures/phase5c_two_action_raw.png)

### Adjusted contrasts and probabilities

Unpenalized logistic models use `motif + total_progression + first_action_start_x
+ duration_seconds`, with PP/PPP treatment-reference coding. Match-cluster CR1
covariance uses `G/(G−1) × (N−1)/(N−K)` and 95% `t(G−1)` intervals, as in Phase 5B.
No iid p-values or predictive model selection are used. The shared estimator now
optionally exposes its full coefficient covariance for categorical contrasts and
probabilities; its default Phase 5B behavior is unchanged.

| motif | model_N | motif_N | motif_positive_N | coefficient | odds_ratio | predicted_probability | model_status | OR_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP | 24273 | 1232 | 119 | 0 | 1 | 0.08975 | ok | [1.000, 1.000] |
| PC | 24273 | 11800 | 1259 | 0.003482 | 1.003488 | 0.090035 | ok | [0.844, 1.194] |
| CP | 24273 | 10679 | 1119 | -0.017197 | 0.98295 | 0.088355 | ok | [0.825, 1.171] |
| CC | 24273 | 562 | 68 | 0.103091 | 1.108593 | 0.098536 | ok | [0.768, 1.601] |

- **CC vs PP:** adjusted OR **1.109 [0.768, 1.601]**. Higher adjusted effectiveness
  is **not established**. The interval still permits meaningful differences in
  either direction; absence of evidence is not equivalence.
- **PC vs CP:** OR **1.021 [0.967, 1.078]**,
  from the full-covariance contrast `beta_PC − beta_CP`. No clear order difference
  remains at comparable modeled context.
- Neither PC nor CP differs clearly from PP. Adding motif identity changes
  McFadden pseudo-R² by only **0.000051** beyond the three context controls.

Predicted probabilities use the **same length-specific median covariates for every
motif**. These are model-based descriptions, not hypothetical tactical interventions.
Logit-scale delta-method intervals use the match-clustered covariance. PP/PPP OR=1
is a fixed comparison baseline, not an estimated confidence interval.

| window_length | total_progression | first_action_start_x | duration_seconds |
| --- | --- | --- | --- |
| 2 | 3.1 | 63.2 | 2.571 |
| 3 | 4 | 63 | 4.176 |

Two-action predicted box-entry probabilities are **8.98% PP, 9.00% PC, 8.84% CP,
9.85% CC**, at the common median context. Full probability intervals are in the CSV.

![Adjusted two-action ORs](../outputs/figures/phase5c_two_action_adjusted_or.png)

![Adjusted probabilities](../outputs/figures/phase5c_two_action_probabilities.png)

## D. Three-action effectiveness

| motif | N | share_of_windows | matches | median_total_progression | median_start_x | median_duration | box_entry_rate | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPP | 121 | 0.006157 | 32 | -0.2 | 62.9 | 4.448 | 0.123967 | 0.008264 | 0.002163 |
| PPC | 932 | 0.047428 | 34 | 2.45 | 57.6 | 4.283 | 0.099785 | 0.005365 | 0.000632 |
| PCP | 8365 | 0.425678 | 34 | 3 | 63.7 | 3.927 | 0.105081 | 0.011715 | 0.001087 |
| PCC | 385 | 0.019592 | 34 | 8.6 | 56.7 | 6.781 | 0.127273 | 0.015584 | 0.00223 |
| CPP | 873 | 0.044425 | 34 | 5.3 | 56.8 | 4.455 | 0.09622 | 0.008018 | 0.000868 |
| CPC | 8588 | 0.437026 | 34 | 4.8 | 63 | 4.2675 | 0.108873 | 0.013624 | 0.001299 |
| CCP | 370 | 0.018829 | 34 | 7.75 | 55.65 | 6.836 | 0.105405 | 0.016216 | 0.001251 |
| CCC | 17 | 0.000865 | 12 | 13.2 | 54.7 | 8.945 | 0.058824 | 0 | 0 |

PCC has the highest raw rate (**12.73%**), closely followed by rare PPP (**12.40%**).
CPC/PCP dominate support (8,588/8,365 windows), rather than those raw leaders.

| motif | model_N | motif_N | motif_positive_N | coefficient | odds_ratio | predicted_probability | model_status | OR_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PPP | 19651 | 121 | 15 | 0 | 1 | 0.114151 | ok | [1.000, 1.000] |
| PPC | 19651 | 932 | 93 | -0.222177 | 0.800774 | 0.093536 | ok | [0.417, 1.536] |
| PCP | 19651 | 8365 | 879 | -0.291086 | 0.747451 | 0.087855 | ok | [0.388, 1.439] |
| PCC | 19651 | 385 | 49 | -0.08935 | 0.914526 | 0.105423 | ok | [0.424, 1.974] |
| CPP | 19651 | 873 | 84 | -0.284381 | 0.75248 | 0.088394 | ok | [0.392, 1.446] |
| CPC | 19651 | 8588 | 935 | -0.249967 | 0.778827 | 0.091207 | ok | [0.403, 1.505] |
| CCP | 19651 | 370 | 39 | -0.25513 | 0.774816 | 0.09078 | ok | [0.363, 1.653] |
| CCC | 19651 | 17 | 1 | -1.132086 | 0.32236 | 0.039883 | ok | [0.036, 2.885] |

**No adjusted motif contrast versus PPP excludes OR=1.** PCC vs PPP is
**0.915 [0.424, 1.974]**; CCC is **0.322 [0.036, 2.885]** on just one positive.
PPP is an estimable reference but its small sample makes these contrasts imprecise.
The full model adds only **0.000278** McFadden pseudo-R² beyond progression/start/duration.
There is no robust three-action effectiveness winner. Probabilities at the common
three-action medians are descriptive and inherit this uncertainty.

![Three-action summary](../outputs/figures/phase5c_three_action_summary.png)

Carry-count aggregation is secondary and does not replace the eight motifs:

| carry_count | N | box_entry_rate | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- |
| 0 | 121 | 0.123967 | 0.008264 | 0.002163 |
| 1 | 10170 | 0.103835 | 0.010816 | 0.001027 |
| 2 | 9343 | 0.109494 | 0.013807 | 0.001336 |
| 3 | 17 | 0.058824 | 0 | 0 |

The rates do not support a monotonic "more Carries = more effectiveness" claim.

### Direction and starting-position context

All locked F/R profiles have substantial descriptive support. F is positive action
progression; R includes zero and negative progression. FF/FFF have higher raw rates
and more progression than RR/RRR. No separate direction-regression family is fitted.

| window_length | motif | N | median_total_progression | box_entry_rate |
| --- | --- | --- | --- | --- |
| 2 | FF | 7596 | 13.9 | 0.134413 |
| 2 | FR | 5024 | 3.5 | 0.09992 |
| 2 | RF | 5632 | 1.3 | 0.104936 |
| 2 | RR | 6021 | -8.8 | 0.074905 |
| 3 | FFF | 3355 | 21.6 | 0.145753 |
| 3 | FFR | 2401 | 9.9 | 0.107872 |
| 3 | FRF | 1798 | 8.5 | 0.126251 |
| 3 | FRR | 2302 | -1.6 | 0.080365 |
| 3 | RFF | 2865 | 7.8 | 0.115183 |
| 3 | RFR | 1732 | 1 | 0.094688 |
| 3 | RRF | 2741 | -3.5 | 0.09595 |
| 3 | RRR | 2457 | -12.9 | 0.072446 |

Inherited thirds are `[0,40)`, `[40,80)`, `[80,120]`. Cells show **N / raw 10s rate**:

| window_length | motif | attacking_third | defensive_third | middle_third |
| --- | --- | --- | --- | --- |
| 2 | CC | 134 / 17.16% | 158 / 6.33% | 270 / 12.96% |
| 2 | CP | 2276 / 18.67% | 1924 / 5.41% | 6479 / 9.11% |
| 2 | PC | 2682 / 18.75% | 1851 / 5.62% | 7267 / 8.97% |
| 2 | PP | 207 / 19.81% | 238 / 7.14% | 787 / 7.75% |
| 3 | CCC | 5 / 0.00% | 4 / 0.00% | 8 / 12.50% |
| 3 | CCP | 77 / 18.18% | 108 / 5.56% | 185 / 10.27% |
| 3 | CPC | 1791 / 18.26% | 1501 / 5.86% | 5296 / 9.82% |
| 3 | CPP | 134 / 23.13% | 178 / 6.74% | 561 / 7.31% |
| 3 | PCC | 57 / 17.54% | 80 / 10.00% | 248 / 12.50% |
| 3 | PCP | 1755 / 17.38% | 1226 / 6.85% | 5384 / 9.10% |
| 3 | PPC | 146 / 21.23% | 179 / 6.70% | 607 / 8.24% |
| 3 | PPP | 21 / 9.52% | 21 / 14.29% | 79 / 12.66% |

Two-action CC is highest in the middle third but not the attacking third. Rare
three-action cells also reorder across thirds. No pooled adjusted ranking is treated
as universal; with no established overall motif advantage, these descriptions do
not justify a large interaction model.

## E. Shot and future xG

The two-action Shot model is numerically stable, but its reference PP has only nine
positive rows. CC has 12. These are shared-outcome reference rows, not unique Shots.

| motif | model_N | motif_N | motif_positive_N | coefficient | odds_ratio | predicted_probability | model_status | OR_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP | 24273 | 1232 | 9 | 0 | 1 | 0.004316 | ok | [1.000, 1.000] |
| PC | 24273 | 11800 | 153 | 0.360517 | 1.434071 | 0.006178 | ok | [0.652, 3.154] |
| CP | 24273 | 10679 | 136 | 0.377658 | 1.458864 | 0.006284 | ok | [0.674, 3.160] |
| CC | 24273 | 562 | 12 | 0.70799 | 2.029907 | 0.008722 | ok | [0.743, 5.545] |

CC's raw Shot rate is **2.14%**, versus **0.73%** for PP, but adjusted OR
**2.030 [0.743, 5.545]** is inconclusive. PC vs CP Shot OR is **0.983 [0.894, 1.081]**.
Three-action Shots remain descriptive: PPP has one positive and CCC zero, so no
three-action Shot model is fitted.

Future xG remains descriptive; no zero-heavy or adjusted mean model is added:

| window_length | motif | mean_future_xg | proportion_positive_xg | mean_positive_xg |
| --- | --- | --- | --- | --- |
| 2 | PP | 0.000872 | 0.007305 | 0.119405 |
| 2 | PC | 0.001211 | 0.012966 | 0.093398 |
| 2 | CP | 0.001235 | 0.012735 | 0.096995 |
| 2 | CC | 0.002327 | 0.021352 | 0.108989 |
| 3 | PPP | 0.002163 | 0.008264 | 0.261719 |
| 3 | PPC | 0.000632 | 0.005365 | 0.117859 |
| 3 | PCP | 0.001087 | 0.011715 | 0.092786 |
| 3 | PCC | 0.00223 | 0.015584 | 0.143116 |
| 3 | CPP | 0.000868 | 0.008018 | 0.108195 |
| 3 | CPC | 0.001299 | 0.013624 | 0.095382 |
| 3 | CCP | 0.001251 | 0.016216 | 0.077163 |
| 3 | CCC | 0 | 0 | — |

CC has the largest raw two-action mean xG (**0.002327**), but this sparse unadjusted
pattern does not establish an independent motif effect. PCC/PPP have high three-action
means on small Shot support. Excluding immediate terminal Shots gives:

| window_length | motif | N | shot_rate | mean_future_xg |
| --- | --- | --- | --- | --- |
| 2 | PP | 1232 | 0.007305 | 0.000872 |
| 2 | PC | 11779 | 0.011206 | 0.001099 |
| 2 | CP | 10666 | 0.011532 | 0.001128 |
| 2 | CC | 558 | 0.014337 | 0.001073 |
| 3 | PPP | 121 | 0.008264 | 0.002163 |
| 3 | PPC | 932 | 0.005365 | 0.000632 |
| 3 | PCP | 8355 | 0.010533 | 0.000971 |
| 3 | PCC | 383 | 0.010444 | 0.000659 |
| 3 | CPP | 873 | 0.008018 | 0.000868 |
| 3 | CPC | 8570 | 0.011552 | 0.001168 |
| 3 | CCP | 370 | 0.016216 | 0.001251 |
| 3 | CCC | 17 | 0 | 0 |

The two-action Shot-exclusion model gives CC vs PP **1.447 [0.466, 4.487]** and
PC vs CP **0.946 [0.866, 1.033]**; neither establishes a difference.

## F. Spatial explanation

Only after the primary models, one two-action box-entry model adds the frozen
**net_opp_centroid_x**, meaning terminal minus starting opponent centroid x.
No per-leg substitute, other geometry predictor or formal mediation claim is used.

| motif | model_N | motif_N | motif_positive_N | coefficient | odds_ratio | predicted_probability | model_status | OR_95CI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PP | 24267 | 1232 | 119 | 0 | 1 | 0.085977 | ok | [1.000, 1.000] |
| PC | 24267 | 11797 | 1259 | 0.018065 | 1.018229 | 0.087407 | ok | [0.857, 1.209] |
| CP | 24267 | 10676 | 1119 | 0.010134 | 1.010186 | 0.086777 | ok | [0.847, 1.204] |
| CC | 24267 | 562 | 68 | 0.061784 | 1.063733 | 0.090958 | ok | [0.730, 1.551] |

Six windows lack net centroid data, leaving **24,267** rows. CC's OR moves from
**1.109 to 1.064 [0.730, 1.551]**. Its small positive point estimate overlaps with its
characteristic observed centroid displacement, but neither model establishes a CC
advantage. The comparison also involves six missing-data exclusions, so the change
is descriptive. PC vs CP becomes **1.008 [0.954, 1.064]**. There is no motif advantage
that must be given a spatial explanation.

## G. Robustness

Primary two-action models are repeated at 5/15s (10s stays primary), with the inherited
strict-chain ≤5/≤3 rules, immediate box-entry exclusion, and whole-window OOB/coincidence
exclusion. `maximum_leg_gap <= H` means **every leg <= H**, verified against the stored
leg gaps. Unknown OOB/coincidence flags are excluded under the existing support logic.

| scope | horizon | motif | model_N | odds_ratio | OR_95CI |
| --- | --- | --- | --- | --- | --- |
| all | 10 | CC | 24273 | 1.108593 | [0.768, 1.601] |
| all | 10 | PC_vs_CP | 24273 | 1.020894 | [0.967, 1.078] |
| all | 5 | CC | 24273 | 1.101022 | [0.773, 1.569] |
| all | 5 | PC_vs_CP | 24273 | 1.058092 | [0.987, 1.134] |
| all | 15 | CC | 24273 | 1.078647 | [0.774, 1.504] |
| all | 15 | PC_vs_CP | 24273 | 1.01021 | [0.967, 1.055] |
| gap_le_5 | 10 | CC | 22257 | 1.212908 | [0.788, 1.866] |
| gap_le_5 | 10 | PC_vs_CP | 22257 | 1.012092 | [0.955, 1.072] |
| gap_le_3 | 10 | CC | 18976 | 1.328869 | [0.761, 2.320] |
| gap_le_3 | 10 | PC_vs_CP | 18976 | 1.015929 | [0.953, 1.083] |
| exclude_immediate | 10 | CC | 23882 | 1.009234 | [0.667, 1.526] |
| exclude_immediate | 10 | PC_vs_CP | 23882 | 0.969857 | [0.918, 1.024] |
| exclude_oob | 10 | CC | 18940 | 1.016219 | [0.659, 1.567] |
| exclude_oob | 10 | PC_vs_CP | 18940 | 1.029026 | [0.975, 1.086] |
| exclude_coincidence | 10 | CC | 24234 | 1.095374 | [0.758, 1.583] |
| exclude_coincidence | 10 | PC_vs_CP | 24234 | 1.021372 | [0.967, 1.079] |
| centroid_adjusted | 10 | CC | 24267 | 1.063733 | [0.730, 1.551] |
| centroid_adjusted | 10 | PC_vs_CP | 24267 | 1.007962 | [0.954, 1.064] |

The central conclusion persists: **CC vs PP and PC vs CP intervals include 1 in
every requested sensitivity**. CC estimates span about 1.01–1.33; shorter gaps reduce
its sample from 562 to 383 (≤5s) and 183 (≤3s), widening uncertainty. Removing immediate
box-entry terminals brings CC to **1.009 [0.667, 1.526]** and reverses the tiny PC/CP
point ordering, without establishing a difference. OOB exclusion gives CC **1.016**;
coincidence exclusion gives **1.095**, with both intervals crossing 1.

Three-action horizon comparisons remain descriptive:

| motif | 5s_rate | 10s_rate | 15s_rate |
| --- | --- | --- | --- |
| CCC | 0.058824 | 0.058824 | 0.058824 |
| CCP | 0.059459 | 0.105405 | 0.135135 |
| CPC | 0.067536 | 0.108873 | 0.147299 |
| CPP | 0.054983 | 0.09622 | 0.135166 |
| PCC | 0.080519 | 0.127273 | 0.161039 |
| PCP | 0.061207 | 0.105081 | 0.142379 |
| PPC | 0.061159 | 0.099785 | 0.139485 |
| PPP | 0.099174 | 0.123967 | 0.132231 |

PPP is highest at 5s, while PCC is highest at 10s/15s and in the ≤5/≤3 gap samples.
PCC also remains high after OOB/coincidence exclusions, but PPP overtakes it after
immediate-entry exclusion. Sparse CCC becomes 0/9 and 0/4 positive at the short-gap
cuts. This is no stable adjusted ranking; three-action sensitivities are deliberately
descriptive. All eight motif rates and sample sizes for every scope are retained in
the single sensitivity CSV.

All fitted canonical and sensitivity models are numerically stable. For general reuse,
an absent or pure-outcome motif cell is explicitly unestimable and retained descriptively;
no penalized or rare-event framework is introduced. No such exclusion was needed here.

## H. Football interpretation

### Observed findings

Raw motif differences are small for the well-supported two-action motifs and largely
disappear under the specified context adjustment. CC's raw advantage is not established
after adjustment; PC and CP have very similar adjusted outcomes. Three-action rankings
are uncertain and contribute almost no additional in-sample model fit. Sparse Shot/xG
patterns do not supply convincing independent motif-effectiveness evidence.

### Plausible tactical interpretation

Territorial progression, starting location and timing may matter more for these
near-term outcomes than whether a short window contains a particular Pass/Carry order.
The same symbolic motif can occur in very different football situations. This is a
possible interpretation, not evidence that order is irrelevant or that one composition
causes an outcome. Phase 5B's spatial association does not imply composition-level
effectiveness once basic context is considered.

## I. Limitations

- Overlapping fixed windows and repeated motifs within matches/spells share actions,
  anchors and future outcomes. Match clustering addresses within-match dependence;
  43,924 windows are not 43,924 independent attacks.
- Observational associations and partial 360 observations, with changing visible players.
- Sparse Shots/xG and rare motifs; numerical estimability does not imply precise evidence.
- Fixed windows are not natural tactical boundaries. Observation gaps may span intervening events.
- Immediate outcomes can occur at the terminal anchor; exclusion changes the population.
- Adjustment does not eliminate all confounding; controls are simple linear logit terms.
  Common-median probabilities are model descriptions with potentially limited joint
  covariate support in rare motifs, not tactical interventions.
- Locked spell membership excludes terminal-boundary Shots. Phase 5A has only 110
  qualifying Shots; the canonical outcomes do not cover all attack-ending attempts.
- No defensive-context conditioning or classification yet. Sensitivities are related
  comparisons, not independent confirmations; no equivalence or causal claim is made.

## J. Decision

**PHASE 5C — COMPLETE / MOTIF EFFECTIVENESS MOSTLY EXPLAINED BY PROGRESSION AND CONTEXT**

The adjusted two-action estimates are near 1 and motif terms add negligible fit for
both lengths. This supports proceeding to **discussion of Phase 6 — Defensive Context
and Final Tactical Synthesis**, to consider context the present models omit. It does
not establish equivalent motifs, and does not authorize automatic Phase 6 execution.
No defensive structures were classified in this phase.

### Reproduction

Run `.venv/Scripts/python.exe scripts/sequence_effectiveness.py`. The analysis reads
only the frozen Phase 4B window CSV and Phase 5A anchor outcomes, then writes three
Phase 5C CSVs, this report and four figures. Core CSV reruns must match byte-for-byte.
Only these immediate source hashes are recorded; prior pipelines are not replayed.

| input | sha256 |
| --- | --- |
| outputs/analysis/phase4b_spatial_sequence_windows.csv | 8b26620d1ee85bfc3377e9fa939237057fd11277038670fd651de303dbea42e8 |
| outputs/analysis/phase5a_anchor_outcomes.csv | 60a4dcc5d56549f7df8d264d43ede468839d8ec58179d230f7fec2d3346e1d40 |

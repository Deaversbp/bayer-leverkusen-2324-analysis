"""Measured Phase 5C report; raw composition is not a tactical ranking."""

import pandas as pd

from leverkusen.sequences.effectiveness import CONTROLS, description
from leverkusen.spatial.danger_report import markdown

DECISION = "PHASE 5C — COMPLETE / MOTIF EFFECTIVENESS MOSTLY EXPLAINED BY PROGRESSION AND CONTEXT"


def model_table(rows):
    table = rows[["motif", "model_N", "motif_N", "motif_positive_N", "coefficient", "odds_ratio",
                  "predicted_probability", "model_status"]].copy()
    table["OR_95CI"] = [f"[{a:.3f}, {b:.3f}]" if pd.notna(a) else "not estimable"
                        for a, b in zip(rows.or_ci_low, rows.or_ci_high)]
    return markdown(table)


def render_report(data, summary, sensitivity, hashes):
    raw = summary[summary.record_type.eq("raw_motif")]
    models = summary[summary.record_type.eq("model") & summary.outcome.eq("box_entry")]
    shot = summary[summary.record_type.eq("model") & summary.outcome.eq("shot")]
    contrast = summary[summary.record_type.eq("contrast") & summary.outcome.eq("box_entry")].iloc[0]
    explanatory = sensitivity[sensitivity.record_type.eq("model") & sensitivity.scope.eq("centroid_adjusted")]
    headline = pd.concat([summary, sensitivity])
    headline = headline[headline.window_length.eq(2) & headline.outcome.eq("box_entry")
                        & headline.record_type.isin(["model", "contrast"]) & headline.motif.isin(["CC", "PC_vs_CP"])]
    head = headline[["scope", "horizon", "motif", "model_N", "odds_ratio"]].copy()
    head["OR_95CI"] = [f"[{lo:.3f}, {hi:.3f}]" for lo, hi in zip(headline.or_ci_low, headline.or_ci_high)]
    thirds = summary[summary.record_type.eq("starting_third")].copy()
    thirds["N / rate"] = [f"{int(n)} / {rate:.2%}" for n, rate in zip(thirds.N, thirds.box_entry_rate)]
    thirds = thirds.pivot(index=["window_length", "motif"], columns="starting_third", values="N / rate").reset_index()
    direction = summary[summary.record_type.eq("direction")]
    carries = summary[summary.record_type.eq("carry_count")]
    population = pd.DataFrame([dict(window_length=k, **description(g)) for k, g in data.groupby("window_length")])
    medians = data.groupby("window_length")[list(CONTROLS)].median().reset_index()
    three_horizons = pd.concat([raw[raw.window_length.eq(3)], sensitivity[sensitivity.record_type.eq("raw_motif")
        & sensitivity.window_length.eq(3) & sensitivity.outcome.eq("box_entry") & sensitivity.scope.eq("all")]])
    three_horizons = three_horizons.pivot(index="motif", columns="horizon", values="box_entry_rate").reset_index()
    three_horizons.columns = ["motif", "5s_rate", "10s_rate", "15s_rate"]
    xg_later = sensitivity[sensitivity.record_type.eq("raw_motif") & sensitivity.outcome.eq("shot")]
    return f"""# Phase 5C: sequence effectiveness

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

{markdown(population[["window_length", "N", "matches", "box_entry_N", "box_entry_rate", "shot_N", "shot_rate", "mean_future_xg"]])}

Each motif's matches, sample share and covariate medians appear below. PP has 1,232
windows and 119 positive box-entry rows. PPP has 121 windows in 32 matches and 15
positives. CCC has only 17 windows in 12 matches and one positive: estimable here,
but extremely uncertain. The model uses all 34 matches as covariance clusters.

## C. Two-action effectiveness

### Raw composition

{markdown(raw[raw.window_length.eq(2)][["motif", "N", "share_of_windows", "matches", "median_total_progression", "median_start_x", "median_duration", "box_entry_rate", "shot_rate", "mean_future_xg"]])}

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

{model_table(models[models.window_length.eq(2)])}

- **CC vs PP:** adjusted OR **1.109 [0.768, 1.601]**. Higher adjusted effectiveness
  is **not established**. The interval still permits meaningful differences in
  either direction; absence of evidence is not equivalence.
- **PC vs CP:** OR **{contrast.odds_ratio:.3f} [{contrast.or_ci_low:.3f}, {contrast.or_ci_high:.3f}]**,
  from the full-covariance contrast `beta_PC − beta_CP`. No clear order difference
  remains at comparable modeled context.
- Neither PC nor CP differs clearly from PP. Adding motif identity changes
  McFadden pseudo-R² by only **0.000051** beyond the three context controls.

Predicted probabilities use the **same length-specific median covariates for every
motif**. These are model-based descriptions, not hypothetical tactical interventions.
Logit-scale delta-method intervals use the match-clustered covariance. PP/PPP OR=1
is a fixed comparison baseline, not an estimated confidence interval.

{markdown(medians)}

Two-action predicted box-entry probabilities are **8.98% PP, 9.00% PC, 8.84% CP,
9.85% CC**, at the common median context. Full probability intervals are in the CSV.

![Adjusted two-action ORs](../outputs/figures/phase5c_two_action_adjusted_or.png)

![Adjusted probabilities](../outputs/figures/phase5c_two_action_probabilities.png)

## D. Three-action effectiveness

{markdown(raw[raw.window_length.eq(3)][["motif", "N", "share_of_windows", "matches", "median_total_progression", "median_start_x", "median_duration", "box_entry_rate", "shot_rate", "mean_future_xg"]])}

PCC has the highest raw rate (**12.73%**), closely followed by rare PPP (**12.40%**).
CPC/PCP dominate support (8,588/8,365 windows), rather than those raw leaders.

{model_table(models[models.window_length.eq(3)])}

**No adjusted motif contrast versus PPP excludes OR=1.** PCC vs PPP is
**0.915 [0.424, 1.974]**; CCC is **0.322 [0.036, 2.885]** on just one positive.
PPP is an estimable reference but its small sample makes these contrasts imprecise.
The full model adds only **0.000278** McFadden pseudo-R² beyond progression/start/duration.
There is no robust three-action effectiveness winner. Probabilities at the common
three-action medians are descriptive and inherit this uncertainty.

![Three-action summary](../outputs/figures/phase5c_three_action_summary.png)

Carry-count aggregation is secondary and does not replace the eight motifs:

{markdown(carries[["carry_count", "N", "box_entry_rate", "shot_rate", "mean_future_xg"]])}

The rates do not support a monotonic "more Carries = more effectiveness" claim.

### Direction and starting-position context

All locked F/R profiles have substantial descriptive support. F is positive action
progression; R includes zero and negative progression. FF/FFF have higher raw rates
and more progression than RR/RRR. No separate direction-regression family is fitted.

{markdown(direction[["window_length", "motif", "N", "median_total_progression", "box_entry_rate"]])}

Inherited thirds are `[0,40)`, `[40,80)`, `[80,120]`. Cells show **N / raw 10s rate**:

{markdown(thirds)}

Two-action CC is highest in the middle third but not the attacking third. Rare
three-action cells also reorder across thirds. No pooled adjusted ranking is treated
as universal; with no established overall motif advantage, these descriptions do
not justify a large interaction model.

## E. Shot and future xG

The two-action Shot model is numerically stable, but its reference PP has only nine
positive rows. CC has 12. These are shared-outcome reference rows, not unique Shots.

{model_table(shot)}

CC's raw Shot rate is **2.14%**, versus **0.73%** for PP, but adjusted OR
**2.030 [0.743, 5.545]** is inconclusive. PC vs CP Shot OR is **0.983 [0.894, 1.081]**.
Three-action Shots remain descriptive: PPP has one positive and CCC zero, so no
three-action Shot model is fitted.

Future xG remains descriptive; no zero-heavy or adjusted mean model is added:

{markdown(raw[["window_length", "motif", "mean_future_xg", "proportion_positive_xg", "mean_positive_xg"]])}

CC has the largest raw two-action mean xG (**0.002327**), but this sparse unadjusted
pattern does not establish an independent motif effect. PCC/PPP have high three-action
means on small Shot support. Excluding immediate terminal Shots gives:

{markdown(xg_later[["window_length", "motif", "N", "shot_rate", "mean_future_xg"]])}

The two-action Shot-exclusion model gives CC vs PP **1.447 [0.466, 4.487]** and
PC vs CP **0.946 [0.866, 1.033]**; neither establishes a difference.

## F. Spatial explanation

Only after the primary models, one two-action box-entry model adds the frozen
**net_opp_centroid_x**, meaning terminal minus starting opponent centroid x.
No per-leg substitute, other geometry predictor or formal mediation claim is used.

{model_table(explanatory)}

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

{markdown(head)}

The central conclusion persists: **CC vs PP and PC vs CP intervals include 1 in
every requested sensitivity**. CC estimates span about 1.01–1.33; shorter gaps reduce
its sample from 562 to 383 (≤5s) and 183 (≤3s), widening uncertainty. Removing immediate
box-entry terminals brings CC to **1.009 [0.667, 1.526]** and reverses the tiny PC/CP
point ordering, without establishing a difference. OOB exclusion gives CC **1.016**;
coincidence exclusion gives **1.095**, with both intervals crossing 1.

Three-action horizon comparisons remain descriptive:

{markdown(three_horizons)}

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

**{DECISION}**

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

{markdown(pd.DataFrame(hashes, columns=["input", "sha256"]))}
"""

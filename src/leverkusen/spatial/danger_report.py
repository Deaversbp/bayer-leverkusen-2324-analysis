"""Compact Phase 5B measured report, without motif or causal claims."""

import numpy as np
import pandas as pd

from leverkusen.spatial.danger_analysis import LABELS, PRIMARY, describe

DECISION = "PHASE 5B — COMPLETE / ROBUST SPATIAL-DANGER ASSOCIATIONS IDENTIFIED"


def markdown(frame):
    def cell(value):
        if pd.isna(value):
            return "—"
        if isinstance(value, (float, np.floating)):
            return f"{value:.6f}".rstrip("0").rstrip(".")
        return str(value)
    return "\n".join(["| " + " | ".join(frame.columns) + " |",
                      "| " + " | ".join("---" for _ in frame.columns) + " |",
                      *["| " + " | ".join(cell(v) for v in row) + " |"
                        for row in frame.itertuples(index=False, name=None)]])


def model_table(rows, *, sensitivity=False):
    cols = ["action_type", "scope", "horizon", "outcome"] if sensitivity else ["action_type", "spatial_metric", "model"]
    table = rows[[*cols, "N", "positive_N", "coefficient", "odds_ratio_1sd", "mcfadden_r2", "model_status"]].copy()
    if "spatial_metric" in table:
        table["spatial_metric"] = table.spatial_metric.map(LABELS)
    table["OR_1SD_95CI"] = [f"[{lo:.3f}, {hi:.3f}]" if pd.notna(lo) else "—"
                            for lo, hi in zip(rows.or_1sd_ci_low, rows.or_1sd_ci_high)]
    return markdown(table)


def render_report(data, summary, sensitivity, input_hashes):
    models = summary[summary.record_type.eq("model")]
    centroid = models[models.spatial_metric.eq(PRIMARY) & models.outcome.eq("box_entry")]
    secondary = models[~models.spatial_metric.eq(PRIMARY)]
    shots = models[models.outcome.eq("shot")]
    bins = summary[summary.record_type.eq("quartile") & summary.spatial_metric.eq(PRIMARY)]
    later_xg = sensitivity[sensitivity.record_type.eq("quartile") & sensitivity.outcome.eq("future_xg")]
    thirds = summary[summary.record_type.eq("starting_third")]
    population = pd.DataFrame([dict(action_type=action, **describe(group))
                               for action, group in [("All", data), *data.groupby("action_type", sort=True)]])
    availability = pd.DataFrame([dict(action_type=action, **{LABELS[m]: int(group[m].notna().sum()) for m in LABELS})
                                 for action, group in data.groupby("action_type", sort=True)])
    immediate = data.groupby("action_type")[["reference_is_box_entry", "reference_is_shot"]].sum().reset_index()
    unstable = pd.concat([models, sensitivity]).query("record_type == 'model' and model_status != 'ok'")
    return f"""# Phase 5B: spatial change to danger

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

**30,375 Phase 4A source rows → {len(data):,} exact TO joins**, with **0 unmatched rows**
and no identity or spell conflicts. Pass: **14,848**; Carry: **15,527**. Both cover
34 matches. Geometry missingness is handled per metric, never by dropping a whole
transition from the exported dataset. All rates below are proportions.

{markdown(population[["action_type", "N", "box_entry_positive_N", "box_entry_rate", "shot_positive_N", "shot_rate", "mean_future_xg"]])}

Available spatial-predictor rows:

{markdown(availability)}

Immediate TO events retained in the canonical analysis:

{markdown(immediate)}

## C. Opponent centroid-x → danger

**Greater opponent-centroid x displacement is followed by higher 10s box-entry
rates for both actions, and the association remains after the specified adjustment.**

### Descriptive quartiles

Quartiles use the full available predictor distribution separately for each action
type, with tied values kept together. Boundaries are presentation bins, not tactical
thresholds. The same centroid bins are retained for the starting-third descriptions.

{markdown(bins[["action_type", "quartile", "N", "median_spatial_change", "box_entry_rate", "shot_rate", "mean_future_xg"]])}

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

{model_table(centroid)}

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

{markdown(thirds[["action_type", "starting_third", "quartile", "N", "box_entry_rate"]])}

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

{model_table(secondary)}

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

{model_table(shots)}

Adjusted Shot ORs are **1.594 [1.345, 1.891] for Pass** and
**1.403 [1.161, 1.695] for Carry**, per +1 SD. The canonical modeled samples contain
181 and 222 positive reference rows, spread over only 27 and 28 matches respectively;
they do not represent that many distinct Shots.

Future xG stays descriptive: quartile means above, and positive proportions and
positive-only medians below. No distributional or linear xG model is fitted.

{markdown(bins[["action_type", "quartile", "N", "mean_future_xg", "proportion_positive_xg", "positive_xg_median"]])}

Mean 10s xG rises from **0.000524 to 0.002381** across Pass quartiles and from
**0.000607 to 0.002667** across Carry quartiles. This is an unadjusted descriptive
pattern, not evidence of an independently adjusted xG association. The joined
population has no missing horizon xG values.

The immediate-Shot exclusion also repeats the xG quartile descriptions using the
same canonical centroid-bin boundaries, so it tests the spatial pattern for danger
developing afterward rather than only reporting a change in overall mean:

{markdown(later_xg[["action_type", "quartile", "N", "mean_future_xg", "proportion_positive_xg", "positive_xg_median"]])}

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

{model_table(sensitivity[sensitivity.outcome.eq("box_entry")], sensitivity=True)}

{model_table(sensitivity[sensitivity.outcome.eq("shot")], sensitivity=True)}

Unstable model rows across the main and sensitivity tables: **{len(unstable)}**.
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

**{DECISION}**

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

{markdown(pd.DataFrame(input_hashes, columns=["input", "sha256"]))}
"""

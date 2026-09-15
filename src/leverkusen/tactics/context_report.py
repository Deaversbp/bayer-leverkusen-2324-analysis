"""Measured Phase 6A report, bounded before final synthesis."""

import pandas as pd

from leverkusen.spatial.danger_report import markdown
from leverkusen.tactics.context import COUNT, DIMENSIONS

DECISION = "PHASE 6A — COMPLETE / LIMITED DEFENSIVE-CONTEXT MODERATION"


def effect_table(rows, keys):
    table = rows[[*keys, "coefficient"]].copy()
    table["OR [95% CI]"] = [f"{r.odds_ratio:.3f} [{r.or_ci_low:.3f}, {r.or_ci_high:.3f}]" for r in rows.itertuples()]
    return markdown(table)


def render_report(data, summary, interactions, motif_summary, motifs):
    cuts = summary[summary.record_type.eq("cutpoints")][["context_dimension", "starting_third", "N", "lower_cut", "upper_cut"]].copy()
    for column in ("lower_cut", "upper_cut"):
        cuts[column] = cuts[column].map(lambda v: format(v, ".17g"))
    descriptions = summary[summary.record_type.eq("context")]
    centroid = descriptions[descriptions.context_dimension.eq("centroid")]
    primary = interactions.query("scope == 'all' and horizon == 10")
    coefficients = primary[primary.record_type.eq("coefficient")]
    slopes = primary[primary.record_type.eq("context_slope") & primary.context_dimension.eq("centroid")]
    predictions = primary[primary.record_type.eq("prediction")]
    probabilities = predictions.pivot(index=["action_type", "context"], columns="displacement_sd", values="probability").reset_index()
    probabilities.columns = ["action_type", "context", "minus_1_SD", "zero_delta", "plus_1_SD"]
    sensitivity = interactions[interactions.context_dimension.eq("centroid") & interactions.record_type.eq("coefficient") & interactions.term.eq("centroid_x_T3")]
    quartiles = summary[summary.record_type.eq("displacement_quartile")]
    raw_motifs = motif_summary[motif_summary.record_type.eq("raw")]
    motif_terms = motif_summary[motif_summary.record_type.eq("coefficient")]
    motif_contrasts = motif_summary[motif_summary.record_type.eq("contrast")]
    support = pd.DataFrame([dict(action_type=a, N=len(g), **{f"{dim}_missing_N": int(g[f"{dim}_context"].isna().sum()) for dim in DIMENSIONS},
                                 visible_count_min=g[COUNT].min(), visible_count_median=g[COUNT].median(), visible_count_max=g[COUNT].max())
                            for a, g in data.groupby("action_type", sort=False)])
    model_support = primary[primary.record_type.eq("coefficient") & primary.term.eq("centroid_per_sd")]
    return f"""# Phase 6A: defensive context analysis

## A. Question

Does the established association between progression, observed opponent-centroid displacement
and subsequent danger differ with the opponent geometry visible at the starting anchor?
Observed defensive context describes the available event-aligned 360 frame. It does not
identify a formation or reconstruct a defensive block. Box entry within 10 seconds remains primary.

## B. Context construction

**{len(data):,} frozen Phase 5B transitions: 14,848 Pass and 15,527 Carry, across 34 matches.**
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

{markdown(cuts)}

### Observability support

{markdown(support)}

Centroid, width and depth each have three unavailable starts; spacing has 34.
The primary model additionally excludes two rows with missing centroid response.
Tertile assignment weights eligible transitions, not matches equally.

![Context distribution](../outputs/figures/phase6a_context_distribution.png)

## C. Starting defensive depth

### Descriptive progression, response and danger

Rates below are proportions. Context is starting visible-centroid T1/T2/T3. `N` counts all
context rows; `centroid_response_N` is the available response denominator.

{markdown(centroid[["action_type", "context", "N", "centroid_response_N", "progression_median", "centroid_delta_median", "centroid_delta_mean", "box_entry_rate", "shot_rate", "mean_future_xg"]])}

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

{markdown(model_support[["action_type", "context_dimension", "N", "missing_N", "positive_N", "matches", "model_status", "mcfadden_r2"]])}

{effect_table(coefficients[coefficients.context_dimension.eq("centroid")], ["action_type", "term", "N"])}

### Displacement OR within each starting visible-centroid context

{effect_table(slopes, ["action_type", "context", "context_N", "context_positive_N"])}

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

{markdown(probabilities)}

![Predicted probabilities](../outputs/figures/phase6a_context_probabilities.png)

### Shot and future xG: descriptive only

Use action-wide centroid-displacement quartiles, shared across starting-centroid contexts,
without outcome-driven cuts. Q4 has higher Shot rates and mean future xG than Q1 in every
action/context cell, but the intermediate pattern is not consistently monotone. Deep visible
centroid contexts have the highest overall Shot rate for both actions. These are sparse,
overlapping future observations, not independent shots or adjusted Shot effects.
No Shot interaction models are fitted.

{markdown(quartiles[["action_type", "context", "quartile", "N", "shot_positive_N", "shot_rate", "mean_future_xg"]])}

## D. Width, depth and spacing context

Each secondary dimension gets one 10s interaction model per action with the **same centroid
displacement response mechanism** and the same three controls. Context T1/T2/T3 always
increases that dimension, relative to actions starting in the same third.

{markdown(descriptions[~descriptions.context_dimension.eq("centroid")][["action_type", "context_dimension", "context", "N", "progression_median", "centroid_delta_mean", "box_entry_rate"]])}

{effect_table(coefficients[~coefficients.context_dimension.eq("centroid")], ["action_type", "context_dimension", "term", "N"])}

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

{markdown(centroid[["action_type", "context", "progression_response_slope", "progression_response_ci_low", "progression_response_ci_high", "progression_response_rho"]])}

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

{markdown(raw_motifs[["motif", "context", "N", "matches", "positive_N", "box_entry_rate"]])}

```text
box_entry_10s ~ motif + starting_centroid_context + motif:starting_centroid_context
               + total_progression + first_action_start_x + duration_seconds
```

Reference: PP in T1. One model only; no three-action or secondary-geometry motif interactions.

{effect_table(motif_terms, ["term", "model_N", "model_matches"])}

Adjusted within-context contrasts below are derived from that same model and its full
clustered covariance; PC/CP/CC compare with PP, while PC_vs_CP compares action order.

{effect_table(motif_contrasts, ["context", "motif"])}

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

{effect_table(sensitivity, ["action_type", "scope", "horizon", "N"])}

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

**{DECISION}**

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
.venv\\Scripts\\python.exe scripts/defensive_context_analysis.py
.venv\\Scripts\\python.exe -m ruff check .
.venv\\Scripts\\python.exe -m pytest -q
```

Next authorized step: **Phase 6B — Final Tactical Synthesis and Research Report**.
Phase 6B is not started here.
"""

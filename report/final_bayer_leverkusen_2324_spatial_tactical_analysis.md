# Bayer Leverkusen 2023/24: progression, visible spatial structure and attacking danger

**Final research synthesis · Phase 6B · PROJECT ANALYSIS COMPLETE**

This report synthesizes the frozen project results. No new models, outcome definitions,
thresholds or tactical classifications were introduced. Numerical estimates are rounded
from the canonical artifacts; the [technical appendix](final_bayer_leverkusen_2324_technical_appendix.md)
provides cohorts, definitions, cut points, robustness and a source map.

## 1. Executive Summary

**How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24 Bundesliga
season, and which recurring attacking sequences were most effective against different
defensive structures?** This study answers the observable part of that question using
StatsBomb events and 360 frames from all 34 league matches. The frames show a partial set
of visible players at events; they do not provide tracking or complete defensive shape.

The analysis follows hard-bounded attacking control spells, trusted spatial observations,
and fixed short Pass/Carry windows. Its principal findings are:

1. **Forward progression had a consistent longitudinal spatial association.** Greater
   progression was associated with a deeper next-observed visible opponent centroid.
   Spearman correlations were 0.622 for Pass and 0.648 for Carry. Carry's descriptive
   slope was substantially steeper: 0.831 versus 0.349 centroid x-units per progression
   x-unit. This measures differences between visible point clouds, not defender retreat.
2. **Centroid displacement carried danger information beyond progression.** Adjusted
   10-second box-entry odds ratios per additional action-specific standard deviation
   of opponent-centroid displacement were **1.214 [1.141, 1.292] for Pass** and
   **1.287 [1.188, 1.394] for Carry**, controlling for progression, starting x and
   observation gap. The association persisted across the main robustness checks.
3. **Spatial differences between motifs did not establish effectiveness differences.**
   CC retained a positive progression-adjusted centroid contrast against PP, but its
   higher raw box-entry rate did not translate into a clear adjusted danger advantage.
   Spatial displacement and attacking effectiveness are distinct outcomes.
4. **No uniquely superior short Pass/Carry motif was established.** CC led the raw
   two-action box-entry rates at 12.10%; PCC led the three-action rates at 12.73%.
   Adjusted contrasts were uncertain, PC versus CP showed no clear order advantage,
   and motif identity added negligible overall danger-model fit.
5. **Defensive-context moderation was limited and sensitive to observation gap.**
   Full-sample starting-centroid interactions were uncertain. At gaps of at most
   three seconds, displacement had a weaker danger association when the starting
   visible centroid was relatively deep. The wide-versus-narrow visible-structure
   interaction for Pass was tentative; depth and spacing moderation were uncertain.

**Direct answer.** The most consistent observed pattern linked forward progression,
especially Carry progression, with longitudinal differences in the visible opponent
structure; those differences were associated with near-term box-entry danger beyond
progression alone. The evidence supports this general spatial relationship more strongly
than a preferred short action sequence or a context-specific motif prescription.

“Danger” here primarily means a recorded box entry in the same locked control spell.
The main outcome window begins **at** the TO observation, so it can include danger at
that anchor. The positive association also survives excluding immediate box entries.
Shot/xG evidence is secondary: only 110 qualifying Shots remain under the locked
membership convention, which excludes many terminal-boundary Shots. The study cannot
establish how particular players physically created space or why the team went unbeaten.

## 2. Research Question and Scope

The football question concerns Bayer Leverkusen's 2023/24 Bundesliga attacking play.
Its operational form is:

> How did Leverkusen's attacking sequences alter the event-aligned visible spatial
> structure around possession, and which recurring structural changes preceded
> dangerous attacking outcomes?

“Alter” is evaluated through differences between observations, with no causal claim.
“Defensive structure” means the observed geometry of visible opponents. “Sequence” means
a fixed window inside a control spell unless stated otherwise. These definitions allow
useful football interpretation while keeping the answer within the data's resolution.

All analytical evidence comes from this project's frozen results. There is no comparison
club, another season, external tactical narrative or explanation of championship success.

## 3. Data and Methodology

### Source and observation model

The source is StatsBomb Open Data plus 360: competition **9**, season **281**, team
**904**, **34 matches**, pinned to revision
`533862946a73608c134d18b78226b6371ce7173c`. The source audit reconciled 137,765 events
and 118,581 uniquely linked frames. Pinning resolves the observed revision mismatch
between event IDs and 360 UUIDs; it does not heuristically repair links.

360 supplies an event-aligned partial observation of visible players and a visible-area
polygon. Ordinary off-ball players are anonymous. The set of observed players can change
between frames even when the count is unchanged. A mathematically available metric is
therefore not evidence of full-team coverage.

Team/orientation mapping is restricted to the locked Phase 2C semantic gates. In that
scope, Leverkusen attacks toward increasing x on the provider's 120 × 80 grid; positive
opponent-centroid x-change is farther toward the opponent's own goal. Raw coordinates
remain preserved. Coordinate units are not metres.

### Geometry and eligibility

Primary geometry uses visible records explicitly identified as non-goalkeepers:
centroid, lateral width, longitudinal depth, and pairwise/nearest-neighbor spacing.
The observed convex-hull footprint is secondary and observation-sensitive. Formulas,
metric-specific availability and support flags follow the locked Phase 2B contract;
there is no universal player-count cutoff, deduplication or coordinate repair.
Whole-frame out-of-bounds and coincidence exclusions are sensitivity checks.

### From provider possession to analytical windows

```text
StatsBomb provider possession
  → hard-bounded attacking control spell
  → trusted spatial anchors
  → observed spatial change
  → same-spell danger outcomes
```

Provider possession groups can contain interruptions or opponent control. The full event
stream therefore defines spells bounded by corroborated control changes, ball out,
stoppages and qualifying terminal Shots. Recycling or retreat does not create a new
spell. A spell is a data unit, not a natural tactical sequence.

Trusted anchors attach only after spell construction. A single-action observation pairs
an eligible Leverkusen FROM Pass/Carry with its existing next trusted TO anchor in the
same spell. Progression is the recorded action endpoint x minus start x; spatial change
is geometry(TO) minus geometry(FROM). Failed/unknown Pass endpoints and inherited
restart/relocation exclusions remain excluded. Signed backward and zero progression
remain eligible. No anchor is skipped to obtain a preferred response.

Fixed two-action windows require three consecutive trusted anchors; three-action windows
require four. Each action leg must already be Phase 4A eligible. P denotes Pass and C
Carry. These overlapping windows summarize action composition and order; they do not
identify complete attacks. Direction profiles are separate descriptive codes.

### Outcomes and temporal ordering

- **Box entry:** a completed Leverkusen Pass or Carry with valid on-pitch endpoints,
  beginning outside and ending inside `x ≥ 102, 18 ≤ y ≤ 62`; edges are inclusive.
- **Shot:** a Leverkusen Shot with the same locked control-spell membership.
- **Future xG:** sum of provider Shot xG over eligible events. No Shot means zero;
  missing provider xG would remain missing. There is no composite danger score.

Ten seconds is primary; five and fifteen seconds are sensitivities. Outcomes use the
full event stream, including events without a spatial frame, in source order and within
the same spell. The interval includes the reference event and the horizon endpoint;
action duration is not added to event time. Spell termination censors the search.

For single actions, context is measured at FROM, response is TO minus FROM, and outcomes
start at TO. For motifs, context is at START, response is terminal minus START, and
outcomes start at the terminal anchor. Thus temporal alignment is preserved, but an
inclusive outcome may coincide with the final spatial observation. Immediate-outcome
exclusion checks address that distinction separately.

### Statistical summaries

Pass and Carry are analyzed separately. Phase 4 uses descriptive rank correlations and
linear models. Phase 5 uses unpenalized logistic models with the prescribed progression,
location and timing controls. Phase 6A adds one starting-context dimension and its
centroid-displacement interaction at a time. Confidence intervals use match-clustered
CR1 covariance and t intervals with 33 degrees of freedom. Odds ratios describe odds,
not equal percentage changes in probability. These are explanatory associations within
the observed sample, not out-of-sample predictive validation or causal effects.

## 4. Methodological Validation

| Milestone | Frozen validation result |
|---|---|
| Source compatibility | One pinned revision; 34 matches; no orphan frames or duplicate event/frame IDs |
| Phase 2C semantics | 72,596 validated frames across the season; 45,985 linked frames outside the supported scope |
| Hard boundaries | 27/27 scored hard targets accepted: 24 exact onsets and three accepted paired-context timing differences |
| Control spells | 3,202 spells from 2,888 Leverkusen provider-possession parents |
| Trusted sequences | 43,737 anchors and 40,638 within-spell transitions; 3,099 spells have anchors, 103 do not |
| Opponent metric availability | Centroid/width/depth: 43,732/43,737 anchors; NN spacing: 43,681/43,737 |
| Outcome reconciliation | 43,737/43,737 anchor outcome rows; 833 box-entry events and 110 qualifying Shots |
| xG completeness | 110/110 qualifying Shots have provider xG; zero missing |

The hard-boundary review was purposive and partly ambiguous, so acceptance is not an
estimate of season-wide detection accuracy. Near-complete metric availability applies
to the trusted sample and does not imply nearly complete football visibility.

Soft-reset experiments supplied useful negative validation. Versions v0.1, v0.2 and
v0.3 respectively had **3/9, 3/9 and 7/9 exact matches**, with **4, 4 and 1 missed resets**
and **17, 13 and 11 extra splits**. Despite improvement, false fragmentation remained
material. Soft resets were retained as descriptive within-spell phenomena and excluded
from production boundaries. The appendix preserves the replay table and its source.

At the 10s anchor horizon, 4,672 anchors had a box entry and 650 had a Shot:
prevalences **10.682031%** and **1.486156%**, with mean future xG **0.00139921**.
These reference rows can share the same future event; they are not unique-event counts.
Sources: [Phase 3A](phase3a_control_spell_segmentation.md),
[Phase 3B](phase3b_spatial_sequence_construction.md), and
[Phase 5A](phase5a_danger_outcome_design.md).

## 5. Single-Action Spatial Mechanisms

Greater forward progression was consistently associated with a deeper next-observed
visible opponent centroid. This was the clearest Phase 4A relationship.

| Action | Available N | Spearman rho | Centroid-x slope | Match-clustered 95% CI | R² |
|---|---:|---:|---:|---|---:|
| Pass | 14,845 | 0.621912 | 0.349024 | [0.329627, 0.368420] | 0.422234 |
| Carry | 15,525 | 0.647793 | 0.831274 | [0.797721, 0.864828] | 0.604149 |

The slope is the fitted centroid x-difference per progression x-unit. Carry's steeper
relationship is descriptive: Pass and Carry differ in progression distributions,
observation gaps and surrounding events. It is not a controlled estimate of replacing
a Pass with a Carry. Positive within-match rank associations occur in all 34 matches
for each action. Gap restrictions attenuate slope magnitudes while retaining direction.

![Figure 1. Pass progression and observed opponent-centroid change](../outputs/figures/phase4a_pass_centroid.png)

*Figure 1. Existing Phase 4A plot. Decile medians and response IQR summarize partial
observations; the band is not a confidence interval or a tracked movement envelope.*

![Figure 2. Carry progression and observed opponent-centroid change](../outputs/figures/phase4a_carry_centroid.png)

*Figure 2. Existing Phase 4A plot. The axes differ from Figure 1; use the numerical
slopes above for comparison rather than the visual angle of the lines.*

Pass also showed a modest positive opponent-width association (rho **0.169128**, slope
**0.077325**); Carry width was near null (rho **−0.005945**). Carry nearest-neighbor
spacing was weakly negative (rho **−0.144585**, slope **−0.048945**) and weakened at
shorter gaps. Pass's pairwise and nearest-neighbor summaries did not share one direction.
These secondary results do not support a general claim of team expansion or compactness.
[Source: Phase 4A](phase4a_progression_linked_spatial_change.md).

## 6. Multi-Action Spatial Patterns

The fixed-window inventory contains **24,273 two-action** and **19,651 three-action**
windows. PC (**11,800**) and CP (**10,679**) dominate two-action support; CPC (**8,588**)
and PCP (**8,365**) dominate three-action support. Frequencies reflect both play and the
provider action/anchor representation, not tactical intent.

CC had the largest two-action median opponent-centroid change, **+5.234** x-units.
Among better-supported three-action motifs, PCC (**+6.650**) and CCP (**+6.124**) had
large medians. CCC was numerically larger but had only **17 windows in 12 matches**;
it does not support a general football claim.

![Figure 3. Two-action observed spatial changes](../outputs/figures/phase4b_2_action_centroid.png)

*Figure 3. Frozen Phase 4B median and IQR plot. Raw spatial change is distinct from
adjusted spatial change and from subsequent danger.*

After progression adjustment, CC retained a **+2.986 [1.902, 4.070]** centroid x-unit
contrast against PP. PC and CP retained negative contrasts against PP. Progression-only
R² was **0.5358** for two-action and **0.5950** for three-action windows; adding motifs
raised it to **0.5412** and **0.5992**. Some composition-related spatial differences
therefore remain, but the extra overall model fit is small. No simple “more Carries,
more displacement” rule holds across motifs. Raw medians and adjusted mean contrasts
answer different questions. The appropriate conclusion remains **mixed sequence signal**.
[Source: Phase 4B](phase4b_multi_action_spatial_sequences.md).

## 7. Spatial Change and Danger

### Centroid displacement retained information beyond forward ball movement

The Phase 5B models ask whether observed centroid displacement is associated with
10s box entry after accounting for the action's progression, starting x and observation
gap. This advances beyond the descriptive progression relationship: the spatial term
retains an association conditional on those controls.

| Action | Model N | Positive reference rows | Unadjusted OR per +1 SD | Adjusted OR per +1 SD [95% CI] |
|---|---:|---:|---:|---|
| Pass | 14,845 | 1,530 | 1.316 | **1.214 [1.141, 1.292]** |
| Carry | 15,525 | 1,680 | 1.268 | **1.287 [1.188, 1.394]** |

SDs are **6.273044** centroid x-units for Pass and **7.132492** for Carry. Pass attenuates
after adjustment; Carry remains similar. Different action-specific SDs and separate
models preclude treating the OR difference as a formal Pass-versus-Carry test.

![Figure 4. Observed box-entry prevalence across centroid-change quartiles](../outputs/figures/phase5b_centroid_quartiles.png)

*Figure 4. Frozen unadjusted rates, using action-specific displacement quartiles.
Pass rises from 6.52% to 15.41%; Carry from 7.70% to 14.04%. These are observed
prevalences, not adjusted probabilities or tactical cutoffs.*

![Figure 5. Adjusted centroid-displacement associations with box entry](../outputs/figures/phase5b_adjusted_centroid.png)

*Figure 5. Frozen Phase 5B estimates with match-clustered 95% intervals. The reported
association includes information beyond the specified progression/location/gap controls.*

### Robustness and the meaning of “subsequent”

The positive box-entry association survives 5/15s horizons, ≤5/≤3s gap restrictions,
visible-count adjustment, and whole-frame OOB/coincidence exclusions. Magnitudes change:
shorter gaps strengthen the Pass estimate and attenuate Carry's estimate.

Because the primary window includes TO, the transition may culminate at an immediate
box entry. Excluding those reference rows attenuates the ORs to **1.144 [1.077, 1.216]**
for Pass and **1.190 [1.094, 1.295]** for Carry. This is the stronger basis for saying
the spatial association also extends to danger developing afterward. It remains an
association in a selected subset, not evidence that centroid displacement caused entry.

### Secondary geometry, Shot and xG

Pass depth-change OR was **0.918 [0.866, 0.974]**, and width-change OR was
**0.921 [0.874, 0.971]**, per metric-specific SD. These modest negative extent
associations do not support “more widening always means more danger.” They also differ
from the positive progression–width relationship in Section 5: the predictors, outcomes
and conditioning are different. NN-spacing danger associations were inconclusive.

Centroid-displacement Shot ORs were positive: **1.594 [1.345, 1.891]** for Pass and
**1.403 [1.161, 1.695]** for Carry. Shot support is sparse and repeatedly shared across
reference rows. At ≤3s the Pass interval includes 1. Future xG increases descriptively
across centroid-change quartiles, without an adjusted xG claim. Neither result has the
same evidentiary weight as box entry. The underlying 110 qualifying Shots exclude many
terminal attempts under the locked spell-membership rule.
[Source: Phase 5B](phase5b_spatial_change_to_danger.md).

## 8. Sequence Effectiveness

**Motif effectiveness was mostly explained by progression and context in the specified
models.** Here context means starting location and sequence duration; explicit starting
opponent geometry is introduced separately in Section 9.

### Two-action raw rates and adjusted comparisons

| Motif | Windows | Positive box-entry rows | Raw 10s box-entry rate | Adjusted OR versus PP [95% CI] |
|---|---:|---:|---:|---|
| PP | 1,232 | 119 | 9.66% | 1 (reference) |
| PC | 11,800 | 1,259 | 10.67% | 1.003 [0.844, 1.194] |
| CP | 10,679 | 1,119 | 10.48% | 0.983 [0.825, 1.171] |
| CC | 562 | 68 | 12.10% | 1.109 [0.768, 1.601] |

The adjusted model contains motif, total progression, first-action start x and duration.
CC leads the raw rates, but its interval permits differences in either direction.
PC versus CP is **1.021 [0.967, 1.078]**: no clear order advantage. Adding motif identity
increases McFadden pseudo-R² by only **0.000051** beyond the three controls.

![Figure 6. Adjusted two-action motif effectiveness](../outputs/figures/phase5c_two_action_adjusted_or.png)

*Figure 6. Frozen Phase 5C comparisons. All non-reference intervals cross 1. PP at 1
is a fixed reference, not an estimated certainty about its effectiveness.*

Adding net opponent-centroid displacement moves CC's OR from **1.109** to
**1.064 [0.730, 1.551]**. The small positive point estimate overlaps with CC's observed
spatial signature; six missing-centroid exclusions also change the model population.
This comparison is descriptive and is **not formal mediation**. Neither model establishes
an independent CC advantage. Across the prescribed two-action sensitivities, CC versus
PP and PC versus CP intervals continue to include 1.

### Three-action windows

PCC has the highest raw 10s rate, **12.73%** (49/385 windows), but its adjusted OR versus
PPP is **0.915 [0.424, 1.974]**. No adjusted three-action contrast against PPP excludes 1.
Motif identity adds only **0.000278** McFadden pseudo-R². PPP itself has 121 windows and
15 positives; CCC has 17 windows and one positive, making some comparisons particularly
imprecise. These findings neither establish equivalent motifs nor identify a winner.
[Source: Phase 5C](phase5c_sequence_effectiveness.md).

## 9. Defensive Context

Starting context is measured **before** the action or window: FROM for single actions,
START for two-action motifs. Separate tertiles of visible opponent centroid x, width,
depth and NN spacing are calculated within action-start thirds [0,40), [40,80), [80,120].
Cuts are shared across Pass and Carry, use no outcomes, and remain fixed for motifs and
sensitivities. They describe relative visible geometry, not formations or defensive blocks.

### Starting visible-centroid depth

In the primary full sample, deep-versus-advanced visible-centroid interaction ORs are
**0.919 [0.819, 1.031] for Pass** and **0.958 [0.848, 1.083] for Carry**. Neither clearly
distinguishes the displacement–danger slope between those contexts. Carry's within-context
displacement associations remain positive; Pass's deepest-context estimate is weaker
and uncertain. A clear result in one subgroup and an uncertain result in another does
not itself demonstrate moderation.

At gaps **≤3s**, the interaction ORs are **0.714 [0.599, 0.851] for Pass** and
**0.667 [0.525, 0.847] for Carry**. These are ratios of displacement ORs across contexts,
not direct deep-context outcome odds or probability ratios. Under tighter temporal
observation, additional centroid displacement has a weaker danger association when the
starting visible centroid is already relatively deep. The finding also appears at ≤5s,
but its full-sample uncertainty makes the gap qualification essential. Nested gap subsets
change action composition and are not independent replications.

### Other visible geometry and motifs

Pass's wide-versus-narrow starting visible-width interaction is **1.134 [1.007, 1.278]**.
Its lower bound is only just above 1 among several exploratory comparisons, and no
secondary robustness family was fitted. It is tentative. Starting longitudinal extent
and spacing moderation remain uncertain; a context main effect is not evidence of a
different displacement slope.

![Figure 7. Full-sample starting-context interactions](../outputs/figures/phase6a_interaction_effects.png)

*Figure 7. Frozen Phase 6A full-sample 10s results. T1/T2/T3 increase the specified
dimension within starting third. This figure does not display the short-gap results
quoted above; those are tabulated in the appendix.*

The single two-action motif-by-starting-centroid model establishes no clear context-specific
motif advantage. CC cells have only 163–230 windows and 21–24 positives. Conditioning on
visible starting geometry therefore supplies no convincing reason to overturn Phase 5C's
conclusion. No claim about success against a “low block” follows from these bins.
[Source: Phase 6A](phase6a_defensive_context_analysis.md).

## 10. Integrated Tactical Interpretation

The evidence is most coherent as a relationship between **progression, observed longitudinal
structure and danger**. Progression describes the recorded ball action. Centroid change
describes the difference between visible opponent point clouds. Box entry describes a
later or coincident recorded outcome. Their association is informative, but none can
substitute for a measurement of individual defender movement or free space.

Carry progression has a particularly strong descriptive longitudinal spatial relationship.
Yet that does not imply an extra Carry reliably improves an attack: CC's residual spatial
contrast coexists with an uncertain adjusted box-entry contrast. A motif can have a
recognizable spatial signature without a demonstrated independent effectiveness advantage.

Similarly, the common PC/CP and CPC/PCP windows establish recurring recorded action
patterns, but frequency is not evidence of superiority. Their contribution is to describe
how attacks are represented locally. Progression, location and timing account for much
of the danger variation that a motif label alone might appear to explain.

**Tactical hypotheses, separated from observed evidence:** an already deeper visible
opponent structure may leave less longitudinal room for a further centroid shift; wider
starting observations may coincide with Pass situations in which longitudinal
reorganization is more informative about danger. These are plausible interpretations,
not evidence of deliberate exploitation, tactical intent or a recognized defensive system.
Changing frame composition and the shared FROM term in context and displacement offer
observational explanations as well.

### Final evidence table

Strength labels describe evidentiary confidence **within this study**, not football
importance, causal certainty or a numerical score.

| Finding | Evidence | Robustness | Interpretation strength |
|---|---|---|---|
| Progression ↔ visible opponent-centroid displacement | Pass rho 0.622; Carry 0.648 | Positive in every match; direction persists under gap/support checks; magnitude varies | **Strong** |
| Centroid displacement ↔ near-term box entry | Adjusted OR 1.214 Pass; 1.287 Carry | Positive across primary horizon, gap, immediate-entry and support sensitivities | **Strong** |
| Carry has a steeper descriptive longitudinal relationship | Slope 0.831 versus 0.349 for Pass | Persists directionally across contexts; separate samples and timing prevent an intervention comparison | **Moderate** |
| CC has a residual spatial signature | Adjusted centroid contrast +2.986 versus PP | Positive but gap-sensitive; sparse relative to PC/CP | **Moderate** |
| Pass progression ↔ visible width | rho 0.169; modest positive slope | Weaker than centroid and context-dependent; no general expansion claim | **Tentative** |
| Starting visible-centroid depth moderates danger | Deep-versus-advanced interaction below 1 at ≤3s for both actions | Full sample uncertain; gap subsets change composition | **Tentative** |
| Wide starting visible structure moderates Pass | Interaction OR 1.134 [1.007, 1.278] | Exploratory comparison, close to 1; no secondary robustness family | **Tentative** |
| Independent motif effectiveness / PC-versus-CP superiority | Adjusted contrasts uncertain; negligible added fit | Main two-action null conclusion survives prescribed checks | **Not established** |
| Universal context-specific motif advantage | No clear two-action motif/context contrast | Sparse CC cells and wide intervals | **Not established** |

## 11. What the Study Does NOT Establish

The study does not establish causality, exact defender trajectories, formation recognition,
low/mid/high block labels, true defensive-line height, complete team compactness, pitch
control, named off-ball player movements, tactical intent, or universal superiority of
CC or any other motif. A positive centroid delta is not a measured defensive-line retreat.
A higher raw outcome rate is not an adjusted or causal effectiveness advantage. The
study also does not establish motif equivalence or an explanation of the unbeaten season.

## 12. Limitations

- **Partial 360 coverage:** visible areas and player counts vary, and observed player
  identities may change. Geometry can shift because the observed sample changes.
- **Event timing and gaps:** the next trusted anchor need not coincide with action
  completion. Intervening events, composition and observation delay affect magnitudes.
- **Anonymous off-ball players:** the analysis cannot attribute differences to named
  movements or separate individual tactical roles.
- **Selection:** restricted semantic trust and inherited action eligibility define a
  subset of football activity. Near-complete metrics within that subset do not remove bias.
- **Repeated observations:** overlapping windows share actions and future events.
  Match clustering addresses within-match dependence in model uncertainty, not causality.
- **Sparse and censored Shot/xG:** 505 Leverkusen Shots in the provider-possession context
  lack spell membership, including 502 terminal-Shot boundaries. The 110 qualifying
  Shots do not represent all attack-ending attempts. xG completeness within that set
  does not remedy its restricted coverage.
- **Relative context:** within-third tertiles and linear start-x adjustment leave
  residual field-position confounding. FROM centroid also enters displacement with a
  minus sign; mathematical coupling and regression to the mean can contribute to patterns.
- **Model uncertainty:** simple observational controls cannot remove all confounding.
  Interactions and rare motifs are noisy, and exploratory comparisons are not corrected
  for multiplicity. Statistical non-detection is not proof of no football difference.
- **Generalization:** this is one team in one season with 34 match clusters. Its
  associations are not universal tactical laws or externally validated predictions.

## 13. Conclusions

**How did Leverkusen create dangerous space?** The strongest supported answer is that
forward progression was associated with longitudinal displacement of the visible
opponent structure, and that displacement retained an association with near-term box
entry beyond progression, starting position and observation gap. Carry progression
showed the steeper descriptive spatial relationship. Modest Pass widening was secondary.
These are advantageous observed spatial conditions associated with danger; the data
does not measure physical space creation or establish the actions that caused it.

**Which recurring sequences were most effective?** CC and PCC led the raw two- and
three-action box-entry rates, respectively, but the data did not establish a uniquely
superior short Pass/Carry motif after adjustment. PC versus CP showed no clear order
advantage. Motif identity added little danger-model fit beyond progression, location
and duration, despite some residual motif-related spatial differences.

**Against different defensive structures?** The answer is limited to relative visible
starting geometry. Short-gap observations suggest a weaker displacement–danger
relationship when the visible centroid is already deeper; full-sample moderation is
uncertain. The Pass width-context finding is tentative, and no reliable context-specific
motif advantage emerges. This does not identify low blocks, formations or tactical intent.

The project's contribution is an observation-aware account of the relationship between
progression, visible longitudinal structure and danger, together with a substantive
negative finding about short motif superiority. **PROJECT ANALYSIS COMPLETE.** Future
replication with another season or tracking data would be an optional extension, not
a required continuation of this study.

# Technical appendix: Bayer Leverkusen 2023/24 spatial analysis

**PROJECT ANALYSIS COMPLETE · Phase 6B**

Companion to the [final research report](final_bayer_leverkusen_2324_spatial_tactical_analysis.md).
This appendix reads the frozen findings; it does not change their methods or rerun
their models. Exact machine-readable estimates remain in the canonical CSVs. Display
rounding is explicit; context boundaries below retain round-trip precision.

## A. Provenance, phase inventory and evidence map

The immutable StatsBomb source revision is
`533862946a73608c134d18b78226b6371ce7173c`, configured in
[`config/project.yaml`](../config/project.yaml). Competition 9, season 281, team 904,
34 Bundesliga matches. Source/observation provenance and earlier source references
are retained in the [source foundation](../docs/source_foundation.md) and
[methods specification](../docs/methods_specification.md). No external football
commentary or new source retrieval informs the synthesis.

| Phase | Final disposition | Canonical reference |
|---|---|---|
| 1/1B | Source and observability audit complete | [Methods §32](../docs/methods_specification.md#32-completed-phase-11b-contract-and-findings) |
| 2A | Geometry definitions locked and implemented | [Metric registry](../docs/metric_registry.md) |
| 2B | Eligibility/support locked | [Calibration matrix](../docs/phase2b3_metric_calibration_matrix.csv); [methods §37](../docs/methods_specification.md#37-human-approved-phase-2b-lock-and-operational-research-scope) |
| 2C | Locked restricted semantic scope | [Methods §40](../docs/methods_specification.md#40-human-approved-phase-2c-restricted-semantic-scope-lock) |
| 3A | LOCKED / COMPLETE | [Control-spell report](phase3a_control_spell_segmentation.md) |
| 3B | READY WITH ANALYSIS-SPECIFIC SUPPORT REQUIREMENTS | [Spatial-sequence report](phase3b_spatial_sequence_construction.md) |
| 4A | COMPLETE / STABLE SINGLE-ACTION SPATIAL RELATIONSHIPS IDENTIFIED | [Progression report](phase4a_progression_linked_spatial_change.md) |
| 4B | COMPLETE / MIXED SEQUENCE SIGNAL | [Multi-action report](phase4b_multi_action_spatial_sequences.md) |
| 5A | LOCKED / OUTCOME LAYER COMPLETE | [Outcome report](phase5a_danger_outcome_design.md) |
| 5B | COMPLETE / ROBUST SPATIAL-DANGER ASSOCIATIONS IDENTIFIED | [Spatial-danger report](phase5b_spatial_change_to_danger.md) |
| 5C | COMPLETE / MOTIF EFFECTIVENESS MOSTLY EXPLAINED BY PROGRESSION AND CONTEXT | [Effectiveness report](phase5c_sequence_effectiveness.md) |
| 6A | COMPLETE / LIMITED DEFENSIVE-CONTEXT MODERATION | [Defensive-context report](phase6a_defensive_context_analysis.md) |
| 6B | Final synthesis complete | [Final report](final_bayer_leverkusen_2324_spatial_tactical_analysis.md) |

Earlier reports retain their historical next-step language. This closing status
supersedes those scheduling statements without revising the underlying analytical decisions.

### Numerical source map

Paths below are relative to the repository root; analysis tables are under
`outputs/analysis/` and are ignored generated artifacts in the existing project workflow.

| Final report claim | Canonical table / selection |
|---|---|
| Single-action N, rho, slope, CI and R² | `phase4a_metric_summary.csv`, action and `response_metric`, scope `all` |
| Motif frequency and raw spatial medians | `phase4b_motif_summary.csv`; Phase 4B report §C |
| Adjusted spatial motif contrasts and model fit | `phase4b_centroid_adjusted_summary.csv`, scope `all`, named model/term |
| Outcome counts/prevalence and exclusion coverage | Phase 5A report §§C–E; `phase5a_anchor_outcomes.csv`, `phase5a_outcome_events.csv` |
| Spatial-danger ORs and descriptive quartiles | `phase5b_spatial_danger_summary.csv`, model/quartile record, action, metric and outcome |
| Spatial-danger robustness | `phase5b_sensitivity_summary.csv`, centroid model, outcome, scope and horizon |
| Raw/adjusted motif danger and added fit | `phase5c_motif_effectiveness_summary.csv`, length, motif, outcome and record type |
| Motif robustness / centroid addition | `phase5c_sensitivity_summary.csv`, named scope and contrast |
| Starting-context support and cuts | `phase6a_context_summary.csv`, context/cutpoints records |
| Context moderation and robustness | `phase6a_context_interactions.csv`, coefficient records, action, dimension, horizon, scope and term |
| Motif/context support and comparisons | `phase6a_motif_context_summary.csv`, raw/coefficient/contrast records |

The final main tables distinguish raw rates, descriptive spatial slopes, adjusted
mean contrasts and adjusted danger ORs. These should not be combined into one effect
scale. The seven figures are linked in place from the frozen `outputs/figures/` set;
no figure was regenerated. Their legends govern their colors independently, and their
captions distinguish IQRs from confidence intervals.

## B. Cohorts and denominators

| Layer | Count | Meaning |
|---|---:|---|
| Full-season events | 137,765 | Pinned complete event stream |
| Uniquely linked 360 frames | 118,581 | Event-aligned observations, not tracking samples |
| Validated semantic frames, full season | 72,596 | Frames satisfying the locked gates |
| Unsupported linked frames | 45,985 | Not assigned operational team/orientation semantics |
| Leverkusen provider parents | 2,888 | Provider possession groups, not control spells |
| Full-stream events in those parents | 86,025 | Context includes unsupported and opponent events |
| Validated anchors before spell attachment | 46,143 | Phase 2C provider-context population |
| Context anchors outside locked spell membership | 2,406 | Reconciled exclusions, not missing joins |
| Attacking control spells | 3,202 | Includes 103 zero-anchor spells |
| Spells with trusted anchors | 3,099 | All 34 matches represented |
| Trusted spatial anchors / outcome rows | 43,737 / 43,737 | Exact outcome-layer reconciliation |
| Within-spell transitions | 40,638 | Consecutive trusted anchors |
| Eligible single-action transitions | 30,375 | 14,848 Pass; 15,527 Carry |
| Available single-action opponent-centroid pairs | 30,370 | 14,845 Pass; 15,525 Carry |
| Two-action windows | 24,273 | 24,267 with endpoint-centroid support |
| Three-action windows | 19,651 | 19,646 with endpoint-centroid support |
| Phase 6A centroid-context motif model | 24,270 | Two-action windows with starting context; different support requirement from endpoint displacement |
| Qualifying box-entry / Shot events | 833 / 110 | Unique underlying outcome events in the retained layer |
| Qualifying Shots with provider xG | 110 / 110 | No missing qualifying Shot xG |

For 10s outcomes over all 43,737 anchors: 4,672 positive box-entry rows, 650 positive
Shot rows, and mean future xG 0.00139921. Reference rows can point to the same event.
Do not add event counts and positive-anchor counts or treat overlapping windows as
independent attacks. Phase 4A's complete centroid sample also supplies the primary
Phase 5B and Phase 6A centroid models; this coincidence of N does not make their
specifications identical.

## C. Definitions and frozen model specifications

### Observed geometry

- **Centroid:** arithmetic mean of selected visible point coordinates.
- **Width:** maximum y minus minimum y of selected points.
- **Depth:** maximum x minus minimum x; distinct from centroid x-position.
- **Pairwise spacing:** mean/median Euclidean distance over unordered distinct record pairs.
- **Nearest-neighbor spacing:** mean of each selected record's nearest-other-record distance.
- **Hull:** convex-hull area of the observed footprint, secondary; not occupied or controlled area.

All use provider coordinate units (squared units for area). Keeper-excluded measurements
retain only literal `keeper=False`; unidentified flags do not become outfield players
by assumption. Records are not deduplicated. Primary eligibility requires the metric's
existing `ok` status and actor status `single` or `none`, with inherited semantic gates.
Support, visible area and whole-frame anomalies remain available for interpretation.
The existing whole-frame OOB/coincidence sensitivity rules also exclude unknown flags.

### Progression, windows and inference

Single-action progression is the explicit provider endpoint x minus start x, not an
inter-anchor ball-location jump. Net window progression sums eligible action vectors;
net spatial change is final minus initial geometry. Pressure may be an eligible spatial
anchor but does not become a Leverkusen progression action. Window boundaries use
consecutive anchors, while intervening full-stream context remains available.

| Phase | Response and principal specification |
|---|---|
| 4A | Each spatial delta ~ intercept + action progression; Pass/Carry separate; Spearman primary descriptive association |
| 4B | Net opponent-centroid x ~ progression + motif, separately for length 2/3; first start x added only in the specified supplementary model |
| 5B | Box entry ~ one spatial delta + action progression + start x + anchor gap; centroid-only Shot models |
| 5C | Box entry ~ motif + total progression + first start x + duration; one two-action extension adds net opponent-centroid x |
| 6A | Box entry ~ centroid delta + starting context + delta × context + progression + start x + gap; one context dimension at a time and separate actions |
| 6A motifs | Box entry ~ motif + starting-centroid context + motif × context + total progression + first start x + duration; length 2 only |

OLS and logistic coefficient covariance uses match-clustered CR1:
`G/(G−1) × (N−1)/(N−K)`, with K including the intercept, and t(G−1) intervals.
The full supported models have G=34. Phase 5/6A use unpenalized logistic MLE.
Fixed full-action sample SDs standardize reported centroid ORs across sensitivity
subsets: Pass 6.273044 and Carry 7.132492. Context interactions are ratios of those
ORs relative to T1. A context main effect is evaluated at zero displacement in
Phase 6A; it is not itself slope moderation.

No p-value optimization, feature selection, clustering, pitch-control estimate,
formation model, xT, EPV or causal mediation analysis is part of the completed study.

## D. Within-start-third context boundaries

Cuts are empirical 1/3 and 2/3 quantiles with linear interpolation, pooled across
Pass/Carry within each starting third. T1 ≤ lower; lower < T2 ≤ upper; T3 > upper.
Ties remain together. No outcomes enter cut calculation. Motifs and sensitivity
subsets inherit the same cuts. Raw geometry remains in the Phase 6A dataset.

Thirds are [0,40), [40,80), [80,120]. Increasing centroid T1/T2/T3 means advanced,
middle and deep **visible** centroid; width means narrow/medium/wide visible extent;
depth means shallow/medium/deep visible longitudinal extent; spacing means tight/
medium/loose visible NN spacing. Count is metadata, not a tactical category.

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

Centroid, width and depth each have three unavailable starts; spacing has 34.
The primary transition models also exclude two additional missing centroid responses.
Context binning reduces gross field-position conflation but does not establish
universal defensive states or remove all within-third confounding.

## E. Selected frozen robustness tables

### E1. Phase 5B adjusted centroid–box-entry OR per +1 SD

| action_type | scope | horizon | N | OR [95% CI] |
| --- | --- | --- | --- | --- |
| Pass | all | 10 | 14845 | 1.214 [1.141, 1.292] |
| Pass | gap_le_5 | 10 | 14419 | 1.286 [1.158, 1.429] |
| Pass | gap_le_3 | 10 | 13970 | 1.346 [1.203, 1.505] |
| Pass | exclude_immediate | 10 | 14647 | 1.144 [1.077, 1.216] |
| Pass | exclude_oob | 10 | 12300 | 1.255 [1.179, 1.336] |
| Pass | exclude_coincidence | 10 | 14832 | 1.214 [1.141, 1.292] |
| Pass | all | 5 | 14845 | 1.288 [1.192, 1.392] |
| Pass | all | 15 | 14845 | 1.142 [1.078, 1.211] |
| Pass | visible_count_adjustment | 10 | 14845 | 1.215 [1.144, 1.291] |
| Carry | all | 10 | 15525 | 1.287 [1.188, 1.394] |
| Carry | gap_le_5 | 10 | 14673 | 1.273 [1.154, 1.405] |
| Carry | gap_le_3 | 10 | 12962 | 1.202 [1.075, 1.344] |
| Carry | exclude_immediate | 10 | 15236 | 1.190 [1.094, 1.295] |
| Carry | exclude_oob | 10 | 13076 | 1.281 [1.187, 1.382] |
| Carry | exclude_coincidence | 10 | 15507 | 1.286 [1.187, 1.392] |
| Carry | all | 5 | 15525 | 1.433 [1.287, 1.595] |
| Carry | all | 15 | 15525 | 1.225 [1.134, 1.324] |
| Carry | visible_count_adjustment | 10 | 15525 | 1.287 [1.190, 1.392] |

The source table contains each action's complete-case N and cluster diagnostics.
The direction and intervals above 1 persist throughout these prescribed comparisons.
Immediate exclusion removes reference anchors already recording box entry. Visible-count
adjustment uses the existing Phase 5B support covariate; it is not a correction for
unobserved player identities. All comparisons remain observational.

### E2. Phase 6A deepest-versus-advanced visible-centroid interaction

| action_type | scope | horizon | N | OR [95% CI] |
| --- | --- | --- | --- | --- |
| Pass | all | 10 | 14845 | 0.919 [0.819, 1.031] |
| Pass | all | 5 | 14845 | 0.960 [0.817, 1.128] |
| Pass | all | 15 | 14845 | 0.884 [0.774, 1.010] |
| Pass | gap_le_5 | 10 | 14419 | 0.807 [0.724, 0.898] |
| Pass | gap_le_3 | 10 | 13970 | 0.714 [0.599, 0.851] |
| Pass | exclude_oob | 10 | 12300 | 0.878 [0.756, 1.019] |
| Pass | exclude_coincidence | 10 | 14832 | 0.923 [0.824, 1.033] |
| Pass | visible_count | 10 | 14845 | 0.918 [0.818, 1.030] |
| Carry | all | 10 | 15525 | 0.958 [0.848, 1.083] |
| Carry | all | 5 | 15525 | 0.885 [0.720, 1.088] |
| Carry | all | 15 | 15525 | 0.941 [0.839, 1.055] |
| Carry | gap_le_5 | 10 | 14673 | 0.826 [0.688, 0.991] |
| Carry | gap_le_3 | 10 | 12962 | 0.667 [0.525, 0.847] |
| Carry | exclude_oob | 10 | 13076 | 0.968 [0.837, 1.120] |
| Carry | exclude_coincidence | 10 | 15507 | 0.960 [0.850, 1.085] |
| Carry | visible_count | 10 | 15525 | 0.959 [0.848, 1.084] |

These are interaction ORs, not within-context displacement ORs. The full-sample
comparison is uncertain; short-gap comparisons are stronger. At ≤3s, the within-context
deep-visible-centroid displacement OR is 1.001 [0.850, 1.179] for Pass and
0.868 [0.702, 1.074] for Carry. The interaction therefore supports a relative weakening,
not a clearly negative displacement association in that context. Visible-count sensitivity
adds FROM visible count once per action. No secondary-context robustness family is implied.

### E3. Motif effectiveness checks

Phase 5C's CC:PP and PC:CP intervals include 1 at the primary horizon and throughout
5/15s, every-leg ≤5/≤3s, immediate-entry, OOB and coincidence sensitivities. Adding net
centroid also leaves both uncertain. Full numbers remain in the
[Phase 5C robustness table](phase5c_sequence_effectiveness.md#g-robustness).

Phase 6A's single motif/context model has no interaction or within-context motif contrast
whose interval excludes 1. Raw CC cells have N=230/169/163 and 23/24/21 positive windows
for advanced/middle/deep visible-centroid context. No category merging or new sparse-cell
threshold search was used. These results do not demonstrate motif equivalence.

## F. Hard-boundary and soft-reset validation history

The 27 scored hard targets comprise 24 exact onsets and three accepted paired-context
timing differences with matching football context/regains. No unaccepted scored hard-boundary
failure remains. Ambiguous/unreviewed material remains unscored. This is reviewed-case
validation rather than a representative season-wide error estimate.

| Historical soft-reset candidate | Exact reset matches | Missed resets | Extra splits |
|---|---:|---:|---:|
| v0.1 | 3/9 | 4 | 17 |
| v0.2 | 3/9 | 4 | 13 |
| v0.3 | 7/9 | 1 | 11 |

Exact matches, missed resets and extra splits are the historical replay categories;
the first two are not complementary partitions of nine. Timing/context classifications
also occur in the replay. Improved recall did not remove false fragmentation, so no
soft-reset rule feeds production segmentation. See the
[locked Phase 3A decision](phase3a_control_spell_segmentation.md#e-soft-reset-decision)
and [historical replay report](phase3a3_reset_rule_replay.md).

## G. Final assembly and preservation

Phase 6B contains two Markdown reports, a concise README completion update, and an
append-only closing section in the methods specification. The final report was authored
directly against canonical reports/CSVs; a persistent build framework was unnecessary.
Seven suitable existing PNGs were visually inspected and referenced without rewriting.

Final checks compare headline values with frozen summary rows, validate local report/
figure links and required sections, review interpretation language, run Ruff and inspect
ordinary git diff/status. No analytical or application code changed, so pytest and the
analytical pipeline need not run again. No historical artifact hashes are recomputed.
Earlier analytical reports, code, datasets and figures remain unchanged.

Validation completed: 49 selected numeric claims matched frozen CSV estimates at
their displayed precision; all 37 local report links/fragments resolved; the main
report contains the required 13 sections and seven reused figures, with an executive
summary below 650 words. Ruff and git whitespace checks passed. The methods change
is append-only; the working-tree changes are limited to the four intended Phase 6B
documentation files. No pytest or analytical pipeline rerun was performed.

**PROJECT ANALYSIS COMPLETE.** Optional extensions such as another club/season or
tracking-data replication are outside the completed scope; there is no required next phase.

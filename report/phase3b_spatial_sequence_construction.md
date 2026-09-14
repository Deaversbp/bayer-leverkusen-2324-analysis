# Phase 3B: spatial-state sequence construction

**PHASE 3B — CONSTRUCTION COMPLETE / READY FOR METHOD-SPECIFIC SPATIAL ANALYSIS**

## A. Purpose and locked inputs

Construct spell-level spatial observations from the full ordered event stream, the existing
`attacking_control_spell_id` membership, trusted Phase 2C anchors and locked Phase 2B geometry.
Phase 3A remains **LOCKED / COMPLETE**, unchanged: 34 matches, 2,888 provider parents,
86,025 context events and 3,202 control spells. The source revision is
`533862946a73608c134d18b78226b6371ce7173c`. No soft resets or new boundaries enter this build.

The existing Phase 3A event CSV has no UUID. Exact `(match_id, event_index)` equality against
the pinned complete stream recovers it, with one-to-one checks of period, parent, possession
team, timestamp, elapsed time, event type and event team. This is exact provider identity,
never nearest order or timestamp matching. All subsequent joins use `(match_id, event_id)`.
The Phase 3A summary revision, Phase 2C source inventory and every selected geometry revision
must agree. The full historical geometry file must match its Phase 2B protected SHA-256.
The manifest records input, code, canonical fetched-record and analytical output hashes.

## B. Construction method

Re-run the existing complete-match Phase 2C semantic audit, including both directions of
explicit related-event evidence. Only `validated_core_event_team_scope` supplies states.
Unsupported and missing frames remain in `phase3b_event_context.csv`, including events outside
spells with their original membership status. No outcomes are exported or used; outcome-bearing
provider payloads are removed before invoking the shared event inventory validator.

Each anchor inherits its spell; `spatial_anchor_order` is one-based and follows source order.
`events_from_previous_anchor` is the difference in complete-stream positions (adjacent events
have gap 1); `intervening_event_count` subtracts one. `events_from_spell_start` is zero-based.
Seconds use actual period-local provider timestamps, including stoppage time, without endpoint
arrival estimates. First-anchor previous IDs/gaps and last-anchor next IDs remain missing.

The geometry source is the locked `phase2a_frame_geometry.csv`, under the Phase 2B contract.
The existing Phase 2C point-team mapper assigns literal event-team and other-team subsets to
`lev_` and `opp_`; `all_` denotes all visible. Original subset names remain as source metadata.
These primary fields exclude keepers; keeper-included counts remain alongside them and all six
original geometry variants remain linkable by match/event/frame index. Event-team identity
determines the mapping independently of possession team. The existing normalizer retains
Leverkusen-event centroids and rotates opponent-event centroids `(120-x, 80-y)`. Width/depth,
hull area and spacing are invariant under that rotation and retain their original values.
No home/away or period flip is applied. Units remain StatsBomb coordinate units (area squared).

The Phase 2B `D_primary` eligibility utility supplies each metric's availability: mathematical
status `ok` and actor status single/none, without a count, coverage, OOB or coincidence cutoff.
Each metric retains value, original status and availability, with side-specific selected count,
keeper policy, OOB/coincidence and measurement flags, and shared actor/visible-area support.
Whole-original-frame anomaly flags are carried separately from selected-outfield flags.

Transitions join consecutive trusted anchors within the same match and spell. Only two
available endpoints produce a delta; otherwise the delta is missing, with from/to/both-endpoint
status and original endpoint metric statuses. Endpoint support accompanies the transition.
These deltas are **differences between two event-aligned partial observations**, not continuous
movement or rates. Pressure is an observation of spatial structure, not an automatic ball or
progression action. Opponent anchors remain explicitly labeled as context.

## C. Anchor reconciliation

The old population reproduces exactly **46,143** trusted anchors: Pass 20,921; Carry 18,525;
Pressure 6,109; Shot 588; opponent-event anchors 6,846. Old provider-parent intervals reproduce
exactly **43,431**. The spell build contains **43,737 anchors**, **40,638 transitions**
and **5,526 opponent-event anchors**.

Exactly **2,406** prior trusted anchors have no locked spell
membership. These are excluded solely by Phase 3A's existing membership convention; terminal
boundary records belong outside the closing spell. Geometry availability causes no anchor loss.
The event-context output retains each excluded UUID and membership/boundary reason for inspection.

| label | value |
| --- | --- |
| dead_or_terminal_context/Pass | 234 |
| dead_or_terminal_context/Shot | 477 |
| insufficient_context_no_spell/Pressure | 1 |
| outside_control/Carry | 629 |
| outside_control/Pass | 609 |
| outside_control/Pressure | 450 |
| outside_control/Shot | 6 |

The 2,793 removed old intervals comprise
**2,778** with at least one excluded endpoint and
**15** whose retained endpoints belong to different
spells. No new pair bridges an excluded prior anchor. Transition count also equals retained
anchors minus spells with at least one anchor. **Unexplained discrepancies: 0.**

| event_type | leverkusen_action | opponent_context |
| --- | --- | --- |
| Carry | 17864 | 32 |
| Pass | 19876 | 202 |
| Pressure | 367 | 5291 |
| Shot | 104 | 1 |

## D. Control-spell spatial coverage

All **3,202** spells remain in the readiness inventory, including zero-anchor spells.
Percentages use all 3,202 spells. The 5+ group is nested within 3+.

| label | value | percent |
| --- | --- | --- |
| 0 | 103 | 3.217 |
| 1 | 193 | 6.027 |
| 2 | 167 | 5.215 |
| 3_plus | 2739 | 85.54 |
| 5_plus | 2360 | 73.704 |

The spell table also retains event count/duration, anchor proportions, per-type/team counts,
transition count, first/last anchor offsets, median/p90/maximum gaps and metric availability
counts. Single-anchor spells have no gap statistics. Sparse-spell quantiles are descriptive
and can be determined by very few pairs; their transition counts make that support explicit.

## E. Anchor-gap structure

Seconds across the 40,638 within-spell pairs; quantiles use linear interpolation of the
observed gap distribution. Landmark percentages use the number of observed transitions.

| label | value | percent |
| --- | --- | --- |
| median | 1.096 | — |
| p75 | 1.732 | — |
| p90 | 3.158 | — |
| p95 | 4.506 | — |
| maximum | 22.126 | — |
| le_1_seconds | 18261 | 44.936 |
| le_3_seconds | 36199 | 89.077 |
| le_5_seconds | 39057 | 96.11 |
| gt_5_seconds | 1581 | 3.89 |

Long gaps do not invalidate endpoints, split spells or create exclusions. Consecutive spatial
anchors need not be consecutive football actions. No interpolation, forward fill or synthetic
anchors are used.

## F. Metric availability

Available primary keeper-excluded measurements out of **43,737** trusted anchors per side:

| metric | all | lev | opp |
| --- | --- | --- | --- |
| centroid_x | 43737 | 43737 | 43732 |
| centroid_y | 43737 | 43737 | 43732 |
| convex_hull_area | 43734 | 43680 | 43549 |
| mean_nearest_neighbor_distance | 43736 | 43732 | 43681 |
| mean_pairwise_distance | 43736 | 43732 | 43681 |
| median_pairwise_distance | 43736 | 43732 | 43681 |
| visible_depth | 43737 | 43737 | 43732 |
| visible_player_count | 43737 | 43737 | 43737 |
| visible_width | 43737 | 43737 | 43732 |

`phase3b_metric_availability.csv` gives exact mathematical statuses, primary percentages and
available transition counts for every metric/side. Semantic trust does not certify every
geometry metric, full-team observation or comparable point composition at two endpoints.

| section | label | value | percent |
| --- | --- | --- | --- |
| support | frame_oob | 4436 | 10.142 |
| support | frame_coincident | 24 | 0.055 |
| visible_area_fraction | p05 | 0.176 | — |
| visible_area_fraction | median | 0.294 | — |
| visible_area_fraction | p95 | 0.455 | — |

Visible-area fractions describe supplied on-pitch coverage, not complete player observation.
No new sensitivity analysis or exclusion policy is applied. Later comparisons can apply the
locked whole-frame OOB/coincidence checks using retained endpoint metadata.

## G. Match-level consistency

All 34 matches contribute anchors and control spells. Coverage varies; every match remains
visible in the season denominator. Counts below impose no match or spell exclusion.

| match_id | spell_count | anchor_count | zero_anchor_spells | three_plus_anchor_spells | five_plus_anchor_spells | opponent_anchor_count |
| --- | --- | --- | --- | --- | --- | --- |
| 3895052 | 93 | 859 | 3 | 75 | 61 | 136 |
| 3895060 | 103 | 1397 | 1 | 89 | 79 | 175 |
| 3895067 | 95 | 1490 | 2 | 89 | 80 | 147 |
| 3895074 | 93 | 1123 | 5 | 74 | 64 | 153 |
| 3895086 | 98 | 1490 | 2 | 87 | 78 | 202 |
| 3895095 | 82 | 1087 | 2 | 70 | 59 | 127 |
| 3895107 | 91 | 1493 | 4 | 77 | 65 | 184 |
| 3895113 | 93 | 1241 | 4 | 80 | 70 | 173 |
| 3895121 | 93 | 1390 | 4 | 73 | 61 | 117 |
| 3895134 | 84 | 1038 | 6 | 69 | 57 | 169 |
| 3895139 | 84 | 1615 | 0 | 73 | 65 | 208 |
| 3895153 | 97 | 1389 | 2 | 88 | 74 | 178 |
| 3895158 | 114 | 1303 | 2 | 103 | 92 | 161 |
| 3895167 | 97 | 951 | 3 | 83 | 64 | 138 |
| 3895180 | 104 | 1387 | 2 | 95 | 88 | 170 |
| 3895182 | 109 | 1405 | 7 | 94 | 77 | 216 |
| 3895194 | 118 | 1546 | 2 | 103 | 81 | 217 |
| 3895202 | 85 | 1178 | 3 | 67 | 58 | 131 |
| 3895210 | 94 | 2063 | 1 | 89 | 84 | 293 |
| 3895220 | 104 | 1512 | 3 | 88 | 71 | 238 |
| 3895232 | 91 | 858 | 3 | 67 | 53 | 151 |
| 3895244 | 111 | 1136 | 3 | 88 | 75 | 199 |
| 3895250 | 113 | 1290 | 6 | 91 | 81 | 152 |
| 3895258 | 96 | 1483 | 3 | 83 | 77 | 163 |
| 3895266 | 79 | 1669 | 2 | 70 | 69 | 102 |
| 3895275 | 81 | 1313 | 1 | 67 | 58 | 103 |
| 3895286 | 103 | 1393 | 1 | 92 | 83 | 141 |
| 3895292 | 86 | 1182 | 3 | 78 | 68 | 111 |
| 3895302 | 74 | 1201 | 1 | 69 | 61 | 170 |
| 3895309 | 83 | 1008 | 2 | 75 | 59 | 173 |
| 3895320 | 102 | 944 | 3 | 80 | 65 | 175 |
| 3895333 | 79 | 758 | 3 | 68 | 54 | 118 |
| 3895340 | 91 | 1124 | 7 | 76 | 66 | 100 |
| 3895348 | 82 | 1421 | 7 | 69 | 63 | 135 |

## H. Limitations

These are event-aligned partial observations, with no continuous tracking. Ordinary off-ball
players are anonymous; endpoint records do not establish persistent player identity. Missing
and unsupported frames, variable visible area, changing selected counts/composition and gaps
between anchors limit comparisons. Metric-specific support remains necessary even when both
endpoint values exist. No interpolation or continuous-movement inference is made. This phase
constructs no outcomes, tactical labels, sequence archetypes or effectiveness analysis.

## I. Readiness decision

**READY WITH ANALYSIS-SPECIFIC SUPPORT REQUIREMENTS**

Exact joins and source reconciliation succeed, all matches are represented, and
2,739 spells contain at least three observations; however,
103 have none and 193 have only one.
Variable observation density and metric/visibility support require an explicit support strategy
for the chosen analysis. Anchor counts can describe the observations available for before/after
or richer ordered comparisons, but this audit approves no universal minimum-anchor or maximum-gap
threshold. Successful CSV reruns verify byte-identical outputs and preserve historical artifacts.

Phase 3B construction is complete; Phase 3 as a whole is not declared complete. Next authorized
discussion: **select the first within-control-spell spatial-change analysis**.

# Metric registry — proposed, not implemented

Let P be a qualified set of visible player coordinates in one event-aligned frame,
n its size and d Euclidean distance in StatsBomb coordinate units. Inclusion of
goalkeepers, team/role mapping and orientation remain to be fixed. Empty/degenerate
sets require explicit missing-value rules. No row below is implemented.

Provenance uses SOURCE, ADOPT, ADAPT, DERIVE, PROJECT and REJECT as defined in
[source foundation](source_foundation.md). Status describes definition maturity,
not completed code. Source IDs refer to the supplied PDF transcribed in the source
foundation; they do not imply independent verification of every original formula.
Unspecified project definitions and thresholds remain open.

| Variable | Football meaning | Formula / definition | Source / provenance | Status | Required raw fields | Observation grain | Limitations | Research question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Defensive width | Lateral span of visible defenders | max(y) − min(y) over qualified visible defenders | DERIVE: geometric range; S07, S12: published width definition; ADAPT: visible-defender subset | DERIVED | freeze_frame.location, teammate, keeper; event team/possession_team | Frame | Visibility and orientation dependent; no full-team claim | 2, 5, 6, 9 |
| Defensive depth | Longitudinal span of visible defenders | max(x) − min(x), distinct from centroid field position | DERIVE: geometric range; S07, S12: published team-length definition; ADAPT: visible-defender subset | DERIVED | freeze_frame.location, teammate, keeper; event team/possession_team | Frame | Span is not block height; missing players bias it | 2, 5, 6, 9 |
| Team centroid | Mean position of the selected visible team subset | (sum(x)/n, sum(y)/n) | DERIVE: arithmetic mean; S07, S08: centroid definition/precedent; ADAPT: visible-team subset | DERIVED | freeze_frame.location, teammate, keeper; event team | Frame/team subset | Composition changes can move centroid without motion | 2, 5, 7 |
| Convex hull area | Area enclosing the selected visible players | Area(convex hull(P)) | DERIVE: planar geometry; S07, S08: hull/surface-area definition/precedent; ADAPT: visible-team subset | DERIVED | freeze_frame.location, teammate, keeper | Frame/team subset | Degenerate sets and keeper inclusion unresolved; not controlled space | 2, 3, 7, 9 |
| Mean pairwise/interpersonal distance | Average spacing within a visible subset | sum over i<j of d(P_i,P_j) / (n(n−1)/2) | DERIVE: Euclidean distances (S07); PROJECT: stated all-pairs mean; ADAPT: visible subset; PDF supplies pair distance, not this exact aggregation | DERIVED | freeze_frame.location, teammate, keeper | Frame/team subset | Undefined for n<2; not line spacing or tracking distance | 2, 7, 9 |
| Nearest defender distance | Visible pressure proximity to an observed actor | min d(actor, defender); eligible actor/defenders require audit | ADAPT: S21 defender-proximity precedent, S07 base distance; PROJECT: visible minimum and eligibility rules, not an exact formula supplied by the PDF | ADAPT | freeze_frame.actor, location, teammate; event location/team | Event/frame | Unseen defenders may be nearer; not arrival time | 1, 3, 8 |
| Local numerical superiority | Visible attacking minus defending presence nearby | Candidate N_attackers(r) − N_defenders(r); center, r and actor inclusion TBD | PROJECT: local neighborhood definition | TBD | freeze_frame.location, teammate, actor; event team/possession_team | Event/local neighborhood | Radius null; visible subset only; cannot label global overload | 1, 3, 6, 9 |
| Visible-area-clipped Voronoi area | Observed geometric partition around a player | Area(Voronoi cell intersect visible polygon intersect pitch) | ADAPT: S13 Voronoi precedent; S01, S02 visibility context; S11 spatial-variable distinctions; PROJECT: visible-area/pitch clipping; S14, S17 dynamic-control boundary | ADAPT | freeze_frame.location; visible_area | Frame/player point | Boundary/duplicate-point handling TBD; unseen players alter cells; not pitch control | 3, 6, 9 |
| Future xG | Subsequent recorded chance quality | Candidate sum of shot_statsbomb_xg in a future window; team/boundary rules TBD | SOURCE: S01 shot data, S03 xG meaning; PROJECT: future-window aggregation, explicitly the study definition in the PDF | TBD | match_id, index, timestamp, period, possession, team, type, shot.statsbomb_xg | Anchor event/window | Window null; censoring, overlap and attribution unresolved | 4, 5, 6, 9 |
| Future shot | Whether a subsequent shot occurs | Indicator of eligible Shot event in calibrated future window | SOURCE: S01 event data/type provenance; PROJECT: future window and eligibility | TBD | match_id, index, timestamp, period, possession, team, type | Anchor event/window | Window null; possession termination and censoring unresolved | 4, 5, 9 |
| Future box entry | Whether a later action enters the attacking box | Eligible entry from outside to inside provisional penalty area; action/outcome rules TBD | PROJECT: entry and window definition | TBD | location, pass.end_location, carry.end_location, pass.outcome, type, team, period, possession, timestamp, index, match_id | Anchor event/window | Orientation and completed-action rules pending; window null | 3, 4, 6, 9 |
| Defensive regime | High, mid or deep observed defensive structure | Qualified visible structure classification; features/cutoffs TBD | PROJECT: regime operationalization; S04, S05: phase vocabulary/context; ADAPT: S06 operational baseline; project cutoffs are not standards | TBD | Qualified geometry, event team/possession_team, visibility fields | Frame or sequence; TBD | No final centroid threshold, clustering or classification | 5, 6, 9 |
| Valuable space | Space relevant to creating danger | Value function and spatial aggregation TBD | PROJECT: exact construct/formula unresolved; ADAPT: S18 occupation/generation and location-weighted space, S19 off-ball opportunity, S20 EPV concept/ceiling; faithful tracking EPV remains REJECT | TBD | TBD after definition and observation audit | TBD | Area alone is not value; avoid circular outcome definitions | 3, 4, 6, 7 |

Line spacing, sequence aggregation, geometric degeneracy, actor attribution and
sensitivity variants require further specification. No adopted academic formula
is asserted without a verified source. Continuous velocity, acceleration, dynamic
pitch control and tracking EPV are REJECT for faithful reconstruction here.

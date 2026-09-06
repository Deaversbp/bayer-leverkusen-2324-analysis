# Metric registry — proposed, not implemented

Let P be a qualified set of visible player coordinates in one event-aligned frame,
n its size and d Euclidean distance in StatsBomb coordinate units. Inclusion of
goalkeepers, team/role mapping and orientation remain to be fixed. Empty/degenerate
sets require explicit missing-value rules. No row below is implemented.

Provenance uses SOURCE, ADOPT, ADAPT, DERIVE, PROJECT and REJECT as defined in
[source foundation](source_foundation.md). Status describes definition maturity,
not completed code. Academic provenance is TBD wherever not available locally.

| Variable | Football meaning | Formula / definition | Source / provenance | Status | Required raw fields | Observation grain | Limitations | Research question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Defensive width | Lateral span of visible defenders | max(y) − min(y) over qualified visible defenders | DERIVE: geometric range; football source TBD | DERIVED | freeze_frame.location, teammate, keeper; event team/possession_team | Frame | Visibility and orientation dependent; no full-team claim | 2, 5, 6, 9 |
| Defensive depth | Longitudinal span of visible defenders | max(x) − min(x), distinct from centroid field position | DERIVE: geometric range; football source TBD | DERIVED | freeze_frame.location, teammate, keeper; event team/possession_team | Frame | Span is not block height; missing players bias it | 2, 5, 6, 9 |
| Team centroid | Mean position of the selected visible team subset | (sum(x)/n, sum(y)/n) | DERIVE: arithmetic mean | DERIVED | freeze_frame.location, teammate, keeper; event team | Frame/team subset | Composition changes can move centroid without motion | 2, 5, 7 |
| Convex hull area | Area enclosing the selected visible players | Area(convex hull(P)) | DERIVE: planar geometry | DERIVED | freeze_frame.location, teammate, keeper | Frame/team subset | Degenerate sets and keeper inclusion unresolved; not controlled space | 2, 3, 7, 9 |
| Mean pairwise/interpersonal distance | Average spacing within a visible subset | sum over i<j of d(P_i,P_j) / (n(n−1)/2) | DERIVE: Euclidean distances | DERIVED | freeze_frame.location, teammate, keeper | Frame/team subset | Undefined for n<2; not line spacing or tracking distance | 2, 7, 9 |
| Nearest defender distance | Visible pressure proximity to an observed actor | min d(actor, defender); eligible actor/defenders require audit | ADAPT: proximity concept; source review TBD | ADAPT | freeze_frame.actor, location, teammate; event location/team | Event/frame | Unseen defenders may be nearer; not arrival time | 1, 3, 8 |
| Local numerical superiority | Visible attacking minus defending presence nearby | Candidate N_attackers(r) − N_defenders(r); center, r and actor inclusion TBD | PROJECT: local neighborhood definition | TBD | freeze_frame.location, teammate, actor; event team/possession_team | Event/local neighborhood | Radius null; visible subset only; cannot label global overload | 1, 3, 6, 9 |
| Visible-area-clipped Voronoi area | Observed geometric partition around a player | Area(Voronoi cell intersect visible polygon intersect pitch) | ADAPT: geometric partition; source review TBD | ADAPT | freeze_frame.location; visible_area | Frame/player point | Boundary/duplicate-point handling TBD; unseen players alter cells; not pitch control | 3, 6, 9 |
| Future xG | Subsequent recorded chance quality | Candidate sum of shot_statsbomb_xg in a future window; team/boundary rules TBD | SOURCE: shot field; PROJECT: aggregation | TBD | match_id, index, timestamp, period, possession, team, type, shot.statsbomb_xg | Anchor event/window | Window null; censoring, overlap and attribution unresolved | 4, 5, 6, 9 |
| Future shot | Whether a subsequent shot occurs | Indicator of eligible Shot event in calibrated future window | SOURCE: event type; PROJECT: window | TBD | match_id, index, timestamp, period, possession, team, type | Anchor event/window | Window null; possession termination and censoring unresolved | 4, 5, 9 |
| Future box entry | Whether a later action enters the attacking box | Eligible entry from outside to inside provisional penalty area; action/outcome rules TBD | PROJECT: entry and window definition | TBD | location, pass.end_location, carry.end_location, pass.outcome, type, team, period, possession, timestamp, index, match_id | Anchor event/window | Orientation and completed-action rules pending; window null | 3, 4, 6, 9 |
| Defensive regime | High, mid or deep observed defensive structure | Qualified visible structure classification; features/cutoffs TBD | PROJECT: regime operationalization | TBD | Qualified geometry, event team/possession_team, visibility fields | Frame or sequence; TBD | No final centroid threshold, clustering or classification | 5, 6, 9 |
| Valuable space | Space relevant to creating danger | Value function and spatial aggregation TBD | PROJECT: construct requiring source review | TBD | TBD after definition and observation audit | TBD | Area alone is not value; avoid circular outcome definitions | 3, 4, 6, 7 |

Line spacing, sequence aggregation, geometric degeneracy, actor attribution and
sensitivity variants require further specification. No adopted academic formula
is asserted without a verified source. Continuous velocity, acceleration, dynamic
pitch control and tracking EPV are REJECT for faithful reconstruction here.

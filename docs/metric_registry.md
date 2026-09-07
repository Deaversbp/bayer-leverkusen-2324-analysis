# Metric registry — Phase 2A definitions locked; geometry not implemented

**Phase 2A method lock: 7 September 2026.** This contract freezes the eight basic
within-frame measurement definitions below. It does not implement them, select a
final research sample, or advance later metrics. Existing Phase 1 raw-record
counts remain audit outputs; the Phase 2A valid-point count has the explicit
definition below and must not silently replace those audit fields.

Provenance uses SOURCE, ADOPT, ADAPT, DERIVE, PROJECT and REJECT from the
[source foundation](source_foundation.md#3-provenance-framework). Definition status
`LOCKED` is separate from provenance and implementation status. S01/S02 support
provider/observation provenance, S07/S08/S12 support the stated base geometry,
and PROJECT identifies our subset, aggregation and error-handling choices.
The source foundation supplies citation evidence, not independent verification of
every original publication. No academic attribution is invented for the mean or
median aggregations or nearest-neighbor summary.

## 1. Shared Phase 2A measurement contract

### 1.1 Records and valid points

The unit is one **original 360 frame record**, preserving its ordinal within the
match, not an arbitrarily selected event/frame join. Let R be its observed
`freeze_frame` list. A missing/unavailable/non-list container has unknown counts
and all eight metrics are NA with `metric_status=frame_unavailable`; an observed
empty list is known empty. Never create zero-player frames for events without 360.

A valid point record is a dictionary whose `location` is a two-element list or
tuple of finite real numeric values `(x,y)`. Booleans, numeric strings, nulls,
NaN/infinity, missing or
wrong-length locations and non-dictionary list entries are not valid points.
Use the supplied values without coercion, imputation, rounding, snapping, clipping
or coordinate repair. Invalid records remain in the raw data and are counted in
metadata; only the valid selected records enter P. Other malformed fields do not
invalidate a finite point unless required for that subset/keeper variant.

Finite coordinates outside the nominal inclusive bounds `[0,120] × [0,80]` remain
in these **diagnostic measurements** and are flagged/countable as out of bounds;
no tolerance, clamp or automatic exclusion is introduced. Here “valid point” means
mathematically evaluable, not verified pitch placement or research eligibility.
This separates existing coordinate/coverage diagnostics from later sample choices.

P is an indexed collection of selected valid **records**, `P_i=(x_i,y_i)`, with
`n=len(P)`. It is not a deduplicated set of people or coordinates. The original
point ordinal supplies i; no inferred player identity is used. Let u be the
number of distinct exact coordinate pairs for hull diagnostics only. Computing u
does not remove records or change counts/weights. Coincident points remain separate
records in every calculation, including input to the hull operation.

### 1.2 Subsets and goalkeeper variants

All eight metrics are defined for all six combinations below, subject only to
their mathematical minima. `all_visible` describes the combined visible point
cloud, not one team's shape. Neither literal team subset is globally named
attacking/defending or Leverkusen/opponent.

| `selected_subset` | Selection before goalkeeper filtering |
| --- | --- |
| `all_visible` | Every valid point, including records with missing/unknown `teammate` |
| `teammate_true` | Valid points whose `teammate` is literal boolean True |
| `teammate_false` | Valid points whose `teammate` is literal boolean False |

Unknown/missing/non-boolean `teammate` values do not enter either literal team
subset. Do not coerce `1`, `0`, strings or nulls to flags; retain the unassigned
count so team subsets are not assumed to partition all visible records completely.

| `goalkeeper_policy` | Exact filter and interpretation |
| --- | --- |
| `included` | No keeper filter: retain valid subset points regardless of `keeper`, including unknown flags |
| `excluded` | Keep only literal `keeper=False`; omit True and unknown/missing/non-boolean keeper flags, retaining separate exclusion counts |

Thus `excluded` means **known non-goalkeepers**, not an assumption that an unknown
flag denotes an outfield player. Record unknown flags before filtering even when
the resulting subset is empty. Compute/report both variants as paired planned
sensitivity outputs wherever defined, including counts and the all-visible cloud;
do not choose a universally correct goalkeeper convention. Differences with unknown
flags reflect both keeper removal and unclassified records, and must be described
as such. Both variants exclude no actor merely because it is the actor.

### 1.3 Coordinates, distances and aggregation

Use native StatsBomb 120 × 80 axes throughout Phase 2A. Do not flip, normalize
attacking direction, choose mirrored coordinates, convert to metres, or rescale
axes for the primary measurements. Centroid x/y are stored coordinate summaries,
not direction-dependent football statements. Width is the native y-span and depth
the native x-span. Neither span establishes attacking direction or block height.

For distinct **record indices** i and j:

```text
d(i,j) = sqrt((x_i-x_j)^2 + (y_i-y_j)^2)
D = [d(i,j) for every i<j]; k = n(n-1)/2
```

D contains one distance per unordered record pair, including zeros and repeated
distance values. “Unique pairs” does not mean unique coordinate pairs or unique
distance values. No self-pairs, double counting or zero-distance removal is allowed.
For a sorted collection `z_(1),...,z_(k)`, the median is the middle element for odd
k and `(z_(k/2)+z_(k/2+1))/2` for even k. The arithmetic mean/median uses equal
record/pair weights as specified, with no rounding before aggregation.

Native distances/spans/centroid coordinates are in StatsBomb coordinate units;
areas are in squared StatsBomb coordinate units, never metres or square metres.
Counts are integer records, not a count of verified distinct people.

### 1.4 Required fields and output grain

In the locked table, **F** means raw `freeze_frame.location`; raw `teammate` for
the two flag subsets and raw `keeper` for the excluded variant; `actor` for frame
ambiguity diagnostics; and the context contract below for **every** variant.
The included/all-visible measurement can still be computed when a team/keeper
flag is unknown. No event location, possession-team mapping or named-player ID
is a numerical input to Phase 2A geometry.

**G** means one original frame × `selected_subset` × `goalkeeper_policy` × metric
(centroid emits two components). A wide row carrying all eight metrics at that
frame/subset/keeper grain is equivalent, but every metric needs its own status.
Retain all six subset/keeper combinations even when a result is zero or NA. No
cross-frame pooling or interpolation is part of the definition.

| Mandatory context | Exact meaning |
| --- | --- |
| `match_id`, `frame_index`, `event_id`, `event_type` | Match context, zero-based original frame ordinal, raw `event_uuid` as `event_id` only when a nonblank string (otherwise NA), and event type only from a unique match-local join; retain ambiguity/missing type explicitly |
| `event_join_status`, source revision | Carry audit join status and immutable release provenance; never expand a many-to-many join or pick an arbitrary event |
| `selected_subset`, `goalkeeper_policy` | One of the three literal subsets and one of the two keeper policies above |
| `n_valid_points_used`, `n_unique_points` | n and u after validity/subset/keeper selection; NA when frame container unavailable |
| `total_visible_players` | Raw list length, including malformed entries if present; a provider-record inventory, not a distinct-person or valid-point count; NA for unavailable/non-list frame, 0 for observed empty list |
| Invalid/selection counts | Whole-frame non-dictionary entries and dictionaries with invalid locations, counted separately; whole-frame valid points unassigned by unknown teammate; counts of keeper=True and keeper-unknown valid points in each selected team subset before keeper filtering (zero omitted in `included`, both counts omitted in `excluded`) |
| `n_out_of_bounds_points` | Selected finite points outside inclusive native pitch bounds; diagnostic only |
| `visible_area_fraction`, visible-area validity/status | Carry Phase 1 polygon missing/malformed/topology-valid status and pitch-intersection area divided by `120*80`; unknown/invalid fraction is NA, not zero; do not compute a substitute player hull as visible area |
| `actor_count`, multiple-actor status | Whole-frame literal actor flags, plus unknown/malformed actor flags; status `multiple`, `single`, `none`, or `unknown` under section 3 |
| Coincidence / multiple-actor flags | `n-u` coincident excess records for selected P and whole-frame ambiguity status; these are warnings about records, not deduplication instructions |
| `metric_status`, `measurement_flags` | Numerical status and all applicable context flags (partial invalid input, unknown role/keeper, out-of-bounds, missing/invalid visible area, ambiguous join, coincidence, actor ambiguity); flags never silently disappear when a metric is computable |

Metadata names above define a data contract, not newly implemented fields.
Existing audit fields may be mapped explicitly without changing their meaning.
For invalid raw event IDs, retain diagnostic raw-ID information separately if
available; `frame_index` preserves grain even when `event_id` is missing/duplicated.

No visible-player, visible-area or edge-censoring threshold is set here. The table's
minimum n/u values are mathematical requirements, not research-visibility cutoffs.
Missing/invalid visible area, low coverage, missing actor alignment or an ambiguous
event join does not by itself prevent a within-frame mathematical measurement.
Retain the result and context; event type can be unknown. The geometry layer does
not emit a final research-eligibility decision or equate `frames_joint_checks`
with eligibility. Future event-linked analysis still must satisfy the methods
specification's observation gate.

## 2. Locked Phase 2A metric rows

Every row is `LOCKED / NOT IMPLEMENTED` under this contract. **All six** means the
three literal subsets × included/excluded goalkeeper variants from section 1.2;
F and G expand to the complete fields/context and observation grain above.

| Metric / output | Exact formula | Source / provenance | Definition / implementation status | Required raw fields | Valid subsets / goalkeeper policy | Minimum valid points | Units | Grain | Missing / degenerate behavior | Visibility limitation | Research question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Visible player count: `visible_player_count` | `n = len(P)` | SOURCE: S01, S02 records/flags; DERIVE count; PROJECT validity/subset policy | LOCKED / NOT IMPLEMENTED | F | All six | 0 for a known list | Integer valid records | G | Known empty selection yields 0; unavailable/non-list frame yields NA; coincident records each count | Partial/unknown flags and invalid points can lower selected n; duplicate records can overstate people; never full-team count | 2, 9 |
| Centroid: `centroid_x`, `centroid_y` | `centroid_x = sum_i(x_i)/n`; `centroid_y = sum_i(y_i)/n` | S07, S08: ADOPT arithmetic centroid; DERIVE coordinates; ADAPT visible subset; PROJECT record policy | LOCKED / NOT IMPLEMENTED | F | All six | 1 | Native coordinate units per component | G | n=0: both NA; n=1: that point; duplicates retain equal record weights; no unique-point requirement | Visibility/subset composition and duplicate weights affect centroid; no direction-dependent interpretation | 2, 5, 7, 9 |
| Visible width: `visible_width` | `max_i(y_i) - min_i(y_i)` | S07, S12: ADOPT base width/range; DERIVE span; ADAPT visible subset/native-axis reporting | LOCKED / NOT IMPLEMENTED | F | All six | 1 | Native coordinate units | G | n=0: NA; n=1: 0; all equal y: 0; duplicates do not change extrema | Unseen extreme players/edge censoring bias observed span; not a full-team or attacking-direction measure | 2, 5, 6, 9 |
| Visible depth: `visible_depth` | `max_i(x_i) - min_i(x_i)` | S07, S12: ADOPT base length/range; DERIVE span; ADAPT visible subset/native-axis reporting | LOCKED / NOT IMPLEMENTED | F | All six | 1 | Native coordinate units | G | n=0: NA; n=1: 0; all equal x: 0; duplicates do not change extrema | Native x-span, not block height or attacking direction; unseen extreme points can increase full span | 2, 5, 6, 9 |
| Convex hull area: `convex_hull_area` | `Area(ConvexHull(P))` only for a valid nonempty Polygon with finite positive area | S07, S08: ADOPT hull/surface construction; DERIVE area; ADAPT visible subset; PROJECT degeneracy/error policy | LOCKED / NOT IMPLEMENTED | F | All six | n>=3 AND u>=3 AND non-collinear | Squared native coordinate units | G | n<3, u<3, collinear/empty/nonpolygon/zero-area hull: NA; repeated points allowed if valid polygon remains; Shapely/GEOS error or invalid polygon: NA with error status | Observed footprint only, not space controlled; duplicates leave hull unchanged but can disguise insufficient unique points | 2, 3, 7, 9 |
| Mean pairwise distance: `mean_pairwise_distance` | `sum_{i<j} d(i,j) / (n(n-1)/2)` | S07: ADOPT base Euclidean distance; DERIVE arithmetic; PROJECT all-pairs mean; ADAPT visible subset; exact aggregation not attributed to S07 | LOCKED / NOT IMPLEMENTED | F | All six | 2 records, not 2 unique locations | Native coordinate units | G | n<2: NA; coincident-pair zeros retained; n=2: the sole pair distance, including 0 | Record multiplicity/visibility alter pair weights and spacing; no inferred line spacing or motion | 2, 7, 9 |
| Median pairwise distance: `median_pairwise_distance` | `median(D)` using section 1.3 odd/even rule | S07: ADOPT base Euclidean distance only; DERIVE median; PROJECT all-pairs aggregation; ADAPT visible subset | LOCKED / NOT IMPLEMENTED | F | All six | 2 records, not 2 unique locations | Native coordinate units | G | n<2: NA; preserve zero/repeated distances; n=2: sole pair distance; even k: mean of central two | Describes observed record pairs; missing players/duplicates change distribution; not a published median metric claimed here | 2, 7, 9 |
| Nearest-neighbor spacing: `mean_nearest_neighbor_distance` | `NN_i = min_{j!=i} d(i,j)`; `mean_nearest_neighbor_distance = sum_i(NN_i)/n` | S07: ADOPT base Euclidean distance only; DERIVE minima/mean; PROJECT within-subset NN summary; ADAPT visible observations | LOCKED / NOT IMPLEMENTED | F | All six | 2 records, not 2 unique locations | Native coordinate units | G | n<2: NA; exclude self by record index, not coordinate equality; coincident distinct records give NN=0; n=2: mean of two equal sole-neighbor distances | Neighbor restricted to selected P; unseen players can be closer, duplicates force artificial zeros; not actor-to-nearest-defender distance | 2, 7, 9 |

The prior basic rows “Defensive width,” “Defensive depth,” “Team centroid” and
“Mean pairwise/interpersonal distance” are represented by the literal-subset rows
above. No attacker/defender label or published novelty is inferred by renaming.
Later actor-to-nearest-defender distance remains a separate unchanged candidate.
The **arithmetic mean** is the single locked frame summary for nearest-neighbor
spacing; a median NN summary or neighbor identity/tie-breaking output is not
introduced. Tied minima need only a scalar minimum, not selection of a named player.

### 2.1 Minimum-point and numerical status rules

Apply these per metric, not as a filter dropping the frame or another metric's
valid result. NA always has an explicit reason, never a silently substituted zero.

| Condition | Value / `metric_status` |
| --- | --- |
| Frame container unavailable/missing/non-list | All metric values and unknown counts NA / `frame_unavailable` |
| Known n=0 selection | Count 0 / `ok`; centroid and spans NA / `empty_points`; distance summaries NA / `insufficient_points`; hull NA / `insufficient_points` |
| n=1 | Count 1, centroid the point, spans 0 / `ok`; all distance summaries and hull NA / `insufficient_points` |
| n>=2 | Distances evaluable including coincident zeros / `ok`, subject to numeric errors; hull still needs its own gate |
| Hull n<3 | NA / `insufficient_points` |
| Hull n>=3 but u<3 | NA / `insufficient_unique_points` |
| Hull with adequate n/u but empty, Point, LineString or zero area | NA / `degenerate_hull`; exactly three collinear points follow this rule |
| Shapely/GEOS hull construction or area-evaluation failure, invalid Polygon, or unexpected nonpolygon type | NA / `geometry_error`; retain diagnostic error category; no repair/retry with altered coordinates |
| Nonfinite arithmetic/area result or numerical failure | NA / `numeric_error`; do not emit infinity, clamp a negative area to zero, or drop records to force a value |
| Successful finite result satisfying that metric's gates | Value / `ok`, while retaining all context/ambiguity flags |

Centroid components are returned together: an unavailable/failed centroid yields
both NA. For hull checks use the stated order (container, n, u, construction,
geometry validity/type, finite positive area). Nonfinite area is `numeric_error`;
finite negative area is `geometry_error`. Other unexpected programming/schema
failures must surface, not be swallowed as an ordinary missing hull.

A single-point span of zero is the exact range of one observed coordinate, not
proof of a zero-width team; n is always retained. Similarly a pair of distinct
records at the same location has a real zero recorded distance, even though their
identity is uncertain. Hull area is a two-dimensional footprint: return NA for
lower-dimensional/insufficient geometry rather than presenting 0 as measured
occupied surface. No epsilon for collinearity, near-coincidence or small positive
area is introduced. Use supplied numeric coordinates and the geometry result;
near-collinear but valid positive-area polygons remain numeric, not thresholded.

## 3. Multiple actors and coincident records

Frame actor status uses the full raw list before any subset/keeper filter. Count
literal `actor=True` records; two or more imply `multiple` even if other flags
are unknown. With fewer than two, any unknown/non-boolean actor flag or malformed
record/container implies `unknown`; otherwise exactly one is `single` and zero
is `none`. Do not replace missing actor flags with False. Multiple-actor flags are
inherited by **all** subset/keeper variants, even those not containing both actors.

The four known frames in match 3895139 (event indices 541, 798, 1978 and 2036;
UUIDs in the [technical appendix](../report/technical_appendix.md#multiple-actors))
each retain their two identical actor locations. No record is selected, removed,
merged, or assigned an inferred identity. Apply the generic status rule, not a
hard-coded exception for those four IDs.

| Quantity | Effect of repeating an already present valid record |
| --- | --- |
| Count | Increases selected record count if retained by the subset/keeper filters; can overstate distinct people |
| Centroid | Reweights the repeated location and generally moves the record mean; may be unchanged in special cases |
| Mean/median pairwise distance | Adds a zero pair and repeats distances to other records; changes pair weights and can distort either summary |
| Nearest-neighbor spacing | Distinct coincident records become zero-distance neighbors; can depress the mean without actual tactical proximity |
| Width/depth | Exact duplicate locations do not change extrema |
| Hull | Exact duplicates do not change the mathematical footprint; u/non-collinearity still determine whether a polygon exists |

**Locked ambiguity policy:** calculate and retain the unmodified record-based
measurements wherever mathematically defined, with `measurement_flags` recording
`multiple_actor`/`actor_status_unknown` and any `coincident_records`. These values
are diagnostic measurements, not a resolution of player identity. Do not suppress
the frame inventory, mutate raw observations or treat coincidences alone as proof
that records are duplicated players.

For later comparisons of these Phase 2A metrics, keep frames with `multiple` or
`unknown` actor status out of the **primary** comparison and retain them unchanged
as a separately labeled inclusion sensitivity. This is a conservative,
frame-level record-ambiguity policy, applying even to duplicate-invariant spans
and hulls so paired comparisons use the same declared policy. It is not a final
research-eligibility decision and is not executed by the measurement layer.
`single`/`none` do not establish final eligibility either. Coincidence without
actor ambiguity is retained with a flag and the same formulas, with no automatic
deduplication or exclusion. A later justified change to the ambiguity policy
requires an explicit method revision; unknown person identity remains unresolved.

## 4. Remaining calibration and interpretation decisions

The eight formulas, minima, record/flag filters, units, numerical missing rules
and ambiguity treatment are locked for implementation planning. Remaining choices
are research eligibility/visibility thresholds (including edge censoring), a
preferred goalkeeper convention if later justified, resolution of actual identity
in multiple-actor records, and event/team/coordinate semantics for football
interpretation. None prevents computing the defined native-record diagnostics.

`config/visibility.yaml` remains unchanged: `minimum_visible_attackers`,
`minimum_visible_defenders` and `minimum_visible_area_fraction` are null;
`exclude_edge_sensitive_frames: false` is not a validated eligibility rule. No
visibility or outcome threshold, coordinate transformation, composite compactness,
Voronoi, tactical regime, sequence feature or outcome model is added by this lock.

## 5. Later metric candidates — unchanged status

The following existing rows remain proposed, not implemented. Their exact
definitions, role mapping, observation eligibility, thresholds and sensitivity
choices are not advanced by Phase 2A. Their original Status column describes
definition maturity, not completed code.

| Variable | Football meaning | Formula / definition | Source / provenance | Status | Required raw fields | Observation grain | Limitations | Research question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nearest defender distance | Visible pressure proximity to an observed actor | min d(actor, defender); eligible actor/defenders require audit | ADAPT: S21 defender-proximity precedent, S07 base distance; PROJECT: visible minimum and eligibility rules, not an exact formula supplied by the PDF | ADAPT | freeze_frame.actor, location, teammate; event location/team | Event/frame | Unseen defenders may be nearer; not arrival time | 1, 3, 8 |
| Local numerical superiority | Visible attacking minus defending presence nearby | Candidate N_attackers(r) − N_defenders(r); center, r and actor inclusion TBD | PROJECT: local neighborhood definition | TBD | freeze_frame.location, teammate, actor; event team/possession_team | Event/local neighborhood | Radius null; visible subset only; cannot label global overload | 1, 3, 6, 9 |
| Visible-area-clipped Voronoi area | Observed geometric partition around a player | Area(Voronoi cell intersect visible polygon intersect pitch) | ADAPT: S13 Voronoi precedent; S01, S02 visibility context; S11 spatial-variable distinctions; PROJECT: visible-area/pitch clipping; S14, S17 dynamic-control boundary | ADAPT | freeze_frame.location; visible_area | Frame/player point | Boundary/duplicate-point handling TBD; unseen players alter cells; not pitch control | 3, 6, 9 |
| Future xG | Subsequent recorded chance quality | Candidate sum of shot_statsbomb_xg in a future window; team/boundary rules TBD | SOURCE: S01 shot data, S03 xG meaning; PROJECT: future-window aggregation, explicitly the study definition in the PDF | TBD | match_id, index, timestamp, period, possession, team, type, shot.statsbomb_xg | Anchor event/window | Window null; censoring, overlap and attribution unresolved | 4, 5, 6, 9 |
| Future shot | Whether a subsequent shot occurs | Indicator of eligible Shot event in calibrated future window | SOURCE: S01 event data/type provenance; PROJECT: future window and eligibility | TBD | match_id, index, timestamp, period, possession, team, type | Anchor event/window | Window null; possession termination and censoring unresolved | 4, 5, 9 |
| Future box entry | Whether a later action enters the attacking box | Eligible entry from outside to inside provisional penalty area; action/outcome rules TBD | PROJECT: entry and window definition | TBD | location, pass.end_location, carry.end_location, pass.outcome, type, team, period, possession, timestamp, index, match_id | Anchor event/window | Orientation and completed-action rules pending; window null | 3, 4, 6, 9 |
| Defensive regime | High, mid or deep observed defensive structure | Qualified visible structure classification; features/cutoffs TBD | PROJECT: regime operationalization; S04, S05: phase vocabulary/context; ADAPT: S06 operational baseline; project cutoffs are not standards | TBD | Qualified geometry, event team/possession_team, visibility fields | Frame or sequence; TBD | No final centroid threshold, clustering or classification | 5, 6, 9 |
| Valuable space | Space relevant to creating danger | Value function and spatial aggregation TBD | PROJECT: exact construct/formula unresolved; ADAPT: S18 occupation/generation and location-weighted space, S19 off-ball opportunity, S20 EPV concept/ceiling; faithful tracking EPV remains REJECT | TBD | TBD after definition and observation audit | TBD | Area alone is not value; avoid circular outcome definitions | 3, 4, 6, 7 |

Line spacing, sequence aggregation, actor attribution and later sensitivity
variants require further specification. Continuous velocity, acceleration, dynamic
pitch control and tracking EPV remain REJECT for faithful reconstruction here.

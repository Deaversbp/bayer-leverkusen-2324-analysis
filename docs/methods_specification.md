# Methods specification — draft

Status: Phase 1 — Data & Observability Audit. This is a planning specification;
model selection, tactical classification, model training and results analysis
have not been performed. No local methods PDFs or academic source Markdown were
present at migration. Formal source-backed definitions remain to be reviewed.

## Data flow and existing behavior

StatsBomb Open Data → nested records → pandas DataFrames → validation and
transformations → future analysis → figures, tables and diagnostics.

Package loaders retain nested lists of dictionaries; `normalize_events` uses
`pandas.json_normalize(..., sep="_")`. The dataset builder preserves source event
order, team/type filters, match date conversion, opponent and Home/Away context.
With no matching events it returns exactly the four context columns. It does not
sort, construct possessions, reorient coordinates or classify tactics.

Old loaders read local files. Package loaders now fetch in memory by default;
explicit `raw_data_dir` and legacy wrappers preserve read-only offline access.
No database or persistent raw-data cache is introduced.

## Observational boundary

StatsBomb 360 is event-aligned freeze-frame spatial context, not continuous
22-player tracking. Supported future analyses can use visible-player coordinates,
teammate/opponent structure, visible defensive width/depth, centroids, convex
hulls, pairwise spacing, zone occupation, local overloads, visible-area-clipped
Voronoi and changes between observed event-aligned spatial states.

Do not claim faithful continuous player velocity, acceleration, continuous player
trajectories, true time-to-intercept models, full dynamic pitch control, continuous
EPV tracking models or named off-ball trajectories where identity is unavailable.
The `trajectories.py` namespace is reserved for event-state sequences only.

Use “visible defensive width,” not “full-team defensive width.” A visible subset
may change between frames; an apparent structural change may reflect visibility.
Visible-area clipping does not recover the influence of unobserved players.
Frame teammate flags must be interpreted relative to the event actor/team before
labeling attackers and defenders. Goalkeeper inclusion is not yet fixed.

## Phase 1 audit requirements

1. Reconfirm 34 unique Leverkusen Bundesliga matches for competition 9/season 281.
2. Quantify per-match and per-event 360 availability; distinguish missing files,
   absent frames, malformed frames and empty visible-player lists.
3. Join events `id` to frames `event_uuid` within match, checking uniqueness and
   unmatched records before computing visible attacker/defender counts.
4. Inspect visible-area polygons and pitch coverage, edge sensitivity, player
   locations, actor/event-coordinate consistency and missing fields.
5. Verify event/frame orientation, possession-team interpretation, goalkeeper
   handling and period transitions before comparing spatial states.
6. Report sample attrition and missingness by match, event type and context.
   Establish the usable sample before modeling. Existing notebook record counts
   do not establish spatial observability.

## Decisions still open

### Implemented observability definitions

`leverkusen.data.observability` implements the inventory, event/frame integrity,
visible-player counts, visible-area checks, actor consistency and grouped attrition.
The CLI writes only the three derived Phase 1 CSVs. It fetches each match's events
and 360 once per run without persisting raw responses.

ID joins are match-local. Event rows and frame rows retain their original grain;
duplicates do not expand a many-to-many join. Duplicate counts are excess records
beyond the first occurrence, with duplicated-ID group counts also reported. IDs
that are missing, blank or not strings never match. Ambiguous frame links retain
their rows but have no arbitrarily selected event metadata or actor comparison.

Missing 360 files have status `missing`; other HTTP/transport/payload failures have
status `error`. Their frame inventories are unknown, not zero. Attrition's zero
observed frame rows for such a match must be read alongside
`events_360_load_unavailable` and the match load status. Failed event loading aborts
the audit. An observed empty 360 list is distinct from an unavailable resource.

An observed empty freeze-frame list has zero players. Missing/malformed containers
have unknown counts. Non-dictionary entries and invalid player locations are
reported. `teammate_true` and `teammate_false` count literal boolean flags; unknown
flags are retained separately. No global attacker/defender labels are assigned.

Visible areas must be flat lists of at least three finite x/y pairs. Absent/null
areas are missing; structurally invalid lists (including empty lists) are malformed.
Shapely validates topology; invalid polygons are not repaired. Both original polygon
area and its pitch-intersection area are reported. `visible_area_fraction` is the
intersection area divided by pitch length × width, not unbounded polygon area.
Scalar coordinate count and paired vertex count are distinct; a supplied closing
vertex is included in the count. These are observability checks, not team-shape
metrics. See the [Shapely manual](https://shapely.readthedocs.io/en/stable/manual.html)
for polygon validation and intersection operations.

Actor distance uses original coordinates only, for one located actor and a uniquely
linked event with a finite two-coordinate location. Unmeasurable distances are null,
never zero. Counts, mean, median, maximum and 25/75/90/95/99 percentiles are reported.
`actor_distance_review_rank` ranks measured distances descending; ties follow source
order. The ten largest are presented for inspection, not designated threshold
failures. Neither player coordinates nor event coordinates are transformed.

Attrition first reports independent event/frame counts. Cumulative frame checks
then require unique event and frame IDs, a nonempty freeze frame, valid visible area,
and finally measurable actor distance plus valid locations for all player records.
`frames_joint_checks` does **not** require a small actor discrepancy, sufficient
visible players, sufficient area, known identities or calibrated sample eligibility.
Scopes (season, match, event type, event team) are alternative partitions, not
additive across scopes. Orphan/ambiguous/missing categories remain in the totals.

### Calibration still pending

All visibility and outcome thresholds are intentionally null. Before analysis is
locked, calibrate minimum visible players/area, edge handling, local radius,
defensive regimes, future outcome windows, valuable-space definitions and player
inclusion rules. Null values must not silently be interpreted as zero.

`config/zones.yaml` supplies simple provisional rectangles on a 120 × 80 grid.
Its lane convention assumes attacking toward increasing x. Do not apply it before
verifying orientation; no orientation transformation is implemented. Euclidean
distances are coordinate units, not automatically physical metres.

Future sequences must be keyed by match, possession and period, ordered by event
index/timestamp, with explicit restart, turnover and censoring rules. Do not
interpolate anonymous off-ball identities between frames. Future xG aggregation,
shot/box-entry definitions and attribution remain unresolved; avoid overlapping
window leakage and report sensitivity. Associations will not establish causation.

## Reproducibility before method lock

Record upstream revision/retrieval time, match IDs, package environment,
configuration, exclusions and derived output provenance. Review sources in
[source foundation](source_foundation.md), update the [registry](metric_registry.md),
and lock calibration choices before evaluating effectiveness. No methods have been
selected merely to populate the package skeleton.

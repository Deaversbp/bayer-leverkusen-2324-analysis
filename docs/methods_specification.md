# Creating Space Under Xabi Alonso — Methods & Data Specification

Bayer Leverkusen 2023/24 Spatial-Sequence Analysis.

**Current status: Phase 1/1B COMPLETE — Phase 2A basic geometry definitions LOCKED.**
The 7 September 2026 [Phase 2A registry contract](metric_registry.md#1-shared-phase-2a-measurement-contract)
freezes eight within-frame metrics, subsets, goalkeeper variants and edge cases.
It supersedes earlier pending-definition wording for those eight measurements;
visibility calibration and later methods remain open. No Phase 2 metrics,
direction normalization, tactical classifier, pattern discovery or predictive
model has been implemented or approved for implementation by this synchronization.

Document lineage: original *Methods & Data Specification v1.0*, September 2026
(26-page supplied PDF), merged with the repository's completed Phase 1/1B work and
current source foundation on 7 September 2026. This is the current methodology
contract, with the original 31 major section numbers retained for traceability.
Statements marked proposed, candidate, optional or deferred describe future work.
Results below are transferred from the technical appendix, not a new audit run.

## 1. Purpose of this specification

Make the technical research article reproducible, citation-aware, feasible with
free data and resistant to methodological drift. Prefer published definitions
where required inputs exist. Otherwise transparently adapt and rename the method,
retain it only as conceptual background, or reject faithful reproduction. Preserve
enough contextual data contracts for the full article without repeatedly rebuilding
ingestion; an analytical mart here means in-memory DataFrames, not a database.

| Document | Responsibility |
| --- | --- |
| This methods specification | Current methodology contract, phase scope and change record |
| [Source foundation](source_foundation.md) | Evidence, bibliography, source IDs and provenance framework |
| [Metric registry](metric_registry.md) | Exact operational formulas, source/provenance, maturity, input fields, grain and limitations |
| [Research questions](research_questions.md) | Current numbered research questions referenced by the registry |
| [Technical appendix](../report/technical_appendix.md) | Implementation/verification details, measured results and explicitly historical findings |

### Reconciled assumptions

Original scientific intent is preserved; newer empirical findings and existing
interfaces govern where the original proposal differs.

| Original proposal / earlier assumption | Current contract and reason |
| --- | --- |
| Public retrieval through `statsbombpy`, including `sb.frames`, with DataFrame-returning loaders | Existing `requests` loaders preserve nested records; normalization is separate. No wrapper migration or new dependency is needed (sections 4, 6, 25) |
| Mutable Open Data `master` used in the early repository workflow | Every source uses immutable revision `533862946a73608c134d18b78226b6371ce7173c`; later release event/frame UUID incompatibilities were observed (section 32) |
| PDF section 7.3 called event locations possession-oriented | Actor/team and event-type semantics require verification; the statement is not a universal orientation rule |
| PDF section 7.4 would correct a frame when its flipped actor alignment is materially closer, otherwise quarantine it | Direct/mirrored comparisons remain diagnostic only; no automatic coordinate transformation, correction flag claiming a correction, or universal tolerance (sections 7, 32) |
| Standard-pitch metre coordinates proposed | Native 120 × 80 units remain the implemented convention; the 105 × 68 rescaling proposal is retained but unimplemented |
| PDF schema tests allowed valid or repairable visible polygons | Current audit validates without repair; invalid polygons remain reported as invalid |
| One canonical row per 360 event in analytical tables | Audit retains original frame records, including duplicates/ambiguous links; analytical event-grain uniqueness requires an explicit eligibility contract |
| Phase 1 audit still pending / UUID cause unresolved | Phase 1/1B complete; pinned release has zero orphan frames. Coordinate, actor, visibility and metric eligibility questions remain open |
| Academic sources unavailable at migration | S01–S35 are synchronized in the source foundation; exact adaptations still require method review |
| Broad Phase 2 included zones and clipped Voronoi | Initial Phase 2A is restricted to basic within-frame geometry method lock; zones/Voronoi and tactical interpretation remain later work |
| PDF ADOPT labels for all-pairs mean, and DERIVE labels for proximity/overload | Current registry preserves published base geometry versus PROJECT aggregation/eligibility/radius; PDF labels alone do not establish an exact published formula |
| PDF “Phase 0” calibration and example windows | Calibration remains pending before each relevant method lock; candidate values are not current defaults and all null thresholds remain null |

The PDF's recommended layout/loader signatures and source aliases are mapped to
current repository equivalents in sections 24, 25 and 30 rather than silently
treated as existing code. No historical appendix finding is removed.

## 2. Locked research scope

### Primary research question

> How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24 Bundesliga season, and which recurring attacking sequences were most effective against different defensive structures?

### Supporting questions

The current [research questions](research_questions.md) control numbering:

1. What recurring attacking spatial patterns characterized Leverkusen's possession play?
2. How did opponent defensive width, depth, compactness, occupied area and line spacing evolve during those patterns?
3. Which attacking patterns created the largest increases in valuable attacking space?
4. Which resulting spatial changes were associated with the greatest subsequent chance quality?
5. How did effectiveness differ across high, mid and deep defensive structures?
6. Against deep defenses specifically, which patterns most effectively disrupted defensive structure or created exploitable space?
7. At what point in successful sequences did defensive structure begin to deteriorate?
8. Which player actions were most involved in producing those changes?
9. How sensitive are results to visibility thresholds, defensive-regime definitions and sequence-window definitions?

The Methods PDF's compatible wording additionally specifies occupied area,
spacing/line structure (question 2), exploitable space (3), on-ball players
initiating/progressing/completing sequences (8), and stability under alternative
quality thresholds and window lengths (9). Preserve those aims within the current
questions. Named attribution is restricted to identified event actors. “Evolve,”
“trajectory” and “point” refer to observed states, not unobserved continuous motion.

### Intended contribution and novelty boundary

The research form is a technical article with academic rigor: an interpretable
single-team case study connecting event sequence, timing, visible-player spatial
history, defensive structural change and subsequent chance quality. Recurring
attacking mechanisms and opponent response subtypes are proposed findings, not
results already established.

Centroid, width, occupied surface, stretch and distance families (S07–S12),
Voronoi/dominant regions (S13–S14), EPV/xT/VAEP/OBV (S20, S22–S25), event sequences
(S26, S29), 360 representations/Situational xT (S27) and event/freeze-frame tactic
extraction (S28) are established work. Position the contribution against S18,
S20, S21, S27, S28 and S29, not only reviews S34/S35.

The study is not designed to identify a universal optimum for breaking low blocks,
establish causation from observational patterns, reproduce continuous tracking from
360, or name anonymous off-ball points without directly available identity.

## 3. Citation and provenance policy

Use the [source foundation](source_foundation.md#3-provenance-framework) categories:

| Category | Meaning | Required treatment |
| --- | --- | --- |
| SOURCE | Raw provider field or provider documentation | Cite provider documentation |
| ADOPT | Published definition/method used materially unchanged | Cite original or authoritative source |
| ADAPT | Published concept modified for StatsBomb 360 or project constraints | Cite source, explain modification, rename when needed |
| DERIVE | Mathematical quantity directly derived from observed data | Document formula and dependencies |
| PROJECT | New project-specific operationalization or construct | State explicitly, validate and sensitivity-test |
| REJECT | Method incompatible with the available observation model | Do not use its published name for an unacknowledged proxy |

Compatibility, provenance, definition maturity and implementation status are
separate. A visible metric may DERIVE arithmetic from an ADOPT base formula while
ADAPT describes its observed subset. SOURCE is not a method implementation.
Citation roles such as DATA, METRIC DEFINITION, ONTOLOGY, ORIGIN, REVIEW, BENCHMARK,
BOUNDARY, CLOSEST PRIOR WORK, VALIDATION and UNCERTAINTY retain their meanings in
the foundation; they do not replace these six categories. Never borrow a metric
name while silently changing its inputs. Source IDs reference the supplied
research foundation, not a claim that every original paper has been reverified.

## 4. Computing environment and cost architecture

Use Python in VS Code, GitHub for versioned code/configuration/documentation, and
Codex for repository work against these contracts. No paid database, commercial
StatsBomb account or persistent raw StatsBomb warehouse is required.

Current flow: pinned StatsBomb Open Data → `requests` → nested records → pandas
DataFrames in memory → validation/normalization → future derived features →
figures, aggregate tables and article outputs. Paid-only convenience metrics must
not be assumed available. The PDF proposed `statsbombpy` as a public access wrapper,
not a paid API; that access-layer choice is superseded by the working loaders.

Prefer match-by-match processing: obtain match metadata, fetch one match's events,
360 and relevant lineups, validate, retain only needed derived analytical records,
release raw match objects, then continue. Reuse objects within a session to avoid
repeated requests. Do not retain the full raw corpus unless memory diagnostics
justify it. The implemented audit fetches each match's events and 360 once per run;
lineups are available through a separate loader, not an inferred audit dependency.

Git contains code, configuration, tests, methods and optionally intentionally
selected final aggregate figures/tables. Derived diagnostics go under ignored
`outputs/`; raw JSON/frame dumps are not committed or newly cached to disk. A clean
clone should regenerate the study from the pinned public source. Existing ignored
raw files and read-only legacy access remain preserved outside the pinned audit;
`scripts/download_data.py` is legacy and outside the current workflow.

## 5. Python stack and version policy

The verified repository environment is Windows Python 3.14; package syntax requires
Python >=3.10. Other environments need their own validation. Use the existing
`.venv` as the VS Code interpreter/notebook kernel and editable `leverkusen`
installation; reusable imports should not require notebook path hacks.

| Library / tool | Role and current disposition |
| --- | --- |
| `requests` | Implemented public, revision-pinned retrieval; replaces PDF's `statsbombpy` choice |
| pandas / NumPy | DataFrames and vectorized numerical work |
| SciPy | Planned geometry/distances/statistical utilities; present in notebook dependencies |
| Shapely | Now required for implemented visible-polygon validity and pitch intersection; future clipping |
| matplotlib / seaborn / mplsoccer | Core plots, statistical graphics and StatsBomb-aware pitch/sequence visualization |
| scikit-learn | Planned scaling, PCA, clustering, regression/classification and validation; not added by this merge |
| statsmodels | Planned interpretable statistical models/inference; not added by this merge |
| NetworkX | Optional graph/passing-network work; retained notebook dependency |
| PyYAML | Project constants and future calibrated definitions |
| Jupyter / pytest / Ruff | Notebook exploration, meaningful unit/data-contract tests and linting |
| hdbscan | Optional density clustering if an unknown cluster count warrants it |
| umap-learn | Optional representation visualization, not default inference |
| prefixspan | Optional sequential pattern mining (S28) |
| tslearn | Optional dynamic-time-warping experiments for variable-length state trajectories |
| xgboost | Optional nonlinear benchmark if simpler scikit-learn models are insufficient |
| joblib | Optional persistence of derived model artifacts for reproducibility |

Deep-learning frameworks are omitted from the baseline; add only if simpler
methods fail to answer the research questions and a later method decision justifies
them. No package installation or environment change is part of this merge.

Keep conceptual methods independent of today's versions. `requirements.in` lists
direct dependencies; `requirements-lock.txt` freezes a tested machine-specific
environment, including Windows dependencies, and is not a cross-platform solver
lock. The old `requirements.txt` is historical. Resolve and validate a new platform
before freezing its environment; do not broadly upgrade as part of synchronization.

## 6. StatsBomb source schema and project dependencies

### Scope and raw sources

Use competition **9**, season **281**, Bayer Leverkusen team **904**, as configured
in [project.yaml](../config/project.yaml). Match metadata is fetched dynamically
from the same immutable release as events, lineups and 360. The verified study
sample contains 34 Bundesliga matches. S01/S02 provide dataset provenance.

| Source | Fields/context to preserve when present |
| --- | --- |
| Match records | `match_id`, `match_date`, `match_week`, home/away teams and scores, competition/season, `match_status_360`, data/XY fidelity metadata when exposed |
| Derived match context | Leverkusen home/away, opponent, final result, chronological order; only existing loader/transform behavior is currently implemented |
| Events | `id`, `index`, `period`, `timestamp`, `minute`, `second`, `type`, `possession`, `possession_team`, `play_pattern`, `team`, `player`, `position`, `location`, `duration`, `under_pressure`, `related_events` |
| Action attributes | Action end locations/outcomes; pass recipient, length, angle and available descriptors; carry endpoint; shot outcome and `shot.statsbomb_xg` |
| 360 records | Raw `event_uuid`, `freeze_frame` points with `location`, `teammate`, `actor`, `keeper`, and frame `visible_area`; attach match ID as context |
| Lineups | Named-player metadata and available role/substitution/position context; never identities for anonymous off-ball frame points |

The PDF described `statsbombpy` player rows with renamed `id` and optional
`distance_from_edge_of_visible_area`. The current raw loader retains `event_uuid`
and nested frame records. No wrapper-derived edge distance is guaranteed. Event
normalization uses underscore-separated flattened names (for example
`shot_statsbomb_xg`); assert actual schema/optional fields rather than assuming
wrapper columns. Raw nested and normalized names must not be confused.

### Observation model

Events describe timestamped actions and identified actors where provided. A 360
frame is a partially visible, event-aligned point cloud with actor-relative team
flags, not continuous tracking. Ordinary off-ball points are anonymous; lineups
do not identify them. Missing frames, empty frames and unavailable files are
different observations. Incomplete visible field and changing point-set composition
can change geometry without any corresponding full-team movement.

There are no observed continuous velocities, accelerations or trajectories, no
faithful tracking-based dynamic pitch-control reconstruction, and no named off-ball
trajectories inferred from anonymous points. Full-tracking methods remain boundaries
(S14, S17, S20); snapshot methods S27/S28 do not remove these limitations.

## 7. Coordinate and time conventions

Preserve native StatsBomb coordinates, x in 0–120 and y in 0–80. Current distances
are coordinate units. The original optional reporting conversion is retained:

```text
x_m = x_SB * (105 / 120)
y_m = y_SB * (68 / 80)
```

These would be standard-pitch rescaled coordinates, not measured venue dimensions.
No such conversion is implemented; any future metre-based result must disclose
the convention and retain native coordinates alongside it.

The PDF's proposal to flip/correct a frame if its mirrored alignment is materially
closer is **superseded**. The implemented audit compares direct event-to-actor
distance with a diagnostic 180-degree mirror `(120-x, 80-y)` without transforming
event or frame coordinates. No universal tolerance, automatic correction or
outcome-based quarantine rule is set. Event types have different semantics;
opposing/paired events, actor roles and mixed types require particular care.
Exact diagnostic definitions and findings are retained in section 32.

Before applying direction-dependent zones or naming attackers/defenders, justify
event-specific orientation and interpret `teammate` relative to the event actor/team
and possession team. A closer mirror or majority within an event type is not proof
of attacking direction. The existing orientation test checks no mutation, not a
future normalization rule. Phase 2A uses both locked goalkeeper variants in the
registry; no universally preferred inclusion convention has been selected.

The planned canonical match clock must be monotonic across periods, preserve raw
timestamps, and document stoppage/period handling. Sequence duration and delta-t
will use that elapsed-time field. It is not implemented. Use index/time and period
boundaries explicitly; do not invent motion between snapshots or carry windows
silently across periods.

## 8. Canonical analytical grains

These are conceptual DataFrame/data-contract grains, not database tables or a
claim that all tables exist. Avoid one giant denormalized DataFrame for every task.

| Concept | Planned grain | Content and current qualification |
| --- | --- | --- |
| `match_context` | One row per match | Match/date/week, opponent, home/away, score, metadata and revision; audit match summary exists, full analytical contract is future |
| `event_actions` | One row per source event | IDs, order/time, possession/team/player, action type/location and attributes; existing event normalization preserves source order |
| `frame_points` | One row per observed player record per frame | Match/event plus original frame/point ordinal, native location, actor-relative team/actor/keeper flags; metre position and edge distance are future; PDF correction flag is replaced by diagnostic orientation status until a correction method exists |
| `frame_quality` | Planned one row per eligible 360 event; audit currently one row per original frame | Visible team counts, polygon area, actor error/orientation diagnostics; target-zone visibility, edge censoring and quality tier are pending; duplicates remain distinct in the audit |
| `frame_geometry` | One row per eligible event-aligned state and declared subset/variant | Future metric source, retaining frame-quality metadata and eligibility/missingness; subset/keeper variants require explicit keys |
| `sequence_steps` | One eligible event in a Leverkusen possession | Event context, geometry, previous-state deltas and separately marked future targets; not implemented |
| `possession_sequences` | One possession or analytical sub-sequence | Start/end context, event/spatial-history summaries, later pattern labels and aggregate outcomes |
| Future outcome (explicit target view) | Anchor state × declared horizon/outcome | Future xG/shot/box-entry, team/possession boundary and censoring metadata; never predictor inputs |
| Tactical/pattern representation | Declared state/sequence representation and model version | Feature vector/rules, pattern assignment, validation and interpretation metadata; future work |

The final two views make the PDF's outcomes and pattern concepts explicit without
changing base ingestion. Preserve match-local event `id` → frame `event_uuid`
joins, original-record grain and ambiguity flags. No many-to-many expansion or
arbitrary event/frame selection is permitted.

## 9. Eligible events for spatial-sequence anchoring

The PDF's primary **candidate** actions are Pass, Carry, suitable non-duplicative
Ball Receipt, Dribble, Shot and Miscontrol/Dispossessed as useful terminal actions.
Pressure, Duel, Foul, Offside, tactical and stoppage events remain context and need
not be spatial anchors; some locations describe the acting player rather than
the ball. Retain the full stream for context and elapsed time.

This list is not a locked inclusion rule. Phase 1B's mixed Ball Receipt/Dribble
behavior and predominantly mirrored Dispossessed/Foul Won/Dribbled Past behavior
prevent treating these candidates as automatically eligible. The existing
`Ball Receipt*` source label and paired/opposing semantics need explicit handling.
Direct-favoring Pressure does not automatically become an on-ball anchor either.

The PDF's possession ID + possession team + match boundary is retained and refined
by the repository's **period** boundary. New sequences start on possession change;
future action-sequence/sub-sequence IDs must retain their parent match, possession,
team and period. Specify restarts, turnovers, terminal actions, set-piece/transition
subtypes and censoring without rebuilding ingestion. These IDs/rules are planned.

## 10. Frame-quality and observability gate

Visibility is part of the measurement model. For each proposed metric require a
valid join, valid visible polygon, valid selected-player coordinates, sufficient
observed geometry and justified actor/event alignment where integration depends
on the actor. The currently implemented mechanical checks do not constitute
final analytical eligibility.

For Phase 2A this is a later analytical-use gate, not a rule suppressing raw
within-frame diagnostic measurements. The registry locks mathematical evaluability
separately: retain calculable values with missing/invalid visibility or join
context flagged, and do not determine final research eligibility in the geometry
layer. Its point minima are not calibrated visibility thresholds.

Use metric-specific flags rather than only global pass/fail. A small visible area
may support some local proximity measurements while edge-censoring a width
estimate; it never proves an unseen defender cannot be nearer. For extrema-based
width/depth, plan to flag an extreme near the visible boundary. The edge tolerance
is uncalibrated. Report visible-player/team-subset geometry, not full-team coverage.

Retain raw observability metadata alongside every future metric: original frame
identity, counts and unknown flags, visible area/coverage, join validity,
actor/multiple-actor diagnostics, subset/keeper choice, and metric eligibility or
missing reason. Derived target-zone coverage and quality tiers remain future.

Choose thresholds from pre-outcome coverage distributions and geometric stability,
not whichever threshold yields the strongest tactical result. Freeze before
outcome comparisons, report attrition by match/event/context, and sensitivity-test
visibility choices. Section 32 retains exact implemented audit definitions.

## 11. Method compatibility gate

For **every** candidate method, document before production analytical code:

1. What does the published method require (fields, identity, coverage, time grain,
   units, velocity/trajectory assumptions)?
2. Does StatsBomb provide those inputs at the necessary grain and quality?
3. Classify compatibility as **EXACT / ADOPT**, **PARTIAL / ADAPT**, or
   **NO / REJECT**, with source IDs, modifications, renamed output and limits.

These are compatibility decisions, not implementation status. SOURCE, DERIVE and
PROJECT describe raw inputs or constructed quantities alongside the compatibility
decision; they do not bypass it.

| PDF gate family | Retained scope and current qualification |
| --- | --- |
| Green: observed data / feasible calculations | Event order, possession IDs/timing, eligible ball/action locations, pass/carry endpoints, shot xG, visible points/team flags/actor/keeper/area; visible centroids, width/depth, hulls, distances, clipped Voronoi, snapshot changes and future outcomes are possible after explicit definitions, not all implemented |
| Yellow: explicit adaptation/proxy | Defensive regimes, compactness composites, inferred lines/gaps, receiver openness, defensive-reaction classes, dangerous space, observed spatial-control share and tactical-pattern labels require ADAPT/PROJECT justification and validation |
| Red: unsupported faithful reproduction | Continuous velocity/acceleration, exact time-to-intercept, velocity-dependent pitch control, full 22-player tracking EPV, exact continuous running paths, anonymous named off-ball trajectories, FIFA tracking block/stationary definitions requiring speed and continuous duration |

The PDF's green label does not promote future outcomes from PROJECT to ADOPT or
visible-area-clipped Voronoi to full dynamic control. A published full-team method
restricted to visible points requires an explicit observation-model adaptation.
Red methods can be conceptual predecessors, never reproduced results (S14, S17,
S20). No movement proxy currently exists; any future proxy needs its own name,
definition, limitations and validation.

## 12. Metric registry — planned spatial structure

Exact production definitions/provenance belong in [metric_registry.md](metric_registry.md).
**No metric enters production analytical code until its source, status, exact
formula, data requirements, grain, eligibility and limitations are documented
there.** The foundation's formula ledger is evidence; this specification sets
scope. A formula in the original project PDF is not itself proof of academic origin.

| PDF baseline family | Planned meaning/use and source relationship |
| --- | --- |
| Centroid | Mean selected visible coordinates, collective location; S07/S08 |
| Visible width / depth (length) | Lateral/longitudinal extrema spans; S07/S12; depth span is not centroid position/block height |
| Length-to-width ratio | Depth divided by width; shape proportion, not universal compactness; S07; zero-width handling unresolved |
| Convex hull / occupied surface | Visible footprint; S07/S08; Phase 2A registry now locks three distinct non-collinear points and NA for degenerate/error cases |
| Mean pairwise/interpersonal distance | Mean over unordered selected pairs; S07 supports base distance, registry aggregation remains explicit PROJECT/DERIVE |
| Stretch index | Mean observed-player distance from centroid; S07/S12; component choices require review |
| Nearest-opponent distance (later) | Actor/ball, receiver-endpoint or zone-center proximity remains deferred; S07 base distance, S21 precedent. Phase 2A within-subset nearest-neighbor spacing is a separate PROJECT/DERIVE summary |
| Local numerical balance / overload / density | Attacking minus defending presence around target/radius; neighborhood and radius are PROJECT, pre-registered sensitivity choices |
| Zone occupation | Counts/shares in geometric central lane, half-spaces, wide lanes, penalty area and other declared zones; PROJECT boundaries fixed before outcomes |

This table retains the original broader plan. For the eight Phase 2A metrics,
the registry now locks `all_visible`, literal `teammate=True` and `teammate=False`
subsets with both keeper policies; no global attacker/defender mapping is required
or inferred. Counts already exist as observability diagnostics; geometry does not.
Median pairwise distance and mean within-subset nearest-neighbor spacing are now
locked PROJECT/DERIVE aggregations without invented published attribution.
The PDF's blanket ADOPT/DERIVE labels do not supersede current registry provenance,
especially for aggregates, proximity selection and local balance.

## 13. Voronoi and visible-space geometry — deferred

Retain S13's observed-point nearest-player tessellation concept. Any future cell
must be clipped to `visible_area` and the pitch under the registry's adaptation;
unbounded/full-pitch cells are not complete territorial control. The PDF's proposed
zone share is attacking cells' area intersected with zone and visible region,
divided by that zone's observed area. Cell union, zero denominator, duplicates,
boundaries and eligibility require exact registry definitions before use.

This is static nearest-player territorial share under observed geometry, not
dynamic pitch control (S11, S14, S17). Clipping cannot recover unseen influence.
Soft/weighted Voronoi or learned representations may be secondary comparisons to
S27, not required v1 methods. Neither clipped Voronoi nor naive full-pitch Voronoi
is part of initial Phase 2A implementation scope.

## 14. Defensive regime and compactness methodology — deferred

A defensive block is a tactical phase; compactness is a geometric property/family
(S09–S12). FIFA vocabulary/context (S04/S05) and Bauer's phase/formation precedent
(S06) inform interpretation, not universal numerical cutoffs. FIFA tracking-based
stationary/block definitions requiring player speed and continuous duration cannot
be faithfully reproduced with these snapshots.

Use **deep defensive structure/regime** unless a stricter low-block proxy has passed
validation; label any such proxy as PROJECT/ADAPT rather than FIFA's formal phase.
Candidate features are ball longitudinal position, visible defensive centroid,
width/depth, count/share goal-side of the ball, count/share in the defensive third,
hull area, stable inferred line positions and play-pattern/possession context.
All direction-dependent features await orientation/role justification.

Future ladder: transparent rules → inspect frames/distributions → threshold
sensitivity → optional geometry-clustering comparison → freeze regime mapping
before pattern-effectiveness evaluation. Composite compactness, high/mid/deep
thresholds and low-block classification remain explicitly unapproved.

## 15. Inferred defensive lines and between-line structure — deferred

Anonymous off-ball points prevent assigning lines from nominal player positions.
The PDF proposes ADAPT clustering visible defenders longitudinally, for example
hierarchical clustering or a one-dimensional Gaussian mixture. Constrain possible
line counts by football plausibility and observability; the original `x_m` example
depends on the unimplemented standard-pitch conversion in section 7.

For two stable inferred lines, the candidate gap is the absolute difference of
their mean longitudinal coordinates. This is a project operationalization until
its exact definition/provenance is registered. Emit no gap when visibility or
clustering quality is insufficient; missing is preferable to false precision.
Line counts, reliability thresholds and inference are not implemented.

## 16. Spatial trajectory features — planned

Here trajectory means an event-state history, not an identified player's continuous
path. The reserved `sequences/trajectories.py` namespace has that restricted meaning.
For a base metric M, the PDF proposes its first difference between eligible
consecutive states and a rate obtained by dividing that difference by delta-t.
These are DERIVE/PROJECT features citing M's source, not new published motion
formulas. Rates describe observed metric change, not velocity or acceleration.
Nonpositive/unknown delta-t, period transitions, missing states and changing
visibility require explicit missing/boundary rules in the registry.

For a prior-state or prior-time window, candidate summaries are start value,
current/end value, net change, mean, minimum/maximum, linear slope, total absolute
change and maximum one-step change. Such interpretable vectors can precede any
deep sequence model. Timing alone and geometry history are distinct comparisons
(S12, S26, S27, S29).

The PDF's proposed sensitivity grid is **previous 3, 5 and 7 eligible states** and
**previous 5, 10 and 15 seconds**. Retain both because equal action counts need not
represent equal elapsed time. These are candidates, not selected defaults or
configuration changes. Record all comparisons and preselect the primary
representation without optimizing on held-out effectiveness.

## 17. Attacking sequence descriptors — planned

Ball progression derives from action starts/endpoints and cumulative movement.
After orientation justification, candidates include forward/lateral/backward
displacement, widthwise switch-of-play distance, entry/exit from central/half-space
zones and box entry. Preserve provider pass type/cross/cutback/through-ball tags
only when actually supplied and schema-verified; do not assume paid convenience
metrics are available.

Overlap, underlap, overload-to-isolation, third-man combination and striker-drop
are not raw variables. Create labels only through explicit rules, supervised
labeling, sequential pattern mining (S28) or clearly identified post-cluster
football interpretation. Never derive named off-ball runners from anonymous
points. Retain identified on-ball initiator/progressor/completer context where
supported, distinguishing participation from causal credit.

## 18. Outcome variables — planned, not locked

Primary family: future chance quality (S03, S21). The original PDF candidate for
Leverkusen possession at t sums shot xG strictly after t and up to and including
t + T, restricted to the same possession. It proposes 5, 10 and 15 seconds and the
remainder of the possession. This is a **PROJECT future aggregation of SOURCE
xG**, not a published future-xG metric or a currently calibrated horizon.

Retained secondary candidates are shot or box entry within 5/10/15 seconds, shot
within possession, maximum/total possession xG, and possession loss without
final-third progression. PSxG is downstream of shot execution and unsuitable as
the primary buildup/chance-creation outcome; use provider shot xG meaning (S03).

The registry still controls the unresolved team attribution, action eligibility,
completed-action/entry rules, terminal possession/restart rules, horizon and
censoring choices. Preserve candidate same-possession intent without treating it
as a completed outcome implementation. Unknown follow-up is not automatically
zero. The current event/shot cannot appear as its own future target.

### Leakage controls

Predictors may contain only information available at the anchor. Keep future
outcomes separate from event/spatial histories even if joined for analysis.
Match, possession, period and ordered-event boundaries apply to both histories
and labels. Prevent overlapping windows/related sequence states from crossing
evaluation partitions; retain end-of-possession/match censoring. Fit scalers,
imputers, feature selection, clustering, learned value surfaces and probability
calibration on training data only. Do not tune windows, regimes or visibility on
held-out outcomes, or define valuable space using the same future target whose
association is being evaluated. These are future design requirements, not claims
that models already pass them.

## 19. Valuable-space measurement: staged approach — deferred

Do not create a dangerous-space composite prematurely (S18–S20).

| Original stage | Retained plan and limits |
| --- | --- |
| A: direct geometric outcomes | Report quantities separately: central/half-space visible-space share, nearest-defender distance, zone occupation, defensive width/depth/hull changes and local numerical balance. Each needs its own observation/definition gate; a named share is not already validated |
| B: static visible territorial advantage | Visible-area-clipped Voronoi shares within declared tactical zones; not dynamic pitch control |
| C: optional value weighting | After validation, integrate spatial availability times a published or empirically estimated location-value surface over visible area; ADAPT concepts and PROJECT exact combination |

The PDF's integral proposal leaves `Availability` and `V` operationally unspecified.
Register the exact formula before use; if V is xT-derived cite S22 and label the
combination project-specific. S18 distinguishes space occupation from generation
for teammates; S19/S20 set related-value/full-tracking boundaries. Do not call this
score pitch control or EPV. Availability, denominator, units, coverage and outcome
circularity remain unresolved; no dangerous-space score is approved.

## 20. Pattern-discovery methodology ladder — deferred

1. Football-defined descriptive patterns: transparent rules as baselines and
   interpretation aids.
2. Trajectory-feature clustering: standardized possession/sub-sequence event and
   spatial-summary vectors; K-means baseline, Gaussian mixtures for probabilistic
   clusters, HDBSCAN only if unknown cluster count/density structure warrants it.
3. Sequential pattern mining: discretize actions/zones and consider PrefixSpan
   with event/freeze-frame tactical precedents (S28).
4. Learned frame/sequence representations: consider only if levels 1–3 fail to
   capture useful structure; S27 is a benchmark, not a deep-learning requirement.

Silhouette/stability diagnostics are aids, not an objective to maximize at the
expense of football meaning or out-of-sample stability. Sequence clustering,
Transformer, LSTM and GNN models are explicitly deferred. No model is chosen to
fill the package skeleton.

## 21. Prediction models and baselines — deferred

Prediction is secondary to explanation; its role is to test whether spatial
history adds information beyond simpler context.

| Family | Feature comparison retained from PDF |
| --- | --- |
| A: event/location baseline | Current ball/action location, action type, play pattern, elapsed possession time and basic event context |
| B: current spatial state | Add current visible-frame geometry |
| C: event/timing history | Add prior actions and elapsed-time features |
| D: spatial trajectory history | Add changes/summaries of prior spatial states |

The key comparison is D against B and C out of sample, not whether a complex model
beats a trivial xT baseline. Explicitly declare the nested/ablation feature sets
when modeling is eventually locked. S22/S23 provide value lineage; S24/S25 action
value contrasts; S26 event-history, S27 snapshot and S29 timing comparisons.

Start with logistic regression for binary targets, regularized linear/GLM models
for continuous/sparse future-xG variants, then random forest or gradient boosting
as nonlinear benchmarks. Calibrate probabilities where appropriate using training
partitions. Proceed from descriptive analysis and geometry through interpretable
classical baselines and event-/spatial-history comparisons. More complex
sequence/GNN/deep models require evidence and a later method decision. Future-xG
predictive models are not currently approved.

## 22. Validation and statistical inference

Use S31/S32 for dependence-aware evaluation and S33 for bootstrap uncertainty.

- Hold out complete matches; preserve possessions/sequences within matches. Use
  chronological or grouped cross-validation for development and report variation
  across held-out matches/opponents. Never randomly split correlated event rows.
- For clustering, evaluate resampling stability, persistence across matches,
  football interpretability, sensitivity to scaling/features and domination by
  trivial ball location. Inspect representative sequences before naming clusters.
- Use match-level or possession-aware bootstrap where appropriate, retaining the
  dependence structure rather than blindly resampling event rows. Specify how
  match effects are respected if possessions are the resampling unit. Report
  uncertainty for pattern frequencies, future-xG means and differences only when
  sample size supports it.
- Evaluate probability calibration where applicable and use interpretable
  baselines. Keep all preprocessing and tuning within development partitions.
- Report visibility/missingness and sample attrition by match, event type/team and
  context. Sensitivity analyses must cover visibility/edge thresholds, player and
  goalkeeper inclusion, coordinate eligibility, sequence/action/time windows,
  outcome horizons, regimes, and later composite construction.
- Distinguish exploratory from confirmatory findings under many patterns/subgroups;
  do not present the largest discovered difference as pre-specified evidence.
- Use “associated with,” “preceded,” “co-occurred with” or “was followed by.” Pattern
  discovery alone does not establish that an attacking action caused a defensive
  response; causal claims remain outside the current design.

No predictive/clustering validation has been performed. The completed audit's
mechanical verification and the later analytical validation requirements are distinct.

## 23. Analytical outputs — planned

The team-level tactical profile will show defensive regimes faced, Leverkusen
occupation by regime, common progression routes, current-state and trajectory
summaries. Pattern cards should contain a football-readable name assigned after
inspection, frequency, representative sequence, start/end geometry, characteristic
spatial changes, future box-entry/shot rates, future xG, uncertainty and
opponent/regime distribution. For a given attacking pattern, compare defensive
response subtypes and spatial consequences without causal attribution.

Sequence visuals should show event-aligned states left-to-right in small multiples:
pitch, ball/action point, visible attackers/defenders after justified role mapping,
visible boundary, optional qualified clipped Voronoi/zone shading, event/action
label, elapsed time and selected geometry. Visuals must explain football while
showing observation limits. Current outputs are audit diagnostics, not these
tactical results. S30 is a professional spatial-representation/retrieval precedent
in the constrained corner-kick domain, not evidence of this project's effectiveness.

## 24. Repository architecture

The PDF's flat-module and `.yml` layout is a functional plan, superseded by the
existing package layout. Do not create duplicate flat modules or proposed tables.

| Responsibility | Current location / mapping |
| --- | --- |
| Project constants and calibration | `config/project.yaml`, `zones.yaml`, `visibility.yaml`, `analysis_thresholds.yaml`; replaces PDF `project.yml`, `zones.yml`, `quality_thresholds.yml`, `analysis_windows.yml` |
| Method/evidence/metrics | `docs/methods_specification.md`, `source_foundation.md`, `metric_registry.md`; canonical Markdown replaces PDF-era filename suggestions |
| Loading/schema/quality | `src/leverkusen/data/loader.py`, `schemas.py`, `validation.py`, `observability.py`, `transforms.py` |
| Future coordinates/geometry/visibility/zones/Voronoi | `src/leverkusen/spatial/`; normalization is not yet implemented |
| Future possessions/trajectories/outcomes | `src/leverkusen/sequences/` |
| Future regimes/patterns/clustering | `src/leverkusen/tactics/` |
| Future modeling/validation | `src/leverkusen/models/` |
| Future pitch/sequence/results figures | `src/leverkusen/visualization/` |
| Tests | Existing loader/transform/observability/orientation tests; geometry/sequence files remain scaffolds |
| Notebooks | `00_data_observability_audit`, `01_event_eda`, `02_360_frame_audit`, `03_spatial_geometry`, `04_defensive_structures`, `05_sequence_construction`, `06_pattern_discovery`, `07_effectiveness_analysis` (`.ipynb`); existing `00_data_audit`/`01_pass_eda` preserved |
| Outputs/article | Ignored `outputs/diagnostics/`, figures/tables; `report/` article/appendix documents, replacing the PDF's suggested `outputs/article/` convention |

Notebooks support exploration/narrative; reusable logic belongs in the package.
Feature/analysis entry points remain reserved and exit 2; the observability CLI
works. The original source/Methods PDFs remain external reference material; no PDF
archive, database or raw warehouse is created by this synchronization.

## 25. Data-loader contract

The PDF proposed DataFrame-returning `load_matches`, `load_events`, `load_frames`,
dictionary-of-DataFrames `load_lineups`, and `load_match_bundle -> MatchBundle`.
That interface was a recommendation, not the current API. Preserve the working
small-function interface:

```text
load_matches(*, raw_data_dir=None) -> list[dict]
load_events(match_id, *, raw_data_dir=None) -> list[dict]
load_lineups(match_id, *, raw_data_dir=None) -> list[dict]
load_360(match_id, *, raw_data_dir=None) -> list[dict]
normalize_events(events) -> pandas.DataFrame
```

There is no implemented `load_frames` or `load_match_bundle` API. Any future bundle
would remain in memory without raw persistence. The loaders access public data,
preserve source names/nesting and avoid research feature engineering. Normalize
stable columns separately and assert schemas; do not change the current return
types as part of methods synchronization.

`normalize_events` uses `pandas.json_normalize(..., sep="_")`. The dataset builder
preserves event order, team/type filters, match-date conversion, opponent and
Home/Away context; with no matching events it returns exactly four context columns.
It does not sort, construct possessions, reorient coordinates or classify tactics.

Missing resources (including 360) raise `FileNotFoundError`; transport/other HTTP
errors propagate from `requests`; invalid match IDs raise `ValueError`. The audit
records missing/unavailable 360 separately and aborts on event loading failure.
An absent frame is never evidence of zero visible players. Legacy `raw_data_dir`
and `src.data_loader`/`src.transforms` preserve read-only original local behavior;
unverified local revisions are excluded from the pinned audit.

## 26. Schema-contract tests and completed verification

The PDF's pre-analysis contracts remain requirements at the relevant method gate:

| Contract | Current evidence / remaining scope |
| --- | --- |
| 34 expected matches; all have 360 | Verified on the pinned release; unavailable resources still need explicit failure handling |
| Unique event IDs and frame joins | Verified zero duplicates/orphans in the pinned run; invalid/ambiguous records remain diagnostic cases |
| Usable ordered event indices; possession IDs/teams | Original order is preserved; complete future sequence eligibility/order contracts remain to be locked |
| Frame teammate/actor/keeper boolean/null structure | Audit records literal boolean/unknown flags; no inferred global attacking/defending labels |
| Coordinates within tolerated bounds | Validity/coordinate diagnostics exist; final geometry bounds/tolerances and eligibility remain uncalibrated |
| Visible polygons valid or flagged | Topology validation implemented; PDF's “repairable” option is superseded by no automatic repair |
| Shot xG present where expected | Must be asserted before future outcome construction; not established merely by overall event/frame counts |
| Coordinate/orientation sanity checks pass or flagged | Direct/mirrored diagnostics implemented; no coordinate rule or normalization is validated by a closer comparison |

Required schema failure should stop dependent analytical work early. The existing
audit itself retains malformed/ambiguous inputs as diagnostics where possible;
that is not permission to pass them into metrics. Future geometry/sequence tests
must be meaningful rather than treating current scaffolds as implemented methods.

The appendix records 119 offline tests, Ruff and the full pinned live CLI passing
for Phase 1B, with all six derived CSVs and unchanged raw inventory/null calibration.
Earlier migration/Phase 1 checks (44/86 offline tests and their other checks) remain
historical evidence in the appendix. This documentation merge does not rerun the
analytical suite or remeasure the data.

## 27. Calibration tasks — fixed before substantive results

The original “Phase 0” means planned pre-outcome calibration, not an assertion
that audit completion has resolved thresholds. Phase 1/1B established evidence;
Phase 2A research eligibility and later stage-specific locks still require choices.

Before the relevant outcome analysis freeze and document: actor alignment policy
and tolerance if justified; visibility/edge censoring; observation sufficiency
beyond Phase 2A's now-locked mathematical minima;
tactical zones; overload radii; regime thresholds; line-clustering quality;
eligible event family; primary action/time windows; and primary future horizon.
Use pre-outcome diagnostics, geometry stability and explicit sensitivity plans.
Record rationale and values in versioned config and article methods.

All current visibility and outcome thresholds are intentionally null. Null means
uncalibrated, not zero or permissive eligibility.
`exclude_edge_sensitive_frames: false` is a provisional setting, not validated
approval of edge-censored metrics.
The provisional `zones.yaml` rectangles assume attack toward increasing x and
must not be applied to tactical interpretation before orientation is justified.
No configuration values are resolved or changed here.

## 28. Analysis phases and immediate Phase 2A boundary

| Phase | Current status / intended work |
| --- | --- |
| 1: data and observability audit | **COMPLETE**: coverage, counts, joins, visible-player/area diagnostics, missingness and actor-coordinate checks |
| 1B: revision pinning and coordinate semantics | **COMPLETE**: immutable source, compatible pinned joins, diagnostic hypotheses and multiple-actor findings; semantics are not universally resolved |
| 2A: basic within-frame visible-player geometry | **Definitions LOCKED; not implemented.** Registry controls formulas, record handling and metadata; research eligibility remains open |
| Remaining Phase 2 geometry validation | Later: qualified zones and clipped Voronoi, representative-frame visual validation; separate method decisions required |
| 3: defensive regime characterization | Later: define/validate high/mid/deep structure without outcome information |
| 4: sequence construction | Later: possessions, event/spatial histories and action/time windows |
| 5: descriptive spatial evolution | Later: where/when observed defensive structure changes |
| 6: pattern discovery | Later: interpretable clustering/sequential methods; inspect before naming |
| 7: effectiveness analysis | Later: pattern frequencies, spatial changes, box entries, shots and future xG with uncertainty |
| 8: predictive incremental-value test | Later: spatial history versus current state and event/timing history |
| 9: technical article synthesis | Later: pair statistical results with football-readable sequences and inference limits |

Phase 2A locked metrics are visible player count, centroid, visible width, visible
depth, convex hull area, mean pairwise distance, median pairwise distance and
nearest-neighbor spacing (mean of each record's nearest other record in its subset).
Counts already exist as audit metadata; these Phase 2A definitions are not an
implemented geometry layer. The [locked registry](metric_registry.md#2-locked-phase-2a-metric-rows)
specifies exact formulas/provenance, six subset/keeper combinations, native units,
valid-point rules, minima, missing/degenerate outcomes and Shapely error handling.

Require raw observability metadata with every metric and both goalkeeper variants.
The registry retains record-based measurements and ambiguity flags, with a future
primary-comparison exclusion and unchanged-record inclusion sensitivity for
multiple/unknown actor status. This does not select a final research sample.
Preserve all raw actor records; do not silently select/deduplicate them.
No direction-dependent tactical interpretation
is permitted until orientation and role semantics are justified. Scalar within-frame
geometry must still disclose visibility/composition limitations and native axes.
Metric-specific eligibility, not `frames_joint_checks` alone, controls later use.

Explicitly **defer approval** of composite compactness, low/mid/high thresholds,
low-block classification, dangerous-space composites, full-pitch naive Voronoi,
pitch control, EPV tracking reconstruction, sequence clustering, future-xG
predictive models, Transformer, LSTM, GNN and causal claims. Faithful tracking
reconstructions and naive full-pitch control claims remain REJECT under this data
model, not merely waiting for a later phase. This task stops at documentation.

## 29. Change-control policy

The v1.0 intent is architectural stability with transparent empirical decisions.
Refactoring with identical outputs, plotting styles, bug fixes restoring documented
behavior, and threshold choices following the pre-specified calibration process
need no scientific version bump. They still require appropriate verification and
a reproducible record.

A scientific version v1.1 or higher is required for a new primary question,
materially changed study population, new primary outcome, threshold changes after
viewing effectiveness, replacing a published metric with another proxy, adding
external data to core inference, or making a high-capacity model primary.
This document records the original v1.0, completed audit amendments and the
7 September 2026 Phase 2A measurement-definition lock; it does not claim that
visibility calibration or later analytical method lock has occurred.
Future method changes must record trigger, rationale, provenance,
compatibility, validation/sensitivity and effect on prior results.

Record upstream revision and retrieval time, match IDs, package environment,
configuration, exclusions and derived-output provenance. Freeze definitions before
effectiveness evaluation. Reusable architecture is not a reason to select a method.

## 30. Primary source map

The full bibliography stays in [source_foundation.md](source_foundation.md).
This crosswalk preserves the original Methods PDF's aliases without inventing
new S-numbered sources or treating software documentation as an academic formula.

| Original PDF alias | Canonical source / retained role |
| --- | --- |
| SB-OD | S01: Open Data layout/terms/availability; PDF's older `https://github.com/statsbomb/open-data` pointer maps to the foundation's Hudl repository |
| SBPY | [Hudl StatsBombPy](https://github.com/hudl/statsbombpy): original optional public wrapper reference, superseded as implementation access layer; no S-number assigned |
| SB-LEV | S02: 34-match release; PDF's general [free-data hub](https://statsbomb.com/what-we-do/hub/free-data/) is retained as its original pointer; use S02's specific release citation |
| MPLSOCCER | Rowlinson, A., [mplsoccer documentation](https://mplsoccer.readthedocs.io/): software/visualization reference supplied by PDF; no S-number assigned |
| POS-REV | S10 for Low et al.; S09/S11 for review context and S07/S08/S12 for geometry definition/precedent |
| FERN18 | S18: Wide Open Spaces; PDF supplies an alternative [author-hosted paper](https://www.lukebornn.com/papers/fernandez_ssac_2018.pdf) |
| TANG23 | S27: 360 representation, clustering and Situational xT |
| YEUNG24 | S28: event/freeze-frame tactics; DOI `10.20965/jrm.2024.p0603` |
| FIFA-BLOCK | S05 for mid-block/compactness context, with S04 ontology and S06 operational adaptation; source-foundation link resolves the intended citation |
| FIFA-LOW | Separate PDF coaching reference: *Team organisation out of possession / low-block coaching literature*. No verified matching S-number or complete bibliographic record is supplied; not silently equated with S04/S05 |
| XT | S22: Singh xT; S23 adds Markov lineage |
| VAEP | S24: action valuation/game-state probability |
| EPV | S20: full-tracking possession value and observation-model ceiling |
| SEQ2EVENT | S26: event-sequence prediction |
| TEMPXT26 | S29: Semi-Markov temporal xT; PDF's [publisher link](https://www.nature.com/articles/s41598-026-52938-1) matches the supplied DOI |

The PDF contains no embedded hyperlink annotations. Its two printed FIFA URLs
contain typographic en dashes, so their intended literal web addresses are not
reliably established by extraction. Preserve the printed strings here without
silently replacing punctuation or inventing a bibliography entry:

```text
FIFA-BLOCK: https://www.fifatrainingcentre.com/en/fwc2022/technical-and-tactical-analysis/controlling-the-game-without-the-ball–the-mid-block-and-compactness.php
FIFA-LOW: https://www.fifatrainingcentre.com/en/game/game-analysis/out-of-possession/team-organisation–out-of-possession-.php
```

Use S05's existing source-foundation URL for the matched mid-block reference.
FIFA-LOW's exact URL/bibliographic mapping remains unresolved; no new external
verification or guessed identifier is part of this merge. Other links are retained
as supplied rather than claimed freshly verified. Method-specific sections also
reference S03, S13–S17, S19, S21, S25 and S30–S35 where their foundation roles apply.

## 31. Final methodological principle

The project's value should come from connecting established methods correctly,
not inventing complexity. The intended analytical chain is:

```text
Leverkusen action sequence + explicit timing + event-aligned visible-player geometry
    -> measured defensive structural change
    -> space made more/less exploitable
    -> next attacking actions
    -> future box entry / shot / xG
    -> recurring tactical pattern + football interpretation
```

This is a research workflow, not a causal diagram or completed result. State when
the open data lack required information. Use a simpler published metric when it
answers the question; name and validate necessary adaptations transparently.
The current work ends with the eight Phase 2A measurement definitions locked in
the registry, not analytical implementation.

## 32. Completed Phase 1/1B contract and findings

Phase 1 and Phase 1B are **COMPLETE** within their audit/diagnostic scope. Completion
does not mean every actor/orientation convention, metric eligibility or threshold
has been resolved. The following preserves existing implementation semantics and
the newer pinned findings. Detailed result tables and historical baselines remain
in the [technical appendix](../report/technical_appendix.md#phase-1b-pinned-revision-and-coordinate-semantics).

### Implemented observability definitions

`leverkusen.data.observability` implements the inventory, event/frame integrity,
visible-player counts, visible-area checks, actor consistency and grouped attrition.
The CLI writes the three Phase 1 CSVs plus three Phase 1B diagnostic CSVs. It fetches each match's events
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

### Phase 1B revision and coordinate diagnostics

The source revision is configured solely in `config/project.yaml` as
`533862946a73608c134d18b78226b6371ce7173c`, the original Leverkusen release of
May 21, 2024. All matches/events/lineups/360 URLs are built from that SHA. The
loader reads it once per Python process and rejects mutable branch names; the CLI
checks that its configuration agrees with the imported loader. Restart after a
config change. The pinned audit never uses legacy local files or mixed revisions.

This choice follows the project history investigation: later `master` returned
event/360 identifiers that were not mutually compatible in matches 3895158,
3895266 and 3895309. Pinning provides a consistent release for measurement, not
proof that all upstream data are incorrect. Rerun results and residual issues are
reported separately from the historical baseline in the technical appendix.

For a uniquely linked event and exactly one located actor, the audit computes
`actor_distance_direct = distance((x,y), actor)` and
`actor_distance_mirrored = distance((length-x,width-y), actor)`. Pitch dimensions
come from project config (120 × 80). `actor_distance` is the backward-compatible
alias for direct distance; existing statistics and review ranks remain direct.
Original coordinates are never changed, and no attacking direction is normalized.

Strict numerical comparison gives `direct_closer`, `mirrored_closer`, or
`equal_or_indeterminate`. Exact ties and missing/invalid pairs share the third
label at frame level; `actor_consistency_measurable` distinguishes them. Event-type
percentages include measurable pairs only, so their equal category contains ties.
Percentages run from 0 to 100. A closer candidate is not necessarily close in
absolute terms; neither this comparison nor an event-type majority establishes a
coordinate rule or a universal exclusion threshold.

`phase1_actor_distance_by_event_type.csv` reports direct-distance count, mean,
median, p75/p90/p95/p99 and max. `phase1_coordinate_semantics_by_event_type.csv`
reports measurable-pair counts, both medians and p95s, and percentages in the three
comparison categories. Both retain frame grain (duplicate frames would count
separately) and omit event types with no measurable pairs. No conclusions are
hard-coded for any event type.

`phase1_multiple_actor_frames.csv` retains all flagged actor locations in source
order, event location, match/event IDs, event index/type and actor count. Locations
are JSON-encoded excerpts for these exceptional frames only, not full raw event or
360 records. Missing actor locations are retained as null entries. Missing or
ambiguous event links leave event location unknown. No actor is chosen; these
frames remain excluded from single-actor distance analysis and retained in general
observability counts. Any later actor-specific use requires a justified resolution.

### Verified pinned-release results

The audit's six derived outputs under `outputs/diagnostics/` are
`phase1_match_summary.csv` (inventory and release/retrieval provenance),
`phase1_frame_summary.csv` (original frame grain and mechanical checks),
`phase1_attrition.csv` (coverage and grouped attrition),
`phase1_actor_distance_by_event_type.csv`,
`phase1_coordinate_semantics_by_event_type.csv`, and
`phase1_multiple_actor_frames.csv`. The observability notebook reads these
diagnostics and rejects cached tables from an unknown/different source revision.
They do not contain a final tactical sample or implemented team-shape metrics.

| Observation | Pinned result |
| --- | ---: |
| Unique Leverkusen matches / successful event and 360 loads | 34 |
| Event records | 137,765 |
| Frame records | 118,581 |
| Frames linked to events | 118,581 |
| Event coverage | 86.074838% (86.07% rounded) |
| Events without frames | 19,184 |
| Orphan frames / missing identifiers | 0 / 0 |
| Duplicate event IDs / frame UUIDs | 0 / 0 |
| Frames with nonempty freeze frame and valid visible polygon | 118,581 |
| Measurable single-actor pairs | 118,577 |
| Multiple-actor frames | 4 |

This pin supersedes the early mutable-`master` source assumption. Mutable branches
can change between runs and need not preserve event/360 compatibility. The
appendix records a history investigation identifying a May 26, 2026 bulk 360 update
for the incompatible matches while their events retained the original release.
This supports the observed cross-resource incompatibility, not a general claim
of upstream corruption. No history investigation or fresh fetch is repeated here.

| Previously incompatible match | Events | Pinned frames / matched events | Orphans |
| --- | ---: | ---: | ---: |
| 3895158 | 3,866 | 3,312 | 0 |
| 3895266 | 4,104 | 3,623 | 0 |
| 3895309 | 3,890 | 3,252 | 0 |

The three matches recovered complete frame-to-event compatibility, not complete
event coverage. The pinned release has 26 fewer frames than the historical
118,607-frame release; coverage gains cannot be obtained by adding its 10,213
orphans to the old 108,394 linked events. No UUID mapping, match-specific fallback,
raw cache, heuristic relinking or cross-revision mixing was used. Historical
visibility distributions and unpinned percentages in the appendix remain labeled
historical rather than being asserted as fresh pinned estimates.

### Coordinate findings and practical limits

Pass, Carry, Shot and Pressure predominantly favor direct coordinates. Their
direct-distance tails still matter: recorded maxima are 7.592760, 110.675243,
0.000003 and 48.200934 native units respectively. A direct majority is not a
blanket eligibility guarantee.

Dribbled Past favors the mirror in 100.000% of measurable pairs; Dispossessed in
97.348% and Foul Won in 96.825%. Mirrored medians remain 1.436289, 0.983314 and
1.127998 units respectively, so mirroring is not exact reconciliation. Ball Receipt*
(11.555% mirrored closer), Dribble (41.915%), Duel (44.51% as reported in the
appendix) and 50/50 (evenly divided) have mixed behavior. These findings require
event-type and paired/opposing semantics review; they do not justify whole-type
rotation, automatic correction or direction-dependent tactical interpretation.

Among measurable pairs, 111,733 are `direct_closer`, 6,813 `mirrored_closer`, and
31 exact ties. The four unmeasurable multiple-actor frames also have
`equal_or_indeterminate` but are excluded from percentage denominators. Taking the
smaller diagnostic distance leaves p95 0.711686, p99 7.424444 and maximum 48.855398.
Neither hypothesis explains all discrepancies; selecting the minimum is neither
a transformed dataset nor an exclusion rule.

### Multiple actors and Phase 2A implications

Four frames in match 3895139 contain two identical actor locations within each
pair: event indices 541 (Pass), 798 (Dispossessed), 1978 (Pass), and 2036
(Ball Receipt*). The appendix retains their UUIDs; the diagnostic CSV keeps both
actor records and the linked event location. Identical coordinates do not prove
whether they represent one player or two. Both records remain retained: no actor
selection, inferred identity or deduplication was performed. Single-actor
diagnostics exclude them, general observability counts retain them, and future
actor-specific analysis requires exclusion until independently justified resolution.
Player-count-sensitive geometry must explicitly account for this unresolved issue.

All 34 matches now have compatible IDs, supporting preparation for basic
within-frame visible-player geometry. Residual mismatches, multiple actors,
goalkeeper inclusion, incomplete/changing visibility and selection sensitivity
remain limitations. Event-specific coordinate/actor/role semantics must be
justified before combining direction-dependent event and frame geometry. No
universal actor-distance or visibility threshold, normalized direction, final
usable sample or Phase 2 metric is established by the audit.

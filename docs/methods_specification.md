# Creating Space Under Xabi Alonso — Methods & Data Specification

Bayer Leverkusen 2023/24 Spatial-Sequence Analysis.

**Current status: Phase 2B = LOCKED / COMPLETE — human approval, 9 September 2026. Phase 2A basic geometry remains LOCKED / IMPLEMENTED.**
**10 September 2026 human approval: Phase 2C = LOCKED / COMPLETE — RESTRICTED
SEMANTIC SCOPE. Section 40 records the approved boundary. Phase 3 — Possession
and Spatial-Sequence Method Design is now authorized within that scope.**
**Phase 3A-1 = DIAGNOSTIC / NOT A METHOD LOCK.** Section 41 records the completed
progression/reset diagnostics and the next Phase 3A-2 review step.
The 7 September 2026 [Phase 2A registry contract](metric_registry.md#1-shared-phase-2a-measurement-contract)
freezes eight within-frame metrics, subsets, goalkeeper variants and edge cases.
It supersedes earlier pending-definition wording for those eight measurements;
Phase 2B eligibility and sensitivity calibration is now locked in section 37.
Later method definitions remain open. The eight locked geometry
families are now implemented and tested without a method change. Direction
normalization is locked only within the validated Phase 2C population; tactical
classifiers, pattern discovery and predictive models remain deferred. The next
gate is **possession and spatial-sequence method design**. Section 33 records
the geometry implementation boundary; sections 28 and 40 control the current
roadmap. Tactical interpretation and outcomes still require later method review.

Document lineage: original *Methods & Data Specification v1.0*, September 2026
(26-page supplied PDF), merged with the repository's completed Phase 1/1B work and
current source foundation on 7 September 2026. This is the current methodology
contract, with the original 31 major section numbers retained for traceability.
Sections 32–36 retain dated historical evidence, including pre-approval proposals.
Section 37 supersedes their pending calibration wording; unselected candidates
remain candidates. Other proposed, optional or deferred methods remain unapproved.
Sections 38–39 retain the initial Phase 2C findings and Phase 2C-2 recommendation
as dated history; section 40 supersedes their pending-lock status only, preserving
the semantic gates, empirical evidence and unresolved full-sample limitations.
Phase 1/1B results below are preserved from the technical appendix; Phase 2A
implementation diagnostics are recorded separately in section 33 and the appendix.

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
| Phase 1 audit still pending / UUID cause unresolved | Phase 1/1B complete; pinned release has zero orphan frames. Phase 2B comparison eligibility and restricted Phase 2C semantics are locked; Phase 3 sequence-method design is now authorized (section 40) |
| Academic sources unavailable at migration | S01–S35 are synchronized in the source foundation; exact adaptations still require method review |
| Broad Phase 2 included zones and clipped Voronoi | Initial Phase 2A implements the locked basic within-frame geometry; zones/Voronoi and tactical interpretation remain later work |
| PDF ADOPT labels for all-pairs mean, and DERIVE labels for proximity/overload | Current registry preserves published base geometry versus PROJECT aggregation/eligibility/radius; PDF labels alone do not establish an exact published formula |
| PDF “Phase 0” calibration and example windows | Phase 2B calibration is locked; visibility nulls mean no universal hard cutoff approved. Later sequence/outcome windows remain uncalibrated and null |

The PDF's recommended layout/loader signatures and source aliases are mapped to
current repository equivalents in sections 24, 25 and 30 rather than silently
treated as existing code. No historical appendix finding is removed.

## 2. Locked research scope

### Primary research question

> How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24 Bundesliga season, and which recurring attacking sequences were most effective against different defensive structures?

### Operational analytical formulation — locked scope

> How did Bayer Leverkusen’s attacking sequences alter the event-aligned visible spatial structure around possession, and which recurring structural changes preceded dangerous attacking outcomes?

The first is the football-facing primary question; this second formulation states
what event + 360 observations can directly support. Both are retained. Changes
and temporal precedence describe observed states, not causal attribution.

### Supporting questions

The current [research questions](research_questions.md) control numbering:

1. What recurring attacking spatial patterns characterized Leverkusen's possession play?
2. How did observed spatial structure change during those patterns, using visible width/depth, observed outfield convex-hull footprint, spacing and relevant local context after team/role validation?
3. Which attacking patterns preceded structural changes associated with dangerous attacking outcomes, without requiring a valuable-space composite?
4. Which resulting spatial changes were associated with the greatest subsequent chance quality?
5. If a separately justified defensive-regime method is validated, how did effectiveness differ across high, mid and deep observed defensive structures?
6. Conditional on that optional validation, which patterns against deep observed structures preceded spatial openings and dangerous outcomes?
7. At which observed event-aligned states did structural changes occur in successful sequences?
8. Which player actions were most involved in producing those changes?
9. How sensitive are results to observational support, approved Phase 2B robustness challenges, keeper convention and sequence-window definitions, plus regime definitions if that optional method is used?

Question numbers are preserved for registry references. The PDF's broader aims
are narrowed to observed states; inferred lines, regimes and composites are
optional gates, not required answers. Named attribution is restricted to identified
event actors. Spatial-state history describes observations, not continuous motion.

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
| Shapely | Implemented visible-polygon validity, pitch intersection and Phase 2A convex hulls; future clipping |
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
| `frame_geometry` | One original frame record × literal subset × goalkeeper policy | Implemented Phase 2A diagnostic source with original frame ordinal, quality metadata and per-metric statuses; no final eligibility decision |
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

**Phase 2B D-primary is LOCKED:** the metric's existing status must be `ok` and
actor status must be `single` or `none`. There is no universal minimum n or
visible-area fraction, automatic OOB exclusion, hard polygon-containment rule or
edge-distance cutoff. Polygon validity/consistency and continuous boundary
distances remain diagnostic metadata; they do not automatically gate Phase 2A
comparison eligibility. No filtering is added to the measurement layer.

Primary eligibility does not permit naive pooling. Every later structural
comparison must inspect and report selected valid-player count, visible-area
fraction, subset, keeper policy, whole-frame OOB/coincidence flags and actor status.
Keep original frame identity, join status and missingness as additional context.
Materially different observation populations require an explicitly documented
common-support restriction, stratification, matched descriptive comparison or
statistical adjustment. **No specific adjustment or weighting method is selected.**

Event-integrated and actor-dependent methods require their own validated join,
team/role and coordinate semantics. Actor-dependent work requires `single` and a
unique event join; that condition alone does not validate actor alignment. No
unseen player, complete team structure or true controlled space is established by
these gates. Section 37 states the approved keeper and robustness conventions;
section 32 retains exact historical audit definitions.

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
| Convex hull footprint | Observed outfield convex-hull footprint when keeper excluded; secondary observation-sensitive structure, not controlled space; S07/S08; locked mathematical conditions unchanged |
| Mean pairwise/interpersonal distance | Mean over unordered selected pairs; S07 supports base distance, registry aggregation remains explicit PROJECT/DERIVE |
| Stretch index | Mean observed-player distance from centroid; S07/S12; component choices require review |
| Nearest-opponent distance (later) | Actor/ball, receiver-endpoint or zone-center proximity remains deferred; S07 base distance, S21 precedent. Phase 2A within-subset nearest-neighbor spacing is a separate PROJECT/DERIVE summary |
| Local numerical balance / overload / density | Attacking minus defending presence around target/radius; neighborhood and radius are PROJECT, pre-registered sensitivity choices |
| Zone occupation | Counts/shares in geometric central lane, half-spaces, wide lanes, penalty area and other declared zones; PROJECT boundaries fixed before outcomes |

This table retains the original broader plan. For the eight Phase 2A metrics,
the registry now locks `all_visible`, literal `teammate=True` and `teammate=False`
subsets with both keeper policies; no global attacker/defender mapping is required
or inferred. Audit record counts remain separate from the implemented Phase 2A
valid-point count and geometry outputs.
Median pairwise distance and mean within-subset nearest-neighbor spacing are now
locked PROJECT/DERIVE aggregations without invented published attribution.
The PDF's blanket ADOPT/DERIVE labels do not supersede current registry provenance,
especially for aggregates, proximity selection and local balance.

## 13. Voronoi and visible-space geometry — deferred

**OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION.** Apply section 37's five
admission conditions before considering the retained method options below.

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

**OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION.** Neither high/mid/deep
classification nor a compactness composite is a mandatory phase. The following
design options apply only if section 37's admission conditions are met.

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

**OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION.** Inferred lines are not
required for the core event-aligned spatial-state analysis.

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

## 16. Event-aligned spatial-state sequence features — planned

Use spatial-state history or spatial-state change for an event-state sequence.
The legacy `sequences/trajectories.py` namespace has that restricted meaning; it
does not authorize continuous movement or named off-ball trajectory claims.
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

**OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION.** The original stages below
are design alternatives if justified, not a required progression to a composite.

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

The core goal is recurring interpretable sequence mechanisms. Clustering, graph
representations and learned spatial representations are **OPTIONAL — REQUIRES
METHOD-SPECIFIC JUSTIFICATION** under section 37. The choices below are not a
mandatory escalation ladder; simpler descriptive mechanisms may be sufficient.

1. Football-defined descriptive patterns: transparent rules as baselines and
   interpretation aids.
2. Optional spatial-state sequence clustering: standardized possession/sub-sequence event and
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
| D: spatial-state history | Add changes/summaries of prior observed spatial states |

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
  context. Apply the approved Phase 2B keeper, OOB and multiplicity robustness
  plan and inspect observational support; polygon/edge metadata introduce no
  threshold gate. Sequence windows/outcome horizons need later sensitivity plans.
  Regimes and composites require such checks only if their optional gates pass.
- Distinguish exploratory from confirmatory findings under many patterns/subgroups;
  do not present the largest discovered difference as pre-specified evidence.
- Use “associated with,” “preceded,” “co-occurred with” or “was followed by.” Pattern
  discovery alone does not establish that an attacking action caused a defensive
  response; causal claims remain outside the current design.

No predictive/clustering validation has been performed. The completed audit's
mechanical verification and the later analytical validation requirements are distinct.

## 23. Analytical outputs — planned

After semantics and sequence/outcome gates, prioritize observed spatial-state
sequences and recurring interpretable attacking mechanisms. Pattern cards should
show a football-readable name assigned after inspection, frequency, representative
sequence, start/end observed geometry, spatial-state changes, box-entry/shot rates,
future xG and uncertainty under approved outcome definitions. Report observational
support and robustness alongside those comparisons. Opponent labeling requires
validated team semantics. Regime distributions or inferred response subtypes are
optional additions only after method-specific justification and validation; the
core article must not depend on classifying high/mid/deep regimes. No causal
attribution or continuous spatial trajectory is implied.

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
| Basic geometry and descriptive diagnostics; future visibility/zones/Voronoi | `src/leverkusen/spatial/geometry.py` and `diagnostics.py` implemented; normalization and later spatial metrics remain deferred |
| Future possessions/trajectories/outcomes | `src/leverkusen/sequences/` |
| Future regimes/patterns/clustering | `src/leverkusen/tactics/` |
| Future modeling/validation | `src/leverkusen/models/` |
| Future pitch/sequence/results figures | `src/leverkusen/visualization/` |
| Tests | Offline loader/transform/observability/orientation and Phase 2A geometry/integration tests; sequence tests remain a scaffold |
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
| Finite supplied coordinates and nominal bounds flags | Phase 2B retains finite OOB coordinates in primary observations; whole-frame OOB-B is routine headline sensitivity, without tolerance or repair |
| Visible polygons valid or flagged | Topology validation implemented; PDF's “repairable” option is superseded by no automatic repair |
| Shot xG present where expected | Must be asserted before future outcome construction; not established merely by overall event/frame counts |
| Coordinate/orientation sanity checks pass or flagged | Direct/mirrored diagnostics implemented; no coordinate rule or normalization is validated by a closer comparison |

Required schema failure should stop dependent analytical work early. The existing
audit itself retains malformed/ambiguous inputs as diagnostics where possible;
that is not permission to coerce them into geometry. Phase 2A geometry tests now
exercise these boundaries; future sequence tests must test their actual implementation.

The appendix records 119 offline tests, Ruff and the full pinned live CLI passing
for Phase 1B, with all six derived CSVs and unchanged raw inventory/null calibration.
Earlier migration/Phase 1 checks (44/86 offline tests and their other checks) remain
historical evidence in the appendix. This documentation merge does not rerun the
analytical suite or remeasure the data.

## 27. Calibration tasks — fixed before substantive results

Phase 2B completed the pre-specified pre-outcome calibration process and is
**LOCKED / COMPLETE** (section 37). D-primary deliberately has no universal n,
coverage, polygon-containment or edge-distance cutoff. Metric-specific q25/q05
landmarks are fixed sensitivity challenges only, not definitions of valid frames.

In `config/visibility.yaml`, null now means **no universal hard cutoff approved**;
it does not mean zero or calibration pending. `exclude_edge_sensitive_frames:
false` records the deliberate absence of automatic edge exclusion. YAML values
are preserved; only their explanatory comments change. Outcome-window nulls in
other configuration files still mean those later definitions are uncalibrated.

Before later analysis, define team/role and orientation semantics, possession and
sequence eligibility, common observational support strategy, action/time windows,
success/failure outcomes and future horizons. Optional spatial methods need their
own justification and calibration if pursued. Zones, radii, regimes and line
inference are not mandatory preconditions to the core descriptive sequence study.
Provisional `zones.yaml` rectangles assume increasing-x attack and remain unusable
for tactical interpretation until orientation is validated. Choose no later
threshold or adjustment method in this lock.

## 28. Analysis phases and immediate Phase 2A boundary

**Roadmap updated on 10 September 2026 after restricted Phase 2C approval.**
The newly authorized Phase 3 is possession/spatial-sequence method design. The
older numerical roadmap is retained with explicit legacy labels where needed;
the old optional defensive-regime phase 3 is not the newly authorized Phase 3.

| Phase | Current status / intended work |
| --- | --- |
| 1: data and observability audit | **COMPLETE**: coverage, counts, joins, visible-player/area diagnostics, missingness and actor-coordinate checks |
| 1B: revision pinning and coordinate semantics | **COMPLETE**: immutable source, compatible pinned joins, diagnostic hypotheses and multiple-actor findings; semantics are not universally resolved |
| 2A: basic within-frame visible-player geometry | **LOCKED / IMPLEMENTED.** Formulas, units, mathematical minima, record handling and six variants unchanged |
| 2B: observation validation and calibration | **LOCKED / COMPLETE.** Count/coverage/keeper sensitivity, observation quality, representative review and human-approved calibration |
| 2C: team/role semantics and attacking orientation | **LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE**, unchanged frame gates; unsupported observations remain unresolved |
| 2C-2: sequence-readiness audit | **COMPLETE — READY — WITH RESTRICTIONS**; empirical coverage inventory, no sequence thresholds |
| 3: possession and spatial-sequence method design | **AUTHORIZED** for validated spatial-anchor sequence analysis; complete provider event context, validated states and Phase 2B comparison support remain separate |
| Legacy 4: sequence construction | After Phase 3 method review: implement approved possession/state sequences; no final dataset is constructed by this lock |
| 5: descriptive spatial evolution | Next: descriptive spatial-state change with common observational support |
| 7: outcome definitions and descriptive comparisons | Next: lock success/failure definitions, then compare observed spatial evolution preceding box entries, shots and future xG |
| 6: recurring interpretable sequence mechanisms | Next: football-readable descriptive mechanisms; clustering or learned representations are optional |
| Legacy 3: defensive regime characterization | **OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION**; separate from current Phase 3; no automatic high/mid/deep classification |
| Advanced spatial options | Inferred lines, compactness, Voronoi, valuable-space composites, graphs and learned representations are optional gates under section 37 |
| 8: predictive incremental-value test | Secondary and unapproved; only after a separate need and method definition |
| 9: technical article synthesis | Later: pair statistical results with football-readable sequences and inference limits |

Phase 2A locked metrics are visible player count, centroid, visible width, visible
depth, convex hull area, mean pairwise distance, median pairwise distance and
nearest-neighbor spacing (mean of each record's nearest other record in its subset).
Audit counts retain their original semantics; the Phase 2A geometry layer now
implements the [locked registry](metric_registry.md#2-locked-phase-2a-metric-rows), which
specifies exact formulas/provenance, six subset/keeper combinations, native units,
valid-point rules, minima, missing/degenerate outcomes and Shapely error handling.

Require raw observability metadata with every metric and both goalkeeper variants.
The registry retains record-based measurements and ambiguity flags. Phase 2B now
locks the primary-comparison exclusion and unchanged-record inclusion sensitivity
for multiple/unknown actor status. A comparison still needs its specific common
observational support assessment; eligibility does not certify naive pooling.
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
model, not merely waiting for a later phase. Current implementation stops at the
eight basic geometry families and descriptive diagnostics.

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
This document records the original v1.0, completed audit amendments, the
7 September 2026 Phase 2A measurement-definition lock and the **9 September 2026
human-approved Phase 2B lock and research-scope realignment**. This is **not a
scientific version bump**: no research population or outcome changed after
effectiveness analysis; calibration followed the pre-specified validation process;
and interpretation was narrowed to the actual observation model before any
tactical/outcome analysis. The football-facing primary question is preserved.
No downstream sequence, outcome, adjustment or tactical method is approved here.
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
The current implementation ends with the eight locked Phase 2A measurement
families and descriptive validation, with later analytical methods still deferred.

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

## 33. Phase 2A implementation and descriptive execution

Implemented on 7 September 2026 against the frozen registry, with no change to its
eight metric rows beyond implementation status. The complete formulas, units,
minima, subset/keeper filters, numerical status rules and actor ambiguity policy
were compared with the pre-implementation Git version and remained identical.
No scientific method revision or calibration threshold was introduced.

`src/leverkusen/spatial/geometry.py` provides `valid_point`, `measure_points`,
`frame_geometry` and `build_frame_geometry`. The frame builder uses unique
match-local event metadata and preserves the zero-based original frame ordinal.
It returns six wide rows per original frame, including known-empty and unavailable
containers, with nine numeric outputs, per-output status and mandatory context.
No frames are invented for missing 360 resources or events without frames.
Phase 1 observability semantics remain unchanged; polygon inspection is reused.

`src/leverkusen/spatial/diagnostics.py` and `scripts/geometry_diagnostics.py`
produce the derived frame table, match inventory, availability/status summaries,
histograms, exact-n strata, paired keeper sensitivity and anomaly counts.
`src/leverkusen/visualization/geometry.py` renders the three diagnostic figures;
`notebooks/03_spatial_geometry.ipynb` presents those package results.

The pinned execution loaded all 34 matches and measured 118,581 original frames,
producing **711,486 rows**, exactly six per frame. All Phase 1 frame IDs, raw record
counts, actor counts and visible-area fractions agreed exactly. The notebook
executed all five code cells and saved three figures. Verification passed
**194 offline tests** (two network tests deselected), Ruff and full-table
grain/schema/status checks. Raw-file and configuration hashes remained unchanged.

These are all-row descriptive implementation diagnostics, retaining multiple actors,
coincidences and finite out-of-bounds points with flags. They do not constitute a
primary analytical comparison or final eligible research sample. The appendix
records availability, keeper effects and anomalies:
[Phase 2A implementation and initial diagnostics](../report/technical_appendix.md#phase-2a-implementation-and-initial-diagnostics).

The implementation is ready for empirical geometry validation. Representative-frame
review, visibility/edge calibration, unresolved record identity and direction/role
semantics remain open. Later geometry, sequences, outcome models and tactical
interpretation are not implemented by this phase.

## 34. Phase 2B-1 descriptive observation sensitivity

Completed on 7 September 2026 using the existing Phase 2A frame-variant table,
without geometry recomputation. Six existing geometry metrics are summarized by
exact selected valid-point count and shared visible-area quintiles, separately
for all three literal subsets and both keeper policies. Coverage bins weight
each original frame once, retain ties and represent missing coverage separately;
they are descriptive grouping boundaries with no eligibility meaning.

Keeper differences pair the same original frame and subset, using jointly defined
values. All-frame and actual-keeper-removal scopes have explicit denominators;
unknown keeper omissions are reported separately. Standard deviations use ddof=1,
quantiles use pandas linear interpolation, and undefined metrics remain NA.
All recorded frame-quality flags are retained in this diagnostic population.

The notebook adds exactly three sensitivity figures with compact supporting tables.
Results and verification are recorded in the
[Phase 2B-1 appendix](../report/technical_appendix.md#phase-2b-1--observation-sensitivity-diagnostics).
The evidence is ready for human review before calibration. No formula, provenance,
visibility threshold, keeper convention or configuration value changed. Detailed
boundary/edge, out-of-bounds, coincidence, representative-frame and orientation
work remains deferred, as do all tactical and later analytical methods.

## 35. Phase 2B-2 observation quality and edge validation

This empirical diagnostic phase adds point/polygon boundary checks and deterministic
frame review to the locked Phase 2A observations. It uses the existing derived
geometry CSV and retrieves each match's 360 records once, in memory, through the
unchanged revision-pinned loader. Original frame ordinals, event IDs, selected
counts and visible-area fractions must agree with Phase 2A. The source CSV hash,
revision and retrieval inventory accompany the outputs. No raw frame/JSON cache
is created; a bounded representative candidate pool stays in memory for plotting.

The reusable implementation is `src/leverkusen/spatial/observation_quality.py`;
run `python scripts/observation_quality.py` and review the Phase 2B-2 notebook
section, compact `outputs/diagnostics/phase2b2_*.csv` tables and
`outputs/figures/phase2b2_*.png` figures. Generated outputs remain ignored by Git.

### Diagnostic definitions and denominators

- Out-of-bounds means any strict violation of x=0, x=120, y=0 or y=80 by a finite
  supplied point. Axis excursions are `max(0,-x,x-120)` and `max(0,-y,y-80)`;
  distance to the nominal rectangle is their Euclidean norm. Exact boundary
  points have zero excursion. No tolerance, rounding or coordinate change applies.
  Record-weighted excursion quantiles describe severity; affected frame/match
  counts are separately deduplicated by identifiers, never by player coordinates.
- Valid polygons reuse the Phase 1 inspector without repair. Report pitch coverage,
  intersection with the pitch boundary, containment, original area inside/outside
  the pitch and outside area divided by original polygon area. Existing
  `visible_area_fraction` remains intersection area divided by 9,600. Intersection
  and difference are diagnostic geometries, not replacement polygons.
- Point statuses are mutually exclusive `inside` (strict), `boundary` (covered
  but not inside) and `outside`; `polygon_covered` includes inside and boundary.
  Invalid/missing polygons have unavailable statuses/distances, not zero distances.
  Boundary distances are unsigned Euclidean distances in native units, including
  points outside the polygon; those points are counted separately.
- For every variant, retain all indices tied at min/max x/y. The named scalar
  extreme-edge measure is the minimum boundary distance among tied defining
  records; a supplemental table preserves every tied record's distance. This
  avoids silently choosing a record. Minimum/median selected distances retain
  record multiplicity. Empty selected sets have unavailable edge measures.
- Metric/edge relationships use five empirical quantile bins separately for each
  variant and edge measure. Intervals are right closed with the minimum included;
  duplicate edges collapse, equal values stay together and missing distances are
  reported separately. Bin edges, inventories, defined metric denominators,
  metric summaries, median n and median coverage are explicit. Quantiles use
  pandas linear interpolation. No bin is an eligibility rule or censoring label.
- Extreme-tail tables use observed lower/upper one-percent metric quantiles within
  each variant, retaining all ties. All-defined baselines allow comparison of n,
  coverage, continuous edge distances, out-of-bounds, keeper presence, coincident
  records, multiple actors and points outside the supplied polygon. These are
  marginal descriptions, without causal or independently adjusted interpretation.

### Record multiplicity and deterministic visual review

Exact-coordinate coincidence groups preserve original record indices, flag
inventories and excess-record counts. To empirically test metric sensitivity
without deduplicating anything, a separate counterfactual adds one record at each
already-coincident selected location in turn. It applies the unchanged locked
measurement function and reports added-minus-original values/statuses for all
nine numeric outputs. It is a local multiplicity perturbation, not an estimate
of actual identity error or a replacement for any Phase 2A observation. All four
multiple-actor frames retain every record; actor-coordinate pair distances and
literal teammate/keeper flags are reviewed without resolving identity. Actor flags
alone are not a numerical input to these geometry formulas.

Representative selection is deterministic: largest axis excursions, smallest
positive excursion, largest excursion on each observed pitch side, minimum/median/
maximum coverage, minimum/maximum all-visible count, minimum/maximum of five major
metrics among defined-hull observations, largest absolute paired keeper changes
in depth/hull/centroid x, every multiple-actor frame, and the first three distinct
event-type examples with coincidence and at most one actor. Ties resolve by match
ID, original frame ordinal, literal subset and keeper policy. A frame can satisfy
several rules. The defined-hull preference applies only to representative metric
plots; low-count/undefined geometry remains in the summaries and count examples.

Contact sheets show native provider x/y axes, the nominal pitch, unmodified visible
polygon, every finite player point, literal teammate flags, keeper/actor markers,
out-of-bounds rings, multiplicity labels and the selected convex hull. Axis limits
include outside points and polygon vertices. No mirroring, direction inference,
identity mapping, tactical zones or formation interpretation is introduced.

**EMPIRICAL FINDING:** Results and visual-review observations are recorded in the
[Phase 2B-2 appendix](../report/technical_appendix.md#phase-2b-2--observation-quality-and-edge-validation).

**METHODOLOGICAL DECISION:** None selected. Phase 2A formulas/provenance, source
revision, raw-loading behavior, all calibration YAML values, goalkeeper preference
and eligibility rules remain unchanged. Human review of calibration is the next
permitted phase; orientation and all later analytical methods remain deferred.

## 36. Phase 2B-3 eligibility and goalkeeper calibration candidates

**Historical candidate evaluation, before human approval on 9 September 2026.**
The evidence and alternative rules below are retained for traceability. Section 37
now controls the approved primary/sensitivity rules and scope. In particular it
requires routine OOB-B for headline findings, fixes the outfield keeper convention,
and leaves the common-support comparison strategy to a later explicit method.

**PROPOSED — REQUIRES HUMAN APPROVAL.** This section records reviewable
alternatives, not an adopted eligibility contract. Configuration, the metric
registry, source revision, Phase 2A measurements and their formulas are unchanged.
Run `python scripts/calibration.py` to evaluate the existing derived CSV offline;
the runner checks its hash against both preceding diagnostic runs and records
the hashes of all Phase 2B-1/2 evidence tables. It neither retrieves raw data nor
persists coordinates, frame records or eligible-frame lists. Only aggregate
candidate summaries are saved under `outputs/diagnostics/phase2b3_*.csv`.

The main review artifact is the
[metric calibration matrix](phase2b3_metric_calibration_matrix.csv), reproduced
as `outputs/diagnostics/phase2b3_metric_calibration_matrix.csv` and in the final
notebook section. The [technical appendix](../report/technical_appendix.md#phase-2b-3--human-reviewable-calibration-candidates)
contains measured retention, distribution shifts, stability and composition.
These are PROJECT eligibility candidates informed by empirical diagnostics, not
published cutoffs or causal results.

### Candidate definitions and why these landmarks

Twenty named alternatives cover five strategies plus explicit paired OOB,
coincidence and actor treatments. Every alternative first requires that the
particular metric's existing status is `ok`; there is no common hull-validity
gate suppressing another metric. Centroid components retain their shared status.

| Strategy | Candidate rule and purpose |
| --- | --- |
| A | Every mathematically defined metric; no visibility or anomaly exclusion. Permissive diagnostic baseline and ambiguity-inclusion alternative. |
| B | `n >= q05`, `q25`, `q50`, or `q75`, separately for each literal subset and keeper variant. These sample the lower tail and the central distribution landmarks already examined in Phase 2B-1. |
| C | Coverage `>= q20`, `q40`, `q60`, or `q80` across original frames, using the existing Phase 2B-1 quintile boundaries. |
| D primary | Metric status `ok` and actor status `single` or `none`; no extra count, coverage, OOB or coincidence exclusion. Preserve the registry's later primary-comparison ambiguity policy. |
| D sensitivity | D primary plus metric-specific count/anomaly checks listed below. No hard coverage gate. |
| E | D primary plus count q25/coverage q20, or count q50/coverage q40, excluding whole-frame OOB and coincidence. Conservative comparisons, not preferred defaults. |

Count quantiles use the observed integer value at pandas `higher` interpolation;
coverage quantiles use linear interpolation with each original frame weighted once.
Both comparisons are inclusive (`>=`); all ties remain together. Consequently C
retention is not exactly the complement of the earlier right-closed bins. Missing
coverage fails C/E, but remains flagged and eligible under A/D if the metric is
defined. A missing anomaly inventory fails only a requested anomaly check. All
unknowns and exclusions remain declared, without imputing observations.

| Variant | n q05 | n q25 | n q50 | n q75 |
| --- | ---: | ---: | ---: | ---: |
| all_visible / included | 11 | 14 | 17 | 19 |
| all_visible / excluded | 10 | 14 | 17 | 19 |
| teammate_true / included | 5 | 7 | 8 | 10 |
| teammate_true / excluded | 5 | 7 | 8 | 9 |
| teammate_false / included | 4 | 7 | 9 | 10 |
| teammate_false / excluded | 4 | 7 | 9 | 10 |

Coverage landmarks are approximately **0.216822584412, 0.265017325037,
0.318401586888 and 0.383158787876**; use full precision in
`phase2b3_empirical_thresholds.csv`, not these display-rounded values. Exact-n
support, observations below/at each threshold, and joint count/coverage strata
are supplied. Threshold selection does not use metric values or an outcome.
The subsequent stability results do not identify a common plateau: these
landmarks remain comparison candidates, not validated minimum sample sizes.

### Exact proposed primary, sensitivity and metadata treatments

**Primary proposal:** D primary for descriptive comparisons of observed geometry,
with the literal subset and intended keeper population declared. Retain all
mathematically eligible values without a universal count/coverage threshold.
This is conditional on reporting count and coverage alongside comparisons:
nearest-neighbor comparisons should use exact selected-n strata and shared
coverage quintiles; hull comparisons must also disclose joint count/coverage
support. Do not present an unadjusted pooled comparison across different
observation populations as a structural difference. Where strata have no common
support, report the comparison as unsupported. The later analysis must declare
its contrasts, support and weighting before any outcome analysis; no minimum
stratum size, covariate model or weight is approved by this calibration.

**Metric-specific sensitivity proposal (D sensitivity):**

- Count and centroid: exclude whole frames with any coincident records.
- Width: exclude whole frames with any nominal-pitch OOB point.
- Depth: retain D primary eligibility; prioritize the included/excluded keeper
  pair as its sensitivity. Broad OOB-B remains an additional comparison.
- Hull: require n at least the variant's q25 (14 all-visible, 7 either teammate
  subset) and exclude whole-frame OOB. q25 is a lower-quartile support landmark
  used to challenge this especially n-sensitive quantity, not a stability lock.
- Mean pairwise distance: exclude whole-frame OOB and coincidence.
- Median pairwise distance: exclude whole-frame coincidence; test OOB separately.
- Mean nearest-neighbor distance: require n at least q05 (included/excluded
  all-visible 11/10; teammate_true 5; teammate_false 4) and exclude whole-frame
  coincidence. This challenges sparse endpoints while retaining most observations;
  it does not make NN comparable across unequal n or verify unseen neighbors.

Report the individual B, C, OOB and coincidence comparisons as well as D/E, so
offsetting changes in a combination are not mistaken for robustness. The q05/q25
choice for these different sensitivities is a reviewable methodological judgment
about coverage cost and observed sensitivity, not an automatically inferred optimum.

**Goalkeeper proposal:** use `excluded` (literal keeper=False) for observed
outfield centroid, depth, hull and outfield spacing; width may use either
convention empirically, with excluded preferred when paired with other outfield
shape quantities. Use included for an explicitly named full visible footprint,
and always preserve both count inventories. The all-visible cloud combines both
literal teammate subsets and must never be called one team's shape. Keeper
pairing uses the same original frame/subset and jointly defined values; report
the loss of definition as well as actual-removal and all-frame deltas. Unknown
keeper omissions remain separate (zero in the current sample). This choice is
about the represented population, not minimizing variance.

**OOB proposal:** OOB-A and OOB-B/C primary all retain supplied finite values with
flags. OOB-B sensitivity excludes any affected original frame for every metric;
OOB-C sensitivity does so only for width, hull and mean pairwise distance, whose
upper tails showed OOB enrichment. The latter is prioritization, not evidence
that other metrics are immune. No clipping, projection, point-only deletion,
repair, rescaling or coordinate transformation is allowed.

**Metadata-only:** supplied-polygon inconsistency and continuous boundary
proximity never gate eligibility here. All 118,581 polygons were valid and
pitch-contained, yet 20,582 frames had points outside their polygon; containment
cannot certify observation validity. Preserve the existing flags/edge summaries
for later sensitivity/stratification. Full-population point/polygon flags are
not newly reconstructed because Phase 2B-2 persisted aggregate edge outputs.

**Coincidence/actor proposal:** preserve every record. Exclude coincident frames
only in multiplicity-sensitive robustness checks, never by deduplication. The
four multiple-actor frames remain included in generic diagnostic geometry (A).
For later primary comparisons retain the registry's exclusion of `multiple` and
`unknown`, with A as unchanged inclusion sensitivity. Generic-geometry inclusion
in a primary comparison would require an explicit registry policy revision;
this task does not make that revision. Actor-dependent work additionally requires
`single` and a unique event join (`actor_unique` candidate); this is necessary,
not sufficient to approve actor alignment or identity-dependent analyses.

### Human approval and remaining boundaries

The evidence favors a **combination**: metric-specific mathematical availability,
the existing comparison ambiguity rule, analysis-specific common observation
support, and sensitivity-only count/coverage/anomaly restrictions. A single global
visibility gate discards unequal portions of event and match populations without
certifying the remaining full-team geometry. No statistical stability tolerance
or causal explanation is claimed.

Human review must approve the represented keeper population, D primary and its
analysis-specific comparison conditions, the exact D sensitivity thresholds,
OOB-C priorities versus routine OOB-B, and whether the existing actor-ambiguity
comparison rule should ever be revised. Any future operationalization requires
a separate explicit approval and method change. Section 10's eventual join,
polygon and actor-alignment requirements for integrated event analyses remain
open; D is not permission to bypass them. No tactical analysis is started.

## 37. Human-approved Phase 2B lock and operational research scope

**Phase 2B = LOCKED / COMPLETE — 9 September 2026.** Human methodological review
approves the following contract. It supersedes the pending recommendations in
section 36, the earlier Phase 2B appendix sections and saved candidate notebook
outputs. Unselected B/C/E alternatives remain historical comparison evidence;
they are not all promoted to approved primary filters. The current
[calibration matrix](phase2b3_metric_calibration_matrix.csv) records the lock.

### Observation model, terminology and intended analytical chain — LOCKED

StatsBomb 360 supplies **event-aligned partial spatial observations**. It does
not supply continuous tracking, complete 22-player states, named off-ball
trajectories, continuous team-shape reconstruction, true controlled space, true
pitch control or continuous movement trajectories. Future claims must use
**observed spatial structure**, **visible outfield structure**, **event-aligned
spatial state**, **spatial-state change**, **visible width/depth**, and **observed
outfield convex-hull footprint** as appropriate.

Do not claim “true team width,” “complete defensive shape,” “actual occupied
area,” “reconstructed tracking,” “player trajectories from 360” or “true pitch
control” without independently supported later justification. Methods already
REJECTED for missing tracking information remain rejected for faithful
reproduction; the optional gates below do not reopen those claims.

The football question and operational formulation in section 2 are both retained.
The core analytical chain is:

```text
Leverkusen attacking actions
    → event-aligned visible spatial states
    → change in observed surrounding structure
    → next attacking actions
    → box entry / shot / future xG
    → recurring interpretable attacking mechanisms
```

This is an analytical priority and temporal sequence, not a causal finding. No
outcome window, success/failure rule or sequence construction is implemented here.

### Primary eligibility and common observational support — LOCKED

A Phase 2A metric is primarily eligible for later descriptive/research comparison
exactly when **its existing status is `ok` and actor status is `single` or `none`**.
The locked mathematical minima and missing/degenerate behavior remain unchanged.
There is **no universal minimum selected-player count, universal minimum
visible-area fraction, hard polygon-containment rule, hard edge-distance threshold
or automatic OOB exclusion**. These are deliberate decisions, not unfinished
calibration. Null visibility minima mean **no universal hard cutoff approved**.

Every structural comparison must inspect and report common observational support,
retaining at minimum selected valid-player count, visible-area fraction, selected
subset, keeper policy, OOB flag, coincident-record flag and actor status. Missing
support metadata must be disclosed. Where compared observation populations differ
materially, the later phase must explicitly document common-support restriction,
stratification, matched descriptive comparison or statistical adjustment. **No
specific method, weighting or definition of material difference is approved now.**
Hull must inspect joint n/coverage support; NN comparisons must account for both.
Primary eligibility alone never permits naive pooling of unlike observations.

### Goalkeeper and hull interpretation — LOCKED

Use **`goalkeeper_policy = excluded`** as primary for centroid, visible width,
visible depth, convex hull area, mean/median pairwise distance and mean nearest-
neighbor distance when representing **observed outfield structure**. The existing
filter means literal `keeper=False`; unknown keeper omissions remain separately
recorded. Included geometry remains available for an explicitly named **full
visible footprint** or sensitivity. Player-count inventories report both variants.
Do not delete either variant. Literal teammate subsets remain literal flags;
all_visible combines both sides and is not one team's geometry.

Keeper-excluded hull is the **observed outfield convex-hull footprint**, an
observation-sensitive **secondary structural measure**. It is not complete team
occupied area, controlled space, pitch control or a complete defensive footprint.
Do not base tactical conclusions on hull alone. Claims of stretching, expansion
or structural opening should triangulate visible width, visible depth, hull
footprint, pairwise spacing and relevant local spatial context where appropriate.
This does not authorize a composite metric or implement a local-context method.

### Sensitivity plan and record preservation — LOCKED

All robustness samples start from the applicable D-primary comparison sample,
except the explicitly labeled unchanged-record actor-inclusion diagnostic. Use
whole **original-frame** OOB/coincidence flags, even if the selected subset or
keeper-excluded variant does not contain the offending point. Preserve all raw
records and all original Phase 2A measurements.

| Metric | Approved prioritized sensitivity in addition to keeper pairing |
| --- | --- |
| Count | Whole-frame coincidence exclusion; report both keeper inventories |
| Centroid | Whole-frame coincidence exclusion |
| Visible width | Whole-frame OOB exclusion |
| Visible depth | Keeper pairing prioritized; routine headline OOB-B still applies |
| Convex hull area | n>=14 all_visible; n>=7 teammate_true; n>=7 teammate_false; plus whole-frame OOB exclusion |
| Mean pairwise distance | Whole-frame OOB and coincidence exclusion |
| Median pairwise distance | Whole-frame coincidence exclusion |
| Mean nearest-neighbor distance | n>=11 all_visible/included; n>=10 all_visible/excluded; n>=5 teammate_true and n>=4 teammate_false under either keeper policy; plus whole-frame coincidence exclusion |

These fixed q25 hull and q05 NN values are **robustness landmarks only**, not
definitions of valid frames. They are the approved values from the pinned sample;
do not silently re-estimate them in later groups or revised populations. Individual
challenges should remain distinguishable from combinations so offsetting selection
effects are not called robustness. B/C/E sweeps may supply historical context;
they introduce no universal primary count or coverage filter.

**OOB:** primary observations retain all finite supplied coordinates and their
flags. No clipping, projection, coordinate repair, point-only deletion or automatic
frame exclusion. **OOB-B is routine for every future headline spatial finding**:
rerun the applicable comparison excluding the entire original frame if it contains
any nominal-pitch OOB point. Width, hull and mean pairwise remain priorities,
without exempting other headline metrics. If a substantive finding changes
materially, flag it, investigate and report the sensitivity; do not select the
more convenient result. No numeric material-change threshold is chosen here.

**Polygon/edge:** containment, validity/consistency and continuous polygon-boundary
distance remain diagnostic metadata. Neither “outside visible polygon = invalid”
nor an edge-distance censoring rule is approved.

**Coincidence:** never deduplicate coordinates. Whole-frame exclusion is sensitivity
for count, centroid and all three spacing metrics. Width, depth and hull do not
prioritize coincidence exclusion because exact repetitions leave their geometry
invariant, subject to their unchanged mathematical status rules.

**Actors:** preserve records; exclude `multiple`/`unknown` from later primary
comparisons. Permit generic diagnostic inclusion as unchanged sensitivity.
Actor-dependent work requires `single` and a unique event join, but this does
not approve event/frame actor-coordinate semantics or resolve identities.

### Optional method gates and immediate next work — LOCKED scope

Inferred defensive lines, high/mid/deep defensive regimes, compactness composites,
Voronoi, valuable-space composites, graph representations, clustering and learned
spatial representations are **OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION**.
They are not globally rejected and are not mandatory phases. Each requires all of:

1. A specific analytical need.
2. Support from the observation model.
3. Interpretable incremental value over simpler geometry.
4. A feasible validation approach.
5. A material improvement to the football analysis.

The immediate next gate is **team/role semantics and attacking-orientation
validation**. After it, prioritize reliable possessions and sequence construction;
event-aligned spatial-state sequences; descriptive spatial-state change;
success/failure outcome definitions; comparison of evolution preceding box
entries/shots/future xG; and recurring interpretable sequence mechanisms, in that
order. No defensive-regime classification, Voronoi or clustering starts
automatically. Existing phase numbering is preserved in the revised section 28.

### Change control

This is **not a scientific version bump**. No research population or outcome
changed after effectiveness analysis; calibration followed the pre-specified
validation process; and the scope narrows interpretation to the actual observation
model before tactical/outcome analysis. The football-facing primary question,
Phase 2A formulas, units, minima, validity/degeneracy behavior, provenance, derived
data, source revision and raw-loading behavior are unchanged. This task locks
the documented method; it does not execute a later research comparison or select
an adjustment/weighting scheme. Historical candidate helpers remain diagnostic
evaluators, not a production eligibility pipeline.

## 38. Phase 2C team/role semantics and attacking orientation

*Historical initial audit. Section 40 records the subsequent human-approved
restricted lock; the gates and unresolved findings below remain unchanged.*

**9 September 2026 — VALIDATED PARTIALLY — NOT LOCKED.** This additional semantic
layer does not change the Phase 2A native measurements or the locked Phase 2B
D-primary, keeper, observation-quality or sensitivity contracts. Semantic
unsupported status is not a new geometry validity filter. No sequence, tactical
or outcome implementation is authorized by this audit.

### Evidence and provenance

The audit uses the existing loader at immutable revision
`533862946a73608c134d18b78226b6371ce7173c`: all 34 Leverkusen matches, 137,765
events and 118,581 uniquely linked 360 frames. Events, frames and lineups are
read in memory; only aggregate tables, a bounded representative manifest and
rendered figures are written. Mutable branch documentation is not a source.

The pinned [360 specification, pages 1–2](https://github.com/hudl/open-data/blob/533862946a73608c134d18b78226b6371ce7173c/doc/Open%20Data%20360%20Frames%20v1.0.0%20%281%29.pdf)
defines teammate relative to the actor's team, and location in the linked
event's actor-team attacking direction, 0 to 120. The pinned
[event specification, pages 6 and 23](https://github.com/hudl/open-data/blob/533862946a73608c134d18b78226b6371ce7173c/doc/Open%20Data%20Events%20v4.0.0.pdf)
defines possession team as the team starting the possession; other teams may
have events within it. Its coordinate diagram has x increasing rightward and
y increasing downward. These are intended provider semantics, tested against
the observed sample rather than accepted as universal record-level guarantees.

All 118,585 actor records have literal `teammate=True`; four frames contain
multiple actors. All checked named event actors belong to their event-team
lineup. Ordinary 360 points lack named identity: actor flags and lineup checks
cannot independently verify every off-ball team assignment. The named shot
freeze-frame cross-check is supporting evidence only: proximity is not identity.

Provider `related_events` gives 174,952 directed edges to other known events;
36,250 share an exactly equal native coordinate/keeper multiset. Of those,
35,615 have the expected team labels (unchanged for same event team, inverted
for opposite event teams), but 635 do not. Edges are directed, not counts of
independent pairs or frames; reciprocal links can count twice. Exact cloud
reuse is evidence of paired observations, not inferred cross-time identity.
Both endpoints of any observed contradiction are quarantined from operational
semantic mapping, including incoming nonreciprocal links. This evidence rules
out a universal observed teammate-to-event-team guarantee. It does not identify
which endpoint is wrong or authorize correcting it.

### Event team, possession and role language

Event team equals possession team in **99,999 frames** and differs in **18,582
(15.6703%)**. Neither field is missing in this pinned sample. The breakdown by
exact provider event type is `phase2c_event_vs_possession_team.csv`. Opponent
events within a Leverkusen possession remain opponent events. Possession team
is a possession annotation, not proof of the team's control at every instant.

`team_context()` preserves event/possession IDs and names independently and
returns `event_team_is_leverkusen`, `possession_team_is_leverkusen`, explicit
agreement/missing status, and these descriptive contexts:

| Context | Required literal team fields |
| --- | --- |
| Leverkusen event in Leverkusen possession | Both IDs are 904 |
| Opponent event in Leverkusen possession | Event belongs to other match team; possession ID 904 |
| Leverkusen event in opponent possession | Event ID 904; possession belongs to other match team |
| Opponent possession context | Both IDs belong to the other match team |
| Ambiguous possession context | Missing/invalid team or possession anchor |

Later “Leverkusen attacking context” may use **Leverkusen possession-team
annotation** as its candidate unit, keeping both its own and opponent events
distinguishable. This is not a possession boundary algorithm, sequence-inclusion
decision or instantaneous attacking-role assignment. `teammate=False` means
the other team only in validated scope; it must not universally mean “defending
team”: Pressure, for example, can be performed by the non-possession team.
No inferred defender roles, formations, tactical lines or identities are emitted.

### Orientation hypotheses and the Phase 1B reconciliation

| Hypothesis | Evidence and decision |
| --- | --- |
| H1: fixed-pitch/team-period flipping | Rejected as a general rule for event anchors. All 134 nonempty match/team/half shot strata have median start x at least 91.6; both teams shoot toward the same increasing-x end across halves and venues. Two of the 136 possible strata have no shots. |
| H2: event-team +x | Supported for core event coordinates and a restricted aligned 360 subset. All 916 event shots end at x >= 92.1; 914 start above x=60; 889 are 360-linked. Pass/carry displacement distributions include both signs. Goalkeeper distributions and event/possession-disagreement contexts supply additional checks. |
| H3: possession-team +x | Not a universal frame rule. Core events can disagree with possession team while their actor matches the event coordinate exactly and the literal teammate keeper is generally at low x. Shot evidence alone cannot distinguish H2/H3 when those team IDs agree. |
| H4: event-type-dependent/paired semantics | Supported. Related opposite-team events can share unchanged native clouds while their labels invert; difficult event locations need not reference the frame's retained orientation. Some pairs also contradict expected flag inversion. No universal repair follows. |

Pass and Carry are supporting anchors, not evidence that every action travels
forward. “Normal pass” here means no provider `pass.type` field. The aggregate
outputs separate all event anchors from 360-linked anchors, match/team/period,
normal vs typed passes, event/possession agreement, start x, end x, delta x and
visible keeper means. Keeper means describe visible observations only; no keeper
visibility or distance threshold becomes an eligibility condition.

Phase 1B direct/mirrored distances remain diagnostic ranks, not alignment truth
or normalization gates. Shot is direct; Pass, Carry and Pressure are predominantly
direct. Dribbled Past is entirely mirrored in this sample; Dispossessed and
Foul Won are overwhelmingly mirrored. Duel, 50/50, Ball Receipt* and Dribble
are mixed. Equal-cloud related-event evidence supports reuse of paired/opponent
coordinates as an explanation for part of this pattern. It does not prove every
case, explain every mixed type, or permit historical coordinate changes.

### Conditional semantic scope and additional coordinates

`frame_semantics()` returns `validated_core_event_team_scope` only if all hold:

1. Exact pinned revision; unique audited event/frame join and two distinct known
   match teams including Leverkusen; the event team is one of those teams.
2. Exact event type is Shot, Pass, Carry or Pressure. Whole event types are **not**
   declared safe: the remaining gates apply to each frame.
3. The complete match's incoming and outgoing provider links have been audited
   and no exact-native-cloud team-label contradiction touches the frame. A
   missing audit assertion is unsupported, not equivalent to no conflict.
4. All supplied points have finite valid coordinate pairs and literal boolean
   actor/team/keeper flags; exactly one actor exists and its teammate flag is True.
5. Actor coordinates equal either the supplied event coordinate pair exactly or
   its exact float32 encoding. This encoding fingerprint is not a distance
   tolerance, coordinate rounding/repair, or proof of named point identity.

The restricted scope combines intended provider semantics, primary/supporting
anchors, observed encoding alignment and absence of known linked contradiction.
It is a conservative operational validation, **not independent verification of
every anonymous point** or an estimate of unseen label error. Other event types
remain unsupported even when their actor is direct. Exact alignment alone does
not promote a type; absence of a related link does not verify its neighbors.

Within that scope, `point_team_label()` maps literal True to event team and False
to the other match team. Thus True/False are Leverkusen/opponent for a Leverkusen
event, and opponent/Leverkusen for an opponent event. It returns `team_id`,
`frame_player_side`, `is_leverkusen` and `is_opponent`, without named identity.
Unsupported flags/scope/teams return unresolved and missing semantic fields.

`normalize_attacking_point()` preserves `x_raw,y_raw` and supplies
`x_attacking,y_attacking,orientation_status,orientation_basis`. The caller must
name both the validated event-team reference and the desired attacking target:

| Reference versus target team | Additional coordinates | Status |
| --- | --- | --- |
| Same team | `(x, y)` | `identity_explicit` |
| Other match team | `(120-x, 80-y)` | `rotated_180` |
| Unsupported semantics/reference | Missing normalized coordinates | `unsupported` |
| Invalid supplied location | Missing coordinates | `invalid_location` |

Native core coordinates already have the event team attacking +x. The figures
choose Leverkusen as target, so its events are explicit identity and opponent
events rotate 180 degrees. Neither half nor home/away enters this rule. Rotation
of both axes preserves handedness (determinant +1), distances and hull area;
x-only reflection would reverse handedness. Y still increases down the displayed
pitch. Left/right interpretation requires a named attacking frame, not fixed
stadium-side inference. Polygon vertices and action ends use the same transform.
Finite OOB points remain OOB; raw data and Phase 2A geometry are never overwritten.

In validated scope “forward” is an increasing-x displacement for the named
attacking reference. “Toward the attacking end” is axial direction, not guaranteed
decreasing distance to goal, ball control, danger or tactical success. No such
language is attached to unsupported observations.

### Review, style and remaining method gate

`phase2c_event_semantics.csv` records per-type counts, direct/mirrored rates,
agreement, conditional scope counts, excluded counts and reasons. Supporting
tables retain every exact event type, including small samples. Representative
selection is deterministic: first sorted match/supplied frame for team/half/core
action strata, away-pass strata, each difficult type, one linked conflict and
nonexact core examples. It is not an effectiveness or prevalence sample.
Native/normalized figures show the supplied polygon, points, actor, keeper and
explicit event vector; unsupported normalized panels remain empty.

The [visualization guide](visualization_style_guide.md) establishes red Leverkusen,
charcoal opponent, gold action, subdued polygon, keeper square, outfield circle,
actor halo and redundant L/O text **within the conditional validated scope**.
Unrestricted application remains blocked. Solid arrows mean provider-recorded
action vectors; dashed arrows are reserved for future event-to-event progression
indicators. Neither is a continuously tracked trajectory.

**Lock questions A–G:** C (team versus possession) is answered for the full
sample. D/E (orientation/transform) and B/G (point mapping/football plotting) are
supported only within the explicit scope. A is intended actor-team semantics
with observed contradictions, not a universal guarantee. F provides a reviewable
conditional/unsafe classification; difficult types remain materially unresolved.
The exact blockers are team-label contradictions on reused related clouds,
unresolved orientation/actor association in mixed and paired event types, and
lack of independent named identity for ordinary off-ball points. A provider-backed
resolution or a separately justified restricted research population is needed
before a full method lock. **Do not begin reliable sequence construction,
tactical interpretation or outcome analysis on the full sample.**

## 39. Phase 2C-2 validated spatial-anchor coverage and sequence readiness

*Historical readiness audit and recommendation. Human approval is recorded in
section 40; the empirical findings below are preserved as originally reviewed.*

**10 September 2026: readiness audit complete — READY — WITH RESTRICTIONS.**
**Phase 2C = VALIDATED PARTIALLY — NOT LOCKED.** This section records an empirical
feasibility inventory and a human-review recommendation. It does not supersede
the section 38 semantic gates or the locked Phase 2A/2B contracts.

### Diagnostic population, order and timing

`leverkusen.sequences.readiness` reads each pinned match's complete event stream
and 360 records once in memory. The immutable source remains
`533862946a73608c134d18b78226b6371ce7173c`. It audits incoming and outgoing related
links across both possession teams before calling the existing `frame_semantics`
function. Missing/duplicate event/frame IDs, orphans, ambiguous event indices,
missing possession/team/time annotations, conflicting possession-team annotations,
noncontiguous possession identifiers within a period and backwards timestamps
abort the audit; they are not repaired or silently dropped.

The **full event sequence** is ordered by supplied event `index` and grouped by
`(match_id, period, possession_id, possession_team_id)`, retaining groups whose
possession-team ID is 904. This implements the diagnostic grouping already
specified in section 9, without inventing possession boundaries. Nineteen
match/provider-possession IDs occur in multiple periods; retaining the period
boundary yields 2,888 groups versus 2,869 distinct match/provider-possession IDs.
All events in each group remain context: other-team, unsupported, unlinked,
administrative and stoppage records are included. No control-at-every-instant
claim follows from the provider possession-team annotation.

**Validated spatial anchors** are only events whose unique frame returns
`validated_core_event_team_scope`. Whole event types are not promoted. This run
reproduces the existing full-season totals exactly: 137,765 events, 118,581 linked
frames, 72,596 validated frames and 45,985 unsupported frames. It supplies neither
interpolated states nor trajectories. Repeated/related observations are retained
as provider events, not asserted to be independent spatial samples. In particular,
Pressure is a frame anchor, not automatically a ball-location observation.

Timestamp strings are preserved and parsed into seconds **within each period**,
including supplied stoppage time. There is no new canonical across-period clock.
Possession duration is last event start minus first event start, not playing time
or the end of the final action; event `duration` is not added. First/last anchor
times use the same period-local seconds. Zero-anchor times/spans are missing;
a one-anchor span is zero. Consecutive gaps never cross possession or period
boundaries. Five equal-timestamp anchor pairs contribute zero-second gaps.

Event-index gap is next index minus previous index. Intervening-event count is
the difference between the anchors' positions in the **full retained group**,
minus one; it is not calculated on a filtered anchor stream. In the pinned sample
these equal index gap minus one, but the code does not assume consecutive indices.
Quantiles use pandas' default linear interpolation. Time-gap summaries pool
intervals, so longer/richer possessions contribute more intervals. Possession and
match summaries retain their own denominators, without inferential independence
claims or resampling.

### Descriptive strata and bounded outputs

Simple duration bins are `[0,5)`, `[5,15)`, `[15,30)`, `[30,60)` and `[60,infinity)`
seconds. These are presentation bins, not eligibility cutoffs. Candidate minimum
state counts 2/3/4/5/6/8 and inclusive windows 3/5/10/15 seconds are enumerated
without selection. Consecutive tuples overlap; possession window counts require
at least one such tuple. With ordered nondecreasing time, an interval containing
at least N anchors contains a consecutive N-anchor tuple, so no interpolation
or custom rolling-event inclusion rule is required.

`has_shot` means any provider Shot in the group, with separate Leverkusen and
opponent shot counts. `has_goal` means a Shot with provider outcome Goal; it is
not a scoreboard or own-goal inventory. `ends_in_shot` means the **literal last
recorded event** is Shot. A separate final-meaningful-event convention is deferred:
Goal Keeper and other terminal/context records cannot be discarded without an
additional operational choice. These flags define neither danger nor success;
no xG is read or thresholded. Box-entry inventory is skipped because full-stream
event-location semantics and entry/completion handling are unresolved; the
provisional zone configuration is not promoted into an entry definition. No
cross-event location inference or maximum-x field is necessary for this audit.

Match coverage reports the fraction of frames linked to **Leverkusen possessions**
that validate, including opponent events. It is distinct from frames attached
only to Leverkusen-team events. Ascending rank of the >=3-anchor rate identifies
comparatively weak matches descriptively; it creates no exclusion rule.

Ten distinct representative possessions are selected deterministically. Reserve
the lexicographically first maximum-anchor group; then choose the first unused
match/period/possession/team key in each stratum: zero, one, two anchors; moderate
count (empirical p25–p75 and at least three); high count (at least p95); Shot;
opponent anchor; long/sparse (duration at least p75, anchors/duration at most p25);
short/dense (duration at most p25, rate at least p75). Zero durations have missing
rates. These are review strata only. The sample is intentionally deterministic
and concentrated in the first sorted match; prevalence comes from season tables.
Each selected timeline retains all its events and distinguishes validated,
unsupported-linked and no-360 statuses. These bounded derived timelines contain
no raw coordinates, nested records or full-season event dump.

The CLI writes 18 derived CSVs under ignored `outputs/diagnostics/`: possession
coverage; per-pair gaps; count coverage; distributions; gap thresholds; match and
duration coverage; anchor types and transitions; event-team composition; shot
coverage; temporal windows; candidate state counts; human-review summary;
representative manifest and timelines; source inventory; run summary. Every table
records the source SHA; the source inventory records URLs, and the run summary
records completion UTC, software versions and reconciliation counts. Three
neutral figures show all/shot attrition, the gap ECDF (detail and full range) and
all 34 match rates. `notebooks/05_sequence_readiness.ipynb` presents these outputs
offline with provenance and denominator checks; reusable logic stays in the package.

### Readiness evidence and recommendation

The full Leverkusen possession stream contains **86,025 events**, **74,647 linked
frames** and **46,143 validated anchors** (61.8149% of linked frames); 28,504 linked
frames remain unsupported. Median events/linked frames/anchors per possession
are **20/17/10**. There are 176 zero-anchor possessions; **84.0720%** have at least
three anchors and **73.5111%** at least five. All 34 matches contribute substantial
support: >=3-anchor possession rates range **72.0930–92.7083%**. The 43,431
consecutive intervals have median/p90 time gaps **1.103/3.214 seconds**; **95.9660%**
are at most five seconds. Median/p90 intervening-event counts are **1/2**.
Among **571 Shot-containing possessions**, **87.7408%** have at least three
anchors. All four anchor types occur in all 34 matches. Opponent events supply
**6,846 anchors (14.8365%)**, and must remain explicitly distinguished.

**READY — WITH RESTRICTIONS** is an evidence-based judgment across these six
dimensions, not a score or single cutoff. The count, temporal and event-gap
support is broad enough for meaningful event-aligned spatial-sequence design
within the validated population. The restrictions are the existing frame-level
semantic scope, partial visibility, event/possession-team distinction and pending
sequence/measurement decisions. Short and zero-anchor possessions, long-gap tails
and variable observation support must remain visible during that later review.
Semantic anchor counts do not establish that every Phase 2B geometry metric is
available or comparable at every anchor; metric status, subset, keeper convention
and observational support remain required for subsequent comparisons.

**Recommendation A: lock the restricted semantic scope for `validated
spatial-anchor sequence analysis`, subject to human approval.** Additional work
on unsupported-type semantics is **not necessary before restricted sequence
design** on coverage grounds. It remains necessary if those types or a broader
spatial population are later required. Neither continued semantic expansion merely
to enlarge the sample nor project redesign is indicated by this readiness audit.
The analytical sequence dataset, eligibility minima, maximum gaps, duration/window
choices, final outcomes and tactical interpretation remain unimplemented.
**This recommendation does not lock Phase 2C.** Detailed distributions and the
review examples are recorded in the Phase 2C-2 technical appendix.

## 40. Human-approved Phase 2C restricted semantic scope lock

**Human methodological approval — 10 September 2026.**
**Phase 2C = LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE.**

Phase 2C is complete for the restricted semantic/orientation population approved
for **validated spatial-anchor sequence analysis**. This accepts Recommendation
A from section 39. It changes approval status only: the exact frame-level gates,
raw coordinates, source pin and Phase 2A/2B contracts are unchanged. Historical
progression remains:

| Decision stage | Recorded status |
| --- | --- |
| Initial Phase 2C audit, 9 September | VALIDATED PARTIALLY — NOT LOCKED |
| Phase 2C-2 readiness audit, 10 September | READY — WITH RESTRICTIONS; restricted lock recommended |
| Human approval, 10 September | LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE |

This is not a resolution of every StatsBomb 360 frame/event type, named identity
for ordinary off-ball points, correction of unsupported frames, or authorization
for full-sample spatial normalization/sequence analysis. Section 38's observed
linked-cloud contradictions, mixed/paired orientation findings and identity
limitations remain part of the method record. Its former full-sample blockers
do not prevent the restricted Phase 3 design now authorized below.

### Exact approved population and pinned-run reconciliation

`semantics_status == validated_core_event_team_scope` is the authoritative
membership decision, implemented by the unchanged `frame_semantics()` gates in
`leverkusen.spatial.orientation`. Pass, Carry, Shot and Pressure are the only
currently supported types, **subject to every existing frame-level gate**.
Type membership alone is insufficient. No gate is loosened, tightened, duplicated
or replaced by a count target, new helper, proximity heuristic or event-ID list.

The approved reconciliation is specific to immutable revision
`533862946a73608c134d18b78226b6371ce7173c` and the audited 34-match season. It is
not a universal expectation for another source revision or research population.

| Locked-run measure | Full season | Leverkusen provider-possession groups |
| --- | ---: | ---: |
| Retained events | 137,765 | 86,025 |
| Uniquely linked 360 frames | 118,581 | 74,647 |
| Validated semantic/orientation frames | 72,596 | 46,143 |
| Unsupported linked frames | 45,985 | 28,504 |
| Possession groups | Not the selected denominator | 2,888 |

Leverkusen groups retain match, period, provider possession ID and possession-team
ID 904. This preserves the section 39 audit grouping; it does not settle the
future analytical sequence unit or start/end rules. Among the 46,143 anchors,
**6,846 are opponent-team events**. The readiness CLI checks both sets of locked
counts before writing results. The reconciliation check is tied to this exact
revision and has offline guard tests; it never chooses or changes frame membership.
Historical CSVs and executed notebooks retain their original dated status. New
CLI status messages/run metadata report the human-approved lock.

### Team mapping and attacking reference — locked within validated scope

Within validated scope only, literal `teammate=True` maps to the **event team**;
`teammate=False` maps to the **other known match team**. Therefore:

| Event team | Literal True | Literal False |
| --- | --- | --- |
| Bayer Leverkusen | Bayer Leverkusen | Opponent |
| Opponent | Opponent | Bayer Leverkusen |

Outside this scope, semantic point labels remain unresolved; football-facing
plots must not infer team labels or apply Leverkusen/opponent semantic colors.
Point mapping is not named off-ball identity. Event-team and possession-team
fields remain separate: an opponent event inside a Leverkusen possession is
still an opponent event. Provider possession-team annotation can define context
grouping without asserting instantaneous possession/control at every event.

Validated native event coordinates use **event-team attack toward increasing x**.
For a requested Leverkusen attacking reference, the approved additional coordinates
and statuses are:

| Event team | Additional `(x_attacking, y_attacking)` | Orientation status |
| --- | --- | --- |
| Leverkusen | `(x_raw, y_raw)` | `identity_explicit` |
| Opponent | `(120 - x_raw, 80 - y_raw)` | `rotated_180` |

The reference then has Leverkusen attacking toward increasing x. Raw coordinates
are preserved, including finite out-of-bounds values; the same transform applies
to the supplied observations, polygon and valid explicit event start/end points.
Half-based, home/away, possession-team flipping and x-only reflection are not
approved. Unsupported frames return unresolved/missing normalized spatial states.

Approved football language within scope includes Leverkusen/opponent, event team,
possession team, Leverkusen attacking reference, attacking x/y, visible Leverkusen
or opponent players, event-aligned spatial state and observed outfield structure.
Increasing x means toward the named attacking end; forward displacement must be
explicitly relative to that validated frame. It does not establish danger, actual
movement between frames, complete team observation, a full tracking state, named
anonymous-player identity or continuously observed trajectories.

**Pressure caveat:** a validated Pressure frame can be a spatial anchor. It is
not automatically ball location, a Leverkusen possession action, exact
defender-to-ball distance or a continuous pressure episode. How action semantics
and state semantics interact belongs to Phase 3 design.

### Full event context and spatial anchors — locked architecture

The complete provider possession event stream retains ordered validated,
unsupported, unlinked, opponent and administrative/context events, subject to
later analytical sequence-method decisions. Only the validated Phase 2C subset
contributes trusted normalized spatial states. The 45,985 unsupported frames
remain **unsupported for normalized spatial-semantic analysis**; their events
are not thereby invalid football events, deleted context or bad data by definition.
Their spatial states must not be repaired heuristically, interpolated, forward
filled or inferred. This is an architectural contract, not a final sequence table.

Dribbled Past, Dispossessed, Foul Won, Duel, 50/50, Ball Receipt*, Dribble and other
unsupported/mixed types retain their existing classifications. No further work
on these types is needed before restricted sequence design. Revisit them only
when a specific downstream need requires their spatial state, never simply to
increase sample size.

Semantic validity and geometry-comparison eligibility remain **separate layers**:

```text
event exists -> 360 frame exists -> Phase 2C scope passes
    -> trusted spatial anchor exists
    -> Phase 2B metric-specific eligibility/support checked
    -> metric may enter that particular comparison
```

A semantically validated anchor does not guarantee a usable/comparable value for
every geometry metric. The unchanged Phase 2B contract still requires metric
status, actor policy, goalkeeper convention, selected-player count, visible-area
support, OOB and coincidence flags, metric-specific robustness checks and common
observational support. Specific downstream comparison implementations remain open.

### Approval rationale, visualization and change control

Human review considered the whole readiness evidence, not a single cutoff:
93.91/88.54/84.07/78.46/73.51% of the 2,888 groups contain at least 1/2/3/4/5
anchors, respectively; the median is 10. The 43,431 consecutive intervals have
median/p90 gaps of 1.103/3.214 seconds, with 88.77% at most three seconds and
95.97% at most five. Match >=3-anchor rates span approximately 72.09–92.71% across
all 34 matches. Among 571 Shot-containing groups, 87.74% have >=3 anchors and
79.51% >=5. All four anchor types appear in all 34 matches. This supports restricted
design without semantic expansion. These are observational coverage diagnostics,
not tracking resolution, independent samples or sequence validity thresholds.

The [visualization style guide](visualization_style_guide.md) is now **LOCKED
within validated scope**: Leverkusen red, opponent charcoal, action/event gold,
outfield circles, goalkeeper squares, actor halo/outline and useful redundant L/O
labels. Unsupported frames cannot receive those semantic team colors. A solid
arrow means a provider-recorded event action vector with explicit valid start/end;
a dashed arrow means a future event-to-event progression indicator. Neither is a
continuously tracked ball trajectory. No sequence plotting is implemented here.

**No scientific version bump is required.** The restricted population follows
pre-outcome semantic validation and the pre-specified feasibility audit. Sequence
outcomes/effectiveness have not been examined; no primary outcome, tactical result
or effectiveness finding drove this decision. Descriptive Shot containment in the
readiness inventory was coverage evidence, not a locked success/danger outcome.
Raw data, source revision, Phase 2A/2B methods, the football-facing research
question and the operational formulation remain unchanged. The established chain
of actions → validated spatial states → observed structural change → next actions
→ later box-entry/shot/future-xG definitions → interpretable mechanisms remains
the research aim, without an outcome or causal claim from this lock.

### Remaining boundaries and Phase 3 authorization

Unsupported-type semantics/orientation, ordinary off-ball identities, continuous
tracking and full-sample normalization remain unresolved or unsupported. Sequence
unit, start/end and eligibility definitions, minimum anchors, maximum time/event
gap, possession-duration requirements, rolling windows and spatial-state features
remain open. Box entry, future-xG horizon, success/failure, comparison-specific
common-support implementation and tactical mechanism definitions also remain
unresolved. These are not blockers to completing restricted Phase 2C; a later
method must address the boundaries it specifically requires. In particular,
84.07% with >=3 anchors does not imply a three-anchor minimum, and neither the
median nor p90 time gap defines an allowed maximum.

**Phase 3 — Possession and Spatial-Sequence Method Design is now authorized**
specifically for **validated spatial-anchor sequence analysis**, using complete
provider possession events as context, the locked Phase 2C subset as trusted
states, and the locked Phase 2B contract underneath any geometry comparison.
No final sequence dataset, segmentation, sequence threshold, outcome, tactic,
clustering, prediction or causal analysis is implemented or authorized by this
documentation change. Unrestricted full-sample spatial analysis remains outside
the approved population. This task stops at recording the lock and design
authorization; Phase 3 implementation requires its own subsequent work.

## 41. Phase 3A-1 progression and reset diagnostics

**10 September 2026 — Phase 3A-1 = DIAGNOSTIC / NOT A METHOD LOCK.**
Phase 2C remains **LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE**. The Phase
2A/2B/2C contracts, source behavior, gates and frame membership are unchanged.

The working hypothesis for later calibration is that an attacking episode may
be a contiguous portion of a Leverkusen possession characterized by sustained
or renewed progression, bounded by explicit football termination or a meaningful
reset of progress. This is not an adopted definition. The hierarchy remains
match → provider possession → full event context → future candidate episodes,
with validated anchors available inside that context. No final segmentation,
eligibility, outcome, tactical label, clustering or change-point method is created.

### Population and two analytical layers

The parent is the existing match/period/provider-possession/team-904 group.
`match_event_inventory()` audits each complete match, including incoming/outgoing
related-cloud conflicts, before selection. `frame_semantics()` remains the sole
semantic authority. Source revision remains
`533862946a73608c134d18b78226b6371ce7173c`. All 2,888 groups and 86,025 events remain
context, including unsupported, unlinked, opponent and administrative records.

**Action-vector layer:** use own-team Pass/Carry events with valid explicit
start/end pairs **and a validated Phase 2C frame**. This conservative diagnostic
extraction does not enlarge semantic scope or define future sequence eligibility.
Otherwise explicit unsupported/unlinked vectors remain event context without
normalized action coordinates. Shot and Pressure are not forced into this layer.
A recorded pass endpoint does not assert successful controlled possession; no
completion filter is applied. `normalize_attacking_point()` supplies the existing
Leverkusen reference, without duplicated orientation logic. IDs, indices, times,
teams and raw/additional coordinates remain distinct in memory.

Derive `delta_x = end_x - start_x`, corresponding delta-y, Euclidean displacement,
forward component `max(delta_x,0)` and backward magnitude `abs(min(delta_x,0))`.
These use explicit vectors only; no displacement is inferred between actions.
The resulting sample is 20,092 Pass and 17,892 Carry vectors (37,984 total),
covering 2,662 groups. There are 5,713 otherwise explicit own-team vectors outside
the frame scope. The 226 groups with no safe action retain missing progression
measurements, not invented zero progression. No raw coordinate is altered.

**Spatial-anchor layer:** retain all 46,143 validated frames, including 6,846
opponent anchors. Summarize consecutive normalized event-start-x differences by
previous/next type and actual event-team IDs separately. These are differences
between actor/event references, not automatically ball progression. Pressure is
not automatically ball location, a Leverkusen possession action, defender-to-ball
distance or a continuous pressure episode. Mixed actor/type coordinates are not
pooled into action-path retreat/recovery. Phase 2B metric-specific geometry
eligibility remains a separate layer; no geometry metric is recomputed here.

The existing revision-bound guard checks full-season and possession totals.
All 43,431 anchor intervals reconcile with Phase 2C-2, including median/p90
1.103/3.214 seconds. No unsupported frame receives trusted normalized coordinates.

### Ordered vertices, cumulative displacement and retreat

Order safe actions by event index within each parent, appending each recorded
start then end as two **action-ordered vertices**. These are not two independent
360 observations. Retain repeated coordinates. First-safe x is the first action
start; last-safe x is the final action end; min/max cover all vertices; net x is
last minus first. Forward/backward totals sum only the explicit-vector components.
They can exceed pitch length through repeated actions and are not player distance
or attacking success. A zero backward total gives a missing ratio and an explicit
zero-denominator flag; no-action ratios remain missing.

Inter-action jumps `next_start_x - previous_end_x` are reported separately.
Net progression equals forward minus backward totals plus the sum of those jumps.
Skipped actions or action semantics may explain discontinuities; they do not
establish observed motion. No coordinate or running peak is forward-filled into
unsupported full-context rows.

At each ordered vertex, running peak is the maximum observed x so far; retreat
is peak minus current x. Report all vertices and each measurable parent's maximum.
The vertex distribution weights longer paths and repeats shared endpoints; it is
not an independent-frame or possession-weighted distribution. Also summarize
maximum retreat after first reaching x>=30/60/80/100. The >=5/10/15/20/25/30/40
retreat sweep is diagnostic only, with both all-parent and measurable-parent
denominators. No value defines a reset.

### Runs, temporal interruption and exploratory recovery

Strict runs are maximal contiguous positive or negative delta-x values **in the
usable action subsequence**. Zero/opposite sign ends a run. Full-context events
may intervene and their counts are retained; runs do not certify consecutive
football actions or uninterrupted control. Report action count, cumulative and
maximum single components, first-start/last-end x, and first-to-last action-start
timestamp span. A one-action span is zero, not instantaneous action completion.
A separately labeled non-positive alternative permits exact-zero actions while
requiring at least one negative action. No near-zero tolerance or preferred run
convention is selected. >=2/3/4/5-action settings are prevalence sweeps only.

Time gaps use source period-local timestamps for all context events, safe actions,
and all validated anchors separately. No pair crosses match/period/possession
boundaries. Report quantiles through p99, maximum and strict >3/5/10/15-second
rates; equal timestamps remain zero. No allowed maximum is chosen. Possession
duration remains last event start minus first event start, including stoppage or
administrative time, not active playing time.

The simple exploratory recycling/recovery calculation is a nonoverlapping
excursion below the **running record peak**. First observed x below that peak
starts it; first later observed x at or above the same level ends it. Equal peaks
update the reference to the latest observation. Record reference/onset/trough/
return event indices, retreat size, peak-to-return event-position difference and
peak-to-trough/trough-to-recovery timing. `new_peak_reached` means any subsequent
safe vertex in the same parent exceeds the reference, not a future outcome.

Unobserved recovery is censored at the last safe observation. Recovery time/count
is missing, with follow-up recorded separately; this does not establish failure
to recover in the full football sequence. Endpoint arrival times are not supplied:
both vertices carry their source **action-start timestamp reference**. These
durations are source timestamp differences, not exact physical recycling times.
No action duration, trajectory or motion is inferred.

This running-record diagnostic is simpler than a local-peak or “sustained rise”
rule. It can miss renewed local rises below an earlier high. In this sample,
171 groups start their safe path at x=120 and 205 reach 120 somewhere. Both plotted
extreme examples begin with provider Corner records at x=120, so a global-peak
excursion can persist through many later rises. This needs human review, not
coordinate correction or an automatic reset declaration.

### Presentation, provider context and selection

Delta-x bins are `<-20`, `[-20,-10)`, `[-10,0)`, `[0,10)`, `[10,20)`, `>=20`;
zero is separately counted in the numeric summary. Field-depth bands are below
0, `[0,30)`, `[30,60)`, `[60,80)`, `[80,100)`, `[100,120)`, and 120 or above.
These are presentation choices, not tactical zones; provisional zone config is
not used. Duration landmarks use strict >30/60/90/120 seconds. Arithmetic uses
supplied values without rounding/tolerance/repair; quantiles use pandas linear
interpolation.

Football context inventories actual type names (Shot, Foul Won/Committed,
Offside, Injury Stoppage, Referee Ball-Drop, Half Start/End, Dispossessed,
Miscontrol, Interception, Ball Recovery, Duel, Block, Clearance), literal
`out=True`/`counterpress=True`, named pass types and supplied Pass/Duel/Interception/
Ball Receipt outcomes. Shot outcome, goal and xG do not select signals or settings.
Provider labels such as pass.type:Recovery and duel.outcome:Won are not project
success outcomes. The final provider-group record is inventoried with actual
next-event type/team/possession-team/period context. No token automatically
creates a hard episode boundary; overlapping tokens are not independent counts.

Candidate prevalence covers literal tokens, single backward magnitude, cumulative
peak retreat, run length, all temporal layers, observed peak-recovery time,
censored follow-up and any observed recovery. Recovery/follow-up settings use
>3/5/10/15/30 seconds. Each setting stays separate: no score, boundary strength or
preferred setting. Cross-family overlap enumerates all numeric combinations for
single backward actions, peak retreat, strict negative runs, safe-action gaps and
observed peak-recovery time. All-parent prevalence means observed support, not
proof of signal absence where actions are missing.

The extreme manifest unions top 20 groups by duration, event count, anchor count
and maximum retreat, breaking ties by possession key and retaining ranks: 50
distinct groups. The separate 26-group review manifest takes first two keys per
stratum: nonnegative vectors with >=2 positive actions; exactly one backward
action <=5 units and p75 forward total; p95 single retreat; >=3 negative actions
in a run; observed recovery; p95 excursion count; positive duration <=p25 with
p90 net-x/time; Shot context; p95 anchor count; <=1 anchor; and p95 absolute summed
inter-action jump. Add four extreme leaders, then fill to 26 from the longest
unused extreme groups. These values select review cases only. Nonnegative vectors
need not imply a monotonic full path when jumps occur; that ambiguity is retained.

Each selected full timeline retains every parent event, both team fields, relative
time, UUID/index/type, validated status and safe action coordinates/displacement/
peak/retreat where defined. Unsupported spatial fields stay missing. Selected
path vertices and literal provider-token context are separate CSVs. No episode,
reset or tactical label is attached; this is not a prevalence sample.

### Artifacts, support and next gate

`scripts/progression_diagnostics.py` writes 28 derived CSVs and four lightweight
figures. Reusable logic resides in `leverkusen.sequences.progression_diagnostics`
and `leverkusen.visualization.progression`. Every CSV records the source revision;
the source inventory records URLs/counts, and execution summary records completion
UTC and package versions. `run_statistics` holds sign-run distributions separately
from execution `run_summary`. The requested retreat/run/recovery tables are
derived diagnostics, not raw-source dumps or final sequences. Previous outputs
remain untouched. `06_progression_reset_diagnostics.ipynb` reviews the evidence
offline without embedding reusable transformations.

Pass/Carry median delta-x is 2.3/0.2 units and negative rates are 41.18/28.86%.
Measurable-possession median net/forward/backward progression is 31.0/57.75/18.1;
median/p90 maximum peak retreat is 16.8/53.2. At the illustrative 20-unit setting,
383 groups contain a single backward vector and 1,195 show cumulative peak retreat.
That difference can include multiple actions **and discontinuities**; it is not
a reset count. Of 4,781 record-peak excursions, 3,519 have observed recovery and
1,262 are censored; conditional median/p90 recovery timestamp spans are
5.008/22.1512 seconds. The technical appendix records the complete findings.

The next review should compare cumulative and single-action retreat, strict and
zero-tolerant runs, literal stoppage/restart context, all temporal layers, and
observed/censored recovery. Restart-seeded peaks, endpoint-time uncertainty and
skipped-action discontinuities prevent promoting any signal directly into a
boundary rule. **No segmentation threshold/rule, outcome or model is selected.**
**Phase 3A-2 — Representative Possession / Boundary Review is next**, followed by
**Phase 3A-3 — Segmentation Calibration & Method Lock**. Phase 2C remains locked
as before; Phase 3 sequence segmentation remains unimplemented.

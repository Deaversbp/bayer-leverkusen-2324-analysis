# Spatial Sequence Analysis — Source Foundation

Spatial Sequence Analysis of Bayer Leverkusen 2023/24. Canonical machine-readable
source/provenance reference for the technical research article, methodology
appendix and reproducible codebase.

Document basis: *Source Foundation & Annotated Bibliography*, Football Analytics
Research Foundation v0.1, prepared 4 September 2026, supplied as
`Leverkusen_Spatial_Sequence_Source_Foundation.pdf` (11 pages). All 35 bibliography
entries, their substantive annotations, priorities, citation roles and embedded
source links are retained. Scope: method sources directly relevant to the planned
Leverkusen spatial-sequence technical article, not a universal football analytics
bibliography. The external PDF has not been copied or recreated in the repository.

Bibliographic facts and research claims are transferred from the supplied PDF,
not independently reverified against its linked publications. Author spellings,
`et al.`, dates, publication details and identifiers follow the PDF. Its “Open
source” labels are source-access links, not license/open-access certifications.
Primary provenance mappings, raw-field mappings and explicit repository notes
below are documentation integration, not additional published definitions.
Unspecified details remain unresolved; no identifiers or publication pinpoints
have been invented.

Research principle: If we borrow a published idea, definition, formula, metric,
model family, or analytical convention, cite it. If we change it, cite the source
and label our version as an adaptation.

## 1. Methodological stance

The literature supports the project, but it also narrows what we should claim. The strongest design is an interpretable tactical case study grounded in established positional metrics, explicit operational definitions, and sequence-aware validation.

Treat compactness as a feature family, not a universal scalar. Use width, length/depth, convex-hull area, stretch indices, line/cluster gaps and interpersonal distances. If a composite score is created, call it a project-specific index and report sensitivity to its construction. [S09-S12]

Treat low-/mid-/high block as operational phase labels. Use FIFA/Bauer as precedents; derive a transparent StatsBomb-360-compatible classifier and sensitivity-test thresholds. Do not imply our cutoff is an industry standard. [S04-S06]

Use event-aligned spatial trajectories, not continuous-tracking language. StatsBomb 360 gives player locations in the visible frame around events, so describe changes between event snapshots. Avoid claims about exact velocity, acceleration or continuous pitch control unless separately estimated and validated. [S01-S02, S14, S17, S27]

Do not use naive full-pitch Voronoi if relevant players are unobserved. Bound calculations to defensible observed regions or use features robust to partial visibility; explicitly report missing-player / visible-frame limitations. [S01-S02, S11, S27]

Use future xG as the main danger outcome; keep shot/box-entry probability as secondary outcomes. Future xG is upstream of shot execution quality and better aligned with the buildup problem than PSxG. [S03, S21]

Start with interpretable geometry + sequence features before deep learning. The 34-match case study is rich enough for clustering, regression/tree models and sequence summaries, but not an excuse to force a high-capacity neural architecture. Deep representation learning remains a benchmark/future extension. [S27-S31]

Validate by match or whole sequence, never by randomly splitting event rows. Events and possession states are dependent. Keep entire matches/sequences together across train/test or resampling folds. [S31-S32]

Separate evidence from tactical interpretation. Report observed associations first; label causal/coaching explanations as interpretations unless supported by a causal design. [S31, S34-S35]

Repository integration: the preceding paragraphs preserve the PDF's proposed
methodological stance. Models and outcomes are not selected or implemented by
this synchronization. The PDF's possibility of separately estimated/validated
motion does not weaken the repository's faithful-reproduction exclusions in
section 6; no such proxy currently exists.

### Research questions preserved from the PDF

The PDF's locked primary question is:

> How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24 Bundesliga season, and which recurring attacking sequences were most effective against different defensive structures?

Its eight supporting questions are preserved as source-document wording:

1. What recurring attacking spatial patterns characterized Leverkusen's possession play?

2. How did opponent defensive width, depth, compactness and line spacing evolve during those patterns?

3. Which attacking patterns created the largest increases in valuable space?

4. Which resulting spatial changes were associated with the greatest subsequent chance quality?

5. How did effectiveness differ across high, mid and deep defensive structures?

6. Against deep defenses specifically, which patterns most effectively disrupted compactness or created exploitable space?

7. At what point in successful sequences did defensive structure begin to deteriorate?

8. Which player movements were most strongly associated with those changes?

Repository integration: [research_questions.md](research_questions.md) remains
the current question numbering used by the registry. It adds occupied area to
question 2, clarifies attacking/valuable space and structural disruption, restricts
question 8 to identified player actions, and adds question 9 on sensitivity.
The PDF's “player movements” wording does not authorize anonymous off-ball identity
inference. “Evolve,” “trajectory” and “point” refer to observed event-aligned states.

## 2. Novelty boundary

This section is intentionally conservative. It prevents the article from presenting established ideas as new.

- Not novel: Voronoi / dominant-region analysis itself (S13-S14).

- Not novel: measuring centroid, width, surface area, stretch or interpersonal distances (S07-S12).

- Not novel: valuing locations/actions with xT, VAEP, OBV or EPV (S20, S22-S25).

- Not novel: using prior event sequences for prediction (S26, S29).

- Not novel: using 360 freeze frames to learn situational representations / Situational xT (S27).

- Not novel: extracting tactical patterns from event + freeze-frame data (S28).

- Potential contribution: an interpretable single-team case study that links event sequence + timing + event-aligned visible-player spatial-state trajectory to measurable defensive structural change, identifies recurring Leverkusen attacking mechanisms, quantifies the dangerous space/future chance quality associated with those mechanisms, and connects successful patterns to opponent defensive reactions.

This potential contribution is a research proposal, not an achieved result or
causal claim. The base methods and closest prior work remain established.

## 3. Provenance framework

The six primary categories are repository provenance labels. A source can support
different categories depending on what is borrowed from it.

| Category | Meaning |
| --- | --- |
| SOURCE | Raw provider field or provider documentation |
| ADOPT | Published definition/method used materially unchanged |
| ADAPT | Published concept modified because of StatsBomb 360 or project constraints |
| DERIVE | Mathematical quantity directly derived from observed data |
| PROJECT | New project-specific operationalization or construct |
| REJECT | Method incompatible with the available observation model |

Provenance is separate from definition maturity and implementation status.
`DERIVED` in the registry describes a proposed computed metric, not implemented
code. `ADAPT` and `TBD` may describe open definition decisions. An adopted base
geometry definition can be mathematically DERIVE and require ADAPT for a visible
subset. Citations do not implement or finalize a metric.

The PDF's additional **citation roles** explain why a source belongs in the
article; they do not replace the primary categories. Exact compound role labels
are retained in each bibliography entry.

| PDF citation role/family | Relationship to primary provenance |
| --- | --- |
| DATA — must cite | SOURCE for dataset/provider provenance; cite in Data/Reproducibility |
| METRIC DEFINITION | SOURCE for provider xG; published definitions can support ADOPT; future aggregation remains PROJECT |
| ONTOLOGY / PHASE DEFINITION; ONTOLOGY / CONTEXT | ADOPT vocabulary; ADAPT concepts and PROJECT classifier/cutoffs |
| ADOPT — formulas; ADOPT / TIME-SERIES PRECEDENT | ADOPT definition; ADAPT observation model where necessary; DERIVE quantity |
| ADAPT / OPERATIONAL BASELINE; ADAPT / PASS EFFECT; ADAPT — core concept | Explicit adaptation; changed formulas/composites require PROJECT attribution |
| ORIGIN / PRECEDENT; ORIGIN / VORONOI; METRIC ORIGIN; FOUNDATIONAL / MARKOV | Method lineage supporting ADOPT/ADAPT; role does not prove first invention |
| ORIGIN / DYNAMIC INFLUENCE; BOUNDARY / PITCH CONTROL; RELATED / FULL-TRACKING CEILING | Conceptual boundary; REJECT faithful reproduction where motion/full tracking is unavailable |
| REVIEW / METRIC SELECTION; REVIEW / LIMITATION; REVIEW / PROJECT FRAMING; REVIEW / HISTORICAL CONTEXT | Evidence for selection, interpretation and limitations; no automatic formula adoption |
| BENCHMARK / PASS VALUE; METRIC ORIGIN / BENCHMARK; BENCHMARK / ACTION VALUE; PROVIDER BENCHMARK | Comparison/contrast; does not establish input/model availability or compatibility |
| RELATED / OFF-BALL VALUE; RELATED / PRE-SHOT SEQUENCE; RELATED / EVENT HISTORY | Related work and novelty boundary; ADAPT only with an explicit feasible definition |
| CLOSEST PRIOR WORK; CLOSEST 360 SNAPSHOT BASELINE; CLOSEST PATTERN-DISCOVERY PRECEDENT | Closest competing approaches; source-specific ADOPT/ADAPT still needs method review |
| TIMING / TEMPORAL BASELINE; PROFESSIONAL / HUMAN-IN-LOOP CEILING | Temporal/professional-value precedents, not a reproduced model/domain |
| VALIDATION — must cite if modeling; VALIDATION / BLOCKING | ADOPT validation guidance; specify project groups and partitions |
| UNCERTAINTY / BOOTSTRAP | ADOPT bootstrap methodology if used; respect match/possession dependence |

## 4. Citation provenance matrix

“Direct citation” means the source should appear adjacent to the relevant
method/data statement in the final article. This preserves the PDF's matrix.

| Article component | Primary source IDs | How to use |
| --- | --- | --- |
| Dataset and 360 provenance | S01, S02 | Direct citation |
| StatsBomb xG / future chance quality | S03 | Direct metric definition |
| High / mid / low defensive phase vocabulary | S04, S05, S06 | Adopt vocabulary; adapt operational classifier |
| Centroid, length, width, surface area, stretch, distances | S07, S08, S12 | Adopt formulas / precedent |
| Why compactness is multivariate / non-standardized | S09, S10, S11 | Review evidence / limitation |
| Voronoi dominant regions | S13 | Adopt if used |
| Dynamic dominant region / true pitch-control boundary | S14, S17 | Conceptual boundary |
| Pass-induced space-control change | S15, S16 | Adapt / benchmark |
| Space occupation and space generation | S18 | Core conceptual adaptation |
| Off-ball opportunity / spatial threat | S19, S20 | Related work / methodological ceiling |
| Pre-shot spatiotemporal history | S21 | Closest prior work |
| xT / Markov value surface | S22, S23 | Metric lineage / optional benchmark |
| VAEP / OBV action value | S24, S25 | Benchmark / contrast |
| Event sequence history | S26 | Related sequence baseline |
| 360 snapshot representation + Situational xT | S27 | Closest snapshot baseline |
| Tactical pattern extraction from event + freeze frame | S28 | Closest pattern-discovery precedent |
| Timing / temporal xT | S29 | Temporal baseline |
| Spatial recommendations and similar-situation retrieval | S30 | Professional-value precedent |
| Train/test partitioning and sports-model evaluation | S31, S32 | Adopt validation guidance |
| Confidence intervals | S33 | Adopt if bootstrap used |
| Broad tactical analytics framing | S34, S35 | Literature review |

## 5. Formula and metric source ledger

These formulas/constructions are transcribed from the PDF. Its planned
normalization of longitudinal/lateral axes is a prerequisite for future use,
not an implemented transformation. Orientation, goalkeeper inclusion and
eligibility remain unresolved. Distances use StatsBomb coordinate units, not
automatically physical metres.

For the field mapping, **G** means `freeze_frame.location`, `teammate`, `keeper`,
with event `team` / `possession_team` as needed for subset selection after
role/orientation review. Join event `id` to frame `event_uuid` within `match_id`.
**Q** means relevant `visible_area`, valid coordinate and visible-player checks.
These are repository mappings, not field names attributed to original papers;
they do not set qualification thresholds.

| Formula / construction from PDF | Conceptual meaning | Published citation basis in PDF | Planned provenance | StatsBomb fields required (repository mapping) | Compatibility / visibility limits |
| --- | --- | --- | --- | --- | --- |
| `C_x = (1/N) sum_i x_i; C_y = (1/N) sum_i y_i` | Team centroid: mean selected-player position | S07, S08 | ADOPT base arithmetic; DERIVE quantity; ADAPT visible subset | G, Q | Empty set undefined; composition can move centroid without motion; not full-team centroid |
| `L = x_max - x_min` after orienting x longitudinally | Team length; registry defensive depth is longitudinal span | S07, S12 | ADOPT range; DERIVE quantity; ADAPT visible defenders | G, Q | Unseen extrema bias span; keeper/orientation rules open; depth is not block height |
| `W = y_max - y_min` after orienting y laterally | Team width: lateral span | S07, S12 | ADOPT range; DERIVE quantity; ADAPT visible defenders | G, Q | Visibility and orientation dependent; no full-team claim |
| `LpW = L / W` | Length-to-width ratio | S07 | ADOPT ratio if used; ADAPT visible subset | G, Q | Zero width/degenerate cases unresolved; inherits span visibility bias |
| `d(a,b) = sqrt((x_a-x_b)^2 + (y_a-y_b)^2)` | Interpersonal Euclidean distance | S07 | ADOPT base distance; DERIVE quantity; ADAPT selection/aggregation | G, Q; `actor` and event `location` for actor proximity | PDF supplies pair distance, not the registry's all-pairs mean or nearest-defender selection rule |
| Area of convex hull enclosing selected team players | Surface / effective occupied area | S07, S08 | ADOPT construction; DERIVE area; ADAPT visible subset | G, Q | Degenerate sets/keeper inclusion unresolved; occupied surface is not controlled space |
| Mean player distance from team centroid; optionally decomposed longitudinally/laterally | Stretch index | S07, S12 | ADOPT stated concept if used; ADAPT visible subset | G, Q | PDF gives no component equations; composition/missing players affect dispersion |
| Partition observed space by nearest player under Euclidean distance | Voronoi dominant area | S13 | ADOPT partition concept; ADAPT observed-region/pitch clipping | `freeze_frame.location`, `visible_area`; team flags for team aggregation | Registry visible-polygon/pitch intersection is an adaptation; unseen players alter cells; not dynamic pitch control |
| `xT_xy = s_xy*g_xy + m_xy * sum_zw T_(xy->zw) * xT_zw` | xT / Markov location-value baseline | S22; S23 is historical lineage | ADOPT recurrence only if unchanged; ADAPT changed state/model | Candidate mapping: `location`, `pass.end_location`, `carry.end_location`, `type`, shot/action outcomes, team, possession, event order | PDF does not define symbols, estimator, grid, training sample or full field requirements; unresolved. Path independence ignores defender manipulation (S22) |
| Sum of StatsBomb xG for shots produced within a pre-specified future horizon after state t | Future xG outcome | **Our study definition**; xG meaning from S03 | SOURCE shot value; PROJECT window/aggregation | `shot.statsbomb_xg`, `match_id`, `index`, `timestamp`, `period`, `possession`, `team`, `type` | Horizon, attribution, termination, censoring and overlap unresolved; not a published future-xG formula |
| `Delta M_t = M_t - M_(t-1)` for a published base metric M | Spatial change between observed states | **Our derived feature**; cite source of M | DERIVE difference; PROJECT sequence/observation selection; ADAPT base metric as needed | Fields for M, `match_id`, event/frame IDs, `possession`, `period`, `index`, `timestamp` | Irregular intervals/changing subsets; not continuous motion or identity inference |
| Candidate adaptation: integrate/sum spatial availability/control weighted by a location-value surface | Dangerous-space score | Adapt from S18, S19, S20 | ADAPT concepts; PROJECT exact formula if changed | Unresolved until definition; candidate visible geometry/area plus justified location-value surface | No final equation in PDF; static area is not value/control; tracking models cannot be faithfully reproduced; avoid circular outcome definitions |

The registry's mean pairwise distance is its declared aggregation of the S07
distance, not a claim that the PDF gives that exact mean formula. S21 supplies
defender-proximity precedent for nearest-defender distance; the visible minimum,
actor eligibility and defender selection remain project adaptations. Retaining
the PDF's ratio, stretch, xT and spatial-change ledger adds no registry metrics.

## 6. Method compatibility implications

### Supported or potentially supported after observation checks

StatsBomb 360 is event-aligned visible-player context, not continuous 22-player
tracking. S01/S02 establish the data source; S27/S28 provide snapshot/pattern
precedents. Qualified future work can use visible-player geometry, event-aligned
spatial states, visible width/depth, centroids, convex hulls, pairwise distances,
zone occupation, local numerical superiority, visible-area-aware Voronoi and
spatial changes between observed frames.

These are feasibility statements, not completed methods. Local neighborhoods,
line/cluster gaps, valuable space and defensive regimes need explicit definitions.
Visible-area clipping does not recover unobserved players' influence. Occupied,
exploration and dominant/influence space are related but distinct (S11); space
occupation and teammate space generation are distinct (S18). Neither hull area
nor a nearest-player partition establishes control or danger by itself.

### Unsupported for faithful reproduction

**REJECT** faithful reconstruction of continuous velocity, acceleration, exact
time-to-intercept, continuous player trajectories, full dynamic tracking pitch
control, tracking EPV requiring velocities/full trajectories, and named anonymous
off-ball trajectories. S14/S17 are motion/time-to-arrival boundaries; S20 is the
full-tracking EPV ceiling. S16's tracking pass risk/reward and S19's spatiotemporal
off-ball opportunity are conceptual/comparison references, not evidence that
their complete inputs exist here.

The PDF discusses separately estimated and validated movement as a possible
qualification for future claims. This does not weaken the repository's REJECT
status for faithful reproduction. Any proxy needs its own definition, limitations
and validation; no such proxy exists yet. The reserved `trajectories.py`
namespace means event-state sequences only. Do not interpolate anonymous
off-ball identities between frames.

### Repository-specific constraints retained

The migration-era claim that academic sources were unavailable is superseded by
this document. Existing exploratory notebooks, loaders/transforms and environment
history remain project context, not academic validation of formulas. The official
[S01 repository](https://github.com/hudl/open-data) documents layout and attribution.
Its [documentation directory](https://github.com/hudl/open-data/tree/master/doc),
retained from the previous source foundation, remains the starting point for raw
field semantics. That directory link is repository material, not an extra PDF
bibliography entry. Migration layout checks were not a complete specification
review or academic justification of spatial metrics.

[methods_specification.md](methods_specification.md) and the
[technical appendix](../report/technical_appendix.md) retain the Phase 1/1B audit,
including configured revision `533862946a73608c134d18b78226b6371ce7173c`.
That revision is repository provenance, not an identifier from the PDF. Joins,
original coordinates, event-team-relative teammate flags, multiple-actor
ambiguities, changing visibility and goalkeeper inclusion must be resolved for
each intended metric. Coordinate discrepancies do not authorize automatic
mirroring or universal actor-distance thresholds. Null calibration remains null.
S02's “roughly 3,400 events per match” is retained as the PDF annotation, not
substituted for the pinned audit's measured counts.

Future sequences must use match, possession and period keys, index/timestamp
ordering, and explicit restart, turnover and censoring rules. Future xG, shot and
box-entry windows/attribution remain unresolved. Avoid overlapping-window leakage.
S31/S32 support grouped/blocked evaluation; S33 supports bootstrap uncertainty if
used, respecting match/possession dependence. Random event-row splitting or blind
individual-event bootstrap is not justified.

Remaining source review must inspect linked definitions, relevant sections, raw
requirements and proposed adaptations before method lock. Reviews support feature
selection and limitations, not every exact formula or project cutoff. No Phase 2
implementation is part of this documentation synchronization.

## 7. Annotated bibliography

Core means likely citation in the main article/methods appendix; Supporting means
cite only if the associated method/claim is used. Neither means implemented.
Complete substantive PDF annotations follow. Source type is classified from the
supplied citation/venue. “Project provenance interpretation” maps the PDF role to
section 3 and is not an additional publication claim. Data requirements and
limitations are preserved where the annotations state them; full input schemas,
equation pinpoints and unstated requirements remain unresolved. Section 5's raw
field mappings and section 6's restrictions are repository guidance.

### S01 — StatsBomb Open Data [GitHub repository]

- **Authors / organization:** Hudl StatsBomb.
- **Year / date:** n.d.
- **Title:** StatsBomb Open Data [GitHub repository]
- **Publication / organization:** Hudl StatsBomb
- **Source type:** Provider GitHub repository.
- **PDF topic group:** Data & provider methodology.
- **PDF citation role:** DATA - must cite.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://github.com/hudl/open-data).
- **Project provenance interpretation:** SOURCE: provider data layout, fields and attribution.

**PDF annotation — relevance, methodological contribution and intended use:**

Primary provenance for the JSON event, lineup, match, competition, and selected StatsBomb 360 files. The repository also states the publication-credit requirement. Cite in Data and Reproducibility.

### S02 — Free Data: Bayer Leverkusen's Invincible Bundesliga Title Win

- **Authors / organization:** Hudl StatsBomb.
- **Year / date:** 2024, May 21
- **Title:** Free Data: Bayer Leverkusen's Invincible Bundesliga Title Win
- **Publication / organization:** Hudl StatsBomb
- **Source type:** Provider article / methodology documentation.
- **PDF topic group:** Data & provider methodology.
- **PDF citation role:** DATA - must cite.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://statsbomb.com/news/free-statsbomb-data-bayer-leverkusens-invincible-bundesliga-title-win/).
- **Project provenance interpretation:** SOURCE: Leverkusen sample and event-aligned visible-player observation model.

**PDF annotation — relevance, methodological contribution and intended use:**

Primary source for the project sample: all 34 Leverkusen Bundesliga matches in 2023/24, roughly 3,400 events per match, with 360 locations for players in the visible frame around events.

### S03 — What is xG? How is it calculated?

- **Authors / organization:** Hudl StatsBomb.
- **Year / date:** n.d.
- **Title:** What is xG? How is it calculated?
- **Publication / organization:** Hudl StatsBomb
- **Source type:** Provider article / methodology documentation.
- **PDF topic group:** Data & provider methodology.
- **PDF citation role:** METRIC DEFINITION.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://statsbomb.com/soccer-metrics/expected-goals-xg-explained/).
- **Project provenance interpretation:** SOURCE: provider xG meaning; PROJECT: future-horizon aggregation.

**PDF annotation — relevance, methodological contribution and intended use:**

Use to define StatsBomb xG and to justify future-xG as chance-quality outcome. Also supports why PSxG is downstream of the buildup and is mainly a post-shot/goalkeeping metric.

### S04 — The FIFA Football Language

- **Authors / organization:** FIFA Training Centre.
- **Year / date:** 2022
- **Title:** The FIFA Football Language
- **Publication / organization:** FIFA Training Centre
- **Source type:** Practitioner ontology / technical article.
- **PDF topic group:** Defensive phase & structure.
- **PDF citation role:** ONTOLOGY / PHASE DEFINITION.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.fifatrainingcentre.com/en/game/performance-analysis/football-language-analysis/the-fifa-football-language.php).
- **Project provenance interpretation:** ADOPT vocabulary; ADAPT/PROJECT the 360 phase classifier, not FIFA tracking rules.

**PDF annotation — relevance, methodological contribution and intended use:**

Official practitioner ontology for in- and out-of-possession phases, including high-, mid-, and low-block/press concepts. Useful as vocabulary precedent, not as a claim that our 360 implementation exactly reproduces FIFA tracking rules.

### S05 — Controlling the game without the ball: The mid-block and compactness

- **Authors / organization:** FIFA Training Centre.
- **Year / date:** 2023
- **Title:** Controlling the game without the ball: The mid-block and compactness
- **Publication / organization:** FIFA Training Centre
- **Source type:** Practitioner ontology / technical article.
- **PDF topic group:** Defensive phase & structure.
- **PDF citation role:** ONTOLOGY / CONTEXT.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.fifatrainingcentre.com/en/fwc2022/technical-and-tactical-analysis/controlling-the-game-without-the-ball--the-mid-block-and-compactness.php).
- **Project provenance interpretation:** ADOPT phase vocabulary/context; PROJECT quantitative block/compactness rules.

**PDF annotation — relevance, methodological contribution and intended use:**

Supports the football meaning of a connected, narrow block and shows that block classification is a phase-of-play problem. Helpful for coaching interpretation and terminology.

### S06 — Putting team formations in association football into context

- **Authors / organization:** Bauer, P., Anzer, G., & Shaw, L.
- **Year / date:** 2023
- **Title:** Putting team formations in association football into context
- **Publication / organization:** Journal of Sports Analytics, 9(1), 39-59.
- **Source type:** Journal article.
- **PDF topic group:** Defensive phase & structure.
- **PDF citation role:** ADAPT / OPERATIONAL BASELINE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.3233/JSA-220620).
- **DOI supplied via PDF link:** `10.3233/JSA-220620`.
- **Project provenance interpretation:** ADAPT operational phase/formation baseline; PROJECT calibrated classifier.

**PDF annotation — relevance, methodological contribution and intended use:**

Important precedent for automated phase classification and context-specific formation analysis. Includes explicit rule-based low-/mid-/high-block baselines and demonstrates that phase labels can be operationalized and then learned.

### S07 — Navigating team tactical analysis in football: An analytical pipeline leveraging player tracking technology

- **Authors / organization:** Zhang, G., Kempe, M., McRobert, A., Folgado, H., & Olthof, S. B. H.
- **Year / date:** 2025
- **Title:** Navigating team tactical analysis in football: An analytical pipeline leveraging player tracking technology
- **Publication / organization:** Proceedings of the Institution of Mechanical Engineers, Part P: Journal of Sports Engineering and Technology.
- **Source type:** Journal article.
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** ADOPT - formulas.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1177/17543371251392456).
- **DOI supplied via PDF link:** `10.1177/17543371251392456`.
- **Project provenance interpretation:** ADOPT base geometry definitions; DERIVE quantities; ADAPT visible-subset use.

**PDF annotation — relevance, methodological contribution and intended use:**

Best recent formula source for centroid, team length, team width, length-to-width ratio, convex-hull surface area, longitudinal/lateral stretch indices, and interpersonal distance. Cite directly for adopted geometry definitions.

### S08 — Oscillations of centroid position and surface area of soccer teams in small-sided games

- **Authors / organization:** Frencken, W., Lemmink, K., Delleman, N., & Visscher, C.
- **Year / date:** 2011
- **Title:** Oscillations of centroid position and surface area of soccer teams in small-sided games
- **Publication / organization:** European Journal of Sport Science, 11(4), 215-223.
- **Source type:** Journal article.
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** ORIGIN / PRECEDENT.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1080/17461391.2010.499967).
- **DOI supplied via PDF link:** `10.1080/17461391.2010.499967`.
- **Project provenance interpretation:** ADOPT centroid/surface precedent; ADAPT from original positional setting to visible frames.

**PDF annotation — relevance, methodological contribution and intended use:**

Foundational positional work using team centroid and surface area as collective variables and investigating their dynamics around goals.

### S09 — Current approaches to tactical performance analyses in soccer using position data

- **Authors / organization:** Memmert, D., Lemmink, K. A. P. M., & Sampaio, J.
- **Year / date:** 2017
- **Title:** Current approaches to tactical performance analyses in soccer using position data
- **Publication / organization:** Sports Medicine, 47(1), 1-10.
- **Source type:** Journal review (systematic where specified in title).
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** REVIEW / METRIC SELECTION.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1007/s40279-016-0562-5).
- **DOI supplied via PDF link:** `10.1007/s40279-016-0562-5`.
- **Project provenance interpretation:** Review support for ADOPT/ADAPT feature selection; PROJECT any composite.

**PDF annotation — relevance, methodological contribution and intended use:**

Broad tactical-position-data review covering inter-player, inter-line and inter-team coordination and compactness-type measures. Useful to position our feature set within established positional analysis.

### S10 — A systematic review of collective tactical behaviours in football using positional data

- **Authors / organization:** Low, B., Coutinho, D., Goncalves, B., Rein, R., Memmert, D., & Sampaio, J.
- **Year / date:** 2020
- **Title:** A systematic review of collective tactical behaviours in football using positional data
- **Publication / organization:** Sports Medicine, 50(2), 343-385.
- **Source type:** Journal review (systematic where specified in title).
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** REVIEW / LIMITATION.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1007/s40279-019-01194-7).
- **DOI supplied via PDF link:** `10.1007/s40279-019-01194-7`.
- **Project provenance interpretation:** Review limitation for ADAPT/PROJECT compactness; no universal scalar.

**PDF annotation — relevance, methodological contribution and intended use:**

Key evidence that collective tactical behavior has been measured with many different variables and methods. Supports our decision not to treat compactness as one universally standardized scalar.

### S11 — Identification, computational examination, critical assessment and future considerations of spatial tactical variables to assess the use of space in team sports by positional data: A systematic review

- **Authors / organization:** Rico-Gonzalez, M., Pino-Ortega, J., Nakamura, F. Y., Moura, F. A., & Los Arcos, A.
- **Year / date:** 2021
- **Title:** Identification, computational examination, critical assessment and future considerations of spatial tactical variables to assess the use of space in team sports by positional data: A systematic review
- **Publication / organization:** Journal of Human Kinetics, 77, 205-221.
- **Source type:** Journal review (systematic where specified in title).
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** REVIEW / METRIC SELECTION.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.2478/hukin-2021-0021).
- **DOI supplied via PDF link:** `10.2478/hukin-2021-0021`.
- **Project provenance interpretation:** Review support for distinctions among occupied, exploration and influence space; ADAPT visible spatial measures.

**PDF annotation — relevance, methodological contribution and intended use:**

Classifies spatial variables into occupied, exploration, and dominant/influence space. Particularly important for explaining why Voronoi, time-based influence, and weighted space are related but not interchangeable.

### S12 — Soft-assembled multilevel dynamics of tactical behaviors in soccer

- **Authors / organization:** Ric, A., Torrents, C., Goncalves, B., Sampaio, J., & Hristovski, R.
- **Year / date:** 2016
- **Title:** Soft-assembled multilevel dynamics of tactical behaviors in soccer
- **Publication / organization:** Frontiers in Psychology, 7, 1513.
- **Source type:** Journal article.
- **PDF topic group:** Team shape & positional metrics.
- **PDF citation role:** ADOPT / TIME-SERIES PRECEDENT.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.3389/fpsyg.2016.01513).
- **DOI supplied via PDF link:** `10.3389/fpsyg.2016.01513`.
- **Project provenance interpretation:** ADOPT length/width definitions and temporal precedent; ADAPT to irregular event snapshots.

**PDF annotation — relevance, methodological contribution and intended use:**

Uses positioning-derived variables as time series; explicitly defines team length/width as extrema differences and studies tactical patterns and their timescales. Strong precedent for analyzing spatial evolution rather than only snapshots.

### S13 — Spatial dynamics of team sports exposed by Voronoi diagrams

- **Authors / organization:** Fonseca, S., Milho, J., Travassos, B., & Araujo, D.
- **Year / date:** 2012
- **Title:** Spatial dynamics of team sports exposed by Voronoi diagrams
- **Publication / organization:** Human Movement Science, 31(6), 1652-1659.
- **Source type:** Journal article.
- **PDF topic group:** Dominant space & spatial control.
- **PDF citation role:** ORIGIN / VORONOI.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1016/j.humov.2012.04.006).
- **DOI supplied via PDF link:** `10.1016/j.humov.2012.04.006`.
- **Project provenance interpretation:** ADOPT Voronoi concept; ADAPT visible-region clipping; no dynamic control claim.

**PDF annotation — relevance, methodological contribution and intended use:**

Direct precedent for using Voronoi dominant regions and their temporal variability to describe attacker-defender spatial interactions.

### S14 — Visualization of dominant region in team games and its application to teamwork analysis

- **Authors / organization:** Taki, T., & Hasegawa, J.
- **Year / date:** 2000
- **Title:** Visualization of dominant region in team games and its application to teamwork analysis
- **Publication / organization:** In Computer Graphics International 2000 (pp. 227-235).
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Dominant space & spatial control.
- **PDF citation role:** ORIGIN / DYNAMIC INFLUENCE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1109/CGI.2000.852338).
- **DOI supplied via PDF link:** `10.1109/CGI.2000.852338`.
- **Project provenance interpretation:** REJECT faithful dynamic/time-to-arrival reproduction; retain conceptual lineage.

**PDF annotation — relevance, methodological contribution and intended use:**

Early dynamic dominant-region work replacing pure distance with time-to-arrival. Useful boundary reference: true dynamic influence needs movement information that event-aligned 360 does not fully provide.

### S15 — Which pass is better? Novel approaches to assess passing effectiveness in elite soccer

- **Authors / organization:** Rein, R., Raabe, D., & Memmert, D.
- **Year / date:** 2017
- **Title:** Which pass is better? Novel approaches to assess passing effectiveness in elite soccer
- **Publication / organization:** Human Movement Science, 55, 172-181.
- **Source type:** Journal article.
- **PDF topic group:** Dominant space & spatial control.
- **PDF citation role:** ADAPT / PASS EFFECT.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1016/j.humov.2017.07.010).
- **DOI supplied via PDF link:** `10.1016/j.humov.2017.07.010`.
- **Project provenance interpretation:** ADAPT pass-induced space change/outplayed-defender concepts; PROJECT exact disruption score.

**PDF annotation — relevance, methodological contribution and intended use:**

Direct precedent for evaluating passes by changes in space control and defenders outplayed. Highly relevant if we quantify how Leverkusen actions change spatial superiority.

### S16 — Not all passes are created equal: Objectively measuring the risk and reward of passes in soccer from tracking data

- **Authors / organization:** Power, P., Ruiz, H., Wei, X., & Lucey, P.
- **Year / date:** 2017
- **Title:** Not all passes are created equal: Objectively measuring the risk and reward of passes in soccer from tracking data
- **Publication / organization:** Proceedings of KDD 2017, 1605-1613.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Dominant space & spatial control.
- **PDF citation role:** BENCHMARK / PASS VALUE.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1145/3097983.3098051).
- **DOI supplied via PDF link:** `10.1145/3097983.3098051`.
- **Project provenance interpretation:** Benchmark/contrast for ADAPT pass-effect concepts; tracking-dependent reproduction is unsupported.

**PDF annotation — relevance, methodological contribution and intended use:**

Tracking-based pass risk and reward; reward is linked to future shot creation. Useful methodological comparison if we build pass-level spatial-disruption scores.

### S17 — Physics-based modeling of pass probabilities in soccer

- **Authors / organization:** Spearman, W., Basye, A., Dick, G., Hotovy, R., & Pop, P.
- **Year / date:** 2017
- **Title:** Physics-based modeling of pass probabilities in soccer
- **Publication / organization:** MIT Sloan Sports Analytics Conference.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Dominant space & spatial control.
- **PDF citation role:** BOUNDARY / PITCH CONTROL.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.researchgate.net/publication/315166647_Physics-Based_Modeling_of_Pass_Probabilities_in_Soccer).
- **Project provenance interpretation:** REJECT faithful time-to-intercept/control reproduction; boundary for static Voronoi terminology.

**PDF annotation — relevance, methodological contribution and intended use:**

Time-to-intercept/time-to-control model for spatial control and pass probability. Cite as a conceptual ancestor and a reason not to call static 360 Voronoi a full pitch-control model.

### S18 — Wide open spaces: A statistical technique for measuring space creation in professional soccer

- **Authors / organization:** Fernandez, J., & Bornn, L.
- **Year / date:** 2018
- **Title:** Wide open spaces: A statistical technique for measuring space creation in professional soccer
- **Publication / organization:** MIT Sloan Sports Analytics Conference.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Space creation & off-ball value.
- **PDF citation role:** ADAPT - core concept.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.sloansportsconference.com/research-papers/wide-open-spaces-a-statistical-technique-for-measuring-space-creation-in-professional-soccer).
- **Project provenance interpretation:** ADAPT space occupation/generation and location-weighted control concepts; PROJECT exact dangerous-space score.

**PDF annotation — relevance, methodological contribution and intended use:**

One of the central ancestors for this project. Separates space occupation from space generation for teammates and combines spatial control with location value. Any dangerous-space or space-created metric we adapt should cite this explicitly.

### S19 — Beyond expected goals

- **Authors / organization:** Spearman, W.
- **Year / date:** 2018
- **Title:** Beyond expected goals
- **Publication / organization:** MIT Sloan Sports Analytics Conference.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Space creation & off-ball value.
- **PDF citation role:** RELATED / OFF-BALL VALUE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.researchgate.net/publication/327139841_Beyond_Expected_Goals).
- **Project provenance interpretation:** ADAPT off-ball opportunity concept if feasible; tracking-dependent reproduction is unsupported.

**PDF annotation — relevance, methodological contribution and intended use:**

Builds off-ball scoring opportunity from spatiotemporal player/ball context. Important precedent for valuing opportunities created before a shot and for recognizing contributions that event logs miss.

### S20 — A framework for the fine-grained evaluation of the instantaneous expected value of soccer possessions

- **Authors / organization:** Fernandez, J., Bornn, L., & Cervone, D.
- **Year / date:** 2021
- **Title:** A framework for the fine-grained evaluation of the instantaneous expected value of soccer possessions
- **Publication / organization:** Machine Learning, 110, 1389-1427.
- **Source type:** Journal article.
- **PDF topic group:** Space creation & off-ball value.
- **PDF citation role:** RELATED / FULL-TRACKING CEILING.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1007/s10994-021-05989-6).
- **DOI supplied via PDF link:** `10.1007/s10994-021-05989-6`.
- **Project provenance interpretation:** REJECT faithful full-tracking EPV reproduction; ADAPT conceptual value/space linkage only with explicit definition.

**PDF annotation — relevance, methodological contribution and intended use:**

EPV framework using full spatiotemporal tracking. Defines an important novelty boundary: all-player spatial dynamics and instantaneous possession value already exist with richer tracking; our contribution must focus on event-aligned spatial trajectories, interpretable tactical mechanisms, and the Leverkusen case study.

### S21 — Quality vs quantity: Improved shot prediction in soccer using strategic features from spatiotemporal data

- **Authors / organization:** Lucey, P., Bialkowski, A., Monfort, M., Carr, P., & Matthews, I.
- **Year / date:** 2015
- **Title:** Quality vs quantity: Improved shot prediction in soccer using strategic features from spatiotemporal data
- **Publication / organization:** MIT Sloan Sports Analytics Conference.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Chance quality & possession value.
- **PDF citation role:** RELATED / PRE-SHOT SEQUENCE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://www.sloansportsconference.com/research-papers/quality-vs-quantity-improved-shot-prediction-in-soccer-using-strategic-features-from-spatiotemporal-data).
- **Project provenance interpretation:** ADAPT pre-shot history/proximity concepts; PROJECT event-aligned window/features; no imported ten-second threshold.

**PDF annotation — relevance, methodological contribution and intended use:**

Very close prior work: analyzes the ten seconds before nearly 10,000 shots using defender proximity, surrounding-player interactions, speed of play, and shot location. Must be discussed when positioning our temporal-spatial contribution.

### S22 — Introducing Expected Threat (xT)

- **Authors / organization:** Singh, K.
- **Year / date:** 2019, February 15
- **Title:** Introducing Expected Threat (xT)
- **Publication / organization:** Not supplied in the PDF citation.
- **Source type:** Public methodological article.
- **PDF topic group:** Chance quality & possession value.
- **PDF citation role:** METRIC ORIGIN / BENCHMARK.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://karun.in/blog/expected-threat.html).
- **Project provenance interpretation:** ADOPT xT recurrence if unchanged and used; ADAPT changed state/value construction; optional benchmark.

**PDF annotation — relevance, methodological contribution and intended use:**

Canonical public xT formulation. Cite if we use xT as a baseline, a location-value surface, or discuss Markov possession value. Singh also explicitly notes that path independence ignores defender manipulation - directly relevant to our motivation.

### S23 — A framework for tactical analysis and individual offensive production assessment in soccer using Markov chains

- **Authors / organization:** Rudd, S.
- **Year / date:** 2011
- **Title:** A framework for tactical analysis and individual offensive production assessment in soccer using Markov chains
- **Publication / organization:** New England Symposium on Statistics in Sports.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Chance quality & possession value.
- **PDF citation role:** FOUNDATIONAL / MARKOV.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://www.nessis.org/nessis11.html).
- **Project provenance interpretation:** Historical lineage for ADOPT/ADAPT Markov state-value approaches; no model selected.

**PDF annotation — relevance, methodological contribution and intended use:**

Early public Markov-chain football possession-value framework. Cite in historical lineage if discussing the origins of state-value approaches.

### S24 — Actions speak louder than goals: Valuing player actions in soccer

- **Authors / organization:** Decroos, T., Bransen, L., Van Haaren, J., & Davis, J.
- **Year / date:** 2019
- **Title:** Actions speak louder than goals: Valuing player actions in soccer
- **Publication / organization:** Proceedings of the 25th ACM SIGKDD Conference on Knowledge Discovery & Data Mining, 1851-1861.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Chance quality & possession value.
- **PDF citation role:** BENCHMARK / ACTION VALUE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1145/3292500.3330758).
- **DOI supplied via PDF link:** `10.1145/3292500.3330758`.
- **Project provenance interpretation:** Benchmark/contrast for action valuation; ADOPT/ADAPT only if later explicitly specified.

**PDF annotation — relevance, methodological contribution and intended use:**

VAEP action valuation. Important comparison for event-level value and for distinguishing our spatial-trajectory problem from action-value models.

### S25 — Introducing On-Ball Value (OBV)

- **Authors / organization:** Hudl StatsBomb.
- **Year / date:** 2021, September 16
- **Title:** Introducing On-Ball Value (OBV)
- **Publication / organization:** Hudl StatsBomb
- **Source type:** Provider article / methodology documentation.
- **PDF topic group:** Chance quality & possession value.
- **PDF citation role:** PROVIDER BENCHMARK.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://statsbomb.com/news/introducing-on-ball-value-obv/).
- **Project provenance interpretation:** SOURCE provider benchmark description; comparison does not establish available OBV fields/model.

**PDF annotation — relevance, methodological contribution and intended use:**

Provider possession-state benchmark. Especially relevant because StatsBomb deliberately excludes possession-history proxies from OBV, highlighting a design tradeoff that our trajectory analysis investigates directly with spatial context.

### S26 — Seq2Event: Learning the language of soccer using Transformer-based match event prediction

- **Authors / organization:** Simpson, I., Beal, R. J., Locke, D., & Norman, T. J.
- **Year / date:** 2022
- **Title:** Seq2Event: Learning the language of soccer using Transformer-based match event prediction
- **Publication / organization:** Proceedings of KDD 2022, 3898-3908.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Sequence & pattern modeling.
- **PDF citation role:** RELATED / EVENT HISTORY.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1145/3534678.3539138).
- **DOI supplied via PDF link:** `10.1145/3534678.3539138`.
- **Project provenance interpretation:** Related event-history baseline; ADOPT/ADAPT only if selected after review; no neural model committed.

**PDF annotation — relevance, methodological contribution and intended use:**

Sequence model predicting future events from prior event history/context. Important contrast: it models event history rather than the evolving geometry of all visible players; the authors list adaptation to all-player tracking as future work.

### S27 — Clustering football game situations via deep representation learning

- **Authors / organization:** Tang, Z., Wang, X., & Zhang, S.
- **Year / date:** 2023
- **Title:** Clustering football game situations via deep representation learning
- **Publication / organization:** StatsBomb Conference 2023.
- **Source type:** Conference / symposium contribution.
- **PDF topic group:** Sequence & pattern modeling.
- **PDF citation role:** CLOSEST 360 SNAPSHOT BASELINE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://statsbomb.com/wp-content/uploads/2023/10/Clustering-Football-Game-Situations-via-Deep-Representation-Learning.pdf).
- **Project provenance interpretation:** Closest 360 snapshot baseline; ADAPT only with explicit implementation/validation; distinguish state history.

**PDF annotation — relevance, methodological contribution and intended use:**

Closest StatsBomb 360 precedent: learns representations of individual freeze frames using soft Voronoi reconstruction, pass success, and next-action prediction; clusters situations and builds Situational xT. Our trajectory work must explicitly distinguish state classification/value from state-history evolution.

### S28 — Unveiling multi-agent strategies: A data-driven approach for extracting and evaluating team tactics from football event and freeze-frame data

- **Authors / organization:** Yeung, C. C. K., Bunker, R., & Fujii, K.
- **Year / date:** 2024
- **Title:** Unveiling multi-agent strategies: A data-driven approach for extracting and evaluating team tactics from football event and freeze-frame data
- **Publication / organization:** Journal of Robotics and Mechatronics, 36(3), 603-617.
- **Source type:** Journal article.
- **PDF topic group:** Sequence & pattern modeling.
- **PDF citation role:** CLOSEST PATTERN-DISCOVERY PRECEDENT.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.20965/jrm.2024.p0603).
- **DOI supplied via PDF link:** `10.20965/jrm.2024.p0603`.
- **Project provenance interpretation:** Closest event/freeze-frame pattern precedent; ADAPT only after method review.

**PDF annotation — relevance, methodological contribution and intended use:**

Highly relevant for extracting tactics from event plus freeze-frame data using sequential pattern mining and multi-agent modeling. Strong methodological precedent for the pattern-discovery portion of our article.

### S29 — A Semi-Markov framework for modeling football possessions and temporal expected threat

- **Authors / organization:** Le Coz, S., Boustila, F., & Imbach, F.
- **Year / date:** 2026
- **Title:** A Semi-Markov framework for modeling football possessions and temporal expected threat
- **Publication / organization:** Scientific Reports, 16, 22590.
- **Source type:** Journal article.
- **PDF topic group:** Sequence & pattern modeling.
- **PDF citation role:** TIMING / TEMPORAL BASELINE.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1038/s41598-026-52938-1).
- **DOI supplied via PDF link:** `10.1038/s41598-026-52938-1`.
- **Project provenance interpretation:** Temporal baseline; ADOPT/ADAPT only if used; changing player geometry is a separate project component.

**PDF annotation — relevance, methodological contribution and intended use:**

Recent temporal-xT work incorporating action type, ball location and elapsed time. Useful baseline for the value of timing, while our planned spatial-state trajectory adds changing player geometry rather than only on-ball state/timing.

### S30 — TacticAI: An AI assistant for football tactics

- **Authors / organization:** Wang, Z., Velickovic, P., Hennes, D., et al.
- **Year / date:** 2024
- **Title:** TacticAI: An AI assistant for football tactics
- **Publication / organization:** Nature Communications, 15, 1906.
- **Source type:** Journal article.
- **PDF topic group:** Sequence & pattern modeling.
- **PDF citation role:** PROFESSIONAL / HUMAN-IN-LOOP CEILING.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1038/s41467-024-45965-x).
- **DOI supplied via PDF link:** `10.1038/s41467-024-45965-x`.
- **Project provenance interpretation:** Professional-value precedent; no transfer claim from corners to open-play sequences.

**PDF annotation — relevance, methodological contribution and intended use:**

Demonstrates professional value of spatial representations, similar-situation retrieval, prediction and counterfactual positional recommendations in a constrained corner-kick domain, validated with Liverpool FC experts.

### S31 — Methodology and evaluation in sports analytics: Challenges, approaches, and lessons learned

- **Authors / organization:** Davis, J., Bransen, L., Devos, L., Jaspers, A., Meert, W., Robberechts, P., Van Haaren, J., et al.
- **Year / date:** 2024
- **Title:** Methodology and evaluation in sports analytics: Challenges, approaches, and lessons learned
- **Publication / organization:** Machine Learning, 113, 6977-7010.
- **Source type:** Journal article.
- **PDF topic group:** Validation & inference.
- **PDF citation role:** VALIDATION - must cite if modeling.
- **Priority:** Core.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1007/s10994-024-06585-0).
- **DOI supplied via PDF link:** `10.1007/s10994-024-06585-0`.
- **Project provenance interpretation:** ADOPT match/sequence-aware evaluation guidance if modeling; PROJECT exact validation design.

**PDF annotation — relevance, methodological contribution and intended use:**

Best soccer-specific methodological reference for non-i.i.d. data, data partitioning, context, indicator evaluation, explainability and uncertainty. Supports match/sequence-aware validation rather than random event-row splitting.

### S32 — Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure

- **Authors / organization:** Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., et al.
- **Year / date:** 2017
- **Title:** Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure
- **Publication / organization:** Ecography, 40(8), 913-929.
- **Source type:** Journal article.
- **PDF topic group:** Validation & inference.
- **PDF citation role:** VALIDATION / BLOCKING.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1111/ecog.02881).
- **DOI supplied via PDF link:** `10.1111/ecog.02881`.
- **Project provenance interpretation:** ADOPT grouped/blocked validation guidance; PROJECT grouping appropriate to dependence.

**PDF annotation — relevance, methodological contribution and intended use:**

General structured-data reference showing why random cross-validation can underestimate error when observations are dependent. Useful support for match-level/block validation.

### S33 — Bootstrap methods for standard errors, confidence intervals, and other measures of statistical accuracy

- **Authors / organization:** Efron, B., & Tibshirani, R.
- **Year / date:** 1986
- **Title:** Bootstrap methods for standard errors, confidence intervals, and other measures of statistical accuracy
- **Publication / organization:** Statistical Science, 1(1), 54-75.
- **Source type:** Journal article.
- **PDF topic group:** Validation & inference.
- **PDF citation role:** UNCERTAINTY / BOOTSTRAP.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1214/ss/1177013815).
- **DOI supplied via PDF link:** `10.1214/ss/1177013815`.
- **Project provenance interpretation:** ADOPT bootstrap if used; PROJECT resampling design respecting match/possession dependence.

**PDF annotation — relevance, methodological contribution and intended use:**

Canonical bootstrap reference if we report bootstrap confidence intervals. For this project, resampling should respect the match/possession structure rather than blindly resampling individual event rows.

### S34 — Unlocking the potential of big data to support tactical performance analysis in professional soccer: A systematic review

- **Authors / organization:** Goes, F. R., Meerhoff, L. A., Bueno, M. J. O., Rodrigues, D. M., Moura, F. A., Brink, M. S., et al.
- **Year / date:** 2021
- **Title:** Unlocking the potential of big data to support tactical performance analysis in professional soccer: A systematic review
- **Publication / organization:** European Journal of Sport Science, 21(4), 481-496.
- **Source type:** Journal review (systematic where specified in title).
- **PDF topic group:** Field reviews & framing.
- **PDF citation role:** REVIEW / PROJECT FRAMING.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1080/17461391.2020.1747552).
- **DOI supplied via PDF link:** `10.1080/17461391.2020.1747552`.
- **Project provenance interpretation:** Review/project framing; supports contextual interpretation, not an adopted metric.

**PDF annotation — relevance, methodological contribution and intended use:**

Broad review of tactical analytics using big data. Useful for introduction/literature review and for framing the bridge between data science and coaching practice.

### S35 — Big data and tactical analysis in elite soccer: Future challenges and opportunities for sports science

- **Authors / organization:** Rein, R., & Memmert, D.
- **Year / date:** 2016
- **Title:** Big data and tactical analysis in elite soccer: Future challenges and opportunities for sports science
- **Publication / organization:** SpringerPlus, 5, 1410.
- **Source type:** Journal review (systematic where specified in title).
- **PDF topic group:** Field reviews & framing.
- **PDF citation role:** REVIEW / HISTORICAL CONTEXT.
- **Priority:** Supporting.
- **Source link supplied in PDF:** [Open source](https://doi.org/10.1186/s40064-016-3108-2).
- **DOI supplied via PDF link:** `10.1186/s40064-016-3108-2`.
- **Project provenance interpretation:** Review/historical context; supports multi-source spatiotemporal framing, not an adopted formula.

**PDF annotation — relevance, methodological contribution and intended use:**

Foundational review arguing for contextual, multi-source, spatiotemporal tactical analysis rather than decontextualized counts. Useful for motivating the project at a high level.

## 8. Working citation rules

- Use the original or strongest primary methodological source when we adopt a published metric; use a systematic review to explain alternatives, inconsistency, or limitations.

- For simple geometry formulas, cite the positional-analysis source once in the Methods section and use consistent notation thereafter; do not add a citation after every repeated equation.

- For project-specific composites (for example a dangerous-space index), cite the concepts being combined and state explicitly: “we define” or “we adapt,” followed by the exact formula and sensitivity analysis.

- Do not call an event-aligned 360 calculation “continuous pitch control” unless velocity/time-to-intercept is actually available or separately estimated and validated.

- When the final paper discusses novelty, cite the closest competing approaches (Lucey 2015; Fernandez & Bornn 2018; Fernandez et al. 2021; Tang et al. 2023; Yeung et al. 2024; Le Coz et al. 2026), not only broad reviews.

- Use match-level or whole-sequence splits for predictive evaluation; when reporting uncertainty over season-level tactical effects, use resampling or hierarchical methods that respect match/possession dependence.

- Keep the final References section limited to sources actually used in the article. This source foundation is intentionally larger than the final bibliography.

Repository qualification: the PDF's conditional wording about continuous pitch
control does not authorize faithful reconstruction from these observations.
The REJECT boundary and requirements for any separately defined proxy in section
6 remain in force. Exact formulas, data requirements and adaptations still need
source review before adoption; source access links do not fill absent details.

## 9. Core sources to keep open during implementation

The PDF selects these twelve from the broader Core-priority bibliography:

| Source ID | Source / purpose |
| --- | --- |
| S01 | Hudl StatsBomb, StatsBomb Open Data — data layout and attribution |
| S02 | Hudl StatsBomb (2024), Leverkusen release — sample and 360 context |
| S03 | Hudl StatsBomb, What is xG? — provider metric meaning |
| S06 | Bauer, Anzer & Shaw (2023) — context-specific formations and phase baselines |
| S07 | Zhang et al. (2025) — positional geometry formulas |
| S10 | Low et al. (2020) — collective tactical behaviours systematic review |
| S11 | Rico-Gonzalez et al. (2021) — spatial tactical variables systematic review |
| S18 | Fernandez & Bornn (2018), Wide open spaces — occupation/generation and value |
| S21 | Lucey et al. (2015), Quality vs quantity — pre-shot temporal/spatial history |
| S27 | Tang, Wang & Zhang (2023) — 360 representations and Situational xT |
| S28 | Yeung, Bunker & Fujii (2024) — event/freeze-frame tactic extraction |
| S31 | Davis et al. (2024) — sports-model methodology and evaluation |

Full bibliographic details and original PDF links are in section 7. This reading
list is retained for future implementation; this task does not begin Phase 2.

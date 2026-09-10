# Technical appendix — draft

Future content: source provenance, release/retrieval details, environment,
observability diagnostics, sample exclusions, metric definitions, calibrated
configuration, sequence rules, validation and sensitivity analysis.

Current implementation includes data loading, preserved event transforms and the
Phase 1/1B observability audit and the eight locked Phase 2A geometry families.
Historical checks below retain their original phase-specific scope. **Phase 2B
= LOCKED / COMPLETE**, following human approval on **9 September 2026**. The
final decision section supersedes earlier proposed/pending calibration wording;
candidate data and historical empirical conclusions remain unchanged. See
`docs/methods_specification.md` section 37 for the approved Phase 2B contract.
**Phase 2C = LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE**, following human
approval on **10 September 2026**. [Methods section 40](../docs/methods_specification.md#40-human-approved-phase-2c-restricted-semantic-scope-lock)
and the final approval record below control the current boundary and authorize
Phase 3 possession/spatial-sequence method design. Historical audit statuses,
findings and saved outputs retain their original chronology.

## Phase 1 migration verification

Verified on 2026-09-06 in the repository's Windows Python 3.14 environment.

- 44 offline tests passed; two separately selected live Open Data checks passed.
- Ruff, dependency consistency, all package imports, YAML parsing and notebook
  schema validation passed. New imports also work from the notebook directory.
- Live loading confirmed 34 Leverkusen matches and valid events for match 3895292.
- Existing local data yielded 34 matches, 3,843 events, two lineup records and
  3,195 frames for match 3895292 before and after migration.
- The full Leverkusen passing dataset remained 24,244 rows × 142 columns with
  identical values/order. SHA-256 of pandas row hashes after string conversion:
  `ae4c3a2912379fda65934adc9080ae730bb5ccd91aa637eb4653181127e2a66c`.
  This is an environment-specific regression check, not an upstream data digest.
- All 111 code cells in the existing audit notebook and 20 code cells in the
  passing notebook executed using existing local records through mocked HTTP.
  Saved notebook outputs were not regenerated. Full live notebook execution was
  intentionally avoided to prevent repeated season downloads during verification.
- CLI help succeeds; reserved pipelines exit 2 with an explicit pending message.
- No raw files were added to Git. Existing raw files, original requirements and
  the historical downloader were preserved. No commit or push was performed.

The shell sandbox initially blocked package installation and live HTTP checks;
approved network execution completed both. The live pytest run reported a cache
write warning, which did not affect either check. There are no known remaining
behavioral regressions for the existing notebook workflow after editable install.

Geometry/sequence tests remain documented scaffolds because those helpers do not
exist yet. The orientation test verifies that normalization leaves coordinates
unchanged; it does not validate a future attacking-direction convention.

## Phase 1 live observability results

Historical unpinned baseline. The Phase 1B section below supersedes its coverage
and readiness assessment; these earlier measurements are retained for comparison.

The full on-demand audit ran on 2026-09-06 against the loader's upstream `master`
URLs. Retrieval timestamps are recorded per match in the derived match summary.
These results describe the fetched release, not an immutable upstream commit.

| Observation | Count |
| --- | ---: |
| Unique Leverkusen matches | 34 |
| Matches whose 360 data loaded | 34 |
| Event records / unique event IDs | 137,765 |
| 360 frames / unique frame UUIDs | 118,607 |
| Events linked to a frame | 108,394 (78.68% of events) |
| Events without a frame | 29,371 |
| Frames without a matching event | 10,213 |
| Duplicate event IDs / frame UUIDs | 0 / 0 |
| Frames with nonempty freeze frames | 118,607 |
| Frames with valid visible-area polygons | 118,607 |
| Frames with measurable actor distance | 108,390 |
| Frames with two actor flags | 4 |
| Frames passing joint mechanical checks | 108,390 |

The actor-measurable and joint-check counts are not final research eligibility:
the checks do not impose an actor-distance tolerance or minimum visibility.

### UUID mismatches

All orphan frames occur in three matches with **zero** overlap between event IDs
and frame event UUIDs. Their frames were retained without inferred event metadata.

| Match ID | Date | Opponent | Events | Orphan frames |
| --- | --- | --- | ---: | ---: |
| 3895158 | 2023-12-03 | Borussia Dortmund | 3,866 | 3,318 |
| 3895266 | 2024-03-10 | Wolfsburg | 4,104 | 3,615 |
| 3895309 | 2024-04-21 | Borussia Dortmund | 3,890 | 3,280 |

At this stage the cause was unresolved. The subsequent history investigation and
the pinned rerun below address release compatibility without heuristic relinking
or interpolation.

### Visibility and actor consistency

Visible-player counts range from 1 to 22 (median 17). Valid visible-area coverage
has mean 30.03%, median 29.08%, 5th percentile 16.77% and 95th percentile 45.93% of
the pitch. Polygon validity alone does not imply full-team observability.

For the 108,390 measurable actor/event pairs, distance in unchanged StatsBomb
coordinate units has mean 4.036708, median approximately 0.000002, 95th percentile
36.416486, 99th percentile 99.125536 and maximum 137.004351. Large discrepancies
concentrate in certain event types, including Dribbled Past, Dispossessed, Foul Won
and some Ball Receipt events. This pattern warrants source coordinate/actor-semantic
review; it does not justify an automatic rotation or correction.

Four frames in match 3895139 have two actor flags (two Pass events, one Dispossessed,
one Ball Receipt). They remain in frame counts but have no actor-distance measure.

Leverkusen event coverage is 64,373 / 81,440; opponent coverage is 44,021 / 56,325.
Administrative events have systematically absent frames; missingness varies by
event type, so the all-event coverage percentage is not an action-specific estimate.
The event-type and team partitions are available in `phase1_attrition.csv`.

### Readiness and unresolved questions

The data support inspection of visible polygons and player observations. The full
season is **not ready for unrestricted event-linked spatial analysis**: resolve or
explicitly exclude the three UUID-incompatible matches, investigate actor-coordinate
conventions, and define handling for multiple actors and incomplete visibility first.
Thirty-one matches have event-linked frames, but their eligibility still depends on
those decisions. No final thresholds, exclusions or direction normalization were set.

Open questions are the cause of the three UUID mismatches, event-type-specific
actor/coordinate conventions, appropriate treatment of multiple actors, goalkeeper
inclusion and how visibility-driven sample selection varies across football contexts.
This audit does not infer off-ball identity or correct missing players. Work stops
at Phase 1.

### Implementation verification

The Phase 1 implementation passes 86 offline tests (including 42 new synthetic
observability cases), Ruff, dependency consistency and notebook schema checks.
The live CLI completed all 34 matches and produced the three required derived CSVs.
The observability notebook's code executed offline against those outputs; no saved
raw responses or raw-coordinate arrays were added to the repository. The existing
raw-file inventory and calibration file hashes were checked for changes.


## Phase 1B pinned revision and coordinate semantics

### Source choice and verification scope

All four on-demand loaders now use **533862946a73608c134d18b78226b6371ce7173c**,
the original Leverkusen release dated May 21, 2024. The SHA is configured only in
`config/project.yaml`; source URLs and the recorded revision come from that value.

The project history investigation supplied for Phase 1B identified a May 26, 2026
bulk Open Data update affecting the 360 files of the three incompatible matches
while their event files retained the original release. The measured conclusion is
that the later Open Data revision produced event/360 identifiers that were not
mutually compatible for those matches. This is not a general claim of upstream
corruption. The present task verifies the pin through a fresh full-season fetch;
it does not recreate the entire upstream history investigation.

### Pinned rerun

All 34 matches loaded events and 360 successfully. There are 137,765 events and
118,581 frames; **all 118,581 frames link to events**, giving 86.074838% event
coverage. There are 19,184 events without frames, zero orphan frames, zero missing
identifiers, zero duplicated event IDs and zero duplicated frame UUIDs. Every
loaded frame has a nonempty freeze frame and a valid visible-area polygon.
118,577 pairs have measurable single-actor distance; four have multiple actors.

| Match | Events | Pinned frames | Matched events | Orphan frames |
| --- | --- | --- | --- | --- |
| 3895158 | 3866 | 3312 | 3312 | 0 |
| 3895266 | 4104 | 3623 | 3623 | 0 |
| 3895309 | 3890 | 3252 | 3252 | 0 |

All three problem matches recovered complete frame-to-event compatibility, not
complete event coverage. The pinned release has 26 fewer frames overall than the
historical unpinned baseline; coverage gains must not be inferred by simply adding
the old orphan count. No UUID mapping, match-specific fallback, local raw cache or
cross-revision mixing was used.

### Direct actor distances by major event type

Distances below are in original StatsBomb coordinate units. The CSV contains all
event types with measurable pairs and retains full precision. Small values rounded
to approximately zero reflect floating-point differences; no tolerance is imposed.

| Event type | Pairs | Mean direct | Median direct | p75 | p90 | p95 | p99 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pass | 33,070 | 0.001146 | 0.000002 | 0.000002 | 0.000003 | 0.000003 | 0.000004 | 7.592760 |
| Carry | 28,741 | 0.156629 | 0.000002 | 0.000002 | 0.000003 | 0.000003 | 0.000004 | 110.675243 |
| Shot | 889 | 0.000002 | 0.000002 | 0.000003 | 0.000003 | 0.000003 | 0.000003 | 0.000003 |
| Ball Receipt* | 33,397 | 8.137769 | 0.000002 | 0.000003 | 38.075462 | 76.026542 | 106.002379 | 135.570643 |
| Dribble | 773 | 33.116166 | 0.000003 | 73.681702 | 98.766204 | 109.390134 | 123.381464 | 134.349385 |
| Dribbled Past | 446 | 77.165054 | 79.031946 | 94.791334 | 110.663672 | 115.439952 | 125.961741 | 137.004351 |
| Dispossessed | 641 | 70.748363 | 74.372608 | 91.026066 | 107.130788 | 117.732494 | 126.696949 | 135.684070 |
| Foul Won | 630 | 60.759273 | 62.302216 | 79.589663 | 99.595978 | 106.347144 | 122.923405 | 140.871882 |
| Pressure | 10,080 | 0.004784 | 0.000002 | 0.000002 | 0.000003 | 0.000003 | 0.000004 | 48.200934 |

### Direct versus mirrored hypotheses

The diagnostic mirror is `(120-x, 80-y)`. Percentages use measurable pairs only;
exact ties are retained. No event or frame coordinate was changed.

| Event type | Median mirrored | p95 mirrored | Direct closer % | Mirrored closer % | Equal % |
| --- | --- | --- | --- | --- | --- |
| Pass | 63.247135 | 112.256036 | 99.906 | 0.000 | 0.094 |
| Carry | 64.064030 | 109.411699 | 99.732 | 0.268 | 0.000 |
| Shot | 92.740712 | 111.740266 | 100.000 | 0.000 | 0.000 |
| Ball Receipt* | 58.040674 | 107.568472 | 88.445 | 11.555 | 0.000 |
| Dribble | 48.088252 | 111.721595 | 58.085 | 41.915 | 0.000 |
| Dribbled Past | 1.436289 | 3.250010 | 0.000 | 100.000 | 0.000 |
| Dispossessed | 0.983314 | 3.166039 | 2.652 | 97.348 | 0.000 |
| Foul Won | 1.127998 | 3.794437 | 3.175 | 96.825 | 0.000 |
| Pressure | 69.483667 | 110.567047 | 99.990 | 0.010 | 0.000 |

Pass, Carry, Shot and Pressure predominantly favor direct coordinates. The large
direct tails in some types still matter: even Pass reaches 7.592760 units, Carry
110.675243 and Pressure 48.200934. Direct consistency is not a blanket guarantee.

Dribbled Past favors mirroring in every measured pair; Dispossessed and Foul Won
favor it in approximately 97.35% and 96.83%. Their mirrored medians remain about
1.44, 0.98 and 1.13 units respectively, so mirroring is not exact reconciliation.
Ball Receipt* (11.55% mirrored closer) and Dribble (41.91%) exhibit mixed behavior.
Duel is also mixed (44.51% mirrored closer), and 50/50 divides evenly. No whole-type
rotation is justified solely by these percentages.

Across all measurable pairs, 111,733 are direct closer, 6,813 mirrored closer and
31 exact ties; the four unmeasurable multiple-actor frames also carry the
`equal_or_indeterminate` label but are excluded from percentage denominators.
As an additional diagnostic, taking the smaller of the two distances leaves a
95th percentile of 0.711686, 99th percentile of 7.424444 and maximum of 48.855398.
This is evidence that neither coordinate hypothesis explains every discrepancy;
it is not a transformed dataset or an exclusion criterion.

### Multiple actors

Four frames remain in match 3895139:

| Event index | Event type | Event UUID |
| --- | --- | --- |
| 541 | Pass | fdb22e5a-a841-4f0a-871f-5628deffa2c5 |
| 798 | Dispossessed | 3e29e673-5de2-4f22-b0c9-0d298431320b |
| 1978 | Pass | c766113e-d3c8-4c8c-9685-ac26faa2bfd6 |
| 2036 | Ball Receipt* | 61d8965a-fcaa-41c1-b98f-4add7693b817 |

Each has two identical actor locations within its pair. The diagnostic CSV keeps
both positions and the event location. This does not establish whether the records
refer to one player or two; no actor selection, identity inference or deduplication
was performed. These four frames remain excluded from single-actor distance
analysis. Actor-specific analysis requires exclusion until an independently
justified resolution is available; general frame observability counts retain them.
Player-count-sensitive geometry must also account for this unresolved duplication.

### Remaining issues and Phase 2 recommendation

**Ready for a scoped Phase 2 of basic within-frame visible-player geometry.** All
34 matches now have internally compatible IDs, and the coordinate diagnostics
identify where stronger assumptions would be unsafe. This recommendation does not
approve unrestricted direction-dependent event/frame integration or tactical models.

Before combining event and frame geometry, establish event-specific coordinate and
actor/role semantics, especially for opposing/paired events and mixed event types.
The closer distance alone is not sufficient to select an orientation. Residual
mismatches, multiple-actor handling, goalkeeper inclusion, visibility-based selection
and sensitivity remain unresolved. No universal actor-distance threshold or final
visibility threshold has been set; incomplete visibility remains an observation
limit. No Phase 2 metric or attacking-direction normalization was implemented.

### Checks

119 offline tests passed, including revision URL/configuration checks, both distance
hypotheses, classification, invalid locations, event-type aggregation, multiple
actors and no-coordinate-mutation tests. Ruff and the full pinned live CLI passed.
All six derived CSVs were generated; the existing raw-data inventory and null
calibration files remain unchanged. The notebook presents the new diagnostics and
rejects cached tables from an unknown or different source revision.

## Phase 2A implementation and initial diagnostics

Verified on **7 September 2026**, using the immutable StatsBomb revision
`533862946a73608c134d18b78226b6371ce7173c`. The season CLI fetched events and 360
once per match in memory; all 34 match resources loaded. It processed **118,581
original frames**, producing **711,486 frame-variant rows**, exactly six per frame.
The original match-local frame ordinal is retained, with no synthetic frames for
events without 360. The match summary records retrieval timestamps and source URL.

### Implementation and verification

The reusable APIs in `leverkusen.spatial.geometry` are `valid_point`,
`measure_points`, `frame_geometry` and `build_frame_geometry`. Nine numeric
outputs implement the eight locked metric families; centroid has two components.
Every numeric output has its own status; centroid component statuses agree.
The registry implementation section maps all context fields, including separate
raw-list inventory, valid points, invalid entries, unknown flags, keeper removals,
actor status, polygon validity, coincidences and out-of-bounds records.

`leverkusen.spatial.diagnostics` provides the pinned CLI's summaries and paired
keeper deltas; `leverkusen.visualization.geometry` produces the diagnostic plots.
`notebooks/03_spatial_geometry.ipynb` executed **all five code cells**, with three
saved figures covering distributions, goalkeeper sensitivity and exact-n strata.
Calculations reside in the package. The notebook reads compact derived summaries
and verifies source revision; it does not persist raw frames.

**194 offline tests passed; two optional network tests were deselected.**
`python -m ruff check .`, CLI help, notebook schema validation and full-table
checks passed. Tests cover valid/invalid coordinates, exact literal flags,
empty/unavailable inputs, record multiplicity, hand-computable distance aggregates,
nearest-neighbor ties/self exclusion, hull degeneracy and expected failures,
unexpected errors, actor ambiguity, observability context, duplicate joins,
six-row grain, keeper pairing and raw-free outputs.

Full CSV verification confirmed unique original-frame variant keys, six variants
per frame, the current API schema, finite successful values, positive measured
hulls, and exact status/NA correspondence. IDs, raw record counts, actor counts
and visible-area fractions agree exactly with the Phase 1 derived frame table.
The implementation also preserves diagnostic information for invalid scalar event
IDs; none occurred in this pinned run.

Environment: Windows, Python 3.14.0, pandas 3.0.5, NumPy 2.5.2, Shapely 2.1.2,
Matplotlib 3.11.1 and nbclient 0.11.0. The existing dependency configuration was
retained. Raw-data and all configuration SHA-256 inventories were unchanged.

### Metric availability

Denominator is **711,486 variant rows per output**, including all record-quality
flags. The six variants are repeated measurements of original frames, not
independent observations for statistical inference.

| Output(s) | Available per output | NA per output | NA rate |
| --- | ---: | ---: | ---: |
| Visible player count | 711,486 | 0 | 0.000000% |
| Centroid x; centroid y; visible width; visible depth | 711,460 | 26 | 0.003654% |
| Convex hull area | 709,524 | 1,962 | 0.275761% |
| Mean pairwise; median pairwise; mean nearest-neighbor distance | 711,019 | 467 | 0.065637% |

The 26 missing centroid/span measurements per output were `empty_points`.
All missing distances and hulls were `insufficient_points`. There were **zero**
observed `geometry_error`, `numeric_error`, `degenerate_hull` or
`insufficient_unique_points` statuses; their behavior is covered offline.
Count remains zero for known-empty selected subsets. All raw frame lists loaded.

Each subset/keeper variant has 118,581 rows. Count is available for every row;
the remaining NA rates vary by selected point count:

| Subset | Keepers | Centroid/spans NA % | Hull NA % | Each distance NA % |
| --- | --- | ---: | ---: | ---: |
| all_visible | included | 0.000000 | 0.005903 | 0.000843 |
| all_visible | excluded | 0.000843 | 0.016023 | 0.005903 |
| teammate_true | included | 0.000000 | 0.167818 | 0.042165 |
| teammate_true | excluded | 0.002530 | 0.238655 | 0.051442 |
| teammate_false | included | 0.008433 | 0.604650 | 0.146735 |
| teammate_false | excluded | 0.010120 | 0.621516 | 0.146735 |

All-visible included counts range from 1 to 22 (median 17); excluded counts range
from 0 to 21 (median 17). Both literal teammate subsets reach 11 records;
their medians are 8 for teammate_true and 9 for teammate_false under both keeper
policies. These are visible record counts, without inferred player identity.
Exact-n summaries retain denominators and NA rates rather than selecting a cutoff.

### Goalkeeper sensitivity

Differences are **excluded minus included**, paired on original frame and literal
subset. There were no unknown keeper flags in the pinned records. Keeper removal
affected **47,394 all-visible frames**, **23,020 teammate_true subsets** and
**24,374 teammate_false subsets**. Four all-visible frames contained two keeper
records. The tables retain both the all-pairs and records-removed summaries.

The following are mean paired deltas **among affected subsets**, using jointly
defined results for each metric. These are descriptive composition effects, without
a preferred keeper convention or tactical interpretation.

| Output | all_visible | teammate_true | teammate_false |
| --- | ---: | ---: | ---: |
| Visible count (records) | -1.000084 | -1.000130 | -1.000041 |
| Centroid x | 0.114428 | 2.349380 | -1.914999 |
| Centroid y | 0.006411 | -0.045508 | 0.067619 |
| Width | -0.041751 | -0.076058 | -0.043144 |
| Depth | -10.426598 | -9.992064 | -11.780091 |
| Hull area | -219.621707 | -190.248580 | -199.587353 |
| Mean pairwise distance | -0.838901 | -0.835709 | -1.304203 |
| Median pairwise distance | -0.859980 | -0.964069 | -1.319484 |
| Mean nearest-neighbor distance | -0.405916 | -0.028279 | -0.543254 |

Units are native coordinate units, except record counts and squared units for
hull area. Paired denominators differ: centroid/spans use 47,393 / 23,017 / 24,372
affected pairs in column order; hulls use 47,375 / 22,922 / 24,352; distances use
47,387 / 23,006 / 24,372. Count uses all affected subsets. The CSV also records
medians, quantiles, absolute deltas, changed-pair counts and missingness.

### Geometry and data-quality anomalies

| Flag | Original frames with flag | Variant rows with flag |
| --- | ---: | ---: |
| Coincident records | 50 | 198 |
| Multiple actors | 4 | 24 |
| Finite out-of-bounds points | 11,508 | 45,565 |

The all-visible included observations contain **52 coincident excess records**
across those 50 frames and **13,812 out-of-bounds record observations** across
11,508 frames. These are frame-local record observations, not unique people.
The four previously known multiple-actor frames remain unchanged; the generic
actor rule flags every one of their six variants. The other 118,577 frames have
single-actor status; none have unknown actor status.

There were no non-dictionary player entries, invalid locations, unknown teammate
or keeper flags, ambiguous/unmatched event joins, or invalid visible polygons.
Finite out-of-bounds coordinates remain measured in native units and flagged,
without clipping or exclusions. Coincidence is retained without deduplication
or a claim that each coincidence represents the same person.

### Artifacts and validation boundary

Nine ignored derived CSVs were generated under `outputs/diagnostics/`:
`phase2a_frame_geometry.csv`, `phase2a_match_summary.csv`,
`phase2a_inventory.csv`, `phase2a_metric_summary.csv`,
`phase2a_metric_status.csv`, `phase2a_histograms.csv`,
`phase2a_by_valid_points.csv`, `phase2a_goalkeeper_sensitivity.csv` and
`phase2a_anomalies.csv`. Three diagnostic PNGs were exported under
`outputs/figures/`; the notebook also embeds them. No raw StatsBomb JSON or full
freeze frames were saved, and generated diagnostics were not added to Git.

**Formulas remained identical to the method lock.** The eight complete registry
rows were compared with their pre-implementation versions, allowing only the
implementation-status change; numerical rules, actor policy and later candidates
also matched exactly. No coordinate transformation, calibration change, tactical
role mapping, final eligibility filter, sequence or later metric was introduced.

**Ready for empirical geometry validation.** Initial descriptive execution is
complete; representative-frame review and visibility/edge calibration remain
future work. Out-of-bounds placement, incomplete visibility and record identity
still require interpretation. The locked later primary-comparison exclusion for
multiple/unknown actors remains in force when those comparisons are undertaken;
it was not applied to this all-row diagnostic inventory. Direction-dependent
semantics and every later tactical/outcome method remain unresolved and deferred.
No unresolved implementation conflict with the Phase 2A lock was identified.

## Phase 2B-1 — observation sensitivity diagnostics

Completed **7 September 2026** as bounded descriptive sensitivity analysis of the
existing Phase 2A table: **118,581 original frames, 711,486 variants, 34 matches**.
No raw resource was fetched and no geometry was recomputed. The input SHA-256 was
`a6af9ceb6182c02159de78c8e57ad5ecda635d47e282eec610baf9daa45d5216`;
the upstream revision remains
`533862946a73608c134d18b78226b6371ce7173c`.

Six existing metrics are summarized: width, depth, hull area, mean pairwise
distance, median pairwise distance and mean nearest-neighbor distance. Every
literal subset and keeper policy is reported separately. All recorded quality
flags remain in the diagnostic population. No primary analytical sample is selected.

### Summary conventions and reproducibility

Run `python scripts/observation_sensitivity.py` from the repository root.
Reusable summaries are in `leverkusen.spatial.observation_sensitivity`; the
three requested figures are in `leverkusen.visualization.observation_sensitivity`.
The clearly labeled Phase 2B-1 notebook section loads their compact derived tables.

For exact-n and coverage summaries, `frame_count` is the group inventory,
`denominator` counts defined values used for that metric, and `na_count` is the
difference. Undefined hull groups retain denominator-only rows with NA statistics.
Standard deviation uses ddof=1; p05/p25/p75/p95 use pandas linear interpolation.
All exact-n strata are retained. The joint coverage/count table uses the same
statistic columns to describe n, with its own observed-count denominator.

Visible-area quintiles are computed once from original frames, with equal weight
per frame and shared boundaries across all six variants. Bins are right closed;
the first includes the minimum. Tied values remain together, duplicate edges
collapse, and missing coverage has a separate unavailable category if present.
There was no missing coverage in this input. These grouping boundaries are solely
descriptive and are not proposed eligibility thresholds.

| Coverage bin | Lower fraction | Upper fraction | Original frames / rows in each variant |
| --- | ---: | ---: | ---: |
| B1 | 0.045220068008 | 0.216822584412 | 23,718 |
| B2 | 0.216822584412 | 0.265017325037 | 23,715 |
| B3 | 0.265017325037 | 0.318401586888 | 23,717 |
| B4 | 0.318401586888 | 0.383158787876 | 23,716 |
| B5 | 0.383158787876 | 0.861461387123 | 23,715 |

Bounds above are rounded for display; the CSV retains numeric precision.
Each bin's metric denominator can be smaller when that metric is undefined.

### A. Dependence on selected valid-player count

To give a compact quantitative comparison, the table below uses exact-n strata
at each variant's observed 25th- and 75th-percentile player counts. This reporting
comparison does not remove other n values or establish a reliable range. The
546-row exact-n table contains every observed stratum and all requested statistics.

Values are **median at lower n → median at higher n**. All six metrics are defined
for every frame in these particular endpoint strata. Units are native StatsBomb
coordinate units, with squared units for hull area. Mean PD and median PD denote
the existing pairwise summaries; mean NN is the existing nearest-neighbor summary.

| Subset / keepers | n comparison; frame counts | Width | Depth | Hull | Mean PD | Median PD | Mean NN |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all_visible / included | 14 → 19; 8,493 → 15,263 | 45.62 → 50.28 | 31.60 → 33.91 | 893.32 → 1,150.46 | 21.14 → 21.78 | 19.92 → 20.65 | 6.67 → 6.07 |
| all_visible / excluded | 14 → 19; 8,911 → 14,654 | 45.19 → 50.79 | 28.69 → 31.53 | 820.46 → 1,107.74 | 20.62 → 21.74 | 19.42 → 20.63 | 6.32 → 5.99 |
| teammate_true / included | 7 → 10; 17,795 → 25,571 | 43.30 → 48.57 | 25.66 → 30.80 | 615.45 → 973.99 | 23.56 → 24.46 | 21.90 → 23.23 | 11.79 → 10.69 |
| teammate_true / excluded | 7 → 9; 18,304 → 28,730 | 42.87 → 46.29 | 24.55 → 29.02 | 590.75 → 848.68 | 23.10 → 23.81 | 21.48 → 22.45 | 11.52 → 10.93 |
| teammate_false / included | 7 → 10; 14,664 → 30,268 | 36.76 → 39.98 | 24.38 → 27.35 | 481.62 → 678.71 | 20.40 → 20.56 | 19.07 → 19.53 | 10.41 → 9.18 |
| teammate_false / excluded | 7 → 10; 15,721 → 33,770 | 36.41 → 39.93 | 23.64 → 25.42 | 465.03 → 638.80 | 20.14 → 20.19 | 18.80 → 19.17 | 10.23 → 8.95 |

Across these comparisons, median hull area rises **28.78–58.26%**, width rises
**7.98–12.41%**, and depth rises **7.30–20.03%**. Median mean pairwise distance
changes **+0.23–5.46%** and median median-pairwise distance **+1.99–6.24%**;
median mean NN falls **5.09–12.48%**. These are differences between observed
strata, without an independent player-count effect estimate. Figure A also shows
departures from simple monotonic patterns at some endpoints; their denominators
remain available without a cutoff or detailed frame investigation.

### B. Dependence on visible-area fraction

Across B1 and B5, all six summarized metric medians increase under every variant.
The following table gives endpoint medians; the full 180-row coverage table also
includes B2–B4, means, standard deviations, quantiles and metric denominators.

| Subset / keepers | Width B1 → B5 | Depth B1 → B5 | Hull B1 → B5 | Mean PD B1 → B5 | Median PD B1 → B5 | Mean NN B1 → B5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| all_visible / included | 39.22 → 55.46 | 27.63 → 37.96 | 650.77 → 1,393.44 | 17.91 → 24.44 | 16.95 → 23.13 | 5.21 → 6.88 |
| all_visible / excluded | 39.22 → 55.46 | 25.01 → 34.08 | 593.66 → 1,278.34 | 17.72 → 24.01 | 16.76 → 22.69 | 5.09 → 6.67 |
| teammate_true / included | 35.22 → 52.60 | 22.69 → 32.89 | 436.28 → 1,088.55 | 19.47 → 27.12 | 18.30 → 25.44 | 9.30 → 12.49 |
| teammate_true / excluded | 35.17 → 52.60 | 21.60 → 31.36 | 417.18 → 1,039.90 | 19.42 → 26.86 | 18.25 → 25.17 | 9.32 → 12.41 |
| teammate_false / included | 31.10 → 42.12 | 21.57 → 29.07 | 369.88 → 762.36 | 17.56 → 22.52 | 16.55 → 21.34 | 8.52 → 10.48 |
| teammate_false / excluded | 31.06 → 42.12 | 20.00 → 27.27 | 342.82 → 705.65 | 17.49 → 22.09 | 16.43 → 20.96 | 8.51 → 10.33 |

Across variants, median hull area is **105.84–149.51% higher** in B5 than B1;
width is **35.45–49.56% higher**, depth **34.82–45.20%**, mean PD **26.30–39.31%**,
median PD **27.56–39.03%**, and mean NN **21.41–34.31%**.

Player counts also differ across those bins:

| Subset / keepers | Mean n B1 → B5 | Median n B1 → B5 | n p25–p75 in B1 | n p25–p75 in B5 |
| --- | ---: | ---: | --- | --- |
| all_visible / included | 15.1466 → 18.0452 | 15 → 19 | 13–17 | 17–20 |
| all_visible / excluded | 14.6491 → 17.7034 | 15 → 19 | 13–17 | 16–20 |
| teammate_true / included | 7.5436 → 9.0562 | 8 → 9 | 6–9 | 8–10 |
| teammate_true / excluded | 7.3096 → 8.8748 | 7 → 9 | 6–9 | 8–10 |
| teammate_false / included | 7.6030 → 8.9890 | 8 → 10 | 6–9 | 8–10 |
| teammate_false / excluded | 7.3395 → 8.8285 | 8 → 10 | 6–9 | 8–10 |

All selected counts are defined in this run: each row above describes 23,718 B1
frames and 23,715 B5 frames. The complete joint table has 30 rows, covering all
five bins and six variants. Coverage and n co-vary; their separate marginal
summaries do not isolate either relationship from composition or event context.

### C. Paired goalkeeper sensitivity

Each subset has 118,581 total original frames. Actual keeper removal occurs in
47,394 all_visible, 23,020 teammate_true and 24,374 teammate_false observations.
Unknown keeper omissions are separately counted and are zero here.

Deltas are excluded minus included, joined on match, original frame ordinal and
literal subset. Only jointly defined values enter comparisons. The 36-row table
reports both all_frames and keeper_removed scopes, total and scope inventories,
actual removals, jointly defined pairs, NA pairs, mean/median/mean absolute delta,
sample standard deviation, p05/p25/p75/p95, min/max and exact numerical change.
The proportion with numerical change uses jointly defined pairs as its denominator.

Among actual-removal observations, the following mean deltas and proportions apply:

| Subset | Metric | Jointly defined pairs | Mean delta | Mean absolute delta | Numerically changed |
| --- | --- | ---: | ---: | ---: | ---: |
| all_visible | Width | 47,393 | -0.04175 | 0.04175 | 1.17% |
| all_visible | Depth | 47,393 | -10.42660 | 10.42660 | 95.14% |
| all_visible | Hull | 47,375 | -219.62171 | 219.62171 | 98.85% |
| all_visible | Mean PD | 47,387 | -0.83890 | 0.90496 | 100.00% |
| all_visible | Median PD | 47,387 | -0.85998 | 0.96452 | 96.47% |
| all_visible | Mean NN | 47,387 | -0.40592 | 0.51093 | 100.00% |
| teammate_true | Width | 23,017 | -0.07606 | 0.07606 | 2.15% |
| teammate_true | Depth | 23,017 | -9.99206 | 9.99206 | 95.62% |
| teammate_true | Hull | 22,922 | -190.24858 | 190.24858 | 98.58% |
| teammate_true | Mean PD | 23,006 | -0.83571 | 1.34041 | 100.00% |
| teammate_true | Median PD | 23,006 | -0.96407 | 1.51750 | 91.09% |
| teammate_true | Mean NN | 23,006 | -0.02828 | 0.85573 | 100.00% |
| teammate_false | Width | 24,372 | -0.04314 | 0.04314 | 1.49% |
| teammate_false | Depth | 24,372 | -11.78009 | 11.78009 | 98.50% |
| teammate_false | Hull | 24,352 | -199.58735 | 199.58735 | 99.71% |
| teammate_false | Mean PD | 24,372 | -1.30420 | 1.40417 | 100.00% |
| teammate_false | Median PD | 24,372 | -1.31948 | 1.48392 | 94.34% |
| teammate_false | Mean NN | 24,372 | -0.54325 | 0.67989 | 100.00% |

All-frame median deltas are zero for every metric/subset because most observations
have no keeper removed. For all_visible, all-frame mean depth and hull deltas
are -4.16721 and -87.75643, using 118,580 and 118,562 jointly defined pairs.
Figure C displays median, IQR and p05–p95 for both scopes; these intervals describe
observed deltas and are not confidence intervals.

The teammate_true mean NN has an affected mean delta of -0.02828, median -0.25159,
mean absolute delta 0.85573 and p05–p95 of -1.46624 to 2.23752. Its small signed mean
coexists with variation in both directions. No keeper convention is selected.

### Artifacts, checks and remaining decisions

Seven compact CSVs were written under `outputs/diagnostics/`:
`phase2b1_metric_by_valid_point_count.csv` (546 rows),
`phase2b1_metric_by_visible_area.csv` (180),
`phase2b1_visibility_vs_player_count.csv` (30),
`phase2b1_goalkeeper_sensitivity.csv` (36),
`phase2b1_visible_area_bins.csv` (5),
`phase2b1_player_count_context.csv` (6), and
`phase2b1_run_summary.csv` (1). The last records input hash, upstream revision,
population and generation time.

Exactly three new PNGs were exported under `outputs/figures/`:
`phase2b1_metric_vs_player_count.png`, `phase2b1_metric_vs_visible_area.png`
and `phase2b1_goalkeeper_sensitivity.png`. They are also embedded in the notebook.
Generated CSVs and PNGs remain ignored by Git.

**203 offline tests passed**, including nine focused new sensitivity tests; two
optional network tests were deselected. Ruff passed. All four new notebook code
cells executed using the existing setup, preserving the earlier Phase 2A cells.
Tests cover exact-n grouping and quantiles, original-frame quantile weighting,
ties/missing coverage, same-frame pairing across matches, undefined-pair exclusion,
exact denominators, unchanged inputs and retention without threshold filtering.
The source geometry CSV, Phase 2A geometry implementation, metric registry and all
configuration files remained unchanged.

**Evidence is ready for human review before calibration.** Observed player count
and coverage are associated with geometry in different ways; their separate
summaries do not estimate independent effects. Keeper deltas vary materially by
metric and subset. Endpoint irregularities and mixed-sign spacing deltas remain
descriptive patterns without a resolution.

No thresholds, eligibility rules, keeper preference, geometry formulas or metric
provenance changed. No tactical interpretation or later metric was introduced.
Detailed out-of-bounds, polygon-boundary/edge, coincidence, representative-frame
and orientation investigations remain explicitly deferred.

## Phase 2B-2 — Observation quality and edge validation

Executed on **8 September 2026** using revision
`533862946a73608c134d18b78226b6371ce7173c`. Raw 360 was loaded through the unchanged
loader, match by match in memory, and joined to existing Phase 2A geometry by
match and original frame ordinal. Event IDs, selected counts and coverage agreed.
The geometry CSV SHA-256 remains
`a6af9ceb6182c02159de78c8e57ad5ecda635d47e282eec610baf9daa45d5216`, identical to
the Phase 2B-1 input. CSV numeric reads use round-trip precision so parser rounding
does not masquerade as an exact multiplicity effect. No geometry formula changed.

The run reconfirmed **118,581 frames, 711,486 variants, exactly six per frame,
34 matches, 11,508 out-of-bounds frames, 50 coincident-record frames and four
multiple-actor frames**. Unknown keeper flags and geometry/numeric implementation
error rows remain zero. The Phase 2B-1 count, coverage and keeper findings stand;
this phase adds boundary/quality evidence rather than repeating those analyses.

### A. Out-of-bounds coordinates

**EMPIRICAL FINDING:** There are **13,812 finite out-of-bounds player records**
in 11,508 frames (9.7048% of original frames), spread across all 34 matches.
The distribution is mixed, ranging from tiny excursions to deviations of several
native units. It cannot be described as only floating-point boundary noise.

| Distance to nominal pitch rectangle | Native units |
| --- | ---: |
| Minimum | 0.00009865 |
| p05 | 0.102619 |
| p25 | 0.557954 |
| Median | 1.380061 |
| p75 | 2.644052 |
| p90 | 4.093298 |
| p95 | 5.048831 |
| p99 | 6.782837 |
| Maximum | 10.662860 |

The five empirical severity bins retain equal values; their exact bounds are in
`phase2b2_excursion_quantile_bins.csv`. They are descriptive groups, not tolerances.
Axis maxima are 6.775173 for x and 10.662860 for y. Of the records, 13,806 violate
one side and six violate two sides. Side counts therefore sum to 13,818:

| Side violated | Records |
| --- | ---: |
| x < 0 | 776 |
| x > 120 | 979 |
| y < 0 | 6,096 |
| y > 80 | 5,967 |

Literal teammate=True/False counts are 9,934/3,878; keeper=True/False counts are
1,350/12,462; actor=True/False counts are 16/13,796. Pass, Ball Receipt*, Carry and
Pressure account for 3,829, 3,785, 3,306 and 1,721 records respectively. These are
event-population counts, not event-specific risk estimates; the event table also
provides original-frame denominators. Match totals range from 205 records in
3895134 to 722 in 3895210. The by-match and by-event tables retain the complete
distributions, including event types with zero affected records. No cause is inferred.

### B–C. Polygon bounds and player/polygon consistency

**EMPIRICAL FINDING:** All **118,581 supplied polygons are valid and fully
contained in the nominal pitch**. None extends outside it; every measured outside
area and outside-area fraction is exactly zero. **118,185 polygons (99.6661%)**
intersect the nominal pitch boundary; 396 do not. On-pitch polygon area ranges
from 434.112653 to 8,270.029316 squared native units. Coverage remains the original
pitch-intersection area / 9,600, with range 0.045220–0.861461 and median 0.290810.

**Every one of the 13,812 out-of-bounds player records is outside its supplied
visible polygon**: zero strictly inside, zero on the boundary and zero covered.
Thus larger provider polygons do not explain these nominal-pitch excursions.
All five excursion quantiles have 100% outside status, so there is no status-group
contrast to estimate. Distance to the visible boundary has median 1.385617,
p95 5.101008, p99 7.022613 and maximum **74.146048**. That long maximum shows that
some inconsistencies extend far beyond a small nominal-pitch excursion.

There are **20,582 frames (17.3569%)** with at least one selected point outside
the polygon under all_visible/included. Because every out-of-bounds frame is in
that set, 9,074 additional frames have polygon-inconsistent points despite having
no nominal-pitch violation. This is an exact geometric inconsistency with the
supplied observation window, not proof of its origin or a rule to remove records.

### D. Defining players and visible-boundary proximity

**EMPIRICAL FINDING:** For all_visible/included, all 118,581 edge observations
are defined. The following distances retain exact extreme ties; scalar values
use the smallest boundary distance among tied defining records.

| Defining point / measure | p05 | p25 | Median | Exact zero frames |
| --- | ---: | ---: | ---: | ---: |
| Minimum x | 0.391126 | 2.098020 | 4.419601 | 3 |
| Maximum x | 0.266168 | 1.500653 | 3.518131 | 266 |
| Minimum y | 0.295280 | 2.562087 | 5.572777 | 116 |
| Maximum y | 0.289216 | 2.594434 | 5.750905 | 377 |
| Minimum across selected players | 0.061858 | 0.389378 | 1.016352 | 509 |
| Median across selected players | 5.786921 | 8.523550 | 10.496467 | 0 |

Thus the lowest five percent of each defining-extreme distribution reach roughly
0.27–0.39 native units, while half of frames have some selected player within the
empirical median minimum distance of 1.016352. These quantify proximity without
choosing what should count as “close.” The 36-row edge table gives every variant's
denominator and distribution. Empty selections remain NA: edge denominators range
from 118,569 to 118,581. The tie table has 597 tied-extreme record entries across
107 original frames; one record can enter more than one extreme or variant.

For all_visible/included, endpoint metric medians behave as follows:

| Metric / associated edge measure | Nearest-distance quintile median | Farthest-distance quintile median |
| --- | ---: | ---: |
| Width / minimum-y edge distance | 51.0345 | 44.5636 |
| Width / maximum-y edge distance | 51.0147 | 44.6490 |
| Depth / minimum-x edge distance | 34.5667 | 31.6433 |
| Depth / maximum-x edge distance | 34.5045 | 30.8122 |
| Hull area / minimum selected edge distance | 1,065.9254 | 923.6264 |

Every one of these endpoint comparisons is lower in the farthest-distance
quintile across all six variants. Interior quintiles need not be monotonic.
For the hull comparison, median minimum distance is 0.135427 versus 3.456104;
median n is 17 in both groups, while median coverage is 0.265977 versus 0.321168.
Equal median n does not constitute adjustment for the count distribution.

These associations are compatible with observation-sensitive extent, but cannot
establish which unseen players exist or how large the full-team geometry is.
The supplied polygon boundary often includes the actual pitch boundary; proximity
to that boundary is not automatically proximity to an interior camera limit.
Distances are unsigned, and outside-polygon points remain included. No observation
is labeled censored and no cutoff is selected.

### E. Extreme-value sanity review

**EMPIRICAL FINDING:** Extreme geometry does concentrate in some observation-
sensitive contexts, with different patterns by metric. All-visible/included
upper one-percent tails have these characteristics (ties retained):

| Metric | Tail frames | Median n | Median coverage | OOB frames | Outside-polygon frames | Keeper present |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Width | 1,186 | 19 | 0.4100 | 29.93% | 41.91% | 42.24% |
| Depth | 1,186 | 20 | 0.4865 | 9.36% | 31.53% | 98.65% |
| Hull area | 1,186 | 20 | 0.4631 | 16.53% | 36.59% | 89.88% |
| Mean pairwise distance | 1,186 | 17 | 0.4143 | 19.31% | 37.44% | 77.32% |
| Mean nearest-neighbor distance | 1,187 | 10 | 0.3204 | 10.03% | 21.23% | 88.71% |

The all-frame baseline is median n=17, coverage=0.2908, OOB=9.70%,
outside-polygon=17.36% and keeper presence=39.97% (defined-metric denominators
vary slightly and are provided in the table). Upper width/hull/mean-pairwise tails
have median minimum edge distances 0.8041/0.7494/0.6315, versus about 1.0163 overall.
Upper nearest-neighbor spacing instead has median n=10 and minimum edge distance
1.0320; it does not show the same edge pattern. A single observation-quality
explanation would be inadequate.

Lower width/depth/hull tails have median n=12/11/11 and coverage
0.1757/0.1656/0.1555. Their median minimum edge distances are 1.7263/2.2767/2.0638,
farther from the polygon boundary than the baseline. Sparse or narrow observed
windows can yield small geometry even when defining players are not near an edge.
Low mean-pairwise and nearest-neighbor tails have median n=16/18 and coverage
0.1567/0.1668, reflecting a different observed composition.

Coincident records remain rare overall (50/118,581 = 0.0422%). Four coincident
frames occur in the upper depth tail and two in the upper hull tail; none of the
four multiple-actor frames enters any all-visible/included one-percent tail of
these five metrics. The 90-row tail table and 60 exact-extreme observations retain
all variants and mathematical low-count extremes. No hard plausibility or anomaly
classification is imposed on the population.

### F. Coincidence, multiple actors and representative visual review

**EMPIRICAL FINDING:** The 50 coincident frames contain **52 exact-coordinate
groups, all of size two: 104 participating records and 52 excess records**.
They occur in five matches: 3895060 (4 frames), 3895139 (42), 3895275 (2),
3895286 (1) and 3895292 (1). Two frames contain two coincidence groups.
Grouped record flags are teammate=True/False 60/44, keeper=True/False 2/102,
and actor=True/False 8/96, with no unknown flags. Event counts and flags are in
the group and summary tables. Identical coordinates do not establish player identity.

There are **206 variant/location perturbations**, each adding one record at an
already-coincident selected location and retaining all original records. In all
206, width, depth and hull area are exactly unchanged; no metric status changes.
Count increases by one. Both centroid components, mean pairwise and mean nearest-
neighbor distance change in all 206, while median pairwise distance changes in
165. Across variants, maximum absolute perturbations are centroid x=2.052918,
centroid y=3.235926, mean pairwise=3.638268, median pairwise=3.441697 and mean
nearest-neighbor=2.262228 native units. These are diagnostic local sensitivities,
not estimated errors in the retained observations. Their low prevalence limits
population exposure but does not make individual spacing/count effects negligible.

All four multiple-actor frames are in match **3895139**, at zero-based frame
indices **472, 693, 1689 and 1733** (Pass, Dispossessed, Pass, Ball Receipt*).
Each has two actor=True records with exactly the same coordinates, both
teammate=True and keeper=False. Actor pair distance is exactly zero. All-visible
counts are 8, 15, 19 and 17. Actor flags alone do not enter the Phase 2A formulas;
retaining both records preserves their count and distance weights. Adding another
coincident actor-location record in the diagnostic comparison changes all-visible
mean NN by -0.992914, -0.347876, -0.353331 and -0.321829 respectively, while all
spans and hulls remain unchanged. The Phase 1 actor-ambiguity policy is preserved.

**28 unique frames were visually reviewed on seven four-panel contact sheets**,
selected by 32 documented rules. They cover all four pitch sides, multiple matches
and event types, low/typical/high coverage, low/high counts, the five major metrics,
keeper sensitivity, all four multiple actors and three other coincident examples.
The CSV retains full UUIDs, source ordinal, selected variant, counts, coverage,
quality flags, edge distances and selection values. Key visual observations:

| Match / frame | Selection and observed geometry |
| --- | --- |
| 3895060 / 124 | Largest hull (4,304.40); several points extend far beyond the supplied polygon, including a distant keeper. Keeper removal changes depth by 54.65 and hull by 1,679.01. Polygon inconsistency is visible despite n=19. |
| 3895060 / 1381 | n=22 does not ensure polygon consistency: the point cloud extends far beyond a relatively narrow visible polygon (coverage 0.2504). |
| 3895244 / 2747 | Maximum depth 110.97 includes a distant actor outside the supplied polygon, although every point is inside the nominal pitch. |
| 3895244 / 1609 | Width 81.29 exceeds nominal pitch width because an out-of-bounds defining point remains measured. |
| 3895232 / 1520 | The smallest positive excursion is visually almost on the pitch boundary; the same frame also contains a more visible excursion. No display jitter is used. |
| 3895250 / 1969; 3895309 / 2436 | Largest x and y excursions visibly cross the nominal boundary; records remain plotted at their supplied coordinates. |
| 3895167 / 645 | One visible record gives zero spans and unavailable hull/pairwise/NN geometry. |
| 3895180 / 3837; 3895244 / 501 | Tiny width/depth among defined hulls comes from nearly aligned three-record selections. |
| 3895348 / 2256 | Hull area 0.0923 is a nearly collinear three-point selection with substantial y-span, not a numeric implementation failure. |
| 3895340 / 1380–1381 | Low pairwise spacing and the minimum-coverage example show a small observed cluster; coverage alone does not identify a full-team shape. |
| 3895194 / 1600; 3895258 / 1850 | Low NN shows a dense observed cluster (n=16); high NN in the selected literal subset uses just three points. |
| 3895074 / 3720 | Maximum keeper centroid-x change (15.69) compares two versus one selected records; this is a sparse-denominator sensitivity. |
| 3895167 / 2998; 3895194 / 3257 | Typical/high coverage show broader internally plausible point arrangements; they remain partial observations, not verified full-team measurements. |
| 3895139 / 472, 693, 1689, 1733 | Coincident actor markers are explicitly labeled x2. Their geometry remains evaluable; actor identity remains unresolved. |
| 3895060 / 205, 1222, 1223 | Other coincidence examples show x2 locations within otherwise ordinary observed point clouds. Adjacent Ball Recovery/Carry frames repeat the pattern; this is not independent identity evidence. |

These panels distinguish mathematically evaluable geometry from visible observation
sensitivity and concrete point/polygon inconsistencies. They do not certify true
football positions, infer identities or establish the cause of any inconsistency.

### G. Artifacts, checks and readiness for calibration

Eighteen compact CSVs were generated under `outputs/diagnostics/`: the requested
out-of-bounds summaries/by-match/by-event, polygon-bounds summary, edge summary,
metric-edge relationships, coincident summary, multiple-actor review,
representative frames and extreme review; plus excursion bins, coincident groups,
multiplicity impacts and sensitivity, tied-extreme distances, extreme-tail summary,
match inventory and run summary. No raw point lists, freeze frames or JSON were
persisted. Ten PNGs comprise three population figures and seven contact sheets.
The representative frames were retrieved again in memory only for a layout review;
the final CLI reproduces the layout in its normal single retrieval pass.

`notebooks/03_spatial_geometry.ipynb` adds the eight-part Phase 2B-2 narrative,
supporting tables and embedded figures. Reusable transformations remain outside
the notebook. The focused offline tests cover excursions/corner distances,
polygon containment/intersection, point status and boundary distance, all extreme
ties, coincidence/multiplicity, deterministic selection, invalid polygons,
unchanged inputs, no clipping/filtering, source-key mismatch and derived-only
runner persistence. **228 offline tests passed** (25 new focused tests; two
optional network tests deselected). `python -m ruff check .` passed. All eight
new notebook code cells executed successfully, figures were embedded, and notebook
schema validation passed. Earlier notebook cells were preserved. Locked code,
metric registry, source foundation and all configuration files remain unchanged.

**EMPIRICAL FINDING — readiness:** The evidence is sufficient to **begin human-
reviewed Phase 2B-3 visibility/eligibility calibration**. It is not sufficient to
automatically finalize a sample. In particular, polygon validity and even n=22
do not ensure point/polygon agreement; out-of-bounds magnitude is heterogeneous;
boundary proximity combines actual pitch boundaries with observation-window
boundaries; and count, coverage, event context and goalkeeper composition co-vary.
Missing full-team positions remain unobserved, and actor/coordinate semantics
remain unresolved for actor-specific or direction-dependent work.

**METHODOLOGICAL DECISION:** None selected. No visibility, count or edge threshold,
eligibility rule, goalkeeper convention, source revision, geometry formula or
metric provenance changed. No coordinates were clipped, mirrored, repaired or
deduplicated. Defensive regimes, orientation normalization, Voronoi, zones,
sequences, clustering, modeling and causal interpretation remain out of scope.

## Phase 2B-3 — Human-reviewable calibration candidates

**Historical pre-approval evaluation.** The final human-approval section below
records which rules were adopted. Proposed language and saved candidate outputs
in this section are evidence of that earlier stage, not the current lock status.

**PROPOSED — REQUIRES HUMAN APPROVAL.** Evaluated on 9 September 2026 using
the existing **118,581 original frames / 711,486 variants / 34 matches**.
The geometry SHA-256 remains
`a6af9ceb6182c02159de78c8e57ad5ecda635d47e282eec610baf9daa45d5216` and revision
`533862946a73608c134d18b78226b6371ce7173c` is unchanged. This was an offline
evaluation, without new raw retrieval, geometry recomputation or permanent
eligibility changes. All earlier Phase 2B findings above remain empirical
associations, not causal explanations.

The reproducible entry point is `python scripts/calibration.py`; candidate
definitions and summary code live in `leverkusen.spatial.calibration`. The main
human-review artifact is the eight-row
[metric calibration matrix](../docs/phase2b3_metric_calibration_matrix.csv), also
generated at `outputs/diagnostics/phase2b3_metric_calibration_matrix.csv`.
[Methods section 36](../docs/methods_specification.md#36-phase-2b-3-eligibility-and-goalkeeper-calibration-candidates)
states exact proposed rules, their rationale and the approval boundary.

### Candidate grid, denominators and support

Twenty named candidates cover A (all mathematically defined), four B count
landmarks, four C coverage landmarks, D primary/sensitivity, two E combined
filters, five OOB primary/sensitivity variants, coincidence sensitivity and
unique-actor eligibility. Explicit no-op primary OOB rows show that retaining
coordinates is distinct from rerunning a restricted robustness population.
OOB/coincidence predicates refer to the **entire original frame**, propagated from
all_visible/included, even when a literal subset has no affected selected point.
There is no containment or polygon-edge exclusion.

Each candidate has 54 metric/variant summaries (nine numeric outputs, including
both centroid components, times six variants): **1,080 retention rows and 1,080
distribution rows**. Retention percentages use the original 118,581-frame
inventory; separate columns use the metric's mathematical denominator and count
only additional filter removals. Match summaries include zero-retained matches;
minimum/median counts are over all 34 matches. Event composition preserves all
24 observed event types, including rare categories and zero-retained categories.
Distribution references are all-defined A values for that metric/variant, not a
complete-case population selected by another metric. Paired-primary columns also
compare each sensitivity with its explicitly named primary. Mean, median, sample
standard deviation (ddof=1), p05/p25/p75/p95, absolute differences and relative
differences are retained. Relative differences divide by the absolute baseline
statistic; zero/undefined denominators remain NA.

Count landmarks are q05/q25/q50/q75 from each variant's observed distribution,
using `higher` interpolation to return actual integer n values. Exact-n support
at these landmarks is **2,985–33,770 frames** across the six variants. Coverage
landmarks are the four previous quintile boundaries, weighted once per original
frame. Both rules use `>=`, preserving ties; C retains 94,865 / 71,149 / 47,433 /
23,717 original frames before metric availability. They differ slightly from
complements of the earlier right-closed bins because boundary ties are included.
No 30%, 40% or 50% coverage default was introduced.

The joint `phase2b3_count_coverage_support.csv` shows n-by-coverage-quintile
inventories, match support and defined counts/medians for all nine outputs. It
supports review of common observational support without treating equal medians
or marginal summaries as independent adjustment. Sparse/empty strata do not
become certified comparisons merely because their inputs are mathematically valid.

### Retention and distribution consequences

The following comparison uses **all_visible / excluded hull area**. All candidates
retain some frames in every match; the range of match retention is still material.

| Candidate | Eligible frames | % of inventory | Minimum per match | Median per match | Hull median change vs A |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 118,562 | 99.984 | 2,847 | 3,443 | 0.00% |
| B q05: n>=10 | 114,011 | 96.146 | 2,718 | 3,333 | +1.90% |
| B q25: n>=14 | 93,745 | 79.056 | 2,003 | 2,804.5 | +7.09% |
| B q50: n>=17 | 62,278 | 52.519 | 924 | 1,907 | +14.46% |
| B q75: n>=19 | 31,202 | 26.313 | 214 | 919.5 | +26.39% |
| C q20 | 94,851 | 79.988 | 1,841 | 2,848.5 | +8.60% |
| C q40 | 71,142 | 59.994 | 1,061 | 2,151 | +16.09% |
| C q60 | 47,429 | 39.997 | 548 | 1,350.5 | +25.04% |
| C q80 | 23,717 | 20.001 | 138 | 676.5 | +36.91% |
| D primary | 118,558 | 99.981 | 2,847 | 3,443 | +0.001% |
| D sensitivity: n>=14, no frame OOB | 84,150 | 70.964 | 1,860 | 2,495.5 | +5.81% |
| E q25/q20 | 71,019 | 59.891 | 1,149 | 2,079.5 | +12.42% |
| E q50/q40 | 41,232 | 34.771 | 407 | 1,175 | +23.90% |
| OOB-B sensitivity | 107,054 | 90.279 | 2,650 | 3,156.5 | -1.60% |

Across all six variants, E q25/q20 retains **59.72–64.43%** and E q50/q40
**32.78–43.37%** for each of the six geometry metrics. Their retained populations
are alike within a variant because these count cutoffs exceed the mathematical
minima in this sample, not because the method enforces a common complete case.

The primary/sensitivity trade-off for the three **excluded** populations is:

| Metric | all_visible primary / sensitivity | teammate_true primary / sensitivity | teammate_false primary / sensitivity |
| --- | ---: | ---: | ---: |
| Count | 118,577 / 118,531 | 118,577 / 118,531 | 118,577 / 118,531 |
| Centroid (each axis) | 118,576 / 118,530 | 118,574 / 118,528 | 118,565 / 118,519 |
| Width | 118,576 / 107,069 | 118,574 / 107,067 | 118,565 / 107,058 |
| Depth | 118,576 / 118,576 | 118,574 / 118,574 | 118,565 / 118,565 |
| Hull | 118,558 / 84,150 | 118,294 / 87,167 | 117,840 / 84,325 |
| Mean pairwise | 118,570 / 107,020 | 118,516 / 106,967 | 118,403 / 106,855 |
| Median pairwise | 118,570 / 118,524 | 118,516 / 118,470 | 118,403 / 118,357 |
| Mean nearest-neighbor | 118,570 / 113,963 | 118,516 / 114,730 | 118,403 / 116,003 |

Depth's D sensitivity mask is identical because its prioritized robustness check
is the keeper convention. The separate OOB-B and B/C rows remain available. Count
is defined for known empty sets; the other mathematical denominators differ.
The proposed outfield hull sensitivity retains **70.96–73.51%**, whereas the
outfield NN sensitivity retains **96.11–97.83%**. Neither establishes completeness.

| all_visible / excluded metric | A median | D sensitivity median | E q25/q20 median | C q80 median |
| --- | ---: | ---: | ---: | ---: |
| Width | 47.5236 | 47.0688 | 50.1095 | 55.4623 |
| Depth | 29.8332 | 29.8332 | 31.4002 | 34.0768 |
| Hull | 933.6984 | 987.9524 | 1,049.6490 | 1,278.2893 |
| Mean pairwise | 21.1891 | 21.0436 | 21.7817 | 24.0079 |
| Median pairwise | 20.0302 | 20.0305 | 20.6197 | 22.6858 |
| Mean nearest-neighbor | 6.1393 | 6.1052 | 6.1429 | 6.6656 |

For example E q25/q20 barely moves the NN median (+0.059%) while removing 40.1%
of frames. This is not evidence that filtering is harmless: count and coverage
restrictions can move the marginal distribution in opposite directions.

### Stability findings and limits

Successive changes are reported in `phase2b3_threshold_stability.csv`, starting
at A and stepping through each B/C/E family. No percentage is used to classify
"stable". These are changes in nested observed populations, not repeated
measurements of a known true geometry or independent-effect estimates.

For all_visible/excluded hull, successive median changes under B are
**+1.90%, +5.09%, +6.89%, +10.42%**. Under C they are **+8.60%, +6.90%, +7.71%,
+9.49%**. Increasing restriction does not yield a diminishing-change plateau.
For NN, the B sequence is **-0.56%, -1.60%, -0.51%, +1.47%**: the sign reverses.
Its C sequence diminishes (**+3.22%, +2.31%, +1.64%, +1.16%**), but leaves only
20% of frames and does not certify common n/composition or unseen neighbors.
The complete table includes all seven statistics and all six variants, so a
single favorable median cannot decide a rule.

### Goalkeeper convention: the quantity, not the variance

The new paired comparison includes count and centroid as well as the six Phase
2B-1 metrics. Pairing is on match, original frame ordinal and literal subset,
with all-frame and actual-keeper-removal scopes and jointly defined denominators.

Among actual-removal frames, width changes in only **1.17–2.15%**, with mean
absolute changes **0.0418–0.0761** native units. Either convention is defensible
for the declared observed width; excluded is a coherent companion to outfield
shape. Depth changes in **95.14–98.50%**, mean decrease **9.99–11.78** units;
hull changes in **98.58–99.71%**, mean decrease **190.25–219.62** squared units.
Use excluded to represent the observed outfield footprint, and included for a
full visible footprint. These are different quantities, not error corrections.

Mean absolute keeper deltas are **0.905–1.404** for mean pairwise distance,
**0.965–1.518** for median pairwise, and **0.511–0.856** for NN. The teammate_true
NN signed mean of -0.028 hides a mean absolute change of 0.856; it must not be
described as insensitive. Outfield spacing should use excluded and retain the
included pairing. For centroid x, actual-removal mean absolute changes are
**1.392, 2.475 and 2.040** for all-visible, teammate_true and teammate_false;
the corresponding y values are **0.443, 0.763 and 0.732**. These describe stored
native axes, without pooled direction-dependent positional interpretation.

Exclusion loses defined hulls in **12 / 84 / 20** frames, centroid/spans in
**1 / 3 / 2**, and distance metrics in **6 / 11 / 0**, respectively. These are
losses relative to defined included values; both variants can already be NA.
All current keeper flags are known. Count should accompany whichever population
is represented, with both inventories preserved; it is a record count.

### OOB, coincidence, polygon and actor policy

OOB-A and OOB-B/C primary retain all observations subject to mathematical
definition. OOB-B sensitivity removes **11,508 original frames (9.7048%)**, leaving
**107,073 (90.2952%)** before metric availability, across all 34 matches. Match
retention for included width ranges **85.09–94.37%**. OOB-C applies this same
whole-frame removal only to width, hull and mean pairwise distance because their
upper tails showed OOB enrichment (29.93%, 16.53%, 19.31%, against 9.70%).
It does not imply the other metrics are immune.

For all-visible outfield geometry, OOB-B changes median width **-0.957%**, depth
**-0.540%**, hull **-1.597%**, mean pairwise **-0.686%**, median pairwise **-0.599%**
and NN **-0.717%**. These modest population medians coexist with tail enrichment
and meaningful individual excursions (previous median/p95/max 1.380/5.049/10.663).
Retain supplied coordinates with flags in primary observations; prioritize OOB-C
and show the full OOB-B comparison. Do not remove only offending points.

Coincidence sensitivity removes **50 frames (0.0422%)**, leaving **118,531** before
metric availability, across five affected matches. Of these, 42 are in match
3895139 (about 1.12% of that match), so global rarity masks concentration. The
four multiple-actor frames overlap this group; D sensitivity removes only 46
additional frames for centroid/count/median pairwise after D primary exclusions.
No coincident frame is automatically removed for duplicate-invariant width,
depth or hull; their coincidence-sensitivity outputs therefore equal A exactly.

Across all six variants, coincidence exclusion changes centroid means by at most
**0.001738** (x) / **0.000858** (y), mean-pairwise means by **0.000269**, median-
pairwise means by **0.000138**, and NN means by **0.000744** native units. NN median
changes are at most **0.001486** units. These small population effects do not
negate the local multiplicity effects established in Phase 2B-2. A notable
discrete exception is teammate_false/excluded **median count 9 → 8**, despite a
mean count change of only **-0.000219**: removing 50 frames crosses the median
rank boundary. Do not report all count summaries as numerically insensitive.

All four multiple-actor frames remain unmodified. A includes them for generic
point-cloud diagnostics. D primary follows registry section 3 by excluding
`multiple`/`unknown` for later comparisons; A is the inclusion sensitivity.
The user-suggested generic-primary retention is mathematically feasible but would
revise that existing comparison policy, so it is not silently adopted. The
`actor_unique` candidate also requires a unique event join and actor status
`single`, excluding four current frames; actor-specific alignment remains
unapproved. No actor selection, coordinate alteration or deduplication occurs.

The polygon evidence remains **118,581 valid pitch-contained polygons**, all
13,812 OOB points outside their supplied polygon, and **20,582 polygon-inconsistent
frames**, with defining-extreme p05 edge distances about **0.266–0.391** units.
These are metadata and sensitivity concerns, not point/frame invalidity criteria.
Full-population edge flags were not persisted upstream; this phase reuses their
aggregate evidence and does not fabricate row-level edge eligibility.

### Filtering bias and human decisions

Coverage q20 retains 80% overall, but only **34.87% of Shot**, **20.74% of Goal
Keeper**, and **40.49% of Clearance** observations, versus **82.87% of Pass**.
At q80 only **10/889 Shot frames (1.12%)** remain. Match 3895292 retains only
**1,843/3,195 (57.68%)** under q20; match 3895202 retains **138/3,433 (4.02%)**
under q80, compared with a best-match q80 retention of **48.67%**. A cleaner-looking
sample would systematically lose large portions of particular contexts.

Even count q25 for all-visible/included retains **66.73–97.44%** across matches;
outfield q25 spans **63.59–96.30%** (see match table for exact denominators).
For all-visible/excluded, E q25/q20 retains **59.89%** overall but only **35.96%**
in its least-retained match; E q50/q40 retains **34.77%** overall and **12.74%**
in its least-retained match. Included E q50/q40 retains just **6.19% of Shot**
and **2.15% of Goal Keeper** frames. No tactical reason is inferred.

OOB exclusion also changes event representation: included width retains **86.56%**
of Pressure, **89.86%** of Pass and **97.53%** of Shot. Event tables show both
retention within each type and percentage-point changes in its share of the
defined population; rare categories retain their denominators rather than being
pooled away. Thus even the prioritized anomaly sensitivity is not neutral sampling.

The most defensible recommendation is a **combination**, not global validity:
metric mathematical minima plus the existing actor-comparison policy, keeper
choice tied to the observed quantity, count/coverage common-support disclosure
for intended comparisons, and metric-specific robustness exclusions. Primary
eligibility alone does not authorize an unstratified structural comparison.
Exact-n/coverage strata remain descriptive support checks; later contrasts,
minimum inferential support and weights require their own approved definition.

Human decisions remain: approve D primary with these comparison conditions;
approve or revise the q25 hull/q05 NN sensitivity landmarks; decide whether
OOB-C priorities suffice or OOB-B is routine for every metric; declare full
visible footprint versus outfield shape; and explicitly approve any departure
from the registry's actor-ambiguity comparison rule. Missing full-team locations,
unknown identity and unresolved coordinate/team semantics cannot be resolved by
thresholds. No calibration is marked locked or applied permanently.

### Artifacts and verification

Fourteen aggregate CSVs (about 13.8 MB combined) contain the candidate definitions,
28 empirical thresholds, 1,080 resolved metric/variant rules, retention and
distribution comparisons, 540 successive-threshold rows, 427 joint count/coverage
strata, event/match composition, paired keeper and OOB comparisons, the metric
matrix, evidence inventory and run provenance. They are derived summaries, not
raw coordinates, freeze frames or selected-frame exports, and remain ignored by
Git. The matrix also has the versioned documentation copy for review in a clone.

The notebook appends **16 cells, including eight executed code cells**, preserving
all **37 original cells** and their outputs. Two standalone PNGs show retention
versus median changes and successive-threshold changes for the all-visible
outfield example; all six variants remain in the CSVs and notebook tables. Both
figures were visually reviewed, and notebook schema validation passed.

**244 offline tests passed; two optional network tests were deselected.** The 16
new calibration cases cover deterministic empirical landmarks and ties, explicit
metric-specific and paired definitions, original-frame anomaly propagation,
mathematical availability without hidden thresholds, missing coverage/anomaly
semantics, zero-retained matches, distribution denominators, keeper pairing,
source/status rejection and preservation of raw records and excursions. An
all-undefined object-dtype hull fixture exposed a validation edge case; finite
validation now handles empty defined-value collections without coercing values.
`python -m ruff check .` passed. Commands used the repository `.venv` interpreter.

Independent artifact checks reconciled every match/event composition count with
the 1,080 retention rows, confirmed every candidate/metric/variant still covers
all 34 matches, and checked original notebook-cell equality. The Phase 2A CSV
hash matches both preceding diagnostic runs; Git reports no changes to locked
geometry, the metric registry, source foundation or any configuration file.
Recommendations remain **PROPOSED — REQUIRES HUMAN APPROVAL**.

## Phase 2B human approval and research-scope lock — 9 September 2026

**Phase 2B = LOCKED / COMPLETE.** Human methodological review is complete. The
approved contract is [methods section 37](../docs/methods_specification.md#37-human-approved-phase-2b-lock-and-operational-research-scope)
and the current [metric calibration matrix](../docs/phase2b3_metric_calibration_matrix.csv).
This decision supersedes the earlier proposed status; it does not rewrite the
empirical candidate comparisons or promote every tested alternative to a rule.
Saved candidate notebooks/CSVs retain their historical pre-approval meaning.

**Primary:** D-primary requires each metric's existing status `ok` and actor
status `single` or `none`. No universal n/visible-area cutoff, hard polygon or
edge rule, or automatic OOB exclusion. Null visibility minima explicitly mean
**no universal hard cutoff approved**. Primary eligibility never permits naive
pooling: every later structural comparison must inspect/report n, coverage,
subset, keeper convention, OOB/coincidence flags and actor status. Materially
different observation populations require an explicitly documented support or
adjustment strategy; no particular restriction, stratification, matching,
statistical adjustment or weighting is selected now.

**Keeper convention:** excluded is primary for centroid, width, depth, hull and
all spacing metrics representing observed outfield structure. Included remains
available for the explicitly named full visible footprint and sensitivity; count
inventories retain both. The prior evidence supports the distinction: affected
width changes are rare (1.17–2.15%), while keeper removal changes depth/hull and
spacing substantially. Width now follows the approved outfield population even
though either convention was empirically plausible.

**Robustness:** routine **OOB-B for all future headline spatial findings** excludes
the entire original frame if any nominal-pitch OOB point exists, with width/hull/
mean pairwise prioritized. A material change in a finding must be flagged,
investigated and reported, never resolved by selecting the convenient result.
The existing 11,508 affected frames (9.7048%), event/match imbalance and modest
population median shifts justify sensitivity reporting rather than primary
coordinate exclusion. Finite coordinates remain supplied values: no clipping,
projection, repair, point-only deletion or automatic primary frame removal.

The approved metric-specific plan retains the Phase 2B-3 sensitivity treatments:
whole-frame coincidence exclusion for count, centroid and spacing; OOB exclusion
for width and mean pairwise; keeper pairing prioritized for depth. Hull requires
n>=14 all_visible or n>=7 either teammate subset plus whole-frame OOB exclusion
in sensitivity only. NN sensitivity requires n>=11/10 for all_visible included/
excluded, n>=5 teammate_true and n>=4 teammate_false, plus whole-frame coincidence
exclusion. These fixed q25/q05 landmarks are robustness challenges, never valid-
frame definitions or thresholds to re-fit in each later group. Routine headline
OOB-B is additional to any prioritized metric treatment.

The 50 coincident frames remain unchanged; records are never deduplicated. Spans
and hull do not prioritize coincidence exclusion because exact repetitions leave
their geometry invariant. Multiple/unknown actors remain excluded from primary
comparisons and included in generic unchanged diagnostics. Actor-dependent work
requires `single` and a unique event join without approving actor-coordinate
semantics. Polygon containment and boundary distance remain metadata; prior
point/polygon inconsistencies do not establish invalidity.

**Research scope:** preserve the football-facing primary question:

> How did Bayer Leverkusen create dangerous space during their unbeaten 2023/24 Bundesliga season, and which recurring attacking sequences were most effective against different defensive structures?

Add its operational analytical formulation:

> How did Bayer Leverkusen’s attacking sequences alter the event-aligned visible spatial structure around possession, and which recurring structural changes preceded dangerous attacking outcomes?

Both are retained. The second describes what **event-aligned partial spatial
observations** directly support. They are not tracking, complete 22-player state,
named off-ball trajectories, continuous team-shape reconstruction, true controlled
space, pitch control or continuous movement. Use observed spatial structure,
visible outfield structure, event-aligned spatial state and spatial-state change.

Keeper-excluded hull is now termed **observed outfield convex-hull footprint**,
an observation-sensitive secondary structural measure. It remains in Phase 2A
with the same formula and minima. It is not complete occupied area or defensive
footprint. Later stretching/expansion/opening claims must triangulate relevant
width/depth, hull, spacing and local context; no composite is created for that purpose.

**Revised roadmap:** team/role semantics and attacking-orientation validation is
the immediate next gate. Then prioritize reliable possession/sequence construction,
event-aligned spatial-state sequences, descriptive spatial-state change,
success/failure definitions, comparisons preceding box entries/shots/future xG,
and recurring interpretable mechanisms. The action → visible state → structural
change → next action → outcome → mechanism chain guides method selection without
causal claims. Existing phase numbers are preserved where useful.

Inferred lines, high/mid/deep regimes, compactness composites, Voronoi, valuable-
space composites, graphs, clustering and learned spatial representations are
**OPTIONAL — REQUIRES METHOD-SPECIFIC JUSTIFICATION**. Each needs a specific
analytical need, observational support, interpretable incremental value over
simpler geometry, feasible validation and material football value. They are not
globally rejected. Existing tracking-dependent REJECT decisions stand.

**Change control:** this is **not a scientific version bump**. No research
population/outcome changed after effectiveness analysis; calibration followed
the pre-specified validation process; and scope was narrowed to the observation
model before tactical/outcome analysis. Phase 2A formulas, units, minima, point
validity, degeneracy and provenance, derived data, source revision and raw loading
remain unchanged. No tactical spatial interpretation is permitted until the
team/role semantics + attacking-orientation gate passes.

**Verification of this lock:** `python -m pytest` passed **244 offline tests**
with two optional network tests deselected; `python -m ruff check .` passed,
using the existing `.venv` interpreter. No diagnostic rerun or source retrieval
was needed. A direct lock audit confirmed the full Phase 2A registry measurement
contract and every registry formula/provenance table unchanged, equality of
parsed visibility YAML values, and unchanged SHA-256 hashes for 13 protected
files (all nine Phase 2A CSVs, geometry implementation, loader, source foundation
and project/source configuration). It also checked all eight matrix lock statuses,
keeper-excluded outfield conventions, routine headline OOB-B and the exact
approved hull/NN sensitivity values. Synthetic D-primary observations with low n,
missing/tiny coverage, OOB flags, polygon inconsistency and zero edge distance
remained eligible when their metric/actor statuses permitted; their inputs were
unchanged. No runtime helper or measurement code was modified. `git diff --check`
passed. The visibility YAML edit changes explanatory comments only.

## Phase 2C semantic and orientation audit — 9 September 2026

*Historical initial result. The subsequent restricted-scope human approval is
recorded at the end of this appendix; no finding below is withdrawn.*

**VALIDATED PARTIALLY — NOT LOCKED.** The complete audit ran against revision
`533862946a73608c134d18b78226b6371ce7173c` using the unchanged loader. All 34
matches, 137,765 events, 118,581 frames and both team lineups per match were
inspected. There were no duplicate event/frame IDs or orphan frames. The method
and pinned provider documentation are in
[section 38](../docs/methods_specification.md#38-phase-2c-teamrole-semantics-and-attacking-orientation).

### Team semantics and possession

All **118,585 actor records** have literal teammate True; four frames have
multiple actors. No valid observed point has an unknown teammate flag. All
checked named event actors are in their event-team lineup. This supports intended
actor-team semantics without independently identifying anonymous off-ball points.

Of **174,952 directed related-event edges**, **36,250** have identical native
coordinate/keeper multisets. Expected team-label agreement holds on **35,615**;
**635** edges contradict it. These touch **642 distinct frames**, counting
both incoming and outgoing links. A directed edge count is not a unique pair
or frame count. For example, opposite-team Clearance → Duel has 209 equal-cloud
edges, of which 207 fail expected label inversion. There are also contradictions
touching core types; the audit does not declare either endpoint correct.

The independent named shot freeze-frame dataset supplies **13,157** point
records, all in the expected team lineup. Nearest 360 point flags agree for
**11,855 (90.104%)**; nearest distance median is **0.980** units, p95 **3.091**,
maximum **43.126**. One nearest-point tie occurs. This is a proximity check,
not a point-identity match, and its disagreements do not establish an error rate
for 360 team labels. Coverage, coincident points and separately supplied positions
limit the comparison; no nearest-player identity is assigned or persisted.

Event/possession team IDs agree in **99,999** frames and differ in **18,582
(15.6703%)**, with neither missing. Selected exact-type breakdown:

| Event type | Same team | Different team |
| --- | ---: | ---: |
| Pass | 31,657 | 1,415 |
| Carry | 27,698 | 1,043 |
| Shot | 874 | 15 |
| Pressure | 1,210 | 8,870 |
| Dribbled Past | 27 | 419 |
| Dispossessed | 528 | 114 |
| Foul Won | 525 | 105 |
| Duel | 814 | 925 |
| 50/50 | 93 | 87 |
| Ball Receipt* | 32,121 | 1,277 |

### Orientation evidence and exceptions

All **916 event shots** have valid end x, ranging **92.1–120**; 391 end exactly
at 120. Starts range **57.7–118.8**, with 914 above x=60. Every one of **134
nonempty match/team/period strata** has median start x at least 91.6. Two
possible team/half strata have no shots. Both teams and halves share the same
attacking end in event coordinates; fixed-pitch period flipping is unsupported.
The linked subset has **889 shots**, all direct in the actor-distance diagnostic.

Normal passes (no provider pass.type) have both positive and negative delta x:
20,189 positive and 13,180 negative among 33,689 valid all-event vectors. Carries
likewise have 17,312 positive and 9,496 negative among 32,369 vectors. Zero-dx
events account for the remainder. These are supporting distributions, not a
definition that passes or carries are inherently forward.

Pressure distinguishes event versus possession references particularly well:
among **8,870 differing-team frames**, **8,869** actors match the event start
exactly as supplied or after exact float32 encoding; one does not. The visible
literal teammate keeper mean-x median is **3.659** (2,271 frames with such a
keeper), versus **114.902** for literal non-teammate keepers (1,443 frames).
This supports event-team rather than universal possession-team coordinates;
visible-keeper exceptions remain in the distributions. Shots alone would not
distinguish these hypotheses where team IDs agree.

Phase 1B patterns recur: Dribbled Past **100% mirrored**, Dispossessed **97.348%**,
Foul Won **96.825%**; Duel **44.508% mirrored**, 50/50 **50%**, Ball Receipt*
**11.555%**, Dribble **41.915%**. Pass is **99.906% direct**, with exact ties;
Carry **99.732%**, Pressure **99.990%**. Rates use frames with comparable single
actor distances, not all records. Unchanged exact related clouds support paired
reuse for some opposite-team events; they do not establish a correction for
every observation. Direct-versus-mirrored rank never selects a normalization.

### Conditional implementation and visual review

The source/type/join/known-flag/single-actor/exact-encoding/no-linked-conflict
gates yield:

| Type | All linked frames | Validated conditional scope | Unsupported |
| --- | ---: | ---: | ---: |
| Pass | 33,072 | 32,999 | 73 |
| Carry | 28,741 | 28,648 | 93 |
| Pressure | 10,080 | 10,076 | 4 |
| Shot | 889 | 873 | 16 |
| All other types | 45,799 | 0 | 45,799 |
| Total | 118,581 | **72,596** | **45,985** |

Among the 186 unsupported core frames, first-failure reasons are 83 linked-team
conflicts, 101 nonexact actor encodings and two unresolved actor statuses.
Reasons are ordered and need not be independent. The 642 conflict-frame count
includes non-core types and is reported separately rather than hidden by the
first-failure status. The four-type scope is a conservative additional semantic
restriction, not a replacement for the Phase 2B geometry sample.

Within it, **1,200,432 anonymous point records** can receive conditional
Leverkusen/opponent labels. There are **43,781 identity frames** and **28,815
180-degree frames** when Leverkusen is the target. Arithmetic validation covers
**1,273,028 locations** (those points plus event starts); maximum round-trip
absolute error is **7.106e-15** units, with zero for identity. This is numerical
precision, not a calibrated spatial tolerance or evidence for an ambiguous
frame. Synthetic non-collinear examples verify both-axis rotation, handedness,
pairwise-distance and hull-area invariance, including OOB coordinates.

**27 deterministic native/normalized figures** cover both teams, both halves,
home/away matches, Shot/Pass/Carry, Pressure and seven difficult types, an
equal-cloud conflict and nonexact core actors. They are review examples rather
than a random prevalence sample. Identity and rotated examples preserve team
labels and rotate the polygon, actor, points and event vector consistently;
unsupported examples show literal T/F native markers and an explicitly empty
normalized panel. Representative inspection includes a second-half identity
pass, an opponent shot rotated through both axes, and Dispossessed with distant
native event/actor locations. No visual inspection assigns named point identity.

The [style guide](../docs/visualization_style_guide.md) and centralized constants
establish a conditional convention: Leverkusen red `#B51232`, opponent charcoal
`#30343B`, action gold `#A65F00`, L/O text, keeper squares, outfield circles and
actor halos. Solid recorded-action vectors and reserved dashed event-transition
indicators have distinct meanings. Unrestricted football-facing use is not locked.

### Reproduction, validation and readiness

`scripts/semantics_orientation.py` writes 14 aggregate/manifest CSVs prefixed
`phase2c_` and the 27 figures; it never persists raw JSON or a full duplicate
frame table. Source SHA is included in every CSV; run summary includes retrieval
completion UTC and the match inventory records denominators. The new
`04_semantics_orientation.ipynb` reads these outputs offline and checks source
and count consistency. `--figures-only` can refresh styling from the existing
audit manifest without recomputing season semantics; a changed semantic rule
requires the complete audit.

Offline verification: **268 tests passed**, two optional network tests
deselected; `ruff check .` and `git diff --check` passed. All 13 protected-file
SHA-256 hashes remain unchanged: nine Phase 2A CSVs, geometry implementation,
loader, source foundation and project/source configuration. The old geometry
and defensive-structure notebooks, registry formulas, visibility configuration
and locked Phase 2B matrix are untouched. The new notebook executed all nine
code cells successfully and passed notebook schema/output validation.

The remaining blockers are concrete: conflicting labels on reused clouds;
unresolved frame reference and actor association for mixed/paired types; and no
independent ordinary off-ball identity with which to settle all exceptions.
Provider clarification or an explicitly justified restricted research scope
must resolve the relevant gate. **Full-sample reliable sequence construction
is not ready to begin.** No possessions, transitions, tactical zones, outcomes,
clustering, tracking or causal claims were implemented.

## Phase 2C-2 sequence-readiness audit — 10 September 2026

*Historical readiness recommendation before human approval. The final decision
record below supersedes its pending-lock status only.*

**Readiness classification: READY — WITH RESTRICTIONS. Recommendation A:
lock the restricted semantic scope for validated spatial-anchor sequence
analysis, subject to human review. Phase 2C remains VALIDATED PARTIALLY — NOT
LOCKED.** This is an empirical readiness judgment, not an eligibility decision.
No unsupported event type, tactical method, dangerous outcome or sequence
threshold is promoted. Phase 2A/2B data, formulas, source behavior and contracts
remain unchanged.

### Population and reconciliation

The pinned live run completed at `2026-09-10T17:47:26.095244+00:00` using revision
`533862946a73608c134d18b78226b6371ce7173c`, Python 3.14.0, pandas 3.0.5 and NumPy
2.5.2. All 34 matches were processed in memory. Reapplying the existing Phase 2C
gates reproduced **137,765 events, 118,581 linked frames, 72,596 validated frames
and 45,985 unsupported frames** exactly. No raw records were saved.

The diagnostic group is match + period + provider possession ID + possession-team
ID 904. Nineteen provider IDs span periods, so there are **2,888 period-bounded
Leverkusen possessions**, compared with 2,869 distinct match/provider-possession
IDs. No new possession-boundary algorithm is introduced. The complete selected
stream contains **86,025 events**, including opponent, unsupported, unlinked,
administrative and stoppage events. There are **74,647 linked frames**, of which
**46,143 (61.8149%)** validate and **28,504 (38.1851%)** remain unsupported.
Median event/frame/anchor counts per possession are **20/17/10**.

Elapsed times use supplied period-local timestamps, including stoppage time;
possession duration is last event start minus first event start. Final action
duration, halftime and an inferred across-period clock are not added. This is
not active ball-in-play time. Zero-anchor times/spans are missing; one-anchor
spans are zero. No gap crosses a possession or period boundary.

### Primary anchor-count coverage

Every rate below uses all 2,888 diagnostic possessions as its denominator.

| Validated anchors | Possessions | Percentage |
| --- | ---: | ---: |
| 0 | 176 | 6.0942% |
| >=1 | 2,712 | 93.9058% |
| >=2 | 2,557 | 88.5388% |
| >=3 | 2,428 | 84.0720% |
| >=4 | 2,266 | 78.4626% |
| >=5 | 2,123 | 73.5111% |
| >=6 | 1,986 | 68.7673% |
| >=8 | 1,734 | 60.0416% |
| >=10 | 1,518 | 52.5623% |

Anchor-count mean is **15.9775**, median **10**, p05 **0**, p25 **4**, p75 **22**,
p90 **38.3**, p95 **52** and maximum **120**. Quantiles use linear interpolation;
p90 need not be an observed integer count. All 176 zero-anchor possessions
remain in the inventory. Their median duration is zero and maximum is 68.246
seconds, so missing support is neither exclusively an administrative issue nor
confined to short groups.

### Temporal and event-gap density

There are **43,431 consecutive-anchor intervals**, exactly the sum over
possessions of `max(anchor_count - 1, 0)`. These describe spacing between trusted
event-aligned partial observations, **not continuous tracking resolution**.
Longer/richer possessions contribute more intervals to the pooled distribution.

| Measure | Mean | Median | p25 | p75 | p90 | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Elapsed seconds | 1.5251 | 1.103 | 0.665 | 1.765 | 3.214 | 4.5825 | 31.708 |
| Event-index difference | 1.7221 | 2 | 1 | 2 | 3 | 4 | 22 |
| Intervening events | 0.7221 | 1 | 0 | 1 | 2 | 3 | 21 |

| Gap at most | Intervals | Percentage |
| --- | ---: | ---: |
| 1 second | 19,356 | 44.5672% |
| 2 seconds | 34,446 | 79.3120% |
| 3 seconds | 38,553 | 88.7684% |
| 5 seconds | 41,679 | 95.9660% |
| 10 seconds | 43,247 | 99.5763% |
| 15 seconds | 43,388 | 99.9010% |

Five intervals have identical anchor timestamps and contribute zero-second gaps.
There are 21,135 adjacent-event anchor pairs and 17,935 pairs with one intervening
event; the remaining 4,361 skip two or more events. Actual row positions count
intervening events, independently of provider index differences. They agree with
index difference minus one in this pinned sample. The longest time interval is
31.708 seconds in match 3895067, period 1, possession 25, Carry → Carry, with
three intervening events. Long time gaps and large event gaps therefore need not
coincide. Nothing is interpolated across them.

### Match and duration distribution

All 34 matches contribute each of the four validated anchor types. The match
table and figure cover every match; >=3-anchor possession rates range from
**72.0930% to 92.7083%**. The relatively weakest three are Freiburg (3895121,
29 October: 72.0930%), RB Leipzig (3895052, 19 August: 74.4186%) and Bayern Munich
(3895232, 10 February: 74.7126%). These are descriptive ranks, **not exclusions**.
The maximum is Augsburg (3895194, 13 January: 92.7083%). Match coverage is broad
enough that candidate sequences are not supplied only by a few fixtures.
`phase2c2_match_coverage.csv` includes each match's possession count, mean/median
anchors, >=1/2/3/5 rates, median/p90 time gap and linked-frame validation fraction.
Its denominator includes opponent events within Leverkusen possessions.

| Duration, seconds | Possessions | Median events | Median anchors | >=2 anchors | >=3 anchors |
| --- | ---: | ---: | ---: | ---: | ---: |
| [0,5) | 531 | 5 | 1 | 47.2693% | 31.4501% |
| [5,15) | 744 | 12 | 6 | 95.0269% | 90.3226% |
| [15,30) | 648 | 25 | 13 | 99.2284% | 98.6111% |
| [30,60) | 611 | 46 | 25 | 98.8543% | 98.6907% |
| [60,infinity) | 354 | 84 | 47 | 99.4350% | 98.0226% |

Longer groups generally supply more anchors. Very short groups account for much
of the weak count coverage; bins are descriptive and create no future duration
eligibility rule. The long-duration group still contains sparse exceptions.

### Anchor types, transitions and event team

| Anchor type | Anchors | Share of anchors | Possessions containing | Share of possessions | Matches |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pass | 20,921 | 45.3395% | 2,588 | 89.6122% | 34 |
| Carry | 18,525 | 40.1469% | 2,462 | 85.2493% | 34 |
| Pressure | 6,109 | 13.2393% | 2,086 | 72.2299% | 34 |
| Shot | 588 | 1.2743% | 541 | 18.7327% | 34 |

The largest consecutive-anchor transitions are Pass → Carry (15,119; 34.8115%),
Carry → Pass (13,538; 31.1713%), Carry → Pressure (3,556; 8.1877%), Pressure → Pass
(3,303; 7.6052%) and Pass → Pass (2,439; 5.6158%). The complete transition table
includes count, percentage of all intervals, median elapsed seconds and match
coverage for every observed pair. These are event-label frequencies without
tactical interpretation; related observations are not necessarily independent.

| Event team | Pass | Carry | Pressure | Shot | Total anchors | Share of all anchors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Leverkusen | 20,092 | 17,892 | 732 | 581 | 39,297 | 85.1635% |
| Opponent | 829 | 633 | 5,377 | 7 | 6,846 | 14.8365% |

Opponent anchors occur in **2,074 possessions (71.8144%)** and all 34 matches.
Opponent Pass, Carry and Pressure anchors each cover all 34 matches; the seven
opponent Shot anchors occur in seven possessions and seven matches. Pressure
accounts for 78.5422% of opponent anchors. Possession team is therefore materially
different from event team; automatically dropping opponent events would change
the available spatial history. Both teams remain explicit and included.

### Shot-containing and literal shot-ending possessions

Shot containment refers to any provider Shot, independently of 360 validation.
There are 615 Leverkusen and seven opponent Shot events in the selected stream.
No xG or success/failure definition is used. `has_goal` flags 88 possessions with
a Shot outcome Goal; it is not a count of season team goals or own goals.

| Group | Possessions | Median anchors | >=2 | >=3 | >=5 | Gap median (s) | Gap p90 (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Contains Shot | 571 | 14 | 92.9947% | 87.7408% | 79.5096% | 1.133 | 3.327 |
| No Shot | 2,317 | 10 | 87.4407% | 83.1679% | 72.0328% | 1.091 | 3.1711 |
| Literal final event Shot | 42 | 14 | 90.4762% | 88.0952% | 80.9524% | 1.197 | 3.4381 |

The alternate Shot-containing attrition inventory is 571 total → 567 with >=1
anchor → 531 with >=2 → 501 with >=3 → 480 with >=4 → 454 with >=5. Four have zero
validated anchors. The 42 literal Shot-ending groups are **not an estimate of
final meaningful Shot-ending possessions**: goalkeeper or context records can
follow a Shot within the provider group. Defining which records to disregard is
deferred. Box-entry inventory is also deferred because full event-location
semantics and entry/completion conventions are unresolved; no permanent box-entry
rule is introduced from provisional zone bounds.

### Candidate state counts and temporal windows

The season supplies **46,143 observed anchor states**. Here “state” means an
eligible semantic frame, not a complete pitch or independently observed 22-player
configuration. The candidate inventory is not the final sequence dataset.

| States per candidate | Capable possessions | Consecutive overlapping tuples | All anchors in capable possessions |
| --- | ---: | ---: | ---: |
| 2 | 2,557 | 43,431 | 45,988 |
| 3 | 2,428 | 40,874 | 45,730 |
| 4 | 2,266 | 38,446 | 45,244 |
| 5 | 2,123 | 36,180 | 44,672 |
| 6 | 1,986 | 34,057 | 43,987 |
| 8 | 1,734 | 30,219 | 42,357 |

| Inclusive window | Consecutive pairs | Consecutive triples |
| --- | ---: | ---: |
| 3 seconds | 38,553 | 25,915 |
| 5 seconds | 41,679 | 34,865 |
| 10 seconds | 43,247 | 40,152 |
| 15 seconds | 43,388 | 40,731 |

There are **2,424 possessions** with >=3 anchors inside some 10-second interval,
**2,251** with >=4 inside 10 seconds, and **2,427** with >=3 inside 15 seconds.
The windows overlap and no window is selected. These are feasibility counts,
not independent samples or analysis inclusion decisions.

### Deterministic timeline inspection

The manifest selects ten distinct groups using the documented first-key/quantile
rules in methods section 39; all their events are saved as bounded derived
timeline rows, with no raw locations. Nine examples come from the first sorted
match, so selection is not a representative prevalence sample.

| Review stratum | Match / period / possession | Events | Anchors | Duration (s) |
| --- | --- | ---: | ---: | ---: |
| Zero anchors | 3895052 / 1 / 1 | 4 | 0 | 0.000 |
| One anchor | 3895052 / 1 / 75 | 4 | 1 | 0.740 |
| Two anchors | 3895052 / 1 / 48 | 8 | 2 | 4.602 |
| Moderate count | 3895052 / 1 / 6 | 16 | 9 | 6.815 |
| High count | 3895052 / 2 / 120 | 91 | 54 | 95.123 |
| Contains Shot | 3895052 / 1 / 19 | 35 | 16 | 27.586 |
| Opponent anchor | 3895052 / 1 / 9 | 13 | 6 | 8.716 |
| Long / relatively sparse | 3895052 / 1 / 26 | 57 | 25 | 62.576 |
| Short / relatively dense | 3895052 / 1 / 15 | 9 | 5 | 6.089 |
| Maximum count | 3895210 / 1 / 15 | 233 | 120 | 173.277 |

The zero-anchor example consists of Starting XI/Half Start records at time zero;
it demonstrates the unfiltered provider denominator. The one-anchor group keeps
its unsupported terminal Foul Won. The two-anchor group includes a validated
opponent Pressure and ends in unsupported Foul Won. The Shot-containing example
ends in Goal Keeper, illustrating the difference between shot containment and a
literal final Shot. The maximum-count example still contains 72 unsupported
linked frames and 41 unlinked events; a large anchor count does not make every
event a trusted spatial observation. Long/short density is relative to empirical
quartiles: duration p25/p75 = 7.0025/39.65175 seconds and anchors-per-second
p25/p75 = 0.467534/0.788185. The long example has 25 anchors over 62.576 seconds,
so “sparse” here means lower relative rate, not near-zero anchor count.

### Human-review conclusion and validation

The concise machine-readable review table is
`outputs/diagnostics/phase2c2_sequence_readiness_summary.csv`. It records the
2,888-possession denominator, median event/frame/anchor counts, every requested
anchor rate, median/p90 temporal gaps, <=3/5-second rates, Shot-containing >=3
coverage and minimum/maximum match >=3 coverage. The count attrition and gap/match
figures are `phase2c2_sequence_readiness_waterfall.png`,
`phase2c2_anchor_time_gaps.png` and `phase2c2_match_coverage.png`.

**READY — WITH RESTRICTIONS** follows jointly from broad possession coverage,
substantial anchor counts, short typical time and event gaps, support throughout
all 34 matches, and strong Shot-containing coverage. This justifies recommending
**A — lock the restricted semantic scope for validated spatial-anchor sequence
analysis**. Further unsupported-type semantic work is not necessary before
restricted sequence design on coverage grounds. Expanding the semantic population
would still require resolving its existing blockers; no expansion is justified
merely to increase sample size.

The recommendation retains partial visibility, conditional anonymous-point
semantics, explicit event/possession-team distinction, sparse/short exceptions,
long-gap tails and comparison-specific Phase 2B observational support. Semantic
anchor counts are not counts of valid values for every geometry metric. Future
sequence definitions must still address timing, repetition, roles, boundary
context and measurement support through human review. No minimum anchors,
maximum gap, duration window, final outcome, tactical classification or automatic
Phase 2C lock is implemented.

Verification: **297 offline tests passed; two optional network tests deselected**.
The 29 new tests cover provider grouping and selection, period and match context,
retained unsupported/unlinked events, anchor extraction/order, time/index/row gaps,
opponent events, match and Shot aggregation, incoming semantic conflicts,
unpromoted types, empty intervals, no interpolation, no eligibility filter,
deterministic timelines and raw-input preservation. `python -m ruff check .` and
`git diff --check` passed. All ten code cells of the new notebook executed
successfully offline. The three figures were rendered and visually inspected;
the ECDF shows both its short-gap detail and full long-gap range. The new code
reuses the unchanged loader and semantic gates, and the full-season scope counts
reconcile exactly with Phase 2C. Only derived `phase2c2_` outputs are written;
previous Phase 2A/2B outputs and locked implementation/configuration are untouched.

## Phase 2C restricted-scope human approval — 10 September 2026

**Phase 2C = LOCKED / COMPLETE — RESTRICTED SEMANTIC SCOPE.** Human methodological
review approved Recommendation A for **validated spatial-anchor sequence analysis**.
The initial result (VALIDATED PARTIALLY — NOT LOCKED) and Phase 2C-2 readiness
result (READY — WITH RESTRICTIONS) remain historical evidence. This decision
closes Phase 2C only for the approved population; it does not resolve all frames
or authorize unrestricted full-sample normalization or spatial-sequence analysis.

The one authoritative scope remains `validated_core_event_team_scope`, with the
unchanged `frame_semantics()` logic. Pass, Carry, Shot and Pressure still require
every existing frame-level gate. No type is universally safe, and unsupported
types retain their classifications, related-cloud contradictions and orientation
uncertainty. No named identity is assigned to ordinary off-ball points.

The locked-run reconciliation is specific to revision
`533862946a73608c134d18b78226b6371ce7173c`:

| Population | Possession groups | Events | Linked frames | Validated | Unsupported linked |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full audited 34-match season | — | 137,765 | 118,581 | 72,596 | 45,985 |
| Leverkusen provider possession/period groups | 2,888 | 86,025 | 74,647 | 46,143 | 28,504 |

These are observed counts for the reviewed release, not expectations for another
revision. Of the Leverkusen-possession anchors, 6,846 are opponent events. The
complete event context retains its own event-team and possession-team fields;
the latter does not establish instantaneous control or change an opponent event
into a Leverkusen action.

Within validated scope, teammate True/False maps to event team/other known match
team. Native event-team attacking direction is increasing x. An explicit
Leverkusen reference keeps `(x_raw,y_raw)` for Leverkusen events and uses
`(120-x_raw,80-y_raw)` for opponent events, with `identity_explicit` and
`rotated_180` statuses respectively. Raw coordinates remain unchanged. No half,
home/away, possession-team or x-only flip is approved. Unsupported frames return
unresolved labels and no trusted normalized spatial state.

Unsupported events remain valid full-stream context, not invalid/deleted football
events or data eligible for heuristic repair. No interpolation, forward fill or
inferred spatial state is permitted. Dribbled Past, Dispossessed, Foul Won, Duel,
50/50, Ball Receipt*, Dribble and other mixed/unsupported types need no additional
semantic work before restricted design; revisit them only for a demonstrated
downstream need. Pressure can supply a validated frame but is not automatically
ball location, a Leverkusen possession action, exact defender-to-ball distance
or a continuously observed pressure episode.

Approval rests on the pre-specified readiness evidence: >=1/2/3/4/5-anchor rates
of 93.91/88.54/84.07/78.46/73.51%, median 10 anchors, median/p90 time gaps of
1.103/3.214 seconds across 43,431 intervals, 88.77% <=3 seconds and 95.97% <=5,
match >=3 rates of 72.09–92.71%, and >=3/5 rates of 87.74/79.51% among 571
Shot-containing possessions. All four anchor types occur in all 34 matches.
These measure coverage, not tracking resolution or analytical sequence validity.

The architectural lock separates complete ordered event context from the trusted
spatial-anchor subset. Semantic validity does not replace Phase 2B eligibility:
metric status, actor policy, goalkeeper convention, selected-player counts,
visible-area support, OOB/coincidence flags, robustness checks and common
observational support still govern each geometry comparison. A validated frame
can lack a usable or comparable value for a particular metric.

The visualization convention is locked only for validated frames: Leverkusen
red, opponent charcoal, action gold, outfield circles, keeper squares, actor
halo/outline and useful L/O labels. Unsupported frames cannot use semantic team
colors. Solid arrows require provider action start/end coordinates; dashed arrows
are future event-to-event progression indicators. Neither is a tracked trajectory.
This lock implements no sequence plot or tactical interpretation.

**No scientific version bump is required.** The approved restriction follows
pre-outcome semantic validation and the planned feasibility audit. Descriptive
Shot coverage is not an effectiveness result or a selected success/danger outcome.
No outcome, tactical or effectiveness finding drove the population choice, and
raw data, Phase 2A/2B methods and both research-question formulations are unchanged.

**Phase 3 — Possession and Spatial-Sequence Method Design is now authorized**
within the approved semantic population. Unsupported semantics, off-ball identity,
continuous tracking, unrestricted normalization, sequence unit/start/end/eligibility,
anchor/time/event-gap minima or maxima, duration/windows, spatial-state features,
box entry, future-xG horizon, success/failure, specific common-support implementations
and tactical mechanisms remain unresolved. These do not block the restricted
Phase 2C completion. No sequence dataset, threshold, outcome or tactical method
is introduced by this approval.

The implementation change is limited to approval-status metadata and a
revision-bound reconciliation guard, preserving every semantic gate. The guard
checks the full-season and Leverkusen-possession totals before a future readiness
run writes outputs; focused offline tests exercise count drift and wrong-revision
rejection without network retrieval. The existing derived audit files and executed
notebooks are preserved as historical evidence; the current approval lives here
and in methods section 40. No live season rerun is needed for this status lock.

Lock verification: **309 offline tests passed; two optional network tests
deselected**. The 12 added tests cover approval metadata and acceptance/rejection
of the exact revision-bound reconciliation, including drift in any of the nine
population counts. `python -m ruff check .` and `git diff --check` passed. An AST
comparison against the preceding commit confirmed every semantic mapping,
orientation and normalization function is unchanged, along with semantic-evidence
helpers; only the diagnostic later-use status text changed. The saved pinned
inventory and possession table passed the new reconciliation guard, including
6,846 opponent anchors. A combined SHA-256 check over 155 protected files confirmed
unchanged diagnostic CSVs, figures, notebooks, configuration, loader, geometry
implementation, metric registry and Phase 2B calibration matrix. This verifies
preservation of the audited population and methods without re-downloading or
rewriting the historical evidence.

# Technical appendix — draft

Future content: source provenance, release/retrieval details, environment,
observability diagnostics, sample exclusions, metric definitions, calibrated
configuration, sequence rules, validation and sensitivity analysis.

Current implementation includes data loading, preserved event transforms and the
Phase 1/1B observability audit and the eight locked Phase 2A geometry families.
Historical checks below retain their original phase-specific scope; the Phase 2A
implementation and initial diagnostics are recorded in the final section.
See `docs/methods_specification.md` for pending decisions and observational limits.

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

# Technical appendix — draft

Future content: source provenance, release/retrieval details, environment,
observability diagnostics, sample exclusions, metric definitions, calibrated
configuration, sequence rules, validation and sensitivity analysis.

Current implementation includes data loading, preserved event transforms and the
Phase 1 observability audit. No Phase 2 spatial metrics are implemented.
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

The cause is unresolved. A release/version mismatch is a possibility, not a
verified explanation. No heuristic relinking or interpolation was attempted.

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

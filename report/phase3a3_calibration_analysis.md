# Phase 3A-3: exploratory segmentation calibration

**11 September 2026 — ANALYSIS ONLY; no segmentation rules or method lock.**

Retreat and persistence distinguish the centers of the reviewed distributions,
but every supplied numerical diagnostic overlaps across labels. Recovery is
useful context, with important counterexamples. The strongest prerequisite for
rule design is resolving episode-local measurement scope: some workbook-safe
rows explicitly describe a new phase while still referencing an earlier provider
peak. These findings describe the matrix, not validated episode-local thresholds.

## A. Data used

The authoritative input is the preserved
[calibration workbook](../data/calibration/Phase3A3_Segmentation_Calibration_Matrix.xlsx),
SHA-256 `683a232989f9956c788815299b9f9c4577ad91007c219e0a50af5142ec7b4006`.
Its provenance identifies StatsBomb revision
`533862946a73608c134d18b78226b6371ce7173c`. No football cases were relabeled,
no event streams were re-reviewed, and no outcome variables entered the analysis.
StatsBomb 360 remains event-aligned partial observation, not tracking data.

The primary descriptive cohort requires `threshold_safe == TRUE`, one of the
three reset-review labels, `provider_peak_contaminated == FALSE`, and either
`lock_status == LOCKED` or an explicitly confirmed partial-lock candidate.
The only partial exceptions are **C15_M07, C17_M04 and C17_M05**, each explicitly
labeled POSSIBLE_RESET. This uses the workbook Provenance statement that only
explicitly confirmed labels in C15/C17 are included. It does not promote those
cases to fully locked status or infer labels for their other proposals.

| Cohort | CONTINUE | POSSIBLE_RESET | CLEAR_RESET | Total |
| --- | ---: | ---: | ---: | ---: |
| Primary: locked plus explicit partial confirmations | 62 | 11 | 18 | 91 |
| Sensitivity: strictly LOCKED only | 62 | 8 | 18 | 88 |
| Distinct cases contributing to primary class | 22 | 8 | 9 | 24 distinct overall |

The 91 rows span 24 provider parents and nine matches. Class-specific case counts
are not additive. Candidates within a case are correlated observations, sometimes
multiple samples of the same reset excursion; 18 CLEAR_RESET rows are **not** 18
independent resets. C01 and C28 have no matrix candidates; their absence is recorded
in workbook provenance and is not filled with synthetic observations.

Of 127 matrix rows, 36 are excluded: 21 flagged as provider-peak contaminated,
six deferred/unlabeled, and nine other threshold-unsafe rows. These are disjoint
groups in this workbook. The separate **46 Hard_Boundaries observations** are
archived for traceability only; they never enter reset summaries or sweeps.
All 127 inclusion decisions and reasons are in the
[inclusion audit](../outputs/diagnostics/phase3a3_inclusion_audit.csv).

Overrides remain separate from original diagnostics:

| Candidate | Label | Original provider retreat | Episode-local override | Included? |
| --- | --- | ---: | ---: | --- |
| C14_M09 | POSSIBLE_RESET | 41.2 | approximately 21 | No |
| C16_M06 | POSSIBLE_RESET | 35.6 | approximately 14 | No |
| C16_M08 | CLEAR_RESET | 43.0 | approximately 33 | No |

An override alone does not repair the other peak, time, run or recovery variables,
and all three rows remain `threshold_safe == FALSE`.

All calculations below describe **as-supplied provider-parent diagnostics**. The
workbook's safe flag is an inclusion permission for exploration, not proof of
episode-local recomputation. C09_M03, C10_M07 and C12_M04 are explicit examples:
their notes describe new/rebuilt phases, but their retreats remain 88.7, 50.2 and
46.2. They remain visible in the requested cohort without being silently repaired
or relabeled. These values cannot establish the distribution of retreat inside
the new episode. A verified episode-local cohort is unavailable in this input.

### Missingness and measurement definitions

| Metric: missing count | CONTINUE (62) | POSSIBLE_RESET (11) | CLEAR_RESET (18) |
| --- | ---: | ---: | ---: |
| Retreat, signed negative dx, magnitude, time/events since peak | 0 each | 0 each | 0 each |
| Negative run length | 34 | 0 | 2 |
| Nonpositive run length | 32 | 0 | 0 |
| Time/events to recovery | 30 each | 0 each | 5 each |

Blanks remain missing, including run lengths; they are not converted to zero.
Retreat is in StatsBomb x-coordinate units, not meters. The signed
`largest_recent_negative_dx` is retained; its separately derived absolute value
is `largest_recent_backward_magnitude`. This is the largest backward vector in
the last three safe actions, not cumulative retreat. Time/events since peak refer
to the latest equal running peak. Recovery is the first later safe vertex reaching
that reference peak, timed **from the candidate**, not from the start of a reset
excursion. Event counts and safe-action run counts have different denominators.
These definitions follow existing [Phase 3A-2 documentation](../docs/methods_specification.md#42-phase-3a-2a-representative-possession--boundary-review-pack).

### Summary-sheet reconciliation

Fresh calculations agree with workbook class counts and mean retreat, backward
magnitude and time since peak. Recovery means differ:

| Label | Cached summary mean (s) | Recomputed mean over available times (s) | Available / class total |
| --- | ---: | ---: | --- |
| CONTINUE | 7.872 | 15.252 | 32 / 62 |
| POSSIBLE_RESET | 31.196 | 31.196 | 11 / 11 |
| CLEAR_RESET | 20.230 | 28.011 | 13 / 18 |

The discrepant cached means equal the observed-time sum divided by the **entire
class size**. That is inappropriate for a conditional observed-recovery mean.
Summary formulas and caches are preserved as reference, never consumed as
measurements or thresholds; the workbook is unchanged. The analysis does not
claim to have recalculated Excel formulas. See the
[reconciliation table](../outputs/diagnostics/phase3a3_summary_reconciliation.csv).

## B. Univariate distributions

The [full statistics CSV](../outputs/diagnostics/phase3a3_descriptive_statistics.csv)
and [generated numerical appendix](../outputs/diagnostics/phase3a3_numerical_appendix.md)
provide total count, available count, missing count, mean, median, sample standard
deviation (`ddof=1`), minimum, p10, p25, p50, p75, p90, maximum and IQR for all nine
metrics, including both signed dx and magnitude. Percentiles use linear
interpolation; median and p50 intentionally agree. No missing-value imputation,
confidence weighting or class balancing is applied.

| Metric | CONTINUE median [p25, p75] | POSSIBLE_RESET median [p25, p75] | CLEAR_RESET median [p25, p75] |
| --- | --- | --- | --- |
| Retreat | 3.85 [0, 8.65] | 17.9 [13.85, 28.35] | 44.8 [36.3, 48.425] |
| Largest backward magnitude | 4.8 [1.925, 8.8] | 13.8 [7, 19.55] | 17.05 [11.175, 27.025] |
| Negative run | 1 [1, 1] | 2 [1.5, 2] | 3.5 [2, 4] |
| Nonpositive run | 1 [1, 2] | 2 [2, 2.5] | 3.5 [2, 4] |
| Time since peak (s) | 0 [0, 1.307] | 2.877 [0.331, 9.496] | 8.957 [5.829, 17.881] |
| Events since peak | 0 [0, 2.75] | 4 [1, 7] | 10.5 [5.25, 18] |
| Observed recovery time (s) | 5.906 [3.187, 31.775] | 26.898 [14.647, 35.245] | 25.068 [21.447, 26.651] |
| Observed recovery events | 6.5 [2.75, 26.25] | 30 [16, 40] | 26 [21, 30] |

Retreat has well-separated IQRs, but substantial tail overlap. All three class
pairs overlap in the observed range of **every** requested metric. The following
are intersections of class ranges, not regions of equal probability:

| Metric | CONTINUE / POSSIBLE | CONTINUE / CLEAR | POSSIBLE / CLEAR |
| --- | --- | --- | --- |
| Retreat | [10.2, 37.3] | [19.7, 88.7] | [19.7, 37.3] |
| Backward magnitude | [3.9, 22.2] | [2, 40.4] | [3.9, 22.2] |
| Negative run | [1, 4] | [1, 4] | [1, 4] |
| Nonpositive run | [1, 4] | [1, 5] | [1, 4] |
| Time since peak (s) | [0, 13.269] | [2.799, 21.530] | [2.799, 13.269] |
| Events since peak | [0, 14] | [2, 16] | [2, 14] |
| Observed recovery time (s) | [5.774, 74.454] | [0.445, 69.913] | [5.774, 69.913] |
| Observed recovery events | [5, 72] | [1, 68] | [5, 68] |

Eight of 62 CONTINUE and all 18 CLEAR_RESET rows lie in their shared retreat
range. Five of 11 POSSIBLE_RESET and five of 18 CLEAR_RESET rows occupy their
shared retreat range. The [overlap CSV](../outputs/diagnostics/phase3a3_overlap.csv)
also gives intersections of IQRs and p10–p90 intervals, available denominators,
widths and candidate counts inside each intersection. Touching intervals count
as overlap with zero width. An interval intersection need not contain actual
observations from both classes: for example, the CONTINUE/CLEAR recovery IQR
intersection [21.447, 26.651] contains zero CONTINUE points and seven CLEAR points.
The ECDFs and raw observations therefore matter more than interval width alone.

![Retreat observations and ECDF](../outputs/figures/phase3a3_retreat_from_peak.png)

![Time since peak observations and ECDF](../outputs/figures/phase3a3_time_since_peak.png)

![Nonpositive run observations and ECDF](../outputs/figures/phase3a3_nonpositive_run_length.png)

## C. Recovery behavior

| Label | Observed recovery | Not observed: censored | Not applicable: at peak | Other unavailable | New peak afterward: true / false / missing |
| --- | ---: | ---: | ---: | ---: | --- |
| CONTINUE | 32 | 8 | 22 | 0 | 32 / 8 / 22 |
| POSSIBLE_RESET | 11 | 0 | 0 | 0 | 11 / 0 / 0 |
| CLEAR_RESET | 13 | 5 | 0 | 0 | 13 / 5 / 0 |

Among candidates below their reference peak, observed recovery is 32/40 (80%)
for CONTINUE, 11/11 (100%) for POSSIBLE_RESET and 13/18 (72.2%) for CLEAR_RESET.
Recovery occurrence alone is not a clean continuation indicator. `new_peak_afterward`
duplicates the observed-recovery Boolean exactly wherever available in this
sample, so it adds no separation here. Reaching a higher provider peak later
does not prove that the original attacking episode continued.

The following diagnostic windows are illustrative, not selected cutoffs. Each
denominator is the number with an observed recovery time; censored and at-peak
rows are excluded, not assigned infinite or zero recovery times.

| Window | CONTINUE | POSSIBLE_RESET | CLEAR_RESET |
| --- | --- | --- | --- |
| Recovery within 3 s | 7/32 (21.9%) | 0/11 | 2/13 (15.4%) |
| Recovery within 5 s | 15/32 (46.9%) | 0/11 | 2/13 (15.4%) |
| Recovery within 10 s | 23/32 (71.9%) | 2/11 (18.2%) | 2/13 (15.4%) |
| Recovery within 3 events | 13/32 (40.6%) | 0/11 | 2/13 (15.4%) |

Rapid recovery characterizes many CONTINUE observations, but is neither necessary
nor sufficient. Nine recovered CONTINUE observations take more than 30 seconds.
C05_M03 is CLEAR_RESET with recovery in 2.975 seconds; C05_M04, explicitly another
sample of the established reset, has recovery in 0.040 seconds. Both refer to the
same later return, measured from different candidate times. Even the first CLEAR
candidate in that case is a fast-recovery exception.

The [first-CLEAR-per-case sensitivity](../outputs/diagnostics/phase3a3_first_clear_per_case.csv)
contains nine candidates, six with observed recovery; one of those six recovers
within three seconds. It is a dependence check, not one example per independently
verified episode, and omits later resets in cases containing multiple resets.
Missing follow-up durations prevent survival estimation or classification of
censored cases as "no recovery within X seconds." C02_M02 also illustrates the
semantic distinction: its note describes immediate Leverkusen control recovery,
while the numerical flag says no observed **return to the old x peak**.

![Recovery time observations and ECDF](../outputs/figures/phase3a3_observed_recovery_time.png)

## D. Multivariable relationships

No classifier or clustering was fitted. Fixed, interpretable conjunctions expose
tradeoffs. Values 20 x units, 5 seconds, 3 actions and 10 recovery seconds are
illustrative round-number probes, not optimized or proposed production settings.
The [combination table](../outputs/diagnostics/phase3a3_combinations.csv) includes
matched IDs, nonmatches and missing counts. All features in a conjunction must
be available; the denominator changes when a run or recovery value is required.

| Diagnostic conjunction | CONTINUE matched/evaluable | POSSIBLE matched/evaluable | CLEAR matched/evaluable |
| --- | --- | --- | --- |
| Retreat >=20 | 8/62 | 5/11 | 17/18 |
| Retreat >=20 and time since peak >=5 | 6/62 | 2/11 | 15/18 |
| Retreat >=20 and nonpositive run >=3 | 3/30 | 2/11 | 11/18 |
| Retreat >=20 and observed recovery time >=10 | 1/32 | 4/11 | 10/13 |
| Retreat >=20, time since peak >=5, observed recovery time >=10 | 1/32 | 1/11 | 9/13 |

Adding time on the same complete cohort removes two CONTINUE, three POSSIBLE and
two CLEAR matches. Adding recovery appears more selective among observed returns,
but discards 30 CONTINUE and five CLEAR rows with unavailable recovery times;
that change is not evidence of improved full-cohort classification. The triple
conjunction still includes CONTINUE C10_M07, excludes four recovered CLEAR rows,
and cannot evaluate five other CLEAR rows. No displayed combination resolves the
state-reference problem or is sufficient as a boundary rule.

The [univariate sweeps](../outputs/diagnostics/phase3a3_threshold_sweeps.csv) show
the same tradeoffs over retreat {10,20,30,40,60}, time {3,5,10,20}, nonpositive
run {2,3,4}, recovery time {1,3,5,10,30} and recovery events {1,3,5,10}.
Recovery-status combinations are reported separately so that censoring never
becomes an implied long recovery time.

Redundancy is substantial. Pairwise-complete Spearman correlations are 0.987 for
time/events since peak (n=91), 0.966 for recovery time/events (n=56), and 0.864
for negative/nonpositive runs (n=55). Within-label time/event correlations remain
0.926–0.991; recovery correlations remain 0.904–0.998. Run correlation is 1.0
among 16 CLEAR rows with both run counts. These are descriptive rank associations,
not independent significance tests. See [correlations](../outputs/diagnostics/phase3a3_correlations.csv).
The signed negative dx and its magnitude are exactly redundant up to sign.
Confidence, calibration role and threshold weight were not used as predictors:
they are review metadata, not progression evidence.

Strictly LOCKED sensitivity moves POSSIBLE medians to retreat 19.0, time since
peak 5.884 seconds and observed recovery 32.034 seconds; the other classes are
unchanged. It does not remove the range overlaps. Giving each case one within-label
median produces retreat medians 3.8 / 17.1 / 47.9 and recovery medians
4.760 / 27.702 / 24.508 for CONTINUE / POSSIBLE / CLEAR. The broad contrast and
nonmonotonic recovery ordering persist. These checks reduce obvious candidate
multiplicity effects without pretending cases are independent episodes.

![Retreat versus time since peak](../outputs/figures/phase3a3_retreat_vs_time_since_peak.png)

![Retreat versus observed recovery time](../outputs/figures/phase3a3_retreat_vs_observed_recovery_time.png)

## E. Important overlap cases

| Candidate | Label | Retreat | Time since peak (s) | Nonpositive run | Observed recovery (s) |
| --- | --- | ---: | ---: | ---: | ---: |
| C09_M03 | CONTINUE | 88.7 | 8.982 | 3 | censored |
| C11_M05 | CONTINUE | 64.6 | 21.530 | 1 | censored |
| C11_M03 | CONTINUE | 63.5 | 14.572 | 4 | censored |
| C11_M04 | CONTINUE | 63.5 | 16.076 | 5 | censored |
| C10_M07 | CONTINUE | 50.2 | 8.813 | missing | 66.302 |
| C12_M04 | CONTINUE | 46.2 | 8.228 | missing | censored |
| C08_M07 | CLEAR_RESET | 19.7 | 10.685 | 3 | 25.068 |
| C07_M07 | CLEAR_RESET | 23.7 | 3.719 | 4 | 30.162 |
| C07_M08 | CLEAR_RESET | 31.2 | 7.230 | 2 | 26.651 |
| C18_M07 | CLEAR_RESET | 32.8 | 14.500 | 3 | 25.667 |
| C22_M05 | CONTINUE | 20.9 | 4.340 | missing | 3.853 |
| C04_M03 | CONTINUE | 21.3 | 0.705 | 1 | 4.732 |
| C07_M06 | POSSIBLE_RESET | 20.1 | 0 | 1 | 33.881 |
| C04_M04 | POSSIBLE_RESET | 33.5 | 12.543 | 2 | 36.610 |
| C15_M07 | POSSIBLE_RESET, partial lock | 32.3 | 9.012 | 4 | 6.962 |

The first six rows are the largest-retreat CONTINUE examples. C08_M07, C07_M07,
C07_M08 and C18_M07 are the four smallest-retreat CLEAR examples. C22_M05 and
C04_M03 have retreat similar to C08_M07 but shorter time since peak and much
faster return. C07_M06 sits in that same retreat neighborhood as a warning with
slow return. C04_M04 has stronger persistence yet remains warning evidence;
C15_M07 combines a larger retreat and a four-action run with faster recovery.
Thus POSSIBLE_RESET occupies intermediate and mixed-signal regions.

C09_M02 (CLEAR) and C09_M03 (CONTINUE) both have retreat 88.7 and no observed
return; the latter is explicitly "New buildup after reset." C11_M02 (CLEAR,
retreat 62.8) precedes the large-retreat C11 CONTINUE examples. Those labels are
preserved, with no new football interpretation supplied. C25_M07 is CONTINUE
despite four nonpositive actions: retreat is only 8.9 and recovery takes 4.297
seconds. These cases demonstrate why a run count alone is inadequate.

Full context and notes are retained in the
[overlap-case table](../outputs/diagnostics/phase3a3_overlap_cases.csv).
The [similar-retreat pairs](../outputs/diagnostics/phase3a3_similar_retreat_pairs.csv)
list every CONTINUE/CLEAR pair within three x units; this is a descriptive matching
tolerance, not a boundary parameter. C17_M04/M05 remain explicit partial warnings
at retreats 13.8/13.9 and recovery times 15.212/14.083 seconds.

## F. What the data supports

1. **The supplied metrics cannot individually separate reset states.** Retreat
   has the strongest visible shift in central values, but post-reset provider
   references create misleading extremes. This says nothing definitive about
   the separability of correctly recomputed episode-local retreat.
2. **CLEAR generally has greater retreat and persistence**, with median
   nonpositive run 3.5 and time since peak 8.957 seconds. These are tendencies,
   not required minima: C18_M09 has a one-action run, and C05_M03 is CLEAR after
   2.799 seconds with fast recovery.
3. **Recovery timing adds useful context, not a veto.** Many CONTINUE candidates
   recover sooner, but slow CONTINUE and fast CLEAR examples preclude an
   unconditional rapid-recovery escape rule. Absence of rapid recovery is not
   universally necessary for CLEAR.
4. **POSSIBLE_RESET behaves more like intermediate warning evidence than a clean
   third numerical class.** Retreat/run medians are intermediate, yet recovery
   time and event medians exceed CLEAR's. That matches its warning-only role;
   the statistics do not authorize episode cuts for warnings.
5. **Combinations deserve discussion**, particularly retreat with persistence
   and recovery context. The current conjunctions show tradeoffs rather than
   sufficient rules, and highly correlated metrics should not be counted as
   independent reinforcement.

## G. What the data does not support

No production cutoff, optimal parameter, causal recovery effect, generalization
claim or final segmentation policy follows from this sample. It was selected for
review, not randomly sampled; class balance and candidate multiplicity do not
estimate season-wide prevalence. Repeated established-reset examples cannot be
counted as new boundary events. Even a random candidate train/test split would
share cases and excursions, so no such apparent validation is reported.

The 21 explicitly contaminated rows and three local overrides cannot support
numeric thresholds. Workbook-safe post-reset rows also require state-reference
clarification: peak, retreat, elapsed time, event counters, recent-action window,
run counts and future recovery reference must respect hard boundaries and
confirmed resets. Future provider-peak return may cross a boundary. Recovery time
depends on where inside an excursion the candidate was sampled and uses future
information; a retrospective rule would need an explicit bounded lookahead and
boundary-censoring convention. No continuous trajectory or physical ball speed
can be inferred from these event-aligned measurements.

Missing run counts, absent censoring durations and label-dependent recovery
availability prevent treating complete-case comparisons as full-cohort results.
The numerical overlap cannot determine whether a particular defensive intervention
established control. That remains the already reviewed football boundary question,
not something to infer from a clearance label, pressure, Ball Recovery label,
isolated gap, or downstream success.

## H. Candidate ingredients for the next rule-design discussion

1. Apply reviewed football/control boundaries to the full ordered event stream
   first. After opponent-established control, begin at the first event clearly
   re-establishing Leverkusen control. Reset episode state after each hard boundary
   or confirmed reset, and distinguish a reset onset from later samples of it.
2. Recompute episode-local peak and retreat before discussing magnitude settings;
   use meaningful retreat as the strongest current candidate ingredient.
3. Add persistence evidence using time and/or action progression. Evaluate whether
   nonpositive runs add information beyond time; their missingness and correlation
   with negative runs must be respected.
4. Treat rapid recovery as conditional supporting evidence for continuation.
   Discuss a lookahead/censoring convention and the C05 exceptions before any
   recovery escape condition. Do not use provider-wide future return as proof
   of within-episode continuity.
5. Retain POSSIBLE_RESET as a warning state pending reinforcing evidence, never
   as an automatic split. Attach trusted Phase 2C anchors and Phase 2B geometry
   only after football episodes are constructed.

Unresolved methodological questions are how to reconcile workbook-safe post-reset
diagnostics with episode-local state; how to distinguish reset onset from continued
reset-phase samples; how to define recovery reference and follow-up horizon without
crossing boundaries; and how missing runs should be represented after recomputation.
No answer is imposed here, and no additional human labels are requested or invented.

## Reproduction, artifacts and validation

New source files are
[the analysis script](../scripts/segmentation_calibration.py),
[seven focused tests](../tests/test_segmentation_calibration.py), this report,
the preserved workbook and its [input README](../data/calibration/README.md).
No pre-existing repository files, production pipeline, review annotations or
locked methodology documents were modified. The original Downloads workbook
is also unchanged.

Generated artifacts are **22 CSVs, six PNG figures, a JSON manifest and a Markdown
numerical appendix**, all named `phase3a3_*` under the existing diagnostics/figures
directories. The [manifest](../outputs/diagnostics/phase3a3_manifest.json) lists
every CSV/figure and records input/script hashes and dependency versions.
Generated outputs remain ignored by Git under the existing repository convention;
the source workbook, script, tests and report make them reproducible.

Commands run from the repository root:

```powershell
.venv\Scripts\python.exe scripts/segmentation_calibration.py
.venv\Scripts\python.exe -m ruff format scripts/segmentation_calibration.py tests/test_segmentation_calibration.py
.venv\Scripts\python.exe -m ruff check scripts/segmentation_calibration.py tests/test_segmentation_calibration.py
.venv\Scripts\python.exe -m pytest tests/test_segmentation_calibration.py -q
.venv\Scripts\python.exe -m pytest -q
```

Focused checks cover authoritative counts, explicit partial locks, exclusion of
deferred/hard-boundary/contaminated rows, override preservation, nullable Booleans,
censoring and denominators, sample statistics, touching interval overlap, and
rejection of formulas in measurement cells. Figures were visually inspected for
legibility, and the class observations are shown without smoothing.

Validation result: **7 focused tests passed; 348 tests passed in the full default
suite, with 2 network tests deselected; Ruff passed.** The original and copied
workbook hashes match. Artifact checks confirm the report's local file links,
manifest entries and a repeat run's deterministic output hashes.

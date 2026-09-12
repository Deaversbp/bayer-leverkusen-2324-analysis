# Phase 3A-3B — Episode-local diagnostic reconstruction

**11 September 2026. Reviewed calibration reconstruction only; no production
segmenter, threshold selection, classifier, clustering or method-specification change.**

The reconstruction encodes **53 episode intervals across 26 of the 28 reviewed
parents**, with C27/C28 excluded. Of these intervals, 47 have a usable recorded
start; six are explicitly provisional. There are 12 confirmed reset excursions,
each represented once, including three whose exact onset remains unresolved.
The resulting candidate-state descriptive cohort contains **99 rows: 72 CONTINUE,
11 POSSIBLE_RESET and 16 CLEAR_RESET**. These are correlated reviewed samples,
and onset/confirmation/later-phase roles must remain separate in the next analysis.

## A. Reconstruction method

The starting repository commit was `80a9611` (Phase 3A-3 calibration distribution
analysis). The existing report, original workbook, input README, analysis script,
Phase 3A-2 complete timeline/candidate/parent artifacts, HTML pack, and methods
section 42 were inspected. The workbook is unchanged, with SHA-256
`683a232989f9956c788815299b9f9c4577ad91007c219e0a50af5142ec7b4006`.

The authored [boundary ledger](../data/calibration/phase3a3_reviewed_boundaries.csv)
is the reconstruction authority. Each row names the workbook review source,
boundary family, event references, precision, onset/confirmation relationship and
remaining uncertainty. The implementation consumes this ledger; it does not infer
boundaries from numerical diagnostics or mechanically turn labels into cuts.
Original workbook labels, deferred status and approximate overrides are retained.

For context-aligned hard boundaries, an already reviewed controlled spell is
located in the ordered timeline. For example, the C04 hard-boundary candidate is
a Leverkusen Carry at 201, but the reviewed opponent spell is Recovery–Carry–Pass
196–199; the regained Recovery–Carry starts at 200–201. The ledger uses that
context and exposes the alignment. C13 event 353 and C25 event 1264 are explicitly
specified regain events in the review. A missing usable 360 vector never delays
these football starts. No unreviewed opponent-control judgments are added in the
partially locked C15/C17 cases.

Episode IDs are local review identifiers (`C13_E02`, for example), not season-wide
IDs. Provider possession remains a parent/source key. The map uses inclusive
event intervals, ends the preceding episode before a reset-onset action, and
includes that action in the new episode. Reviewed opponent-control intervals,
terminal boundary events and unresolvable intervals remain unassigned context.
Opponent pressure/other contextual events can occur within an episode interval,
but only Leverkusen Pass/Carry events can be marked as attacking action events.

The hierarchy is full ordered events → reviewed boundaries → episode membership
→ episode state. The inherited safe-vector flags control **measurement availability**,
not boundaries. No spatial coordinates are interpolated or forward-filled. The
full 1,960 source rows and 181 sampled candidates are preserved, including all
19 candidates absent from the workbook review record. Those 19 are unrecorded,
not newly labeled CONTINUE. Six explicitly deferred candidates remain deferred.

### Measurement conventions

The script recomputes peak, retreat, latest-equal-peak time/event distance, recent
three-action backward vector, and negative/nonpositive runs within each episode.
Peak and retreat use only the current episode's trusted action start/end vertices.
New episode state never inherits the previous episode's peak, recent-action queue
or run counters. Spatial outputs at unsupported/non-action rows remain missing;
episode IDs and elapsed event time are context fields, not filled ball positions.

Trusted progression is restricted to existing safe Leverkusen Carry vectors and
Pass vectors without a recorded unsuccessful/unknown pass outcome. Failed/unknown
pass endpoints are preserved as recorded vectors but cannot establish a controlled
peak, recovery, or deliberate backward run. This is a new reconstruction diagnostic
filter; it does not change the locked Phase 2 safe-vector extraction.

Only an action's own start-to-end delta contributes to its backward run. A negative
change between successive action locations is exported as `episode_inter_action_dx`;
when failed-action/clearance/loose-ball context intervenes, it is explicitly flagged
as relocation. Such a drawdown is excluded from the ready cohort until restoration
to the reference peak removes the affected drawdown. A failed action breaks current
run counts; unsupported observations supply no vector. Otherwise runs and recent
actions are observations in the trusted-action subsequence, not continuous tracking.

Opening restart vectors do not supply reset evidence. A trusted restart endpoint
can initialize episode state, but its backward vector does not enter the negative
run or recent-negative window. A failed restart supplies no trusted endpoint.
This avoids seeding an abandoned-attack peak from the corner/kickoff origin.
Zero run counts on observed forward actions are explicit zeros in the new schema;
the original provider fields retain their historical blank conventions.

## B. Episode map

The [episode map](../outputs/diagnostics/phase3a3_reviewed_episode_map.csv) includes
parent identity, episode ID, inclusive start/end indices, reasons, boundary source
IDs, reset onset and confirmation, precision, review status, confidence where
recorded, and exclusion/state-validity flags. Numerical certainty is not inferred
from a confidence score. Initial parent intervals do not receive an invented
human confidence rating.

| Quantity | Count |
| --- | ---: |
| Reviewed provider parents | 28 |
| Reconstructed episode intervals | 53 |
| Intervals with usable recorded start | 47 |
| Provisional intervals | 6 |
| Internal opponent-control breaks with a subsequent regain | 15 |
| Consolidated terminal hard-boundary contexts | 13 |
| Confirmed reset excursions / single split relationships | 12 |
| Reset excursions with encoded candidate-resolution onset | 9 |
| Reset excursions with unresolved onset window | 3 |
| Explicit no-episode parent exclusions | 2 |
| Deferred tails where known membership is truncated | 3 |

One of the 15 opponent-control breaks is in partially locked C17; both its episode
intervals remain provisional. Six provisional intervals comprise the three
confirmation-start proxies for unresolved resets, one C15 interval and two C17
intervals. The 53 total must not be reported as 53 fully resolved football episodes.
Opening restart contexts are episode starts, not additional reset splits. Multiple
hard-boundary observations for one stoppage are consolidated, so the 46 workbook
Hard_Boundaries observations are not a count of 46 cuts.

| Cases | Episode intervals per case |
| --- | --- |
| C01, C02, C03 | 1, 1, 1 |
| C04, C05, C06 | 3, 2, 2 |
| C07, C08, C09, C10 | 2, 2, 2, 2 |
| C11, C12 | 5, 4 |
| C13, C14, C15 | 2, 2, 1 provisional |
| C16, C17, C18 | 5, 2 provisional, 4 |
| C19, C20, C21, C22, C23, C24, C25, C26 | 2, 1, 1, 1, 1, 1, 2, 1 |
| C27, C28 | 0, 0 |

The [event membership table](../outputs/diagnostics/phase3a3_episode_event_membership.csv)
contains 1,023 events in intervals with usable starts, 528 in provisional intervals,
404 in boundary/unresolved context, and five in the two excluded parents. These
are observation/membership counts, not numbers of independent attacks. The
[episode summary](../outputs/diagnostics/phase3a3_reviewed_episode_summary.csv)
provides event/action counts and local peak/retreat summaries per interval.

## C. Provider versus episode-local differences

The [comparison table](../outputs/diagnostics/phase3a3_provider_vs_episode_diagnostics.csv)
contains 11 diagnostic comparisons for each of the 181 candidates. **63 candidates
change at least one mutually available diagnostic value** beyond numerical tolerance
(`atol=1e-9`, zero relative tolerance). **144 candidates change a value or availability**.
The latter includes deliberate changes from unavailable measurements to available
ones and from old run blanks to explicit observed zeros. This tolerance is only
floating-point comparison precision, not a segmentation threshold.

| Candidate | Provider retreat | New episode retreat | New peak | Interpretation |
| --- | ---: | ---: | ---: | --- |
| C09_M03 | 88.7 | 40.4 | 71.7 | Old corner-origin peak removed |
| C10_M07 | 50.2 | 48.0 | 85.1 | New episode starts at warning onset; its own recycling still contributes |
| C12_M04 | 46.2 | 21.0 | 94.8 | New reset episode uses its Recovery Pass start |
| C13_M06 | 33.0 | 17.7 | 74.3 | New episode begins at reviewed regain 353 |
| C13_M07 | 33.2 | 17.9 | 74.3 | No pre-turnover peak inheritance |
| C14_M09 | 41.2 | 21.1 | 90.2 | Reproduces approximate human override 21 |
| C16_M06 | 35.6 | 14.1 | 64.0 | Reproduces approximate human override 14 |
| C16_M08 | 43.0 | 5.4 provisional | 47.9 provisional | Exact onset unresolved; not ready |
| C25_M09 | 18.4 | 0.0 | 83.0 | First usable observation within episode starting at 1264 |
| C20_M01 | 16.9 | unavailable | unavailable | Failed current pass; recorded forward dx retained |

Nonzero retreat after a reviewed reset is not automatically contamination. Under
the newly authorized onset convention, the new episode includes the reset action
and subsequent reorganization. C09_M03 therefore retains 40.4 from the new
episode's own 71.7 start, rather than inheriting 120. C10_M07 similarly retains
retreat inside its newly defined interval. Resetting again at every later CONTINUE
or "rebuilt phase" sample would add unsupported extra cuts. The report does not
force these values to zero to improve class separation.

C16_M08 needs a different interpretation. A separately named
`confirmation_unsplit_reference_retreat_from_peak` is **32.8**, matching the
approximate 33 override when the post-regain reference is carried through the
review window. It is a counterfactual audit bridge assuming no reset until
confirmation. Its 5.4 confirmation-start proxy is not asserted to be a clean
episode-local replacement for 33. Neither value is admitted for that candidate.

## D. Reset onset versus confirmation

| Excursion | Encoded onset | Confirmation | Last sampled reset event | Status |
| --- | ---: | ---: | ---: | --- |
| C04_R01 | 177 | 189 | 192 | Explicit warning begins; later confirmation |
| C05_R01 | 3612 | 3614 | 3616 | Reviewed warning/confirmation sequence |
| C07_R01 | 689 | 694 | 699 | Reviewed warning/confirmation sequence |
| C08_R01 | 2766 | 2768 | 2772 | Reviewed warning/confirmation sequence |
| C09_R01 | 576 | 576 | 576 | Reviewed recycle action; no earlier warning asserted |
| C10_R01 | 2416 | 2420 | 2422 | Reviewed warning transition; one reset |
| C11_R01 | 783 | 783 | 783 | Reviewed recycle Carry |
| C11_R02 | unresolved within 832–853 | 853 | 853 | Last reviewed CONTINUE is 831 |
| C12_R01 | 2438 | 2438 | 2438 | Reviewed Recovery Pass; Shot warning is not backward onset |
| C12_R02 | unresolved within 2451–2481 | 2481 | 2483 | Last reviewed CONTINUE is 2450 |
| C16_R01 | unresolved within 545–574 | 574 | 574 | Earlier warning cancelled by renewed progression at 544 |
| C18_R01 | 1296 | 1304 | 1309 | Warnings and repeated clear samples explicitly linked |

For the six retrospective warning placements, the encoded event is the reviewed
candidate-resolution onset supported by the warning/confirmation sequence and
same-excursion notes. It is not a claim about an earlier unsampled physical onset.
These are explicit applications of the user's new convention, not pre-existing
exact-boundary annotations hidden in the workbook. For the three same-action
onset/confirmation rows, no earlier warning is invented.

The unknown windows are bounded by the last recorded CONTINUE and the confirmation;
their lower limits are bounds, not asserted onset events. Events before confirmation
inside these windows remain unassigned. A provisional interval starts at confirmation
for inspection, but it does not claim that the true episode started exactly there.
No threshold or backward-action run was used to pick an onset within these windows.

The [reset excursion table](../outputs/diagnostics/phase3a3_reset_excursion_diagnostics.csv)
separates three reference systems: `onset_pre_split_*` evaluates the boundary action
against the preceding episode; `confirmation_episode_*` uses the reconstructed new
episode; `confirmation_unsplit_reference_*` is a counterfactual audit bridge and
is never a final membership or calibration field. Candidate roles identify onset,
confirmation, later samples and warnings. Human labels are not replaced by these roles.

For example, C04 onset retreat is 33.5 against the preceding episode; its
confirmation retreat is 22.3 against the new episode, while the counterfactual
pre-reset reference would give 40.2. These are different questions, not rival
estimates of the same peak. C16_M05/M06, C22_M05 and C25_M06/M07 retain cancelled
or continuation-warning status and do not create cuts. C14's remaining warning
is unconfirmed in the available record, not declared cancelled by missing evidence.

## E. Recovery reconstruction

Recovery is the first **later** trusted action vertex at or above the candidate's
current episode peak; equality counts. A higher vertex counts as recovery and
also supports `episode_new_peak_afterward`. The latter is computed separately:
an equal return need not establish a new peak. If no later trusted vertex exists,
new-peak status is unavailable, rather than proof that a new peak never occurred.

Candidate-time recovery starts at the candidate timestamp; event distance counts
all intervening ordered episode events. A reset-onset snapshot is evaluated against
the preceding episode reference and censored at the final split. It cannot claim
a return in the next episode as recovery of the abandoned episode. The excursion
table also records elapsed time from onset to confirmation, which is not recovery
time. Both action endpoints use the source action-start timestamp: no physical
arrival time, continuous trajectory or ball speed is inferred.

At-peak observations are `not_applicable_at_peak`; unsupported or failed current
measurements are unavailable. Below-peak candidates without a later observed
return are explicitly censored, with null recovery time/event count, a censor event
and observed follow-up duration. No zero, infinity or arbitrary large number replaces
a missing recovery time. Follow-up ends at the final episode interval, including
hard/terminal boundaries or conservative truncation before an unresolved/deferred
window. `episode_end_reason` distinguishes these reasons in the candidate table.
An uncertainty truncation is an observation limit, not a newly invented football cut.

| Candidate | Old recovery time (s) | New recovery time/status |
| --- | ---: | --- |
| C04_M04 | 36.610 | 6.067 to its new local peak |
| C12_M03 | unavailable | 5.816 to its new local peak |
| C13_M06 | 20.859 | 10.126 after the reviewed regain |
| C16_M06 | 92.041 | censored before unresolved later reset window |
| C18_M05 | 30.187 | 28.985 to its new local peak |
| C25_M09 | 6.516 | at peak; recovery not applicable |

The [recovery summary](../outputs/diagnostics/phase3a3_episode_local_recovery_summary.csv)
uses only available observed times in each ready class's conditional mean:

| Label | Ready candidates | Observed times | Missing times | Conditional mean (s) | Censored | At peak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CONTINUE | 72 | 31 | 41 | 5.775 | 16 | 25 |
| POSSIBLE_RESET | 11 | 6 | 5 | 19.174 | 5 | 0 |
| CLEAR_RESET | 16 | 11 | 5 | 16.054 | 5 | 0 |

These are verification summaries, not a new overlap analysis. The workbook's old
cached recovery means and all archived inputs remain unchanged.

## F. Edge-case validation

| Case | Result against recorded review |
| --- | --- |
| C09 | Earlier corner-origin peak removed; M03 uses its own reset episode's peak. Deferred tail from 602 remains unresolved. |
| C10 | One split at 2416, confirmed 2420; M06 does not split again. M07's remaining retreat is within the new episode. Membership after 2450 is not asserted through deferred review. |
| C12 | Shot/GK/clearance warning is not automatically a hard break. First recycle at 2438 starts the reset episode; later reset onset remains unresolved. Opponent-control regain 2544 starts fresh state. |
| C13 | Explicit regain 353 starts new episode; M06/M07 retreat becomes 17.7/17.9. |
| C14 | Regain starts at 2485 before usable geometry; M09's 21.1 agrees with approximate override 21. Warning alone does not split. |
| C16 | Regains at 536, 613 and 651 reset state. M06's 14.1 agrees with override 14. Later M08 onset unresolved; counterfactual 32.8 agrees with approximate 33 but is not admitted as final state. |
| C18 | One reset excursion, then separate reviewed regains at 1372 and 1427. M11/M12 may still have retreat zero, but their histories and recovery searches are now separate. |
| C25 | Warning-like CONTINUE samples do not split. Explicit regain 1264 starts state despite missing vector; M09 becomes zero retreat from new observed peak 83. |
| C20 | Current recorded dx is forward, not backward. Failed endpoints do not become controlled peaks; M01's numerical reset measurement is unavailable, not a fake 16.9 backward recycle. |
| C22 | M05 remains CONTINUE with cancelled-warning role; recovery 3.853 seconds remains inside the same episode. |
| C24 | Opening backward kickoff is context only; no negative-run evidence or reset. M02 has an unknown pass outcome and is excluded from trusted progression rather than treated as a completed pass. |
| C27 | Four administrative events preserved; no episode. |
| C28 | Single insufficient goalkeeper-context event preserved; no episode. |

These checks support the implemented measurement safeguards within the recorded
review scope. They do not resolve the three unknown reset onsets or the unrecorded
parts of C15/C17. No attacking-success variable was used to judge consistency.

## G. New calibration-ready cohort

The [candidate table](../outputs/diagnostics/phase3a3_episode_local_candidate_diagnostics.csv)
retains original candidate IDs and labels, renamed provider diagnostics, original
workbook safety flags/overrides, new episode metrics, episode membership, candidate
role, warning resolution, new suitability and explicit exclusion reasons.

Readiness requires an available recorded review label, usable episode start,
trusted current progression observation, no opening-restart evidence, and no
contest-relocation contamination of the current drawdown. It is recomputed from
local validity, not copied from `threshold_safe`. Thus C14_M09 is newly eligible,
while old-safe C20_M01 is no longer eligible. Partial-label confirmation alone
does not repair incomplete case structure: C15_M07 and C17_M04/M05 remain
preserved but ineligible here.

| Label | Ready candidate states | Role breakdown |
| --- | ---: | --- |
| CONTINUE | 72 | 69 normal samples; 3 continuation/cancelled-warning samples |
| POSSIBLE_RESET | 11 | 6 retrospective onset samples; 2 later warning-phase samples; 3 remaining/cancelled warnings |
| CLEAR_RESET | 16 | 3 same-action onset/confirmation; 6 later confirmations; 7 later reset-phase samples |

**Ready means suitable for descriptive comparisons of these recorded candidate
states, stratified by role and observation scope.** It does not mean 99 reset-onset
training examples. In particular, a retrospectively placed split changes the peak
reference at subsequent confirmation, and a POSSIBLE label at onset remains the
original label even when that excursion was later confirmed. Flattening these
different roles into a new threshold optimization would recreate a supervision
mismatch. All candidate observations remain statistically dependent within cases.

Seven of the nine encoded onset events also have an available pre-split observed
peak. C09_R01 and C11_R01 follow failed opening corners with no trusted prior
progression vertex; their pre-split reference metrics remain unavailable rather
than borrowing the corner-origin peak. Their current-episode action measurements
are still available. The three unresolved onsets have no onset snapshot.

## H. Remaining ambiguities

Three onset windows remain unresolved: C11_R02, C12_R02 and C16_R01. The workbook
contains confirmation labels but no exact onset placement within those windows.
The candidate-resolution onsets encoded elsewhere do not establish the earliest
unsampled onset; this precision distinction must survive later interpretation.

C15/C17 are partial cases. Their absent labels and unrecorded later football
structure cannot be filled by automatically discovering new controlled spells.
The C17 controlled spell explicitly described before M09 is encoded, while its
surrounding intervals stay provisional. Deferred tails in C04, C09 and C10 also
prevent complete exact membership; C10's post-terminal provider tail is preserved
as context without invented later episodes.

Unknown/missing vectors restrict the measurements to observed, trusted action
subsequences, not complete ball paths. Context-aligned hard boundaries carry their
original ranges or approximate timing in the ledger; a reviewed regain can be
usable even when the preceding loss interval is approximate. Missing recovery is
an observation/censoring statement, not a football failure label.

## I. Next-step recommendation

Proceed with a **restricted, role-aware episode-local distribution/overlap pass**
on the 99 ready candidate states, retaining case dependence and censoring. Compare
onset transition snapshots separately from confirmation and later-phase states.
The project is **not ready for a universal reset-onset threshold calibration or
production method lock**. Exact remaining onsets and the intended onset-versus-state
calibration target must be resolved first; no thresholds are selected here.

## Reproduction, files and checks

New source artifacts are the boundary ledger, three review-source CSV snapshots,
source provenance JSON, [reconstruction script](../scripts/episode_local_reconstruction.py),
[focused tests](../tests/test_episode_local_reconstruction.py), and this report.
The only modified pre-existing file is the
[calibration README](../data/calibration/README.md), documenting the new command,
inputs and validity scope. The production pipeline, locked methods, original
workbook and Phase 3A-2/3A-3 outputs were not modified.

Seven generated CSVs and the
[episode-local manifest](../outputs/diagnostics/phase3a3_episode_local_manifest.json)
are written under the existing ignored diagnostics directory. The manifest records
source hashes, script and workbook-reader hashes, package/runtime versions and
each generated CSV hash. The source-provenance JSON records the original review
artifact hashes. The input snapshots allow reconstruction offline without those
ignored outputs or another data download.

Commands, run from the repository root:

```powershell
.venv\Scripts\python.exe scripts/episode_local_reconstruction.py
.venv\Scripts\python.exe -m ruff format scripts/episode_local_reconstruction.py tests/test_episode_local_reconstruction.py
.venv\Scripts\python.exe -m ruff check scripts/episode_local_reconstruction.py tests/test_episode_local_reconstruction.py
.venv\Scripts\python.exe -m pytest tests/test_episode_local_reconstruction.py -q
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts/episode_local_reconstruction.py --output-dir outputs/temp/phase3a3b_repeat
```

Focused tests check hard-boundary state resets, regain before spatial availability,
one split per confirmed excursion, cancellation, restart protection, failed-endpoint
and relocation safeguards, no-episode parents, opponent context, boundary-censored
recovery, equal/higher recovery, uncertain-onset exclusion, override comparisons,
new validity decisions, conditional recovery denominators, full row preservation,
workbook immutability and boundary-map independence from numerical inputs.

Final validation: **13 focused tests passed; the full suite passed 361 tests,
with two network tests deselected (46.54 seconds); Ruff and `git diff --check`
passed.** Repeat execution produced byte-identical files for all seven CSVs and
the manifest. Hash checks confirmed that the original workbook, Phase 3A-2
artifacts, prior calibration report and locked methods were unchanged. All 127
matrix labels, lock statuses and recorded confidences reconcile with the new
candidate table, and all 12 local report links resolve.

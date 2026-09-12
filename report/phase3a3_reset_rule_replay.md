# Phase 3A-3: Candidate Rule v0.1 and one v0.2 replay

Bounded C01–C28 replay. **NOT READY — ONE SPECIFIC MATERIAL FAILURE REMAINS.**
The blocking failure is false confirmation of reviewed continuation, particularly C16's
cancelled warning. The one re-arm revision removes four extra splits but does not fix that failure.
No production segmentation code, human labels, thresholds or earlier artifacts were changed.

## A. Rule replayed

Candidate Rule **v0.1**, with the supplied numerical settings unchanged:

1. **ACTIVE / ARMED:** arm only after trusted Leverkusen forward progression has established
   a valid episode-local attacking peak. Opening restart backward vectors cannot arm the detector.
   Failed/unknown pass endpoints and contest/relocation jumps cannot establish trusted progression.
2. **ACTIVE → WARNING:** on a trusted deliberate Leverkusen action, warn when retreat from the
   stored episode peak **>=10.0**. Store onset event/time/retreat, the pre-warning peak and its
   timestamp, and the current warning low. Do not split yet; freeze the warning reference.
3. **Magnitude evidence:** frozen-reference retreat **>=20.0 OR** largest relevant deliberate
   backward-action magnitude **>=10.0**.
4. **Persistence evidence:** time since the stored peak **>=5.0 seconds OR** current trusted
   nonpositive run **>=2 actions**. These are two evidence families, not four independent votes.
5. **WARNING → CONFIRMED RESET:** magnitude **AND** persistence, provided cancellation or a hard
   boundary has not superseded the warning. Create one excursion and one final split at its onset.
6. **WARNING → CANCEL:** before confirmation, trusted forward progression reducing frozen-reference
   retreat to **<10.0** cancels. Return to ACTIVE in the same episode; exact peak recovery is unnecessary.
7. **CONFIRMED RESET → REBUILD:** start the new episode retrospectively at the stored onset, clear
   old peak/run state and disarm. Backward/circulating reset-phase samples alone cannot create another cut.
8. **REBUILD → ACTIVE:** require a trusted forward action establishing a new episode-local peak
   after reset onset. Hard football boundaries always take precedence over all soft transitions.

Execution conventions resolve implementation details without a parameter search. Initial arming uses
the first trusted forward action with a valid local peak; only REBUILD requires exceeding the local peak.
A successful forward restart may arm from its endpoint, while all restart vectors are excluded from
reset evidence. Restart backward endpoints seed context without arming. The existing diagnostic's
three-trusted-action window defines “largest relevant backward action”; unsupported observations do not
supply vectors, failed passes break the nonpositive run, and contest-affected drawdown stays ineligible
until peak restoration. The latest equal-peak vertex supplies peak time, so onset can have zero age.
All four settings are fixed, with inclusive evidence comparisons and strict cancellation comparison.

Each eligible action updates state, checks cancellation first, then confirmation. Confirmation can
occur on the warning action itself if both families already hold; it is not artificially delayed.
On confirmation, only measurement history from the predicted onset through confirmation is rebuilt;
soft transitions are not replayed inside that history. Re-arming is evaluated on subsequent actions.
The old peak never becomes the new episode's measurement reference.

Inputs are the existing 1,960-row reviewed event snapshot, 28-parent source, human boundary ledger,
candidate diagnostics and episode map. Soft predictions never consume reviewed soft splits, labels or
episode membership. Hard boundaries/exclusions are supplied constraints: zero hard mismatches verifies
preservation, **not independent hard-boundary detection accuracy**. The 26 eligible parent starts and
15 reviewed regains are preserved, including starts lacking a spatial vector. Opening restarts are
start context rather than extra cuts; C27/C28 have no predicted episodes. No data were downloaded.

## B. Overall replay

| metric | v0.1 | v0.2 |
| --- | --- | --- |
| reviewed_scored_resets | 9 | 9 |
| matched_resets | 3 | 3 |
| early_splits | 1 | 1 |
| late_splits | 1 | 1 |
| missed_resets | 4 | 4 |
| extra_final_splits | 17 | 13 |
| warning_count | 43 | 38 |
| predicted_confirmation_count | 33 | 28 |
| predicted_cancellation_count | 10 | 10 |
| warning_only_false_positives | 0 | 0 |
| correctly_cancelled_warnings | 9 | 9 |
| hard_boundary_mismatches | 0 | 0 |
| unscored_warnings | 11 | 10 |
| unscored_ambiguous_case | 9 | 9 |

The nine scored reset targets are the encoded onsets, including C09/C11 even though their pre-split
quantitative calibration references were unavailable. The three unknown onsets are never imputed.
Exact onset matches are counted separately from early/late splits. All confirmation timings remain
visible below; an exact split match does not assert an exact human-confirmation-time match.

Comparison is constrained to the same reviewed hard-control span and the same reviewed excursion:
the interval after its preceding reviewed ordinary CONTINUE through its last reset-phase sample.
Within that alignment window, nearest-onset pairing is one-to-one; there is no tolerance search.
A predicted cut after the last reset-phase sample is an extra cut, not a late match to an old reset.
No alignment limit becomes a newly inferred human onset. The ledger supplies continuation intervals;
absence of another cut inside a fully reviewed interval is the extra-split reference.

Unresolved onset windows and ensuing provisional membership, deferred tails, C14's unresolved warning
and all partial C15/C17 structure are **UNSCORED_AMBIGUOUS**. Predictions run through those intervals,
but any warning-to-resolution interval overlapping them is excluded from error counts. These masks
affect scoring only. The nine affected cases are C04, C09, C10, C11, C12, C14, C15, C16 and C17.
The partial C17 hard boundary is also unscored, while still preserved. The other 27 consolidated hard
boundaries and both no-episode exclusions match in both versions.

Warning counts include every firing, including immediate confirmations and unscored warnings.
The nine correct cancellations agree with reviewed continuation; only C22 overlaps an explicitly
reviewed cancelled-warning sample. They are not nine independently reviewed cancellation timestamps.
C18 additionally cancels the warning at its reviewed onset and later confirms a displaced onset;
that cancellation is not counted as correct. No scored warning merely expires or is superseded without
confirmation/cancellation, hence zero FALSE_WARNING_ONLY. Cancelled warnings do not add episode splits.
The CSV detail rows distinguish reviewed-target results from predicted-warning results to avoid
double-counting matches or C18's warning failure.

## C. Case-level mismatches

Both versions have the same nine reviewed-reset alignment results:

| case_id | classification | reviewed_onset | predicted_onset | reviewed_confirmation | predicted_confirmation |
| --- | --- | --- | --- | --- | --- |
| C04 | EARLY_SPLIT | 177 | 176 | 189 | 176 |
| C05 | MATCH | 3612 | 3612 | 3614 | 3614 |
| C07 | MATCH | 689 | 689 | 694 | 691 |
| C08 | MATCH | 2766 | 2766 | 2768 | 2770 |
| C09 | MISSED_RESET | 576 | — | 576 | — |
| C10 | MISSED_RESET | 2416 | — | 2420 | — |
| C11 | MISSED_RESET | 783 | — | 783 | — |
| C12 | MISSED_RESET | 2438 | — | 2438 | — |
| C18 | LATE_SPLIT | 1296 | 1300 | 1304 | 1304 |

- **C04:** magnitude and peak age already satisfy both families at 176, one event before reviewed
  onset 177. v0.1 re-arms at 180 below the abandoned peak and splits again at 185, before human
  confirmation 189. v0.2 removes the second cut; the early onset remains.
- **C09/C11:** failed corners supply no trusted forward arming action. Deep backward recycle
  actions 576/783 occur while disarmed, so both reviewed onsets are missed. Later forward actions
  579/791 arm against already accumulated local retreat and generate extra cuts. No failed endpoint
  or inferred onset is substituted to rescue those targets.
- **C10:** the opening throw-in lacks a safe vector and the early trusted actions all go backward.
  The detector remains disarmed at reviewed onset 2416. Forward action 2423 arms and immediately
  splits the reviewed rebuilt phase; v0.1 adds a further cut at 2442. v0.2 removes only the latter.
- **C12:** the backward opening corner does not arm. The subsequent clearance/recovery produces
  relocation-affected drawdown at 2438, which cannot supply reset evidence under the inherited
  safeguards. The known onset is missed; the later unknown onset remains unscored.
- **C18:** warning 1296 has retreat 10.2, backward magnitude 3.9 and peak age 9.980s. Persistence
  alone cannot confirm. Forward event 1297 reduces retreat to 8.5 and cancels; event 1300 starts
  a new warning, confirmed at 1304. The split is therefore late even though confirmation matches.
- **C07/C08:** split onsets match, but algorithm confirmation is 691 versus reviewed 694 and
  2770 versus reviewed 2768, respectively. C07 meets the run alternative earlier; C08 needs later
  retreat magnitude. These timing differences are visible rather than counted as extra cuts.

Every scored extra split is listed below. Each row meets the unchanged magnitude/persistence gate
inside an interval the review retains as one episode. Values are at algorithm confirmation, not
substituted onset features; versions absent from a row did not generate that extra split.

| case | split | versions | evidence |
| --- | --- | --- | --- |
| C04 | 185 | v0.1 | At 185: retreat 11.8, recent backward 10.6; peak age 0.775s, run 2. |
| C06 | 453 | v0.1, v0.2 | At 463: retreat 35.9, recent backward 0.0; peak age 11.089s, run 1. |
| C09 | 579 | v0.1, v0.2 | At 581: retreat 24.9, recent backward -0.0; peak age 6.057s, run 0. |
| C09 | 585 | v0.1 | At 587: retreat 10.8, recent backward 10.8; peak age 1.610s, run 2. |
| C09 | 600 | v0.1 | At 600: retreat 10.5, recent backward 10.2; peak age 0.960s, run 3. |
| C10 | 2423 | v0.1, v0.2 | At 2423: retreat 50.2, recent backward 11.3; peak age 8.813s, run 0. |
| C10 | 2442 | v0.1 | At 2442: retreat 17.7, recent backward 15.9; peak age 1.424s, run 2. |
| C11 | 791 | v0.1, v0.2 | At 791: retreat 21.1, recent backward 1.9; peak age 10.482s, run 0. |
| C13 | 309 | v0.1, v0.2 | At 309: retreat 16.4, recent backward 15.3; peak age 0.080s, run 2. |
| C14 | 2447 | v0.1, v0.2 | At 2447: retreat 15.1, recent backward 12.7; peak age 0.746s, run 2. |
| C14 | 2461 | v0.1, v0.2 | At 2463: retreat 19.1, recent backward 17.5; peak age 1.367s, run 2. |
| C16 | 541 | v0.1, v0.2 | At 541: retreat 12.5, recent backward 10.3; peak age 2.000s, run 2. |
| C16 | 624 | v0.1, v0.2 | At 626: retreat 10.9, recent backward 10.2; peak age 0.720s, run 2. |
| C18 | 1346 | v0.1, v0.2 | At 1348: retreat 16.3, recent backward 15.1; peak age 0.844s, run 2. |
| C18 | 1389 | v0.1, v0.2 | At 1389: retreat 19.7, recent backward 15.9; peak age 3.410s, run 2. |
| C18 | 1439 | v0.1, v0.2 | At 1439: retreat 14.1, recent backward 11.4; peak age 5.795s, run 0. |
| C18 | 1462 | v0.1, v0.2 | At 1462: retreat 23.1, recent backward 13.7; peak age 2.174s, run 8. |

C06's retained post-regain buildup is confirmed from retreat plus elapsed time. C13 and C14 show
ordinary recycling satisfying the backward-magnitude/run alternatives. C16's first extra is the
explicitly cancelled warning, while its 624 excursion is also inside reviewed continuation. C18's
four extras include forward arming within a post-regain recycle at 1439 and later backward runs;
the existence of two numerical families does not establish attack abandonment in these cases.

Final v0.2 case counts (all zero-error cases retained):

| case | match | early | late | miss | extra | warnings | unscored warnings |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C02 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C03 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C04 | 0 | 1 | 0 | 0 | 0 | 2 | 0 |
| C05 | 1 | 0 | 0 | 0 | 0 | 2 | 0 |
| C06 | 0 | 0 | 0 | 0 | 1 | 1 | 0 |
| C07 | 1 | 0 | 0 | 0 | 0 | 3 | 0 |
| C08 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| C09 | 0 | 0 | 0 | 1 | 1 | 2 | 1 |
| C10 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| C11 | 0 | 0 | 0 | 1 | 1 | 3 | 2 |
| C12 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| C13 | 0 | 0 | 0 | 0 | 1 | 3 | 0 |
| C14 | 0 | 0 | 0 | 0 | 2 | 4 | 1 |
| C15 | 0 | 0 | 0 | 0 | 0 | 3 | 3 |
| C16 | 0 | 0 | 0 | 0 | 2 | 4 | 1 |
| C17 | 0 | 0 | 0 | 0 | 0 | 2 | 2 |
| C18 | 0 | 0 | 1 | 0 | 4 | 6 | 0 |
| C19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C22 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| C23 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C24 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C25 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C26 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C27 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C28 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## D. Named stress tests

| Case | Observed behavior |
| --- | --- |
| C05 | Forward free-kick endpoint arms; warning 3612 at zero peak age; confirmation 3614; exact onset match in both versions. |
| C18 | Modest backward magnitude cannot confirm 1296; cancellation 1297 shifts final onset to 1300; four other scored extra cuts remain. |
| C16 | Warning 541 immediately confirms: retreat 12.5, backward 10.3, run 2. The reviewed cancellation is lost in both versions. At renewed progression 544 retreat is still 13.8 from peak 64.0, so even a delayed decision would not meet the supplied <10 cancellation condition then. The later unknown reset stays unscored. |
| C25 | Recorded warning samples have retreat 7.9/8.9, below 10. No warning or split occurs despite the four-action run; no cancellation is invented. |
| C04 | Local forward progression reaches a new local peak below 97.2 before human confirmation. v0.1 creates an extra cut at 185; v0.2 suppresses it. |
| C09/C10 | Reviewed resets missed while disarmed; first forward rebound creates extra 579/2423. v0.2 removes later repeated cuts 585/600 and 2442, but cannot fix the first extra. |
| C20 | Zero warnings/splits; failed endpoints and relocation cannot establish reset evidence. |
| C22 | Warning 425 cancels at 427 with retreat 8.2, before exact peak restoration at 428. Zero split in both versions. |
| C24 | Opening backward kickoff supplies endpoint context only; zero warnings/splits. |
| C27/C28 | Explicit no-episode exclusions preserved; zero warnings and zero episodes. |

## E. One justified revision: v0.2

v0.1 has a repeated, generalizable re-entry failure: C04 re-arms below its abandoned 97.2 peak and
cuts the same reviewed excursion again; C09/C10 likewise generate repeated cuts in rebuilt phases.
This also violates the requirement to avoid repeated splits for an established reset excursion.

**The only change:** while REBUILD, the otherwise eligible forward action must additionally reach
the stored pre-warning peak before re-arming. This uses the already stored reference as a separate
re-arm guard, never as a new-episode peak or run value. Hard boundaries clear the guard. Initial arming,
warning, magnitude, persistence, cancellation, retrospective placement and all numeric settings are
unchanged. Cancellation still does not require full peak recovery. No new feature or case exception
is introduced. v0.2 was evaluated as one fixed revision, without threshold or alternative-rule search.

v0.2 removes exactly four scored extras: C04:185, C09:585/600 and C10:2442. One unscored C11 cut
also disappears. It creates no new scored mismatch; all remaining target timings and cancellations
are unchanged. Its stricter re-arm condition may suppress legitimate deeper attacks that never regain
the old peak; this bounded replay does not establish season-wide recall. No v0.3 is proposed or run.

## F. Lock readiness

**NOT READY — ONE SPECIFIC MATERIAL FAILURE REMAINS.**

The specific blocking failure is **confirmation of reviewed continuation as attack abandonment**.
C16:541 is a direct reviewed counterexample: the 10.3 backward action and two-action run immediately
confirm a warning the human review cancels. The same gate produces extra splits in C06, C13, C14 and
C18; it is not an isolated onset-timing discrepancy. v0.2 still has **13 scored extra final splits**.
This one blocker is sufficient to reject lock. The four missed known resets, early C04 onset and late
C18 onset are additional documented mismatches, not accepted limitations hidden by that decision label.

Stop here: the permitted revision has been used. Neither version is locked or promoted to production,
and this report does not open another analysis phase or propose another rule.

Reproduce with `.venv\Scripts\python.exe scripts/reset_rule_replay.py`.
Six focused executable transition/safeguard checks run before output, together with source completeness,
one-split-per-warning, retrospective-onset, no-episode, count-reconciliation and input-immutability checks.
Outputs are this report and exactly two CSVs: `phase3a3_reset_rule_replay_cases.csv` and
`phase3a3_reset_rule_replay_details.csv` under `outputs/diagnostics/`. No figure is necessary.
The case CSV compares hard/reset boundaries, warnings, cancellations, confirmations and final starts;
the detail CSV contains reference results and one row per predicted warning with its frozen evidence.

Input SHA-256 values:

- `data/calibration/phase3a3_reviewed_event_source.csv`: `1454fedf16559db295cd26a974a88ae5564971d4a6823670d517ecac1951eff7`
- `data/calibration/phase3a3_reviewed_parent_source.csv`: `a34cfdd6ea59ca3031aebd6c9b08d3ff02a8c30e18fbefdf154d465b3ec1c90e`
- `data/calibration/phase3a3_reviewed_boundaries.csv`: `8fa9c84899d8e7240432e12b589f360d8e289e20d0f3780faea4d6fb0853e1e4`
- `outputs/diagnostics/phase3a3_episode_local_candidate_diagnostics.csv`: `e6463c000a58bee185aa54cc8368b71202a834715ff882d66708c54556756246`
- `outputs/diagnostics/phase3a3_reviewed_episode_map.csv`: `c57b046c9aaf0451a5f95064cf0ee15b6a736899cbcf3dfe40d5d9b0b6acb8f5`

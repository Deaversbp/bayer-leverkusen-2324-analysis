# Phase 3A: attacking control spell segmentation

**PHASE 3A — LOCKED / COMPLETE**

## A. Final analytical unit

`attacking_control_spell_id` identifies a contiguous interval of retained or re-established Leverkusen
attacking control without a qualifying hard football boundary. Provider possession remains the source
parent and can contain multiple spells. A control spell is a data container, not a tactical sequence.
IDs are `<match_id>-p<period>-pp<provider_possession_id>-s<spell_number>`, numbered from one per parent.
Soft retreat, recycling and reorganization never increment that number.

## B. Hard-boundary implementation

The implementation reuses the canonical complete-match event inventory and its order/parent checks,
then selects possession-team 904. No 360 frames, spatial anchors, geometry or attacking outcomes enter
the detector. Contextual fields come directly from ordinary provider event records at the pinned SHA.

An opponent completed pass demonstrates controlled distribution. Otherwise a recovery, won interception,
carry, successful receipt or dribble requires corroborating control evidence, including a carry/pass/dribble.
The boundary starts at the first corroborated cue, not at the later evidence event. A recovery alone,
pressure, duel or clearance is insufficient. The symmetric control test locates Leverkusen regains,
including a recovery before its corroborating carry, without requiring a usable spatial vector.

Literal out/pass-Out, offside, non-advantage foul and explicit stoppage end an active spell.
A Leverkusen shot ends the spell only when subsequent context reaches stoppage, established opponent
control or provider-parent termination before another Leverkusen attacking action. A shot followed by
an immediate Leverkusen continuation is retained. Repeated terminal records while already outside a
spell do not create another boundary. A Leverkusen restart starts a spell; an internal restart closes
the previous spell once. Administrative prefixes and administrative-only/goalkeeper-only parents do not
receive spell IDs. Final parent observation closes remaining membership without guessing extra control.

The detector never consumes review IDs, boundary ledger entries, soft-rule output, x coordinates,
retreat/run/time-since-peak values or future attacking success. Boundaries are scored only afterward.

## C. Human-review validation

| classification | count |
| --- | --- |
| MATCH | 32 |
| UNSCORED_AMBIGUOUS | 7 |
| LATE | 3 |

All reviewed hard targets, explicit exclusions and predicted extras are retained in the validation CSV.
Soft reset targets are ignored. C15/C17 and deferred review tails remain unscored; explicitly reviewed
hard targets in those tails are still compared. Exact regain and onset equality is preferred. A later
corroborated opponent-control onset is accepted only if the intervening records describe the same
loss/failed-action context and the regain is identical; event distance alone never grants acceptance.

| case_id | reviewed_id | classification | reviewed_onset | predicted_onset | reviewed_regain | predicted_regain | accepted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | — | MATCH | — | — | — | — | True |
| C02 | — | MATCH | — | — | — | — | True |
| C03 | C03_H01 | MATCH | 3463 | 3463 | — | — | True |
| C04 | C04_H01 | MATCH | 196 | 196 | 200 | 200 | True |
| C05 | — | MATCH | — | — | — | — | True |
| C06 | C06_H01 | MATCH | 440 | 440 | 448 | 448 | True |
| C07 | C07_H01 | MATCH | 731 | 731 | — | — | True |
| C08 | C08_H01 | MATCH | 2804 | 2804 | — | — | True |
| C09 | — | MATCH | — | — | — | — | True |
| C10 | C10_H01 | MATCH | 2507 | 2507 | — | — | True |
| C10 | — | UNSCORED_AMBIGUOUS | — | 2490 | — | 2499 | False |
| C11 | C11_H01 | LATE | 809 | 811 | 818 | 818 | True |
| C11 | C11_H02 | MATCH | 824 | 824 | 829 | 829 | True |
| C12 | C12_H01 | MATCH | 2539 | 2539 | 2544 | 2544 | True |
| C12 | C12_H02 | MATCH | 2550 | 2550 | — | — | True |
| C13 | C13_H01 | LATE | 346 | 348 | 353 | 353 | True |
| C14 | C14_H01 | MATCH | 2481 | 2481 | 2485 | 2485 | True |
| C15 | — | UNSCORED_AMBIGUOUS | — | 121 | — | — | False |
| C16 | C16_H01 | MATCH | 531 | 531 | 536 | 536 | True |
| C16 | C16_H02 | LATE | 603 | 605 | 613 | 613 | True |
| C16 | C16_H03 | MATCH | 643 | 643 | 651 | 651 | True |
| C16 | C16_H04 | MATCH | 712 | 712 | — | — | True |
| C17 | C17_H01 | UNSCORED_AMBIGUOUS | 2123 | 2123 | 2129 | 2129 | False |
| C17 | — | UNSCORED_AMBIGUOUS | — | 2131 | — | — | False |
| C17 | — | UNSCORED_AMBIGUOUS | — | 2215 | — | 2220 | False |
| C17 | — | UNSCORED_AMBIGUOUS | — | 2231 | — | 2241 | False |
| C17 | — | UNSCORED_AMBIGUOUS | — | 2249 | — | — | False |
| C18 | C18_H01 | MATCH | 1366 | 1366 | 1372 | 1372 | True |
| C18 | C18_H02 | MATCH | 1421 | 1421 | 1427 | 1427 | True |
| C18 | C18_H03 | MATCH | 1485 | 1485 | — | — | True |
| C19 | C19_H01 | MATCH | 106 | 106 | 109 | 109 | True |
| C19 | C19_H02 | MATCH | 111 | 111 | — | — | True |
| C20 | — | MATCH | — | — | — | — | True |
| C21 | C21_H01 | MATCH | 263 | 263 | — | — | True |
| C22 | C22_H01 | MATCH | 440 | 440 | — | — | True |
| C23 | — | MATCH | — | — | — | — | True |
| C24 | C24_H01 | MATCH | 1942 | 1942 | — | — | True |
| C25 | C25_H01 | MATCH | 1255 | 1255 | 1264 | 1264 | True |
| C25 | C25_H02 | MATCH | 1275 | 1275 | — | — | True |
| C26 | C26_H01 | MATCH | 2592 | 2592 | — | — | True |
| C27 | C27_X01 | MATCH | — | — | — | — | True |
| C28 | C28_X01 | MATCH | — | — | — | — | True |

No unaccepted scored hard-boundary failure remains.

The 27 scored hard targets comprise 24 exact onsets and three accepted paired-context differences:
C11:809→811 (dispossession/duel to recovery), C13:346→348 (dispossession/duel to recovery), and
C16:603→605 (failed pass/incomplete receipt to interception). All 14 scored regains are exact.
These are timing conventions for the same football loss, not unmatched control spells.
C27/C28 produce no spell. C20 preserves continuity; C09's corner/clearance/recovery and C12's
nonterminal shot/recovery do not create extra hard cuts. C03/C07/C08/C10/C19/C22 terminal shot
contexts, C21 pass-out, C24 paired foul, and C12/C16/C18/C25/C26 out contexts match the ledger.
The reviewed multiple control breaks in C04/C06/C11/C12/C13/C14/C16/C18/C19/C25 are preserved.

## D. Season-wide inventory

| matches | provider_parents | events | control_spells | zero_spell_parents | one_spell_parents | multiple_spell_parents |
| --- | --- | --- | --- | --- | --- | --- |
| 34 | 2888 | 86025 | 3202 | 132 | 2369 | 387 |

| reason | count |
| --- | --- |
| BALL_OUT | 543 |
| OPPONENT_CONTROL | 540 |
| TERMINAL_SHOT | 502 |
| FOUL_STOPPAGE | 353 |
| STOPPAGE | 96 |

Provider-parent endings are reported as spell end reasons, not additional within-parent hard splits.
The 540 opponent-control boundaries include 446 subsequent within-parent Leverkusen regains;
94 have no later spell start in that parent. Terminal/stoppage boundaries total 1,494.
Unclassified emitted boundary reasons: zero. No internal restart boundary occurs in this inventory;
1,405 spells start from opening restarts. Tests also exercise internal restarts.
Uncorroborated control cues: 50 event contexts;
these are uncertainty flags, not inferred boundaries. Spatial availability is explicitly unevaluated.
Pinned source: `533862946a73608c134d18b78226b6371ce7173c`. Exact reconciliation is enforced before writing.

## E. Soft-reset decision

Human review identified recognizable attacking resets and reorganizations. Three deterministic rules
could not reliably distinguish them from ordinary recycling without material false fragmentation.
They remain descriptive within-control-spell phenomena, not primary boundaries. The historical work
is preserved as the empirical justification for this more conservative analytical unit.

| Historical rule | Exact reset matches | Missed resets | Extra splits |
| --- | --- | --- | --- |
| v0.1 | 3/9 | 4 | 17 |
| v0.2 | 3/9 | 4 | 13 |
| v0.3 | 7/9 | 1 | 11 |

## F. Limitations

Event records are not tracking: corroborated control is contextual inference, and unsupported event
types remain context without inferred coordinates. Parent termination limits observation. Human review
is partial and purposive; C01–C28 is not a statistically representative validation sample. Unconfirmed
control cues are retained as such. No tactical-success, box-entry, shot-outcome or xG variables are built.
Spatial anchors are not attached; future availability is not inferred from the absence of loaded frames.
Boundary events themselves remain outside the closing spell. Therefore terminal-only parents with
no preceding usable control interval (including shot/GK-only and immediately-out pass parents)
also produce zero spells. This is an explicit membership convention, not an attacking outcome filter.

## G. Phase decision

**PHASE 3A — LOCKED / COMPLETE**

Deterministic rerun from the same in-memory event stream: **PASS**. Focused production tests
cover opponent control/regain, defensive interventions, shots, stoppages, restarts, exclusions and IDs.
No raw-data cache or parallel event-stream framework is introduced.

# Phase 5A: danger and effectiveness outcome design

## A. Definitions

The reference population is every trusted Phase 3B anchor with valid locked Phase 3A
membership, including opponent-context anchors. Outcomes use Leverkusen events (team
904) from the complete pinned event stream, including events without spatial frames.

- **Box entry:** a completed Pass (no provider pass outcome value) or Carry with finite,
  on-pitch 2D start and endpoint, starting outside and ending inside `x >= 102,
  18 <= y <= 62` on the StatsBomb 120×80 pitch. Edges are inclusive. No missing endpoint
  is inferred, coordinate clipped, failed Pass counted, or inside-to-inside action counted.
- **Shot:** a Bayer Leverkusen Shot with the same locked control-spell ID as the reference.
  No set-piece or penalty filter is applied.
- **Future xG:** sum of provider `shot.statsbomb_xg` over all eligible Shots. No Shots
  means zero. A missing provider value makes the containing horizon's xG missing;
  Shot binaries remain valid. No imputation, custom model or composite success score.

The canonical table retains reference team, immediate box-entry/Shot indicators and
reference Shot xG. Non-Shot reference xG is missing. Next-event fields identify the first
eligible outcome in source order, including the reference; absent outcomes have missing
ID/time/xG. The event table has one row per underlying outcome, with period and timestamp
for audit. No Phase 4 data, deltas, motifs, coefficients or analytical results are loaded.

## B. Horizon convention

**10 seconds is primary.** 5 and 15 seconds are sensitivities; rest of spell is secondary.
Search starts at the reference event and moves forward in source order, with
`outcome_event_index >= reference_event_index`, always inside the same locked spell.
Elapsed time is the difference between period-local event timestamps; `0 <= elapsed <= H`
is inclusive and calculated as integer nanoseconds. Earlier same-timestamp events are
excluded; later ones remain eligible. Pass/Carry duration is not added to entry time.
Immediate outcomes are included in every horizon. No horizon was tuned using Phase 4.

## C. Reconciliation

- Expected anchors: **43,737**; generated outcome rows: **43,737**; discrepancies: **0**.
- Matches: **34**; locked spells: **3,202**;
  spells with anchors: **3,099**;
  zero-anchor spells: **103**.
- Qualifying box-entry events: **833**; qualifying Shot events: **110**;
  total distinct outcome events: **943**.
- Control spells with a box entry: **733**; with a Shot: **105**;
  with neither: **2,447** (all 3,202 spells as denominator).
- The locked Leverkusen-possession context includes **505** Leverkusen Shots
  without spell membership, including **502** marked terminal-shot boundaries.
  These are excluded by the required same-membership rule; no outcome is reassigned across a boundary.

## D. Outcome prevalence

Prevalences are proportions over all 43,737 anchors. xG summaries use nonmissing values;
the explicit missing count records any denominator difference.

| horizon | anchor_count | box_entry_positive_anchors | box_entry_prevalence | shot_positive_anchors | shot_prevalence | mean_future_xg | median_future_xg | proportion_future_xg_positive | missing_future_xg_anchors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5s | 43737 | 2765 | 0.06321879 | 433 | 0.00990008 | 0.00086069 | 0 | 0.00990008 | 0 |
| 10s | 43737 | 4672 | 0.10682031 | 650 | 0.01486156 | 0.00139921 | 0 | 0.01486156 | 0 |
| 15s | 43737 | 6136 | 0.14029312 | 862 | 0.01970871 | 0.00185722 | 0 | 0.01970871 | 0 |
| rest_of_spell | 43737 | 10733 | 0.24539863 | 1615 | 0.03692526 | 0.00308806 | 0 | 0.03692526 | 0 |

## E. Validation

- Exact Phase 3A membership, spell extent/count and Phase 3B trusted-anchor reconciliation: **PASS**.
- Box-entry, Shot and xG 5/10/15/rest nesting: **PASS**, zero violations.
- Source order and nonnegative elapsed time: **PASS**. No cross-period spells.
- Independent per-spell reconstruction of every binary and xG horizon, plus next-event
  identity/order/time checks for every anchor: **PASS**. Cross-spell contribution: zero.
- xG completeness: **110** qualifying Shots, **110** with xG,
  **0** missing. All qualifying Shots have provider xG.

The deterministic audit selects the first closing spell per boundary family with an
anchor and a qualifying outcome in the immediately following spell in the same period.
The real boundary record is excluded.
It lists real outcomes in the immediately following spell, then injects a box entry and
Shot into that next spell at the last reference timestamp as a worst-case leakage probe.
Every outcome field for every anchor in the closing spell remains identical. Injected
events exist only in the audit and are never written to either analytical CSV.

| boundary | match_id | closing_spell | reference_index | boundary_index | next_spell | next_spell_outcome_indices | result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OPPONENT_CONTROL | 3895052 | 3895052-p2-pp113-s1 | 2266 | 2269 | 3895052-p2-pp113-s2 | 2290 | PASS |
| BALL_OUT | 3895052 | 3895052-p1-pp57-s1 | 1437 | 1439 | 3895052-p1-pp58-s1 | 1464 | PASS |
| FOUL_STOPPAGE | 3895052 | 3895052-p1-pp51-s1 | 1247 | 1248 | 3895052-p1-pp52-s1 | 1268 | PASS |
| TERMINAL_SHOT | 3895052 | 3895052-p1-pp58-s1 | 1471 | 1473 | 3895052-p1-pp59-s1 | 1476 | PASS |

Pinned StatsBomb revision: `533862946a73608c134d18b78226b6371ce7173c`. Read-only inputs are the four existing Phase 3A/3B
CSVs listed below, plus `config/project.yaml` and provider event JSON through the existing
loader. No raw files are written and no Phase 2/3/4 analytical artifacts are regenerated.
SHA-256 hashes identify only these immediate inputs and the two core Phase 5A CSVs:

| file | sha256 |
| --- | --- |
| outputs/diagnostics/phase3b_spatial_anchor_sequences.csv | 5cdac53130e0ead9531403baf67da951492148172f47afef1598e91672adb4ad |
| outputs/diagnostics/phase3b_event_context.csv | acbd31ad4740e8d378a0b1cff224eb4582f9abaa3529b070bd8f677c1aa607dd |
| outputs/diagnostics/phase3_attacking_control_spell_events.csv | 0ccf4fdfb1ca3b16409b28c695afa67741cdf2defeafcc046461ac25ae688847 |
| outputs/diagnostics/phase3_attacking_control_spell_summary.csv | 9b956a27d0fb1301c21f80320d10296e571c219b7437a3715d75c95538b0e830 |
| outputs/analysis/phase5a_anchor_outcomes.csv | 60a4dcc5d56549f7df8d264d43ede468839d8ec58179d230f7fec2d3346e1d40 |
| outputs/analysis/phase5a_outcome_events.csv | a13feb7475151655c7d91879b474925db67cecc33cdda4ee77e41ea91e7ccf16 |

## F. Limitations

- Event data, rather than tracking, cannot establish continuous control or movement.
- Timestamps are event timestamps; the recorded Pass/Carry endpoint defines box crossing.
- Box entry does not guarantee sustained box possession.
- xG exists only after Shots; anchors can share the same future outcome and are not
  independent observations simply because they occupy separate rows.
- Horizon choice is a design choice. Spell termination censors all horizons.
- Set pieces remain included whenever their events have valid spell membership.
- Inherited terminal-Shot exclusion substantially restricts Shot/xG coverage. These
  outcomes describe Shots retained inside locked spells, not all Shots ending attacks.
  The requested membership rule is preserved without reopening segmentation.

## G. Decision

**PHASE 5A — LOCKED / OUTCOME LAYER COMPLETE**

The specified outcome layer is complete under the existing membership convention.
Phase 5B — Spatial Change → Danger is the next step; no Phase 5B analysis is run here.

# Phase 3A-3: role-aware reset analysis

**12 September 2026 — final descriptive pass; no fitted rule or production threshold.** This analysis addresses two
questions: what distinguishes onset from continuation, and what distinguishes confirmation from cancellation once a
warning exists. **Yes: the evidence is sufficient to design one provisional deterministic rule for replay against
C01–C28.** It does not establish a final cutoff or a method lock.

## A. Cohorts used

Inputs are restricted to the reconstruction report and the three specified CSVs. The existing role, resolution and
validity fields are authoritative. No workbook, raw events, boundary map or earlier methodology was reopened. No
labels changed. The 99 ready candidate states are not flattened into three human-label classes.

| analysis_role | source_rows | source_ready | Q1_used |
| --- | --- | --- | --- |
| cancelled_warning | 5 | 5 | 5 |
| confirmed_reset_onset | 9 | 9 | 7 |
| excluded_unrecorded_review | 19 | 0 | 0 |
| excluded_unresolved_membership | 6 | 0 | 0 |
| hard_boundary_context | 35 | 0 | 0 |
| later_reset_phase_sample | 10 | 9 | 0 |
| ordinary_continuation | 83 | 69 | 69 |
| reset_confirmation | 9 | 6 | 0 |
| unresolved_warning | 5 | 1 | 1 |

Q1 uses **69 ordinary continuation states, five cancelled-warning samples, one unresolved warning and seven
confirmed onsets: 82 observations**. The seven positives come only from `onset_pre_split_*`, with an encoded event,
`onset_pre_split_available == True` and all four primary features available. They replace the corresponding
new-episode candidate measurements, not augment them. Confirmation and later reset-phase samples contribute zero Q1
positives. All four primary features are available in every included Q1 observation.

Nine onset locations are encoded; C09_R01 and C11_R01 lack a trusted pre-split reference and are excluded from the
quantitative onset comparison. C11_R02, C12_R02 and C16_R01 retain unresolved onset windows. No confirmation-state
or counterfactual measurement substitutes for any of these five missing onsets.

The five cancelled-warning samples are C16_M05/M06, C22_M05 and C25_M06/M07. C14_M09 is the one valid unresolved
warning. C12_M02 has no trusted current measurement; C15_M07 and C17_M04/M05 have partial episode structure. Those
four unresolved-warning samples remain in the audit table but outside quantitative cohorts.

Q2 has **six confirmed warning excursions, three cancelled warning groups and one valid unresolved group**. Paired
C16 and C25 samples each form one group using recorded case/episode/resolution fields. The earliest recorded warning
represents each group; the fastest recovery is never selected. These grouping keys are not new football boundaries.
All member IDs survive in the CSV. Three additional unresolved groups (C12, C15, C17) are retained as ineligible.
Three same-event onset/confirmation excursions have no observed warning interval; their zero onset-to-confirmation
values are not instantaneous warning-resolution evidence.

## B. Reset-onset evidence

Retreat is in StatsBomb x units; peak time is seconds; runs count trusted actions. Largest backward magnitude is the
absolute value of the signed source diagnostic. The original signed fields are retained. Medians/IQRs and observed
ranges follow; quantiles use linear interpolation, with no smoothing or missing-value imputation.

| role | feature | n | missing | mean | median | IQR | range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ordinary_continuation | retreat | 69 | 0 | 7.881 | 3.8 | 0.000–11.400 | 0.000–48.000 |
| ordinary_continuation | peak_time | 69 | 0 | 1.248 | 0 | 0.000–1.128 | 0.000–14.609 |
| ordinary_continuation | nonpositive_run | 69 | 0 | 0.841 | 0 | 0.000–1.000 | 0.000–4.000 |
| ordinary_continuation | backward_magnitude | 69 | 0 | 7.638 | 4.8 | 1.900–10.300 | 0.000–40.400 |
| cancelled_warning | retreat | 5 | 0 | 12.86 | 12.5 | 8.900–14.100 | 7.900–20.900 |
| cancelled_warning | peak_time | 5 | 0 | 2.29 | 2.394 | 2.000–2.716 | 0.000–4.340 |
| cancelled_warning | nonpositive_run | 5 | 0 | 2.2 | 2 | 2.000–3.000 | 0.000–4.000 |
| cancelled_warning | backward_magnitude | 5 | 0 | 8.68 | 7.9 | 7.900–10.300 | 7.000–10.300 |
| unresolved_warning | retreat | 1 | 0 | 21.1 | 21.1 | 21.100–21.100 | 21.100–21.100 |
| unresolved_warning | peak_time | 1 | 0 | 2.227 | 2.227 | 2.227–2.227 | 2.227–2.227 |
| unresolved_warning | nonpositive_run | 1 | 0 | 6 | 6 | 6.000–6.000 | 6.000–6.000 |
| unresolved_warning | backward_magnitude | 1 | 0 | 8.4 | 8.4 | 8.400–8.400 | 8.400–8.400 |
| confirmed_reset_onset | retreat | 7 | 0 | 22.3 | 20.1 | 13.550–28.950 | 10.200–40.800 |
| confirmed_reset_onset | peak_time | 7 | 0 | 5.456 | 6.116 | 0.331–9.436 | 0.000–12.543 |
| confirmed_reset_onset | nonpositive_run | 7 | 0 | 1.571 | 2 | 1.000–2.000 | 1.000–2.000 |
| confirmed_reset_onset | backward_magnitude | 7 | 0 | 13.729 | 14.1 | 7.000–20.950 | 3.900–22.200 |

Onsets show greater central retreat (median **20.1**, IQR **13.55–28.95**) than ordinary continuation (**3.8**, IQR
**0–11.4**). Cancelled warnings sit between them (**12.5**, IQR **8.9–14.1**), but this is overlap, not a separable
third class. The ordinary/onset retreat range intersection is **10.2–40.8**; the cancelled/onset intersection is
**10.2–20.9**. Some ordinary states occur after an earlier reset or regain, as recorded in their roles; they are not
relabeled.

Time since the relevant peak has median **0** for ordinary states, **2.394** for cancelled warnings and **6.116**
for onsets. Yet C05/C07 begin at time zero: requiring elapsed persistence before warning eligibility would miss
those onsets. Onset nonpositive runs are only **1–2 actions**; cancelled samples reach **4**. Persistence can inform
later confirmation without being a mandatory long-run onset test.

| reset_excursion_id | onset_candidate_id | retreat | peak_time | nonpositive_run | backward_magnitude |
| --- | --- | --- | --- | --- | --- |
| C04_R01 | C04_M04 | 33.5 | 12.543 | 2 | 7.2 |
| C05_R01 | C05_M02 | 14.1 | 0 | 1 | 14.1 |
| C07_R01 | C07_M06 | 20.1 | 0 | 1 | 20.1 |
| C08_R01 | C08_M06 | 13 | 8.892 | 2 | 6.8 |
| C10_R01 | C10_M03 | 24.4 | 0.661 | 2 | 22.2 |
| C12_R01 | C12_M03 | 40.8 | 6.116 | 1 | 21.8 |
| C18_R01 | C18_M05 | 10.2 | 9.98 | 2 | 3.9 |

![Individual onset versus continuation observations](../outputs/figures/phase3a3_role_aware_onset_scatter.png)

![Raw retreat distributions](../outputs/figures/phase3a3_role_aware_retreat_distribution.png)

![Every usable onset](../outputs/figures/phase3a3_role_aware_onset_evidence.png)

The following fixed round-number probes are descriptive counts, not optimized cutoffs. There is no accuracy ranking,
parameter search or recommended number.

| illustrative probe | Ordinary continuation | Cancelled warning | Unresolved warning | Confirmed reset onset |
| --- | --- | --- | --- | --- |
| retreat >= 10 | 19/69 | 3/5 | 1/1 | 7/7 |
| retreat >= 20 | 9/69 | 1/5 | 1/1 | 4/7 |
| retreat >= 30 | 4/69 | 0/5 | 0/1 | 2/7 |
| peak_time >= 3 | 11/69 | 1/5 | 0/1 | 4/7 |
| peak_time >= 5 | 5/69 | 0/5 | 0/1 | 4/7 |
| peak_time >= 10 | 1/69 | 0/5 | 0/1 | 1/7 |
| nonpositive_run >= 2 | 14/69 | 4/5 | 1/1 | 4/7 |
| nonpositive_run >= 3 | 8/69 | 2/5 | 1/1 | 0/7 |

For example, retreat >=20 retains 4/7 onsets and also 9/69 ordinary states and 1/5 cancelled samples. Time >=5
retains 4/7 onsets but also misses three onsets. A nonpositive-run requirement >=3 retains **none** of the usable
onsets, while including two cancelled samples. A large recent backward vector alone also fails: onset magnitudes
range 3.9–22.2, whereas ordinary samples reach 40.4.

Alternative counters are sensitivity checks, not independent reinforcement:

| role | pair | n | Spearman |
| --- | --- | --- | --- |
| ordinary_continuation | peak_time / peak_events | 69 | 0.98 |
| ordinary_continuation | nonpositive_run / negative_run | 69 | 0.894 |
| confirmed_reset_onset | peak_time / peak_events | 7 | 0.807 |
| confirmed_reset_onset | nonpositive_run / negative_run | 7 | 1 |
| recorded_warning_groups_local_return | recovery_time / recovery_events | 7 | 0.937 |

These paired rank correlations are descriptive and case-dependent. Recovery pairs use the local-reference durations
shown below and do not validate a common old-peak restoration measure. No model combines correlated variables as
separate evidence.

## C. Warning confirmation versus cancellation

| case_id | resolution | representative_candidate_id | warning_sample_count | time_to_confirmation | recovery_time | recovery_status | onset_nonpositive_run | later_nonpositive_run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C04 | confirmed | C04_M04 | 1 | 11.228 | 6.067 | observed_equal_or_higher_peak | 1 | 4 |
| C05 | confirmed | C05_M02 | 1 | 2.799 | 5.774 | observed_equal_or_higher_peak | 1 | 2 |
| C07 | confirmed | C07_M06 | 1 | 3.719 | 33.881 | observed_equal_or_higher_peak | 1 | 4 |
| C08 | confirmed | C08_M06 | 1 | 1.793 | 14.641 | observed_equal_or_higher_peak | 1 | 2 |
| C10 | confirmed | C10_M03 | 2 | 4.541 | — | censored_at_episode_observation_end | 1 | 3 |
| C18 | confirmed | C18_M05 | 2 | 4.52 | 28.985 | observed_equal_or_higher_peak | 1 | 3 |
| C14 | unresolved | C14_M09 | 1 | — | — | censored_at_episode_observation_end | 6 | 6 |
| C16 | cancelled | C16_M05 | 2 | — | — | censored_at_episode_observation_end | 2 | 3 |
| C22 | cancelled | C22_M05 | 1 | — | 3.853 | observed_equal_or_higher_peak | 0 | 0 |
| C25 | cancelled | C25_M06 | 2 | — | 6.691 | observed_equal_or_higher_peak | 2 | 4 |

For confirmed excursions, `recovery_time` above is return to the **new episode's peak at its onset sample**, while
cancelled/unresolved groups use the original current-episode peak at their first recorded warning. These durations
are not interchangeable measurements of restoration of the abandoned attack. Pre-split recovery for all six
confirmed warning excursions is structurally censored at the retrospective split. That censoring is not evidence of
failure to restore the old peak before confirmation; the allowed artifacts do not measure that future trajectory
against a fixed pre-split reference.

Five of six confirmed groups have an observed **new-reference** return; C10 is censored. Two of three cancelled
groups have an observed current-peak return: C22 at **3.853 s** and C25 at **6.691 s**, measured from its first
warning sample. C25_M07's 4.297 s is a later clock start for the same group's return, not another independent
cancellation. C16 is explicitly cancelled yet has no observed full peak return: its follow-up is truncated after
1.305 s before an unresolved later reset window. Renewed progression and complete peak restoration are different
tests.

Confirmed warning-to-confirmation delays range **1.793–11.228 s**, median **4.1195 s**. All six show new-episode
nonpositive runs increasing from 1 at the onset sample to 2–4 at first confirmation. These are observed
action-subsequence counts, not tracking or uninterrupted physical retreat. Cancellation samples can also reach 3
(C16) or 4 (C25); C22's recorded warning sample has run zero. The last warning sample in a cancelled group is not
asserted to be the exact cancellation event.

The seven ready later reset-phase samples labeled CLEAR_RESET and two later warning-phase samples remain supporting
context for established excursions. They are not extra onsets, confirmations or independent warning-resolution
trials. One additional later-phase sample is ineligible because its episode start is unresolved.

![Warning timings with censoring separate](../outputs/figures/phase3a3_role_aware_warning_resolution.png)

In Figure 3, circles show observed local-reference returns and ticks show recorded confirmation delays. No point is
plotted for a missing/censored recovery time. The unresolved C14 group is censored at parent observation end, with
19.178 s of follow-up; it is neither a cancelled warning nor an inferred confirmed reset.

## D. Important counterexamples

- **C05_R01/C05_M02:** onset retreat 14.1, time zero, run 1; confirmation after
  2.799 s. Its new-episode peak returns after 5.774 s. An eventual quick return
  does not undo the reviewed reset; requiring long onset persistence misses it.
- **C18_R01/C18_M05:** onset retreat 10.2 with only 3.9 recent backward magnitude,
  but 9.980 s since peak. A large single backward-action requirement misses it.
- **C16_M05/M06:** cancellation without observed full peak return. Requiring a
  complete old-peak recovery to cancel would contradict the recorded resolution.
- **C25_M07:** cancelled-warning sample with four nonpositive actions. That run
  is longer than every usable onset run; length alone cannot confirm abandonment.
- **C04_R01:** the new-episode peak returns after 6.067 s, before confirmation
  at 11.228 s. Its new reference is 70.9 versus the pre-split 97.2. This defeats
  treating any local-peak return as restoration of the original attack.
- **C10_M07/C09_M03:** ordinary-role continuation with retreat 48.0/40.4 inside
  rebuilt episodes. A detector needs state/re-entry handling to avoid repeated cuts.
- **C14_M09:** unresolved warning with six nonpositive actions and retreat 21.1.
  An unresolved outcome cannot be converted to confirmation by a numerical rule here.

## E. Candidate state-machine ingredients

1. Retain the reviewed football/control and restart/relocation eligibility
   safeguards before numerical warning evidence; these are inherited constraints.
2. Permit a warning from meaningful retreat supported by the action context.
   Do not require a long negative run or elapsed delay at the onset itself.
3. Once warned, retain the warning's reference and accumulate persistence/
   reorganization evidence; use time or related event counters parsimoniously.
4. Allow restored forward progression to support cancellation without requiring
   complete peak recovery. A fast return is supporting context, not an unconditional veto.
5. Confirm only with reinforcing evidence, then associate one split with the
   recorded warning onset; suppress repeated cuts from later samples of that excursion.

These ingredients describe the next rule-design discussion. No numeric setting, transition implementation or
production policy is selected in this analysis.

## F. What remains unresolved

The three unknown onset windows, two unavailable pre-split references, partial C15/C17 structure, and unmeasured
exact cancellation times remain unresolved. The seven positive onsets are selected, case-dependent review
observations; paired warnings and later samples are not independent. Censoring and changing peak references prevent
a clean common-reference confirmation-versus-cancellation recovery distribution. The snapshot counters also cannot
establish uninterrupted progression between every event. None of these gaps is repaired by interpolation,
counterfactual substitution, outcome labels or numerical relabeling.

## G. Readiness decision

**Yes—design one provisional deterministic state-machine rule, then replay it against C01–C28.** The evidence
supports separating warning eligibility from confirmation, preserving a reference while warned, and checking
cancellation and duplicate-cut behavior against the named counterexamples. Overlap is a reason to assess a candidate
rule in replay, not to add another descriptive research phase. Keep unresolved intervals and partial reviews as
explicit unscored/ambiguous replay checks; they are not negative examples. The missing common-reference recovery
trajectory limits this report's conclusions but does not block a provisional rule that can be inspected during
replay. No material blocker prevents that next step. After replay, revise once if materially necessary before
considering a method lock.

Reproduction: `.venv\Scripts\python.exe scripts/role_aware_reset_analysis.py`. The script writes only this report,
four PNGs and three CSVs, using fixed plotting jitter and deterministic grouping. The CSVs are
`phase3a3_role_aware_cohort.csv`, `phase3a3_role_aware_onset_comparison.csv` and
`phase3a3_role_aware_warning_resolution.csv` in `outputs/diagnostics/`. Guard checks reconcile source
readiness/recovery denominators, reject Boolean ambiguity, enforce unique onset/group IDs, exclude later samples
from Q1 and preserve missing recovery times. No extra test suite or reconstruction changes. Runtime: Python 3.14.0,
pandas 3.0.5, NumPy 2.5.2, Matplotlib 3.11.1.

Input SHA-256 values (provenance only):

- `phase3a3_episode_local_reconstruction.md`: `3d57e581a3c0777fa8971cc1ffd93ecbbab1da342ee227250b84a757c83b30ac`
- `phase3a3_episode_local_candidate_diagnostics.csv`: `e6463c000a58bee185aa54cc8368b71202a834715ff882d66708c54556756246`
- `phase3a3_reset_excursion_diagnostics.csv`: `5374d2b830416670290065130517b4d7ab5527406007d080dabe75e1bf011820`
- `phase3a3_episode_local_recovery_summary.csv`: `d7f5127d72701b069d23c3758c32990a95265753f61236181b3da2fa9e4f916a`


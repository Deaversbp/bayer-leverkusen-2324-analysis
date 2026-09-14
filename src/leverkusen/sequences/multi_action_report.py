"""Pinned Phase 4B evidence and deliberately limited observational interpretation."""

import pandas as pd

from leverkusen.sequences.multi_action import window_scope
from leverkusen.sequences.spatial_readiness import markdown

DECISION = "PHASE 4B — COMPLETE / MIXED SEQUENCE SIGNAL"


def signature_table(table):
    result = table[["window_length", "motif", "N", "matches"]].copy()
    result["share_pct"] = table.share_of_windows * 100
    for metric, name in (("total_progression", "progression"), ("duration_seconds", "seconds"),
                         ("net_opp_centroid_x", "opponent_centroid_x")):
        result[f"{name}_median_[q25,q75]"] = [f"{r[f'{metric}_median']:.3f} [{r[f'{metric}_q25']:.3f}, {r[f'{metric}_q75']:.3f}]" for r in table.to_dict("records")]
    result["opp_width_median"] = table.net_opp_visible_width_median
    result["opp_pairwise_median"] = table.net_opp_mean_pairwise_distance_median
    result["lev_centroid_x_median"] = table.net_lev_centroid_x_median
    return markdown(result)


def select_examples(windows):
    """Representative scalar examples; support landmarks apply only to illustration."""
    results = []
    for length, motif in ((2, "CC"), (3, "PCC"), (3, "CPC")):
        group = windows[windows.window_length.eq(length) & windows.action_type_motif.eq(motif)]
        candidate = group[window_scope(group, "gap_le_3") & window_scope(group, "exclude_oob") &
            window_scope(group, "exclude_coincidence") & group.observed_opp_centroid_x_status.eq("complete")].copy()
        if candidate.empty:
            continue
        count = candidate[[f"anchor_{i}_opp_n_valid_points_used" for i in range(length+1)]].min(axis=1)
        coverage = candidate[[f"anchor_{i}_visible_area_fraction" for i in range(length+1)]].min(axis=1)
        candidate = candidate[count.ge(count.median()) & coverage.ge(coverage.median())].copy()
        if candidate.empty:
            continue
        score = pd.Series(0., index=candidate.index)
        for variable in ("total_progression", "net_opp_centroid_x"):
            scale = group[variable].quantile(.75) - group[variable].quantile(.25)
            if scale > 0:
                score += (candidate[variable] - group[variable].median()).abs() / scale
        candidate["representative_distance"] = score
        results.append(candidate.sort_values(["representative_distance", "match_id", "first_anchor_source_order"]).iloc[0])
    return results


def render_report(windows, audit, tables):
    action, direction, adjusted, sensitivity, support = [tables[k] for k in (
        "motif_summary", "direction_profile_summary", "centroid_adjusted_summary", "sequence_sensitivity", "motif_match_support")]
    sample, context, thirds, reductions = [], [], [], []
    for length, group in windows.groupby("window_length", sort=True):
        sample.append(dict(actions=length, candidate_chains=int(audit[audit.window_length.eq(length)].N.sum()),
            eligible_windows=len(group), matches=group.match_id.nunique(),
            control_spells=group.attacking_control_spell_id.nunique(),
            centroid_endpoint_N=int(group.net_opp_centroid_x_status.eq("ok").sum()),
            duration_median=group.duration_seconds.median(), duration_q25=group.duration_seconds.quantile(.25),
            duration_q75=group.duration_seconds.quantile(.75), duration_p90=group.duration_seconds.quantile(.9),
            duration_p95=group.duration_seconds.quantile(.95), duration_max=group.duration_seconds.max(),
            maximum_leg_gap_median=group.maximum_leg_gap.median(), maximum_leg_gap_p95=group.maximum_leg_gap.quantile(.95)))
        for zero in (True, False):
            g = group[group.intervening_full_event_count.eq(0).eq(zero)]
            context.append(dict(actions=length, context="zero_between_every_anchor" if zero else "one_or_more_intervening_events",
                N=len(g), share_pct=100*len(g)/len(group), intervening_events_median=g.intervening_full_event_count.median(),
                intervening_events_p95=g.intervening_full_event_count.quantile(.95),
                full_span_count_median=g.full_event_span_count.median(), centroid_median=g.net_opp_centroid_x.median()))
        for (motif, third), g in group.groupby(["action_type_motif", "starting_third"], sort=True):
            denominator = len(group[group.starting_third.eq(third)])
            thirds.append(dict(actions=length, motif=motif, starting_third=third, N=len(g),
                share_within_third_pct=100*len(g)/denominator,
                centroid_N=int(g.net_opp_centroid_x_status.eq("ok").sum()), centroid_median=g.net_opp_centroid_x.median()))
        g = group.loc[group.net_opp_centroid_x_status.eq("ok"), ["action_type_motif", "net_opp_centroid_x", "total_progression"]].copy()
        fit = adjusted[adjusted.window_length.eq(length) & adjusted.scope.eq("all") & adjusted.model.eq("progression_only")].set_index("term").coefficient
        g["residual"] = g.net_opp_centroid_x - fit["intercept"] - fit["total_progression"]*g.total_progression
        means = g.groupby("action_type_motif").agg(N=("residual", "size"), raw=("net_opp_centroid_x", "mean"), residual=("residual", "mean"))
        before = (((means.raw - g.net_opp_centroid_x.mean())**2)*means.N).sum()/len(g)
        after = (((means.residual - g.residual.mean())**2)*means.N).sum()/len(g)
        reductions.append(dict(actions=length, raw_weighted_between_motif_mean_variance=before,
            progression_residual_between_motif_mean_variance=after, descriptive_reduction_pct=100*(1-after/before)))
    cross = []
    for length, g in windows.groupby("window_length"):
        cross.append(f"### {length}-action count cross-table\n\n" + markdown(pd.crosstab(g.action_type_motif, g.direction_profile).reset_index()))
    comparison = adjusted[adjusted.scope.eq("all") & adjusted.model.eq("progression_plus_motif") & adjusted.term.str.startswith("motif_")]
    fits = adjusted[adjusted.scope.eq("all")].drop_duplicates(["window_length", "model"])[["window_length", "model", "N", "matches", "r_squared"]]
    primary = action[["window_length", "motif", "N", "net_opp_centroid_x_median"]].assign(scope="all")
    gaps = sensitivity[sensitivity.motif_system.eq("action") & sensitivity.scope.isin(["gap_le_5", "gap_le_3"])][["window_length", "motif", "scope", "N", "net_opp_centroid_x_median"]]
    gap_table = pd.concat([primary, gaps]).pivot(index=["window_length", "motif"], columns="scope", values=["N", "net_opp_centroid_x_median"])
    gap_table.columns = [f"{a}_{b}" for a, b in gap_table.columns]
    examples = []
    for r in select_examples(windows):
        length = int(r.window_length)
        ids = " → ".join(f"`{r[f'anchor_{i}_event_id']}`" for i in range(length+1))
        dx = ", ".join(f"{r[f'action_{i}_delta_x']:.3f}" for i in range(1, length+1))
        delta = ", ".join(f"{r[f'leg_{i}_delta_opp_centroid_x']:.3f}" for i in range(1, length+1))
        counts = ", ".join(str(int(r[f"anchor_{i}_opp_n_valid_points_used"])) for i in range(length+1))
        areas = ", ".join(f"{r[f'anchor_{i}_visible_area_fraction']:.3f}" for i in range(length+1))
        examples.append(f"**{r.action_type_motif}: `{r.window_id}`**, match {int(r.match_id)}. Action dx: [{dx}]; summed progression {r.total_progression:.3f}; net opponent centroid-x {r.net_opp_centroid_x:.3f}; individual observed leg deltas [{delta}]. Duration {r.duration_seconds:.3f} s, largest leg gap {r.maximum_leg_gap:.3f} s. Opponent selected counts [{counts}], supplied visible-area fractions [{areas}].\n\nAnchors: {ids}.")
    secondary = action[["window_length", "motif", "net_opp_visible_width_median", "net_opp_visible_depth_median", "net_opp_convex_hull_area_median", "net_opp_mean_pairwise_distance_median", "net_lev_centroid_x_median"]]
    evolution = action[["window_length", "motif", "leg_1_delta_opp_centroid_x_median", "leg_2_delta_opp_centroid_x_median", "leg_3_delta_opp_centroid_x_median"]]
    return f"""# Phase 4B: multi-action spatial sequence patterns

**{DECISION}**

## A. Question and fixed-window definition

Which short Leverkusen Pass/Carry patterns recur within the locked control spells, and how
does visible spatial structure differ across them? This phase uses **fixed overlapping
2- and 3-action windows**, not new tactical-sequence boundaries. For two actions, A/B/C must
be consecutive trusted anchors; A and B supply eligible Phase 4A actions and C is the next
observation. Three actions require A/B/C/D, with A/B/C eligible and D the next observation.
No trusted anchor is skipped, no control spell is split, and no 4+ window is constructed.

Phase 3B supplies order, geometry values and metric-specific support. The exact frozen Phase
4A dataset supplies membership in its trusted progression population and its explicit action
vectors, already produced by the shared progression helper. Eligibility is not redefined or
recomputed. Joins require exact match/event IDs and the original adjacent TO ID. The construction
reads only derived, outcome-free inputs; no raw outcome records are loaded or inspected.

The primary response is final minus first **visible opponent centroid x**. Positive means that
the final visible centroid is farther toward the opponent's own goal in the normalized
Leverkusen reference. It does not measure a defensive line, full-team retreat or player
displacement. Every per-leg delta is retained exactly from Phase 3B.

Action motifs use P=Pass, C=Carry. Direction profiles are separate: F means strictly positive
action delta-x; R means zero or negative, an observational nonpositive direction code rather
than an inferred recycling action. No optimized threshold, joint motif classifier or clustering
is used. Counts of the cross-product appear only as support audits below.

## B. Analytical sample

Inputs reconcile to **43,737 trusted anchors**, **40,638 Phase 3B transitions**, **14,848 eligible
Phase 4A Pass legs** and **15,527 eligible Carry legs** at pinned revision
`533862946a73608c134d18b78226b6371ce7173c`.

{markdown(pd.DataFrame(sample))}

The candidate denominator includes every contiguous three- or four-anchor tuple within each
spell, regardless of action eligibility: **37,732 two-action candidates** and **34,993 three-action
candidates**. The following disjoint first-failure categories account for every candidate;
geometry missingness does not exclude windows.

{markdown(audit)}

`not_eligible_under_phase4a_progression_rules` inherits Phase 4A's failed/unknown endpoint,
named pass-type/restart and relocation-affected measurement exclusions. This frozen downstream
population is not relabeled with a new vector-validity test. No unexplained chain loss remains.
Unsupported ordinary events between anchors remain full-stream context, as in the locked method.

Duration is first to final **anchor timestamp**, not first to last inferred action completion.
Each action's signed progression, summed positive progression and backward magnitude are retained.
Summed action dx may differ from final action endpoint minus first start because intervening
recorded endpoints/starts need not coincide. Neither difference supplies new control boundaries.

Window IDs contain match, existing spell, action count and first within-spell anchor order.
All action/anchor IDs, per-leg seconds and intervening-event counts remain available. Full-span
count includes both endpoint anchors; summed intervening counts exclude the trusted anchors.
**Windows overlap and are correlated observations, not independent tactical possessions.**
Counts describe observed recurrence, not independent replication.

## C. Recurring action-type motifs

Medians with [q25,q75]; lengths have separate denominators. All motifs remain visible, including
rare CCC. No frequency threshold decides whether a motif exists.

{signature_table(action)}

**PC (11,800; 48.61%) and CP (10,679; 44.00%)** dominate two-action windows; together they account
for 92.61%. **CPC (8,588; 43.70%) and PCP (8,365; 42.57%)** dominate three-action windows (86.27%
together). These alternations also reflect the provider's event/Carry representation and
strict-anchor sampling, not independently identified football combinations.

CC has the largest broadly represented two-action opponent-centroid median, **+5.234**.
Among three-action motifs with wider support, **PCC +6.650** and **CCP +6.124** exceed the common
alternating motifs. CCC's raw median is +13.467, but only **17 windows in 12 matches** support it;
it is retained without strong general interpretation. PP/PPP also show positive raw medians,
so there is no simple monotonic rule that more Carry symbols imply more observed change.

{markdown(support)}

![Two-action frequency and progression](../outputs/figures/phase4b_two_action_frequency.png)
![Two-action opponent centroid](../outputs/figures/phase4b_2_action_centroid.png)
![Three-action opponent centroid](../outputs/figures/phase4b_3_action_centroid.png)

## D. Progression-direction profiles

{signature_table(direction)}

FF and FFF have the clearest positive endpoint-centroid medians (**+6.135**, **+11.864**), whereas
RR and RRR are negative (**−2.254**, **−4.045**). FR exceeds RF (**+1.597** versus **+0.133**).
Among profiles with two forward actions, **FFR > FRF > RFF** in median centroid change
(**5.184 > 3.943 > 2.698**); this ordering persists under the shorter-gap sensitivities.
However their median total progressions also differ (**9.9 > 8.5 > 7.8**), as do type composition
and observation timing. These are descriptive ordering signatures, not isolated order effects
at matched progression. RF's near-zero positive median becomes slightly negative at shorter
gaps; its sign is not a robust signature. Zero and backward actions share R without further bins.

![Direction-profile signatures](../outputs/figures/phase4b_direction_profiles.png)

The following cross-tables are **counts only**. No full-cross-product response model or joint
pattern labels are fitted; sparse cells remain visible.

{chr(10).join(cross)}

## E. Opponent structural evolution

Centroid-x has narrative priority because Phase 4A established its clearest single-action
association. Width, depth, observed outfield convex-hull footprint and spacing remain secondary.

{markdown(secondary)}

The common PC/CP and PCP/CPC motifs have mostly small extent/spacing medians compared with
their centroid changes. PCC and CCP have positive width/footprint medians but slightly negative
pairwise medians; these are not a single coherent expansion measure. Metric families are
dependent, so correlated spacing measures are not separate discoveries. The full motif tables
retain all nine opponent and all nine Leverkusen responses with metric-specific N and IQR.
No extent/spacing result is promoted as a robust tactical signature from its raw median alone.

Each window retains first/final metric values and statuses, net change, every individual leg
delta/status, available-state count, and observed min/max/range. Max/min/range use only available
states and explicitly mark incomplete support as `partial_available_states`. A missing interior
metric can leave net endpoint change available while making its adjacent leg deltas missing.
No geometry is filled. Centroid-x advancement/reversal from start are observed extrema relative
to an available first state, never movement rates or unobserved excursions.

{markdown(evolution)}

For example, PCC's largest **median leg** centroid change is on leg 2 (+3.836), while CCP's is
on leg 1 (+3.236). These locate where the observations differ most at group level; they do not
identify the strongest leg in every window. Leg medians do not add to the median net change.

## F. Leverkusen structural evolution

Leverkusen's visible centroid broadly parallels the opponent centroid: medians are +1.105/+1.202
for PC/CP, +6.094 for CC, +1.690/+2.057 for PCP/CPC and +7.503/+6.195 for PCC/CCP.
This is consistent with changes in the event-aligned view and possible longitudinal
reorganization of both sides. Those contributions cannot be separated here. Secondary own-team
extent, spacing and counts remain in the tables; no causal team-response interpretation follows.

## G. Progression-adjusted motif comparison

Models are fitted separately for each window length and use only available endpoint centroid-x.
The baseline is `net_opp_centroid_x ~ 1 + total_progression`; the primary adjusted model adds
action-type motif indicators, with PP/PPP references. A pre-specified supplementary version adds
the first action's start x. There are no interactions, feature selection or tuned models.
The common slope imposes a linear additive summary; it does not test every possible relation
between progression and Carry composition. Individual motif progression distributions and
sample support remain visible rather than claiming matched or randomized comparisons.

OLS standard errors use one-way **match-clustered CR1** with correction
`G/(G−1) × (N−1)/(N−p)` and 95% t intervals with G−1 degrees of freedom, the same convention as
Phase 4A. Match clustering contains overlapping windows and repeated spells within matches.
No naive iid p-values or multiple-comparison selection are reported. A focused numerical test
reproduces Phase 4A's covariance when the model has only an intercept and progression.

{markdown(fits)}

Progression alone gives R² **0.5358** for two-action and **0.5950** for three-action windows.
Motif terms raise these to **0.5412** and **0.5992**: gains of **0.0053** and **0.0042**, respectively.
Thus most modeled window-level variation is associated with progression, while the extra
global contribution of these additive motif labels is small.

To distinguish overall fit from **between-motif differences**, the next table compares the
window-weighted variance of motif mean centroid changes before and after subtracting the
progression-only fitted value. These are descriptive reductions, not causal explained shares.

{markdown(pd.DataFrame(reductions))}

That reduction is about **47%** for two-action and **61%** for three-action motif means. It would
be inaccurate to say progression eliminates all motif differences, or explains most two-action
between-motif variation. Raw medians and adjusted mean contrasts are different summaries.

{markdown(comparison[['window_length', 'term', 'reference_motif', 'coefficient', 'cluster_se', 'ci_low', 'ci_high', 'motif_N']])}

**CC retains a positive adjusted contrast:** +2.986 relative to PP (95% CI 1.902–4.070).
PC and CP are lower than PP at the model's common progression by 1.237 and 1.591 units.
This is composition-related residual association, not an independent effect of inserting a Carry.
For three actions, PCC and CCP contrasts to PPP are small and uncertain; CCC is highly uncertain.
CPC has two Carries but differs little from one-Carry PCP in adjusted coefficient (about 0.239
units between them). Hence **more Carries is not a general adjusted ordering rule**.

Adding first start x barely changes the CC contrast (2.987); the supplementary three-action
motif contrasts are also similar. Starting-position context matters descriptively without
establishing a new universal spatial mechanism.

![Progression within motifs](../outputs/figures/phase4b_progression_by_motif.png)
![Adjusted motif contrasts](../outputs/figures/phase4b_adjusted_motif_contrasts.png)

## H. Starting-position context

Only the inherited equal thirds are used: [0,40), [40,80), [80,120] of the **first action start**.
Frequencies below are shares within each length/third, not tactical zones.

{markdown(pd.DataFrame(thirds))}

Larger raw centroid changes generally occur from earlier starting positions. CC remains
positive in all thirds (medians 11.725, 4.763, 3.284); PCC/CCP medians are much larger in the
defensive third (15.160/14.088) than the attacking third (0.306/0.884). Common PCP/CPC medians
are slightly negative in the attacking third. These differences prevent a field-position-free
interpretation of raw motif medians; low counts in rare motif/third cells require caution.

## I. Robustness

### Every-leg gap sensitivity

Every one of the two or three leg gaps must be ≤5 or ≤3 seconds. Total window duration is not
the gate: a three-action window can last nine seconds and meet the ≤3-per-leg comparison.
The primary dataset remains unchanged. Counts and centroid medians:

{markdown(gap_table.reset_index())}

CC remains the largest broadly represented two-action median (**5.234 → 3.891 → 3.244**), but
support falls **562 → 383 → 183**. PCC and CCP retain positive and relatively larger three-action
medians (**6.650 → 5.866 → 5.325** and **6.124 → 3.915 → 2.964**), with ≤3 s N **113** and **98**.
These are attenuated signatures, not fixed magnitudes. CCC falls to nine/four windows and is
too sparsely supported for a strong sensitivity conclusion despite remaining in the tables.
Among the common motifs, the small PCP/CPC median ordering changes at ≤3 s; their ordering is
not robust. All raw action-type motif medians remain positive at the season level.

CC's progression-adjusted contrast persists across all/≤5/≤3 (**2.986, 2.857, 1.888**), with
95% intervals **[1.902,4.070]**, **[1.593,4.121]**, **[0.719,3.058]**. PC/CP adjusted contrasts
attenuate substantially; three-action contrasts depend on gap scope and the small PPP reference.
All adjusted sensitivity rows, including uncertainty and N, remain in the adjusted CSV.
No numerical stability threshold is used.

FF/FFF stay positive and RR/RRR negative. FFR > FRF > RFF persists under both gap comparisons;
their ≤3 medians are 3.416 > 2.826 > 1.699. RF changes from +0.133 to −0.025/−0.159, while
FR remains positive. This small RF sign change limits any strong forward-last interpretation.

![Every-leg gap comparisons](../outputs/figures/phase4b_gap_sensitivity.png)

### Terminal team, full-event context and coordinate sensitivities

Leverkusen-terminal-only selection restricts the original final observation; it does not skip
to a later anchor. It preserves the broad raw CC/PCC/CCP patterns (medians **5.217/6.109/6.072**).
CC's adjusted contrast remains positive (**2.266**), but three-action adjusted contrasts are
less stable, including PCC's reference contrast changing sign near zero. The final observation
can otherwise be an opponent event, Pressure or Shot; terminal event type is stored as identity
only and is never used as an attacking outcome or motif definition.

{markdown(pd.DataFrame(context))}

Only **709 two-action windows** have zero intervening full-stream events on every leg; **no
three-action windows** do. This comparison is an observability audit, not an inclusion rule or
a claim of greater causal isolation. Intervening events remain counted, with no inferred
trajectories across them.

The locked OOB sensitivity excludes a window if **any constituent anchor frame** has whole-frame
OOB or unknown OOB status. Coincidence sensitivity analogously checks every frame for the
headline centroid (a multiplicity-sensitive metric). No points are removed or deduplicated,
and no anomalies are removed from the primary data. These whole-window masks preserve the
original whole-frame conditions; they include interior observations, not only endpoints.

OOB exclusion retains CC/PCC/CCP medians at **5.741/7.775/6.114**; CC's adjusted contrast is
**3.456**, with direction unchanged. Coincidence exclusion changes the corresponding medians
to **5.217/6.650/6.100** and CC's adjusted contrast to **2.960**. Main conclusions therefore do
not rely on these flagged frames. Rare CCC remains sensitive to very small changes in support.
The sensitivity CSV includes N, matches, metric-specific counts and medians for both motif
systems; no robustness claim is inferred solely from preserving a point-estimate sign.

## J. Football interpretation

### Observed evidence

Alternating Pass/Carry symbols dominate the strict windows. Larger summed progression is
associated with larger positive net changes in visible opponent centroid x. CC and sequences
containing adjacent Carries show larger raw positional medians, with a residual CC contrast
after progression adjustment. However, additive motif terms contribute little extra global
fit, three-action contrasts are less stable, and a simple count of Carries does not order
adjusted responses. Direction-profile ordering is descriptive and intertwined with progression.

### Plausible football interpretation

The patterns may reflect longitudinal changes in play together with changes in the portion
of each team visible around events. They do not establish that a symbolic motif forces a
defensive response, identifies a defensive line, or describes a recognized tactical category.
No motif is ranked by danger, success or effectiveness.

### Representative windows

For CC, PCC and the common CPC motif, examples are restricted to complete centroid support,
every leg ≤3 s and no whole-frame OOB/coincidence flags. Among those candidates, require minimum
within-window opponent count and minimum visible-area fraction at least their motif-specific
candidate medians; these are **illustration-only support landmarks**, not analysis thresholds.
Choose the nearest candidate to its primary motif medians in total progression and net
centroid change, using summed absolute IQR-scaled distances; ties use match and source order.
No future outcome or terminal event type influences selection. Counts and coverage below
describe partial states, not complete teams or persistent player identity.

{(chr(10) * 2).join(examples)}

Examples illustrate representative observations rather than prove a mechanism. Their individual
leg deltas are differences between partial event-aligned states, not player paths.

## K. Limitations

Overlapping windows are dependent; raw counts do not measure independent replication. Match
clustering is a limited uncertainty convention, not a remedy for observability bias or confounding.
Frames are partial event-aligned observations with no tracking and anonymous ordinary off-ball
players. Variable visible area, changing selected player counts, anchor gaps and intervening
events can all affect comparisons. The next observation need not represent the previous
action's endpoint arrival. Metric families are dependent; hull is an observed outfield
convex-hull footprint and stays secondary.

Fixed windows are descriptive motifs, not natural tactical boundaries. The inherited Phase 4A
eligibility and provider Pass/Carry representation shape their frequency. Rare CCC and the
small PPP reference constrain three-action comparisons; narrow-looking intervals from a tiny
motif are not sufficient evidence. The adjusted model uses a common linear progression slope,
not exhaustive control for progression shape, timing, visibility or composition. No outcomes,
effectiveness, tactical archetypes, sequence embeddings or clustering are used.

## L. Phase decision and required answers

**{DECISION}**

1. **Most frequent motifs:** PC/CP for two actions, CPC/PCP for three, broadly represented in all
   34 matches. Their counts describe recurrence of symbols, not independent tactical sequences.
2. **Largest robust observed centroid changes:** CC for two actions and PCC/CCP among better
   supported three-action motifs. CCC is numerically largest but too sparse for a strong claim.
3. **How much is progression?** It supplies most modeled window-level variation (R² about
   0.536/0.595); motif additions are only 0.0053/0.0042. Between-motif mean dispersion falls
   roughly 47%/61% after progression-only residualization, so residual differences remain.
4. **Composition/order after adjustment:** CC retains a positive, gap-sensitive contrast.
   Three-action results do not support a general more-Carries rule or stable ordering of
   all motifs. No causal composition effect is identified.
5. **Forward/nonpositive ordering:** FF/FFF versus RR/RRR is clearest; FFR > FRF > RFF persists
   descriptively, with different total progressions and compositions. Order alone is not isolated.
6. **Ready for Phase 5?** Yes, for **Danger and Effectiveness Outcome Design**, retaining explicit
   support, timing, overlap and rare-motif limitations. This supports designing the outcome
   layer; it does not establish that any motif is better or dangerous. No outcome work begins here.

Reproduce with `.venv\\Scripts\\python.exe scripts/multi_action_spatial_sequences.py`.
Six CSVs, seven figures and this report form the analytical output family; the manifest records
input/code/output hashes and the full candidate-chain reconciliation. Protected Phase 2/3/4A
artifacts and measurement code remain unchanged. Deterministic reruns compare analytical bytes;
generation timestamps are provenance metadata only.
"""

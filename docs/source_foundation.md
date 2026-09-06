# Source foundation

## Available sources

The original repository contains exploratory notebooks, loader/transform code and
an environment snapshot. No academic methods PDFs or source-foundation Markdown
were present. Bibliographic entries, quotations, page references and evidence for
specific tactical formulas remain **TBD**; none have been fabricated.

The [official StatsBomb Open Data repository](https://github.com/hudl/open-data)
documents the match/event/lineup/360 layout and attribution guidance. Its
[documentation directory](https://github.com/hudl/open-data/tree/master/doc) is the
starting point for raw field semantics. Repository layout was checked at migration;
this is not a completed review of every specification or an academic justification
for spatial metrics.

## Provenance categories

| Category | Meaning |
| --- | --- |
| SOURCE | Raw provider field or documented source material |
| ADOPT | Published definition adopted unchanged after verification |
| ADAPT | Source concept modified for event-aligned, partially visible data |
| DERIVE | Mathematical quantity computed from available observations |
| PROJECT | Project operationalization requiring explicit justification |
| REJECT | Candidate excluded as unsupported by the observation model |

Provenance is separate from implementation status. `DERIVED` describes a proposed
computed metric, not a claim that it is implemented; `ADAPT` and `TBD` signal open
decisions. No proposed metric is implemented during this migration.

## Review queue

For each candidate, add verified title, authors, year, identifier/link, relevant
page/section, original definition, raw-data requirements and proposed adaptation.
Review visible geometry, spatial value, defensive regimes and outcome attribution
sources before treating any formula as established football practice.

Continuous tracking-based motion, pitch-control and EPV models are `REJECT` for
faithful reproduction from these event-aligned frames. A future proxy would need
its own definition, limitations and validation; no such proxy exists yet.

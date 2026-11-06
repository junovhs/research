# How we find things we did not expect

## Two entry points, one evidence standard

**Data first:** look for relationships, residual structure, subpopulations, disagreements between measurements, non-detections and unexpected absences. Search across representations, not just for isolated extreme points. A widespread effect may be ordinary-looking in every individual object.

**Question first:** combine physically meaningful measurement, process and method concepts; prioritize coherent combinations neglected by the chosen literature corpus. Generate concrete tests rather than persuasive paragraphs.

The first route can reveal structures outside our existing conceptual vocabulary. The second helps us ask unfamiliar questions. Neither is assumption-free, and neither gets to skip verification.

## Exploration allocation

Start with 50% diversified/random data-first screening, 30% question-driven probes and 20% follow-up. These are adjustable effort allocations, not measured optimal percentages. Do not let follow-up gradually consume all independent exploration. Diversify dataset, sky region, population, representation and timescale when resources permit.

Rare events may require bigger samples. Population effects may require careful conditioning. A small sample's non-detection is only a statement about its sensitivity and selection, not the whole sky.

## Fast funnel

| Stage | Work | Starting budget | Output |
| --- | --- | --- | --- |
| Screen | Cached-table numerical evaluations; reuse shared calculations | Target under 1 second per simple probe; batches target 60 seconds and stop at 180 seconds | Scores, diagnostics, every attempted configuration and failures |
| Challenge | Cheapest plausible artifact/null explanation | Several short batches, not one unbounded run | Reject, inconclusive, or a frozen candidate claim |
| Confirm | New observations, fixed estimator, controls, uncertainty and multiplicity accounting | Escalation only after a useful screening result | Evidence for the specified claim, or rejection |
| Interpret | Literature, physical plausibility, independent dataset/instrument where available | Human/agent investigation of a small shortlist | Known effect, unresolved candidate, or evidence packet for expert review |

The targets above are engineering limits to benchmark, not claims about achieved performance. Enforce hard batch deadlines and preserve completed work. Do not hide expensive downloads in the probe timer.

## A probe is not a discovery

A probe is a numerical evaluation of a declared transformation, relationship, subset or discrepancy on a specified dataset. It is not one astronomical object, one browser search, one API request, one LLM conversation, or necessarily one independent hypothesis.

Aim for many cheap local evaluations per cached data sample. Network operations and agent reasoning happen at batch boundaries. Before quoting a throughput number, state the dataset size, operator, hardware, warm/cold cache state and what exactly was counted.

## Controls that matter

Carry units, errors, censoring and selection information. Examine magnitude, sky position, observing cadence, crowding, instrument/pipeline version and shared derived quantities. Correlations caused by a common input or mathematical identity are not new physical relationships. Missing data is not zero; negative/noisy measurements are not automatically invalid.

Use synthetic injections to test sensitivity and appropriately structured nulls to test false alarms. Shuffle only where exchangeability is justified; preserve spatial, temporal or group dependence when necessary. Check whether the pipeline notices a known effect, but do not hardcode its identity into the discovery ranking.

Searching a million valid null hypotheses at an unadjusted 0.05 threshold would produce an expected 50,000 false positives. Exploration therefore produces leads, not significance claims. For promoted claims, declare the tested family and suitable multiplicity control, or use genuinely independent confirmation with a fixed analysis. Account for repeated adaptive use of data. Splitting random rows is not sufficient when those rows share an object, instrument, field or observing epoch.

An independent dataset strengthens a result only to the extent its errors and selection mechanisms are genuinely independent.

## Minimal result record

Use experiments/template.json as the shape, not a paperwork requirement. Save data source/release, exact query and hash, code revision, seed, probe-generator configuration, all attempts or reproducible attempt ledger, effect sizes, uncertainties when estimated, control outcomes, timings and the next discriminating test.

Statuses are simple: screened, rejected, inconclusive, or candidate. A candidate is not a confirmed discovery. Do not silently discard failed jobs or count them as negative scientific results.

Keep large cached inputs out of Git. Preserve a manifest and retrieval instructions. Download valuable CI results before their retention expires; artifacts are a convenience, not the research record.

# 02 - LIVE STATE - the only current scientific handoff

**Updated:** 2026-10-13. **Latest exploratory decision:** [R-015](../RESULTS/R-015.md) executed a phase-conditioned semidiscrete ODE probe; PARK a general continuous Allen–Cahn solver, and keep only a narrowly scoped phase-label/forcing-tail challenge. R-014 remains the latest broad transfer evidence.  **Purpose:** scientific state remains [R-014](../RESULTS/R-014.md); owner-approved **workflow integrity update** adds reproducible research evidence, decision gates and independent challenge expectations. No new scientific experiment or confirmation was performed by this policy change. The lab now lives in **junovhs/research** (migrated from junovhs/fractodactyl@314abc8; workflow-only, see [MIGRATION.md](../MIGRATION.md)).

## Goal and priority discipline

Find trustworthy, transferable mathematical shortcuts for expensive scientific computation. **No industrial speedup, general nonlinear compiler, certified continuous PDE solver or proven novel algorithm has been demonstrated.** P-051's original frozen MPFR/performance question remains UNTESTED. The owner's anti-tunnel-vision direction remains active: transfer or resolve a substantive obstruction, rather than indefinitely tune a narrow favorable example. Small credible gains remain valid findings; no universal speed threshold is imposed.

## Latest executed evidence

**R-015 (2026-10-13): REPORTED / EXPLORATORY / PREREGISTERED NO / POD NO / NOVELTY UNVERIFIED.** A source-bound three-case, D=16 semidiscrete ODE probe (not continuum PDE) found a small phase-conditioned scalar envelope after an unforced prefix, but a final -0.25 drive moved the positive center to 0.8803950935673981, so a phase-only equilibrium substitute fails. An assumed 0.92 tail contraction rate gives a 5.665865e-10 width estimate, but finite-arithmetic and numerical integration errors are **not certified**, and the phase bit was free. This narrows the question without establishing novel speed or industrial applicability. **Decision: PARK** general validated-PDE development; challenge only a bounded recent-drive scalar certificate with charged phase classification and fallback, versus a validated specialist. **One-agent self-review, no independent reviewer.** No MAP update (unchanged lineage).

## Prior broad transfer evidence

**R-014: REPORTED / EXPLORATORY / PREREGISTERED NO / POD NO / NOVELTY UNVERIFIED.** A standard cubic Allen-Cahn finite-difference Euler recurrence with heterogeneous dyadic initial conditions and piecewise-bilinear correlated forcing was enclosed using its monotone combined stencil and exact directed 40-bit dyadic integer arithmetic. The target is one exact DISCRETE terminal component, not the continuous PDE.

A 48-case transfer grid at D=512,N=16557 admitted **23** and abstained on **25**, with the same admissions for the temporal-only rival. Every full-reference interval lay inside both shortcut intervals. At amplitudes 0.25,0.5,1,2 the admissions were 0/12,0/12,11/12,12/12. Largest admitted width: 6.6848e-10; largest observed lower-endpoint error versus full binary64 replay: 3.3931e-10. The 32-case pilot overlaps the final grid and is disclosed; this is not preregistered validation.

Three fully replayed million-step cases at D=256 used 8192,2048,4096 recent steps. The first needed the whole ring on its final pass; the other two used 65 and 129 sites. Including failed attempts, local work was 2803456,177920,706304 interval cell updates versus 256044288 full-replay updates. Fresh-query local medians were 122.867,8.26266,32.2700 ms; the same-arithmetic temporal-only rival took 185.123,45.1155,96.0986 ms: **1.51x,5.46x,2.98x**, not a gain over a literature-wide best solver. Shortcut medians use seven batches of three calls; full-replay sampling is limited and explicitly disclosed. Startup/import/compilation are excluded.

Checks: 10,000 exact-Fraction endpoint tuples, 5,000 independent input calculations, 20 independent full/patch replays including wrapped boundaries, 1,000 interval inclusion samples and four 90-digit full trajectories. Source, all completed raw samples and reconstruction instructions are delivered separately; no external reproduction or formal program verification is claimed. *(Migration note: that companion was never committed to Git and is NOT_RECOVERED in this repository; only its SHA-256 anchors survive. See [EVIDENCE/LEGACY.json](../EVIDENCE/LEGACY.json).)*

## Two decisive boundaries

**Persistent phase:** for any input with |b|<=3/8, the disjoint boxes [1/2,2]^D and [-2,-1/2]^D are invariant. An all-state omitted-history initialization cannot shrink a queried range below width one, regardless of horizon or precision. A weak-drive numerical enclosure retained separation >1.99315 after 16557 steps. This is an obstruction to this all-state forgetting assumption, not to the well-posed fixed-IVP problem or every phase-aware solver. Amplitude 0.5 failures lie outside that sufficient theorem.

**Discrete versus continuous accuracy:** the 1e-9 certificate bounds omission/finite arithmetic for the exact Euler recurrence. Two independent DOP853 diagnostics found about 1.00e-4 and 1.07e-4 time-discretization differences. No continuous-time or spatial-discretization certificate exists. Do not sell these measurements as a PDE solution accurate to 1e-9.

## Next discriminating research step

**Priority 1: a decision gate, not automatic solver development.** First define the intended computational output (exact discrete terminal component versus continuous physical-model state), accuracy budget, representative query/fallback workload, available forcing, and strongest specialist comparator. Explicitly compare two next directions: (a) continuous-model omission admission via validated/adaptive high-order time integration, including the phase-persistent obstruction; (b) a different transferable computation-elimination mechanism with a clearer economic/scientific task. Choose the cheapest experiment that would *change that priority decision*, not another radius or amplitude tuning pass. Preserve a CONTINUE/CHALLENGE/PARK/CLOSE decision and competitor rationale with the next R-card. Formal confirmation still requires prospective P/PA and challenge review.

R-014 reuses the existing R-013 lineage; no new MAP edge or routine root-document synchronization. Prior art includes maximum-principle schemes, comparison/forgetting and goal-oriented error control; novelty is unverified. Full equations, source inspection, search provenance, raw observations and hash anchors are in R-014 and its companion.

## Preserved history and parked work

R-001 through R-009 retain their negative, scoped or known-method results; no historical gates are rewritten. R-010/R-011's restricted chart construction and outstanding independent interval audit remain parked rather than compulsory next tasks. R-012's unsupported earlier execution claim and genuinely executed later cross-check remain documented in R-013 and its archive correction. R-013 established the rational-lattice omission prototype; its corrected archive remains intact. P-040/P-060 are optional ingredients, not mandatory fallback contests.

## Recent handoff decisions (maximum three)

- **2026-10-13 - R-015:** phase-conditioned semidiscrete terminal probe; recent forcing invalidates equilibrium-only shortcut. PARK broad PDE development; only narrow specialist-aware phase/tail falsifier remains. Self-review only; no MAP trigger.

- **2026-10-13 - R-014:** partial transfer to correlated-drive Allen-Cahn discrete queries; 23/48 admissions, three million-step references, matched rival, invariant-phase obstruction and measured discretization gap. Next: total continuous-model error, not toy tuning. No MAP trigger.
- **2026-10-13 - R-013:** space-time terminal-query omission with archived reconstruction, a persistent-memory counterexample and temporal-only rival. One provisional direction remains in MAP.md.

## Update rule

An ordinary meaningful exploratory session updates this file and one new R-card or linked correction, plus source-bound EVIDENCE/R-NNN/ when calculations were executed, in one pull request into `main` of junovhs/research that passes `lab-checks`. MAP.md changes only for an evidence-backed structural trigger. Keep mathematics, tables, searches and reconstruction in RESULTS. Read all four AGENTS-READ-THIS files each session and follow [03-WRITEBACK-CHECKLIST.md](03-WRITEBACK-CHECKLIST.md). Never routinely synchronize other historical root documents.

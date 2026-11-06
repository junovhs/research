# Build the smallest working discovery loop

No calendar roadmap, feature backlog, or platform build. Complete these in order, stopping to change course when evidence warrants it.

## 1. One real sample, one measured run

Implement a read-only public-catalog adapter with a documented sampling scheme, timeout, download cap and content hash. Start with about 10,000 rows and a modest set of measurements, errors and quality metadata. Gaia is a candidate starting point, not a commitment about what we should discover. Verify its current schema and query documentation before coding.

Do not call an arbitrary TOP-N result representative. Use a documented random or stratified design, record exclusions, and keep confirmation observations separate. Do not access the confirmation data during initial exploration.

Implement a few cheap probes over the cached table: relationships and conditional residuals, subpopulation structure, and missingness/quality disagreements. Begin with ordinary statistics, not trained neural networks. Include known-signal and null controls. Benchmark elapsed time, peak memory, bytes transferred, actual probe count and timeout behavior.

**Done:** one command produces a reproducible report from real data, including negative results and controls. No astronomical novelty is required. This is the next implementation task.

## 2. Make exploration broad and cheap

Add a seeded probe generator over features, transformations and justified strata. Separate random exploration from adaptive follow-up. Cache shared computations and batch numerical operations; do not make a process or network call per probe. Track feature provenance so algebraic identities and reused measurements do not masquerade as discoveries.

Scale from hundreds to thousands of useful evaluations only after measuring throughput. A million evaluations is an eventual benchmark target, not a promise or a requirement that every run meet it. Never equate more tests with more evidence.

**Done:** resumable batches respect budgets and do not quietly drop failures; a few top candidates can be reconstructed exactly.

## 3. Bring in the actual Alien program

Follow ALIEN.md. Inspect and pin the official code, then attempt its smallest CPU-supported demonstration on the owner's machine inside a separate dependency environment. Record the actual runtime and whether it needs external model calls. Do not spend weeks retraining before the astronomy loop works.

Create a small, source-linked astronomy concept set. Have subscription agents turn selected combinations into testable batch specifications. Treat any lightweight availability score as a proxy, not a validated reproduction. Compare the proposed ranking with random combinations and ordinary agent ideation on the same feasibility budget.

**Done:** at least one traceable Alien-inspired proposal enters the same data-and-falsification loop as a data-first surprise.

## 4. Investigate survivors; add bounded CI only where useful

Freeze one candidate claim and test it on untouched observations. Check known literature, instrument effects and selection explanations. Escalate only when cheaper tests cannot discriminate.

Once a real integration test exists, enable at most two short daily GitHub validation/reproducibility runs. Their purpose must be testing this repository's software; do not disguise a general compute farm as CI. Keep discovery workloads portable to bounded local sessions. GitHub's policy is the boundary, not a free-minute counter.

**Done:** a candidate is rejected, remains explicitly inconclusive, or has a compact reproducible evidence packet. Update STATE.md; choose the next shortest useful test.

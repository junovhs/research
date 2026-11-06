# Using Alien Space of Science without pretending we reproduced it

## Primary sources

- Paper: [The Alien Space of Science: Sampling Coherent but Cognitively Unavailable Research Directions](https://arxiv.org/abs/2603.01092), version 3 dated 2026-10-21.
- Authors' code: [alejandrohdez00/alien-space-of-science](https://github.com/alejandrohdez00/alien-space-of-science).

Source identities and the paper abstract were checked on 2026-11-06. This repository has not yet run or benchmarked their code.

## What we are borrowing

The paper separates scientific coherence from the likelihood that existing researchers/communities would produce a combination. It extracts conceptual atoms from papers and ranks combinations for coherence and low availability. Its reported evaluation concerns machine-learning research; it does not establish astronomical discovery performance.

Our target is the same kind of neglected question, but testable with existing astronomical observations. Add a feasibility screen after idea generation: identifiable data, observable prediction, cheap initial test, possible confounders and a clear rejection criterion. Keep some low-ranked/random proposals to detect biases in our own ranking.

## Actual program, bounded attempt

An agent should inspect the official README, license, inference entry points, dependency sizes and current model download requirements; pin the inspected commit. Attempt a small CPU demonstration only if it fits the owner's budget. A claimed CPU option is not a benchmark on our hardware. Stop rather than quietly rent GPUs or make paid API calls.

Existing ML-domain vocabularies/checkpoints must not be relabeled as astronomy models. Upstream proposal reconstruction may require a model service; interactive subscription-agent reconstruction is a substitution and must be recorded as such. Do not route subscription sessions through an unofficial API.

## Lightweight astronomy adaptation

Start with a small cross-subfield corpus and source-linked atoms covering observables, methods, physical processes, data selection and instrument behavior. Include author/community information only with transparent provenance. In short interactive batches, use the owner's agents to assess coherence and make selected combinations executable.

Co-occurrence rarity and author/community coverage can serve as cheap availability proxies. They measure gaps in our corpus, not what all scientists have thought. Random combinations and ordinary agent brainstorming are baselines, not forbidden approaches. Compare feasibility, diversity, runtime and independently testable results before trusting the ranking.

Any version without the published models/training/evaluation is **Alien-inspired**, not a reproduction. A temporal paper split also does not prevent a pretrained LLM from already knowing later discoveries; disclose that leakage and avoid inflated retrospective claims.

The science loop must continue while this adaptation develops. Do not make a large literature ingestion or retraining project a prerequisite for looking at data.

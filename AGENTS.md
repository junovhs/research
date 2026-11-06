# Instructions for research and coding agents

Read CONSTITUTION.md, OWNERSHIP.md, STATE.md and config/budget.json first. Read PLAN.md for the approach and LOG.md for what's been seen. Then do the next useful executable task. Do not start by rewriting the plan.

The owner wants exploration, not bureaucracy. Write the least documentation the next dig needs: a LOG.md entry per look, and a manifest for any fetched data. Don't add planning documents; Ishoo holds the plan and issues.

## Work style

- Test fast and fail fast. Start with a small cached sample and the cheapest discriminator. Keep at most three active investigations. Park expensive or inconclusive ideas with one sentence explaining why.
- Preserve open exploration. Do not quietly turn this project into a fixed object detector, a favorite-theory verifier, or a hunt for large anomaly scores.
- Use the owner's subscription coding tools interactively. Ordinary scripts consume saved JSON/CSV/Parquet; they do not depend on paid LLM APIs. Do not automate browser logins or repurpose subscription credentials into an unsupported API.
- Execute on the owner's machine or approved GitHub workflows, not ChatGPT's internal environment. No GPU or continuously running process is assumed.
- Make one small end-to-end vertical slice work before building abstractions. Default to Python, files and the standard library; add numerical dependencies when the first experiment needs them. Use Rust only after profiling.

## Scientific discipline

Keep measurements, interpretations and novelty claims separate. Verify sources rather than inheriting factual claims from past chat. Flag proposed ideas as proposals and software benchmarks as benchmarks.

Record every attempted test, not just winners. Screening scores are not calibrated probabilities. Treat data-quality flags, missingness, uncertainty, sky position, magnitude, selection and instrument metadata as possible explanations, not automatic reasons to discard data.

For a survivor, freeze a minimal claim and rejection criterion before accessing a new confirmation sample. Compare with appropriate controls; account for the number and dependence of tests. Do not repeatedly tune against the same holdout and call it independent validation.

Respect archive rate limits and retry/backoff guidance. Many local probes should reuse a few queries. Do not download an entire catalog to avoid learning its query interface.

## Boundaries

Routine work inside the budget needs no approval. Stop and report before spending money, increasing limits, running long unattended workloads, contacting researchers, publishing a discovery claim, or changing account settings. Never upload secrets, model-session cookies, personal data or large raw datasets.

Use a small PR when main is protected. Run the real checks; never fabricate passing status. At handoff, update STATE.md and link the actual result or failure. Do not claim a test ran because you wrote it.

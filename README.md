# Alien Astronomy

**Find reproducible surprises in public astronomical data, including patterns and relationships we did not know to look for.**

One person. Subscription-based AI coding agents. Ordinary consumer hardware. Short, resumable experiments. No paid model APIs, GPU requirement, always-on machines, or ChatGPT-hosted computation.

This is a replacement project, not a continuation of the previous repository contents. No previous research, results, instructions, or code are incorporated.

## Start here

Read [CONSTITUTION.md](CONSTITUTION.md), [OWNERSHIP.md](OWNERSHIP.md), then [STATE.md](STATE.md). Coding agents also read [AGENTS.md](AGENTS.md).

[PLAN.md](PLAN.md) is the short implementation path. [METHOD.md](METHOD.md) describes the discovery loop. [ALIEN.md](ALIEN.md) separates the published Alien Space of Science method from our proposed adaptation. [config/budget.json](config/budget.json) contains initial resource limits.

## The loop

Acquire a small, reproducible public-data sample once. Run many cheap numerical probes against that cached sample. Record failures and null results as well as promising ones. Let AI investigate only the most informative survivors. Test survivors on untouched data and against instrumental and statistical explanations.

Explore data first as well as questions first. Do not decide in advance that the answer must be a brown dwarf, planet, new object class, or new physics.

**A million numerical evaluations is not a million discoveries, independent hypotheses, archive queries, or model calls.** Measure throughput before scaling. Do not optimize for impressive counters.

## What exists now

A concise project contract, experiment template, budgets, and an executable repository/configuration check. The astronomy-data adapter, probe engine, and Alien adaptation are not implemented yet. There are no scientific findings.

Run the current check on your computer:

```sh
python3 tools/check_project.py
```

CI runs that same check. The proposed twice-daily research-software integration runs are not enabled until an actual bounded integration test exists. No subscription credentials are stored in GitHub.

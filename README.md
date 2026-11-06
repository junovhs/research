# Alien Astronomy

**Find reproducible surprises in public astronomical data, including patterns and relationships we did not know to look for.**

One person. Subscription-based AI coding agents. Ordinary consumer hardware. Short, resumable experiments. No paid model APIs, GPU requirement, always-on machines, or ChatGPT-hosted computation.

This is a replacement project, not a continuation of the previous repository contents. No previous research, results, instructions, or code are incorporated.

## Start here

Read [CONSTITUTION.md](CONSTITUTION.md), [OWNERSHIP.md](OWNERSHIP.md), then [STATE.md](STATE.md). Coding agents also read [AGENTS.md](AGENTS.md).

[PLAN.md](PLAN.md) is the approach: pick three spots in the sky and dig down them layer by layer, asking questions nobody has asked. [LOG.md](LOG.md) is the field notebook. [METHOD.md](METHOD.md) describes the discovery loop. [ALIEN.md](ALIEN.md) separates the published Alien Space of Science method from our proposed adaptation. [config/budget.json](config/budget.json) contains initial resource limits.

## The loop

Acquire a small, reproducible public-data sample once. Run many cheap numerical probes against that cached sample. Record failures and null results as well as promising ones. Let AI investigate only the most informative survivors. Test survivors on untouched data and against instrumental and statistical explanations.

Explore data first as well as questions first. Do not decide in advance that the answer must be a brown dwarf, planet, new object class, or new physics.

**A million numerical evaluations is not a million discoveries, independent hypotheses, archive queries, or model calls.** Measure throughput before scaling. Do not optimize for impressive counters.

## What exists now

Three fixed needles, a sealed confirmation field, bounded Gaia DR3 and AllWISE adapters, checksum-verified caches, spherical crossmatching with shifted controls, exploratory probes, and an Alien-inspired question map. No discovery or novelty claim has survived confirmation; the confirmation field is untouched.

Dig either open field from a fresh checkout with Python 3.12 and no extra packages:

```sh
python tools/layers.py --needle calibration --output data/calibration.json
python tools/layers.py --needle exploration --output data/exploration.json
python tools/layers.py --needle exploration --offline --output data/replay.json
```

Raw observations and request ledgers stay outside Git in `~/.cache/research-needles`; set `NEEDLE_CACHE` to use another external directory. Each report includes exact queries, checksums, code provenance, every probe attempted, controls and all candidate/nonmatch IDs. `--offline` requires valid cache and never fetches observations. A catalog nonmatch is not a new object; infrared adds wavelength coverage rather than a universal depth limit. Declared download/time/cache limits are in `config/budget.json`; large brute-force matches fail explicitly.

Read the actual results in [experiments/first-dig.json](experiments/first-dig.json), [experiments/question-map.json](experiments/question-map.json), and [LOG.md](LOG.md). The initial catalog calibration recovers 77/78 published Gaia-AllWISE pairs in GOODS-South and 208/210 in exploration; the three misses lie beyond the fixed 2-arcsecond match radius. That checks catalog associations, not a new physical discovery.

After both open fields are cached, run `python tools/questions.py --output data/questions.json` for the question map, or add `--offline` to reuse literature cache. It produces 20 runnable comparisons with physical rationales, metadata co-mention counts and random baselines, then runs three on each field. It is not a reproduction of Alien's learned models. Keyword zeros cannot establish novelty.

Check locally with `python -m unittest discover -s tests -v` and `python tools/check_project.py`. GitHub Actions has a manual **Bounded needle dig** workflow for a cold-cache two-layer dig and offline replay; it has a ten-minute timeout, one research job at a time and seven-day artifacts. No schedule, paid APIs or subscription credentials are used.

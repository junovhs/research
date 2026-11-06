# The dig

Pick a spot in the sky. Dig straight down it, one survey layer at a time. At each depth, look around and ask what nobody has asked. Then either "hmm, that's weird, look closer" or "nothing at this depth, moving on."

Ishoo holds the live plan and issues. This page is the idea, and it stays short.

## Three needles

- **Calibration:** a well-studied deep field where the answers are known. If the dig can't rediscover what's published there, the dig is broken.
- **Exploration:** a seeded random spot with decent public coverage across surveys. This is where we dig for real.
- **Confirmation:** chosen up front with similar coverage, and not touched until a claim is frozen. A second line of sight is the cure for one-needle flukes.

## Layers

Each layer is one public survey of the needle's circle: Gaia first, then deeper optical and infrared, then X-ray and radio as coverage allows. Fetch a bounded sample once, cache it outside Git with a hash, and cross-match it to the layers above. Keep unmatched objects, because things that appear in one survey and not another are often the interesting ones.

Going deeper means going fainter, so each layer's detection limit is built into every comparison. Populations that "change with depth" usually change because faint things drop out.

## Two ways of asking

- **Data first:** cheap probes over a layer, such as relationships, residuals, clumps, missingness and flag disagreements, each against a null.
- **Unasked questions** (Alien-inspired; see [ALIEN.md](ALIEN.md)): list combinations of what the needle actually measures ("compare A with B", "A only within B", "could A and B be related?"). An agent judges whether each could mean something physically. A script counts how often the literature mentions both together. Coherent and rarely asked goes to the top, and a few random combinations ride along as a baseline.

Both feed the same probes and the same log.

## The log

[LOG.md](LOG.md) is the field notebook: one dated line or short paragraph per look. Write down what was looked at, at what depth, and whether it was weird or nothing. Nulls count. A lead that survives gets a frozen claim and goes to the confirmation needle.

That's it. Anything that isn't digging, asking or checking needs a reason to exist.

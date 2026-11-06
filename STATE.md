# Current state

Updated: 2026-11-06.

The owner repurposed the repository for open astronomical exploration. The live plan is Ishoo's First dig; use Ishoo to land directly on main, with no PRs (owner instruction in the interrupted session). Historical Git/PR records remain; no history rewrite has been performed.

DIG-01: config/needles.json freezes a six-arcminute GOODS-South calibration circle and seeded southern exploration/confirmation circles. Selection is uniform in RA and sin(dec) within a declared southern window, rejects low Galactic latitude and nearby fields, and inspects no source data. All-sky Gaia/AllWISE coverage is intended; deeper optical overlap remains unverified. Confirmation is sealed in tools/dig.py. Coordinates are not themselves confirmation observations.

Ran: deterministic selection, spherical separation edge cases, and holdout safeguard tests. Removing the guard makes the safeguard test fail. No scientific observations fetched yet. Next: bounded Gaia TAP fetch, checksum cache, manifest and real-data probes. No novelty claim, no scheduled work, no paid APIs.

DIG-02: real Gaia DR3 downloaded through ARI after ESA HTTP 503. Calibration: 99 sources, SHA256 bdfa59a6e59dd11a6f3addee14ead3917a48a5f720cc697bff8dd8ed912db77a. Exploration: 344 sources, SHA256 f8c4454e3813eb9dc68b7ce29590096ad6c39935486bfc36471dbac9160e96ab. Portable manifests and raw CSV live in the owner's ~/.cache/research-needles (not Git); attempts.jsonl retains failed requests too. `python tools/dig.py gaia --needle exploration --offline` replays locally. Manual .github/workflows/dig.yml performs bounded fetching and offline replay, with seven-day artifacts and no schedule. Seven tests cover real local HTTP, offline replay with server stopped, corruption, cone/schema validation, size cap, and confirmation protection; removing checksum validation makes its test fail. Next: DIG-03 probes; an end-to-end astronomical calibration rediscovery is still pending.

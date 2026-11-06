# Current state

Updated: 2026-11-06.

The owner repurposed the repository for open astronomical exploration. The live plan is Ishoo's First dig; use Ishoo to land directly on main, with no PRs (owner instruction in the interrupted session). Historical Git/PR records remain; no history rewrite has been performed.

DIG-01: config/needles.json freezes a six-arcminute GOODS-South calibration circle and seeded southern exploration/confirmation circles. Selection is uniform in RA and sin(dec) within a declared southern window, rejects low Galactic latitude and nearby fields, and inspects no source data. All-sky Gaia/AllWISE coverage is intended; deeper optical overlap remains unverified. Confirmation is sealed in tools/dig.py. Coordinates are not themselves confirmation observations.

Ran: deterministic selection, spherical separation edge cases, and holdout safeguard tests. Removing the guard makes the safeguard test fail. No scientific observations fetched yet. Next: bounded Gaia TAP fetch, checksum cache, manifest and real-data probes. No novelty claim, no scheduled work, no paid APIs.

# 00 · READ ALL OF THIS FOLDER FIRST

**Mandatory full-read folder** for every agent working in the Dynamics Transfer Lab.

Read **each** file below completely, **in this order**, at the beginning of every session. Do not skim, truncate, skip passages, replace reading with a summary, or read only the files that sound relevant:

1. [00-START-HERE.md](00-START-HERE.md) — this document and authority boundaries.
2. [01-RULES-AND-METHOD.md](01-RULES-AND-METHOD.md) — scientific mission, evidence standards, and hard limits.
3. [02-LIVE-STATE.md](02-LIVE-STATE.md) — the one live scientific frontier, status, and handoff.
4. [03-WRITEBACK-CHECKLIST.md](03-WRITEBACK-CHECKLIST.md) — complete requirements before and after each research session.

**This directory is deliberately kept small.** All Markdown files directly in this folder are compulsory to read in full; no experiment logs, dossiers, scripts, or expanding archives belong in it. Add a new compulsory document only when a genuinely new permanent rule cannot fit an existing one.

## Single-source-of-truth rule

- These four files are **authoritative** for operations and the live scientific state. The root AGENTS.md and CLAUDE.md are identical entrypoint pointers, not alternative policy sources.
- Other root Markdown files (including README.md, GOAL.md, FRONTIER.md, METHOD.md, INDEX.md, SOURCES.md, PRIOR_ART.md, PROOF_OF_DONE.md and LEAN.md) are **optional, preserved historical/reference snapshots**. **MAP.md is the one event-curated exception:** a selective lineage graph, not the current frontier or an exhaustive P/R index; it changes only on the evidence-backed structural triggers in 03-WRITEBACK-CHECKLIST.md. None of these documents requires routine synchronization. If old process guidance conflicts, follow this folder.
- PROMPTS/, RESULTS/, PRIOR_ART/ and TEMPLATES/ are on-demand records, frozen questions, preregistrations and samples. Historic gates, measurements and provenance cannot be rewritten.
- EVIDENCE/R-NNN/ may contain small, text-based experiment sources, configuration, execution manifests, tests and compact raw records; scripts/ may contain shared research-only validation helpers; .github/ holds the lab's CI. This is the owner's 2026-10-13 exception to the earlier documentation-only convention. No renderer, compiled binaries, build outputs or dependencies are allowed. The lab remains research-only. EVIDENCE/LEGACY.json freezes the imported historical records and registers companion archives that were never committed (see MIGRATION.md).
- The full mathematical details and source links for a new experiment go **in its R-card**, not in this compulsory folder. Keep 02-LIVE-STATE.md concise with pointers to those records.

## Normal change surface

A normal executed exploratory session updates **two narrative files**, plus a minimal source-bound evidence package when there was execution:
- a **new immutable-style report** in RESULTS/R-NNN.md (or a linked correction to an existing report, clearly marked); and
- [02-LIVE-STATE.md](02-LIVE-STATE.md) for the latest finding, active direction, and next falsifier;
- **EVIDENCE/R-NNN/** (or a genuinely durable externally retrievable archive whose URI and hash are verified) for sources/configuration/manifest and relevant raw output. Evidence files are NOT a license for general product code or housekeeping.

Deliver these files as **one pull request into `main`**; the `lab-checks` CI must pass before merge. No other existing file should be updated for routine session housekeeping. Never invent an R-card or evidence run when no calculation was executed. **Exception when lineage materially changes:** update MAP.md together with the new R-card and live state in the same commit, or with live state alone if a documented reassessment of existing evidence changes the graph without a new experiment. A P/R ID, small incremental improvement or routine status change is not itself a trigger. Formal preregistration is a separate exception detailed in the checklist. A session that produces no new evidence or structural decision may have **no Git changes**; never invent work to fill the form.

## Non-negotiable scope

Only the repository **junovhs/research**. Its default branch **`main`** is the lab's research history (it has no relationship to Fractodactyl's `main`). Work on a short-lived branch (for example `r-015-<topic>` or `workflow-<topic>`), open a pull request into `main`, and merge only after the required `lab-checks` CI passes. Never push directly to, force-push, rewrite or delete `main`. Research documentation plus the narrow, owner-approved source/evidence exception above.

**junovhs/fractodactyl is out of scope.** The lab originated there on branch research/dynamics-transfer-lab (preserved as a read-only historical backup; see MIGRATION.md). Never write to Fractodactyl, its branches or its settings unless the owner separately authorizes a specific task. Historical GitHub links into Fractodactyl inside RESULTS/, PRIOR_ART/ and other records are citations of where pretest commits were made; they are not instructions to work there.

Do not add Fractodactyl renderer code, compiled executables, third-party dependencies or generated binaries. Compute in a scratch environment and commit only small, reviewable research text/source/configuration/raw evidence. If a mandatory document cannot be read in full, report the limitation rather than proceeding on a truncated view.

This organization was installed **2026-10-13** as a documentation-workflow change, not a scientific discovery. On **2026-10-13** the lab was migrated from junovhs/fractodactyl@314abc8 into this repository with CI-enforced evidence checks; that migration is also workflow-only (see MIGRATION.md).

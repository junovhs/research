# Next agent: please do

Follow-ups that the 2026-10-13 migration (junovhs/fractodactyl@314abc8 → junovhs/research) could not complete from its environment. Each item names who can do it. Remove an item by pull request once it is done **and verified**. This is not a research task list; scientific priority lives only in [AGENTS-READ-THIS/02-LIVE-STATE.md](AGENTS-READ-THIS/02-LIVE-STATE.md).

## Owner actions (an agent cannot do these; the migration session's GitHub proxy returned HTTP 403)

1. **Turn on branch protection for `main` (most important).** Nothing is enforced yet: CI runs and reports, but a direct push or a red PR can still land. Go to *Settings → Rules → Rulesets → New branch ruleset*:
   - Name `protect-main`, Enforcement **Active**, Target **Default branch**, bypass list **empty**.
   - Enable **Restrict deletions** and **Block force pushes**.
   - Enable **Require a pull request before merging** (0 approvals is fine for a solo owner; turn on "Require conversation resolution").
   - Enable **Require status checks to pass**, add the check **`evidence-and-structure`** (from the GitHub Actions app), and tick "Require branches to be up to date".
   - Verify afterwards: a test `git push origin main` should be rejected, and a PR with failing `lab-checks` should show "Merging is blocked".
   - (Optional) *Settings → General*: enable "Automatically delete head branches".
2. **Delete leftovers of the old repository contents**, which the proxy would not let an agent remove: branch `docs/add-scaffolding-plan-v3` and tag `template` (old app history). Also delete the closed demo branch `ci-demo/evidence-pass-fail`. Each is reachable from *Code → Branches / Tags*.
3. **Workflow-push permission.** The migration's push of `.github/workflows/` succeeded, so no action is needed unless a future agent's push is rejected for "workflow scope".
4. **Old research branch in Fractodactyl:** see "Archiving the old branch" below. Do not change Fractodactyl settings without checking the effect on its main development.

## If the owner still has the ChatGPT companion bundles

[EVIDENCE/LEGACY.json](EVIDENCE/LEGACY.json) lists the R-013 original, R-013 reconstruction and R-014 companions as `NOT_RECOVERED`, with their historical SHA-256 anchors. If you have the files, put the anchored files under each entry's `recovered_path`, change its `status` to `RECOVERED` and open a PR; CI then checks every file against its historical hash. Never regenerate or substitute samples. Files over 2 MB need a durable external archive instead (record the URI and SHA-256 in a new linked correction file, after actually retrieving it once).

## Archiving the old branch in Fractodactyl (low-risk, later, owner-approved)

Keep `research/dynamics-transfer-lab` in junovhs/fractodactyl as a read-only backup; its pretest commits are cited by R-006 to R-009 and PA-P-083. Lowest-risk options, in order:
1. Add a Fractodactyl ruleset that targets only `refs/heads/research/dynamics-transfer-lab`, with "Restrict updates", "Restrict deletions" and "Block force pushes". It does not touch `main` or any other branch. Confirm that the ruleset's target list names only that one branch before saving.
2. Optionally push a tag such as `archive/dynamics-transfer-lab-314abc8` at `314abc8afd5b89915a215f30c07692f77d6b3dec`, so the provenance survives even if the branch is later removed.
3. Do not delete or rename the branch while historical links point into it.

## Known limitations to keep in mind (not tasks)

- CI checks evidence integrity, structure and the append-only rule only. It cannot check mathematics, error bounds, comparator fairness or the retrievability of an external URI.
- The append-only check (`--base`) applies to pull requests. Until item 1 is done, a direct push to `main` bypasses it; the full-tree check still catches edits to the frozen pre-migration records.
- "Distinct challenge review" is a process rule (03-WRITEBACK-CHECKLIST.md). With a solo owner, GitHub cannot require a second human approver; if you want it, add a reviewer and set required approvals to 1 in the ruleset.

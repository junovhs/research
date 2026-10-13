# Next agent: please do

Follow-ups that the 2026-10-13 migration (junovhs/fractodactyl@314abc8 → junovhs/research) could not complete from its environment. Each item names who can do it. Remove an item by pull request once it is done **and verified**. This is not a research task list; scientific priority lives only in [AGENTS-READ-THIS/02-LIVE-STATE.md](AGENTS-READ-THIS/02-LIVE-STATE.md).

## Owner actions

1. **Workflow-push permission.** The migration's push of `.github/workflows/` succeeded, so no action is needed unless a future agent's push is rejected for "workflow scope".

## If the owner still has the ChatGPT companion bundles

[EVIDENCE/LEGACY.json](EVIDENCE/LEGACY.json) lists the R-013 original, R-013 reconstruction and R-014 companions as `NOT_RECOVERED`, with their historical SHA-256 anchors. If you have the files, put the anchored files under each entry's `recovered_path`, change its `status` to `RECOVERED` and open a PR; CI then checks every file against its historical hash. Never regenerate or substitute samples. Files over 2 MB need a durable external archive instead (record the URI and SHA-256 in a new linked correction file, after actually retrieving it once).

## Known limitations to keep in mind (not tasks)

- CI checks evidence integrity, structure and the append-only rule only. It cannot check mathematics, error bounds, comparator fairness or the retrievability of an external URI.
- The append-only check (`--base`) applies to pull requests. The `protect-main` ruleset (done 2026-10-13) requires a pull request with a passing `evidence-and-structure` check, so a direct push to `main` is rejected.
- "Distinct challenge review" is a process rule (03-WRITEBACK-CHECKLIST.md). With a solo owner, GitHub cannot require a second human approver; if you want it, add a reviewer and set required approvals to 1 in the `protect-main` ruleset.

## Done (2026-10-13, verified)

- junovhs/research ruleset `protect-main` (id 25036144): active on the default branch, empty bypass list, restrict deletions, block force pushes, require a pull request (0 approvals, conversation resolution), require `evidence-and-structure` (GitHub Actions) with up-to-date branches. A test `git push origin main` was rejected with GH013; `main` stayed at `fb2e14b`. "Automatically delete head branches" is on.
- Deleted from junovhs/research: branches `docs/add-scaffolding-plan-v3`, `ci-demo/evidence-pass-fail` and the merged `workflow/migration-followups`; tag `template`.
- junovhs/fractodactyl: tag `archive/dynamics-transfer-lab-314abc8` at `314abc8afd5b89915a215f30c07692f77d6b3dec`, and ruleset `archive-dynamics-transfer-lab` (id 25036177) targeting only `refs/heads/research/dynamics-transfer-lab` with restrict updates, restrict deletions and block force pushes. Fractodactyl `main` has no rules applied. The branch was not deleted or renamed.

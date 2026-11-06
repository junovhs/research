# Current state

Updated: 2026-11-06.

## Established

The owner requested a complete replacement of the previous project without a backup or preserved legacy files. The new scope is open-ended astronomical discovery on public data, using subscription agents, bounded consumer-computer sessions and modest policy-compliant CI.

The content reset was merged in PR #31. The current project contains only newly written files: constitution, responsibility contract, agent guidance, lean plan, scientific method, Alien adaptation notes, budgets, experiment template and a runnable configuration check. No previous research/code/results are incorporated. No backup branch or archive was created.

The configuration/link check and Python compile check passed in GitHub Actions. The cleanup job also passed: it deleted all eight old non-main branches and 54 earlier workflow runs. The reset PR branch was removed as well. No old tags, releases, caches, artifacts or open conversations required additional deletion. The one-time destructive workflow and script have now been removed from the current project tree.

## Remaining reset limitation

Git commit history and historical GitHub PR records still exist. The active protect-main ruleset forbids history replacement; this connection cannot change that rule or erase GitHub-controlled PR refs. This is an access limitation, not a preservation policy. Do not claim the repository has a new parentless history.

For a history reset, the owner must change the protection rule and use an authorized administrative workflow. Even rewriting main does not itself delete historical PR refs, external clones or GitHub's retained objects.

## Scientific status and next action

No astronomy adapter or discovery engine has run. There are no scientific results and no measured search throughput yet.

Implement the first real-data vertical slice in PLAN.md: a bounded catalog query, cached sample with provenance, a few numerical probes with null/positive controls, and a measured report. Benchmark before scaling. Run on the owner's machine, not ChatGPT's environment.

Not yet implemented: archive adapter, probe runner, holdout management, actual Alien inference, astronomy-specific scoring or scheduled scientific integration tests. Enable at most two short daily validation runs only once there is useful software/data integration work to validate; do not repeatedly schedule placeholder checks.

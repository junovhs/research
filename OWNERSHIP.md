# Ownership and responsibility contract

This is an operational agreement, not a legal transfer of intellectual-property rights. The four entities have distinct responsibilities.

| Entity | Owns | Does not own |
| --- | --- | --- |
| Human project owner | Mission, priorities, accounts, access, spending, resource ceilings, licensing decisions, collaboration and publication decisions; continuity across sessions | Manually approving every small probe, writing every script, or supervising a continuously running machine |
| AI coding/research agents | Literature/source checks, experimental proposals, implementation, tests, candidate investigation, adversarial review, concise handoff; honest distinction between observed and inferred | Unapproved spending, account/policy changes, credentials redistribution, final scientific authority, publication or outreach without approval |
| Project software | Deterministic data access, caching, numerical probes, budget enforcement, provenance, attempt ledger, checkpoints and machine-readable results | Choosing the mission, inventing results, declaring novelty, changing its own limits or treating a score as a physical explanation |
| GitHub Actions | Bounded software checks, regression/integration tests, reproducibility checks, release/report generation where consistent with GitHub terms, logs and temporary artifacts | Unlimited research compute, a permanent agent, model reasoning, access to subscription logins, or the only durable copy of evidence |

## Decision rights

Agents may browse public sources, edit project code and documents, run bounded local experiments, and merge passing routine work through the repository's normal controls. They need not ask permission to reject an idea or fix a bug.

The human decides changes to the spending/resource contract, external sharing or contact, licensing, destructive future resets, and scientific claims made publicly. Approval of this initial replacement is not standing permission to delete future findings.

Use one agent as investigator and another session as skeptic when helpful. Two models agreeing is not independent experimental evidence. One writer at a time per experiment avoids file collisions; no manager-agent hierarchy is required.

## Durable ownership of state

Git holds code, plans, small manifests and concise reports. Cached observations and large intermediate outputs stay outside Git and have checksums and retrieval instructions. AI conversations and expiring Actions artifacts are not authoritative project memory.

Every session ends with a short update to STATE.md: what actually ran, what it showed, what remains unknown, and the next executable action. One result record per batch is enough when it contains the full attempted-probe ledger or a reproducible generator plus seed and completion information.

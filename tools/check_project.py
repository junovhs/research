"""Validate the initial project contract and configuration; no scientific work."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def check_project() -> list[str]:
    errors: list[str] = []
    documents = (
        "README.md", "CONSTITUTION.md", "OWNERSHIP.md", "AGENTS.md",
        "CLAUDE.md", "PLAN.md", "LOG.md", "METHOD.md", "ALIEN.md", "STATE.md",
        "experiments/README.md",
    )
    for relative in documents:
        path = ROOT / relative
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"Missing or empty document: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^\s)]+)\)", text):
            if "://" in target or target.startswith("#") or target.startswith("mailto:"):
                continue
            linked = path.parent / target.split("#", 1)[0]
            if not linked.exists():
                errors.append(f"Broken local link in {relative}: {target}")

    budget = json.loads((ROOT / "config/budget.json").read_text(encoding="utf-8"))
    template = json.loads((ROOT / "experiments/template.json").read_text(encoding="utf-8"))
    if budget["schema_version"] != 1 or template["schema_version"] != 1:
        errors.append("Unsupported configuration schema")
    for key in ("additional_spend_usd", "llm_api_calls"):
        if budget[key] != 0:
            errors.append(f"Initial no-additional-spend contract violated: {key}")
    for key in ("gpu_required", "chatgpt_internal_execution"):
        if budget[key] is not False:
            errors.append(f"Initial execution contract violated: {key}")
    if not 0 < budget["target_batch_seconds"] <= budget["max_batch_seconds"] <= 180:
        errors.append("Invalid batch limits")
    if not 0 < budget["max_ci_job_minutes"] <= 10:
        errors.append("Invalid CI job duration")
    if not 0 <= budget["max_scheduled_ci_runs_per_day"] <= 2:
        errors.append("Invalid recurring CI limit")
    if budget["ci_concurrency"] != 1 or budget["max_network_concurrency"] != 1:
        errors.append("Initial concurrency must be one")
    fractions = [budget[k] for k in ("exploration_fraction", "question_fraction", "followup_fraction")]
    if not all(0 <= value <= 1 for value in fractions) or not math.isclose(sum(fractions), 1.0):
        errors.append("Exploration fractions must sum to one")
    if budget["exploration_fraction"] < 0.5:
        errors.append("Independent exploration allocation is below the initial minimum")
    if template["status"] != "not-run" or template["execution"]["attempted_probes"] != 0:
        errors.append("The blank experiment template must not claim execution")
    for key in ("data", "execution", "evidence", "conclusion", "next_discriminating_test"):
        if key not in template:
            errors.append(f"Missing experiment field: {key}")
    return errors


def main() -> int:
    try:
        errors = check_project()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Project check could not complete: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Project documents, local links, budget, and experiment template validated.")
    print("This is a software/configuration check, not a scientific experiment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

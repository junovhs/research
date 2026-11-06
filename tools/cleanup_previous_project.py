"""One-time owner-authorized deletion of prior project state. No backups."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if repo != "junovhs/research" or os.environ.get("GITHUB_EVENT_NAME") != "push":
        raise RuntimeError("Not the authorized reset event")
    if not event.get("head_commit", {}).get("message", "").startswith("Reset Research for Alien Astronomy"):
        raise RuntimeError("Not the authorized reset commit")
    if os.environ.get("GITHUB_RUN_ATTEMPT") != "1":
        raise RuntimeError("Reset cannot be rerun")
    if event.get("ref") != "refs/heads/main":
        raise RuntimeError("Unexpected reset branch")
    cutoff = datetime.fromisoformat(event["head_commit"]["timestamp"].replace("Z", "+00:00"))
    current_run = int(os.environ["GITHUB_RUN_ID"])
    base = "https://api.github.com/repos/" + repo
    headers = {
        "Authorization": "Bearer " + os.environ["GH_TOKEN"],
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    failures: list[str] = []
    deleted: dict[str, int] = {}

    def api(method: str, path: str, body=None):
        payload = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(base + path, data=payload, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
        return json.loads(raw) if raw else None

    def collect(path: str, key: str | None = None) -> list[dict]:
        result: list[dict] = []
        joiner = "&" if "?" in path else "?"
        for page in range(1, 21):
            response = api("GET", f"{path}{joiner}per_page=100&page={page}")
            items = response[key] if key else response
            result.extend(items)
            if len(items) < 100:
                return result
        raise RuntimeError("Cleanup pagination cap reached: " + path)

    def remove(path: str, kind: str) -> None:
        try:
            api("DELETE", path)
            deleted[kind] = deleted.get(kind, 0) + 1
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                failures.append(f"DELETE {path}: HTTP {exc.code}")

    def old(item: dict) -> bool:
        value = item.get("created_at")
        return bool(value) and datetime.fromisoformat(value.replace("Z", "+00:00")) < cutoff

    # Snapshot branch names before mutation. The requested wipe covers every
    # non-main branch; none is copied to a preservation branch.
    branches = api("GET", "/git/matching-refs/heads/")
    for item in branches:
        ref = item["ref"]
        if ref != "refs/heads/main":
            remove("/git/refs/" + urllib.parse.quote(ref.removeprefix("refs/"), safe="/"), "branches")
    for item in api("GET", "/git/matching-refs/tags/"):
        remove("/git/refs/" + urllib.parse.quote(item["ref"].removeprefix("refs/"), safe="/"), "tags")
    for item in collect("/releases"):
        if old(item):
            remove("/releases/" + str(item["id"]), "releases")

    # Close obsolete conversations. GitHub does not provide a PR-deletion
    # endpoint; historical PR refs and protected commit history are not erased.
    for item in collect("/issues?state=open"):
        if old(item):
            endpoint = "/pulls/" if "pull_request" in item else "/issues/"
            try:
                api("PATCH", endpoint + str(item["number"]), {"state": "closed"})
                deleted["closed_conversations"] = deleted.get("closed_conversations", 0) + 1
            except urllib.error.HTTPError as exc:
                failures.append(f"Close conversation {item['number']}: HTTP {exc.code}")

    for path, key, kind in (
        ("/actions/artifacts", "artifacts", "artifacts"),
        ("/actions/caches", "actions_caches", "caches"),
    ):
        for item in collect(path, key):
            if old(item):
                remove(path + "/" + str(item["id"]), kind)
    for item in collect("/actions/runs", "workflow_runs"):
        if item["id"] != current_run and old(item):
            if item["status"] != "completed":
                failures.append(f"Old run {item['id']} still active; not deleting an active run")
                continue
            remove("/actions/runs/" + str(item["id"]), "workflow_runs")

    report = {
        "deleted_or_closed": deleted,
        "failures": failures,
        "backup_created": False,
        "protected_commit_history_erased": False,
        "github_historical_pull_requests_erased": False,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(report, indent=2))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("## Reset outcome\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

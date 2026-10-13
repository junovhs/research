#!/usr/bin/env python3
"""Static validation of the lab's structure, records and archived evidence.

Never executes experiment code: it only reads files (and, with --base, asks
git which paths a change touches). It checks objective facts — file layout,
frozen historical records, archive integrity, run citations, required labels —
not whether any mathematics or scientific judgment is correct.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_run  # noqa: E402  (shared manifest verifier; stdlib only)

MANDATORY = ["00-START-HERE.md", "01-RULES-AND-METHOD.md", "02-LIVE-STATE.md", "03-WRITEBACK-CHECKLIST.md"]
ROOT_FILES = {"AGENTS.md", "CLAUDE.md", "README.md", "MAP.md", "MIGRATION.md", "next-agent-please-do.md",
              "FRONTIER.md", "GOAL.md", "INDEX.md", "LEAN.md", "METHOD.md", "PRIOR_ART.md",
              "PROOF_OF_DONE.md", "SOURCES.md", ".gitignore"}
ROOT_DIRS = {"AGENTS-READ-THIS", "RESULTS", "PROMPTS", "PRIOR_ART", "TEMPLATES", "EVIDENCE", "scripts", ".github"}
APPEND_ONLY = ("RESULTS/", "PROMPTS/", "PRIOR_ART/", "EVIDENCE/R-")
FORBIDDEN_PARTS = {"__pycache__", "node_modules", ".venv", "venv", "build", "dist", "target", ".ipynb_checkpoints"}
MAX_FILE = 2 * 1024 * 1024        # larger artifacts belong in a verified external archive
MAX_RUN = 20 * 1024 * 1024
RESULT_NAME = re.compile(r"^R-(\d{3})(-[a-z0-9-]+)?\.md$")
RUN_TOKEN = re.compile(r"\b\d{4}-\d\d-\d\dT[0-9.-]+Z-[0-9a-f]{12}-[0-9a-f]{8}\b")
EXTERNAL = re.compile(r"External archive:\s*(https://\S+)\s+sha256:([0-9a-f]{64})")
LINK = re.compile(r"\]\(([^)\s]+)\)")

class Report:
    def __init__(self):
        self.errors, self.notes = [], []

    def error(self, path, msg):
        self.errors.append((str(path), msg))

    def note(self, msg):
        self.notes.append(msg)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tracked_files(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True).stdout
        names = [n for n in out.decode().split("\0") if n]
        return sorted(n for n in names if (root / n).exists())
    except (OSError, subprocess.CalledProcessError):
        return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                      if p.is_file() and ".git" not in p.relative_to(root).parts)

def check_layout(root, files, rep):
    if not (root / "AGENTS.md").is_file() or not (root / "CLAUDE.md").is_file():
        rep.error("AGENTS.md", "AGENTS.md and CLAUDE.md must both exist")
    elif (root / "AGENTS.md").read_bytes() != (root / "CLAUDE.md").read_bytes():
        rep.error("CLAUDE.md", "AGENTS.md and CLAUDE.md must be byte-for-byte identical")
    mand = sorted(f.split("/", 1)[1] for f in files if f.startswith("AGENTS-READ-THIS/"))
    if mand != MANDATORY:
        rep.error("AGENTS-READ-THIS", f"must contain exactly {MANDATORY}; found {mand}")
    for f in files:
        parts = f.split("/")
        if len(parts) == 1 and f not in ROOT_FILES:
            rep.error(f, "file not permitted at repository root (see AGENTS-READ-THIS/00-START-HERE.md)")
        if len(parts) > 1 and parts[0] not in ROOT_DIRS:
            rep.error(f, f"top-level directory '{parts[0]}' is not part of the lab structure")
        if FORBIDDEN_PARTS & set(parts[:-1]):
            rep.error(f, "build/cache/dependency directory must not be committed")
        p = root / f
        if p.is_symlink():
            rep.error(f, "symlinks are not permitted")
            continue
        if p.suffix.lower() in research_run.BINARY_SUFFIXES:
            rep.error(f, "compiled/packaged artifact must not be committed")
        size = p.stat().st_size
        if size > MAX_FILE:
            rep.error(f, f"file is {size} bytes (> {MAX_FILE}); use a verified external archive")
        if b"\0" in p.read_bytes()[:65536]:
            rep.error(f, "binary content is not permitted (text sources, configs and raw records only)")
    for f in files:
        d, _, name = f.partition("/")
        if d == "RESULTS" and "/" not in name and not RESULT_NAME.match(name):
            rep.error(f, "RESULTS files must be named R-NNN.md or R-NNN-<suffix>.md")
        if d == "PROMPTS" and "/" not in name and not re.match(r"^P-\d{3}\.md$", name):
            rep.error(f, "PROMPTS files must be named P-NNN.md")
        if d == "PRIOR_ART" and "/" not in name and not re.match(r"^(PA-[A-Za-z0-9-]+|TEMPLATE)\.md$", name):
            rep.error(f, "PRIOR_ART files must be named PA-*.md")

def check_links(root, files, rep):
    for f in files:
        if not f.endswith(".md"):
            continue
        for target in LINK.findall((root / f).read_text(errors="replace")):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#") or "NNN" in target:
                continue
            if not (root / f).parent.joinpath(target.split("#")[0]).exists():
                rep.error(f, f"broken relative link: {target}")

def load_legacy(root, rep):
    path = root / "EVIDENCE" / "LEGACY.json"
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        rep.error("EVIDENCE/LEGACY.json", f"missing or invalid legacy registry: {exc}")
        return {"frozen_records": {}, "archives": []}

def check_legacy(root, legacy, rep):
    for rel, digest in legacy.get("frozen_records", {}).items():
        p = root / rel
        if not p.is_file():
            rep.error(rel, "frozen historical record is missing (records are append-only)")
        elif sha(p) != digest:
            rep.error(rel, "frozen historical record was modified; add a linked correction file instead")
    for arc in legacy.get("archives", []):
        status = arc.get("status")
        if status not in {"NOT_RECOVERED", "RECOVERED"}:
            rep.error("EVIDENCE/LEGACY.json", f"{arc.get('id')}: status must be NOT_RECOVERED or RECOVERED")
            continue
        for name, digest in arc.get("sha256_anchors", {}).items():
            if not re.fullmatch(r"[0-9a-f]{64}", digest):
                rep.error("EVIDENCE/LEGACY.json", f"{arc.get('id')}: bad anchor for {name}")
            recovered = root / arc.get("recovered_path", "-") / name
            if status == "RECOVERED":
                if not recovered.is_file():
                    rep.error(str(recovered.relative_to(root)), "archive marked RECOVERED but file missing")
                elif sha(recovered) != digest:
                    rep.error(str(recovered.relative_to(root)), "recovered file does not match its historical SHA-256 anchor")
        if status == "NOT_RECOVERED":
            rep.note(f"legacy archive {arc.get('id')}: NOT_RECOVERED (historical hash anchors only; not verified)")

def check_evidence(root, files, legacy, rep):
    cited = {}
    for f in files:
        if f.startswith("RESULTS/") and f.endswith(".md"):
            for token in RUN_TOKEN.findall((root / f).read_text(errors="replace")):
                cited.setdefault(token, set()).add(f)
    runs = {}
    recovered = {a.get("recovered_path", "").rstrip("/") + "/" for a in legacy.get("archives", []) if a.get("recovered_path")}
    for f in files:
        if not f.startswith("EVIDENCE/") or f == "EVIDENCE/LEGACY.json" or any(f.startswith(r) for r in recovered):
            continue
        parts = f.split("/")
        if len(parts) < 3 or not re.fullmatch(r"R-\d{3}", parts[1]):
            rep.error(f, "evidence must live under EVIDENCE/R-NNN/ (or a registered legacy recovery path)")
            continue
        if len(parts) == 3:
            if not parts[2].endswith(".md"):
                rep.error(f, "only a Markdown note may sit beside run directories in EVIDENCE/R-NNN/")
            continue
        runs.setdefault((parts[1], parts[2]), []).append(f)
    verified = {}
    for (exp, run_id), members in sorted(runs.items()):
        where = f"EVIDENCE/{exp}/{run_id}"
        manifest = root / where / "manifest.json"
        if not manifest.is_file():
            rep.error(where, "run directory has no manifest.json")
            continue
        try:
            doc = research_run.verify(manifest, allow_incomplete=True)
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            rep.error(f"{where}/manifest.json", f"execution record rejected: {exc}")
            continue
        listed = {f"{where}/{n}" for n in doc["files"]} | {f"{where}/manifest.json"}
        if set(members) != listed:
            rep.error(where, f"committed files differ from manifest (missing from git: {sorted(listed - set(members))}, "
                             f"unlisted: {sorted(set(members) - listed)})")
        if sum((root / m).stat().st_size for m in members) > MAX_RUN:
            rep.error(where, f"run archive exceeds {MAX_RUN} bytes; use a verified external archive")
        if doc["experiment"] != exp:
            rep.error(where, f"manifest experiment {doc['experiment']} does not match directory {exp}")
        own = [c for c in cited.get(run_id, ()) if Path(c).name.startswith(exp)]
        if not own:
            rep.error(where, f"run is not cited by RESULTS/{exp}*.md (every archived run must be reported)")
        if doc["status"] != "COMPLETE":
            rep.note(f"{where}: preserved unsuccessful run (status {doc['status']}, exit {doc['exit_code']})")
        verified[run_id] = (exp, doc["status"])
    for token, sources in sorted(cited.items()):
        if token not in verified:
            for s in sorted(sources):
                rep.error(s, f"cites run {token} but no verified archive exists under EVIDENCE/")
    return verified

def check_new_results(root, files, legacy, verified, rep):
    frozen = set(legacy.get("frozen_records", {}))
    numbers = []
    for f in files:
        if not f.startswith("RESULTS/") or "/" in f[8:]:
            continue
        m = RESULT_NAME.match(f[8:])
        if not m:
            continue
        numbers.append(int(m.group(1)))
        if f in frozen:
            continue
        text = (root / f).read_text(errors="replace")
        exp = f"R-{m.group(1)}"
        if m.group(2):
            if f"({exp}.md)" not in text:
                rep.error(f, f"correction must link its parent [{exp}]({exp}.md)")
            continue
        for label, pattern in (("track (EXPLORATORY or CONFIRMATORY)", r"EXPLORATORY|CONFIRMATORY"),
                               ("POD status", r"POD:?\**\s*(YES|NO)"),
                               ("preregistration status", r"PREREGISTERED|Preregistered"),
                               ("evidence class", r"\b(SPECULATION|REPORTED|REPRODUCED|CERTIFIED)\b")):
            if not re.search(pattern, text):
                rep.error(f, f"missing required label: {label}")
        if re.search(r"POD:?\**\s*YES", text) and not re.search(r"\(\.\./PROMPTS/P-\d{3}\.md\)", text):
            rep.error(f, "POD: YES requires a link to its pretest PROMPTS/P-NNN.md card")
        own_ok = [r for r, (e, st) in verified.items() if e == exp and st == "COMPLETE" and r in text]
        external = EXTERNAL.findall(text)
        if not own_ok and not external:
            rep.error(f, f"new R-card has no supporting evidence: cite a COMPLETE run archived under "
                         f"EVIDENCE/{exp}/ or add 'External archive: <https URI> sha256:<hex>'")
        for uri, _ in external:
            rep.note(f"{f}: external archive {uri} declared; retrieval/hash NOT verified by CI")
    if numbers:
        latest = f"R-{max(numbers):03d}.md"
        live = root / "AGENTS-READ-THIS" / "02-LIVE-STATE.md"
        if live.is_file() and f"RESULTS/{latest}" not in live.read_text():
            rep.error("AGENTS-READ-THIS/02-LIVE-STATE.md", f"live state must link the latest result {latest}")

def check_append_only(root, base, rep):
    try:
        out = subprocess.run(["git", "-C", str(root), "diff", "--name-status", "--no-renames", f"{base}...HEAD"],
                             capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        rep.error("git", f"cannot diff against base {base}: {exc}")
        return
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if status != "A" and path.startswith(APPEND_ONLY):
            rep.error(path, f"historical record/evidence {'modified' if status == 'M' else 'deleted'} "
                            "(append-only; add a linked correction instead)")

def validate(root, base=None):
    rep = Report()
    files = tracked_files(root)
    check_layout(root, files, rep)
    check_links(root, files, rep)
    legacy = load_legacy(root, rep)
    check_legacy(root, legacy, rep)
    verified = check_evidence(root, files, legacy, rep)
    check_new_results(root, files, legacy, verified, rep)
    if base:
        check_append_only(root, base, rep)
    return rep

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument("--base", help="git ref to enforce append-only history against (pull requests)")
    args = parser.parse_args()
    rep = validate(Path(args.root).resolve(), args.base)
    gha = os.environ.get("GITHUB_ACTIONS") == "true"
    for note in rep.notes:
        print(f"NOTE: {note}")
    for path, msg in rep.errors:
        print(f"::error file={path}::{msg}" if gha else f"ERROR {path}: {msg}")
    print(f"{'FAILED' if rep.errors else 'PASSED'}: {len(rep.errors)} error(s), {len(rep.notes)} note(s)")
    return 1 if rep.errors else 0

if __name__ == "__main__":
    sys.exit(main())

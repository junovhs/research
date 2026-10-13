#!/usr/bin/env python3
"""Record and verify a research execution without external dependencies.

Captures experiment identity, command, declared source/input/config bytes,
environment, output, exit code and provenance fingerprints. A resumed run is
accepted only from a checkpoint whose originating run has the same
fingerprint. Not a proof of mathematical correctness.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

SCHEMA = 2
STATUSES = {"COMPLETE", "FAILED", "MUTATED_INPUT"}
EXPERIMENT = re.compile(r"^R-\d{3}$")
RUN_ID = re.compile(r"^\d{4}-\d\d-\d\dT[0-9.-]+Z-([0-9a-f]{12})-[0-9a-f]{8}$")
# Compiled or packaged artifacts must be rebuilt by the declared command,
# never declared as trusted source/input (stale-artifact guard).
BINARY_SUFFIXES = {".so", ".o", ".a", ".dll", ".dylib", ".exe", ".pyc", ".pyo",
                   ".class", ".whl", ".egg", ".zip", ".tar", ".gz", ".xz", ".bz2", ".7z"}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def stable(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()

def iso_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def environment(env_vars):
    return {"python": sys.version.split()[0], "implementation": platform.python_implementation(),
            "platform": platform.platform(), "machine": platform.machine(),
            "env": {name: os.environ.get(name) for name in sorted(set(env_vars))}}

def relative(path, cwd):
    p = Path(path).resolve(strict=True)
    try:
        return p, p.relative_to(cwd).as_posix()
    except ValueError:
        raise ValueError(f"declared file must lie under the working directory {cwd}: {p}") from None

def declare(files, kind, cwd):
    out = []
    for path in files:
        p, rel = relative(path, cwd)
        if not p.is_file():
            raise ValueError(f"not a regular file: {p}")
        if p.suffix.lower() in BINARY_SUFFIXES:
            raise ValueError(f"compiled/packaged artifact cannot be declared as {kind}: {rel}")
        data = p.read_bytes()
        out.append({"kind": kind, "path": rel, "sha256": digest(data), "data": data})
    return out

def declared(args, cwd):
    if not args.source or not args.config:
        raise ValueError("at least one --source and exactly one --config are required")
    cfg = declare([args.config], "config", cwd)
    try:
        json.loads(cfg[0]["data"].decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ValueError("config must be valid UTF-8 JSON") from exc
    items = declare(args.source, "source", cwd) + declare(args.input or [], "input", cwd) + cfg
    paths = [x["path"] for x in items]
    if len(set(paths)) != len(paths):
        raise ValueError("a file is declared more than once")
    return items

def fingerprint(experiment, items, command, env):
    return digest(stable({"experiment": experiment, "command": command, "environment": env,
                          "files": [{"kind": x["kind"], "path": x["path"], "sha256": x["sha256"]} for x in items]}))

def safe_file_names(root):
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise ValueError(f"symlink prohibited in run archive: {p}")
        if p.is_file():
            yield p.relative_to(root).as_posix(), p

def record_outputs(folder):
    return {name: digest(path.read_bytes()) for name, path in safe_file_names(folder) if name != "manifest.json"}

def write_manifest(path, doc):
    temp = path.with_suffix(".tmp")
    temp.write_bytes(json.dumps(doc, indent=2, sort_keys=True).encode() + b"\n")
    temp.replace(path)

def load_checkpoint(prior_manifest, checkpoint):
    """Verify a prior run archive and a checkpoint produced by it."""
    prior = verify(prior_manifest, allow_incomplete=True)
    cp = json.loads(Path(checkpoint).read_text())
    if cp.get("run_id") != prior["run_id"] or cp.get("fingerprint") != prior["fingerprint"]:
        raise ValueError("checkpoint does not belong to the stated prior run; refuse resume")
    return prior

def do_run(args):
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if not command:
        raise ValueError("execution command missing; pass after --")
    if not EXPERIMENT.match(args.experiment):
        raise ValueError("--experiment must look like R-NNN")
    cwd = Path.cwd().resolve()
    if bool(args.resume_from) != bool(args.checkpoint):
        raise ValueError("--resume-from and --checkpoint must be given together")
    items = declared(args, cwd)
    env = environment(args.env_var or [])
    fp = fingerprint(args.experiment, items, command, env)
    resumed = None
    if args.resume_from:
        prior = load_checkpoint(args.resume_from, args.checkpoint)
        if prior["fingerprint"] != fp:
            raise ValueError("source, config, inputs, command or environment changed since the "
                             "checkpointed run; start a fresh run instead of resuming")
        _, cp_rel = relative(args.checkpoint, cwd)
        resumed = {"run_id": prior["run_id"], "fingerprint": prior["fingerprint"],
                   "checkpoint": cp_rel, "checkpoint_sha256": digest(Path(args.checkpoint).read_bytes())}
    run_id = iso_now().replace("+00:00", "Z").replace(":", "-") + "-" + fp[:12] + "-" + uuid.uuid4().hex[:8]
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=True)
    folder = root / run_id
    folder.mkdir(mode=0o700, exist_ok=False)
    snapshot = folder / "declared"
    snapshot.mkdir()
    entries = []
    for i, item in enumerate(items):
        name = f"{i:03d}-{item['kind']}-{PurePosixPath(item['path']).name}"
        rel = f"declared/{name}"
        (snapshot / name).write_bytes(item["data"])
        entries.append({"kind": item["kind"], "path": item["path"], "snapshot": rel, "sha256": item["sha256"]})
    manifest = {"schema": SCHEMA, "experiment": args.experiment, "run_id": run_id, "fingerprint": fp,
                "started_utc": iso_now(), "command": command, "declared": entries,
                "environment": env, "resumed_from": resumed, "status": "RUNNING", "exit_code": None}
    write_manifest(folder / "manifest.json", manifest)
    build = Path(tempfile.mkdtemp(prefix="dtl-build-"))
    child_env = dict(os.environ, DTL_RUN_DIR=str(folder), DTL_RUN_ID=run_id, DTL_FINGERPRINT=fp,
                     DTL_BUILD_DIR=str(build), PYTHONDONTWRITEBYTECODE="1")
    if resumed:
        child_env["DTL_RESUME_CHECKPOINT"] = str(Path(args.checkpoint).resolve())
    try:
        with (folder / "stdout.bin").open("wb") as stdout, (folder / "stderr.bin").open("wb") as stderr:
            code = subprocess.run(command, stdout=stdout, stderr=stderr, env=child_env, check=False).returncode
        unchanged = all((cwd / e["path"]).is_file() and digest((cwd / e["path"]).read_bytes()) == e["sha256"]
                        for e in entries)
        manifest["exit_code"] = code
        manifest["status"] = "COMPLETE" if code == 0 and unchanged else ("MUTATED_INPUT" if not unchanged else "FAILED")
    except OSError as exc:
        (folder / "stderr.bin").write_text(f"Launcher failure: {exc}\n")
        (folder / "stdout.bin").touch()
        manifest["exit_code"] = -1
        manifest["status"] = "FAILED"
    finally:
        shutil.rmtree(build, ignore_errors=True)
    manifest["finished_utc"] = iso_now()
    manifest["files"] = record_outputs(folder)
    write_manifest(folder / "manifest.json", manifest)
    print(folder / "manifest.json")
    return 0 if manifest["status"] == "COMPLETE" else 1

def require(cond, message):
    if not cond:
        raise ValueError(message)

def verify(manifest_path, allow_incomplete=False):
    """Fail closed unless the archive is internally consistent.

    With allow_incomplete, FAILED and MUTATED_INPUT records are accepted as
    preserved evidence of an unsuccessful run; RUNNING (never finalized) is not.
    """
    path = Path(manifest_path).resolve(strict=True)
    doc = json.loads(path.read_text())
    root = path.parent
    require(isinstance(doc, dict) and doc.get("schema") == SCHEMA, f"unsupported manifest schema (need {SCHEMA})")
    run_id = doc.get("run_id")
    require(run_id == root.name, "run ID does not match archive directory")
    m = RUN_ID.match(run_id or "")
    require(m is not None, "malformed run ID")
    require(isinstance(doc.get("fingerprint"), str) and m.group(1) == doc["fingerprint"][:12],
            "run ID does not embed the recorded fingerprint")
    require(EXPERIMENT.match(str(doc.get("experiment", ""))) is not None, "missing experiment identity")
    command = doc.get("command")
    require(isinstance(command, list) and command and all(isinstance(c, str) for c in command), "command missing")
    require(doc.get("status") in STATUSES, f"incomplete or unknown run status: {doc.get('status')}")
    require(isinstance(doc.get("exit_code"), int), "exit status missing")
    require(isinstance(doc.get("started_utc"), str) and isinstance(doc.get("finished_utc"), str),
            "start/finish metadata missing")
    require(dt.datetime.fromisoformat(doc["started_utc"]) <= dt.datetime.fromisoformat(doc["finished_utc"]),
            "finished before started")
    if doc["status"] == "COMPLETE":
        require(doc["exit_code"] == 0, "COMPLETE run with nonzero exit status")
    elif not allow_incomplete:
        raise ValueError(f"run did not complete successfully (status {doc['status']}, exit {doc['exit_code']})")
    for name in ("stdout.bin", "stderr.bin"):
        require((root / name).is_file(), f"missing captured {name}")
    require(record_outputs(root) == doc.get("files"), "archive file set or SHA-256 mismatch")
    entries = doc.get("declared")
    require(isinstance(entries, list) and entries, "no declared files")
    kinds = [e.get("kind") for e in entries]
    require("source" in kinds and kinds.count("config") == 1, "need >=1 source and exactly one config")
    for e in entries:
        snap = PurePosixPath(e["snapshot"])
        require(snap.parts[0] == "declared" and ".." not in snap.parts and len(snap.parts) == 2, "bad snapshot path")
        require(not PurePosixPath(e["path"]).is_absolute() and ".." not in PurePosixPath(e["path"]).parts,
                "declared path must be relative")
        require(digest((root / e["snapshot"]).read_bytes()) == e["sha256"], "snapshot integrity failure")
    items = [{"kind": e["kind"], "path": e["path"], "sha256": e["sha256"]} for e in entries]
    require(fingerprint(doc["experiment"], items, command, doc.get("environment")) == doc["fingerprint"],
            "fingerprint mismatch")
    return doc

def do_check_resume(args):
    load_checkpoint(args.manifest, args.checkpoint)
    print("CHECKPOINT MATCH")
    return 0

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    run = subs.add_parser("run", help="execute one immutable run; output must go to DTL_RUN_DIR")
    run.add_argument("--experiment", required=True, help="experiment identity, e.g. R-015")
    run.add_argument("--source", action="append", required=True, help="source file, repeat for all sources")
    run.add_argument("--input", action="append", help="data/input file, repeat as needed")
    run.add_argument("--config", required=True, help="UTF-8 JSON experiment config")
    run.add_argument("--env-var", action="append", help="environment variable affecting results (recorded, fingerprinted)")
    run.add_argument("--resume-from", help="manifest of the interrupted run being continued")
    run.add_argument("--checkpoint", help="checkpoint JSON carrying that run's run_id and fingerprint")
    run.add_argument("--out", required=True, help="run archive root, normally EVIDENCE/R-NNN")
    run.add_argument("command", nargs=argparse.REMAINDER)
    check = subs.add_parser("verify", help="verify immutable run archive and status")
    check.add_argument("--allow-failed", action="store_true", help="accept finalized FAILED/MUTATED_INPUT records")
    check.add_argument("manifest")
    resume = subs.add_parser("check-resume", help="reject checkpoint not matching a verified run")
    resume.add_argument("manifest")
    resume.add_argument("checkpoint")
    args = parser.parse_args()
    try:
        if args.action == "run":
            return do_run(args)
        if args.action == "verify":
            doc = verify(args.manifest, allow_incomplete=args.allow_failed)
            print(f"VERIFIED {doc['run_id']} {doc['fingerprint']} {doc['status']}")
            return 0
        if args.action == "check-resume":
            return do_check_resume(args)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"EVIDENCE GUARD FAILED: {exc}", file=sys.stderr)
        return 1
    return 2

if __name__ == "__main__":
    sys.exit(main())

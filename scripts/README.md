# Evidence execution guard and lab validator (research-only)

Both tools use only the Python standard library (3.10+). Run them from the
repository root (or, for `research_run.py`, from a scratch directory that
contains every declared file).

## 1. Record an execution: `research_run.py`

Work in a scratch directory holding the experiment's sources/config, and write
the archive straight into this repository:

```sh
cd /scratch/r015            # contains probe.py, probe.json (and any inputs)
python3 ~/research/scripts/research_run.py run --experiment R-015 \
    --source probe.py --config probe.json [--input data.csv] [--env-var OMP_NUM_THREADS] \
    --out ~/research/EVIDENCE/R-015 -- python3 probe.py
python3 ~/research/scripts/research_run.py verify ~/research/EVIDENCE/R-015/<run-id>/manifest.json
```

Commit only the run archive `EVIDENCE/R-NNN/<run-id>/` (plus, optionally, one
Markdown note in `EVIDENCE/R-NNN/`). The archive already holds byte-exact
snapshots of every declared file under `declared/`, so sources need not be
committed separately; CI rejects any other files under `EVIDENCE/R-NNN/`.

A probe must write its outputs to `os.environ["DTL_RUN_DIR"]`. The runner records:
experiment identity, the exact command (verbatim; use relative paths), start/end
UTC, exit status, Python/platform/machine plus any `--env-var` values,
working-directory-relative paths and SHA-256 of every declared source/config/input, a
snapshot of each, captured stdout/stderr, and SHA-256 of every archived file.
Every launch gets a new run ID that embeds the fingerprint. The fingerprint
covers experiment, command, environment and declared files, so any change
produces a different fingerprint. Declared files must lie under the working
directory; compiled/packaged artifacts (`.so`, `.o`, `.pyc`, archives, ...)
cannot be declared. Sources mutated during the run mark it `MUTATED_INPUT`.

**Stale artifacts:** compile inside the command into `$DTL_BUILD_DIR`, a fresh
empty directory created per run and deleted afterwards; `PYTHONDONTWRITEBYTECODE`
is set. Put seeds, precision and compiler flags in the config or the command.

**Resume:** a long program writes checkpoints containing `DTL_RUN_ID` and
`DTL_FINGERPRINT`. Continue an interrupted run with
`run ... --resume-from OLD/manifest.json --checkpoint OLD/checkpoint.json`
(the checkpoint path is then in `$DTL_RESUME_CHECKPOINT`). The runner verifies
the old archive, the checkpoint's run ID/fingerprint, and that the new launch
has the *identical* fingerprint; otherwise it refuses. The new run has a fresh
ID and records `resumed_from`. `check-resume MANIFEST CHECKPOINT` performs the
checkpoint check alone. Row-count-only resume is prohibited.

`verify` fails closed on missing/changed/unlisted files, edited manifests,
non-COMPLETE status or nonzero exit. `verify --allow-failed` accepts finalized
FAILED / MUTATED_INPUT records, which should be preserved and reported.

## 2. Validate the tree: `validate_lab.py` (what CI runs)

```sh
python3 scripts/test_research_run.py
python3 scripts/test_validate_lab.py
python3 scripts/validate_lab.py --base origin/main
```

Static only: it never executes experiment code. It checks AGENTS.md==CLAUDE.md,
the four-file mandatory folder, permitted root/directory layout and file names,
no binaries/caches/oversized files, relative links, frozen historical records
(EVIDENCE/LEGACY.json), every EVIDENCE/R-NNN run archive (integrity, status,
experiment directory, exact committed file set) and that each run is cited by
its R-card, that every cited run exists, that each **new** R-card carries track,
POD, preregistration and evidence labels and is supported by a COMPLETE
archived run or an `External archive: <https URI> sha256:<hex>` line, that the
live state links the latest R-card, and (with `--base`) that historical
records/evidence were only added, never modified or deleted.

## Limitations (be explicit)

Neither tool validates mathematics, proves an error bound, detects undeclared
inputs or network access, sandboxes the command, guarantees the host was quiet
for timings, or verifies that an external archive URI is retrievable (CI only
records the declared hash). A green check means the evidence record is
internally consistent and reported, not that the claim is right. Records
created before 2026-10-13 (R-001 to R-014) predate this tooling and were never
checked by it; see MIGRATION.md.

Commit only small, meaningful text/source/config/raw evidence (CI caps files at
2 MB and runs at 20 MB). Larger outputs need a stable, actually retrieved
external archive with recorded hashes. No compiled binaries, dependencies or
application code belong in this repository.

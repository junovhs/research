"""Standard-library tests for the static lab validator (success and failure paths)."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_lab.py"
RUNNER = HERE / "research_run.py"
LEGACY_CARD = "# R-001 · old\n\nEXPLORATORY, REPORTED, POD: NO, PREREGISTERED: NO\n"
NEW_CARD = ("# R-002 · new test\n\n**Track:** EXPLORATORY · **PREREGISTERED:** NO · **POD:** NO · "
            "**Evidence:** REPORTED\n\nRun {run}.\n")

def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        r = self.root
        for name in ("00-START-HERE.md", "01-RULES-AND-METHOD.md", "03-WRITEBACK-CHECKLIST.md"):
            self.write(f"AGENTS-READ-THIS/{name}", f"# {name}\n")
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-001](../RESULTS/R-001.md)\n")
        self.write("AGENTS.md", "entry\n")
        self.write("CLAUDE.md", "entry\n")
        self.write("RESULTS/R-001.md", LEGACY_CARD)
        self.write("scripts/research_run.py", RUNNER.read_text())
        legacy = {"frozen_records": {"RESULTS/R-001.md": hashlib.sha256(LEGACY_CARD.encode()).hexdigest()},
                  "archives": [{"id": "R-001-companion", "status": "NOT_RECOVERED",
                                "recovered_path": "EVIDENCE/legacy/R-001", "sha256_anchors": {"a.json": "0" * 64}}]}
        self.write("EVIDENCE/LEGACY.json", json.dumps(legacy))
        git(r, "init", "-q", "-b", "main")
        git(r, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        git(r, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def validate(self, *extra):
        r = subprocess.run([sys.executable, str(VALIDATOR), "--root", str(self.root), *extra],
                           capture_output=True, text=True)
        return r.returncode, r.stdout

    def assertFails(self, needle, *extra):
        code, out = self.validate(*extra)
        self.assertEqual(code, 1, out)
        self.assertIn(needle, out)

    def run_experiment(self, exp="R-002", program="import os\nfrom pathlib import Path\n"
                       "Path(os.environ['DTL_RUN_DIR'], 'out.json').write_text('{\"x\": 1}')\n"):
        self.write("probe.py", program)
        self.write("probe.json", '{"seed": 3}')
        r = subprocess.run([sys.executable, str(RUNNER), "run", "--experiment", exp, "--source", "probe.py",
                            "--config", "probe.json", "--out", f"EVIDENCE/{exp}", "--", sys.executable, "probe.py"],
                           cwd=self.root, capture_output=True, text=True)
        (self.root / "probe.py").unlink()
        (self.root / "probe.json").unlink()
        return Path(r.stdout.strip())

    def add_valid_result(self):
        manifest = self.run_experiment()
        run_id = manifest.parent.name
        self.write("RESULTS/R-002.md", NEW_CARD.format(run=run_id))
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        return manifest

    def test_clean_tree_passes(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("NOT_RECOVERED", out)

    def test_valid_new_result_with_evidence_passes(self):
        self.add_valid_result()
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        code, out = self.validate("--base", "main")
        self.assertEqual(code, 0, out)

    def test_new_result_without_evidence_fails(self):
        self.write("RESULTS/R-002.md", NEW_CARD.format(run="(none)"))
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        self.assertFails("no supporting evidence")

    def test_external_archive_declaration_is_accepted_but_flagged(self):
        self.write("RESULTS/R-002.md", NEW_CARD.format(run="none") +
                   "External archive: https://example.org/r2.tar.gz sha256:" + "a" * 64 + "\n")
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        code, out = self.validate()
        self.assertEqual(code, 0, out)
        self.assertIn("NOT verified by CI", out)

    def test_missing_labels_fail(self):
        manifest = self.run_experiment()
        self.write("RESULTS/R-002.md", f"# R-002\n\nRun {manifest.parent.name}.\n")
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        self.assertFails("missing required label")

    def test_tampered_evidence_fails(self):
        manifest = self.add_valid_result()
        (manifest.parent / "out.json").write_text('{"x": 2}')
        self.assertFails("SHA-256 mismatch")

    def test_deleted_evidence_file_fails(self):
        manifest = self.add_valid_result()
        (manifest.parent / "out.json").unlink()
        self.assertFails("execution record rejected")

    def test_incomplete_running_record_fails(self):
        manifest = self.add_valid_result()
        doc = json.loads(manifest.read_text())
        doc["status"] = "RUNNING"
        manifest.write_text(json.dumps(doc))
        self.assertFails("incomplete or unknown run status")

    def test_failed_run_is_preserved_but_cannot_be_sole_support(self):
        manifest = self.run_experiment(program="import sys\nsys.exit(4)\n")
        self.write("RESULTS/R-002.md", NEW_CARD.format(run=manifest.parent.name))
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        code, out = self.validate()
        self.assertIn("preserved unsuccessful run", out)
        self.assertIn("no supporting evidence", out)
        self.assertEqual(code, 1)

    def test_uncited_run_fails(self):
        self.run_experiment()
        self.assertFails("is not cited")

    def test_citation_without_archive_fails(self):
        manifest = self.add_valid_result()
        shutil.rmtree(manifest.parent)
        self.assertFails("no verified archive exists")

    def test_run_filed_under_wrong_experiment_fails(self):
        manifest = self.run_experiment(exp="R-003")
        target = self.root / "EVIDENCE/R-002" / manifest.parent.name
        target.parent.mkdir(parents=True)
        manifest.parent.rename(target)
        self.write("RESULTS/R-002.md", NEW_CARD.format(run=target.name))
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-002](../RESULTS/R-002.md)\n")
        self.assertFails("does not match directory")

    def test_modified_legacy_record_fails(self):
        self.write("RESULTS/R-001.md", LEGACY_CARD + "Now conclusive!\n")
        self.assertFails("frozen historical record was modified")

    def test_append_only_against_base_fails(self):
        manifest = self.add_valid_result()
        git(self.root, "add", "-A")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "r2")
        git(self.root, "checkout", "-qb", "edit")
        self.write("RESULTS/R-002.md", (self.root / "RESULTS/R-002.md").read_text() + "edited\n")
        git(self.root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qam", "edit")
        self.assertFails("append-only", "--base", "main")

    def test_live_state_must_link_latest_result(self):
        self.add_valid_result()
        self.write("AGENTS-READ-THIS/02-LIVE-STATE.md", "Latest: [R-001](../RESULTS/R-001.md)\n")
        self.assertFails("live state must link the latest result R-002.md")

    def test_structure_rules(self):
        self.write("CLAUDE.md", "diverged\n")
        self.write("AGENTS-READ-THIS/04-EXTRA.md", "x\n")
        self.write("notes.md", "x\n")
        self.write("src/main.rs", "fn main() {}\n")
        (self.root / "EVIDENCE/R-002").mkdir(parents=True)
        (self.root / "EVIDENCE/R-002/kernel.so").write_bytes(b"\x7fELF\0\0")
        self.write("RESULTS/notes.md", "x\n")
        self.write("README.md", "[gone](missing.md)\n")
        code, out = self.validate()
        self.assertEqual(code, 1)
        for needle in ("byte-for-byte identical", "must contain exactly", "not permitted at repository root",
                       "not part of the lab structure", "compiled/packaged artifact", "binary content",
                       "R-NNN.md", "broken relative link"):
            self.assertIn(needle, out)

    def test_recovered_legacy_archive_must_match_anchor(self):
        legacy = json.loads((self.root / "EVIDENCE/LEGACY.json").read_text())
        legacy["archives"][0]["status"] = "RECOVERED"
        self.write("EVIDENCE/LEGACY.json", json.dumps(legacy))
        self.write("EVIDENCE/legacy/R-001/a.json", "{}")
        self.assertFails("does not match its historical SHA-256 anchor")

if __name__ == "__main__":
    unittest.main()

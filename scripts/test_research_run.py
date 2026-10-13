"""Standard-library tests for the lab's execution provenance guard."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("research_run.py")
TOY = ("import json, os\nfrom pathlib import Path\n"
       "Path(os.environ['DTL_RUN_DIR'], 'result.json').write_text(json.dumps({'value': 7}))\n")

class EvidenceGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.program = self.root / "toy.py"
        self.program.write_text(TOY)
        self.config = self.root / "config.json"
        self.config.write_text('{"seed":1}')

    def cmd(self, *args, env=None):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                              cwd=self.root, env=env)

    def launch(self, *extra, env=None):
        return self.cmd("run", "--experiment", "R-900", "--source", self.program, "--config", self.config,
                        *extra, "--out", "evidence", "--", sys.executable, "toy.py", env=env)

    def perform(self, *extra, env=None):
        r = self.launch(*extra, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return Path(r.stdout.strip())

    def test_complete_and_tamper(self):
        manifest = self.perform()
        self.assertEqual(self.cmd("verify", manifest).returncode, 0)
        (manifest.parent / "result.json").write_text("tamper")
        self.assertNotEqual(self.cmd("verify", manifest).returncode, 0)

    def test_records_identity_relative_paths_and_metadata(self):
        doc = json.loads(self.perform().read_text())
        self.assertEqual(doc["experiment"], "R-900")
        self.assertEqual(doc["status"], "COMPLETE")
        self.assertEqual(doc["exit_code"], 0)
        self.assertTrue(doc["started_utc"] <= doc["finished_utc"])
        self.assertEqual({e["path"] for e in doc["declared"]}, {"toy.py", "config.json"})
        self.assertNotIn(str(self.root), json.dumps(doc), "no absolute local paths in the manifest")
        self.assertIn("result.json", doc["files"])

    def test_missing_or_unlisted_archive_file_fails(self):
        manifest = self.perform()
        (manifest.parent / "extra.txt").write_text("smuggled")
        self.assertIn("mismatch", self.cmd("verify", manifest).stderr)
        (manifest.parent / "extra.txt").unlink()
        (manifest.parent / "result.json").unlink()
        self.assertNotEqual(self.cmd("verify", manifest).returncode, 0)

    def test_edited_manifest_fails(self):
        manifest = self.perform()
        doc = json.loads(manifest.read_text())
        doc["command"] = [sys.executable, "other.py"]
        manifest.write_text(json.dumps(doc))
        self.assertIn("fingerprint mismatch", self.cmd("verify", manifest).stderr)

    def test_unfinished_and_failed_runs(self):
        self.program.write_text("import sys\nsys.exit(3)\n")
        r = self.launch()
        self.assertEqual(r.returncode, 1)
        manifest = Path(r.stdout.strip())
        self.assertIn("did not complete", self.cmd("verify", manifest).stderr)
        ok = self.cmd("verify", "--allow-failed", manifest)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("FAILED", ok.stdout)
        doc = json.loads(manifest.read_text())
        doc["status"] = "RUNNING"
        manifest.write_text(json.dumps(doc))
        self.assertIn("incomplete", self.cmd("verify", "--allow-failed", manifest).stderr)

    def test_checkpoint_is_run_bound(self):
        manifest = self.perform()
        doc = json.loads(manifest.read_text())
        cp = self.root / "cp.json"
        cp.write_text(json.dumps({"run_id": doc["run_id"], "fingerprint": doc["fingerprint"]}))
        self.assertEqual(self.cmd("check-resume", manifest, cp).returncode, 0)
        cp.write_text(json.dumps({"run_id": doc["run_id"], "fingerprint": "incorrect"}))
        self.assertNotEqual(self.cmd("check-resume", manifest, cp).returncode, 0)
        cp.write_text(json.dumps({"rows": 500}))
        self.assertNotEqual(self.cmd("check-resume", manifest, cp).returncode, 0, "row-count-only resume")

    def interrupted(self):
        """A run that writes a checkpoint and then dies, as an interrupted sweep would."""
        self.program.write_text(
            "import json, os, sys\nfrom pathlib import Path\n"
            "cp = os.environ.get('DTL_RESUME_CHECKPOINT')\n"
            "if cp is None:\n"
            "    Path(os.environ['DTL_RUN_DIR'], 'checkpoint.json').write_text(json.dumps("
            "{'run_id': os.environ['DTL_RUN_ID'], 'fingerprint': os.environ['DTL_FINGERPRINT'], 'rows': 2}))\n"
            "    sys.exit(9)\n"
            "Path(os.environ['DTL_RUN_DIR'], 'rest.json').write_text(Path(cp).read_text())\n")
        r = self.launch()
        self.assertEqual(r.returncode, 1)
        manifest = Path(r.stdout.strip())
        return manifest, manifest.parent / "checkpoint.json"

    def test_resume_requires_identical_fingerprint(self):
        manifest, cp = self.interrupted()
        resumed = self.perform("--resume-from", manifest, "--checkpoint", cp)
        doc = json.loads(resumed.read_text())
        prior = json.loads(manifest.read_text())
        self.assertEqual(doc["resumed_from"]["run_id"], prior["run_id"])
        self.assertNotEqual(doc["run_id"], prior["run_id"], "a resumed launch still gets a fresh run ID")
        self.assertEqual(self.cmd("verify", resumed).returncode, 0)
        self.config.write_text('{"seed":2}')
        r = self.launch("--resume-from", manifest, "--checkpoint", cp)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("changed since the checkpointed run", r.stderr)

    def test_resume_refuses_tampered_prior_archive(self):
        manifest, cp = self.interrupted()
        (manifest.parent / "stdout.bin").write_text("edited")
        r = self.launch("--resume-from", manifest, "--checkpoint", cp)
        self.assertNotEqual(r.returncode, 0)

    def test_change_config_never_resumes(self):
        first = self.perform()
        self.config.write_text('{"seed":2}')
        second = self.perform()
        a, b = json.loads(first.read_text()), json.loads(second.read_text())
        self.assertNotEqual(a["run_id"], b["run_id"])
        self.assertNotEqual(a["fingerprint"], b["fingerprint"])
        self.assertEqual(self.cmd("verify", first).returncode, 0)
        self.assertEqual(self.cmd("verify", second).returncode, 0)

    def test_declared_environment_variable_changes_fingerprint(self):
        env = dict(os.environ, OMP_NUM_THREADS="1")
        a = json.loads(self.perform("--env-var", "OMP_NUM_THREADS", env=env).read_text())
        env["OMP_NUM_THREADS"] = "4"
        b = json.loads(self.perform("--env-var", "OMP_NUM_THREADS", env=env).read_text())
        self.assertEqual(b["environment"]["env"], {"OMP_NUM_THREADS": "4"})
        self.assertNotEqual(a["fingerprint"], b["fingerprint"])

    def test_detect_mutated_source(self):
        self.program.write_text("from pathlib import Path\nimport os\np=Path(__file__);p.write_text('changed')\n")
        r = self.launch()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('MUTATED_INPUT', Path(r.stdout.strip()).read_text())

    def test_refuses_compiled_artifacts_and_outside_files(self):
        lib = self.root / "kernel.so"
        lib.write_bytes(b"\x7fELF")
        r = self.cmd("run", "--experiment", "R-900", "--source", self.program, "--input", lib, "--config",
                     self.config, "--out", self.root / "evidence", "--", sys.executable, self.program)
        self.assertIn("compiled/packaged artifact", r.stderr)
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other, "x.py")
            outside.write_text("pass\n")
            r = self.cmd("run", "--experiment", "R-900", "--source", outside, "--config", self.config,
                         "--out", self.root / "evidence", "--", sys.executable, outside)
            self.assertIn("under the working directory", r.stderr)

    def test_fresh_build_dir_each_run(self):
        self.program.write_text(
            "import os, json\nfrom pathlib import Path\nb = Path(os.environ['DTL_BUILD_DIR'])\n"
            "found = sorted(p.name for p in b.iterdir())\n(b / 'stale.so').write_text('x')\n"
            "Path(os.environ['DTL_RUN_DIR'], 'build.json').write_text(json.dumps({'dir': str(b), 'found': found}))\n")
        first = json.loads((self.perform().parent / "build.json").read_text())
        second = json.loads((self.perform().parent / "build.json").read_text())
        self.assertEqual(first["found"], [])
        self.assertEqual(second["found"], [], "no compiled artifact survives into the next run")
        self.assertFalse(Path(first["dir"]).exists())

    def test_bad_experiment_identity_rejected(self):
        r = self.cmd("run", "--experiment", "exp1", "--source", self.program, "--config", self.config,
                     "--out", self.root / "evidence", "--", sys.executable, self.program)
        self.assertIn("R-NNN", r.stderr)

if __name__ == "__main__":
    unittest.main()

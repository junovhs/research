# CI demonstration only: exact integer sum, no research content.
import json, os
from pathlib import Path
cfg = json.loads(Path("probe.json").read_text())
n = cfg["n"]
Path(os.environ["DTL_RUN_DIR"], "result.json").write_text(json.dumps({"n": n, "sum": sum(range(1, n + 1)), "closed_form": n * (n + 1) // 2}) + "\n")

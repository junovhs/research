"""Explore Alien-generated proposals through the authors' official Lacuna MCP."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

ENDPOINT = "https://lacuna.tiptreesystems.com/api/mcp"
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path.home() / ".cache/alien-space-of-science"


class Lacuna:
    def __init__(self):
        self.calls = []
        self.session = None
        self.counter = 0
        self.server = self.request("initialize", {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "alien-explorer", "version": "0.1"}})

    def request(self, method, params):
        self.counter += 1
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        request = urllib.request.Request(ENDPOINT, data=json.dumps({
            "jsonrpc": "2.0", "id": self.counter, "method": method, "params": params}).encode(), headers=headers)
        started = time.monotonic()
        with urllib.request.urlopen(request, timeout=30) as response:
            self.session = response.headers.get("Mcp-Session-Id", self.session)
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Response exceeds 2 MB cap")
        text = raw.decode()
        if text.startswith(("event:", "data:")):
            messages = [json.loads(line[5:].strip()) for line in text.splitlines() if line.startswith("data:")]
            result = next(message for message in messages if message.get("id") == self.counter)
        else:
            result = json.loads(text)
        if "error" in result:
            raise RuntimeError(result["error"])
        result = result["result"]
        if result.get("isError"):
            raise RuntimeError(result)
        self.calls.append({"utc": datetime.now(timezone.utc).isoformat(), "method": method,
                           "params": params, "seconds": round(time.monotonic()-started, 3), "response": result})
        return result

    def tool(self, name, **arguments):
        if name not in {"search_lacuna", "get_hypothesis", "get_direction", "get_direction_papers", "get_paper"}:
            raise ValueError("Only the selected public read-only exploration tools are enabled")
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        if "structuredContent" in result:
            return result["structuredContent"]
        blocks = result.get("content", [])
        text = "\n".join(block["text"] for block in blocks if block.get("type") == "text")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["search", "proposal", "direction", "sample"])
    parser.add_argument("query", nargs="?", help="Search text, or an ID/URL returned by a previous search")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--count", type=int, default=256, help="Fresh candidates for the official CPU sampler")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--runtime", type=Path, default=RUNTIME)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.output = args.output or ROOT / ".cache/alien-exploration" / ("local-run.json" if args.command == "sample" else "hosted-session.json")
    if args.command == "sample":
        python = args.runtime / "venv/Scripts/python.exe"
        if not python.exists():
            raise FileNotFoundError("Official Alien runtime not installed at " + str(args.runtime))
        if args.count < 1:
            parser.error("--count must be positive")
        run_id = f"explore-{args.seed}-{args.count}-{time.time_ns()}"
        command = [str(python), "alien.py", "sample", "--n-gen", str(args.count),
                   "--top-k", "5", "--device", "cpu", "--batch-size", "8", "--seed", str(args.seed),
                   "--betas", "0", "0.4", "0.7", "0.95", "--output-dir", f"results/{run_id}"]
        started = time.monotonic()
        result = subprocess.run(command, cwd=args.runtime / "upstream",
                                env=dict(os.environ, OMP_NUM_THREADS="2", MKL_NUM_THREADS="2"),
                                capture_output=True, text=True, timeout=180)
        ranked_paths = sorted((args.runtime / "upstream" / f"results/{run_id}/k3").glob("beta_*/results.json"))
        rankings = [json.loads(path.read_text()) for path in ranked_paths]
        verified = (result.returncode == 0 and len(rankings) == 4 and
                    all(item["config"]["n_gen"] == args.count and item["top_k_sequences"] for item in rankings))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        record = {"mode": "Official unmodified Alien CPU inference", "command": command[1:],
                  "seconds": round(time.monotonic()-started, 3), "exit_code": result.returncode, "outputs_verified": verified,
                  "stdout": result.stdout, "stderr": result.stderr,
                  "code_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.runtime / "upstream", text=True).strip()}
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"device": "cpu", "seconds": record["seconds"], "outputs_verified": verified,
                          "rankings": [{"beta": item["config"]["beta"], "unique_candidates": item["config"]["n_candidate_sets"],
                                        "top_atom_ids": item["top_k_sequences"][0]["cluster_ids"]} for item in rankings]}, indent=2))
        if not verified:
            print(result.stderr)
        raise SystemExit(0 if verified else result.returncode or 1)
    if not args.query:
        parser.error("Search, proposal and direction require a query or returned ID")
    client = Lacuna()
    if args.command == "search":
        result = client.tool("search_lacuna", query=args.query, search_type="hypothesis", limit=min(10, max(1, args.limit)))
    elif args.command == "proposal":
        result = client.tool("get_hypothesis", hypothesis_id_or_url=args.query, view="context")
    else:
        result = client.tool("get_direction", cluster_id_or_url=args.query, view="context")
    report = json.loads(args.output.read_text()) if args.output.exists() else {
        "endpoint": ENDPOINT, "tool_repository": "https://github.com/tiptreesystems/lacuna-research-mcp",
        "paper": "https://arxiv.org/abs/2603.01092", "calls": [],
        "mode": "Official hosted Alien-generated proposal exploration; no local model inference or retraining claimed."}
    report["calls"].extend(client.calls)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

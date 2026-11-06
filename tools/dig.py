"""Small, standard-library pencil-beam dig. Run from any directory."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261106
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"
ARCHIVES = {"esa": ENDPOINT, "ari": "https://gaia.ari.uni-heidelberg.de/tap/sync"}
COLUMNS = "source_id,ra,dec,ref_epoch,parallax,parallax_error,pmra,pmdec,phot_g_mean_mag,bp_rp,ruwe,astrometric_params_solved,visibility_periods_used,phot_bp_rp_excess_factor,duplicated_source"
SCHEMA_REFERENCE = "https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def cache_directory():
    return Path(os.environ.get("NEEDLE_CACHE", str(Path.home() / ".cache" / "research-needles"))).resolve()


def budget():
    return json.loads((ROOT / "config/budget.json").read_text())


def gaia_query(field):
    return (f"SELECT TOP {budget()['initial_sample_rows']} {COLUMNS} FROM gaiadr3.gaia_source "
            f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{field['ra_deg']},{field['dec_deg']},{field['radius_deg']})) ORDER BY source_id")


def bounded_request(endpoint, query, byte_limit, deadline):
    payload = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}).encode()
    request = urllib.request.Request(endpoint, data=payload, headers={"User-Agent": "research-needles/1.0 (bounded public archive query)"})
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Batch deadline exceeded")
    chunks, total = [], 0
    with urllib.request.urlopen(request, timeout=min(45, remaining)) as response:
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Batch deadline exceeded during download")
            chunk = response.read(min(65536, byte_limit-total+1))
            if not chunk:
                break
            total += len(chunk)
            if total > byte_limit:
                raise ValueError("Download byte budget exceeded")
            chunks.append(chunk)
    return b"".join(chunks)


def parse_gaia(raw, field):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if reader.fieldnames != COLUMNS.split(","):
        raise ValueError("Unexpected Gaia schema or archive error response")
    rows, ids = [], set()
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed CSV row")
        identifier = int(row["source_id"])
        ra, dec = float(row["ra"]), float(row["dec"])
        if identifier in ids or not (math.isfinite(ra) and math.isfinite(dec) and 0 <= ra < 360 and -90 <= dec <= 90):
            raise ValueError("Duplicate source or invalid position")
        if separation(ra, dec, field["ra_deg"], field["dec_deg"]) > field["radius_deg"] + 1e-7:
            raise ValueError("Archive returned source outside requested cone")
        ids.add(identifier)
        rows.append(row)
        if len(rows) > budget()["initial_sample_rows"]:
            raise ValueError("Archive exceeded row budget")
    return rows


def fetch_gaia(role, offline=False, cache=None, endpoint=ENDPOINT):
    field = get_needle(role)  # Must precede cache and network access.
    query = gaia_query(field)
    limits = budget()
    cache = cache or cache_directory()
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((endpoint + query).encode()).hexdigest()[:24]
    csv_path, manifest_path = cache / (key + ".csv"), cache / (key + ".json")
    if manifest_path.exists() and csv_path.exists():
        manifest = json.loads(manifest_path.read_text())
        raw = csv_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
            raise ValueError("Cached data checksum mismatch; refusing reuse")
        rows = parse_gaia(raw, field)
        if len(rows) != manifest["row_count"] or manifest["query"] != query:
            raise ValueError("Cache manifest mismatch")
        return rows, manifest, True
    if offline:
        raise FileNotFoundError("No verified cache for this query")
    used = sum(p.stat().st_size for p in cache.rglob("*") if p.is_file())
    cap = limits["max_download_mb_per_batch"] * 1_000_000
    if used + cap > limits["max_local_cache_mb"] * 1_000_000:
        raise ValueError("Insufficient cache budget; remove old data explicitly")
    started = time.monotonic()
    attempt = {"utc": datetime.now(timezone.utc).isoformat(), "needle": role, "endpoint": endpoint, "query": query}
    try:
        raw = bounded_request(endpoint, query, cap, started + limits["max_batch_seconds"])
        rows = parse_gaia(raw, field)
        sha = hashlib.sha256(raw).hexdigest()
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        manifest = dict(attempt, schema_version=1, release="Gaia DR3", table="gaiadr3.gaia_source", field=field,
                        schema_reference=SCHEMA_REFERENCE, sha256=sha, bytes=len(raw), row_count=len(rows),
                        possibly_truncated=len(rows) == limits["initial_sample_rows"], code_revision=revision,
                        code_dirty=dirty, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        python=sys.version, elapsed_seconds=round(time.monotonic()-started, 3), seed=SEED,
                        cache_file=str(csv_path), acknowledgement="ESA Gaia mission / DPAC; https://www.cosmos.esa.int/gaia")
        tmp = csv_path.with_suffix(".tmp")
        tmp.write_bytes(raw)
        tmp.replace(csv_path)
        write_json(manifest_path, manifest)
        attempt.update(status="ok", sha256=sha, row_count=len(rows))
        return rows, manifest, False
    except Exception as exc:
        attempt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        if isinstance(exc, urllib.error.HTTPError):
            attempt["retry_after"] = exc.headers.get("Retry-After")
        raise
    finally:
        attempt["elapsed_seconds"] = round(time.monotonic()-started, 3)
        with (cache / "attempts.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(attempt) + "\n")


def separation(ra1, dec1, ra2, dec2):
    a, b = math.radians(dec1), math.radians(dec2)
    h = math.sin((b-a)/2)**2 + math.cos(a)*math.cos(b)*math.sin(math.radians(ra2-ra1)/2)**2
    return math.degrees(2*math.asin(math.sqrt(min(1, max(0, h)))))


def galactic_latitude(ra, dec):
    d, p = math.radians(dec), math.radians(27.12825)
    return math.degrees(math.asin(math.sin(d)*math.sin(p) + math.cos(d)*math.cos(p)*math.cos(math.radians(ra-192.85948))))


def select_needles():
    rng = random.Random(SEED)
    fields = [{"id": "calibration", "name": "GOODS-South ESO image center",
               "ra_deg": 53.1364166667, "dec_deg": -27.789,
               "radius_deg": 0.1, "locked": False,
               "reference": "https://www.hq.eso.org/public/images/eso1013a/"}]
    for role in ("exploration", "confirmation"):
        while True:
            ra = rng.uniform(0, 360)
            dec = math.degrees(math.asin(rng.uniform(math.sin(math.radians(-60)), math.sin(math.radians(-15)))))
            if abs(galactic_latitude(ra, dec)) < 35:
                continue
            if any(separation(ra, dec, f["ra_deg"], f["dec_deg"]) < 20 for f in fields):
                continue
            fields.append({"id": role, "name": f"Seeded southern {role}",
                           "ra_deg": round(ra, 8), "dec_deg": round(dec, 8),
                           "radius_deg": 0.1, "locked": role == "confirmation"})
            break
    return {"schema_version": 1, "seed": SEED,
            "selection": "Uniform RA and sin(dec) in -60 < dec < -15; |b| >= 35; separation >= 20 degrees. First eligible draws, no source data inspected.",
            "coverage": "Gaia and AllWISE all-sky layers planned. Deeper optical footprint not yet verified; do not infer coverage from declination alone.",
            "confirmation_policy": "No source queries until a minimal claim, rejection criterion and controls are frozen. No override in ordinary dig commands.",
            "needles": fields}


def get_needle(role):
    config = json.loads((ROOT / "config/needles.json").read_text())
    field = next(f for f in config["needles"] if f["id"] == role)
    if field["locked"] or role == "confirmation":
        raise ValueError("Confirmation needle is sealed: freeze a claim before implementing a separate confirmation run.")
    return field


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["needles", "gaia"])
    parser.add_argument("--needle", choices=["calibration", "exploration", "confirmation"], default="calibration")
    parser.add_argument("--offline", action="store_true", help="Require verified cache; make no network request")
    parser.add_argument("--archive", choices=list(ARCHIVES), default="ari", help="Public Gaia archive; no automatic retries")
    parser.add_argument("--output", type=Path, help="Write a portable manifest copy")
    args = parser.parse_args()
    if args.command == "needles":
        print(json.dumps(select_needles(), indent=2))
    elif args.command == "gaia":
        _, manifest, cached = fetch_gaia(args.needle, args.offline, endpoint=ARCHIVES[args.archive])
        if args.output:
            write_json(args.output, manifest)
        print(json.dumps({"needle": args.needle, "rows": manifest["row_count"], "sha256": manifest["sha256"], "cache_hit": cached, "manifest": str(Path(manifest["cache_file"]).with_suffix('.json'))}, indent=2))


if __name__ == "__main__":
    main()

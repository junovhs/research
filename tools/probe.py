"""Exploratory Gaia screening, with depth-conditioned permutation controls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import subprocess
import time

import dig

PERMUTATIONS = 999


def number(row, key):
    try:
        value = float(row[key])
        return value if math.isfinite(value) else None
    except (KeyError, ValueError, TypeError):
        return None


def ranks(values):
    result = [0.] * len(values)
    ordered = sorted(range(len(values)), key=values.__getitem__)
    i = 0
    while i < len(values):
        j = i + 1
        while j < len(values) and values[ordered[j]] == values[ordered[i]]:
            j += 1
        for k in ordered[i:j]:
            result[k] = (i+j-1)/2
        i = j
    return result


def permutation_association(x, y, groups, seed, permutations=PERMUTATIONS):
    """Correlate within-block centered ranks; permute only within each block."""
    if len(x) < 12:
        return {"status": "insufficient", "n": len(x)}
    rx, ry = ranks(x), ranks(y)
    blocks = [[i for i, group in enumerate(groups) if group == key] for key in sorted(set(groups))]
    for block in blocks:
        mx = statistics.mean(rx[i] for i in block)
        my = statistics.mean(ry[i] for i in block)
        for i in block:
            rx[i] -= mx
            ry[i] -= my
    norm = math.sqrt(sum(a*a for a in rx) * sum(b*b for b in ry))
    if norm == 0:
        return {"status": "constant_within_blocks", "n": len(x)}
    observed = sum(a*b for a, b in zip(rx, ry)) / norm
    rng, exceed = random.Random(seed), 0
    for _ in range(permutations):
        shuffled = ry.copy()
        for block in blocks:
            values = [ry[i] for i in block]
            rng.shuffle(values)
            for i, value in zip(block, values):
                shuffled[i] = value
        score = sum(a*b for a, b in zip(rx, shuffled)) / norm
        exceed += abs(score) >= abs(observed) - 1e-14
    return {"status": "ok", "n": len(x), "within_block_rank_correlation": observed,
            "permutation_p": (exceed+1)/(permutations+1), "permutations": permutations,
            "blocks": len(blocks), "block_sizes": [len(block) for block in blocks]}


def derived(row):
    result = {key: number(row, key) for key in ("phot_g_mean_mag", "bp_rp", "ruwe", "phot_bp_rp_excess_factor", "visibility_periods_used")}
    p, e = number(row, "parallax"), number(row, "parallax_error")
    a, b = number(row, "pmra"), number(row, "pmdec")
    result.update(parallax_snr=p/e if p is not None and e is not None and e > 0 else None,
                  proper_motion=math.hypot(a, b) if a is not None and b is not None else None,
                  missing_parallax=int(p is None), missing_color=int(result["bp_rp"] is None))
    return result


def screen(rows, field, permutations=PERMUTATIONS):
    started = time.monotonic()
    values = [derived(row) for row in rows]
    # Declared before looking at results; exploratory tests, not frozen physical claims.
    specs = [
        ("color_motion", "bp_rp", "proper_motion", "magnitude"),
        ("color_parallax_snr", "bp_rp", "parallax_snr", "magnitude"),
        ("fit_photometric_excess", "ruwe", "phot_bp_rp_excess_factor", "magnitude_color"),
        ("brightness_visibility", "phot_g_mean_mag", "visibility_periods_used", "sky"),
        ("parallax_motion", "parallax_snr", "proper_motion", "magnitude"),
        ("brightness_missing_parallax", "phot_g_mean_mag", "missing_parallax", "sky"),
        ("brightness_missing_color", "phot_g_mean_mag", "missing_color", "sky"),
    ]
    probes = []
    for index, (name, xkey, ykey, conditioning) in enumerate(specs):
        eligible = [(i, v) for i, v in enumerate(values) if v[xkey] is not None and v[ykey] is not None
                    and v["phot_g_mean_mag"] is not None and (conditioning != "magnitude_color" or v["bp_rp"] is not None)]
        x, y, groups = [], [], []
        for i, value in eligible:
            magbin = math.floor(value["phot_g_mean_mag"] / 2)
            row = rows[i]
            sky = (float(row["ra"]) >= field["ra_deg"], float(row["dec"]) >= field["dec_deg"])
            group = sky if conditioning == "sky" else (magbin, math.floor(value["bp_rp"])) if conditioning == "magnitude_color" else (magbin,)
            x.append(value[xkey]); y.append(value[ykey]); groups.append(group)
        result = permutation_association(x, y, groups, dig.SEED+index, permutations)
        # Negative control uses a fully shuffled response, then the identical test.
        control_y = y.copy()
        rng = random.Random(dig.SEED+100+index)
        rng.shuffle(control_y)
        control = permutation_association(x, control_y, groups, dig.SEED+200+index, permutations)
        probes.append(dict(id=name, x=xkey, y=ykey, conditioning=conditioning, result=result, negative_control=control))
    radial = [(dig.separation(float(r['ra']), float(r['dec']), field['ra_deg'], field['dec_deg']) / field['radius_deg'])**2 for r in rows]
    def ks_uniform(sample):
        return max((max((i+1)/len(sample)-v, v-i/len(sample)) for i,v in enumerate(sorted(sample))), default=0)
    observed = ks_uniform(radial)
    rng = random.Random(dig.SEED+999)
    exceed = sum(ks_uniform([rng.random() for _ in radial]) >= observed for _ in range(permutations))
    probes.append({"id": "radial_density", "null": "uniform surface density in the cone; selection/crowding can violate this",
                   "result": {"status": "ok" if len(rows) >= 12 else "insufficient", "n": len(rows), "ks_statistic": observed,
                              "permutation_p": (exceed+1)/(permutations+1), "permutations": permutations}})
    family_size = 2 * len(probes)  # Both open needles, conservatively including skipped tests.
    for probe in probes:
        for key in ("result", "negative_control"):
            result = probe.get(key, {})
            if result.get("status") == "ok":
                result["family_adjusted_p"] = min(1, result["permutation_p"] * family_size)
                result["screening_flag"] = result["family_adjusted_p"] <= 0.05
    summary = {}
    for key in values[0] if values else []:
        present = [v[key] for v in values if v[key] is not None]
        summary[key] = {"present": len(present), "missing": len(rows)-len(present),
                        "median": statistics.median(present) if present else None,
                        "min": min(present) if present else None, "max": max(present) if present else None}
    return {"schema_version": 1, "needle": field["id"], "rows": len(rows), "seed": dig.SEED,
            "attempted_probes": len(probes), "negative_controls": len(specs), "planned_family_size": family_size,
            "summary": summary, "probes": probes, "elapsed_seconds": round(time.monotonic()-started, 4),
            "interpretation": "Exploratory screening only. Permutation exchangeability within coarse bins is an approximation; no calibrated physical probability or novelty claim. No confirmation data used.",
            "selection": "No quality filtering; missingness retained. Two-magnitude bins condition selected relationships on depth; sky quadrants condition brightness tests. Magnitude is not distance. Faint-end completeness not measured."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--needle', choices=['calibration', 'exploration', 'confirmation'], default='calibration')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows, manifest, _ = dig.fetch_gaia(args.needle, offline=True, endpoint=dig.ARCHIVES['ari'])
    result = screen(rows, dig.get_needle(args.needle))
    result['input_manifest'] = manifest
    result['code_revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dig.ROOT, text=True).strip()
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dig.write_json(args.output, result)
    flags = [p['id'] for p in result['probes'] if p['result'].get('screening_flag')]
    controls = [p['id'] for p in result['probes'] if p.get('negative_control', {}).get('screening_flag')]
    print(json.dumps({'needle': args.needle, 'rows': len(rows), 'attempted': result['attempted_probes'], 'flags': flags, 'negative_control_flags': controls, 'seconds': result['elapsed_seconds'], 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()

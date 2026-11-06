"""Small, standard-library pencil-beam dig. Run from any directory."""
import argparse
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261106


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
    parser.add_argument("command", choices=["needles"])
    args = parser.parse_args()
    if args.command == "needles":
        print(json.dumps(select_needles(), indent=2))


if __name__ == "__main__":
    main()

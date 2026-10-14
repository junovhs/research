# R-022 probe: full-domain adaptive DOP853 work at R-014 scale (D=512 periodic sites,
# horizon T=16557/64 ~ 258.7), for the same family of periodic cubic Allen-Cahn ODE with
# spatial cosine forcing and piecewise-linear temporal forcing. Work measured as
# function evaluations x D scalar updates. Reference: rtol 1e-12; compared with rtol 1e-10.
import json, os, time
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]
T = cfg["T"]
knots = np.linspace(0.0, T, cfg["n_knots"])
rng = np.random.default_rng(cfg["seed"])
vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
x = np.arange(D, dtype=float)
spatial = np.cos(2*np.pi*x/D)
u0 = rng.uniform(-0.9, 0.9, size=D)

counter = {"n": 0}
def s(t):
    return np.interp(t, knots, vals)
def rhs(t, u):
    counter["n"] += 1
    lap = np.roll(u, -1) - 2*u + np.roll(u, 1)
    return dcoef*lap + u - u**3 + A*s(t)*spatial

def run(rtol):
    counter["n"] = 0
    t0 = time.perf_counter()
    u = u0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=cfg["max_step"])
        u = sol.y[:, -1]
    return u, counter["n"], time.perf_counter()-t0

ref, nref, sref = run(1e-12)
ref2, nref2, sref2 = run(1e-11)
ref_gap = float(np.max(np.abs(ref - ref2)))
out = {"D": D, "T": T, "reference_nfev": nref, "reference_seconds": sref, "reference_rtol1e-11_nfev": nref2, "reference_gap_rtol1e-12_vs_1e-11": ref_gap, "rows": []}
for rt in cfg["rtols"]:
    u, nfev, sec = run(rt)
    out["rows"].append({"rtol": rt, "nfev": nfev, "scalar_updates": nfev*D,
                        "max_abs_err": float(np.max(np.abs(u-ref))), "seconds": sec})
json.dump(out, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
print("reference nfev", nref, "seconds", round(sref, 3), "ref gap 1e-12 vs 1e-11", ref_gap)
for r in out["rows"]:
    print(r["rtol"], r["nfev"], r["scalar_updates"], "%.3e" % r["max_abs_err"], round(r["seconds"], 3))

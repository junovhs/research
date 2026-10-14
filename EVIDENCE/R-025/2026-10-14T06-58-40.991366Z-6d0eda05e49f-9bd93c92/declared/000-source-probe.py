# R-025: horizon sweep of the R-024 comparison-envelope omission at D=512.
# For each horizon T: full reference (DOP853 rtol 1e-12), then patch enclosures
# (rtol 1e-10) for several radii; width = U_c - L_c at the center site.
# Non-rigorous (numerical ODE solver); cooperative comparison (Kamke) with invariant |u|<=M.
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; M = cfg["M"]
x = np.arange(D, dtype=float)
spatial = np.cos(2*np.pi*x/D)
c = cfg["center"]
results = []

for T in cfg["horizons"]:
    knots = np.linspace(0.0, T, cfg["n_knots"])
    rng = np.random.default_rng(cfg["seed"])
    vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
    u0 = rng.uniform(-0.9, 0.9, size=D)
    def s(t): return np.interp(t, knots, vals)
    counter = {"n": 0}
    def full_rhs(t, u):
        counter["n"] += 1
        lap = np.roll(u, -1) - 2*u + np.roll(u, 1)
        return dcoef*lap + u - u**3 + A*s(t)*spatial
    def integrate(rhs, y0, rtol):
        u = y0.copy()
        for k in range(len(knots)-1):
            sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                            rtol=rtol, atol=rtol, max_step=cfg["max_step"])
            u = sol.y[:, -1]
        return u
    counter["n"] = 0
    ref = integrate(full_rhs, u0, 1e-12)
    full_updates = counter["n"] * D
    rows = []
    for R in cfg["radii"]:
        idx = np.arange(c-R, c+R+1); sp = spatial[idx]
        def make_rhs(bval):
            def rhs(t, p):
                counter["n"] += 1
                pe = np.concatenate(([bval], p, [bval]))
                return dcoef*(pe[2:] - 2*p + pe[:-2]) + p - p**3 + A*s(t)*sp
            return rhs
        counter["n"] = 0
        up = integrate(make_rhs(+M), u0[idx], 1e-10)
        lo = integrate(make_rhs(-M), u0[idx], 1e-10)
        upd = counter["n"] * (2*R+1)
        rows.append({"R": R, "width": float(up[R]-lo[R]),
                     "lower_minus_ref": float(lo[R]-ref[c]), "upper_minus_ref": float(up[R]-ref[c]),
                     "patch_scalar_updates": upd, "full_scalar_updates": full_updates})
    results.append({"T": T, "ref_center": float(ref[c]), "full_scalar_updates": full_updates, "rows": rows})
    print("T", T, "full", full_updates, flush=True)
    for r in rows:
        print("  R", r["R"], "width %.3e" % r["width"], "upd", r["patch_scalar_updates"], flush=True)

json.dump({"D": D, "M": M, "center": c, "results": results},
          open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)

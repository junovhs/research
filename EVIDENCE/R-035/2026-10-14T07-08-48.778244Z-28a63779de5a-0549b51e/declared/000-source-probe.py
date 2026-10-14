# R-035: per-case minimal radius for a valid center width <= 1e-9 at patch rtol 1e-9
# (max_step 1.0, M=1.19), for the R-034 cases that failed at rtol 1e-7. Radii R=14..30.
# A case is accepted only if containment holds against the rtol 1e-12 full reference.
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; T = cfg["T"]
M = cfg["M"]; ms = cfg["max_step"]; prt = cfg["patch_rtol"]
x = np.arange(D, dtype=float); spatial = np.cos(2*np.pi*x/D)
def integ(rhs, y0, knots, rtol, count):
    y = y0.copy()
    def g(t, p):
        count[0] += 1
        return rhs(t, p)
    for k in range(len(knots)-1):
        sol = solve_ivp(g, (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=ms)
        y = sol.y[:, -1]
    return y
rows = []
for seed in cfg["seeds"]:
    knots = np.linspace(0.0, T, cfg["n_knots"])
    rng = np.random.default_rng(seed)
    vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
    u0 = rng.uniform(-0.9, 0.9, size=D)
    def s(t, knots=knots, vals=vals): return np.interp(t, knots, vals)
    def full_rhs(t, u):
        return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
    ref = integ(full_rhs, u0, knots, 1e-12, [0])
    for c in cfg["centers"]:
        found = None; tried = []
        for R in cfg["radii"]:
            idx = np.arange(c-R, c+R+1); sp = spatial[idx]
            def make_rhs(bval):
                def rhs(t, p):
                    pe = np.concatenate(([bval], p, [bval]))
                    return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
                return rhs
            up = integ(make_rhs(+M), u0[idx], knots, prt, [0])
            lo = integ(make_rhs(-M), u0[idx], knots, prt, [0])
            w = float(up[R]-lo[R]); ok = bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10)
            tried.append({"R": R, "width": w, "contains": ok})
            if ok and w <= 1e-9:
                found = {"R": R, "width": w, "sites": 2*R+1}; break
        rows.append({"seed": seed, "center": c, "minimal": found, "tried": tried})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["seed"], r["center"], r["minimal"])

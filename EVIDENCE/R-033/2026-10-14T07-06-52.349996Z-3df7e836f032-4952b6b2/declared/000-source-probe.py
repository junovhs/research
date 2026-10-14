# R-033: integrator choice for the final envelope patch solve (R=18, M=1.19, rtol 1e-7,
# max_step 1.0, D=512, T=258.7). Compares DOP853, RK45 and LSODA on width, containment
# against the rtol 1e-12 reference, and right-hand-side evaluations x sites.
import json, os, time
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; T = cfg["T"]; c = cfg["center"]
knots = np.linspace(0.0, T, cfg["n_knots"])
rng = np.random.default_rng(cfg["seed"])
vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
u0 = rng.uniform(-0.9, 0.9, size=D)
x = np.arange(D, dtype=float); spatial = np.cos(2*np.pi*x/D)
def s(t): return np.interp(t, knots, vals)
cnt = {"n": 0}
def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
def integ(rhs, y0, method, rtol, ms):
    cnt["n"] = 0
    def g(t, p):
        cnt["n"] += 1
        return rhs(t, p)
    y = y0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(g, (knots[k], knots[k+1]), y, method=method,
                        rtol=rtol, atol=rtol, max_step=ms)
        y = sol.y[:, -1]
    return y, cnt["n"]
ref, _ = integ(full_rhs, u0, "DOP853", 1e-12, 0.125)
R = cfg["R"]; M = cfg["M"]; ms = cfg["max_step"]; rt = cfg["rtol"]
idx = np.arange(c-R, c+R+1); sp = spatial[idx]
def make_rhs(bval):
    def rhs(t, p):
        pe = np.concatenate(([bval], p, [bval]))
        return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
    return rhs
rows = []
for m in cfg["methods"]:
    t0 = time.perf_counter()
    up, nu = integ(make_rhs(+M), u0[idx], m, rt, ms)
    lo, nl = integ(make_rhs(-M), u0[idx], m, rt, ms)
    sec = time.perf_counter() - t0
    rows.append({"method": m, "width": float(up[R]-lo[R]),
                 "contains_ref_1e-10": bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10),
                 "envelope_updates": (nu+nl)*(2*R+1), "seconds": sec})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["method"], "%.3e" % r["width"], r["contains_ref_1e-10"], r["envelope_updates"], round(r["seconds"], 3))

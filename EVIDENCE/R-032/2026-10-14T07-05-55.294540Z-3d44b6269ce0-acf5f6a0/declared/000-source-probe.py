# R-032: minimal radius under the final envelope settings (M=1.19, patch rtol 1e-7,
# max_step 1.0) at D=512, T=258.7. Width, containment and cost for R=16,17,18.
import json, os
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
def integ(rhs, y0, rtol, ms):
    cnt["n"] = 0
    y = y0.copy()
    def g(t, p):
        cnt["n"] += 1
        return rhs(t, p)
    for k in range(len(knots)-1):
        sol = solve_ivp(g, (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=ms)
        y = sol.y[:, -1]
    return y, cnt["n"]
def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
ref, _ = integ(full_rhs, u0, 1e-12, 0.125)
M = cfg["M"]; ms = cfg["max_step"]; rt = cfg["patch_rtol"]
rows = []
for R in cfg["radii"]:
    idx = np.arange(c-R, c+R+1); sp = spatial[idx]
    def make_rhs(bval):
        def rhs(t, p):
            pe = np.concatenate(([bval], p, [bval]))
            return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
        return rhs
    up, nu = integ(make_rhs(+M), u0[idx], rt, ms)
    lo, nl = integ(make_rhs(-M), u0[idx], rt, ms)
    rows.append({"R": R, "sites": 2*R+1, "width": float(up[R]-lo[R]),
                 "contains_ref_1e-10": bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10),
                 "envelope_updates": (nu+nl)*(2*R+1)})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["R"], r["sites"], "%.3e" % r["width"], r["contains_ref_1e-10"], r["envelope_updates"])

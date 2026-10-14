# R-029: effect of the solver max_step cap on scalar-update cost (envelope R=18, M=1.19,
# rtol 1e-9; full-domain DOP853 at rtol 1e-9) at D=512, T=258.7. Width and containment
# are re-checked at each cap, so any cost change must come with unchanged accuracy.
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
def wrap(f):
    def g(t, y):
        cnt["n"] += 1
        return f(t, y)
    return g
def integ(rhs, y0, rtol, max_step):
    cnt["n"] = 0
    y = y0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(wrap(rhs), (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=max_step)
        y = sol.y[:, -1]
    return y, cnt["n"]
def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
ref, _ = integ(full_rhs, u0, 1e-12, 0.125)
R = cfg["R"]; M = cfg["M"]; rt = cfg["rtol"]
idx = np.arange(c-R, c+R+1); sp = spatial[idx]
def make_rhs(bval):
    def rhs(t, p):
        pe = np.concatenate(([bval], p, [bval]))
        return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
    return rhs
rows = []
for ms in cfg["max_steps"]:
    up, nu = integ(make_rhs(+M), u0[idx], rt, ms)
    lo, nl = integ(make_rhs(-M), u0[idx], rt, ms)
    env_upd = (nu+nl)*(2*R+1)
    full, nf = integ(full_rhs, u0, rt, ms)
    full_upd = nf*D
    rows.append({"max_step": ms, "width": float(up[R]-lo[R]),
                 "contains_ref": bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10),
                 "env_updates": env_upd, "full_updates": full_upd,
                 "ratio": env_upd/full_upd,
                 "full_err_vs_ref": float(np.max(np.abs(full-ref)))})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["max_step"], "%.3e" % r["width"], r["contains_ref"], r["env_updates"], r["full_updates"], "%.4f" % r["ratio"], "%.2e" % r["full_err_vs_ref"])

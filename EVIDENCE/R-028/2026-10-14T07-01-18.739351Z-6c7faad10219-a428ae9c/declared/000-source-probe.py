# R-028: scalar-update cost of the R-027 minimal configuration (M=1.19, R=18, two patch
# bounds) versus a full-domain DOP853 specialist at the same tolerance (rtol 1e-9),
# with the width and containment recorded. Scalar updates = function evals x sites.
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
def integ(rhs, y0, rtol):
    cnt["n"] = 0
    y = y0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(wrap(rhs), (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=cfg["max_step"])
        y = sol.y[:, -1]
    return y, cnt["n"]

def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
ref, _ = integ(full_rhs, u0, 1e-12)
R = cfg["R"]; M = cfg["M"]
idx = np.arange(c-R, c+R+1); sp = spatial[idx]
def make_rhs(bval):
    def rhs(t, p):
        pe = np.concatenate(([bval], p, [bval]))
        return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
    return rhs
rows = []
for rt in cfg["rtols"]:
    up, nu = integ(make_rhs(+M), u0[idx], rt)
    lo, nl = integ(make_rhs(-M), u0[idx], rt)
    upd_env = (nu + nl) * (2*R+1)
    full, nf = integ(full_rhs, u0, rt)
    upd_full = nf * D
    rows.append({"rtol": rt, "R": R, "M": M, "width": float(up[R]-lo[R]),
                 "contains_ref": bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10),
                 "envelope_scalar_updates": upd_env,
                 "full_specialist_scalar_updates": upd_full,
                 "full_error_vs_ref": float(np.max(np.abs(full-ref))),
                 "ratio_env_over_full": upd_env/upd_full})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["rtol"], "width %.3e" % r["width"], r["contains_ref"], "env %.3e full %.3e ratio %.4f full_err %.2e" % (r["envelope_scalar_updates"], r["full_specialist_scalar_updates"], r["ratio_env_over_full"], r["full_error_vs_ref"]))

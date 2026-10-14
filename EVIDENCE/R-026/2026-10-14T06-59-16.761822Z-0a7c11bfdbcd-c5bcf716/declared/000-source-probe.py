# R-026: check the two assumptions behind the R-024/R-025 comparison envelope at D=512, T=258.7:
# (1) the full trajectory stays in the invariant box |u|<=M (M=1.2), sampled densely;
# (2) the patch enclosures contain the full reference at the center for each radius.
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; M = cfg["M"]; T = cfg["T"]; c = cfg["center"]
knots = np.linspace(0.0, T, cfg["n_knots"])
rng = np.random.default_rng(cfg["seed"])
vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
u0 = rng.uniform(-0.9, 0.9, size=D)
x = np.arange(D, dtype=float); spatial = np.cos(2*np.pi*x/D)
def s(t): return np.interp(t, knots, vals)
def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial

# (1) dense trajectory, track global max |u| and max |s| used
max_abs = 0.0; max_s = float(np.max(np.abs(vals)))
u = u0.copy()
for k in range(len(knots)-1):
    sol = solve_ivp(full_rhs, (knots[k], knots[k+1]), u, method="DOP853",
                    rtol=1e-10, atol=1e-10, max_step=cfg["max_step"], dense_output=True)
    ts = np.linspace(knots[k], knots[k+1], 200)
    max_abs = max(max_abs, float(np.max(np.abs(sol.sol(ts)))))
    u = sol.y[:, -1]
ref_c = float(u[c])
box_margin = M**3 - M - A*max_s   # invariance margin for reaction vs forcing
# (2) containment per radius (patch rtol 1e-10, same as R-025)
rows = []
for R in cfg["radii"]:
    idx = np.arange(c-R, c+R+1); sp = spatial[idx]
    def make_rhs(bval):
        def rhs(t, p):
            pe = np.concatenate(([bval], p, [bval]))
            return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
        return rhs
    def integ(rhs):
        y = u0[idx].copy()
        for k in range(len(knots)-1):
            sol = solve_ivp(rhs, (knots[k], knots[k+1]), y, method="DOP853",
                            rtol=1e-10, atol=1e-10, max_step=cfg["max_step"])
            y = sol.y[:, -1]
        return y
    up = integ(make_rhs(+M)); lo = integ(make_rhs(-M))
    rows.append({"R": R, "lower": float(lo[R]), "upper": float(up[R]),
                 "contains_ref_1e-10_tol": bool(lo[R]-1e-10 <= ref_c <= up[R]+1e-10)})
out = {"max_abs_full_trajectory": max_abs, "M": M, "box_margin_M3_minus_M_minus_A_max_s": box_margin,
       "max_abs_s": max_s, "ref_center": ref_c, "rows": rows}
json.dump(out, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
print("max|u| full", max_abs, "margin", box_margin)
for r in rows: print(r["R"], r["contains_ref_1e-10_tol"], r["lower"], r["upper"])

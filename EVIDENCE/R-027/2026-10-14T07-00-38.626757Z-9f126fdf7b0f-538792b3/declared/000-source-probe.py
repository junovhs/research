# R-027: minimal patch radius for center width <= 1e-9 at D=512, T=258.7, with two
# tuning knobs: invariant box M (analytic check M^3-M >= A*max|s|) and patch rtol.
# Containment against a DOP853 rtol=1e-12 full reference is checked per configuration.
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
max_s = float(np.max(np.abs(vals)))
def s(t): return np.interp(t, knots, vals)

def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
def integ(rhs, y0, rtol, counter):
    y = y0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(rhs, (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=cfg["max_step"])
        y = sol.y[:, -1]
    return y

ref = integ(full_rhs, u0, 1e-12, {"n": 0})
rows = []
for M in cfg["M_list"]:
    margin = M**3 - M - A*max_s
    if margin < 0:
        rows.append({"M": M, "valid_invariant": False, "margin": margin}); continue
    for rt in cfg["patch_rtols"]:
        found = None
        for R in cfg["radii"]:
            idx = np.arange(c-R, c+R+1); sp = spatial[idx]
            def make_rhs(bval):
                def rhs(t, p):
                    pe = np.concatenate(([bval], p, [bval]))
                    return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
                return rhs
            up = integ(make_rhs(+M), u0[idx], rt, {"n": 0})
            lo = integ(make_rhs(-M), u0[idx], rt, {"n": 0})
            width = float(up[R]-lo[R])
            contains = bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10)
            if width <= 1e-9 and contains:
                found = {"R": R, "width": width, "sites": 2*R+1}
                break
        rows.append({"M": M, "valid_invariant": True, "margin": margin,
                     "patch_rtol": rt, "minimal": found})
        print(M, rt, found, flush=True)
json.dump({"max_abs_s": max_s, "ref_center": float(ref[c]), "rows": rows},
          open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)

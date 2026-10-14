# R-024: continuous-time comparison-envelope omission for one site of the D=512 ODE.
# Invariant box |u|<=M with M=1.2 (check: M^3-M=0.528 >= A*max|s|=0.5 for |s|<=1),
# so exterior sites bounded by +/-M. Cooperative (Kamke) structure: d/du_j of the
# diffusion term is +d >= 0 for neighbours. Patch of radius R around center:
# upper patch ODE uses exterior=+M, lower uses -M, true initial state on the patch.
# Enclosure L_c(T) <= u_c(T) <= U_c(T). Non-rigorous (numerical ODE solver).
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; T = cfg["T"]; M = cfg["M"]
knots = np.linspace(0.0, T, cfg["n_knots"])
rng = np.random.default_rng(cfg["seed"])
vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
x = np.arange(D, dtype=float)
spatial = np.cos(2*np.pi*x/D)
u0 = rng.uniform(-0.9, 0.9, size=D)
c = cfg["center"]

def s(t): return np.interp(t, knots, vals)

counter = {"n": 0}
def full_rhs(t, u):
    counter["n"] += 1
    lap = np.roll(u, -1) - 2*u + np.roll(u, 1)
    return dcoef*lap + u - u**3 + A*s(t)*spatial

def integrate(rhs, y0):
    u = y0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                        rtol=cfg["rtol"], atol=cfg["rtol"], max_step=cfg["max_step"])
        u = sol.y[:, -1]
    return u

counter["n"] = 0
ref = integrate(full_rhs, u0)
full_nfev = counter["n"]
full_updates = full_nfev * D

rows = []
for R in cfg["radii"]:
    idx = np.arange(c-R, c+R+1)
    sp = spatial[idx]
    # patch RHS with exterior sign fixed: bc value b applied to the two edge neighbours
    def make_rhs(bval):
        def rhs(t, p):
            counter["n"] += 1
            pe = np.concatenate(([bval], p, [bval]))
            lap = pe[2:] - 2*p + pe[:-2]
            return dcoef*lap + p - p**3 + A*s(t)*sp
        return rhs
    counter["n"] = 0
    up = integrate(make_rhs(+M), u0[idx])
    lo = integrate(make_rhs(-M), u0[idx])
    nfev_patch = counter["n"]
    Uc = float(up[R]); Lc = float(lo[R]); refc = float(ref[c])
    rows.append({"R": R, "patch_sites": 2*R+1, "U_c": Uc, "L_c": Lc,
                 "width": Uc-Lc, "contains_ref": bool(Lc <= refc <= Uc),
                 "patch_scalar_updates": nfev_patch*(2*R+1)})

out = {"D": D, "T": T, "M": M, "center": c, "ref_center": float(ref[c]),
       "full_nfev": full_nfev, "full_scalar_updates": full_updates, "rows": rows}
json.dump(out, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
print("full scalar updates", full_updates)
for r in rows:
    print(r["R"], r["patch_sites"], "%.3e" % r["width"], r["contains_ref"], r["patch_scalar_updates"])

# R-036: honest per-case cost of an adaptive-radius envelope (increase R until width<=1e-9
# and containment holds; every failed attempt is charged) versus a full-domain DOP853
# specialist at rtol 3e-10 for the same seed. D=512, T=258.7, M=1.19, patch rtol 1e-9, max_step 1.0.
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
    cs = [0]
    spec = integ(full_rhs, u0, knots, cfg["specialist_rtol"], cs)
    spec_upd = cs[0]*D
    spec_err = float(np.max(np.abs(spec-ref)))
    for c in cfg["centers"]:
        charged = 0; final = None
        for R in cfg["radii"]:
            idx = np.arange(c-R, c+R+1); sp = spatial[idx]
            def make_rhs(bval):
                def rhs(t, p):
                    pe = np.concatenate(([bval], p, [bval]))
                    return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
                return rhs
            cu = [0]; cl = [0]
            up = integ(make_rhs(+M), u0[idx], knots, prt, cu)
            lo = integ(make_rhs(-M), u0[idx], knots, prt, cl)
            charged += (cu[0]+cl[0])*(2*R+1)
            w = float(up[R]-lo[R]); ok = bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10)
            if ok and w <= 1e-9:
                final = {"R": R, "width": w}; break
        rows.append({"seed": seed, "center": c, "adaptive_charged_updates": charged,
                     "final": final, "specialist_updates": spec_upd,
                     "specialist_err_vs_ref": spec_err,
                     "ratio": (charged/spec_upd) if final else None})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["seed"], r["center"], r["final"], r["adaptive_charged_updates"], r["specialist_updates"], r["ratio"])

# R-034: generalization of the final envelope (M=1.19, R=18, patch rtol 1e-7, max_step 1.0)
# over three seeds and two centers at D=512, T=258.7; plus a direct full-domain DOP853
# specialist run at rtol 3e-10 (max_step 1.0) for the seed-1 case, to replace the R-030
# log-interpolated matched-accuracy estimate.
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; T = cfg["T"]
M = cfg["M"]; R = cfg["R"]; ms = cfg["max_step"]; prt = cfg["patch_rtol"]
x = np.arange(D, dtype=float); spatial = np.cos(2*np.pi*x/D)

def setup(seed):
    knots = np.linspace(0.0, T, cfg["n_knots"])
    rng = np.random.default_rng(seed)
    vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
    u0 = rng.uniform(-0.9, 0.9, size=D)
    return knots, vals, u0

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
    knots, vals, u0 = setup(seed)
    def s(t, knots=knots, vals=vals): return np.interp(t, knots, vals)
    def full_rhs(t, u):
        return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
    ref = integ(full_rhs, u0, knots, 1e-12, [0])
    for c in cfg["centers"]:
        idx = np.arange(c-R, c+R+1); sp = spatial[idx]
        def make_rhs(bval):
            def rhs(t, p):
                pe = np.concatenate(([bval], p, [bval]))
                return dcoef*(pe[2:]-2*p+pe[:-2]) + p - p**3 + A*s(t)*sp
            return rhs
        cu = [0]; cl = [0]
        up = integ(make_rhs(+M), u0[idx], knots, prt, cu)
        lo = integ(make_rhs(-M), u0[idx], knots, prt, cl)
        upd = (cu[0]+cl[0])*(2*R+1)
        rows.append({"seed": seed, "center": c, "width": float(up[R]-lo[R]),
                     "contains_ref_1e-10": bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10),
                     "envelope_updates": upd})
# direct specialist at matched accuracy (seed 1st entry, center 256)
knots, vals, u0 = setup(cfg["seeds"][0])
def s(t): return np.interp(t, knots, vals)
def full_rhs(t, u):
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
ref = integ(full_rhs, u0, knots, 1e-12, [0])
cs = [0]
y = integ(full_rhs, u0, knots, cfg["specialist_rtol"], cs)
spec = {"rtol": cfg["specialist_rtol"], "scalar_updates": cs[0]*D,
        "err_vs_ref": float(np.max(np.abs(y-ref)))}
json.dump({"rows": rows, "specialist": spec}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["seed"], r["center"], "%.3e" % r["width"], r["contains_ref_1e-10"], r["envelope_updates"])
print("specialist", spec)

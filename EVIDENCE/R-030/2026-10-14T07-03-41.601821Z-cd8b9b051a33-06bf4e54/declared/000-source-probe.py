# R-030: matched-accuracy full-domain DOP853 specialist at max_step=1.0 (D=512, T=258.7).
# Sweeps rtol so the specialist's achieved max-norm error vs rtol 1e-12 reference
# can be compared with the envelope's width/accuracy at equal cost.
import json, os
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]; T = cfg["T"]
knots = np.linspace(0.0, T, cfg["n_knots"])
rng = np.random.default_rng(cfg["seed"])
vals = rng.uniform(-1.0, 1.0, size=cfg["n_knots"]); vals[0] = 0.0; vals[-1] = 0.0
u0 = rng.uniform(-0.9, 0.9, size=D)
x = np.arange(D, dtype=float); spatial = np.cos(2*np.pi*x/D)
def s(t): return np.interp(t, knots, vals)
cnt = {"n": 0}
def full_rhs(t, u):
    cnt["n"] += 1
    return dcoef*(np.roll(u,-1)-2*u+np.roll(u,1)) + u - u**3 + A*s(t)*spatial
def integ(rtol, ms):
    cnt["n"] = 0
    y = u0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(full_rhs, (knots[k], knots[k+1]), y, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=ms)
        y = sol.y[:, -1]
    return y, cnt["n"]
ref, _ = integ(1e-12, 0.125)
rows = []
for rt in cfg["rtols"]:
    y, nf = integ(rt, cfg["max_step"])
    rows.append({"rtol": rt, "max_step": cfg["max_step"], "scalar_updates": nf*D,
                 "err_vs_ref": float(np.max(np.abs(y-ref)))})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["rtol"], r["scalar_updates"], "%.3e" % r["err_vs_ref"])

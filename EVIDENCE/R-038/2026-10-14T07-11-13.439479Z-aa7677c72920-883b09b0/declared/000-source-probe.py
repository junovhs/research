# R-037: predict-then-verify radius policy for the envelope (same six cases as R-034/R-036).
# Start at R0=14 and R1=16, estimate the per-site decay rate kappa from the two widths,
# predict R* = R1 + ceil(ln(w1/1e-9)/kappa) + 1, verify; if it fails, step R by +2.
# Every attempt is charged (both bounds). Compared with the R-036 specialist (rtol 3e-10).
import json, os, math
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
    for c in cfg["centers"]:
        charged = 0; log = []
        def attempt(R):
            global charged_acc
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
            w = float(up[R]-lo[R]); ok = bool(lo[R]-1e-10 <= ref[c] <= up[R]+1e-10)
            return w, ok, upd
        R0, R1 = cfg["R0"], cfg["R1"]
        w0, ok0, u0c = attempt(R0); w1, ok1, u1c = attempt(R1)
        charged = u0c + u1c; log.append({"R": R0, "w": w0, "ok": ok0}); log.append({"R": R1, "w": w1, "ok": ok1})
        final = None
        if ok1 and w1 <= 1e-9:
            final = {"R": R1, "width": w1}
        else:
            # per-site decay rate from the two widths (valid only if both widths are positive and decreasing)
            # fixed policy: only predict when the width decays materially (w1 < 0.5*w0);
            # otherwise (saturated / non-decaying) step by +2 from R1. Predicted R capped at R1+30.
            if w0 > 0 and w1 > 0 and w1 < 0.5*w0:
                kappa = math.log(w0/w1)/(R1-R0)
                Rstar = R1 + min(30, math.ceil(math.log(w1/1e-9)/kappa) + 1)
            else:
                Rstar = R1 + 2
            R = max(Rstar, R1+1)
            while R <= cfg["Rmax"]:
                w, ok, upd = attempt(R); charged += upd
                log.append({"R": R, "w": w, "ok": ok})
                if ok and w <= 1e-9:
                    final = {"R": R, "width": w}; break
                R += 2
        rows.append({"seed": seed, "center": c, "final": final, "charged_updates": charged, "attempts": log})
json.dump({"rows": rows}, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
for r in rows: print(r["seed"], r["center"], r["final"], r["charged_updates"], [a["R"] for a in r["attempts"]])

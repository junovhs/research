# R-021 probe: work (function evaluations) needed to reach a 1e-9 max-norm terminal error
# for the same periodic cubic Allen-Cahn ODE as R-020, by several time integrators.
# Reference: DOP853 at rtol=1e-13; cross-checked against rtol=1e-12 to bound reference error.
import json, os, time
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; T = cfg["T"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]
knots = np.array(cfg["forcing_knots_t"], dtype=float)
vals = np.array(cfg["forcing_knots_v"], dtype=float)
x = np.arange(D, dtype=float)
spatial = np.cos(2*np.pi*x/D)
u0 = np.array(cfg["u0"], dtype=float)

counter = {"n": 0}
def s(t):
    return np.interp(t, knots, vals)
def rhs(t, u):
    counter["n"] += 1
    lap = np.roll(u, -1) - 2*u + np.roll(u, 1)
    return dcoef*lap + u - u**3 + A*s(t)*spatial

def reference(rtol):
    u = u0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=0.125)
        u = sol.y[:, -1]
    return u

ref13 = reference(1e-13)
ref12 = reference(1e-12)
ref_gap = float(np.max(np.abs(ref13 - ref12)))

def rk4(m):
    h = 1.0/m; n = int(round(T/h)); u = u0.copy(); t = 0.0
    counter["n"] = 0
    for _ in range(n):
        k1 = rhs(t, u); k2 = rhs(t+h/2, u+h/2*k1)
        k3 = rhs(t+h/2, u+h/2*k2); k4 = rhs(t+h, u+h*k3)
        u = u + h/6*(k1+2*k2+2*k3+k4); t += h
    return u, counter["n"]

def dop853_rtol(rtol):
    counter["n"] = 0
    u = u0.copy()
    for k in range(len(knots)-1):
        sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                        rtol=rtol, atol=rtol, max_step=0.125)
        u = sol.y[:, -1]
    return u, counter["n"]

rows = []
for m in cfg["rk4_m"]:
    u, nfev = rk4(m)
    rows.append({"method": "RK4_fixed", "param": m, "nfev": nfev,
                 "max_abs_err": float(np.max(np.abs(u - ref13)))})
for rt in cfg["dop853_rtol"]:
    t0 = time.perf_counter()
    u, nfev = dop853_rtol(rt)
    rows.append({"method": "DOP853_adaptive", "param": rt, "nfev": nfev,
                 "max_abs_err": float(np.max(np.abs(u - ref13))),
                 "seconds": time.perf_counter()-t0})

out = {"reference_gap_rtol13_vs_rtol12": ref_gap, "rows": rows}
json.dump(out, open(os.path.join(os.environ["DTL_RUN_DIR"], "results.json"), "w"), indent=1)
print("reference gap rtol1e-13 vs 1e-12:", ref_gap)
for r in rows:
    print(r["method"], r["param"], "nfev", r["nfev"], "err", "%.3e" % r["max_abs_err"])

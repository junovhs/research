# R-020 probe: time-discretization error of the R-014-style explicit Euler recurrence
# versus a tight-tolerance DOP853 reference, for the same periodic cubic Allen-Cahn ODE
# with piecewise-linear, spatially cosine-shaped forcing. Continuous-model target.
import json, os, time
import numpy as np
from scipy.integrate import solve_ivp

cfg = json.load(open("probe.json"))
D = cfg["D"]; T = cfg["T"]; A = cfg["amplitude"]; dcoef = cfg["diffusion"]
knots = np.array(cfg["forcing_knots_t"], dtype=float)
vals = np.array(cfg["forcing_knots_v"], dtype=float)   # temporal profile s(t) at knots
x = np.arange(D, dtype=float)
spatial = np.cos(2*np.pi*x/D)
u0 = np.array(cfg["u0"], dtype=float)
assert u0.shape == (D,)

def s(t):
    return np.interp(t, knots, vals)

def rhs(t, u):
    lap = np.roll(u, -1) - 2*u + np.roll(u, 1)
    return dcoef*lap + u - u**3 + A*s(t)*spatial

def euler(h):
    n = int(round(T/h))
    u = u0.copy(); t = 0.0
    for _ in range(n):
        u = u + h*rhs(t, u); t += h
    return u, n

# reference: DOP853 split at forcing knots, tight tolerance
ref_t0 = time.perf_counter()
u = u0.copy(); t = 0.0
for k in range(len(knots)-1):
    sol = solve_ivp(rhs, (knots[k], knots[k+1]), u, method="DOP853",
                    rtol=1e-12, atol=1e-12, max_step=0.125)
    u = sol.y[:, -1]
ref = u
ref_sec = time.perf_counter() - ref_t0

out = {"D": D, "T": T, "amplitude": A, "diffusion": dcoef,
       "reference_seconds": ref_sec, "rows": []}
for m in cfg["refinements"]:
    h = 1.0/m
    t0 = time.perf_counter()
    ue, n = euler(h)
    dt_sec = time.perf_counter() - t0
    err_inf = float(np.max(np.abs(ue - ref)))
    err_site0 = float(abs(ue[0] - ref[0]))
    out["rows"].append({"h": h, "steps": n, "max_abs_err": err_inf,
                        "site0_abs_err": err_site0, "euler_seconds": dt_sec})

outdir = os.environ["DTL_RUN_DIR"]
json.dump({"reference_terminal": ref.tolist(), **out},
          open(os.path.join(outdir, "results.json"), "w"), indent=1)
for r in out["rows"]:
    print(f"h={r['h']:.6g} steps={r['steps']} max_err={r['max_abs_err']:.6e} site0={r['site0_abs_err']:.6e}")
print("reference_seconds", round(ref_sec, 3))

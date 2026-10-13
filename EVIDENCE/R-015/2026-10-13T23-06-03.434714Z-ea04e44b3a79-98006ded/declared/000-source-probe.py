"""Exploratory semidiscrete Allen--Cahn phase-envelope probe (stdlib only)."""
import json
import math
import os
from pathlib import Path

cfg = json.loads(Path('config.json').read_text(encoding='utf-8'))
t0, tail, step = cfg['unforced_time'], cfg['tail_time'], cfg['step']
assert round(t0 / step) * step == t0
assert round(tail / step) * step == tail

def free_flow(x, t):
    return math.copysign(1 / math.sqrt(1 + (1 / (x*x) - 1) * math.exp(-2*t)), x)

def rhs_scalar(x, b):
    return x - x*x*x + b

def rk4_scalar(x, duration, h, b):
    for _ in range(round(duration / h)):
        a = rhs_scalar(x, b)
        c = rhs_scalar(x + h*a/2, b)
        d = rhs_scalar(x + h*c/2, b)
        e = rhs_scalar(x + h*d, b)
        x += h*(a + 2*c + 2*d + e)/6
    return x

def rk4_field(v, duration, h, b, diffusivity):
    def f(y):
        n = len(y)
        return [diffusivity*(y[(i-1)%n]-2*y[i]+y[(i+1)%n])
                + y[i]-y[i]**3+b for i in range(n)]
    def shift(y,k,scale):
        return [a + scale*c for a,c in zip(y,k)]
    for _ in range(round(duration / h)):
        a = f(v)
        c = f(shift(v,a,h/2))
        d = f(shift(v,c,h/2))
        e = f(shift(v,d,h))
        v = [x+h*(p+2*q+2*r+s)/6 for x,p,q,r,s in zip(v,a,c,d,e)]
    return v

runs = []
for phase, pulse in [('positive', 0.0), ('positive', -0.25), ('negative', -0.25)]:
    lo, hi = (0.5, 2.0) if phase == 'positive' else (-2.0, -0.5)
    a, z = free_flow(lo,t0), free_flow(hi,t0)
    a1 = rk4_scalar(a,tail,step,pulse)
    z1 = rk4_scalar(z,tail,step,pulse)
    a2 = rk4_scalar(a,tail,step/2,pulse)
    z2 = rk4_scalar(z,tail,step/2,pulse)
    # Heterogeneous field, all coordinates in the declared phase box.
    n = cfg['sites']
    field = [lo + (hi-lo)*((7*i+3) % n)/(n-1) for i in range(n)]
    field = [free_flow(x,t0) for x in field] if cfg['diffusivity'] == 0 else field
    if cfg['diffusivity']:
        field = rk4_field(field,t0,step,0.0,cfg['diffusivity'])
    field = rk4_field(field,tail,step,pulse,cfg['diffusivity'])
    bound = (z-a)*math.exp(-cfg['contraction_rate']*tail)
    record = dict(phase=phase, pulse=pulse, pre_interval=[a,z],
                  terminal_interval_rk4_fine=[a2,z2],
                  terminal_interval_rk4_coarse=[a1,z1],
                  terminal_width_observed=z2-a2,
                  interval_width_contraction_bound=bound,
                  observed_step_halving=max(abs(a1-a2),abs(z1-z2)),
                  field_center=field[n//2], field_min=min(field), field_max=max(field),
                  field_inside_rk4_envelope=(a2-1e-11 <= min(field) and max(field) <= z2+1e-11))
    runs.append(record)
assert all(r['field_inside_rk4_envelope'] for r in runs)
assert runs[1]['interval_width_contraction_bound'] < cfg['target_width']
assert abs(runs[1]['field_center'] - 1.0) > .05
assert abs(runs[1]['field_center'] - runs[2]['field_center']) > 1.5
out = dict(config=cfg, cases=runs, scope='semidiscrete continuous-time ODE, not continuum PDE; RK4 numbers diagnostic only')
Path(os.environ['DTL_RUN_DIR'],'output.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'cases':len(runs),'pulse_center':runs[1]['field_center'], 'positive_width_bound':runs[1]['interval_width_contraction_bound'], 'opposite_phase_gap':abs(runs[1]['field_center']-runs[2]['field_center'])},sort_keys=True))

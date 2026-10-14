#!/usr/bin/env python3
"""R-019: exact stoichiometric invariant and sparse-output reactive tracer query.
RESEARCH ONLY. Not EPANET, nor a certified continuous chemical model.
"""
import json,os,time,statistics,random,hashlib,platform
from fractions import Fraction as F
from pathlib import Path
import numpy as np
cfg=json.loads(Path('config.json').read_text())
D,N,Q=int(cfg['D']),int(cfg['N']),int(cfg['Q'])
J,SEED=int(cfg['target']),int(cfg['seed'])
y,h,kf,ks,kw=(float(cfg['yield']),float(cfg['time_step']),
            float(cfg['fast_rate']),float(cfg['slow_rate']),float(cfg['wall_rate']))

def rates(t):
    delta=((t%7)-3)/512.0
    return 5.0/8.0+delta,1.0/4.0-delta,1.0/8.0

def transport(x,t):
    a,l,r=rates(t)
    return a*x+l*np.roll(x,1)+r*np.roll(x,-1)

def scenario(q):
    # Six deterministic 4-hour-like dosing windows; doses are conditional on q.
    r=random.Random(SEED+137*q)
    return [(.002+.00015*r.randrange(12),r.choice([3,19,54,73])) for _ in range(6)]

def initials():
    rng=np.random.default_rng(SEED)
    f0=.3+.35*rng.random(D)
    s0=.25+.30*rng.random(D)
    p0=.01+.035*rng.random(D)
    c0=.17+.07*rng.random(D)
    return c0,f0,s0,p0

c0,f0,s0,p0=initials()
z0=p0+y*(f0+s0)

def inject(c,t,events):
    amt,site=events[min(5,(t*6)//N)]
    c[site]+=amt

def evolve_full(events):
    c,f,s,p=[v.copy() for v in (c0,f0,s0,p0)]
    for t in range(N):
        C,Fm,Sm,P=(transport(v,t) for v in (c,f,s,p))
        inject(C,t,events)
        uf=h*kf*C*Fm
        us=h*ks*C*Sm
        c=C-uf-us-h*kw*C
        f=Fm-uf; s=Sm-us
        p=P+y*(uf+us)
    return float(c[J]),float(p[J]),float(f[J]),float(s[J])

def prepare_passive():
    w=np.zeros(D);w[J]=1.
    for t in range(N-1,-1,-1):
        a,l,r=rates(t)
        w=a*w+l*np.roll(w,-1)+r*np.roll(w,1)
    return float(np.dot(w,z0))

def evolve_reduced(events, passive_output):
    c,f,s=[v.copy() for v in (c0,f0,s0)]
    for t in range(N):
        C,Fm,Sm=(transport(v,t) for v in (c,f,s))
        inject(C,t,events)
        uf=h*kf*C*Fm
        us=h*ks*C*Sm
        c=C-uf-us-h*kw*C
        f=Fm-uf; s=Sm-us
    pJ=passive_output-y*(f[J]+s[J])
    return float(c[J]),float(pJ),float(f[J]),float(s[J])

def test_exact():
    n=int(cfg['exact_N']);d=int(cfg['exact_D'])
    a0,l0,r0=F(5,8),F(1,4),F(1,8)
    yy=F(23,100);hh=F(1,8);ff=F(3,25);ss=F(1,40);wall=F(1,100)
    acc=[]; examples=[]
    for seed in range(int(cfg['exact_fraction_cases'])):
        rand=random.Random(seed+97)
        c=[F(rand.randint(5,12),32) for _ in range(d)]
        f=[F(rand.randint(5,15),32) for _ in range(d)]
        s=[F(rand.randint(5,12),32) for _ in range(d)]
        p=[F(rand.randint(0,5),128) for _ in range(d)]
        ini_z=[p[i]+yy*(f[i]+s[i]) for i in range(d)]
        ws=[F(int(i==1),1) for i in range(d)]
        def tr(x):return [a0*x[i]+l0*x[(i-1)%d]+r0*x[(i+1)%d] for i in range(d)]
        for t in range(n):
            C,Fm,Sm,P=map(tr,(c,f,s,p))
            C[seed%d]+=F((t+seed)%3+1,128)
            u=[hh*ff*C[i]*Fm[i] for i in range(d)]
            v=[hh*ss*C[i]*Sm[i] for i in range(d)]
            c=[C[i]-u[i]-v[i]-hh*wall*C[i] for i in range(d)]
            f=[Fm[i]-u[i] for i in range(d)]
            s=[Sm[i]-v[i] for i in range(d)]
            p=[P[i]+yy*(u[i]+v[i]) for i in range(d)]
        for t in range(n-1,-1,-1):
            ws=[a0*ws[i]+l0*ws[(i+1)%d]+r0*ws[(i-1)%d] for i in range(d)]
        passive_exact=sum(ini_z[i]*ws[i] for i in range(d))
        actual=p[1]+yy*(f[1]+s[1])
        assert passive_exact==actual,(seed,'passive invariant failed')
        assert p[1]==passive_exact-yy*(f[1]+s[1])
        acc.append(True)
        if seed==0:examples.append({'seed':seed,'invariant_numerator_digits':len(str(passive_exact.numerator)),'invariant_denominator_digits':len(str(passive_exact.denominator))})
    return {'cases':len(acc),'exact_matches':sum(acc),'example':examples}

def hostile_counterexamples():
    # Scalar reaction with yield depending on time; constant-y invariant fails.
    C,Fm,Sm,P=F(1,2),F(1,2),F(1,3),F(1,25)
    y0=F(23,100)
    u=F(1,16)*C*Fm
    v=F(1,32)*C*Sm
    old=P+y0*(Fm+Sm)
    P2=P+F(1,5)*(u+v)   # actual yield=0.2 rather than assumed 0.23
    F2,S2=Fm-u,Sm-v
    failure=P2+y0*(F2+S2)-old
    assert failure==(F(1,5)-y0)*(u+v)
    assert failure!=0
    # Wall production explicit: byproduct gets wall term not reflected in fast/slow reagents.
    wall_extra=F(1,1024)
    assert wall_extra!=0
    return {'variable_yield_invariant_failure_num':str(failure.numerator),'variable_yield_invariant_failure_den':str(failure.denominator),'wall_yield_unmodelled':str(wall_extra)}

def measure(fn):
    samples=[]
    for _ in range(int(cfg['repetitions'])):
        start=time.perf_counter_ns(); fn();samples.append((time.perf_counter_ns()-start)/1e6)
    return {'samples_ms':samples,'median_ms':statistics.median(samples)}

def actual_case(q,prep):
    events=scenario(q)
    x=evolve_full(events)
    z=evolve_reduced(events,prep)
    return x,z

if __name__=='__main__':
    exact=test_exact();hostile=hostile_counterexamples()
    prep=prepare_passive()
    t0=time.perf_counter();all_cases=[actual_case(q,prep) for q in range(Q)];check_seconds=time.perf_counter()-t0
    err=max(abs(a-b) for (full,reduced) in all_cases for a,b in zip(full,reduced))
    assert err<1e-11,err
    def batch_full():
        for q in range(Q):evolve_full(scenario(q))
    def batch_reduced():
        value=prepare_passive()
        for q in range(Q):evolve_reduced(scenario(q),value)
    times={'full_Q24':measure(batch_full),'reduced_Q24':measure(batch_reduced),
            'full_Q1':measure(lambda:evolve_full(scenario(0))),
            'reduced_Q1':measure(lambda:evolve_reduced(scenario(0),prepare_passive()))}
    report={'experiment':'R-019','purpose':cfg['purpose'],'fraction':exact,'hostile':hostile,
            'float':{'num_cases':Q,'D':D,'N':N,'maximum_full_reduced_absolute_difference':err,
                     'correctness_cross_check_seconds':check_seconds,'first_original':all_cases[0][0],
                     'first_reduced':all_cases[0][1]},'timing_ms':times,
            'cost_exclusions':['process startup/import time','real hydraulics/EPANET','data file I/O','independent specialist chemistry solver',
                               'certified roundoff','continuous physical accuracy'],
            'environment':{'python':platform.python_version(),'numpy':np.__version__}}
    target=Path(os.environ['DTL_RUN_DIR'])/'output.json'
    target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'fraction_matches':exact['exact_matches'],'max_float_difference':err,
                      'Q24_direct_median_ms':times['full_Q24']['median_ms'],
                      'Q24_reduced_median_ms':times['reduced_Q24']['median_ms'],
                      'output':str(target)},sort_keys=True))

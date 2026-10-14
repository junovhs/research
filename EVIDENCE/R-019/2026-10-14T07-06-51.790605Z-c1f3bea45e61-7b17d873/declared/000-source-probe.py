"""Exact finite-horizon reaction-disturbance nullspace challenge; no timings."""
from fractions import Fraction as F
import json, os
from pathlib import Path

cfg = json.loads(Path('config.json').read_text())
d = cfg['D']; assert d == 5 and cfg['N'] == 2

def diffusion(q):
    q = F(q)
    return [[(1-2*q if i==j else F(0)) + (q if (i-j)%d in (1,d-1) else 0)
             for j in range(d)] for i in range(d)]

def mv(M,x): return [sum((a*b for a,b in zip(row,x)), F(0)) for row in M]
def mm(A,B): return [[sum((A[i][k]*B[k][j] for k in range(len(B))),F(0)) for j in range(len(B[0]))] for i in range(len(A))]
def trans(A): return list(map(list,zip(*A)))
def rank_q(A):
    A=[list(map(F,row)) for row in A]; r=0; n=len(A[0]); m=len(A)
    for j in range(n):
        pivot=next((i for i in range(r,m) if A[i][j]),None)
        if pivot is None: continue
        A[r],A[pivot]=A[pivot],A[r]
        z=A[r][j]; A[r]=[v/z for v in A[r]]
        for i in range(r+1,m):
            z=A[i][j]
            if z: A[i]=[a-z*b for a,b in zip(A[i],A[r])]
        r+=1
        if r==m: break
    return r

def rank_mod(A,p):
    A=[[((v.numerator%p)*pow(v.denominator,-1,p))%p for v in row] for row in A]
    r=0; m=len(A); n=len(A[0])
    for j in range(n):
        piv=next((i for i in range(r,m) if A[i][j]),None)
        if piv is None: continue
        A[r],A[piv]=A[piv],A[r]
        z=pow(A[r][j],-1,p); A[r]=[(a*z)%p for a in A[r]]
        for i in range(r+1,m):
            z=A[i][j]
            if z: A[i]=[(a-z*b)%p for a,b in zip(A[i],A[r])]
        r+=1
        if r==m: break
    return r

def reach(Ma,Mb):
    # reaction S=[-I; +I], propagated A*S=[-Ma; +Mb]
    rows=[]
    for i in range(d):
        rows.append([F(-int(i==j)) for j in range(d)]+[-v for v in Ma[i]])
    for i in range(d):
        rows.append([F(int(i==j)) for j in range(d)]+list(Mb[i]))
    return rows

def evolve(gamma, Ma, Mb):
    a=[F(int(i==0)) for i in range(d)]; b=[F(0)]*d
    for t in range(cfg['N']):
        aa=mv(Ma,a); bb=mv(Mb,b)
        rr=[(F(gamma)*z*z if t==0 else F(0)) for z in aa]
        a=[v-r for v,r in zip(aa,rr)]; b=[v+r for v,r in zip(bb,rr)]
    return a,b

same=diffusion(cfg['q_common']); ma=diffusion(cfg['qA']); mb=diffusion(cfg['qB'])
res={}
for name,X,Y in [('identical',same,same),('unequal',ma,mb)]:
    K=reach(X,Y); rq=rank_q(K); rm=rank_mod(K,cfg['modular_prime'])
    assert rq==rm
    # terminal w=(e_j,e_j) and w=(1,...,1) both species
    j=cfg['query_site']; loc=[F(int(i==j)) for i in range(d)]*2
    glob=[F(1)]*(2*d)
    annih_local=[sum((loc[i]*K[i][k] for i in range(2*d)),F(0)) for k in range(2*d)]
    annih_global=[sum((glob[i]*K[i][k] for i in range(2*d)),F(0)) for k in range(2*d)]
    assert not any(annih_global)
    samples=[evolve(rate,X,Y) for rate in cfg['reaction_rates']]
    qs=[[a[i]+b[i] for i in range(d)] for a,b in samples]
    local_delta=qs[1][j]-qs[0][j]
    global_delta=sum(qs[1],F(0))-sum(qs[0],F(0))
    assert global_delta==0
    assert (not any(annih_local))==(local_delta==0)
    res[name]={'reach_rank_exact':rq,'reach_rank_mod_1009':rm,'null_dimension':2*d-rq,
      'local_annihilator':not any(annih_local),'global_annihilator':not any(annih_global),
      'reaction_rates':cfg['reaction_rates'],'local_composite_delta':str(local_delta),
      'global_composite_delta':str(global_delta),
      'nonzero_local_obstruction':[(k,str(x)) for k,x in enumerate(annih_local) if x]}

# Independently check telescoping output formula for seeded arbitrary exact disturbances,
# using whole-block matrix powers rather than the scalar species recurrence above.
import random
rng=random.Random(20261013)
for name,X,Y in [('identical',same,same),('unequal',ma,mb)]:
    n=2*d; Z=[[F(0)]*n for _ in range(n)]
    for i in range(d):
        Z[i][:d]=X[i]; Z[d+i][d:]=Y[i]
    K=reach(X,Y)
    for case in range(20):
        x0=[F(rng.randint(-7,7),11) for _ in range(n)]
        r0=[F(rng.randint(-3,3),13) for _ in range(d)]
        r1=[F(rng.randint(-3,3),17) for _ in range(d)]
        S0=[-z for z in r0]+r0; S1=[-z for z in r1]+r1
        x1=[v+z for v,z in zip(mv(Z,x0),S0)]; x2=[v+z for v,z in zip(mv(Z,x1),S1)]
        predicted=[v+z+t for v,z,t in zip(mv(mm(Z,Z),x0),mv(Z,S0),S1)]
        assert x2==predicted
        # Independently use computed reachability columns for reaction contribution
        effect=[sum((K[i][k]*r1[k] for k in range(d)),F(0))+
                sum((K[i][d+k]*r0[k] for k in range(d)),F(0)) for i in range(n)]
        assert [v-z for v,z in zip(x2,mv(mm(Z,Z),x0))]==effect
    res[name]['independent_random_telescoping_cases']=20
assert res['identical']['null_dimension']==d and res['unequal']['null_dimension']==1
assert res['identical']['local_composite_delta']=='0'
assert res['unequal']['local_composite_delta']!='0'
Path(os.environ['DTL_RUN_DIR'],'output.json').write_text(json.dumps(res,sort_keys=True,indent=2)+'\n')
print('COMPLETE exact rational/mod-1009 rank and 40 telescoping cases; exact nonlinear two-scenario counterexample')

"""R-030 exact-rational source-bound transport-defect probe. No external packages."""
import hashlib
import json
import os
from fractions import Fraction as F
from pathlib import Path

cfg = json.loads(Path('config.json').read_text())
D, N, Q, j = (cfg[k] for k in ('D','N','Q','sensor'))
y = F(1,4)

def matvec(A, x):
    return [sum((A[i][k]*x[k] for k in range(D)), F(0)) for i in range(D)]

def transvec(A, x):
    return [sum((A[i][k]*x[i] for i in range(D)), F(0)) for k in range(D)]

def dot(a,b):
    return sum((u*v for u,v in zip(a,b)),F(0))

def base(kind):
    if kind == 'dense':
        return [[F(1,2)*(i==k)+F(1,2*D) for k in range(D)] for i in range(D)]
    return [[F(3,4)*(i==k)+F(1,8)*(k==(i-1)%D)+F(1,8)*(k==(i+1)%D) for k in range(D)] for i in range(D)]

def matrices(kind):
    P = base('dense' if kind=='rank_one_dense' else 'local')
    Fmat = [row[:] for row in P]
    if kind=='local_ports':
        for r in (j,(j+3)%D):
            Fmat[r][r] -= F(1,16)
            Fmat[r][(r+1)%D] += F(1,16)
    elif kind=='rank_one_dense':
        for k in range(D):
            Fmat[j][k] += F(1,128)*(1 if k<D//2 else -1)
    assert all(sum(row)==1 and min(row)>=0 for A in (P,Fmat) for row in A)
    return P,Fmat

def initial(q):
    C=[F(1,2)+F((i+q)%5,32) for i in range(D)]
    G=[F(3,4)+F((2*i+q)%7,64) for i in range(D)]
    S=[F(1,2)+F((3*i+2*q)%7,64) for i in range(D)]
    P=[F(i%4,64) for i in range(D)]
    return C,G,S,P

def dose(t,i,q):
    return F(1,32) if (i==(2*t+q)%D and (t+q)%3!=0) else F(0)

def forward(MP,MF,q,retain_p):
    C,G,S,P = initial(q)
    history=[]
    for t in range(N):
        history.append((G[:],S[:]))
        c=matvec(MF,C)
        g=matvec(MF,G)
        s=matvec(MF,S)
        p=matvec(MP,P) if retain_p else None
        Cn=[]; Gn=[]; Sn=[]; Pn=[]
        for i in range(D):
            c[i]+=dose(t,i,q)
            u=c[i]*g[i]/64; v=c[i]*s[i]/128
            Cn.append(c[i]-u-v)
            Gn.append(g[i]-u)
            Sn.append(s[i]-v)
            if retain_p: Pn.append(p[i]+y*(u+v))
        C,G,S=Cn,Gn,Sn
        if retain_p: P=Pn
    return C,G,S,P if retain_p else None,history

def weights(MP):
    w=[F(int(i==j)) for i in range(D)]
    out=[None]*N
    for t in reversed(range(N)):
        out[t]=w
        w=transvec(MP,w)
    return w,out

def short_sha(v):
    return hashlib.sha256((str(v.numerator)+'/'+str(v.denominator)).encode()).hexdigest()[:16]

cases=[]
for kind in ('equal','local_ports','rank_one_dense'):
    MP,MF=matrices(kind)
    w0,ws=weights(MP)
    E=[[MF[i][k]-MP[i][k] for k in range(D)] for i in range(D)]
    probes=[transvec(E,w) for w in ws]
    support=[sum(x!=0 for x in g) for g in probes]
    maxerr=F(0); nonzero=0; digests=[]
    for q in range(Q):
        C1,G1,S1,P1,_=forward(MP,MF,q,True)
        C2,G2,S2,_,hist=forward(MP,MF,q,False)
        assert (C1,G1,S1)==(C2,G2,S2)
        _,G0,S0,P0=initial(q)
        z0=[P0[i]+y*(G0[i]+S0[i]) for i in range(D)]
        correction=sum((dot(probes[t],[hist[t][0][i]+hist[t][1][i] for i in range(D)]) for t in range(N)),F(0))
        if correction: nonzero+=1
        predicted=dot(w0,z0)+y*correction-y*(G2[j]+S2[j])
        err=abs(predicted-P1[j])
        maxerr=max(maxerr,err)
        digests.append(short_sha(predicted))
        assert err==0
    cases.append({'kind':kind,'support_per_t':support,'probe_reads_two_species':2*sum(support),'exact_queries':Q,'exact_errors_zero':maxerr==0,'nonzero_corrections':nonzero,'sample_hashes':digests})
# Direct algebraic adversarial witness: rank-one E has sparse rank but dense E^T w.
assert cases[2]['support_per_t']==[D]*N
assert max(cases[1]['support_per_t'])<=4
assert cases[0]['support_per_t']==[0]*N
# Hostile chemistry: fixed-y identity is false for time-dependent yield or independent wall product.
U=F(1,32); V=F(1,128)
y_bad=F(1,5); wall=F(1,1024)
yield_defect=(y_bad-y)*(U+V)
wall_defect=wall
assert yield_defect!=0 and wall_defect!=0
out={'contract':'exact discrete split step, not continuous or EPANET','dimensions':{'D':D,'N':N,'Q':Q,'sensor':j},'cases':cases,'hostiles':{'variable_yield_defect':str(yield_defect),'unmodelled_wall_product_defect':str(wall_defect)},'all_exact':True}
Path(os.environ['DTL_RUN_DIR'],'output.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'cases':[(v['kind'],v['support_per_t'],v['exact_errors_zero']) for v in cases], 'hostiles':out['hostiles']},sort_keys=True))

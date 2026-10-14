"""R-017 exploratory: exact rational remote-update admission for a monotone cubic ring.

No novelty or performance claim. Run only with sealed provenance/manifest.
"""
from fractions import Fraction as Q
from pathlib import Path
import json
import os

import numpy as np
import scipy
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

CFG = json.loads(Path('config.json').read_text(encoding='utf-8'))
N = CFG['sites']
B = Q(*CFG['coupling'])
G = Q(*CFG['cubic'])
XBASE = [Q(*CFG['cached_uniform_state']) + Q(((7*i)%11)-5,128) for i in range(N)]
DELTA = Q(*CFG['perturbation'])
TOL = Q(*CFG['query_tolerance'])
DISTANCES = CFG['distances']


def rational_residual_bound(x, a, forcing):
    # Treat each binary64 computed x_i as an exact rational number; hence
    # the residual bound refers to the exact real root, not rounded evals.
    xx = [Q.from_float(float(v)) for v in x]
    residual = [a * xx[i] + G * xx[i] ** 3 - B *
                (xx[(i - 1) % N] + xx[(i + 1) % N]) - forcing[i]
                for i in range(N)]
    return max(abs(v) for v in residual) / (a - 2 * B)


def warm_newton(a, forcing):
    x = np.array([float(y) for y in XBASE])
    aa, bb, gg = map(float, (a, B, G))
    ff = np.array([float(p) for p in forcing])
    nsolves = 0
    for _ in range(25):
        rr = aa * x + gg * x**3 - bb * (np.roll(x, 1) + np.roll(x, -1)) - ff
        if np.max(np.abs(rr)) < 3e-15:
            break
        jac = lil_matrix((N, N), dtype=float)
        for i in range(N):
            jac[i, i] = aa + 3 * gg * x[i] ** 2
            jac[i, (i-1) % N] = -bb
            jac[i, (i+1) % N] = -bb
        correction = spsolve(jac.tocsr(), rr)
        x -= correction
        nsolves += 1
        if np.max(np.abs(correction)) < 5e-16:
            break
    error = rational_residual_bound(x, a, forcing)
    return x, error, nsolves


def exact_walk_certificate(a):
    # y_K = (delta/a) sum_{k=0}^{K-1}(b/a A)^k e_0.
    # Tail: |delta|/a * q^K/(1-q), q=2b/a<1.
    # All arithmetic here is exact Fraction (no floating certification).
    q = 2 * B / a
    assert 0 < q < 1
    v = [Q(0)] * N
    v[0] = abs(DELTA) / a
    accum = [Q(0)] * N
    cutoff = TOL / 100
    k = 0
    while True:
        tail = abs(DELTA) / a * q**k / (1-q)
        if tail <= cutoff:
            break
        if k >= CFG['max_terms']:
            raise RuntimeError('walk-series convergence too slow; no measured certificate')
        accum = [accum[i] + v[i] for i in range(N)]
        v = [B / a * (v[(i-1)%N] + v[(i+1)%N]) for i in range(N)]
        k += 1
    # Tail used on *every* coordinate, hence this is a rigorous supersolution.
    upper = [z + tail for z in accum]
    # Independent EXACT rational supersolution test: (aI-bA) upper >= |delta| e0.
    margins = [a * upper[i] - B * (upper[(i-1)%N] + upper[(i+1)%N])
               - (abs(DELTA) if i == 0 else 0) for i in range(N)]
    assert min(margins) >= 0
    return upper, k, tail, min(margins)


def main():
    records = []
    per_alpha = []
    for anum, aden in CFG['diagonals']:
        a = Q(anum, aden)
        if a <= 2*B:
            continue
        rhs_base = [a * XBASE[i] + G * XBASE[i] ** 3 - B *
                    (XBASE[(i-1)%N]+XBASE[(i+1)%N]) for i in range(N)]
        upper, k, tail, margin = exact_walk_certificate(a)
        count = 0
        oracle_max = Q(0)
        for sign in (+1, -1):
            rhs = list(rhs_base)
            rhs[0] += sign * DELTA
            solved, rooterr, steps = warm_newton(a, rhs)
            oracle_max = max(oracle_max, rooterr)
            for dist in DISTANCES:
                # The same exact certificate applies for sign +/- by absolute perturbation.
                cert = upper[dist]
                admitted = cert <= TOL  # manufactured baseline vector is exactly rational (zero cache error)
                empirical_change = abs(Q.from_float(float(solved[dist])) - XBASE[dist])
                independent_check = empirical_change + rooterr <= cert
                # This is a separately calculated residual-certified IVP comparison.
                assert independent_check, (a, sign, dist, empirical_change, rooterr, cert)
                if admitted:
                    assert empirical_change + rooterr <= TOL
                    count += 1
                records.append([str(a),sign,dist,float(cert),int(admitted),
                                float(empirical_change),float(rooterr),steps])
        per_alpha.append({'diagonal':str(a),'walk_terms':k,
            'tail_upper_float':float(tail),
            'min_exact_supersolution_margin_float':float(margin),
            'admitted':count,'total':2*len(DISTANCES),
            'max_oracle_error_bound_float':float(oracle_max),
            'global_lipschitz_bound_float':float(abs(DELTA)/(a-2*B))})
    doc={'config':CFG,'versions':{'numpy':np.__version__,'scipy':scipy.__version__},'per_diagonal':per_alpha,
         'query_columns':['diagonal','sign','distance','upper_bound_approx','admit','oracle_change_approx','oracle_error_upper_approx','newton_solves'],
         'queries':records,'total_queries':len(records),'total_admitted':sum(r[4] for r in records),
         'total_fallback':sum(1-r[4] for r in records),
         'note':'EXPLORATORY: exact rational admission and exact residual bounds; decimal outputs are approximate displays'}
    Path(os.environ['DTL_RUN_DIR'],'output.json').write_text(json.dumps(doc,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'queries':doc['total_queries'],'admitted':doc['total_admitted'],
                      'per_diagonal':per_alpha},sort_keys=True))


if __name__=='__main__':
    main()

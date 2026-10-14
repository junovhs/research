#!/usr/bin/env python3
"""R-018: cheap, source-bound specialist challenge on a water-transport surrogate.
NOT the EPANET executable or a validated drinking-water physical model.
"""
import json, math, os, random, statistics, time
from fractions import Fraction
from pathlib import Path

config = json.loads(Path('config.json').read_text())
D, N, QMAX = config['D'], config['N'], max(config['query_counts'])
TARGET = config['target']
TIMING_REPS = config['timing_repetitions']
SEED = config['seed']


def coefficients(t, rho):
    v = ((t % 11) - 5) / 256
    return (rho * (5/8 + v), rho * (1/4 - v), rho / 8)


def events_for_query(q, rho):
    rng = random.Random(SEED + q * 131071)
    pairs = set()
    while len(pairs) < config['events_per_query']:
        pairs.add((rng.randrange(N), rng.randrange(D)))
    return sorted((t, site, (1-rho) * ((1, 2, 3, 4)[(q+site+t) % 4] / 4)) for t, site in pairs)


def timed(fun, repeats=TIMING_REPS):
    times, result = [], None
    for _ in range(repeats):
        start = time.perf_counter_ns()
        result = fun()
        times.append((time.perf_counter_ns() - start) / 1e6)
    return {'median_ms': statistics.median(times), 'samples_ms': times}, result


def forward(events, rho, start_t=0, initial=None):
    x = list(initial) if initial is not None else [0.] * D
    bucket = {}
    for t, site, b in events:
        if t >= start_t:
            bucket.setdefault(t, []).append((site,b))
    for t in range(start_t, N):
        a,l,r = coefficients(t,rho)
        nxt = [a*x[i] + l*x[(i-1)%D] + r*x[(i+1)%D] for i in range(D)]
        for site,b in bucket.get(t, ()):
            nxt[site] += b
        x=nxt
    return x[TARGET]


def reverse_coefficients(rho, event_keys):
    # Coefficient for each requested event, even across distinct scenarios.
    active = {}
    for t,site in event_keys:
        active.setdefault(t, []).append(site)
    weights = {}
    w = [0.] * D
    w[TARGET] = 1.
    for t in range(N-1,-1,-1):
        for site in active.get(t,()):
            weights[(t,site)] = w[site]
        a,l,r=coefficients(t,rho)
        w = [a*w[i] + l*w[(i+1)%D] + r*w[(i-1)%D] for i in range(D)]
    return weights


def suffix_length(rho, eps):
    p=1.0
    for k in range(1,N+1):
        p *= rho
        if p<=eps:
            return k,p
    return None,p


def exact_challenge():
    # Independent Fraction reference, with nonstationary rational coefficient.
    n, d, tgt, rq = 13, 7, 3, 16
    drng = random.Random(60607)
    def abc(t):
        rho = Fraction(15,16)
        v = Fraction(t%5-2,128)
        return rho*(Fraction(5,8)+v),rho*(Fraction(1,4)-v),rho*Fraction(1,8)
    cases=[]
    for q in range(24):
        ev={}
        for _ in range(4):
            t=drng.randrange(n); site=drng.randrange(d)
            ev[t,site]=ev.get((t,site),Fraction(0))+Fraction(1,256)
        # Exact forward recurrence from zero.
        x=[Fraction(0) for _ in range(d)]
        for t in range(n):
            a,l,r=abc(t)
            x=[a*x[i]+l*x[(i-1)%d]+r*x[(i+1)%d]+ev.get((t,i),Fraction(0)) for i in range(d)]
        target_value=x[tgt]
        # Separately expressed transposed recurrence.
        weights=[Fraction(int(i==tgt)) for i in range(d)]
        total=Fraction(0)
        for t in range(n-1,-1,-1):
            total += sum(weights[i]*ev.get((t,i),Fraction(0)) for i in range(d))
            a,l,r=abc(t)
            weights=[a*weights[i] + l*weights[(i+1)%d]+r*weights[(i-1)%d] for i in range(d)]
        cases.append({'q':q,'exact_equal':total==target_value,'fraction_numerator':target_value.numerator,'fraction_denominator':target_value.denominator})
        if total!=target_value:
            raise AssertionError('exact Fraction reference failed')
    return {'completed':len(cases), 'exact_equal':sum(z['exact_equal'] for z in cases), 'sample': cases[:3]}


def main():
    checks=exact_challenge()
    all_results=[]
    for rho in config['rhos']:
        event_time,all_events=timed(lambda:[events_for_query(q,rho) for q in range(QMAX)])
        key_time,keys=timed(lambda:{(t,i) for ev in all_events for t,i,_ in ev})
        adj_time,weights=timed(lambda:reverse_coefficients(rho,keys))
        adj_outputs=[sum(weights[t,i]*b for t,i,b in ev) for ev in all_events]
        k,bound=suffix_length(rho,config['eps'])
        # No free precomputed forward states: all cold queries recompute.
        ref_time,forward_outputs=timed(lambda:[forward(ev,rho) for ev in all_events])
        maxerr=max(abs(x-y) for x,y in zip(adj_outputs,forward_outputs))
        if maxerr > 1e-12:
            raise AssertionError(f'forward/adjoint oracle mismatch: {rho} {maxerr}')
        if k is not None:
            ss_time,ss_out=timed(lambda:[forward(ev,rho,start_t=N-k) for ev in all_events])
            max_suffix_err=max(abs(x-y) for x,y in zip(forward_outputs,ss_out))
            if max_suffix_err>bound+1e-12:
                raise AssertionError('uniform suffix inclusion invalid')
        else:
            ss_time,ss_out,max_suffix_err=None,None,None
        sizes=[]
        for q in config['query_counts']:
            # Amortized specialist cost = precompute + event dot products, not zero-time query.
            # Observed precompute time same for every q; measure actual dot costs separately.
            evq=all_events[:q]
            lookup_time,outs=timed(lambda:[sum(weights[t,i]*b for t,i,b in ev) for ev in evq])
            forward_cost_ms = (ref_time['median_ms']+event_time['median_ms']) * q / QMAX
            suffix_cost_ms = ((ss_time['median_ms']+event_time['median_ms'])*q/QMAX if ss_time is not None else float('nan'))
            adj_total_ms=adj_time['median_ms']+lookup_time['median_ms']+key_time['median_ms']+event_time['median_ms']*q/QMAX
            sizes.append({'Q':q, 'specialist_adjoint_cold_ms':adj_total_ms,
                          'specialist_amortized_ms_per_query':adj_total_ms/q,
                          'forward_cold_estimated_ms':forward_cost_ms,
                          'suffix_cold_estimated_ms':suffix_cost_ms if ss_time is not None else None,
                          'suffix_admission':k is not None,
                          'lookup_median_ms':lookup_time['median_ms'],
                          'forward_cost_extrapolated_from_batch':True,
                          'suffix_cost_extrapolated_from_batch':True})
        all_results.append({'rho':rho,'N':N,'D':D,'queries_checked':QMAX,'events_per_query':config['events_per_query'],
                            'input_event_pairs_unique':len(keys),'target_site':TARGET,
                            'event_generation_timing':event_time, 'event_key_index_timing':key_time,
                            'suffix_K':k,'suffix_unknown_prefix_upper_bound':bound,
                            'max_forward_adjoint_error':maxerr,
                            'max_forward_suffix_error':max_suffix_err,
                            'forward_all_queries_timing':ref_time,
                            'adjoint_preparation_timing':adj_time,
                            'suffix_all_queries_timing':ss_time,
                            'q_costs':sizes})
    result={'status':'complete','model_scope':'linear discrete nonnegative transport surrogate, NOT EPANET',
            'exact_fraction_test':checks,'parameters':config,'results':all_results,
            'qualification':'All medians single-container timings; no real hydraulics/preparation charged; no industrial or novelty claim; specialist identity proven only for exact linear recurrence.'}
    output=Path(os.environ['DTL_RUN_DIR'])/'output.json'
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('OK',json.dumps({'fraction_checks':checks['exact_equal'],'rho_summaries':[{ 'rho':r['rho'],'suffix_K':r['suffix_K'],'max_adj_error':r['max_forward_adjoint_error'],'max_suffix_err':r['max_forward_suffix_error']} for r in all_results]}))

if __name__=='__main__':
    main()

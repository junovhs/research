"""An Alien-inspired question map, not a reproduction of Alien's learned models."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import dig
import layers
import probe

ARXIV = 'https://export.arxiv.org/api/query'
TERMS = {
    'phot_g_mean_mag': '(all:Gaia AND (all:magnitude OR all:brightness))',
    'bp_rp': '(all:Gaia AND (all:colour OR all:color))',
    'parallax_snr': '(all:parallax AND (all:uncertainty OR all:precision))',
    'proper_motion': 'all:"proper motion"',
    'ruwe': '(all:RUWE OR all:"astrometric excess noise")',
    'visibility_periods_used': '(all:Gaia AND (all:"visibility periods" OR all:"scanning law"))',
    'phot_bp_rp_excess_factor': '(all:Gaia AND (all:"flux excess" OR all:"photometric excess"))',
    'wise_color': '(all:WISE AND (all:color OR all:colour OR all:"infrared excess"))',
    'wise_w1': '(all:WISE AND (all:magnitude OR all:brightness))',
    'match_offset': '(all:Gaia AND all:WISE AND (all:offset OR all:crossmatch))',
    'wise_blend': '(all:WISE AND (all:blend OR all:blending))',
    'wise_extended': '(all:WISE AND (all:extended OR all:galaxy))',
    'nearest_gaia_arcsec': '(all:Gaia AND (all:crowding OR all:"nearest neighbour" OR all:"nearest neighbor"))',
    'no_ir_candidate': '(all:Gaia AND all:WISE AND (all:unmatched OR all:incompleteness))',
}

# Session judgments, explicitly proposals rather than scientific or novelty scores.
PROPOSALS = [
    ('ruwe','nearest_gaia_arcsec',2,'Does astrometric fit quality track local neighbour spacing?','Nearby resolved sources can identify crowding; unresolved companions remain a different explanation.'),
    ('phot_bp_rp_excess_factor','nearest_gaia_arcsec',2,'Does flux excess track neighbour spacing within brightness bins?','Blending can alter aperture fluxes; optical color remains a possible confounder.'),
    ('phot_g_mean_mag','no_ir_candidate',2,'Does Gaia-to-WISE nonmatching grow toward faint Gaia magnitudes?','Different detection limits should predict nonmatching before invoking unusual spectra.'),
    ('ruwe','wise_color',2,'Do poor astrometric fits coincide with red WISE colors?','Dust/emission and multiplicity are distinct possibilities; IR colors are not dust diagnoses.'),
    ('phot_bp_rp_excess_factor','wise_color',2,'Does optical flux excess accompany IR color excess?','Blended optical flux and genuine emission can imitate each other.'),
    ('proper_motion','match_offset',2,'Do match offsets increase with proper motion?','Gaia/WISE epoch differences predict displacement; offsets alone are not new motion measurements.'),
    ('nearest_gaia_arcsec','wise_blend',2,'Are WISE deblending components associated with close Gaia neighbours?','WISE resolution may merge optical sources.'),
    ('phot_bp_rp_excess_factor','wise_extended',2,'Does optical flux excess track the WISE extension flag?','Extended sources can violate stellar aperture assumptions.'),
    ('bp_rp','no_ir_candidate',2,'Do nonmatches depend on optical color within brightness bins?','Spectral energy distributions and band-dependent limits can shape completeness.'),
    ('parallax_snr','wise_color',1,'Does IR color vary with parallax significance at fixed optical color?','Stellar populations and distance/precision selection can both contribute; significance is not distance.'),
    ('visibility_periods_used','no_ir_candidate',1,'Does infrared nonmatching track Gaia observation coverage?','A relation could reflect sky/selection structure rather than physics.'),
    ('ruwe','visibility_periods_used',2,'Does poor astrometric fit depend on observation coverage?','Small or structured temporal sampling can distort fits.'),
    ('wise_w1','match_offset',2,'Are infrared-faint counterparts less precisely centered?','Measurement uncertainty should increase at lower signal-to-noise.'),
    ('proper_motion','wise_color',1,'Do optical-color-matched motion populations differ in IR color?','Population mixtures and selection dominate plausible explanations.'),
    ('bp_rp','wise_blend',1,'Are different optical colors associated with WISE deblending?','Crowding, background galaxies and color-dependent detectability may compete.'),
    ('parallax_snr','no_ir_candidate',1,'Does missing infrared coverage depend on parallax precision?','Likely a depth/stellar-population selection relation; useful as a baseline.'),
]


def proposals():
    result = [dict(id=f'Q{i+1:02}',x=x,y=y,coherence=coherence,question=question,rationale=rationale,baseline=False)
              for i,(x,y,coherence,question,rationale) in enumerate(PROPOSALS)]
    rng = random.Random(dig.SEED)
    used = {frozenset((q['x'],q['y'])) for q in result}
    while len(result)<20:
        x,y = rng.sample(sorted(TERMS),2)
        if frozenset((x,y)) in used:
            continue
        if 'no_ir_candidate' in (x,y) and any(k.startswith('wise_') or k=='match_offset' for k in (x,y)):
            continue  # Infrared-only quantities are undefined for the no-match group.
        used.add(frozenset((x,y)))
        result.append(dict(id=f'Q{len(result)+1:02}',x=x,y=y,coherence=1,
                           question=f'Random baseline: compare {x} with {y}.',
                           rationale='A runnable selection/systematics comparison; no specific causal mechanism asserted.',baseline=True))
    for question in result:
        question['conditioning'] = 'sky_quadrants' if question['x']=='phot_g_mean_mag' or question['y']=='phot_g_mean_mag' else 'two_magnitude_bins'
        question['search_query'] = f"cat:astro-ph* AND ({TERMS[question['x']]}) AND ({TERMS[question['y']]})"
    return result


def parse_feed(raw):
    root = ET.fromstring(raw)
    count = root.find('{http://a9.com/-/spec/opensearch/1.1/}totalResults')
    if count is None or count.text is None:
        raise ValueError('arXiv response lacks a valid totalResults count')
    total = int(count.text)
    if total < 0 or any('api/errors' in (entry.findtext('{http://www.w3.org/2005/Atom}id') or '') for entry in root.findall('{http://www.w3.org/2005/Atom}entry')):
        raise ValueError('arXiv returned an error feed')
    return total


def availability(question, offline, deadline):
    query = question['search_query']
    cache = dig.cache_directory()/'literature'
    cache.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(query.encode()).hexdigest()[:24]
    rawpath,metapath=cache/(key+'.xml'),cache/(key+'.json')
    if rawpath.exists() and metapath.exists():
        meta=json.loads(metapath.read_text()); raw=rawpath.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=meta['sha256']:
            raise ValueError('Literature cache checksum mismatch')
        return dict(meta,count=parse_feed(raw),status='ok',cache_hit=True)
    if offline:
        return dict(status='not_cached',count=None,query=query)
    if time.monotonic()+12 > deadline:
        return dict(status='budget_exhausted',count=None,query=query)
    # Persist pacing across invocations on this machine; only one connection at a time.
    stamp=cache/'last-request.txt'
    last=float(stamp.read_text()) if stamp.exists() else 0
    wait=max(0,3.1-(time.time()-last))
    if wait:
        time.sleep(wait)
    url=ARXIV+'?'+urllib.parse.urlencode(dict(search_query=query,start=0,max_results=1))
    meta=dict(query=query,url=url,utc=datetime.now(timezone.utc).isoformat(),count=None)
    try:
        stamp.write_text(str(time.time()))
        request=urllib.request.Request(url,headers={'User-Agent':'research-needles/1.0 (small metadata-only research batch)'})
        with urllib.request.urlopen(request,timeout=min(10,deadline-time.monotonic())) as response:
            raw=response.read(100001)
        if len(raw)>100000:
            raise ValueError('Literature response exceeds 100 KB cap')
        count=parse_feed(raw)
        meta.update(status='ok',count=count,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
        rawpath.write_bytes(raw)
        dig.write_json(metapath,meta)
    except Exception as exc:
        meta.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        if isinstance(exc,urllib.error.HTTPError):
            meta['retry_after']=exc.headers.get('Retry-After')
    with (cache/'attempts.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(meta)+'\n')
    return meta


def measured_rows(gaia,wise,matches):
    output=[]
    wise_by_id={r['designation']:r for r in wise}
    for row in gaia:
        value=probe.derived(row)
        candidates=[p for p in matches['candidate_pairs'] if p['source_id']==row['source_id']]
        value['no_ir_candidate']=int(not candidates)
        value['nearest_gaia_arcsec']=min((3600*dig.separation(float(row['ra']),float(row['dec']),float(other['ra']),float(other['dec'])) for other in gaia if other['source_id']!=row['source_id']),default=None)
        for key in ('wise_color','wise_w1','match_offset','wise_blend','wise_extended'):
            value[key]=None
        if len(candidates)==1 and candidates[0]['designation'] not in matches['shared_allwise']:
            w=wise_by_id[candidates[0]['designation']]
            value.update(match_offset=candidates[0]['separation_arcsec'],wise_blend=probe.number(w,'nb'),wise_extended=probe.number(w,'ext_flg'))
            w1,w2,s1,s2=[probe.number(w,k) for k in ('w1mpro','w2mpro','w1snr','w2snr')]
            if w1 is not None and s1 is not None and s1>=5:
                value['wise_w1']=w1
                if w2 is not None and s2 is not None and s2>=5:
                    value['wise_color']=w1-w2
        value.update(ra=float(row['ra']),dec=float(row['dec']))
        output.append(value)
    return output


def test_question(question,values,field):
    eligible=[v for v in values if v[question['x']] is not None and v[question['y']] is not None and v['phot_g_mean_mag'] is not None]
    if question['conditioning']=='sky_quadrants':
        groups=[(v['ra']>=field['ra_deg'],v['dec']>=field['dec_deg']) for v in eligible]
    else:
        groups=[math.floor(v['phot_g_mean_mag']/2) for v in eligible]
    return probe.permutation_association([v[question['x']] for v in eligible],[v[question['y']] for v in eligible],groups,dig.SEED+int(question['id'][1:]))


def selection_key(question):
    count=question.get('literature',{}).get('count')
    return (-question['coherence'],count is None,count if count is not None else 0,question['id'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=dig.ROOT/'experiments/question-map.json')
    parser.add_argument('--offline',action='store_true',help='Use cached literature only; source data is always cached')
    args=parser.parse_args()
    started=time.monotonic(); deadline=started+dig.budget()['max_batch_seconds']
    questions=proposals()
    service_failed=False
    for question in questions:
        if service_failed:
            result=dict(status='not_attempted_after_service_failure',count=None,query=question['search_query'])
        else:
            result=availability(question,args.offline,deadline)
            service_failed=result['status']=='failed'
        question['literature']=result
    ranked=sorted((q for q in questions if not q['baseline']),key=selection_key)
    selected=ranked[:2]+[next(q for q in questions if q['baseline'])]
    fields={}
    for role in ('calibration','exploration'):
        field=dig.get_needle(role)
        gaia,gm,_=dig.fetch_gaia(role,offline=True,endpoint=dig.ARCHIVES['ari'])
        wise,wm=layers.fetch_wise(role,layers.Batch(),offline=True)
        matches=layers.summarize_matches(gaia,wise,field)
        values=measured_rows(gaia,wise,matches)
        for question in questions:
            question.setdefault('available_pairs',{})[role]=sum(v[question['x']] is not None and v[question['y']] is not None and v['phot_g_mean_mag'] is not None for v in values)
        results=[]
        for question in selected:
            result=test_question(question,values,field)
            if result.get('status')=='ok':
                result['descriptive_26_test_adjusted_p']=min(1,result['permutation_p']*26)
            results.append(dict(question_id=question['id'],question=question['question'],baseline=question['baseline'],result=result))
        fields[role]=dict(gaia_sha256=gm['sha256'],allwise_sha256=wm['sha256'],results=results)
    report=dict(schema_version=1,seed=dig.SEED,method='Alien-inspired proposals and keyword co-mention counts; no learned Alien model, novelty estimator or paid model API.',
                coherence_scale={'0':'no defensible rationale','1':'plausible but weak or mostly selection','2':'direct physical/measurement rationale; session judgment, not a probability'},
                availability_caveat='Counts measure arXiv metadata query coverage, not whether a question was asked. Synonyms, full-text omissions, corpus scope and terminology can hide prior work. Zero is not a novelty claim; errors are unknown.',
                known_related_prior_work=[
                    dict(url='https://arxiv.org/abs/2012.01916',topic='Gaia photometric calibration and crowding; related to Q02 despite its zero keyword count.'),
                    dict(url='https://gea.esac.esa.int/archive/documentation/GDR3/Catalogue_consolidation/chap_crossmatch/sec_crossmatch_algorithm/',topic='Official Gaia crossmatch limitations, multiplicity and resolution; related to Q03 and match-offset questions.')],
                selection_rule='Two highest-coherence proposals, lower successful co-mention count first, then one seeded random baseline. Unknown availability is not zero. Selection used open data and is exploratory.',
                proposals=questions,selected=[q['id'] for q in selected],fields=fields,
                attempted_scientific_tests_this_batch=6,prior_attempted_scientific_tests=20,elapsed_seconds=round(time.monotonic()-started,3),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                interpretation='All tests use already explored open fields. No confirmation or claim of absence. Dependence/overlap with prior tests and adaptive selection prohibit independent-validation language.')
    dig.write_json(args.output,report)
    print(json.dumps(dict(proposals=len(questions),availability_ok=sum(q['literature']['status']=='ok' for q in questions),selected=report['selected'],tests=report['attempted_scientific_tests_this_batch'],output=str(args.output),seconds=report['elapsed_seconds']),indent=2))


if __name__=='__main__':
    main()

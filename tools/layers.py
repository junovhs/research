"""Dig AllWISE, preserve all associations/nonmatches, and check published matches."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import subprocess
import time

import dig
import probe

IRSA = 'https://irsa.ipac.caltech.edu/TAP/sync'
WISE_COLUMNS = 'designation,ra,dec,w1mpro,w2mpro,w1sigmpro,w2sigmpro,w1snr,w2snr,cc_flags,ext_flg,nb,ph_qual'
REFERENCE_COLUMNS = 'source_id,original_ext_source_id,angular_distance,number_of_neighbours,number_of_mates'


class Batch:
    def __init__(self):
        limits = dig.budget()
        self.remaining_bytes = limits['max_download_mb_per_batch'] * 1_000_000
        self.deadline = time.monotonic() + limits['max_batch_seconds']


def table(role, name, endpoint, query, columns, batch, offline=False):
    dig.get_needle(role)
    cache = dig.cache_directory()
    cache.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((endpoint+query).encode()).hexdigest()[:24]
    rawpath, metapath = cache / (key+'.csv'), cache / (key+'.json')
    cached = rawpath.exists() and metapath.exists()
    if cached:
        raw = rawpath.read_bytes()
        meta = json.loads(metapath.read_text())
        if hashlib.sha256(raw).hexdigest() != meta['sha256'] or meta['query'] != query:
            raise ValueError('Layer cache checksum/query mismatch')
    else:
        if offline:
            raise FileNotFoundError(f'No verified cache for {role} {name}')
        used = sum(p.stat().st_size for p in cache.rglob('*') if p.is_file())
        if used + batch.remaining_bytes > dig.budget()['max_local_cache_mb']*1_000_000:
            raise ValueError('Layer cache budget exceeded')
        attempt = dict(utc=datetime.now(timezone.utc).isoformat(), needle=role, layer=name, query=query, endpoint=endpoint)
        started = time.monotonic()
        try:
            raw = dig.bounded_request(endpoint, query, batch.remaining_bytes, batch.deadline)
            batch.remaining_bytes -= len(raw)
            reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
            if reader.fieldnames != columns.split(','):
                raise ValueError('Unexpected layer schema: '+raw[:250].decode(errors='replace'))
            rows = list(reader)
            if len(rows) > dig.budget()['initial_sample_rows']:
                raise ValueError('Layer row budget exceeded')
            if any(None in row or any(v is None for v in row.values()) for row in rows):
                raise ValueError('Malformed layer CSV')
            meta = dict(attempt, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), row_count=len(rows),
                        code_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=dig.ROOT, text=True).strip(),
                        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        code_dirty=bool(subprocess.check_output(['git','status','--porcelain'], cwd=dig.ROOT, text=True).strip()),
                        possibly_truncated=len(rows)==dig.budget()['initial_sample_rows'], cache_file=str(rawpath),
                        elapsed_seconds=round(time.monotonic()-started,3))
            tmp = rawpath.with_suffix('.tmp'); tmp.write_bytes(raw); tmp.replace(rawpath)
            dig.write_json(metapath, meta)
            attempt.update(status='ok', sha256=meta['sha256'], row_count=len(rows))
        except Exception as exc:
            attempt.update(status='failed', error=f'{type(exc).__name__}: {exc}')
            if isinstance(exc, dig.urllib.error.HTTPError):
                attempt['retry_after'] = exc.headers.get('Retry-After')
                attempt['archive_message'] = exc.read(2000).decode(errors='replace')
            raise
        finally:
            attempt['elapsed_seconds'] = round(time.monotonic()-started,3)
            with (cache/'attempts.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(attempt)+'\n')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if reader.fieldnames != columns.split(','):
        raise ValueError('Cached layer schema mismatch')
    rows = list(reader)
    if len(rows) != meta['row_count']:
        raise ValueError('Cached layer row count mismatch')
    return rows, meta


def fetch_wise(role, batch, offline=False):
    field = dig.get_needle(role)
    query = (f"SELECT TOP {dig.budget()['initial_sample_rows']} {WISE_COLUMNS} FROM allwise_p3as_psd "
             f"WHERE CONTAINS(POINT(ra,dec),CIRCLE({field['ra_deg']},{field['dec_deg']},{field['radius_deg']}))=1 ORDER BY designation")
    rows, meta = table(role, 'AllWISE', IRSA, query, WISE_COLUMNS, batch, offline)
    identifiers = set()
    for row in rows:
        ra, dec = float(row['ra']), float(row['dec'])
        if not (math.isfinite(ra) and math.isfinite(dec) and 0 <= ra < 360 and -90 <= dec <= 90):
            raise ValueError('Invalid AllWISE position')
        if dig.separation(ra,dec,field['ra_deg'],field['dec_deg']) > field['radius_deg']+1e-7:
            raise ValueError('AllWISE source outside cone')
        if row['designation'] in identifiers:
            raise ValueError('Duplicate AllWISE designation')
        identifiers.add(row['designation'])
    return rows, meta


def published_matches(role, batch, offline=False):
    dig.get_needle(role)
    gaia, _, _ = dig.fetch_gaia(role, offline=True, endpoint=dig.ARCHIVES['ari'])
    # Indexed IDs avoid a spatial join whose planner scanned the auxiliary table.
    ids = ','.join(str(int(row['source_id'])) for row in gaia) or '-1'
    query = (f"SELECT TOP {dig.budget()['initial_sample_rows']} {REFERENCE_COLUMNS} "
             f"FROM gaiadr3.allwise_best_neighbour WHERE source_id IN ({ids}) ORDER BY source_id")
    return table(role, 'Gaia DR3 published AllWISE best neighbours', dig.ARCHIVES['ari'], query, REFERENCE_COLUMNS, batch, offline)


def associations(gaia, wise, radius_arcsec=2.):
    pairs = []
    for source in gaia:
        for infrared in wise:
            distance = 3600*dig.separation(float(source['ra']),float(source['dec']),float(infrared['ra']),float(infrared['dec']))
            if distance <= radius_arcsec:
                pairs.append(dict(source_id=source['source_id'], designation=infrared['designation'], separation_arcsec=distance))
    return sorted(pairs, key=lambda p:(p['source_id'],p['separation_arcsec'],p['designation']))


def summarize_matches(gaia, wise, field, radius_arcsec=2.):
    pairs = associations(gaia,wise,radius_arcsec)
    gaia_ids, wise_ids = {p['source_id'] for p in pairs}, {p['designation'] for p in pairs}
    counts = {sid:sum(p['source_id']==sid for p in pairs) for sid in gaia_ids}
    mates = {wid:sum(p['designation']==wid for p in pairs) for wid in wise_ids}
    # Common interior subset keeps every shifted query plus match circle inside footprint.
    interior = [r for r in gaia if 3600*dig.separation(float(r['ra']),float(r['dec']),field['ra_deg'],field['dec_deg']) < field['radius_deg']*3600-35]
    shifts = []
    for dra,ddec in [(30,0),(-30,0),(0,30),(0,-30)]:
        shifted = [dict(r, ra=str((float(r['ra'])+dra/(3600*math.cos(math.radians(float(r['dec'])))))%360), dec=str(float(r['dec'])+ddec/3600)) for r in interior]
        hits = {p['source_id'] for p in associations(shifted,wise,radius_arcsec)}
        shifts.append(dict(offset_arcsec=[dra,ddec], matched_gaia=len(hits), denominator=len(interior)))
    interior_hits = {p['source_id'] for p in associations(interior,wise,radius_arcsec)}
    return dict(radius_arcsec=radius_arcsec, gaia_rows=len(gaia), allwise_rows=len(wise), candidate_pairs=pairs,
                matched_gaia=len(gaia_ids), matched_allwise=len(wise_ids),
                gaia_match_fraction=len(gaia_ids)/len(gaia) if gaia else None,
                median_offset_arcsec=statistics.median(p['separation_arcsec'] for p in pairs) if pairs else None,
                ambiguous_gaia=[sid for sid,n in counts.items() if n>1], shared_allwise=[wid for wid,n in mates.items() if n>1],
                unmatched_gaia=[r['source_id'] for r in gaia if r['source_id'] not in gaia_ids],
                unmatched_allwise=[r['designation'] for r in wise if r['designation'] not in wise_ids],
                interior_unshifted=dict(matched_gaia=len(interior_hits),denominator=len(interior)), shifted_controls=shifts,
                caveat='Geometric candidates, not object identities. Gaia epoch 2016 versus AllWISE ~2010; no proper-motion propagation. Resolution, depth, blending and upper limits can explain nonmatches. AllWISE adds infrared wavelength coverage, not a universal fainter optical limit.')


def reference_agreement(matches, reference):
    candidates = {(p['source_id'],p['designation']) for p in matches['candidate_pairs']}
    recovered = [r for r in reference if (r['source_id'],r['original_ext_source_id']) in candidates]
    return dict(published_pairs=len(reference), recovered_pairs=len(recovered),
                missed_published_pairs=[r for r in reference if (r['source_id'],r['original_ext_source_id']) not in candidates],
                examples=recovered[:5],
                meaning='Reproduces published catalog associations; this validates a crossmatch, not a new physical finding or a full deep-field rediscovery.')


def inspect_leads(gaia, wise, matches):
    wise_by_id = {r['designation']:r for r in wise}
    result = []
    top = sorted(gaia,key=lambda r:probe.number(r,'ruwe') or -1,reverse=True)[:10]
    for row in top:
        neighbors = []
        for pair in matches['candidate_pairs']:
            if pair['source_id'] == row['source_id']:
                w = wise_by_id[pair['designation']]
                neighbors.append(dict(pair, photometry={key:w[key] for key in WISE_COLUMNS.split(',') if key not in ('ra','dec','designation')}))
        result.append(dict(source_id=row['source_id'], g=probe.number(row,'phot_g_mean_mag'), bp_rp=probe.number(row,'bp_rp'),
                           ruwe=probe.number(row,'ruwe'), photometric_excess=probe.number(row,'phot_bp_rp_excess_factor'), infrared_candidates=neighbors))
    return result


def infrared_followup(gaia, wise, matches):
    """Adaptive exploratory follow-up, using existing open-field data only."""
    wise_by_id = {row['designation']:row for row in wise}
    pairs = matches['candidate_pairs']
    excluded = dict(no_candidate=0, ambiguous_or_shared=0, missing_or_low_snr=0, missing_optical=0)
    included = []
    for row in gaia:
        candidates = [p for p in pairs if p['source_id']==row['source_id']]
        if not candidates:
            excluded['no_candidate'] += 1
            continue
        if len(candidates)!=1 or candidates[0]['designation'] in matches['shared_allwise']:
            excluded['ambiguous_or_shared'] += 1
            continue
        wise_row = wise_by_id[candidates[0]['designation']]
        w1,w2,s1,s2 = [probe.number(wise_row,k) for k in ('w1mpro','w2mpro','w1snr','w2snr')]
        if any(v is None for v in (w1,w2,s1,s2)) or min(s1,s2)<5:
            excluded['missing_or_low_snr'] += 1
            continue
        g,color = probe.number(row,'phot_g_mean_mag'),probe.number(row,'bp_rp')
        if g is None or color is None:
            excluded['missing_optical'] += 1
            continue
        included.append((row,w1-w2,(math.floor(g/2),math.floor(color))))
    tests = []
    for index,key in enumerate(('ruwe','phot_bp_rp_excess_factor')):
        eligible = [(row,ir,group) for row,ir,group in included if probe.number(row,key) is not None]
        result = probe.permutation_association([probe.number(row,key) for row,_,_ in eligible],
                                               [ir for _,ir,_ in eligible],[group for _,_,group in eligible],dig.SEED+500+index)
        if result.get('status')=='ok':
            result['descriptive_20_test_adjusted_p']=min(1,result['permutation_p']*20)
        tests.append(dict(x=key,y='W1-W2',result=result))
    return dict(status='adaptive_exploration',included=len(included),excluded=excluded,tests=tests,
                interpretation='Two follow-up tests per field selected after Gaia screening; 20 total scientific tests including the original 16. Adjusted p is descriptive, not independent confirmation. SNR>=5 in both WISE bands and one-to-one candidates used for color tests; excluded/flagged sources remain in the raw catalog and match record.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--needle', choices=['calibration','exploration','confirmation'], default='calibration')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    field = dig.get_needle(args.needle)
    started, batch = time.monotonic(), Batch()
    gaia, gm, _ = dig.fetch_gaia(args.needle, offline=True, endpoint=dig.ARCHIVES['ari'])
    wise, wm = fetch_wise(args.needle,batch,args.offline)
    matches = summarize_matches(gaia,wise,field)
    reference, rm = published_matches(args.needle,batch,args.offline)
    result = dict(needle=field, gaia_manifest=gm, allwise_manifest=wm, reference_manifest=rm,
                  gaia_screen=probe.screen(gaia,field), crossmatch=matches,
                  published_calibration=reference_agreement(matches,reference), highest_ruwe_inspection=inspect_leads(gaia,wise,matches),
                  infrared_followup=infrared_followup(gaia,wise,matches),
                  elapsed_seconds=round(time.monotonic()-started,3),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report = json.loads(args.output.read_text()) if args.output.exists() else dict(schema_version=1, fields={})
    report['fields'][args.needle] = result
    report['interpretation'] = 'Exploratory field notebook. No discovery or novelty claim. Confirmation needle remains untouched.'
    report['acknowledgements'] = ['ESA Gaia / DPAC', 'AllWISE: joint UCLA/JPL-Caltech project, funded by NASA; data served by NASA/IPAC IRSA']
    dig.write_json(args.output,report)
    print(json.dumps(dict(needle=args.needle,allwise_rows=len(wise), matched_gaia=matches['matched_gaia'],median_offset_arcsec=matches['median_offset_arcsec'],
                          published=result['published_calibration'],seconds=result['elapsed_seconds']),indent=2))


if __name__ == '__main__':
    main()

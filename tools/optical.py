"""A bounded DES DR2 optical layer; verify schema before fetching a cone."""
import argparse
import json
import hashlib
import itertools
import math
from pathlib import Path
import statistics
import time

import dig
import layers
import probe

ENDPOINT='https://datalab.noirlab.edu/tap/sync'
COLUMNS='coadd_object_id,ra,dec,mag_auto_g,mag_auto_r,mag_auto_i,mag_auto_z,mag_auto_y,magerr_auto_i,spread_model_i,spreaderr_model_i,flags_i,imaflags_iso_i'


def schema(batch,offline=False):
    names=','.join("'"+key+"'" for key in COLUMNS.split(','))
    query=f"SELECT column_name,datatype,unit FROM TAP_SCHEMA.columns WHERE table_name='des_dr2.main' AND column_name IN ({names}) ORDER BY column_name"
    rows,manifest=layers.table('calibration','DES DR2 schema',ENDPOINT,query,'column_name,datatype,unit',batch,offline)
    absent=set(COLUMNS.split(','))-{r['column_name'] for r in rows}
    if absent:
        raise ValueError('DES schema missing requested columns: '+','.join(sorted(absent)))
    return rows,manifest


def fetch(role,batch,offline=False):
    field=dig.get_needle(role)
    # This TAP service passes ADQL geometry to PostgreSQL without translating it.
    # Use an indexed numeric box, then trim its corners locally with exact geometry.
    radius=field['radius_deg']; dec=field['dec_deg']; ra=field['ra_deg']
    width=math.degrees(math.asin(math.sin(math.radians(radius))/math.cos(math.radians(dec))))
    low,high=(ra-width)%360,(ra+width)%360
    ra_clause=f'ra BETWEEN {low} AND {high}' if low<high else f'(ra >= {low} OR ra <= {high})'
    query=(f"SELECT TOP {dig.budget()['initial_sample_rows']} {COLUMNS} FROM des_dr2.main "
           f"WHERE {ra_clause} AND dec BETWEEN {dec-radius} AND {dec+radius} ORDER BY coadd_object_id")
    rows,manifest=layers.table(role,'DES DR2 optical',ENDPOINT,query,COLUMNS,batch,offline)
    identifiers=set()
    for row in rows:
        ra,dec=float(row['ra']),float(row['dec'])
        if not (math.isfinite(ra) and math.isfinite(dec) and 0<=ra<360 and -90<=dec<=90):
            raise ValueError('Invalid DES position')
        if row['coadd_object_id'] in identifiers:
            raise ValueError('Duplicate DES object ID')
        identifiers.add(row['coadd_object_id'])
    cone=[r for r in rows if dig.separation(float(r['ra']),float(r['dec']),field['ra_deg'],field['dec_deg'])<=field['radius_deg']+1e-7]
    manifest=dict(manifest,retrieval_geometry='Numeric bounding box, exact spherical cone trimming locally',
                  rows_in_cone=len(cone),box_rows=len(rows),cone_may_be_truncated=manifest['possibly_truncated'])
    return cone,manifest


def match_pairs(left,right,left_id,right_id,radius_arcsec):
    """Unit-vector cells avoid brute-force pair growth and work at RA wrap/poles."""
    if radius_arcsec<=0:
        raise ValueError('Match radius must be positive')
    cell=2*math.sin(math.radians(radius_arcsec/3600)/2)
    def key(row):
        ra,dec=math.radians(float(row['ra'])),math.radians(float(row['dec']))
        return tuple(math.floor(v/cell) for v in (math.cos(dec)*math.cos(ra),math.cos(dec)*math.sin(ra),math.sin(dec)))
    grid={}
    for row in right:
        grid.setdefault(key(row),[]).append(row)
    pairs=[]
    for row in left:
        base=key(row)
        for delta in itertools.product((-1,0,1),repeat=3):
            for other in grid.get(tuple(a+b for a,b in zip(base,delta)),[]):
                distance=3600*dig.separation(float(row['ra']),float(row['dec']),float(other['ra']),float(other['dec']))
                if distance<=radius_arcsec:
                    pairs.append(dict(left_id=row[left_id],right_id=other[right_id],separation_arcsec=distance))
    return sorted(pairs,key=lambda p:(p['left_id'],p['separation_arcsec'],p['right_id']))


def magnitude(row,band='i'):
    value=probe.number(row,'mag_auto_'+band)
    return value if value is not None and -10<value<40 else None


def median(values):
    values=[v for v in values if v is not None]
    return statistics.median(values) if values else None


def crowding_followup(gaia,optical,pairs,field):
    measured=[]
    excluded=dict(no_secure_primary=0,edge_censored=0,missing_magnitude_or_color=0)
    for row in gaia:
        own={p['right_id'] for p in pairs if p['left_id']==row['source_id']}
        if len(own)!=1:
            excluded['no_secure_primary']+=1
            continue
        distances=[3600*dig.separation(float(row['ra']),float(row['dec']),float(other['ra']),float(other['dec'])) for other in optical if other['coadd_object_id'] not in own]
        nearest=min(distances,default=math.inf)
        edge=3600*(field['radius_deg']-dig.separation(float(row['ra']),float(row['dec']),field['ra_deg'],field['dec_deg']))
        if nearest>edge:
            excluded['edge_censored']+=1
            continue
        g,color=probe.number(row,'phot_g_mean_mag'),probe.number(row,'bp_rp')
        if g is None or color is None:
            excluded['missing_magnitude_or_color']+=1
            continue
        measured.append((row,nearest,(math.floor(g/2),math.floor(color))))
    tests=[]
    for index,key in enumerate(('ruwe','phot_bp_rp_excess_factor')):
        eligible=[(r,d,g) for r,d,g in measured if probe.number(r,key) is not None]
        result=probe.permutation_association([probe.number(r,key) for r,_,_ in eligible],[d for _,d,_ in eligible],[g for _,_,g in eligible],dig.SEED+900+index)
        if result.get('status')=='ok':
            result['descriptive_34_test_adjusted_p']=min(1,result['permutation_p']*34)
        tests.append(dict(x=key,y='nearest_other_DES_source_arcsec',conditioning='two_magnitude_and_one_color_bins',result=result))
    return dict(eligible=len(measured),nearest_other_median_arcsec=median([d for _,d,_ in measured]),excluded=excluded,tests=tests,
                interpretation='Adaptive follow-up to the Gaia fit/excess lead, using the same open fields. Excludes the sole optical primary and censors distances that exceed the distance to the cone boundary. DES deblends/flags can create apparent neighbours; projected separation is not a physical companion classification. No independent confirmation.')


def analyze(gaia,wise,optical,field):
    gp=match_pairs(gaia,optical,'source_id','coadd_object_id',1.)
    wp=match_pairs(wise,optical,'designation','coadd_object_id',2.)
    gi,oi={p['left_id'] for p in gp},{p['right_id'] for p in gp}
    wi,wo={p['left_id'] for p in wp},{p['right_id'] for p in wp}
    bins=[]
    for lower,upper in [(-10,18),(18,20),(20,22),(22,24),(24,40)]:
        sample=[r for r in optical if magnitude(r) is not None and lower<=magnitude(r)<upper]
        bins.append(dict(i_magnitude_interval=[lower,upper],rows=len(sample),with_gaia=sum(r['coadd_object_id'] in oi for r in sample),with_allwise=sum(r['coadd_object_id'] in wo for r in sample)))
    interior=[r for r in gaia if 3600*dig.separation(float(r['ra']),float(r['dec']),field['ra_deg'],field['dec_deg'])<field['radius_deg']*3600-35]
    controls=[]
    for dra,ddec in [(30,0),(-30,0),(0,30),(0,-30)]:
        shifted=[dict(r,ra=str((float(r['ra'])+dra/(3600*math.cos(math.radians(float(r['dec'])))))%360),dec=str(float(r['dec'])+ddec/3600)) for r in interior]
        pairs=match_pairs(shifted,optical,'source_id','coadd_object_id',1.)
        controls.append(dict(offset_arcsec=[dra,ddec],hits=len({p['left_id'] for p in pairs}),denominator=len(interior)))
    tests=[]
    for index,(key,conditioning) in enumerate([('spread_model_i','i_magnitude'),('mag_auto_i','sky_quadrants')]):
        eligible=[r for r in optical if magnitude(r) is not None and probe.number(r,key) is not None]
        x=[probe.number(r,key) for r in eligible]
        y=[int(r['coadd_object_id'] not in oi) for r in eligible]
        groups=[math.floor(magnitude(r)/2) if conditioning=='i_magnitude' else (float(r['ra'])>=field['ra_deg'],float(r['dec'])>=field['dec_deg']) for r in eligible]
        result=probe.permutation_association(x,y,groups,dig.SEED+800+index)
        if result.get('status')=='ok':
            result['descriptive_30_test_adjusted_p']=min(1,result['permutation_p']*30)
        tests.append(dict(x=key,y='no_gaia_candidate',conditioning=conditioning,result=result))
    return dict(gaia_rows=len(gaia),allwise_rows=len(wise),des_rows=len(optical),
                radii_arcsec=dict(gaia_des=1,allwise_des=2),gaia_des_pairs=gp,allwise_des_pairs=wp,
                matched_gaia=len(gi),matched_allwise=len(wi),des_with_gaia=len(oi),des_with_allwise=len(wo),
                gaia_median_offset_arcsec=median([p['separation_arcsec'] for p in gp]),
                unmatched_gaia=[r['source_id'] for r in gaia if r['source_id'] not in gi],
                unmatched_allwise=[r['designation'] for r in wise if r['designation'] not in wi],
                des_without_gaia=[r['coadd_object_id'] for r in optical if r['coadd_object_id'] not in oi],
                des_without_allwise=[r['coadd_object_id'] for r in optical if r['coadd_object_id'] not in wo],
                i_magnitude_bins=bins,median_i=median([magnitude(r) for r in optical]),missing_or_sentinel_i=sum(magnitude(r) is None for r in optical),
                median_spread_i_with_gaia=median([probe.number(r,'spread_model_i') for r in optical if r['coadd_object_id'] in oi]),
                median_spread_i_without_gaia=median([probe.number(r,'spread_model_i') for r in optical if r['coadd_object_id'] not in oi]),
                flagged_i_count=sum(probe.number(r,'flags_i') not in (None,0) or probe.number(r,'imaflags_iso_i') not in (None,0) for r in optical),
                gaia_interior_unshifted=dict(hits=len({p['left_id'] for p in match_pairs(interior,optical,'source_id','coadd_object_id',1.)}),denominator=len(interior)),
                shifted_controls=controls,tests=tests,crowding_followup=crowding_followup(gaia,optical,gp,field),
                selection='All catalog flags retained. Magnitude values outside (-10,40), including DES 99 sentinels, are unavailable for magnitude summaries. Spread_model is a morphology measurement, not a trusted object class. No parallax inversion or redshift inferred. Catalog magnitudes differ in bandpass and cannot be treated as a common distance axis.')


def portable(manifest):
    return dict({k:v for k,v in manifest.items() if k!='cache_file'},cache_filename=Path(manifest['cache_file']).name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema',action='store_true')
    parser.add_argument('--needle',choices=['calibration','exploration','confirmation'],default='calibration')
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--output',type=Path,default=dig.ROOT/'experiments/optical-first-look.json')
    args=parser.parse_args()
    field=dig.get_needle(args.needle)
    started=time.monotonic(); batch=layers.Batch()
    rows,sm=schema(batch,args.offline)
    if args.schema:
        print(json.dumps(dict(columns=rows,sha256=sm['sha256']),indent=2)); return
    optical,om=fetch(args.needle,batch,args.offline)
    gaia,gm,_=dig.fetch_gaia(args.needle,offline=True,endpoint=dig.ARCHIVES['ari'])
    wise,wm=layers.fetch_wise(args.needle,batch,offline=True)
    result=dict(needle=field,schema_manifest=portable(sm),optical_manifest=portable(om),gaia_manifest=portable(gm),allwise_manifest=portable(wm),
                analysis=analyze(gaia,wise,optical,field),elapsed_seconds=round(time.monotonic()-started,3),
                code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                coverage='Nonempty cone demonstrates some DES catalog coverage, not complete spatial coverage or a measured selection function.' if optical else 'Empty cone: no evidence of DES coverage; not an astrophysical absence.')
    report=json.loads(args.output.read_text()) if args.output.exists() else dict(schema_version=1,fields={})
    report['fields'][args.needle]=result
    report['attempted_new_scientific_configurations']=8
    report['prior_scientific_configurations']=26
    report['interpretation']='Exploration on the two open fields. Fixed matching radii and uncalibrated coarse nulls. No confirmation, physical classification or novelty claim.'
    report['references']=['https://datalab.noirlab.edu/data/dark-energy-survey','https://arxiv.org/abs/2101.05765']
    report['acknowledgement']='DES Collaboration; data served by Astro Data Lab at NSF NOIRLab.'
    dig.write_json(args.output,report)
    a=result['analysis']
    print(json.dumps(dict(needle=args.needle,des_rows=len(optical),matched_gaia=a['matched_gaia'],matched_allwise=a['matched_allwise'],median_i=a['median_i'],crowding=a['crowding_followup'],seconds=result['elapsed_seconds']),indent=2))


if __name__=='__main__':
    main()

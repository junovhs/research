from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import optical
import dig


class OpticalTests(unittest.TestCase):
    def test_crowding_excludes_primary_and_censors_field_boundary(self):
        gaia=[dict(source_id='g0',ra='0',dec='0',phot_g_mean_mag='18',bp_rp='1'),
              dict(source_id='g1',ra='.0999',dec='0',phot_g_mean_mag='18',bp_rp='1')]
        des=[dict(coadd_object_id='d0',ra='0',dec='0'),dict(coadd_object_id='d1',ra='.001',dec='0'),
             dict(coadd_object_id='d2',ra='.0999',dec='0'),dict(coadd_object_id='d3',ra='.09',dec='0')]
        pairs=[dict(left_id='g0',right_id='d0'),dict(left_id='g1',right_id='d2')]
        result=optical.crowding_followup(gaia,des,pairs,dict(ra_deg=0,dec_deg=0,radius_deg=.1))
        self.assertEqual(result['eligible'],1)
        self.assertEqual(result['excluded']['edge_censored'],1)
        self.assertAlmostEqual(result['nearest_other_median_arcsec'],3.6)

    def test_index_matches_exact_geometry_at_wrap_and_pole(self):
        rng=random.Random(81)
        left=[dict(id=str(i),ra=str(rng.uniform(0,360)),dec=str(rng.uniform(-89,89))) for i in range(60)]
        left += [dict(id='wrap',ra='359.9999',dec='0'),dict(id='pole',ra='10',dec='89.9999')]
        right=[dict(id='r'+r['id'],ra=str((float(r['ra'])+.0002)%360),dec=r['dec']) for r in left]
        actual=optical.match_pairs(left,right,'id','id',1)
        expected={(r['id'],s['id']) for r in left for s in right if 3600*dig.separation(float(r['ra']),float(r['dec']),float(s['ra']),float(s['dec']))<=1}
        self.assertEqual({(p['left_id'],p['right_id']) for p in actual},expected)
        self.assertEqual(len(actual),len(left))

    def test_sentinel_magnitude_is_unavailable(self):
        self.assertIsNone(optical.magnitude({'mag_auto_i':'99'}))
        self.assertIsNone(optical.magnitude({'mag_auto_i':'NaN'}))
        self.assertEqual(optical.magnitude({'mag_auto_i':'23.5'}),23.5)

    def test_nonmatches_and_flags_remain_in_record(self):
        gaia=[dict(source_id='g',ra='0',dec='0')]
        wise=[dict(designation='w',ra='0',dec='0')]
        des=[dict(coadd_object_id='d1',ra='0',dec='0',mag_auto_i='18',spread_model_i='0',flags_i='4'),
             dict(coadd_object_id='d2',ra='0.01',dec='0',mag_auto_i='24',spread_model_i='.02',flags_i='0')]
        result=optical.analyze(gaia,wise,des,dict(ra_deg=0,dec_deg=0,radius_deg=.1))
        self.assertEqual(result['matched_gaia'],1)
        self.assertEqual(result['des_without_gaia'],['d2'])
        self.assertEqual(result['flagged_i_count'],1)
        self.assertEqual(result['des_rows'],2)


if __name__=='__main__':
    unittest.main()

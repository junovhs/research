from pathlib import Path
import sys
import unittest
import os
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import layers


class CrossmatchTests(unittest.TestCase):
    def test_layer_cache_replay_and_corruption_with_real_file_transport(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = os.environ.get('NEEDLE_CACHE')
            os.environ['NEEDLE_CACHE'] = str(Path(directory)/'cache')
            try:
                source=Path(directory)/'source.csv'
                source.write_text('id,value\na,1\n')
                args=('calibration','fixture',source.as_uri(),'SELECT id,value','id,value')
                rows,meta=layers.table(*args,layers.Batch())
                self.assertEqual(rows,[{'id':'a','value':'1'}])
                source.unlink()
                replay,_=layers.table(*args,layers.Batch(),offline=True)
                self.assertEqual(rows,replay)
                Path(meta['cache_file']).write_text('id,value\na,2\n')
                with self.assertRaisesRegex(ValueError,'checksum'):
                    layers.table(*args,layers.Batch(),offline=True)
            finally:
                if previous is None: os.environ.pop('NEEDLE_CACHE',None)
                else: os.environ['NEEDLE_CACHE']=previous

    def test_ambiguity_nonmatches_and_ra_wrap(self):
        gaia=[dict(source_id='1',ra='359.9999',dec='0'),dict(source_id='2',ra='20',dec='0'),dict(source_id='3',ra='0.0002',dec='0')]
        wise=[dict(designation='a',ra='0',dec='0'),dict(designation='b',ra='359.9998',dec='0'),dict(designation='c',ra='40',dec='0')]
        result=layers.summarize_matches(gaia,wise,dict(ra_deg=0,dec_deg=0,radius_deg=.1))
        self.assertEqual(result['unmatched_gaia'],['2'])
        self.assertEqual(result['unmatched_allwise'],['c'])
        self.assertEqual(set(result['ambiguous_gaia']),{'1','3'})
        self.assertEqual(set(result['shared_allwise']),{'a','b'})
        self.assertEqual(result['matched_gaia'],2)
        self.assertEqual(result['shifted_controls'][0]['matched_gaia'],0)
        self.assertEqual(result['interior_unshifted']['matched_gaia'],2)

    def test_published_pair_identity_not_just_nearness(self):
        matches={'candidate_pairs':[dict(source_id='1',designation='right')]}
        reference=[dict(source_id='1',original_ext_source_id='right'),dict(source_id='2',original_ext_source_id='absent')]
        result=layers.reference_agreement(matches,reference)
        self.assertEqual(result['recovered_pairs'],1)
        self.assertEqual(result['missed_published_pairs'],reference[1:])

    def test_actual_spherical_distance_at_high_declination(self):
        pairs=layers.associations([dict(source_id='1',ra='10',dec='80')],[dict(designation='w',ra='10.002',dec='80')])
        self.assertEqual(len(pairs),1) # 7.2 arcsec in RA, but only 1.25 arcsec on sky.
        self.assertAlmostEqual(pairs[0]['separation_arcsec'],1.2503,places=3)


if __name__ == '__main__':
    unittest.main()

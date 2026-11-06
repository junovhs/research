import math
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import probe


class ProbeTests(unittest.TestCase):
    def test_detect_injected_relation_with_ties(self):
        x = list(range(120))
        y = [i//10 for i in x]
        result = probe.permutation_association(x, y, [0]*120, 12, 199)
        self.assertEqual(result['permutation_p'], 0.005)
        self.assertGreater(result['within_block_rank_correlation'], .99)

    def test_depth_confound_removed_and_constants_not_tested(self):
        x = [0]*40 + [1]*40
        y = x.copy()
        naive = probe.permutation_association(x, y, [0]*80, 2, 199)
        blocked = probe.permutation_association(x, y, x, 2, 199)
        self.assertEqual(naive['permutation_p'], .005)
        self.assertEqual(blocked['status'], 'constant_within_blocks')

    def test_missing_negative_parallax_and_zero_error(self):
        result = probe.derived({'parallax': '-1', 'parallax_error': '0.5', 'pmra': '3', 'pmdec': '4', 'bp_rp': 'NaN'})
        self.assertEqual(result['parallax_snr'], -2)
        self.assertEqual(result['proper_motion'], 5)
        self.assertEqual(result['missing_color'], 1)
        self.assertIsNone(probe.derived({'parallax': '1', 'parallax_error': '0'})['parallax_snr'])

    def test_null_rate_software_benchmark(self):
        # Fixed synthetic benchmark, not a scientific calibration of the sky null.
        rng = random.Random(773)
        flags = 0
        for i in range(40):
            x = [rng.random() for _ in range(60)]
            y = [rng.random() for _ in range(60)]
            result = probe.permutation_association(x, y, [0]*60, 100+i, 199)
            flags += result['permutation_p'] <= .05
        self.assertLessEqual(flags, 6)


if __name__ == '__main__':
    unittest.main()

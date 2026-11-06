import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("dig", Path(__file__).resolve().parents[1] / "tools/dig.py")
dig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dig)


class NeedleTests(unittest.TestCase):
    def test_reproducible_frozen_selection(self):
        import json
        stored = json.loads((dig.ROOT / "config/needles.json").read_text())
        self.assertEqual(dig.select_needles(), stored)

    def test_geometry_and_holdout(self):
        fields = dig.select_needles()["needles"]
        for field in fields[1:]:
            self.assertGreaterEqual(abs(dig.galactic_latitude(field["ra_deg"], field["dec_deg"])), 35)
            self.assertTrue(-60 < field["dec_deg"] < -15)
        for i, field in enumerate(fields):
            for other in fields[i+1:]:
                self.assertGreater(dig.separation(field["ra_deg"], field["dec_deg"], other["ra_deg"], other["dec_deg"]), 20)
        with self.assertRaisesRegex(ValueError, "sealed"):
            dig.get_needle("confirmation")

    def test_ra_wrap_and_pole(self):
        self.assertAlmostEqual(dig.separation(359.999, 0, 0.001, 0), 0.002)
        self.assertAlmostEqual(dig.separation(0, 90, 180, 90), 0)


if __name__ == "__main__":
    unittest.main()

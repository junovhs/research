import importlib.util
from pathlib import Path
import unittest
import csv
import io
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

spec = importlib.util.spec_from_file_location("dig", Path(__file__).resolve().parents[1] / "tools/dig.py")
dig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dig)


def sample_csv(**changes):
    field = dig.get_needle("calibration")
    row = dict.fromkeys(dig.COLUMNS.split(","), "")
    row.update(source_id="1234567890123456789", ra=str(field["ra_deg"]), dec=str(field["dec_deg"]), ref_epoch="2016.0")
    row.update(changes)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=dig.COLUMNS.split(","))
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue().encode()


class ArchiveTests(unittest.TestCase):
    def test_http_fetch_offline_replay_and_corruption(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(sample_csv())
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as directory:
                cache = Path(directory)
                endpoint = f'http://127.0.0.1:{server.server_port}/tap'
                rows, manifest, hit = dig.fetch_gaia('calibration', cache=cache, endpoint=endpoint)
                self.assertFalse(hit)
                self.assertEqual(rows[0]['source_id'], '1234567890123456789')
                server.shutdown()  # Replay must succeed with server stopped.
                _, replay, hit = dig.fetch_gaia('calibration', offline=True, cache=cache, endpoint=endpoint)
                self.assertTrue(hit)
                self.assertEqual(manifest['sha256'], replay['sha256'])
                Path(manifest['cache_file']).write_bytes(b'corrupted')
                with self.assertRaisesRegex(ValueError, 'checksum'):
                    dig.fetch_gaia('calibration', offline=True, cache=cache, endpoint=endpoint)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_reject_wrong_cone_and_error_page(self):
        field = dig.get_needle('calibration')
        with self.assertRaisesRegex(ValueError, 'outside'):
            dig.parse_gaia(sample_csv(ra='180'), field)
        with self.assertRaisesRegex(ValueError, 'schema'):
            dig.parse_gaia(b'<VOTABLE>QUERY_STATUS ERROR</VOTABLE>', field)

    def test_confirmation_rejected_before_any_cache_access(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'must-not-exist'
            with self.assertRaisesRegex(ValueError, 'sealed'):
                dig.fetch_gaia('confirmation', cache=cache, endpoint='http://127.0.0.1:1')
            self.assertFalse(cache.exists())

    def test_download_byte_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'large'
            path.write_bytes(b'x' * 100)
            with self.assertRaisesRegex(ValueError, 'byte budget'):
                dig.bounded_request(path.as_uri(), '', 10, time.monotonic() + 5)


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

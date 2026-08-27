import sys
from pathlib import Path
import unittest

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qr_utils import is_openable_url


class UrlClassificationTests(unittest.TestCase):
    def test_accepts_web_urls(self):
        self.assertTrue(is_openable_url("https://line.me/ti/p/example"))
        self.assertTrue(is_openable_url("http://example.com/path"))

    def test_accepts_line_protocol(self):
        self.assertTrue(is_openable_url("line://ti/p/example"))

    def test_rejects_non_urls(self):
        self.assertFalse(is_openable_url("純文字內容"))
        self.assertFalse(is_openable_url("WIFI:T:WPA;S:network;P:secret;;"))
        self.assertFalse(is_openable_url("https://"))


class QrDecodeTests(unittest.TestCase):
    def test_decodes_a_standard_qr_image(self):
        encoder = cv2.QRCodeEncoder_create(cv2.QRCodeEncoder_Params())
        image = encoder.encode("https://line.me/ti/p/example")
        image = cv2.resize(image, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
        image = cv2.copyMakeBorder(image, 32, 32, 32, 32, cv2.BORDER_CONSTANT, value=255)
        ok, encoded = cv2.imencode(".png", image)
        self.assertTrue(ok)
        from qr_utils import decode_qr_png
        self.assertEqual(decode_qr_png(encoded.tobytes()), ["https://line.me/ti/p/example"])


if __name__ == "__main__":
    unittest.main()

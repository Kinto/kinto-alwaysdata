import unittest
from .utils import hmac_digest


class HmacDigestTest(unittest.TestCase):
    def test_supports_secret_as_text(self):
        value = hmac_digest("blah", "input data")
        self.assertTrue(value.startswith("d4f5c51db246c7faeb42240545b47274b6"))

    def test_supports_secret_as_bytes(self):
        value = hmac_digest(b"blah", "input data")
        self.assertTrue(value.startswith("d4f5c51db246c7faeb42240545b47274b6"))

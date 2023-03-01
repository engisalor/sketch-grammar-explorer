import unittest

from sgex.call.package import Package
from sgex.call.type import Freqs
from sgex.config import default
from sgex.parse import freqs


class TestParseFreqs(unittest.TestCase):
    def test_freqs_json_one_block(self):
        call = Freqs({"corpname": "susanne", "q": 'alemma,"day"', "fcrit": "doc 0"})
        p = Package(call, "noske", default)
        p.send_requests()
        df = freqs.freqs_json(p.responses[0])
        self.assertEqual(df["frq"].sum(), 116)

    def test_freqs_json_two_block(self):
        fcrit = ["doc.file 0", "doc.n 0"]
        call = Freqs({"corpname": "susanne", "q": 'alemma,"day"', "fcrit": fcrit})
        p = Package(call, "noske", default)
        p.send_requests()
        df = freqs.freqs_json(p.responses[0])
        ref = [x.replace(" 0", "") for x in fcrit]

        self.assertListEqual(df["attribute"].unique().tolist(), ref)


if __name__ == "__main__":
    unittest.main()

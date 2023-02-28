import unittest

from sgex.call.package import Package
from sgex.call.type import Wordlist
from sgex.config import default
from sgex.parse import wordlist


class TestParseWordlist(unittest.TestCase):
    def test_wordlist_ttype_analysis_json(self):
        call = Wordlist(
            {
                "corpname": "susanne",
                "wlattr": "doc.file",
                "wltype": "simple",
                "wlminfreq": 1,
            }
        )
        p = Package(call, "noske", default)
        p.send_requests()
        df = wordlist.ttype_analysis_json(p.responses[0])
        self.assertEqual(len(df), 64)


if __name__ == "__main__":
    unittest.main()

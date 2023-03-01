import unittest

from sgex.call.package import Package
from sgex.call.type import CorpInfo
from sgex.config import default
from sgex.parse import corp_info


class TestParseCorpInfo(unittest.TestCase):
    def test_structures_json(self):
        call = CorpInfo({"corpname": "susanne", "struct_attr_stats": 1})
        p = Package(call, "noske", default)
        p.send_requests()
        df = corp_info.structures_json(p.responses[0])
        dt = {
            "structure": {0: "doc", 1: "doc", 2: "doc"},
            "attribute": {0: "file", 1: "n", 2: "wordcount"},
            "size": {0: 64, 1: 12, 2: 1},
        }
        self.assertDictEqual(df.to_dict(), dt)

    def test_sizes_json(self):
        call = CorpInfo({"corpname": "susanne", "struct_attr_stats": 1})
        p = Package(call, "noske", default)
        p.send_requests()
        df = corp_info.sizes_json(p.responses[0])
        dt = {
            "structure": {0: "token", 1: "word", 2: "doc", 3: "par", 4: "sent"},
            "size": {0: 150426, 1: 128998, 2: 149, 3: 1923, 4: 0},
        }
        self.assertDictEqual(df.to_dict(), dt)


if __name__ == "__main__":
    unittest.main()

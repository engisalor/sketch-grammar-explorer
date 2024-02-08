import unittest

import numpy as np

from sgex import util


class Test_Flatten(unittest.TestCase):
    def test_flatten_list_of_dict(self):
        ls_of_dict = [
            {
                "name": "A",
                "location": {"lon": 1.1, "lat": 1.2},
                "id": 1,
                "shortname": "A",
                "primary": True,
            },
            {
                "name": "B",
                "location": {"lon": 2.1, "lat": 2.2},
                "id": 2,
                "shortname": "B",
            },
            {
                "name": "C",
                "id": 3,
                "shortname": "C",
                "primary": True,
            },
        ]
        flat_dict = {
            "name": ["A", "B", "C"],
            "location": {"lon": [1.1, 2.1, np.nan], "lat": [1.2, 2.2, np.nan]},
            "id": [1, 2, 3],
            "shortname": ["A", "B", "C"],
            "primary": [True, np.nan, True],
        }
        self.assertEqual(str(util.flatten_ls_of_dt(ls_of_dict)), str(flat_dict))


class Test_Util(unittest.TestCase):
    def test_detect_cql_type(self):
        t1 = "[#1|#2000|#456789]"
        self.assertEqual(util.detect_cql_type(t1), "ID")
        t1b = "[#1 | #2000 | #456789 ]"
        self.assertEqual(util.detect_cql_type(t1b), "ID")
        t2 = '[lemma="apple"]'
        self.assertEqual(util.detect_cql_type(t2), "CQL")

    def test_url_from_cql(self):
        cql = '[lemma="work"]'
        corpname = "susanne"
        base = "http://localhost:10070/#concordance?"
        url = util.url_from_cql(cql, corpname, base)
        ref = "http://localhost:10070/#concordance?corpname=susanne&cql=%5Blemma%3D%22work%22%5D&viewmode=sen&tab=advanced&queryselector=cql&showresults=1&default_attr=lemma_lc"  # noqa: E501
        self.assertEqual(url, ref)


if __name__ == "__main__":
    unittest.main()

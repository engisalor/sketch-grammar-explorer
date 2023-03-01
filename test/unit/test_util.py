import unittest

import numpy as np

from sgex.util import flatten_ls_of_dt


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
        self.assertEqual(str(flatten_ls_of_dt(ls_of_dict)), str(flat_dict))


if __name__ == "__main__":
    unittest.main()

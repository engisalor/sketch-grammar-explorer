import unittest

from sgex.call import type


class TestType(unittest.TestCase):
    def test_call_validate_missing_required(self):
        with self.assertRaises(ValueError):
            type.Call("freqs", {}).validate()

    def test_call_validate_bad_format(self):
        with self.assertRaises(ValueError):
            type.Call("freqs", {"corpname": "corpus", "format": "sqlite"}).validate()

    def test_call_init_bad_type(self):
        with self.assertRaises(ValueError):
            type.Call("none", {"corpname": "corpus"})

    def test_call_init_bad_params(self):
        with self.assertRaises(TypeError):
            type.Call("freqs", "not a dict!")

    def test_call_type(self):
        c = type.Call("corp_info", {"corpname": "susanne"})
        self.assertEqual(c.type, "corp_info")

    def test_call_dt(self):
        c = type.Call("corp_info", {"corpname": "susanne"})
        ref = {"type": "corp_info", "corpname": "susanne"}
        self.assertDictEqual(c.dt, ref)

    def test_view_asyn(self):
        c = type.View({"corpname": "susanne", "q": "query"})
        self.assertEqual(c.params.get("asyn", None), 0)


if __name__ == "__main__":
    unittest.main()

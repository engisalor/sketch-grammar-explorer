import unittest

from sgex.call import call
from sgex.call.type import CorpInfo, View
from sgex.config import default


class MockPreparedRequest:
    def __init__(self, url) -> None:
        self.url = url


class TestPrepareSteps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.calls_corp_info = [
            CorpInfo({"corpname": "susanne"}),
            CorpInfo({"corpname": "susanne"}),
        ]
        cls.calls_mix = [
            View({"corpname": "a", "q": ['alemma,"dog"'], "dt": {"a": 1}}),
            View({"corpname": "b", "dt": {"b": 2}}),
            View({"q": ['alemma,"cat"']}),
            CorpInfo({"corpname": "a"}),
        ]
        cls.url = "http://localhost:10070/bonito/run.cgi/corp_info?corpname=susanne"

    def test_propagate(self):
        ref = [
            View({"corpname": "a", "q": ['alemma,"dog"'], "dt": {"a": 1}}),
            View({"corpname": "b", "q": ['alemma,"dog"'], "dt": {"a": 1, "b": 2}}),
            View({"corpname": "b", "q": ['alemma,"cat"'], "dt": {"a": 1, "b": 2}}),
            CorpInfo({"corpname": "a"}),
        ]
        call.propagate(self.calls_mix)
        for x in range(len(ref)):
            self.assertDictEqual(self.calls_mix[x].params, ref[x].params)

    def test_add_creds(self):
        calls = [CorpInfo({"corpname": "susanne"}), CorpInfo({"corpname": "susanne"})]
        call.add_creds(calls, {"username": "J. Doe"})
        for c in calls:
            self.assertDictEqual(
                c.params, {"corpname": "susanne", "username": "J. Doe"}
            )

    def test_add_request(self):
        calls = self.calls_corp_info.copy()
        call.add_request(calls, "noske", default)
        for c in calls:
            self.assertEqual(c.request.prepare().url, self.url)

    def test_add_key(self):
        calls = self.calls_corp_info.copy()
        call.add_request(calls, "noske", default)
        call.add_key(calls)
        for c in calls:
            self.assertEqual(c.key, "20ce3425baaba2cc")

    def test_normalize_dt(self):
        dt = {"1": {"1.1 ": ["B", "C", " A"], "1.2": True}, " 2": "apple "}
        ref = {"1": {"1.1": ["A", "B", "C"], "1.2": True}, "2": "apple"}
        dt = call.normalize_dt(dt)
        self.assertDictEqual(dt, ref)


class TestCreateKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:10070/bonito/run.cgi/corp_info?"
        cls.search = "corpname=susanne&A=a&B=b&C=c"
        cls.url = cls.base_url + cls.search
        cls.request = MockPreparedRequest(cls.url)

    def test_create_custom_key_no_ignored(self):
        key = call.create_custom_key(self.request, [])
        self.assertEqual(key, "aa2fab08a7d784df")

    def test_create_custom_key_ignored(self):
        key = call.create_custom_key(self.request, ["B"])
        self.assertEqual(key, "00446a78c2641db3")


if __name__ == "__main__":
    unittest.main()

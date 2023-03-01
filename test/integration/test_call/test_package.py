import pathlib
import unittest
from time import perf_counter

from urllib3.exceptions import HTTPError

from sgex.call import type as t
from sgex.call.call import create_custom_key
from sgex.call.package import Package
from sgex.config import credential_parameters, default, load, read_keyring

avattr = {"avattr": "doc.file"}
corpname = {"corpname": "susanne"}
ref_corpname = {"ref_corpname": "susanne"}
q = {"q": 'alemma,"day"'}
fcrit = {"fcrit": "doc.file 0"}
lemma = {"lemma": "day"}
lemma2 = {"lemma2": "night"}
wordlist = {"wlattr": "word", "wltype": "simple"}

session_params = dict(
    cache_name="test/tmp/file_cache",
    serializer="json",
    backend="filesystem",
    ignored_parameters=credential_parameters,
    key_fn=create_custom_key,
)


def check_noske_responses(self) -> None:
    self.assertEqual(self.package.errors, set())
    for response in self.package.responses:
        self.assertEqual(200, response.status_code)
    self.assertIn(b"suggestions", self.package.responses[0]._content)
    self.assertIn(b"Cooccurrence count", self.package.responses[1]._content)
    self.assertIn(b"structures", self.package.responses[2]._content)
    self.assertIn(b"keywords", self.package.responses[3]._content)
    self.assertIn(b'"ml": true', self.package.responses[4]._content)
    self.assertIn(b"Frequency", self.package.responses[5]._content)
    self.assertIn(b"SubcorpList", self.package.responses[6]._content)
    self.assertIn(b"Lines", self.package.responses[7]._content)
    self.assertIn(b"wlattr", self.package.responses[8]._content)


class MockResponse:
    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError

    def __init__(self) -> None:
        self.base_url = "http://localhost:10070/bonito/run.cgi/corp_info?"
        self.search = "corpname=susanne&A=a&B=b&C=c"
        self.url = self.base_url + self.search
        self.status_code = 200
        self.headers = {"content-type": "application/json"}
        self.json_data = {"key": "value"}


class test__handle_errors(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.response = MockResponse()

    def test_no_raise_for_status(self):
        self.response.raise_for_status()
        package = Package([], "noske", default)
        package._handle_errors(self.response)

    def test_raise_for_status(self):
        with self.assertRaises(HTTPError):
            self.response.status_code = 400
            package = Package([], "noske", default)
            package._handle_errors(self.response)

    def test_halt_raise_ske_error(self):
        with self.assertRaises(Warning):
            package = Package([], "noske", default)
            package.halt = True
            self.response.json_data = {"error": "ERROR"}
            package._handle_errors(self.response)

    def test_halt_ignore_ske_error(self):
        package = Package([], "noske", default)
        package.halt = False
        self.response.json_data = {"error": "ERROR"}
        package._handle_errors(self.response)


class TestPackageNOSKE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pathlib.Path("test/tmp/file_cache").mkdir(exist_ok=True, parents=True)
        cls.calls = [
            t.AttrVals({**corpname, **avattr}),
            t.Collx({**corpname, **q}),
            t.CorpInfo({**corpname}),
            t.ExtractKeywords({**corpname, **ref_corpname}),
            t.Freqml({**corpname, **q, **fcrit}),
            t.Freqs({**corpname, **q, **fcrit}),
            # TODO include freqtt
            # t.Freqtt({**corpname, **{"q": 'alemma,"evening"'}, **fcrit}),
            t.Subcorp({**corpname}),
            t.View({**corpname, **q}),
            t.Wordlist({**corpname, **wordlist}),
        ]

    def test_package_NOSKE_send_sequential(self):
        self.package = Package(
            self.calls, "noske", default, session_params=session_params
        )
        self.package.session.cache.clear()
        self.package.send_requests()
        check_noske_responses(self)

    def test_package_NOSKE_send_async_prohibited(self):
        config = {"noske": {**default["noske"]}}
        config["noske"]["asynchronous"] = False
        self.package = Package(
            self.calls, "noske", config, session_params=session_params
        )
        with self.assertRaises(ValueError):
            self.package.send_async_requests()

    def test_package_NOSKE_send_with_wait(self):
        config = {"noske": {**default["noske"]}}
        # without wait (very quick)
        self.package = Package(
            self.calls[:2], "noske", config, session_params=session_params
        )
        self.package.session.cache.clear()
        t0 = perf_counter()
        self.package.send_requests()
        t1 = perf_counter()
        self.assertGreaterEqual(2, t1 - t0)
        self.package.session.cache.clear()
        # with wait (at least 2 seconds)
        config["noske"]["wait"] = {"1": None}
        self.package = Package(
            self.calls[:2], "noske", config, session_params=session_params
        )
        t2 = perf_counter()
        self.package.send_requests()
        t3 = perf_counter()
        self.assertGreaterEqual(t3 - t2, 2)

    def test_package_NOSKE_send_async(self):
        # TODO aync responses are unordered - could address how to get X call from list
        self.package = Package(
            self.calls, "noske", default, session_params=session_params
        )
        self.package.session.cache.clear()
        self.package.send_async_requests()
        self.assertEqual(self.package.errors, set())
        for response in self.package.responses:
            self.assertEqual(200, response.status_code)

    def test_package_NOSKE_credentials_not_redacted_json(self):
        config = {
            "noske": {
                **default["noske"],
                **{"username": "J. Doe", "api_key": "__mock_api_key__"},
            }
        }
        self.package = Package(self.calls, "noske", config)
        self.package.session.hooks = {"response": []}
        self.package.session.cache.clear()
        self.package.send_requests()
        for response in self.package.responses:
            self.assertIn(b"J. Doe", response.content)
            self.assertIn(b"__mock_api_key__", response.content)

    def test_package_NOSKE_credentials_redacted_json(self):
        config = {
            "noske": {
                **default["noske"],
                **{"username": "J. Doe", "api_key": "__mock_api_key__"},
            }
        }
        self.package = Package(self.calls, "noske", config)
        self.package.session.cache.clear()
        self.package.send_requests()
        for response in self.package.responses:
            self.assertNotIn(b"J. Doe", response.content)
            self.assertNotIn(b"__mock_api_key__", response.content)

    @unittest.skip("check if formats besides JSON need redacting (ignores XLSX)")
    def test_package_NOSKE_credentials_not_in_other_formats(self):
        config = {
            "noske": {
                **default["noske"],
                **{"username": "J. Doe", "api_key": "__mock_api_key__"},
            }
        }
        # run call types for each format and test for credential pollution
        for f in ["xml", "csv", "txt"]:
            format = {"format": f}
            calls = [
                t.AttrVals({**format, **corpname, **avattr}),
                t.Collx({**format, **corpname, **q}),
                t.CorpInfo({**format, **corpname}),
                t.ExtractKeywords({**format, **corpname, **ref_corpname}),
                t.Freqml({**format, **corpname, **q, **fcrit}),
                t.Freqs({**format, **corpname, **q, **fcrit}),
                # TODO include freqtt
                # t.Freqtt({**format,
                #     **corpname, **{"q": 'alemma,"evening"'}, **fcrit}),
                t.Subcorp({**format, **corpname}),
                t.View({**format, **corpname, **q}),
                t.Wordlist({**format, **corpname, **wordlist}),
            ]

            self.package = Package(calls, "noske", config)
            self.package.session.hooks = {"response": []}
            self.package.session.cache.clear()
            self.package.send_requests()
            for response in self.package.responses:
                self.assertNotIn(b"J. Doe", response.content)
                self.assertNotIn(b"__mock_api_key__", response.content)


@unittest.skip("manually test w/ SkE server (requires API key, config file & keyring)")
class TestPackageSKE(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pathlib.Path("test/tmp/file_cache").mkdir(exist_ok=True, parents=True)
        ske_corpname = {"corpname": "preloaded/susanne"}
        ske_ref_corpname = {"ref_corpname": "preloaded/susanne"}
        ske_thes_lemma = {"lemma": "be"}
        cls.ske_calls = [
            t.AttrVals({**ske_corpname, **avattr}),
            t.Collx({**ske_corpname, **q}),
            t.CorpInfo({**ske_corpname}),
            t.ExtractKeywords({**ske_corpname, **ske_ref_corpname}),
            t.Freqml({**ske_corpname, **q, **fcrit}),
            t.Freqs({**ske_corpname, **q, **fcrit}),
            # TODO include freqtt
            # t.Freqtt({**ske_corpname, **{"q": 'alemma,"evening"'}, **fcrit}),
            t.Subcorp({**ske_corpname}),
            t.Thes({**ske_corpname, **ske_thes_lemma}),
            t.View({**ske_corpname, **q}),
            t.Wsdiff({**ske_corpname, **lemma, **lemma2}),
            t.Wsketch({**ske_corpname, **lemma}),
            t.Wordlist({**ske_corpname, **wordlist}),
        ]

    def test_package_SKE_send_sequential(self):
        # NOTE loads credentials from file and keyring
        config = load(".config.yml")
        read_keyring(config, "ske")
        self.package = Package(
            self.ske_calls, "ske", config, session_params=session_params
        )
        self.package.send_requests()
        self.assertEqual(self.package.errors, set())
        for response in self.package.responses:
            self.assertEqual(200, response.status_code)
        self.assertIn(b"suggestions", self.package.responses[0]._content)
        self.assertIn(b"Cooccurrence count", self.package.responses[1]._content)
        self.assertIn(b"structures", self.package.responses[2]._content)
        self.assertIn(b"keywords", self.package.responses[3]._content)
        self.assertIn(b'"ml": true', self.package.responses[4]._content)
        self.assertIn(b"Frequency", self.package.responses[5]._content)
        self.assertIn(b"SubcorpList", self.package.responses[6]._content)
        self.assertIn(b"lemma", self.package.responses[7]._content)
        self.assertIn(b"Lines", self.package.responses[8]._content)
        self.assertIn(b"ws_status", self.package.responses[9]._content)
        self.assertIn(b"ws_status", self.package.responses[10]._content)
        self.assertIn(b"wlattr", self.package.responses[11]._content)


if __name__ == "__main__":
    unittest.main()

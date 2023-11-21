import json
import os
import shutil
import unittest
from copy import deepcopy

from yarl import URL

from sgex import call, job


class TestCacheResponseMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)

    def test_redact_json(self):
        dt = {"username": "J. Doe", "api_key": "1234"}
        dt = call.CachedResponse.redact_json({})
        self.assertDictEqual(dt, {})

    def test_redact_url(self):
        # simple example
        url = "http://localhost:10070/bonito/run.cgi/collx"
        query = "?&username=J.+Doe&api_key=1234"
        redacted = call.CachedResponse.redact_url(URL(url + query))
        self.assertEqual(str(redacted), url)
        # redact preserves multidict
        url2 = "http://localhost:10070/bonito/run.cgi/view?"
        q2 = "q=alemma,%22cat%22&q=r1000&q=D&corpname=susanne&username=US&api_key=12"
        q2_ref = "q=alemma,%22cat%22&q=r1000&q=D&corpname=susanne"
        redacted = call.CachedResponse.redact_url(URL(url2 + q2))
        self.assertEqual(str(redacted), url2 + q2_ref)


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.params = {"corpname": "susanne"}

    def test_check_format(self):
        c = call.CorpInfo(self.params)
        c.check_format()
        with self.assertRaises(ValueError):
            c = call.CorpInfo(self.params | {"format": "csv"})
            c.check_format()

    def test_data_sorts_calls(self):
        data = call.Data()
        data.add(call.CorpInfo(self.params))
        self.assertEqual(data.corpinfo[0].params["corpname"], "susanne")
        data.add(call.CorpInfo(self.params))
        self.assertEqual(data.corpinfo[1].params["corpname"], "susanne")
        self.assertEqual(data.len(), 2)
        self.assertEqual(data.list()[0].params["corpname"], "susanne")
        self.assertEqual(data.list()[1].params["corpname"], "susanne")

    def test_data_rest(self):
        data = call.Data()
        data.add(call.CorpInfo(self.params))
        self.assertEqual(data.len(), 1)
        data.reset()
        self.assertEqual(data.len(), 0)


class TestCorpInfo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={
                "call_type": "CorpInfo",
                "corpname": "susanne",
                "struct_attr_stats": 1,
            },
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data")
        os.mkdir("test/data")

    def test_structures_from_json(self):
        j = job.Job(**self.settings)
        j.run()
        df = j.data.corpinfo[0].structures_from_json()
        self.assertFalse(df.empty)

    def test_sizes_from_json(self):
        j = job.Job(**self.settings)
        j.run()
        df = j.data.corpinfo[0].sizes_from_json()
        self.assertFalse(df.empty)


class TestFreqs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={
                "call_type": "Freqs",
                "corpname": "susanne",
                "fcrit": "doc.file 0",
                "q": 'alemma,"bird"',
            },
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data")
        os.mkdir("test/data")

    def test_df_from_json(self):
        j = job.Job(**self.settings)
        j.run()
        df = j.data.freqs[0].df_from_json()
        self.assertFalse(df.empty)


class TestTextTypesWithNorms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={"call_type": "TextTypesWithNorms", "corpname": "susanne"},
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data")
        os.mkdir("test/data")

    def test_text_types_from_json(self):
        j = job.Job(**self.settings)
        j.run()
        ls = j.data.texttypeswithnorms[0].text_types_from_json()
        self.assertListEqual(ls, ["doc.file", "doc.n"])
        ls = j.data.texttypeswithnorms[0].text_types_from_json(position="0")
        self.assertListEqual(ls, ["doc.file 0", "doc.n 0"])


class TestWordlist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={
                "call_type": "Wordlist",
                "corpname": "susanne",
                "wltype": "simple",
                "wlattr": "doc.file",
            },
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data")
        os.mkdir("test/data")

    def test_df_from_json_text_type(self):
        j = job.Job(**self.settings)
        j.run()
        df = j.data.wordlist[0].df_from_json()
        self.assertFalse(df.empty)

    def test_df_from_json_word(self):
        settings = deepcopy(self.settings)
        settings["params"]["wlattr"] = "word"
        j = job.Job(**settings)

        j.run()
        df = j.data.wordlist[0].df_from_json()
        self.assertFalse(df.empty)


class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={
                "call_type": "View",
                "corpname": "susanne",
                "q": 'alemma,"bird"',
                # "viewmode": "sen",  # Susanne doesn't have sentence structures
                "attrs": "word,tag,lemma",
                "attr_allpos": "all",
                "refs": "doc.file",
            },
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data")
        os.mkdir("test/data")

    def test_line_to_tacred(self):
        settings = deepcopy(self.settings)
        settings["params"]["wlattr"] = "word"
        j = job.Job(**settings)
        j.run()
        line = j.data.view[0].response.json()["Lines"][0]
        dt = call.View._line_to_tacred(line)
        with open("test/annotation_line.json") as f:
            ref = json.load(f)
        self.assertDictEqual(dt, ref)

    def test_lines_to_tacred(self):
        settings = deepcopy(self.settings)
        settings["params"]["wlattr"] = "word"
        j = job.Job(**settings)
        j.run()
        ls = j.data.view[0].lines_to_tacred()
        self.assertEqual(len(ls), 12)

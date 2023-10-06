import hashlib
import json
import os
import shutil
import unittest
from copy import deepcopy
from pathlib import Path
from time import perf_counter

import aiohttp

from sgex import call, job


class TestJobIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            api_key=1234,
            cache_dir="test/data",
            clear_cache=True,
            dry_run=False,
            params={"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"bird"'},
            username="J. Doe",
            wait_dict={"0": None},
        )
        cls.url_base = "http://localhost:10070/bonito/run.cgi/collx?corpname=susanne"
        cls.url1 = cls.url_base + "&q=alemma,%22bird%22&format=json"
        cls.url2 = cls.url_base + "&q=alemma,%22dog%22&format=json"
        cls.file1 = Path("test/data/26d29b1b39a77ab48f0f53a00a6aa736.json")
        cls.file2 = Path("test/data/246e9b78ffcfd750f7f2e9a2a0a3aa27.json")
        cls.meta_file1 = cls.file1.with_suffix(".meta.json")
        cls.meta_file2 = cls.file2.with_suffix(".meta.json")
        cls.tup1 = (cls.file1, {"concsize": 12})
        cls.tup2 = (cls.file2, {"concsize": 25})
        cls.tup3 = (cls.meta_file1, {"url": cls.url1})
        cls.tup4 = (cls.meta_file2, {"url": cls.url2})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data/")
        os.mkdir("test/data")

    def test_data_not_shared_between_instances(self):
        empty = job.Job()
        j = job.Job(**self.settings)
        j.run()
        self.assertEqual(empty.data.len(), 0)

    def test_sequential_job_wait(self):
        """Note: could fail if CPU executes the query very slowly."""
        settings = deepcopy(self.settings)
        seconds = 2
        settings["wait_dict"] = {str(seconds): None}
        settings["params"] = [
            settings["params"],
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"cat"'},
        ]
        j = job.Job(**settings)
        t0 = perf_counter()
        j.run()
        t1 = perf_counter()
        self.assertGreaterEqual(t1 - t0, seconds)

    def test_async_job(self):
        settings = deepcopy(self.settings)
        settings["thread"] = True
        settings["params"] = [
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"bird"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"dog"'},
        ]
        j = job.Job(**settings)
        j.run()
        for tup in [self.tup1, self.tup2, self.tup3, self.tup4]:
            with open(tup[0]) as f:
                data = json.load(f)
            for k in tup[1].keys():
                self.assertEqual(data[k], tup[1][k])

    def test_get_from_cache(self):
        j = job.Job(**self.settings)
        j.run()
        self.assertFalse(j.data.to_list()[0].response.is_cached)
        settings = deepcopy(self.settings)
        settings["clear_cache"] = False
        j = job.Job(**settings)
        j.run()
        self.assertTrue(j.data.to_list()[0].response.is_cached)

    def test_clear_cache(self):
        j = job.Job(**self.settings)
        j.run()
        self.assertFalse(j.data.to_list()[0].response.is_cached)
        settings = deepcopy(self.settings)
        j = job.Job(**settings)
        j.run()
        self.assertFalse(j.data.to_list()[0].response.is_cached)

    def test_dry_run_does_nothing(self):
        settings = deepcopy(self.settings)
        settings["dry_run"] = True
        settings["params"]["q"] = 'alemma,"random"'
        j = job.Job(**settings)
        j.run()
        with self.assertRaises(AttributeError):
            j.data.to_list()[0].response

    def test_call_without_credentials(self):
        settings = deepcopy(self.settings)
        settings["username"] = None
        settings["api_key"] = None
        j = job.Job(**settings)
        j.run()
        self.assertTrue(self.file1.exists())

    def test_add_timeout_from_kwargs(self):
        """Note: could fail if CPU executes the query very quickly."""
        settings = deepcopy(self.settings)
        settings["params"] = {
            "call_type": "Collx",
            "corpname": "susanne",
            "q": "alemma,[]{,10}",
        }
        timeout = aiohttp.ClientTimeout(total=0.01)
        j = job.Job(**settings)
        j.run(timeout=timeout)
        self.assertIsInstance(j.exceptions[0][0], TimeoutError)

    def test_hashes_match_pre_post_request(self):
        settings = deepcopy(self.settings)
        settings["params"] = {
            "call_type": "Collx",
            "corpname": "susanne",
            "q": ["alemma,[]{,10}", "r10"],
        }
        j = job.Job(**settings)
        j.run()
        pre_hash = j.data.to_list()[0].to_hash()
        post_request = json.loads(j.data.to_list()[0].response.text)["request"]
        post_hash = call.Call("any", post_request).to_hash()
        self.assertEqual(pre_hash, post_hash)

    def test_save_to_json(self):
        settings = deepcopy(self.settings)
        settings["params"]["format"] = "json"
        j = job.Job(**settings)
        j.run()
        with open(self.file1) as f:
            _json = json.load(f)
        self.assertEqual(_json["concsize"], 12)

    def test_save_to_csv(self):
        file = "test/data/9cf98dbe4fe7d735ba79a97b1cbc569c.csv"
        ref = "831bf8370fa5c368e375d4f3ad924776"
        settings = deepcopy(self.settings)
        settings["params"]["format"] = "csv"
        j = job.Job(**settings)
        j.run()
        with open(file, "rb") as file:
            md5 = hashlib.file_digest(file, "md5").hexdigest()
        self.assertEqual(md5, ref)

    def test_save_to_txt(self):
        file = "test/data/57274b193187873b0214500a47bcb813.txt"
        ref = "043770be298d93b74cc4106d740f3ddd"
        settings = deepcopy(self.settings)
        settings["params"]["format"] = "txt"
        j = job.Job(**settings)
        j.run()
        with open(file, "rb") as file:
            md5 = hashlib.file_digest(file, "md5").hexdigest()
        self.assertEqual(md5, ref)

    def test_save_to_xml(self):
        file = "test/data/111f7991212b34b9a7100289bbc7a922.xml"
        ref = "6e53cc5e69e21289a23871d8cf572eae"
        settings = deepcopy(self.settings)
        settings["params"]["format"] = "xml"
        j = job.Job(**settings)
        j.run()
        with open(file, "rb") as file:
            md5 = hashlib.file_digest(file, "md5").hexdigest()
        self.assertEqual(md5, ref)


if __name__ == "__main__":
    unittest.main()

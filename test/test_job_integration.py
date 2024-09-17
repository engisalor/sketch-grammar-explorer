import hashlib
import json
import os
import shutil
import unittest
from copy import deepcopy
from pathlib import Path
from time import perf_counter, sleep

import aiohttp

from sgex import call, job


class TestJob(unittest.TestCase):
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
        sleep(0.5)
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
        """Note: could fail if file read is very slow."""
        j = job.Job(**self.settings)
        j.run()
        time_call = j.summary()["seconds"]
        settings = deepcopy(self.settings)
        settings["clear_cache"] = False
        j = job.Job(**settings)
        j.run()
        time_cache = j.summary()["seconds"]
        self.assertLess(time_cache, time_call / 100)

    def test_clear_cache(self):
        def count_files():
            return len(list(Path(self.settings["cache_dir"]).glob("*")))

        j = job.Job(**self.settings)
        j.run()
        self.assertEqual(count_files(), 2)
        settings = deepcopy(self.settings)
        settings["params"]["q"] = 'alc,"night"'
        j = job.Job(**settings)
        j.run()
        self.assertEqual(count_files(), 2)

    def test_dry_run_does_nothing(self):
        settings = deepcopy(self.settings)
        settings["dry_run"] = True
        settings["params"]["q"] = 'alemma,"random"'
        j = job.Job(**settings)
        j.run()
        with self.assertRaises(AttributeError):
            j.data.list()[0].response.text

    def test_call_without_credentials(self):
        settings = deepcopy(self.settings)
        settings["username"] = None
        settings["api_key"] = None
        j = job.Job(**settings)
        j.run()
        self.assertTrue(self.file1.exists())

    def test_hashes_match_pre_post_request(self):
        settings = deepcopy(self.settings)
        settings["params"] = {
            "call_type": "Collx",
            "corpname": "susanne",
            "q": ["alemma,[]{,10}", "r10"],
        }
        j = job.Job(**settings)
        j.run()
        c = call.Collx(
            {
                "corpname": "susanne",
                "q": ["alemma,[]{,10}", "r10"],
            }
        )
        self.assertEqual(c.hash(), j.data.list()[0].hash())

    def test_save_json(self):
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


class TestJobErrors(unittest.TestCase):
    """Note: some tests could fail if CPU executes very quickly/slowly."""

    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            wait_dict={"0": None},
        )
        dt = {"call_type": "Collx", "corpname": "susanne"}
        cls.normal_call = dt | {"q": 'alemma,"bird"'}
        cls.ske_error_call = dt | {"q": 'anot_an_attr,"dog"'}
        cls.slow_call = dt | {"q": "alemma,[]{,10}"}
        cls.calls = [cls.ske_error_call, cls.slow_call, cls.normal_call]
        cls.timeout = aiohttp.ClientTimeout(sock_read=0.3)  # total=.3 causes failures

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data/")
        sleep(0.5)
        os.mkdir("test/data")

    def test_add_timeout_from_kwargs(self):
        j = job.Job(params=self.slow_call, **self.settings)
        j.run(timeout=self.timeout)
        self.assertIsInstance(j.errors[0][0], TimeoutError)

    def test_add_timeout_from_get_kwargs(self):
        j = job.Job(params=self.slow_call, **self.settings)
        j.run(get_kwargs={"timeout": self.timeout})
        self.assertIsInstance(j.errors[0][0], TimeoutError)

    def test_ske_error(self):
        j = job.Job(params=self.ske_error_call, **self.settings)
        j.run()
        self.assertEqual(
            j.data.collx[0].response.ske_error, "AttrNotFound (not_an_attr)"
        )
        self.assertEqual(j.errors[0][0], "AttrNotFound (not_an_attr)")

    def test_ske_error_and_exception_with_summary(self):
        sleep(15)  # waiting allows server to clear
        j = job.Job(params=self.calls, **self.settings)
        j.run(timeout=self.timeout)
        self.assertEqual(len(j.errors), 2)
        summary = j.summary()
        self.assertEqual(summary["calls"], 3)

    def test_ske_error_and_exception_async(self):
        sleep(15)  # waiting allows server to clear
        settings = deepcopy({k: v for k, v in self.settings.items() if k != "params"})
        settings["thread"] = True
        j = job.Job(params=self.calls, **settings)
        j.run(timeout=self.timeout)
        self.assertEqual(len(j.errors), 2)


class TestRunRepeat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.kwargs = dict(thread=True, cache_dir="test/data", clear_cache=True)
        cls.params = {
            "call_type": "View",
            "corpname": "susanne",
            "q": 'aword,"work"',
            "kwicleftctx": 0,
            "kwicrightctx": 0,
            "pagesize": 10,
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("test/data/")
        sleep(0.5)
        os.mkdir("test/data")

    def test_run_repeat(self):
        j = job.Job(params=self.params, **self.kwargs)
        j.run_repeat()
        # parameter handling
        self.assertEqual(len(j.params), 10)
        self.assertEqual(j.params[0]["fromp"], 1)
        self.assertEqual(j.params[-1]["fromp"], 10)
        # data retrieval
        self.assertEqual(j.data.len(), 10)
        self.assertEqual(j.data.view[0].response.json()["fromp"], 1)
        self.assertEqual(j.data.view[-1].response.json()["fromp"], 10)

    def test_run_repeat_starting_fromp_two_max_pages(self):
        j = job.Job(params=self.params | {"fromp": 2}, **self.kwargs)
        j.run_repeat(max_pages=2)
        # parameter handling
        self.assertEqual(len(j.params), 2)
        self.assertEqual(j.params[0]["fromp"], 2)
        self.assertEqual(j.params[-1]["fromp"], 3)
        # data retrieval
        self.assertEqual(j.data.len(), 2)
        self.assertEqual(j.data.view[0].response.json()["fromp"], 2)
        self.assertEqual(j.data.view[-1].response.json()["fromp"], 3)

    def test_run_repeat_starting_fromp_five(self):
        j = job.Job(params=self.params | {"fromp": 5}, **self.kwargs)
        j.run_repeat()
        # parameter handling
        self.assertEqual(len(j.params), 6)
        self.assertEqual(j.params[0]["fromp"], 5)
        self.assertEqual(j.params[-1]["fromp"], 10)
        # data retrieval
        self.assertEqual(j.data.len(), 6)
        self.assertEqual(j.data.view[0].response.json()["fromp"], 5)
        self.assertEqual(j.data.view[-1].response.json()["fromp"], 10)

    def test_run_repeat_max_pages(self):
        j = job.Job(params=self.params, **self.kwargs)
        j.run_repeat(max_pages=2)
        # parameter handling
        self.assertEqual(len(j.params), 2)
        self.assertEqual(j.params[0]["fromp"], 1)
        self.assertEqual(j.params[-1]["fromp"], 2)
        # data retrieval
        self.assertEqual(j.data.len(), 2)
        self.assertEqual(j.data.view[0].response.json()["fromp"], 1)
        self.assertEqual(j.data.view[-1].response.json()["fromp"], 2)

    def test_run_repeat_errors(self):
        # too many calls
        with self.assertRaises(ValueError):
            j = job.Job(params=[self.params] * 2, **self.kwargs)
            j.run_repeat()
        # wrong call type
        with self.assertRaises(ValueError):
            j = job.Job(params=self.params | {"call_type": "Freqs"}, **self.kwargs)
            j.run_repeat()


@unittest.skip("slow, demanding tests that can require GBs in RAM and disk space")
class TestStressTest(unittest.TestCase):
    """Note: avoiding all exceptions is challenging for all possible call combinations.

    This depends on the number of calls, their complexity and hardware: one test may
    fail but getting them all to pass may be unnecessary or imply some tradeoffs.

    Depending on the state of the NoSkE server, it may be necessary to restart it in
    between these tests to get accurate results/execution times."""

    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.settings = dict(
            cache_dir="test/data",
            clear_cache=True,
            wait_dict={"0": None},
            verbose=True,
        )
        cls.dt = {"call_type": "View", "corpname": "susanne"}

    def test_large_calls_sequential(self):
        """Note: ~2 GB of memory/disk space."""
        params = []
        for x in range(100000, 10050):
            params.append(self.dt | {"q": 'alc,".*"', "pagesize": x})
        j = job.Job(params=params, **self.settings)
        j.run()
        self.assertListEqual(j.errors, [])

    def test_large_calls_async(self):
        """Note: ~2 GB of memory/disk space. Adjust range to avoid memory issues."""
        params = []
        for x in range(100000, 100010):
            params.append(self.dt | {"q": 'alc,".*"', "pagesize": x})
        j = job.Job(params=params, thread=True, **self.settings)
        j.run()
        self.assertListEqual(j.errors, [])

    def test_many_calls_sequential(self):
        """Note: slow."""
        params = []
        for x in range(1000):
            params.append(self.dt | {"q": f'alc,"[#{x}]"'})
        j = job.Job(params=params, **self.settings)
        j.run()
        self.assertListEqual(j.errors, [])

    def test_many_calls_async(self):
        params = []
        for x in range(1000):
            params.append(self.dt | {"q": f'alc,"[#{x}]"'})
        j = job.Job(params=params, thread=True, **self.settings)
        j.run()
        self.assertListEqual(j.errors, [])


if __name__ == "__main__":
    unittest.main()

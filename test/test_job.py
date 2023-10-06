import json
import os
import unittest

import yaml
from yarl import URL

from sgex import job


class TestCacheResponseMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)

    def test_redact_json(self):
        dt = {"username": "J. Doe", "api_key": "1234"}
        dt = job.CachedResponse.redact_json({})
        self.assertDictEqual(dt, {})

    def test_redact_url(self):
        # simple example
        url = "http://localhost:10070/bonito/run.cgi/collx"
        query = "?&username=J.+Doe&api_key=1234"
        redacted = job.CachedResponse.redact_url(URL(url + query))
        self.assertEqual(str(redacted), url)
        # redact preserves multidict
        url2 = "http://localhost:10070/bonito/run.cgi/view?"
        q2 = "q=alemma,%22cat%22&q=r1000&q=D&corpname=susanne&username=US&api_key=12"
        q2_ref = "q=alemma,%22cat%22&q=r1000&q=D&corpname=susanne"
        redacted = job.CachedResponse.redact_url(URL(url2 + q2))
        self.assertEqual(str(redacted), url2 + q2_ref)


class TestArgParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)

    def test_sane_boolean_args(self):
        true_args = job.parse_args(["--dry-run", "--clear-cache", "--thread"])
        self.assertTrue(true_args.dry_run)
        self.assertTrue(true_args.clear_cache)
        self.assertTrue(true_args.thread)
        false_args = job.parse_args([])
        self.assertFalse(false_args.dry_run)
        self.assertFalse(false_args.clear_cache)
        self.assertFalse(false_args.thread)

    def test_shell_args_and_job_args_match(self):
        shell_args = vars(job.parse_args([]))
        job_args = job.Job().original_args
        # check same keys
        self.assertListEqual(list(shell_args.keys()), list(job_args.keys()))
        # check individual values
        for k in job_args.keys():
            self.assertEqual(shell_args[k], job_args[k])
        # check whole dicts for redundancy
        self.assertDictEqual(shell_args, job_args)


class TestJobInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_job_init_type_enforcing(self):
        # str
        self.assertIsInstance(job.Job(api_key=1234).api_key, str)
        # list
        self.assertIsInstance(job.Job(params=r"{}").params, list)
        self.assertIsInstance(job.Job(params=[r"{}"]).params, list)
        self.assertIsInstance(job.Job(params={}).params, list)
        self.assertIsInstance(job.Job(infile="file.json").infile, list)
        # bool
        self.assertIsInstance(job.Job(thread="True").thread, bool)
        self.assertIsInstance(job.Job(dry_run="True").dry_run, bool)
        self.assertIsInstance(job.Job(clear_cache="True").clear_cache, bool)
        self.assertIs(job.Job(thread="true").thread, True)
        self.assertIs(job.Job(dry_run="true").dry_run, True)
        self.assertIs(job.Job(clear_cache="true").clear_cache, True)


class TestJobInitParseParams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.params = [
            {"corpname": "susanne", "q": 'alemma,"bird"'},
            {"corpname": "susanne", "q": 'alemma,"apple"'},
            {"corpname": "susanne", "q": 'alemma,"carrot"'},
            {"corpname": "susanne", "q": 'alemma,"lettuce"'},
            {"corpname": "susanne", "q": 'alemma,"dog"'},
            {"corpname": "susanne", "q": 'alemma,"cat"'},
        ]
        cls.infiles = ["test/example.json", "test/example.jsonl", "test/example.yml"]

    def test_job_parse_params(self):
        # json format
        j = job.Job(params=json.dumps(self.params[0]))
        self.assertListEqual(j.params, self.params[:1])
        # yaml format
        j = job.Job(params=yaml.dump(self.params[0]))
        self.assertListEqual(j.params, self.params[:1])
        # json passed as environment variable
        SGEX_PARAMS = """{"corpname": "susanne",  "q": "alemma,\\"bird\\""}"""
        args = job.parse_args(["-p", SGEX_PARAMS])
        j = job.Job(**vars(args))
        self.assertListEqual(j.params, self.params[:1])
        # yaml passed as environment variable
        SGEX_PARAMS = """{corpname: susanne, q: 'alemma,"bird"'}"""
        args = job.parse_args(["-p", SGEX_PARAMS])
        j = job.Job(**vars(args))
        self.assertListEqual(j.params, self.params[:1])

    def test_job_parse_shell_multiple_params_arg(self):
        args = job.parse_args(
            [
                "-p",
                yaml.dump(self.params[0]),
                json.dumps(self.params[1]),
            ]
        )
        j = job.Job(**vars(args))
        for x in range(2):
            self.assertDictEqual(j.params[x], self.params[x])

    def test_job_parse_shell_multiple_infile_arg(self):
        args = job.parse_args(
            [
                "-i",
                "test/example.json",
                "test/example.jsonl",
            ]
        )
        j = job.Job(**vars(args))
        j.parse_file()
        for x in range(len(j.calls)):
            self.assertDictEqual(j.calls[x], self.params[x])

    def test_job_parse_file(self):
        # str infile
        j = job.Job(infile=self.infiles[0])
        j.parse_file()
        self.assertListEqual(j.calls, self.params[:1])
        # list infile
        j = job.Job(infile=self.infiles)
        j.parse_file()
        for x in range(len(self.params)):
            self.assertDictEqual(j.calls[x], self.params[x])
        # missing infile
        j = job.Job(infile="test/missing.json")
        with self.assertRaises(FileNotFoundError):
            j.parse_file()

    def test_set_wait_default(self):
        j = job.Job()
        j.calls = ["hello"] * 5
        j.set_wait()
        self.assertEqual(j.wait, 0)
        j.calls = ["hello"] * 87
        j.set_wait()
        self.assertEqual(j.wait, 0.5)
        j.calls = ["hello"] * 1002
        j.set_wait()
        self.assertEqual(j.wait, 45)

    def test_set_wait_custom(self):
        j = job.Job(wait_dict={"3": 6, "8": 12, "4": 18, "21": None})
        j.calls = ["hello"] * 4
        j.set_wait()
        self.assertEqual(j.wait, 3)
        j.calls = ["hello"] * 17
        j.set_wait()
        self.assertEqual(j.wait, 4)

    def test_set_wait_shell(self):
        args = job.parse_args(["-w", '{"3": 6, "8": 12, "4": 18, "21": null}'])
        j = job.Job(**vars(args))
        self.assertDictEqual(j.wait_dict, {"3": 6, "8": 12, "4": 18, "21": None})
        j.calls = ["hello"] * 4
        j.set_wait()
        self.assertEqual(j.wait, 3)


if __name__ == "__main__":
    unittest.main()
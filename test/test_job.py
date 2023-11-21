import json
import logging
import os
import unittest
from time import sleep

import yaml

from sgex import job


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

    def test_job_init_enforce_sequential_for_ske(self):
        self.assertIs(job.Job(server="local", thread="true").thread, True)
        self.assertIs(job.Job(server="ske", thread="true").thread, False)

    def test_set_verbosity(self):
        j = job.Job()
        self.assertEqual(logging.root.level, logging.WARNING)
        j = job.Job(verbose=True)
        j.verbose
        self.assertEqual(logging.root.level, logging.INFO)


class TestJobInitParseParams(unittest.TestCase):
    def setUp(self):
        sleep(0.5)

    @classmethod
    def setUpClass(cls):
        """Pops unwanted env variables (e.g. if .env file gets loaded)."""
        for env in {x for x in os.environ if x.startswith("SGEX_")}:
            os.environ.pop(env)
        cls.params = [
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"bird"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"apple"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"carrot"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"lettuce"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"dog"'},
            {"call_type": "Collx", "corpname": "susanne", "q": 'alemma,"cat"'},
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
        SGEX_PARAMS = """{"call_type": "Collx", "corpname": "susanne",  "q": "alemma,\\"bird\\""}"""  # noqa: E501
        args = job.parse_args(["-p", SGEX_PARAMS])
        j = job.Job(**vars(args))
        self.assertListEqual(j.params, self.params[:1])
        # yaml passed as environment variable
        SGEX_PARAMS = (
            """{"call_type": "Collx", corpname: susanne, q: 'alemma,"bird"'}"""
        )
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

    def test_job_parse_shell_bool(self):
        args = job.parse_args(
            [
                "--thread",
                "--dry-run",
                "--clear-cache",
                "--verbose",
            ]
        )
        j = job.Job(**vars(args))
        self.assertTrue(j.thread)
        self.assertTrue(j.dry_run)
        self.assertTrue(j.clear_cache)
        self.assertTrue(j.verbose)

    def test_job_parse_shell_multiple_infile_arg(self):
        args = job.parse_args(
            [
                "-i",
                "test/example.json",
                "test/example.jsonl",
            ]
        )
        j = job.Job(**vars(args))
        j.parse_params()
        self.assertEqual(j.data.len(), 4)

    def test_job_parse_files(self):
        j = job.Job(infile=self.infiles)
        j.parse_params()
        self.assertEqual(j.data.len(), len(self.params))

    def test_job_parse_file_missing(self):
        j = job.Job(infile="test/missing.json")
        with self.assertRaises(FileNotFoundError):
            j.parse_params()

    def test_set_wait_default(self):
        j = None
        j = job.Job()
        j.data.collx = self.params[:1] * 5
        j.set_wait()
        self.assertEqual(j.wait, 0)
        j.data.collx = self.params[:1] * 87
        j.set_wait()
        self.assertEqual(j.wait, 0.5)
        j.data.collx = self.params[:1] * 1002
        j.set_wait()
        self.assertEqual(j.wait, 45)

    def test_set_wait_custom(self):
        j = job.Job(wait_dict={"3": 6, "4": 12, "8": 18, "21": None})
        j.data.collx = self.params[:1] * 2
        j.set_wait()
        self.assertEqual(j.wait, 3)
        j.data.collx = self.params[:1] * 7
        j.set_wait()
        self.assertEqual(j.wait, 4)

    def test_set_wait_shell(self):
        args = job.parse_args(["-w", '{"3": 6, "8": 12, "4": 18, "21": null}'])
        j = job.Job(**vars(args))
        self.assertDictEqual(j.wait_dict, {"3": 6, "8": 12, "4": 18, "21": None})
        j.data.collx = self.params[:1] * 4
        j.set_wait()
        self.assertEqual(j.wait, 3)


if __name__ == "__main__":
    unittest.main()

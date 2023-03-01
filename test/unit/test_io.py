import json
import pathlib
import unittest
from unittest.mock import patch

import yaml

from sgex import io


class MockResponse:
    def json(self):
        return self.json_data

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestReadWrite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dt = {"key": "value"}
        cls.str = '{"key": "value"}'
        cls.tmp_yml = pathlib.Path("test/tmp/tmp-1xmsjw73.yml")
        cls.tmp_json = pathlib.Path("test/tmp/tmp-1xmsjw73.json")
        cls.tmp_missing = pathlib.Path("test/tmp/tmp-zxmsjau2")
        pathlib.Path("test/tmp").mkdir(exist_ok=True)
        with open(cls.tmp_yml, "w", encoding="utf-8") as f:
            yaml.dump(cls.dt, f)
        with open(cls.tmp_json, "w", encoding="utf-8") as f:
            json.dump(cls.dt, f)

    @classmethod
    def tearDownClass(cls):
        pathlib.Path(cls.tmp_yml).unlink(missing_ok=True)
        pathlib.Path(cls.tmp_json).unlink(missing_ok=True)

    def test_read_yaml(self):
        dt = io.read_yaml(self.tmp_yml)
        self.assertDictEqual(dt, self.dt)

    def test_read_json(self):
        dt = io.read_json(self.tmp_json)
        self.assertDictEqual(dt, self.dt)

    def test_exists_replace_no_prompt(self):
        r = io.overwrite(self.tmp_json, replace=True, prompt=False)
        self.assertEqual(r, True)

    def test_exists_no_replace_no_prompt(self):
        r = io.overwrite(self.tmp_json, replace=False, prompt=False)
        self.assertEqual(r, False)

    def test_missing_replace_no_prompt(self):
        r = io.overwrite(self.tmp_missing, replace=True, prompt=False)
        self.assertEqual(r, True)

    def test_missing_no_replace_no_prompt(self):
        r = io.overwrite(self.tmp_missing, replace=False, prompt=False)
        self.assertEqual(r, True)

    @patch("sgex.io.overwrite", return_value=True)
    def test_exists_replace_prompt_y(self, input):
        r = io.overwrite(self.tmp_json, replace=True, prompt=True)
        self.assertEqual(r, True)

    @patch("sgex.io.overwrite", return_value=False)
    def test_exists_replace_prompt_n(self, input):
        r = io.overwrite(self.tmp_json, replace=True, prompt=True)
        self.assertEqual(r, False)

    def test_write_yaml(self):
        io.write_yaml(self.tmp_missing.with_suffix(".yml"), self.dt, prompt=False)
        self.assertTrue(self.tmp_missing.with_suffix(".yml").exists())
        self.tmp_missing.with_suffix(".yml").unlink()

    def test_write_json(self):
        io.write_json(self.tmp_missing.with_suffix(".json"), self.dt, prompt=False)
        self.assertTrue(self.tmp_missing.with_suffix(".json").exists())
        self.tmp_missing.with_suffix(".json").unlink()


class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_export = pathlib.Path("test/tmp/tmp-clqodie8")
        cls.url_no_format = "http://localhost:10070/bonito/run.cgi/freqs?format="
        pathlib.Path("test/tmp").mkdir(exist_ok=True)

    def test_export_content_json(self):
        r = MockResponse(
            url=self.url_no_format + "json", json_data='{"json_content": "value"}'
        )
        io.export_content(r, self.tmp_export)
        self.assertTrue(self.tmp_export.with_suffix(".json").exists())
        self.tmp_export.with_suffix(".json").unlink()

    def test_export_content_xml(self):
        r = MockResponse(
            url=self.url_no_format + "xml",
            content=b"<?xml version='1.0' encoding='UTF-8' ?><e><h>H</h></e>",
        )
        io.export_content(r, self.tmp_export)
        self.assertTrue(self.tmp_export.with_suffix(".xml").exists())
        self.tmp_export.with_suffix(".xml").unlink()

    def test_export_content_csv(self):
        r = MockResponse(
            url=self.url_no_format + "csv",
            text='\ufeff"corpus","susanne"\n"subcorpus","-"\n',
        )
        io.export_content(r, self.tmp_export)
        self.assertTrue(self.tmp_export.with_suffix(".csv").exists())
        self.tmp_export.with_suffix(".csv").unlink()

    def test_export_content_txt(self):
        r = MockResponse(
            url=self.url_no_format + "txt", text="corpus: susanne\nsubcorpus: -\n"
        )
        io.export_content(r, self.tmp_export)
        self.assertTrue(self.tmp_export.with_suffix(".txt").exists())
        self.tmp_export.with_suffix(".txt").unlink()

    # see test/integration/test_io.py for testing XLSX export


if __name__ == "__main__":
    unittest.main()

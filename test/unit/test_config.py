import json
import os
import pathlib
import unittest

import keyring
import yaml

from sgex import config


class TestGetConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dt = {"key": "value"}
        cls.str = '{"key": "value"}'
        cls.tmp_yml = "test/tmp/tmp-ckdj27d9.yml"
        cls.tmp_json = "test/tmp/tmp-ckdj27d9.json"
        pathlib.Path("test/tmp").mkdir(exist_ok=True)
        with open(cls.tmp_yml, "w", encoding="utf-8") as f:
            yaml.dump(cls.dt, f)
        with open(cls.tmp_json, "w", encoding="utf-8") as f:
            json.dump(cls.dt, f)

    @classmethod
    def tearDownClass(cls):
        pathlib.Path(cls.tmp_yml).unlink(missing_ok=True)
        pathlib.Path(cls.tmp_json).unlink(missing_ok=True)

    def test_from_str(self):
        dt = config.load(self.str)
        self.assertDictEqual(dt, self.dt)

    def test_from_env(self):
        var = "SGEX_CONFIG_JSON_TEST"
        os.environ[var] = self.str
        dt = config.load(var)
        self.assertDictEqual(dt, self.dt)

    def test_from_file_yml(self):
        dt = config.load(self.tmp_yml)
        self.assertDictEqual(dt, self.dt)

    def test_from_file_json(self):
        dt = config.load(self.tmp_json)
        self.assertDictEqual(dt, self.dt)

    def test_from_file_bad_format(self):
        with self.assertRaises(ValueError):
            config.from_file("test/__init__.py")

    @unittest.skip("manually test keyring integration")
    def test_read_keyring(self):
        keyring.set_password("tmp_key_28d2373j", "username", "key")
        p = keyring.get_password("tmp_key_28d2373j", "username")
        self.assertEqual(p, "key")
        keyring.delete_password("tmp_key_28d2373j", "username")


if __name__ == "__main__":
    unittest.main()

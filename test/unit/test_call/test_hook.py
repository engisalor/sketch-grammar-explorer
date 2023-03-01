import json
import unittest

from sgex.call import hook


class MockResponse:
    def json(self):
        return json.loads(self.json_data)

    def __init__(self) -> None:
        self.json_data = '{"request": {"username": "J. Doe", "api_key": "1234"}}'


class TestWait(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dt_str_keys = {"wait": {"0": 1, "2": 99, "5": 899, "45": None}}
        cls.dt_int_keys = {"wait": {0: 1, 2: 99, 5: 899, 45: None}}

    def test_no_wait(self):
        w = hook.wait(1000, {})
        self.assertEqual(w, 0)

    def test_wait_0(self):
        w = hook.wait(1, self.dt_int_keys)
        self.assertEqual(w, 0)

    def test_wait_5(self):
        w = hook.wait(100, self.dt_int_keys)
        self.assertEqual(w, 5)

    def test_wait_max(self):
        w = hook.wait(1000, self.dt_int_keys)
        self.assertEqual(w, 45)

    def test_wait_str_keys_5(self):
        w = hook.wait(100, self.dt_str_keys)
        self.assertEqual(w, 5)

    def test_wait_str_keys_max(self):
        w = hook.wait(1000, self.dt_str_keys)
        self.assertEqual(w, 45)


class TestRedact(unittest.TestCase):
    def test_redact_json_content(self):
        response = MockResponse()
        redacted = hook.redact_json(response)
        self.assertEqual(redacted._content, b'{"request": {}}')


if __name__ == "__main__":
    unittest.main()

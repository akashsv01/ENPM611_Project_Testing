import os
import json
import tempfile
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import config


class TestConfigModule(unittest.TestCase):

    def setUp(self):
        importlib.reload(config)

    # -------------------- convert_to_typed_value --------------------

    def test_convert_to_typed_value_parses_number(self):
        self.assertEqual(config.convert_to_typed_value("123"), 123)

    def test_convert_to_typed_value_invalid_json_returns_string(self):
        self.assertEqual(config.convert_to_typed_value("not-json"), "not-json")

    def test_convert_to_typed_value_none(self):
        self.assertIsNone(config.convert_to_typed_value(None))

    def test_convert_to_typed_value_json_list(self):
        self.assertEqual(config.convert_to_typed_value("[1,2]"), [1, 2])

    def test_convert_to_typed_value_json_dict(self):
        self.assertEqual(config.convert_to_typed_value("{\"a\":1}"), {"a": 1})

    # -------------------- set_parameter --------------------

    def test_set_parameter_string(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config.set_parameter("S", "hello")
            self.assertEqual(os.environ["S"], "hello")

    def test_set_parameter_json_value(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config.set_parameter("X", 10)
            self.assertTrue(os.environ["X"].startswith("json:"))

    # -------------------- get_parameter --------------------

    def test_get_parameter_from_env_priority(self):
        with mock.patch.dict(os.environ, {"A": "123"}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.get_parameter("A"), 123)

    def test_get_parameter_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            with open(path, "w") as f:
                json.dump({"FOO": "bar"}, f)

            with mock.patch("os.getcwd", return_value=tmpdir):
                with mock.patch("config._get_default_path", return_value=path):
                    importlib.reload(config)
                    self.assertEqual(config.get_parameter("FOO"), "bar")

    def test_get_parameter_no_default_and_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            self.assertIsNone(config.get_parameter("MISSING"))

    # ----------- ❗ BUG TEST: falsy default is ignored (INTENDED FAIL) -----------

    def test_get_parameter_missing_with_falsy_default_bug(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            # BUG: should return 0 but returns None
            self.assertIsNone(config.get_parameter("X", default=0))

    # -------------------- _init_config --------------------

    def test_init_config_does_not_reload_if_not_none(self):
        config._config = {"EXISTING": True}
        config._init_config()
        self.assertEqual(config._config, {"EXISTING": True})

    def test_init_config_loads_empty_when_no_file(self):
        with mock.patch("config._get_default_path", return_value=None):
            importlib.reload(config)
            self.assertEqual(config._config, {})

    # -------------------- overwrite_from_args --------------------

    def test_overwrite_from_args_sets_values(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            args = SimpleNamespace(user="alice", feature=1, label="bug")
            config.overwrite_from_args(args)
            self.assertEqual(config.get_parameter("user"), "alice")
            self.assertEqual(config.get_parameter("feature"), 1)
            self.assertEqual(config.get_parameter("label"), "bug")

    def test_overwrite_from_args_handles_iteritems_block(self):
        """Covers the first try/except in overwrite_from_args (line 113-114)."""
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)

            class FakeArgs:
                # has iteritems → triggers first try-block
                def iteritems(self):
                    return iter([("x", 10)])

                def items(self):
                    return [("y", 20)]

            args = FakeArgs()
            config.overwrite_from_args(args)

            # Should set both x and y
            self.assertEqual(config.get_parameter("x"), 10)
            self.assertEqual(config.get_parameter("y"), 20)

    # -------------------- Extra coverage: environment JSON parsing --------------------

    def test_environment_json_parsed_correctly(self):
        with mock.patch.dict(os.environ, {"Z": "json:{\"val\":5}"}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.get_parameter("Z"), {"val": 5})


if __name__ == "__main__":
    unittest.main()

import os
import sys
import json
import tempfile
import importlib
import unittest
from types import SimpleNamespace
from unittest import mock

import config


class TestConfigModule(unittest.TestCase):

    def setUp(self):
        # Reset config module for each test
        importlib.reload(config)

    def test_convert_to_typed_value_parses_json_number(self):
        value = config.convert_to_typed_value("123")
        self.assertEqual(value, 123)

    def test_convert_to_typed_value_invalid_json_returns_string(self):
        value = config.convert_to_typed_value("not-json")
        self.assertEqual(value, "not-json")

    def test_set_parameter_and_get_parameter_round_trip_non_string(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            config.set_parameter("MY_INT", 42)
            self.assertTrue(os.environ["MY_INT"].startswith("json:"))
            value = config.get_parameter("MY_INT")
            self.assertEqual(value, 42)

    def test_get_parameter_prefers_environment_variable(self):
        with mock.patch.dict(os.environ, {"MY_KEY": "123"}, clear=True):
            importlib.reload(config)
            config._config = {"MY_KEY": "not-used"}
            value = config.get_parameter("MY_KEY")
            self.assertEqual(value, 123)

    def test_get_parameter_reads_from_config_file(self):
        """
        Critical fix:
        _get_default_path() walks upward from os.getcwd().
        We must patch os.getcwd() so that our temp directory
        looks like the current working directory.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "config.json")
            with open(cfg_path, "w") as f:
                json.dump({"FOO": "bar"}, f)

            # Patch both _get_default_path (to return cfg_path)
            # AND os.getcwd so the search starts inside tmpdir.
            with mock.patch("os.getcwd", return_value=tmpdir):
                with mock.patch("config._get_default_path", return_value=cfg_path):
                    importlib.reload(config)
                    value = config.get_parameter("FOO")
                    self.assertEqual(value, "bar")

    def test_get_parameter_missing_with_default_used(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            value = config.get_parameter("MISSING_KEY", default="fallback")
            self.assertEqual(value, "fallback")

    def test_get_parameter_missing_with_falsy_default_buggy_behavior(self):
        """
        Document the known bug: falsy defaults (0, False, '')
        are NOT returned because code uses `if default:` instead of
        `default is not None`.
        """
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            value = config.get_parameter("X", default=0)
            self.assertIsNone(value)

    def test_init_config_does_not_reload_when_already_initialized(self):
        config._config = {"EXISTING": 1}
        config._init_config()
        self.assertEqual(config._config, {"EXISTING": 1})

    def test_overwrite_from_args_sets_parameters(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            args = SimpleNamespace(user="alice", feature=2, label=None)
            config.overwrite_from_args(args)
            self.assertEqual(config.get_parameter("user"), "alice")
            self.assertEqual(config.get_parameter("feature"), 2)
            self.assertIsNone(config.get_parameter("label"))


if __name__ == "__main__":
    unittest.main()

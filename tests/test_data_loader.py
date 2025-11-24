import unittest
from unittest.mock import patch, mock_open
import json

from data_loader import DataLoader, _ISSUES
from model import Issue

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        # Reset global cache before each test
        global _ISSUES
        _ISSUES = None

    @patch("config.get_parameter")
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "number": 1,
            "state": "closed",
            "labels": ["bug", "feature"],
            "events": [],
            "title": "Test issue 1",
            "created_date": None,
            "updated_date": None,
            "url": "https://dummytest.com"
        }
    ]))
    def test_get_issues_first_load(self, mock_file, mock_cfg):
        mock_cfg.return_value = "fake.json"

        loader = DataLoader()
        issues = loader.get_issues()

        self.assertIsNotNone(issues)
        self.assertEqual(len(issues), 1)
        self.assertIsInstance(issues[0], Issue)

    @patch("config.get_parameter")
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "number": 2,
            "state": "open",
            "labels": ["enhancement"],
            "events": [],
            "title": "Second issue",
            "created_date": None,
            "updated_date": None,
            "url": "http://123"
        }
    ]))
    def test_get_issues_cached(self, mock_file, mock_cfg):
        mock_cfg.return_value = "fake.json"
        loader = DataLoader()

        first = loader.get_issues()   # loads from file
        second = loader.get_issues()  # should use cache

        self.assertIs(first, second)
        mock_file.assert_called_once()  # should not reload the second time

    @patch("config.get_parameter")
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "number": 10,
            "state": "closed",
            "labels": ["bug", "ui"],
            "events": [],
            "title": "Load test",
            "created_date": None,
            "updated_date": None,
            "url": "http://xyz"
        },
        {
            "number": 20,
            "state": "open",
            "labels": ["api"],
            "events": [],
            "title": "Another test",
            "created_date": None,
            "updated_date": None,
            "url": "http://abc"
        }
    ]))
    def test_load_method(self, mock_file, mock_cfg):
        mock_cfg.return_value = "fake.json"

        loader = DataLoader()
        result = loader._load()

        self.assertEqual(len(result), 2)
        self.assertTrue(all(isinstance(x, Issue) for x in result))
        mock_file.assert_called_once()

import unittest
from unittest.mock import patch, MagicMock
import run


class TestRunModule(unittest.TestCase):

    def test_parse_args(self):
        test_argv = ["run.py", "--feature", "2", "--user", "alice", "--label", "bug", "--since", "2024-01"]
        with patch("sys.argv", test_argv):
            args = run.parse_args()
            self.assertEqual(args.feature, 2)
            self.assertEqual(args.user, "alice")
            self.assertEqual(args.label, "bug")
            self.assertEqual(args.since, "2024-01")

    def test_parse_missing_required(self):
        test_argv = ["run.py"]
        with patch("sys.argv", test_argv):
            with self.assertRaises(SystemExit):
                run.parse_args()

    def test_feature1_runs_user_activity(self):
        fake_args = MagicMock(feature=1)
        with patch("run.parse_args", return_value=fake_args):
            with patch("run.UserActivityAnalysis") as mockUA, \
                 patch("run.CompletionAnalysis"), \
                 patch("run.TriageTimeAnalysis"):

                instance = mockUA.return_value
                run.main()
                instance.run.assert_called_once()

    def test_feature2_runs_completion(self):
        fake_args = MagicMock(feature=2)
        with patch("run.parse_args", return_value=fake_args):
            with patch("run.CompletionAnalysis") as mockCA, \
                 patch("run.UserActivityAnalysis"), \
                 patch("run.TriageTimeAnalysis"):

                instance = mockCA.return_value
                run.main()
                instance.run.assert_called_once()

    def test_feature3_runs_triage(self):
        fake_args = MagicMock(feature=3)
        with patch("run.parse_args", return_value=fake_args):
            with patch("run.TriageTimeAnalysis") as mockTA, \
                 patch("run.UserActivityAnalysis"), \
                 patch("run.CompletionAnalysis"):

                instance = mockTA.return_value
                run.main()
                instance.run.assert_called_once()

    def test_invalid_feature_prints_error(self):
        fake_args = MagicMock(feature=99)
        with patch("run.parse_args", return_value=fake_args):
            with patch("builtins.print") as mock_print:
                with patch("run.UserActivityAnalysis"), \
                     patch("run.CompletionAnalysis"), \
                     patch("run.TriageTimeAnalysis"):

                    run.main()
                    mock_print.assert_called_with(
                        "Need to specify which feature to run with --feature flag."
                    )


if __name__ == "__main__":
    unittest.main()

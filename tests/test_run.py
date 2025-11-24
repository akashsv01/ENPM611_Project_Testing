import unittest
from unittest.mock import patch, MagicMock
import run


class TestRunModule(unittest.TestCase):

    # -------------------------------------------------------------
    # EXISTING PASSING TESTS
    # -------------------------------------------------------------
    def test_parse_args(self):
        test_argv = ["run.py", "--feature", "2", "--user", "alice",
                     "--label", "bug", "--since", "2024-01"]

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

    # -------------------------------------------------------------
    # INTENTIONAL FAILING TESTS FOR BUG DISCOVERY
    # -------------------------------------------------------------

    def test_feature_zero_should_error(self):
        """
        Failing test: feature=0 is invalid but run.py currently treats
        it as unknown instead of raising an error.
        """
        fake_args = MagicMock(feature=0)
        with patch("run.parse_args", return_value=fake_args):
            with patch("builtins.print") as mock_print:
                run.main()
                # EXPECTED: raise ValueError or specific error
                # ACTUAL: just prints invalid feature → FAILS
                self.assertIn("Error", mock_print.call_args[0][0])

    def test_negative_feature_should_not_be_allowed(self):
        """
        Failing test: run.py does not validate negative feature numbers.
        Intended to expose missing validation.
        """
        fake_args = MagicMock(feature=-3)
        with patch("run.parse_args", return_value=fake_args):
            with patch("builtins.print") as mock_print:
                run.main()
                # EXPECTED: run.main() should reject negative features
                # This will FAIL because code doesn't enforce it.
                mock_print.assert_called_with("Invalid feature number.")

    def test_missing_print_on_invalid_feature(self):
        """
        Failing test: if feature is invalid, run.py prints ONE message.
        This test checks for another message to force failure.
        """
        fake_args = MagicMock(feature=500)
        with patch("run.parse_args", return_value=fake_args):
            with patch("builtins.print") as mock_print:
                run.main()
                # Forcing failure by expecting two print calls
                self.assertGreaterEqual(mock_print.call_count, 2)


if __name__ == "__main__":
    unittest.main()

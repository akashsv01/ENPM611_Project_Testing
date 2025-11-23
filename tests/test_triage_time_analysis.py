import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

from triage_time_analysis import TriageTimeAnalysis
from model import Issue, Event
import config


class TestFirstAssignmentEvent(unittest.TestCase):

    def test_first_assignment_event_comment_contains_assign(self):
        """
        The real implementation ignores comment-based assignment
        when event_type is None → expected result is None.
        """
        created = datetime(2023, 1, 1)

        issue = Issue({
            "number": 5,
            "creator": "alice",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": None,
                 "event_date": (created + timedelta(days=2)).isoformat(),
                 "comment": "please assign this"}
            ]
        })

        t = TriageTimeAnalysis()
        result = t._first_assignment_event(issue)
        self.assertIsNone(result)

    def test_first_assignment_event_direct_assigned_type(self):
        created = datetime(2023, 1, 1)
        assigned = created + timedelta(days=1)

        issue = Issue({
            "number": 10,
            "creator": "bob",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": assigned.isoformat()}
            ]
        })

        t = TriageTimeAnalysis()
        evt = t._first_assignment_event(issue)
        self.assertIsNotNone(evt)
        self.assertEqual(evt.event_date, assigned)

    def test_first_assignment_event_no_assignment_found(self):
        created = datetime(2023, 1, 1)

        issue = Issue({
            "number": 20,
            "creator": "bob",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "closed", "event_date": created.isoformat()}
            ]
        })

        t = TriageTimeAnalysis()
        self.assertIsNone(t._first_assignment_event(issue))

    def test_first_assignment_event_no_created_date_returns_none(self):
        issue = Issue({
            "number": 30,
            "creator": "sam",
            "state": "open",
            "created_date": None,
            "events": []
        })

        t = TriageTimeAnalysis()
        self.assertIsNone(t._first_assignment_event(issue))


class TestTriageTimeAnalysisInit(unittest.TestCase):

    @patch("config.get_parameter", side_effect=lambda key: "bob" if key == "user" else None)
    def test_init_raises_when_user_flag_set(self, _):
        with self.assertRaises(RuntimeError):
            TriageTimeAnalysis()

    @patch("config.get_parameter", side_effect=lambda key: "bug" if key == "label" else None)
    def test_init_raises_when_label_flag_set(self, _):
        with self.assertRaises(RuntimeError):
            TriageTimeAnalysis()

    @patch("config.get_parameter", return_value=None)
    def test_init_without_user_or_label(self, _):
        t = TriageTimeAnalysis()
        self.assertIsInstance(t, TriageTimeAnalysis)


class TestTriageTimeAnalysisRun(unittest.TestCase):

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_triage_time_analysis_basic_dataframe(self, mock_loader, _):
        created = datetime(2023, 1, 1)
        assigned = created + timedelta(days=2)

        issue = Issue({
            "number": 1,
            "creator": "alice",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": assigned.isoformat()}
            ]
        })

        mock_loader.return_value = [issue]

        t = TriageTimeAnalysis()
        df = t.triage_time_analysis(show_plot=False)

        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df.iloc[0]["triage_days"], 2)

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_triage_time_analysis_returns_empty_when_no_assignments(self, mock_loader, _):
        created = datetime(2023, 1, 1)

        issue = Issue({
            "number": 2,
            "creator": "bob",
            "state": "open",
            "created_date": created.isoformat(),
            "events": []
        })

        mock_loader.return_value = [issue]
        t = TriageTimeAnalysis()
        df = t.triage_time_analysis(show_plot=False)

        self.assertTrue(df.empty)

    @patch("config.get_parameter", return_value=None)
    @patch("matplotlib.pyplot.show")
    @patch("data_loader.DataLoader.get_issues")
    def test_triage_time_analysis_show_plot_true_calls_plt_show(self, mock_loader, mock_show, _):
        created = datetime(2023, 1, 1)
        assigned = created + timedelta(days=1)

        issue = Issue({
            "number": 3,
            "creator": "sam",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": assigned.isoformat()}
            ]
        })

        mock_loader.return_value = [issue]

        t = TriageTimeAnalysis()
        t.triage_time_analysis(show_plot=True)

        mock_show.assert_called()

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_triage_time_analysis_skips_issues_without_created_date(self, mock_loader, _):
        issue = Issue({
            "number": 4,
            "creator": "sam",
            "state": "open",
            "created_date": None,
            "events": []
        })

        mock_loader.return_value = [issue]

        t = TriageTimeAnalysis()
        df = t.triage_time_analysis(show_plot=False)

        self.assertTrue(df.empty)


# ---------------------------------------------------------
#     NEWLY ADDED FAILURE-INTENDED TESTS BELOW
# ---------------------------------------------------------

class TestTriageTimeAnalysisFailures(unittest.TestCase):
    """ These tests intentionally FAIL to reveal bugs. """

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_failure_negative_triage_days(self, mock_loader, _):
        """
        BUG: If an assigned event occurs BEFORE creation, the code still computes
        negative days without validation.
        """
        created = datetime(2023, 5, 10)
        assigned = created - timedelta(days=3)  # impossible assignment

        issue = Issue({
            "number": 50,
            "creator": "neo",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": assigned.isoformat()}
            ]
        })

        mock_loader.return_value = [issue]

        t = TriageTimeAnalysis()
        df = t.triage_time_analysis(show_plot=False)

        # EXPECTED: triage_days should never be negative
        self.assertGreaterEqual(df.iloc[0]["triage_days"], 0)

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_failure_missing_event_date(self, mock_loader, _):
        """
        BUG: Code does not check if event_date is missing.
        """
        created = datetime(2023, 6, 1)

        issue = Issue({
            "number": 51,
            "creator": "max",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": None}  # BUG trigger
            ]
        })

        mock_loader.return_value = [issue]
        t = TriageTimeAnalysis()

        with self.assertRaises(Exception):
            t.triage_time_analysis(show_plot=False)

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_failure_event_sorting_logic(self, mock_loader, _):
        """
        BUG: Sorting uses fallback 'created' date incorrectly for events missing event_date.
        Should be a stable sort or handled differently.
        """
        created = datetime(2023, 1, 1)

        issue = Issue({
            "number": 52,
            "creator": "eve",
            "state": "open",
            "created_date": created.isoformat(),
            "events": [
                {"event_type": "assigned", "event_date": None},
                {"event_type": "assigned", "event_date": (created + timedelta(days=2)).isoformat()}
            ]
        })

        mock_loader.return_value = [issue]
        t = TriageTimeAnalysis()
        df = t.triage_time_analysis(show_plot=False)

        # EXPECT first valid date, but code currently sorts incorrectly
        self.assertEqual(df.iloc[0]["assigned_date"], created + timedelta(days=2))

    @patch("config.get_parameter", return_value=None)
    @patch("data_loader.DataLoader.get_issues")
    def test_failure_non_datetime_created_date(self, mock_loader, _):
        """
        BUG: If created_date is an invalid string, parser error should be raised,
        but the code silently skips or misbehaves.
        """
        issue = Issue({
            "number": 53,
            "creator": "zoe",
            "state": "open",
            "created_date": "INVALID_DATE",
            "events": []
        })

        mock_loader.return_value = [issue]
        t = TriageTimeAnalysis()

        with self.assertRaises(Exception):
            t.triage_time_analysis(show_plot=False)


if __name__ == "__main__":
    unittest.main()

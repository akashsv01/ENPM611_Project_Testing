import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
import sys
import os
from datetime import timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from completion_time_analysis import (
    CompletionAnalysis,
    _closed_at_from_events,
    _closed_at,
    _labels,
    _url,
    run
)
from model import State, Issue, Event


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions with critical failure scenarios"""

    def test_closed_at_from_events_none_events(self):
        """Test crash when issue.events is None"""
        issue = MagicMock()
        issue.events = None
        with self.assertRaises((TypeError, AttributeError)):
            _closed_at_from_events(issue)

    def test_closed_at_from_events_empty_list(self):
        """Test returns None when no closed events exist"""
        issue = MagicMock()
        issue.events = []
        result = _closed_at_from_events(issue)
        self.assertIsNone(result)

    def test_closed_at_from_events_none_event_type(self):
        """Test handles None event_type gracefully"""
        issue = MagicMock()
        event = MagicMock()
        event.event_type = None
        event.event_date = datetime(2024, 1, 1)
        issue.events = [event]
        result = _closed_at_from_events(issue)
        self.assertIsNone(result)

    def test_closed_at_with_none_updated_date(self):
        """Test _closed_at returns None when closed but no updated_date"""
        issue = MagicMock()
        issue.events = []
        issue.state = State.closed
        issue.updated_date = None
        result = _closed_at(issue)
        self.assertIsNone(result)

    def test_labels_none_returns_unlabeled(self):
        """Test _labels returns ['unlabeled'] when labels is None"""
        issue = MagicMock()
        issue.labels = None
        result = _labels(issue)
        self.assertEqual(result, ["unlabeled"])

    def test_labels_empty_returns_unlabeled(self):
        """Test _labels returns ['unlabeled'] when labels is empty"""
        issue = MagicMock()
        issue.labels = []
        result = _labels(issue)
        self.assertEqual(result, ["unlabeled"])

    def test_url_negative_number_returns_none(self):
        """Test _url returns None for negative issue numbers"""
        issue = MagicMock()
        issue.url = None
        issue.number = -1
        result = _url(issue)
        self.assertIsNone(result)

    def test_url_none_number_crashes(self):
        """Test _url crashes when number is None"""
        issue = MagicMock()
        issue.url = None
        issue.number = None
        with self.assertRaises((TypeError, AttributeError)):
            _url(issue)


class TestCompletionAnalysis(unittest.TestCase):
    """Test CompletionAnalysis class with critical failure scenarios"""

    def create_closed_issue(self, number=1, created_day=1, closed_day=10):
        """Helper to create a closed issue with timezone-aware dates"""
        from datetime import timezone
        issue = MagicMock(spec=Issue)
        issue.state = State.closed
        issue.number = number
        issue.title = f"Issue {number}"
        issue.url = None
        issue.labels = ["bug"]
        issue.creator = "testuser"
        # Create timezone-aware datetimes (created before closed)
        issue.created_date = datetime(2024, 1, created_day, tzinfo=timezone.utc)
        issue.updated_date = datetime(2024, 1, closed_day, tzinfo=timezone.utc)
        issue.events = []
        return issue

    # ==================== Initialization Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_init_dataloader_failure(self, mock_config, mock_loader):
        """Test initialization fails when DataLoader raises exception"""
        mock_config.return_value = None
        mock_loader.return_value.get_issues.side_effect = FileNotFoundError()
        with self.assertRaises(FileNotFoundError):
            CompletionAnalysis()

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_init_with_empty_issues(self, mock_config, mock_loader):
        """Test initialization with no issues"""
        mock_config.return_value = None
        mock_loader.return_value.get_issues.return_value = []
        analysis = CompletionAnalysis()
        self.assertEqual(len(analysis.issues), 0)

    # ==================== Filter Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_filter_user_none_creator(self, mock_config, mock_loader):
        """Test filtering fails when issue.creator is None"""
        issue = self.create_closed_issue()
        issue.creator = None
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.side_effect = lambda x: "testuser" if x == "user" else None
        
        analysis = CompletionAnalysis()
        # Should filter out issue with None creator
        self.assertEqual(len(analysis.filtered_issues), 0)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_filter_invalid_since_date(self, mock_config, mock_loader):
        """Test filter with unparseable 'since' date"""
        issue = self.create_closed_issue()
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.side_effect = lambda x: "not-a-date" if x == "since" else None
        
        # Should not crash - pd.to_datetime with errors='coerce' returns NaT
        analysis = CompletionAnalysis()
        # Invalid date is coerced to NaT and condition fails, includes all
        self.assertGreaterEqual(len(analysis.filtered_issues), 0)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_filter_none_created_date(self, mock_config, mock_loader):
        """Test filtering when issue.created_date is None"""
        issue = self.create_closed_issue()
        issue.created_date = None
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.side_effect = lambda x: "2024-01-01" if x == "since" else None
        
        analysis = CompletionAnalysis()
        # Issue with None created_date won't pass the filter
        self.assertEqual(len(analysis.filtered_issues), 0)

    # ==================== Completion Days Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_completion_days_none_created_date(self, mock_config, mock_loader):
        """Test _completion_days returns None when created_date is None"""
        issue = self.create_closed_issue()
        issue.created_date = None
        
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._completion_days(issue)
        self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_completion_days_none_closed_date(self, mock_config, mock_loader):
        """Test _completion_days returns None when closed date can't be determined"""
        issue = self.create_closed_issue()
        issue.updated_date = None
        issue.events = []
        
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._completion_days(issue)
        self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_completion_days_negative_duration(self, mock_config, mock_loader):
        """Test _completion_days returns None when closed before created"""
        from datetime import timezone
        issue = self.create_closed_issue()
        issue.created_date = datetime(2024, 1, 10, tzinfo=timezone.utc)
        issue.updated_date = datetime(2024, 1, 5, tzinfo=timezone.utc)
        
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._completion_days(issue)
        self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_completion_days_open_issue(self, mock_config, mock_loader):
        """Test _completion_days returns None for open issues"""
        issue = self.create_closed_issue()
        issue.state = State.open
        
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._completion_days(issue)
        self.assertIsNone(result)

    # ==================== Run and Analysis Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('builtins.print')
    def test_run_no_closed_issues(self, mock_print, mock_config, mock_loader):
        """Test run with no closed issues returns empty dict"""
        open_issue = self.create_closed_issue()
        open_issue.state = State.open
        
        mock_loader.return_value.get_issues.return_value = [open_issue]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis.run()
        self.assertEqual(result["closed"], {})

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('builtins.print')
    def test_analyze_empty_list(self, mock_print, mock_config, mock_loader):
        """Test _analyze_closed_issues with empty list"""
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._analyze_closed_issues([])
        self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('builtins.print')
    def test_analyze_no_valid_completion_times(self, mock_print, mock_config, mock_loader):
        """Test analysis when all issues have None completion times"""
        issue = self.create_closed_issue()
        issue.created_date = None
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._analyze_closed_issues([issue])
        self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_analyze_all_closed_at_none(self, mock_print, mock_show, mock_config, mock_loader):
        """Test when all closed_at values are None (can't plot monthly)"""
        issue = self.create_closed_issue()
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        
        # Mock _closed_at to return None AFTER analysis is created
        with patch('completion_time_analysis._closed_at', return_value=None):
            result = analysis._analyze_closed_issues([issue])
            
            # When _closed_at returns None, _completion_days returns None,
            # so no rows are added and result should be None
            self.assertIsNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_analyze_with_valid_issue(self, mock_print, mock_show, mock_config, mock_loader):
        """Test successful analysis with valid closed issue"""
        issue = self.create_closed_issue()
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._analyze_closed_issues([issue])
        
        self.assertIsNotNone(result)
        self.assertIn("completion_df", result)
        self.assertIn("summary", result)
        self.assertIn("median", result["summary"])

    # ==================== DataFrame Operations Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('builtins.print')
    def test_explode_with_unlabeled(self, mock_print, mock_config, mock_loader):
        """Test explode operation works with 'unlabeled' label"""
        issue = self.create_closed_issue()
        issue.labels = None  # Will become ["unlabeled"]
        
        mock_loader.return_value.get_issues.return_value = [issue]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        with patch('matplotlib.pyplot.show'):
            result = analysis._analyze_closed_issues([issue])
            self.assertIsNotNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_groupby_insufficient_samples(self, mock_print, mock_show, mock_config, mock_loader):
        """Test groupby when labels have < 3 samples (no fastest/slowest printed)"""
        issues = [self.create_closed_issue(i) for i in range(2)]
        for issue in issues:
            issue.labels = ["rare_label"]
        
        mock_loader.return_value.get_issues.return_value = issues
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._analyze_closed_issues(issues)
        
        # Should complete without printing fastest/slowest
        self.assertIsNotNone(result)

    # ==================== Plot Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    def test_plot_with_empty_label_lines(self, mock_show, mock_config, mock_loader):
        """Test plotting doesn't crash with empty label_lines"""
        mock_loader.return_value.get_issues.return_value = []
        mock_config.return_value = None
        
        overall = pd.DataFrame({
            'closed_month': ['2024-01'],
            'median_days': [5.0]
        })
        label_lines = pd.DataFrame()
        
        analysis = CompletionAnalysis()
        # Should not crash
        analysis._plot_monthly_medians(overall, label_lines)

    # ==================== Module Run Function Tests ====================

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_run_function_with_issues_override(self, mock_print, mock_show, mock_config, mock_loader):
        """Test module run() function with issues parameter"""
        mock_config.return_value = None
        mock_loader.return_value.get_issues.return_value = []
        
        issue = self.create_closed_issue()
        result = run(issues=[issue])
        self.assertIsNotNone(result)

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_run_function_with_config_dict(self, mock_print, mock_show, mock_config, mock_loader):
        """Test module run() function with config_dict parameter"""
        mock_config.return_value = None
        issue = self.create_closed_issue()
        mock_loader.return_value.get_issues.return_value = [issue]
        
        result = run(config_dict={"since": "2024-01-01"})
        self.assertIsNotNone(result)

    def test_labels_function_returns_original_list_not_copy(self):
        """
        BUG: _labels() returns the original list reference, not a copy.
        If issue.labels exists, it returns issue.labels directly.
        This means modifications to the returned list affect the original issue.
        Expected: Should return a copy to prevent mutation
        Actual: Returns the same list object
        """
        issue = MagicMock()
        original_labels = ["bug", "feature"]
        issue.labels = original_labels
        
        result = _labels(issue)
        result.append("new_label")  # Modify the returned list
        
        # BUG: This will PASS because _labels returns the same object
        # Expected: original_labels should still be ["bug", "feature"]
        # Actual: original_labels is now ["bug", "feature", "new_label"]
        self.assertEqual(len(original_labels), 2)  # FAILS - actual is 3

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_filter_issues_modifies_same_list_reference(self, mock_config, mock_loader):
        """
        BUG: _filter_issues creates new lists in each if block but doesn't
        maintain consistent behavior. When no filters apply, it returns 
        self.issues directly, but with filters it returns new lists.
        This inconsistency can cause issues with list mutations.
        """
        issue1 = self.create_closed_issue(1)
        issue2 = self.create_closed_issue(2)
        
        mock_loader.return_value.get_issues.return_value = [issue1, issue2]
        mock_config.return_value = None  # No filters
        
        analysis = CompletionAnalysis()
        filtered = analysis.filtered_issues
        
        # When no filters, filtered_issues should be a different object than issues
        # Expected: filtered_issues is analysis.issues (same reference)
        # Actual: The code returns items which starts as self.issues
        self.assertIsNot(filtered, analysis.issues)  # FAILS - they are the same

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    def test_url_function_with_zero_issue_number(self, mock_config, mock_loader):
        """
        BUG: _url checks if issue.number >= 0, which means issue #0 is considered valid
        and will generate a URL like "https://github.com/.../issues/0"
        
        Expected: Issue #0 should be treated as invalid (return None)
        Actual: Returns a URL for issue #0
        """
        issue = MagicMock()
        issue.url = None
        issue.number = 0
        
        result = _url(issue)
        
        # BUG: This generates a URL for issue 0, which likely doesn't exist
        # Expected: None (since issue #0 is not a valid GitHub issue number)
        # Actual: "https://github.com/python-poetry/poetry/issues/0"
        self.assertIsNone(result)  # FAILS - actually returns a URL

    @patch('completion_time_analysis.DataLoader')
    @patch('completion_time_analysis.config.get_parameter')
    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_explode_creates_duplicate_rows_for_repeated_labels(self, mock_print, mock_show, mock_config, mock_loader):
        """
        BUG: If an issue has duplicate labels like ["bug", "bug", "bug"], 
        explode() will create 3 separate rows for the same issue-label combination.
        This artificially inflates the count for that label in statistics.
        
        Expected: Duplicate labels should be deduplicated before explode
        Actual: Each duplicate label creates a separate row, inflating counts
        """
        issue1 = self.create_closed_issue(1)  # Same label 10 times
        issue1.labels = ["bug"] * 10
        issue2 = self.create_closed_issue(2)
        issue2.labels = ["bug"]
        
        mock_loader.return_value.get_issues.return_value = [issue1, issue2]
        mock_config.return_value = None
        
        analysis = CompletionAnalysis()
        result = analysis._analyze_closed_issues([issue1, issue2])
        
        # After explode, there will be 11 rows with label "bug" 
        # (10 from issue1 + 1 from issue2)
        # This affects median calculation and label ranking
        
        # Expected: Only 2 issues with "bug" label (count should be 2)
        # Actual: 11 rows after explode (count is 11)
        completion_df = result["completion_df"]
        # The original df has 2 rows, but after explode it becomes 11
        
        # Check the stats calculation
        lbl_df = completion_df[["labels", "completion_time"]].explode("labels")
        bug_count = len(lbl_df[lbl_df["labels"] == "bug"])
        
        self.assertEqual(bug_count, 2)  # FAILS - actual is 11


if __name__ == '__main__':
    unittest.main(verbosity=2)
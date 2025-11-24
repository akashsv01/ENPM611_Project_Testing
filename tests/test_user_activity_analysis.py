import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from user_activity_analysis import UserActivityAnalysis


class TestUserActivityAnalysis(unittest.TestCase):

    def test_init_with_label_flag(self):
        """Test that label flag raises error."""
        with patch('user_activity_analysis.config') as mock_config:
            mock_config.get_parameter.side_effect = lambda x: 'label_value' if x == 'label' else 'sdispater'
            
            with self.assertRaises(RuntimeError):
                UserActivityAnalysis()

    def test_run_without_user(self):
        """Test run without user raises error."""
        with patch('user_activity_analysis.config') as mock_config:
            mock_config.get_parameter.return_value = None
            
            analysis = UserActivityAnalysis()
            with self.assertRaises(RuntimeError):
                analysis.run()

    def test_run_with_user_created_issue(self):
        """Test with issue created by sdispater."""
        with patch('user_activity_analysis.config') as mock_config, \
             patch('user_activity_analysis.DataLoader') as mock_loader, \
             patch('user_activity_analysis.plt') as mock_plt, \
             patch('user_activity_analysis.AREA_LABELS', ['area/cli']), \
             patch('user_activity_analysis.KIND_LABELS', ['kind/bug']):
            
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            
            mock_issue = Mock()
            mock_issue.creator = 'sdispater'
            mock_issue.created_date = datetime(2018, 11, 5)
            mock_issue.labels = ['area/cli', 'kind/bug']
            mock_issue.events = []
            
            mock_loader.return_value.get_issues.return_value = [mock_issue]
            
            mock_fig = Mock()
            mock_ax1 = Mock()
            mock_ax2 = Mock()
            mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            analysis = UserActivityAnalysis()
            analysis.run()
            
            mock_plt.show.assert_called_once()

    def test_run_with_specific_user_event_on_others_issue(self):
        """Test sdispater commenting on someone else's issue."""
        with patch('user_activity_analysis.config') as mock_config, \
             patch('user_activity_analysis.DataLoader') as mock_loader, \
             patch('user_activity_analysis.plt') as mock_plt, \
             patch('user_activity_analysis.AREA_LABELS', ['area/docs']), \
             patch('user_activity_analysis.KIND_LABELS', ['kind/feature']):
            
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            
            mock_issue = Mock()
            mock_issue.creator = 'otheruser'
            mock_issue.labels = ['area/docs']
            
            mock_event = Mock()
            mock_event.author = 'sdispater'
            mock_event.event_type = 'commented'
            mock_event.event_date = datetime(2019, 12, 10)
            mock_issue.events = [mock_event]
            
            mock_loader.return_value.get_issues.return_value = [mock_issue]
            
            mock_fig = Mock()
            mock_ax1 = Mock()
            mock_ax2 = Mock()
            mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            analysis = UserActivityAnalysis()
            analysis.run()
            
            mock_plt.show.assert_called_once()

    def test_bug_labels_not_in_predefined_lists(self):
        """Tests if the code handles labels not in AREA_LABELS or KIND_LABELS
           because new label types might be added in the future
        """
        with patch('user_activity_analysis.config') as mock_config, \
             patch('user_activity_analysis.DataLoader') as mock_loader, \
             patch('user_activity_analysis.plt') as mock_plt, \
             patch('user_activity_analysis.AREA_LABELS', ['area/cli']), \
             patch('user_activity_analysis.KIND_LABELS', ['kind/bug']):
            
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            
            mock_issue = Mock()
            mock_issue.creator = 'sdispater'
            mock_issue.created_date = datetime(2021, 6, 18)
            mock_issue.labels = ['area/cli', 'kind/performance', 'version/2.0.1']
            mock_issue.events = []
            
            mock_loader.return_value.get_issues.return_value = [mock_issue]
            
            mock_fig = Mock()
            mock_ax1 = Mock()
            mock_ax2 = Mock()
            mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            analysis = UserActivityAnalysis()
            analysis.run()
            
            # Check what labels were actually plotted
            area_call_args = mock_ax1.stackplot.call_args[1]
            area_labels = area_call_args['labels']
            
            self.assertEqual(len(area_labels), 3, "If not equal, then only predefined labels are tracked, and new custom labels are ignored.")
            
            
    def test_run_with_no_matching_activity(self):
        """Test when sdispater has no activity."""
        with patch('user_activity_analysis.config') as mock_config, \
             patch('user_activity_analysis.DataLoader') as mock_loader, \
             patch('user_activity_analysis.plt') as mock_plt, \
             patch('user_activity_analysis.AREA_LABELS', ['area/installer']), \
             patch('user_activity_analysis.KIND_LABELS', ['kind/question']):
            
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            
            mock_issue = Mock()
            mock_issue.creator = 'otheruser'
            mock_issue.labels = ['area/installer']
            mock_issue.events = []
            
            mock_loader.return_value.get_issues.return_value = [mock_issue]
            
            mock_fig = Mock()
            mock_ax1 = Mock()
            mock_ax2 = Mock()
            mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            analysis = UserActivityAnalysis()
            analysis.run()
            
            mock_plt.show.assert_called_once()

    def test_event_to_year_month(self):
        """Test year-month formatting."""
        with patch('user_activity_analysis.config') as mock_config:
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            analysis = UserActivityAnalysis()
            
            event = {"event_date": datetime(2019, 1, 15)}
            self.assertEqual(analysis._event_to_year_month(event), "2019-01")
            
            event = {"event_date": datetime(2019, 11, 15)}
            self.assertEqual(analysis._event_to_year_month(event), "2019-11")
            
    
    def test_display_warning_message_for_user_with_no_activity(self):
        """Tests is the code displays a warning when specific user has no activity.
        The code should print something like "No activity found for user X" instead
        of plotting empty graphs.
        """
        with patch('user_activity_analysis.config') as mock_config, \
            patch('user_activity_analysis.DataLoader') as mock_loader, \
            patch('user_activity_analysis.plt') as mock_plt, \
            patch('user_activity_analysis.AREA_LABELS', ['area/python']), \
            patch('user_activity_analysis.KIND_LABELS', ['kind/question']), \
            patch('builtins.print') as mock_print:
            
            mock_config.get_parameter.side_effect = lambda x: 'sdispater' if x == 'user' else None
            
            mock_issue1 = Mock()
            mock_issue1.creator = 'otheruser1'
            mock_issue1.labels = ['area/python']
            mock_issue1.events = []
            
            mock_issue2 = Mock()
            mock_issue2.creator = 'otheruser2'
            mock_issue2.labels = ['kind/question']

            mock_event = Mock()
            mock_event.author = 'otheruser3'
            mock_event.event_type = 'commented'
            mock_event.event_date = '2024-10-20T00:33:06+00:00'
            mock_issue2.events = [mock_event]
            
            
            mock_loader.return_value.get_issues.return_value = [mock_issue1, mock_issue2]
            
            mock_fig = Mock()
            mock_ax1 = Mock()
            mock_ax2 = Mock()
            mock_plt.subplots.return_value = (mock_fig, (mock_ax1, mock_ax2))
            
            analysis = UserActivityAnalysis()
            analysis.run()
            
            
            print_calls = [str(call) for call in mock_print.call_args_list]
            has_warning = any('no activity' in str(call).lower() or 
                            'no events' in str(call).lower() or
                            'sdispater' in str(call).lower()
                            for call in print_calls)
            
            self.assertTrue(has_warning, "If test fails, the code should warn when user has no activity instead of plotting empty graphs.")
            
if __name__ == '__main__':
    unittest.main()
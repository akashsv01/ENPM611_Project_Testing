import unittest
from datetime import datetime
from model import State, Event, Issue


class TestState(unittest.TestCase):
    """Test the State enum."""
    
    def test_state_open(self):
        """Test State.open value."""
        self.assertEqual(State.open, 'open')
        self.assertEqual(State.open.value, 'open')
    
    def test_state_closed(self):
        """Test State.closed value."""
        self.assertEqual(State.closed, 'closed')
        self.assertEqual(State.closed.value, 'closed')


class TestEvent(unittest.TestCase):
    """Test the Event class."""
    
    def test_event_init_with_none(self):
        """Test Event initialization with None."""
        event = Event(None)
        
        self.assertIsNone(event.event_type)
        self.assertIsNone(event.author)
        self.assertIsNone(event.event_date)
        self.assertIsNone(event.label)
        self.assertIsNone(event.comment)
    
    def test_event_from_json_complete(self):
        """Test Event with complete JSON data."""
        jobj = {
            'event_type': 'commented',
            'author': 'sdispater',
            'event_date': '2019-11-05T12:07:48+00:00',
            'label': 'bug',
            'comment': 'This is a test comment'
        }
        
        event = Event(jobj)
        
        self.assertEqual(event.event_type, 'commented')
        self.assertEqual(event.author, 'sdispater')
        self.assertIsInstance(event.event_date, datetime)
        self.assertEqual(event.label, 'bug')
        self.assertEqual(event.comment, 'This is a test comment')
    
    def test_event_from_json_partial(self):
        """Test Event with partial JSON data."""
        jobj = {
            'event_type': 'closed',
            'author': 'anyuser'
        }
        
        event = Event(jobj)
        
        self.assertEqual(event.event_type, 'closed')
        self.assertEqual(event.author, 'anyuser')
        self.assertIsNone(event.event_date)
        self.assertIsNone(event.label)
        self.assertIsNone(event.comment)
    
    def test_event_from_json_invalid_date(self):
        """Test Event with invalid date format."""
        jobj = {
            'event_type': 'labeled',
            'author': 'testuser',
            'event_date': 'invalid-date-format'
        }
        
        event = Event(jobj)
        
        self.assertEqual(event.event_type, 'labeled')
        self.assertEqual(event.author, 'testuser')
        # Date parsing fails, should remain None
        self.assertIsNone(event.event_date)


class TestIssue(unittest.TestCase):
    """Test the Issue class."""
    
    def test_issue_with_none(self):
        """Test Issue initialization with None."""
        issue = Issue(None)
        self.assertIsNone(issue.url)
        self.assertIsNone(issue.title)
        self.assertIsNone(issue.creator)
        self.assertIsNone(issue.text)
        self.assertEqual(issue.labels, [])
        self.assertEqual(issue.number, -1)
        
    
    def test_issue_without_argument(self):
        """Test Issue initialization without argument."""
        issue = Issue()
        self.assertIsNone(issue.creator)
        self.assertEqual(issue.number, -1)
        self.assertIsNone(issue.text)
        self.assertIsNone(issue.url)
        self.assertIsNone(issue.title)
    
    def test_issue_with_complete_data(self):
        """Test Issue with complete JSON data."""
        jobj = {
            'url': 'https://github.com/python-poetry/poetry/issues/1234',
            'creator': 'sdispater',
            'labels': ['area/build-system', 'kind/bug'],
            'state': 'open',
            'assignees': ['user'],
            'title': 'Test Issue',
            'text': 'Description',
            'number': '1234',
            'created_date': '2019-11-05T10:30:00',
            'updated_date': '2019-11-06T15:45:00',
            'timeline_url': 'https://api.github.com/repos/python-poetry/poetry/issues/1234/timeline',
            "events": [
                            {
                                "event_type": "labeled",
                                "author": "otheruser1",
                                "event_date": "2019-11-09T11:44:18+00:00",
                                "label": "Bug"
                            },
                            {
                                "event_type": "commented",
                                "author": "otheruser2",
                                "event_date": "2019-11-11T00:20:37+00:00",
                                "label" : "status/accepted",
                                "comment": "Fix it using --no-root"
                            }
                        ]
        }
        issue = Issue(jobj)
        
        self.assertEqual(issue.creator, 'sdispater')
        self.assertEqual(issue.state, State.open)
        self.assertEqual(issue.number, 1234)
        self.assertEqual(len(issue.events), 2)
        self.assertIsInstance(issue.events[0], Event)
    
    def test_issue_with_closed_state(self):
        """Test Issue with closed state."""
        jobj = {'state': 'closed', 'creator': 'testuser'}
        issue = Issue(jobj)
        self.assertEqual(issue.state, State.closed)
    
    def test_issue_with_invalid_number(self):
        """Test Issue with invalid number - exception handling."""
        jobj = {'state': 'open', 'number': 'not-a-number'}
        issue = Issue(jobj)
        self.assertEqual(issue.number, -1)
    
    def test_issue_with_invalid_dates(self):
        """Test Issue with invalid dates - exception handling."""
        jobj = {
            'state': 'open',
            'created_date': 'invalid',
            'updated_date': 'invalid'
        }
        issue = Issue(jobj)
        self.assertIsNone(issue.created_date)
        self.assertIsNone(issue.updated_date)


if __name__ == '__main__':
    unittest.main()
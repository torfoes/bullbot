import datetime

from django.test import TestCase

from trading.injestion import TruthClient


class DummyStatus:
    """Dummy status object to simulate Truthbrush output."""
    def __init__(self, id, text, created_at=None):
        self.id = id
        self.text = text
        self.created_at = created_at or datetime.datetime(2025, 4, 21, 12, 0, 0)
        self.user_handle = 'testuser'


class IngestionTest(TestCase):
    def setUp(self):
        # Create client and stub out sc.pull_statuses
        self.client = TruthClient()
        # Simulate three posts (newest first)
        self.statuses = [
            DummyStatus('3', 'Third post'),
            DummyStatus('2', 'Second post'),
            DummyStatus('1', 'First post'),
        ]
        self.client.sc.pull_statuses = lambda username: list(self.statuses)

    def test_get_new_posts_first_time(self):
        # First call should return all posts in oldest-first order
        posts = list(self.client.get_new_posts())
        self.assertEqual([p.id for p in posts], ['1', '2', '3'])
        # last_seen should be set to id of newest post
        self.assertEqual(self.client.last_seen, '3')

    def test_get_new_posts_subsequent(self):
        # First call to set last_seen
        _ = list(self.client.get_new_posts())
        # Second call should yield no posts (nothing newer)
        posts2 = list(self.client.get_new_posts())
        self.assertEqual(posts2, [])

    def test_get_new_posts_with_new_items(self):
        # First call
        _ = list(self.client.get_new_posts())
        # Append a new status to front (newest)
        new_status = DummyStatus('4', 'Fourth post')
        self.client.sc.pull_statuses = lambda username: [new_status] + list(self.statuses)
        posts3 = list(self.client.get_new_posts())
        # Should return only the new one
        self.assertEqual([p.id for p in posts3], ['4'])
        # last_seen updated to '4'
        self.assertEqual(self.client.last_seen, '4')
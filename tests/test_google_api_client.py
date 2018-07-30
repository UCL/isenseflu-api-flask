"""
 Tests Google Trends API client
"""

from datetime import date, timedelta
from unittest import TestCase

from scheduler.google_api_client import GoogleApiClient


class GoogleApiClientTestCase(TestCase):

    def test_fetch_google_scores(self):
        instance = GoogleApiClient()
        terms = ['flu']
        start = date.today() - timedelta(days=5)
        end = start + timedelta(days=1)
        result = instance.fetch_google_scores(terms, start, end)
        self.assertEqual(len(result), 1)
        self.assertIn('term', result[0])
        self.assertIn('points', result[0])


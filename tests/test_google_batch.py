"""
 Tests behaviour of GoogleBatch class under different date ranges
"""

from datetime import date, timedelta
from unittest import TestCase

from scheduler.google_batch import GoogleBatch


class GoogleBatchTestCase(TestCase):
    """ Test case for module scheduler.google_batch """

    def test_get_batch_within_interval(self):
        """
        Scenario: Evaluate GoogleBatch under a date range within the allowed interval
        Given a list of Google terms with 30 items
        When the date_collect tuple has a date range of 66 days
        Then batch has a size of 1
        And the date range tuple is the same as the one used in the constructor
        """
        google_terms = ['Term %d' % t for t in range(1, 31)]
        start_date = date(2018, 1, 1)
        collect_dates = [(start_date, start_date + timedelta(days=66))]
        instance = GoogleBatch(google_terms, collect_dates)
        batch = list(instance.get_batch())
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch[0][1], start_date)
        self.assertEqual(batch[0][2], start_date + timedelta(days=66))

    def test_get_batch_outside_interval(self):
        """
        Scenario: Evaluate GoogleBatch under a date range outside the allowed interval
        Given a list of Google terms with 30 items
        When the date_collect tuple has a date range of 67 days
        Then the batch has a size of 2
        And the date range tuple for the last item in the batch have values
        for start_date and end_date of start_date + 67 days
        """
        google_terms = ['Term %d' % t for t in range(1, 31)]
        start_date = date(2018, 1, 1)
        collect_dates = [(start_date, start_date + timedelta(days=67))]
        instance = GoogleBatch(google_terms, collect_dates)
        batch = list(instance.get_batch())
        self.assertEqual(len(batch), 2)
        self.assertEqual(batch[1][1], start_date + timedelta(days=67))
        self.assertEqual(batch[1][2], start_date + timedelta(days=67))

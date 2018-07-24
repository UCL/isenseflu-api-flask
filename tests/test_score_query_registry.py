"""
 Tests registry of queries handling data for scheduler module
"""

from datetime import date
from unittest import TestCase

from app import create_app, DB
from app.models import GoogleDate
from scheduler.score_query_registry import get_dates_missing_google_score


class ScoreQueryRegistryTestCase(TestCase):
    """ Test case for module scheduler.score_query_registry """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_dates_missing_google(self):
        """
        Scenario: Get a list of dates with missing Google scores
        Given a FluModel with an id value of 1 exists
        And a GoogleTerm with an id value of 1 exists
        And GoogleScore.score_date for term_id = 1 are '2018-01-02', '2018-01-03', '2018-01-05'
        When start = '2018-01-01' and end = '2018-01-05'
        Then the list contains '2018-01-01' and '2018-01-04'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                google_date = GoogleDate()
                google_date.flu_model_id = 1
                google_date.score_date = date(2018, 1, day)
                google_date.save()
            google_date.save()
            result = get_dates_missing_google_score(1, date(2018, 1, 1), date(2018, 1, 5))
            self.assertListEqual(result, [date(2018, 1, 1), date(2018, 1, 4)])

    def test_no_dates_missing_google(self):
        """
        Scenario: Get a list of dates with missing Google scores
        Given a FluModel with an id value of 1 does not exist
        And a GoogleTerm with an id value of 1 does not exist
        Then an empty list is returned
        """
        with self.app.app_context():
            result = get_dates_missing_google_score(1, date(2018, 1, 1), date(2018, 1, 5))
            self.assertListEqual(result, [])

    def tearDown(self):
        DB.drop_all(app=self.app)

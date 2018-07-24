"""
 Tests query functions to access model data
"""

from datetime import date
from unittest import TestCase

from app import create_app, DB
from app.models import get_existing_google_dates, FluModelGoogleTerm, GoogleScore, GoogleTerm


class ModelsTestCase(TestCase):
    """ Test case for models.py """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_existing_google_dates(self):
        """
        Scenario: Get list of existing dates from GoogleScore
        Given FluModelGoogleTerm.flu_model_id value 1 = exists
        And GoogleTerm.id = 1 exists
        And GoogleScore.score_date for term_id = 1 are '2018-01-02', '2018-01-03', '2018-01-05'
        When model_id = 1, start = '2018-01-01', end = '2018-01-02'
        Then the list contains one tuple for date '2018-01-02'
        """
        flu_model_google_term = FluModelGoogleTerm()
        flu_model_google_term.flu_model_id = 1
        flu_model_google_term.google_term_id = 1
        google_term = GoogleTerm()
        google_term.id = 1
        google_term.term = 'Flu'
        with self.app.app_context():
            for day in (2, 3, 5):
                google_score = GoogleScore()
                google_score.term_id = 1
                google_score.score_value = 0.1
                google_score.score_date = date(2018, 1, day)
                DB.session.add(google_score)
            DB.session.add(flu_model_google_term)
            DB.session.add(google_term)
            DB.session.commit()
            result = get_existing_google_dates(1, date(2018, 1, 1), date(2018, 1, 2))
            self.assertListEqual(result, [(date(2018, 1, 2),)])

    def tearDown(self):
        DB.drop_all(app=self.app)

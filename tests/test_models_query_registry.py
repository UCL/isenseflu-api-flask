"""
 Tests query functions to access model data
"""

from datetime import date
from unittest import TestCase

from app import create_app, DB
from app.models import FluModelGoogleTerm, GoogleDate, GoogleTerm
from app.models_query_registry import get_existing_google_dates, get_google_terms_for_model_id


class ModelsTestCase(TestCase):
    """ Test case for models_query_registry.py """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_existing_google_dates(self):
        """
        Scenario: Get list of existing dates from GoogleScore
        Given a GoogleDate.flu_model_id value of 1 exists
        And GoogleScore.score_date with values '2018-01-02', '2018-01-03', '2018-01-05'
        When model_id = 1, start = '2018-01-01', end = '2018-01-02'
        Then the list contains one tuple for date '2018-01-02'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                google_date = GoogleDate()
                google_date.flu_model_id = 1
                google_date.score_date = date(2018, 1, day)
                google_date.save()
            google_date.save()
            result = get_existing_google_dates(1, date(2018, 1, 1), date(2018, 1, 2))
            self.assertListEqual(result, [(date(2018, 1, 2),)])

    def test_get_google_terms_for_model(self):
        """
        Scenario: Get list of Google terms for which a particular flu model was created against
        Given a FluModelGoogleTerm.flu_model_id value of 1 exists
        And GoogleTerms values (1, 'Term 1'), (2, 'Term 2') and (3, 'Term 3') for flu_model_id 1
        When model_id = 1
        Then the list contains 'Term 1', 'Term 2' and 'Term 3' as tuples
        """
        with self.app.app_context():
            expected = []
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                expected.append(('Term %d' % i,))
            result = get_google_terms_for_model_id(1)
            self.assertListEqual(result, expected)

    def tearDown(self):
        DB.drop_all(app=self.app)

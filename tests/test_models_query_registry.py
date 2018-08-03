"""
 Tests query functions to access model data
"""

from datetime import date
from unittest import TestCase

from app import create_app, DB
from app.models import FluModelGoogleTerm, GoogleDate, GoogleScore, GoogleTerm, ModelScore
from app.models_query_registry import get_existing_google_dates, get_google_terms_for_model_id, \
    set_google_date_for_model_id, set_google_scores_for_term, get_existing_model_dates


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
                google_date = GoogleDate(1, date(2018, 1, day))
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

    def test_set_google_scores_for_term(self):
        """
        Scenario: Persist scores if they are not already in the database
        Given a Google term with no score value
        When an entity is saved for that term with a date of 2018-01-01
        Then the result count for a term of that definition and same date is 1
        """
        with self.app.app_context():
            google_term = GoogleTerm()
            google_term.id = 1
            google_term.term = 'Term 1'
            google_term.save()
            set_google_scores_for_term('Term 1', [(date(2018, 1, 1), 0.1)])
            result = GoogleScore.query.filter_by(term_id=1, score_date=date(2018, 1, 1)).count()
            self.assertEqual(result, 1)

    def test_set_google_date_for_model(self):
        """
        Scenario: Persist the date of retrieval of a complete set of scores from Google
        Given a flu model with a set of three terms
        And a score for each of them for one date
        Then the date is persisted on the database
        """
        with self.app.app_context():
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                google_score = GoogleScore(i, date(2018, 1, 1), 0.5 + i)
                google_score.save()
            set_google_date_for_model_id(1, date(2018, 1, 1))
            result = DB.session.query(
                DB.session.query(GoogleDate).filter_by(flu_model_id=1,
                                                       score_date=date(2018, 1, 1)
                                                       ).exists()
            ).scalar()
            self.assertTrue(result)

    def test_get_existing_model_dates(self):
        """
        Scenario: Get list of existing dates from ModelScore
        Given a ModelScore.flu_model_id value of 1 exists
        And ModelScore.score_date with values '2018-01-02', '2018-01-03', '2018-01-05'
        When model_id = 1, start = '2018-01-01', end = '2018-01-02'
        Then the list contains one tuple for date '2018-01-02'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                model_score = ModelScore()
                model_score.flu_model_id = 1
                model_score.score_date = date(2018, 1, day)
                model_score.score_value = 0.1 + day
                model_score.region = 'e'
                model_score.save()
            result = get_existing_model_dates(1, date(2018, 1, 1), date(2018, 1, 2))
            self.assertListEqual(result, [(date(2018, 1, 2),)])

    def tearDown(self):
        DB.drop_all(app=self.app)

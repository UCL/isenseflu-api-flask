"""
 Tests registry of queries handling data for scheduler module
"""

from datetime import date
from unittest import TestCase
from unittest.mock import call, patch

from app import create_app, DB
from app.models import FluModelGoogleTerm, GoogleDate, GoogleTerm, ModelScore
from scheduler.score_query_registry import get_days_missing_google_score, get_google_batch, \
    get_date_ranges_google_score, set_google_scores, get_dates_missing_model_score


class ScoreQueryRegistryTestCase(TestCase):
    """ Test case for module scheduler.score_query_registry """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_days_missing_google(self):
        """
        Scenario: Get the number of days with missing Google scores
        Given a FluModel with an id value of 1 exists
        And a GoogleTerm with an id value of 1 exists
        And GoogleScore.score_date for term_id = 1 are '2018-01-02', '2018-01-03', '2018-01-05'
        When start = '2018-01-01' and end = '2018-01-05'
        Then number of days with missing Google scores is 2
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                google_date = GoogleDate(1, date(2018, 1, day))
                google_date.save()
            google_date.save()
            result = get_days_missing_google_score(1, date(2018, 1, 1), date(2018, 1, 5))
            self.assertEqual(result, 2)

    def test_no_dates_missing_google(self):
        """
        Scenario: Get the number of days with missing Google scores
        Given a FluModel with an id value of 1 does not exist
        And a GoogleTerm with an id value of 1 does not exist
        Then number of days with missing Google scores is 0
        """
        with self.app.app_context():
            result = get_days_missing_google_score(1, date(2018, 1, 1), date(2018, 1, 5))
            self.assertEqual(result, 0)

    def test_get_google_batch(self):
        """
        Scenario: Get a generator that returns the list of Google terms and date ranges to be
        collected from the API organised in batches of up to 30 terms as per API documentation
        Given a FluModel with an id value of 1 exists
        And a list of 31 terms for such FluModel id
        When querying for a list of missing date ranges
        Then the generator returns items grouped by term batch and then date range
        """
        with self.app.app_context():
            terms_expected = []
            for idx in range(31):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = idx
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = idx
                google_term.term = 'Term %d' % idx
                terms_expected.append('Term %d' % idx)
                google_term.save()
            missing_dates = [
                (date(2018, 1, 1), date(2018, 1, 1)),
                (date(2018, 1, 6), date(2018, 1, 9)),
                (date(2018, 1, 11), date(2018, 1, 15))
            ]
            result = list(get_google_batch(1, missing_dates))
            terms_grouped = (terms_expected[0:30], terms_expected[30:31])
            counter = 0
            for terms_grouped_item in terms_grouped:
                for missing_dates_tuple in missing_dates:
                    res_terms, res_start, res_end = result[counter]
                    self.assertListEqual(res_terms, terms_grouped_item)
                    self.assertEqual(res_start, missing_dates_tuple[0])
                    self.assertEqual(res_end, missing_dates_tuple[1])
                    counter += 1

    def test_get_date_ranges_google(self):
        """
        Scenario: Get a list of date ranges with missing Google scores
        Given a FluModel with an id value of 1 exists
        And a GoogleTerm with an id value of 1 exists
        And GoogleScore.score_date for term_id = 1 are '2018-01-02', '2018-01-03', '2018-01-05'
        When start = '2018-01-01' and end = '2018-01-05'
        Then the list contains a list of tuples specifying start and end dates
        """
        with self.app.app_context():
            for day in (2, 3, 4, 5, 10):
                google_date = GoogleDate(1, date(2018, 1, day))
                google_date.save()
            result = get_date_ranges_google_score(1, date(2018, 1, 1), date(2018, 1, 15))[0]
            expected = [
                (date(2018, 1, 1), date(2018, 1, 1)),
                (date(2018, 1, 6), date(2018, 1, 9)),
                (date(2018, 1, 11), date(2018, 1, 15))
            ]
            self.assertListEqual(result, expected)
            result = get_date_ranges_google_score(1, date(2018, 1, 2), date(2018, 1, 5))
            self.assertTupleEqual(result, ([], []))
            result = get_date_ranges_google_score(1, date(2018, 1, 11), date(2018, 1, 15))[0]
            self.assertListEqual(result, [(date(2018, 1, 11), date(2018, 1, 15))])

    def test_set_google_scores(self):
        """
        Scenario: Persist a batch of Google score data
        Given a list of data points containing data for two terms
        Then function app.models_query_registry#set_google_scores_for_term_id is
        called twice
        """
        data_points = [
            {
                'term': 'a flu',
                'points': [
                    {
                        'date': 'Jul 01 2018',
                        'value': 60.587
                    },
                    {
                        'date': 'Jul 02 2018',
                        'value': 83.017
                    }
                ]
            },
            {
                'term': 'flu season',
                'points': [
                    {
                        'date': 'Jul 01 2018',
                        'value': 0.0
                    },
                    {
                        'date': 'Jul 02 2018',
                        'value': 15.144
                    }
                ]
            }
        ]
        expected = [
            ('a flu', [(date(2018, 7, 1), 60.587), (date(2018, 7, 2), 83.017)]),
            ('flu season', [(date(2018, 7, 1), 0.0), (date(2018, 7, 2), 15.144)])
        ]
        with patch('scheduler.score_query_registry.set_google_scores_for_term') as patched_f:
            patched_f.return_value = None
            set_google_scores(data_points)
            self.assertEqual(patched_f.call_count, 2)
            calls = [call(expected[0][0], expected[0][1]), call(expected[1][0], expected[1][1])]
            patched_f.assert_has_calls(calls)

    def test_get_days_missing_model(self):
        """
        Scenario: Get the number of days with missing model scores
        Given a FluModel with an id value of 1 exists
        And ModelScores with score dates '2018-01-02', '2018-01-03', '2018-01-05'
        When start = '2018-01-01' and end = '2018-01-05'
        Then dates missing are '2018-01-01', '2018-01-04'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                model_score = ModelScore()
                model_score.flu_model_id = 1
                model_score.score_date = date(2018, 1, day)
                model_score.score_value = 0.1 + day
                model_score.region = 'e'
                model_score.save()
            result = get_dates_missing_model_score(1, date(2018, 1, 1), date(2018, 1, 5))
            expected = [date(2018, 1, 1), date(2018, 1, 4)]
            self.assertListEqual(result, expected)

    def tearDown(self):
        DB.drop_all(app=self.app)

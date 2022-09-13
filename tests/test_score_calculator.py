"""
 Tests calculation of model scores
"""

from datetime import date, timedelta
from os import environ
from unittest import TestCase
from unittest.mock import patch, DEFAULT, Mock

from app import create_app, DB
from app.models import FluModelGoogleTerm, GoogleDate, GoogleTerm, ModelFunction, ModelScore
from scheduler import score_calculator
from scheduler.google_api_client import GoogleApiClient


class ScoreCalculatorTestCase(TestCase):
    """ Test case for module scheduler.score_calculator """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_no_missing_google_range(self):
        """
        Scenario: Test run function to calculate model score for 2 consecutive dates
        Given requested Google dates already exist for such dates
        And the model score exist for one date
        Then the model score for the missing date is stored
        """
        with self.app.app_context():
            google_date_1 = GoogleDate(1, date(2018, 1, 1))
            google_date_1.save()
            google_date_2 = GoogleDate(1, date(2018, 1, 2))
            google_date_2.save()
            model_function = ModelFunction()
            model_function.flu_model_id = 1
            model_function.function_name = 'matlab_function'
            model_function.average_window_size = 1
            model_function.has_confidence_interval = False
            model_function.save()
            model_score = ModelScore()
            model_score.flu_model_id = 1
            model_score.score_date = date(2018, 1, 1)
            model_score.score_value = 0.5
            model_score.region = 'e'
            model_score.save()
            with patch.multiple('scheduler.score_calculator', build_calculator=DEFAULT) as mock_dict:
                matlab_client = mock_dict['build_calculator'].return_value = Mock()
                matlab_client.calculate_model_score.return_value = 1.0
                result_before = ModelScore.query.filter_by(flu_model_id=1).all()
                self.assertListEqual(result_before, [model_score])
                score_calculator.run(1, date(2018, 1, 1), date(2018, 1, 2))
                result_after = ModelScore.query.filter_by(flu_model_id=1).all()
                self.assertEqual(len(result_after), 2)

    def test_api_returning_zero_values(self):
        """
        Scenario: Test run function to attempt calculating model score for a specific date
        Given the Google API returns zero for the term temperature
        Then the retrieval of the scores and calculation of model scores is skipped
        And the requested data is not available on Google API
        And a warning log message is printed
        """
        with self.app.app_context():
            google_date_1 = GoogleDate(1, date.today() - timedelta(days=1))
            google_date_1.save()
            google_term = GoogleTerm()
            google_term.id = 1
            google_term.term = 'Term 1'
            google_term.save()
            flu_model_google_term = FluModelGoogleTerm()
            flu_model_google_term.flu_model_id = 1
            flu_model_google_term.google_term_id = 1
            flu_model_google_term.save()
            model_function = ModelFunction()
            model_function.flu_model_id = 1
            model_function.function_name = 'matlab_function'
            model_function.average_window_size = 1
            model_function.has_confidence_interval = False
            model_function.save()
            with patch.multiple(
                    GoogleApiClient, fetch_google_scores=DEFAULT, is_returning_non_zero_for_temperature=DEFAULT
            ) as patch_dict, patch('scheduler.score_calculator.get_dates_missing_model_score') as model_score_ctx:
                with self.assertLogs(level='WARNING') as logContext:
                    patch_dict['fetch_google_scores'].return_value = []
                    patch_dict['is_returning_non_zero_for_temperature'].return_value = False
                    model_score_ctx.return_value = False
                    score_calculator.run(1, date.today(), date.today())
                self.assertListEqual(logContext.output, ['WARNING:root:Google API has returned zero for the term temperature. Not fetching scores'])

    def test_failed_retrieval_of_google_scores(self):
        """
        Scenario: Test run function to attempt calculating model score for a specific date
        Given the requested Google date is missing
        And the requested data is not available on Google API
        Then run function returns without calculating the score
        And an error log message is printed
        """
        with self.app.app_context():
            google_date_1 = GoogleDate(1, date.today() - timedelta(days=1))
            google_date_1.save()
            google_term = GoogleTerm()
            google_term.id = 1
            google_term.term = 'Term 1'
            google_term.save()
            flu_model_google_term = FluModelGoogleTerm()
            flu_model_google_term.flu_model_id = 1
            flu_model_google_term.google_term_id = 1
            flu_model_google_term.save()
            model_function = ModelFunction()
            model_function.flu_model_id = 1
            model_function.function_name = 'matlab_function'
            model_function.average_window_size = 1
            model_function.has_confidence_interval = False
            model_function.save()
            with patch.multiple(
                    GoogleApiClient, fetch_google_scores=DEFAULT, is_returning_non_zero_for_temperature=DEFAULT
            ) as patch_dict:
                with self.assertLogs(level='ERROR') as logContext, self.assertRaises(RuntimeError) as errorCtx:
                    patch_dict['fetch_google_scores'].return_value = []
                    patch_dict['is_returning_non_zero_for_temperature'].return_value = True
                    score_calculator.run(1, date.today(), date.today())
                self.assertListEqual(logContext.output, ['ERROR:root:Retrieval of Google scores failed'])
                self.assertTrue('Retry call to Google API' in str(errorCtx.exception))

    def test_twitter_enabled(self):
        """
        Scenario: Test run function behaviour when the environment variable TWITTER_ENABLED is present
        """
        with self.app.app_context():
            google_date = GoogleDate(1, date.today() - timedelta(days=1))
            google_date.save()
            model_function = ModelFunction()
            model_function.flu_model_id = 1
            model_function.function_name = 'matlab_function'
            model_function.average_window_size = 1
            model_function.has_confidence_interval = False
            model_function.save()
            with patch.multiple(
                    'scheduler.score_calculator', build_calculator=DEFAULT, build_message_client=DEFAULT
            ) as mock_dict:
                matlab_client = mock_dict['build_calculator'].return_value = Mock()
                matlab_client.calculate_model_score.return_value = 1.0
                message_client = mock_dict['build_message_client'].return_value = Mock()
                message_client.publish_model_score.return_value = None
                environ['TWITTER_ENABLED'] = 'True'
                environ['TWITTER_MODEL_ID'] = '1'
                with self.assertLogs(level='INFO') as logContext:
                    score_calculator.run(1, google_date.score_date, google_date.score_date)
                self.assertListEqual(logContext.output, [
                    'INFO:root:Google scores have already been collected for this time period',
                    'INFO:root:Latest ModelScore value sent to message queue'
                ])
                result_after = ModelScore.query.filter_by(flu_model_id=1).all()
                self.assertEqual(len(result_after), 1)

    def test_runsched_ntimes(self):
        """
        Scenario: Test runsched function to calculate model scores for more than one id
        """
        with self.app.app_context() \
             and patch('scheduler.score_calculator._run_sched_for_model_no_set_dates') as patched_run:
            score_calculator.runsched([1, 2], self.app)
            self.assertEqual(patched_run.call_count, 2)

    def test_runsched_date_assert_trigger(self):
        """
        Test runsched function to trigger an assertion error when number of days since
        last Google score date is equal or greater than 66
        """
        with self.app.app_context():
            google_date = GoogleDate(1, date.today() - timedelta(days=66))
            google_date.save()
            self.assertRaises(AssertionError, score_calculator.runsched, [1], self.app)

    def test_runsched_google_scores_already_collected(self):
        """
        Test runsched function when Google scores have already been collected for the
        requested time period (end date currently set to T - 3 days)
        """
        with self.app.app_context():
            google_date = GoogleDate(1, date.today() - timedelta(days=3))
            google_date.save()
            with self.assertLogs(level='INFO') as logContext:
                score_calculator.runsched([1], self.app)
                self.assertListEqual(logContext.output, [
                    'INFO:root:Google scores have already been collected for this time period',
                    'INFO:root:Model scores have already been collected for this time period'
                ])

    def test_runsched_google_scores_get_date_ranges(self):
        """
        Evaluate parameters passed to get_date_ranges_google_score function within
        _run_sched_for_model_no_set_dates
        """
        last_date = date.today() - timedelta(days=5)
        with self.app.app_context():
            google_date = GoogleDate(1, last_date)
            google_date.save()
            model_score = ModelScore()
            model_score.flu_model_id = 1
            model_score.score_date = date.today() - timedelta(days=4)
            model_score.score_value = 0.5
            model_score.region = 'e'
            model_score.save()
            with patch('scheduler.score_calculator.get_date_ranges_google_score') as patched_call:
                patched_call.return_value = (None, None)
                score_calculator.runsched([1], self.app)
                patched_call.assert_called_with(1, last_date + timedelta(days=1), date.today() - timedelta(days=4))

    def test_runsched_get_google_batch(self):
        """
        Evaluate parameters passed to get_google_batch function in
        _run_sched_for_model_no_set_dates
        """
        last_date = date.today() - timedelta(days=5)
        end_date = date.today() - timedelta(days=4)
        with self.app.app_context():
            google_date = GoogleDate(1, last_date)
            google_date.save()
            model_score = ModelScore()
            model_score.flu_model_id = 1
            model_score.score_date = end_date
            model_score.score_value = 0.5
            model_score.region = 'e'
            model_score.save()
            with patch('scheduler.score_calculator.get_google_batch') as patched_call:
                patched_call.return_value = []
                score_calculator.runsched([1], self.app)
                patched_call.assert_called_with(1, [(end_date, end_date)])

    @patch('scheduler.score_calculator.GoogleApiClient')
    @patch('scheduler.score_calculator.set_and_verify_google_dates')
    def test_runsched_fetch_google_scores(self, mock_verify, mock_client):
        """
        Evaluate parameters passed to fetch_google_scores and set_and_verify_google_dates
        functions in _run_sched_for_model_no_set_dates
        """
        last_date = date.today() - timedelta(days=5)
        end_date = date.today() - timedelta(days=4)
        with self.app.app_context():
            google_date = GoogleDate(1, last_date)
            google_date.save()
            model_score = ModelScore()
            model_score.flu_model_id = 1
            model_score.score_date = end_date
            model_score.score_value = 0.5
            model_score.region = 'e'
            model_score.save()
            google_term = GoogleTerm()
            google_term.id = 1
            google_term.term = 'Term 1'
            google_term.save()
            flu_model_google_term = FluModelGoogleTerm()
            flu_model_google_term.flu_model_id = 1
            flu_model_google_term.google_term_id = 1
            flu_model_google_term.save()
            patched_api_client = mock_client.return_value
            score_calculator.runsched([1], self.app)
            patched_api_client.fetch_google_scores.assert_called_with(['Term 1'], last_date, end_date)
            mock_verify.assert_called_with(1, [end_date])

    def test_runsched(self):
        """
        Scenario: Test runsched function to calculate model scores
        Given a last score_date of date.today() - timedelta(days=5)
        Then score_calculator.run is called with a start date of date.today() - timedelta(days=3)
        And end date of date.today() - timedelta(days=4)
        """
        with self.app.app_context():
            model_score = ModelScore()
            model_score.flu_model_id = 1
            model_score.score_date = date.today() - timedelta(days=5)
            model_score.score_value = 0.5
            model_score.region = 'e'
            model_score.save()
            with patch('scheduler.score_calculator._run_sched_for_model_no_set_dates') as patched_run:
                score_calculator.runsched([1], self.app)
                patched_run.assert_called_with(1)

    def tearDown(self):
        DB.drop_all(app=self.app)

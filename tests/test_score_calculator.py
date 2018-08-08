"""
 Tests calculation of model scores
"""

from datetime import date
from unittest import TestCase
from unittest.mock import patch, DEFAULT, Mock

from app import create_app, DB
from app.models import GoogleDate, ModelFunction, ModelScore
from scheduler import score_calculator


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
            with patch.multiple('scheduler.score_calculator', build_matlab_client=DEFAULT) as mock_dict:
                matlab_client = mock_dict['build_matlab_client'].return_value = Mock()
                matlab_client.calculate_model_score.return_value = 1.0
                result_before = ModelScore.query.filter_by(flu_model_id=1).all()
                self.assertListEqual(result_before, [model_score])
                score_calculator.run(1, date(2018, 1, 1), date(2018, 1, 2))
                result_after = ModelScore.query.filter_by(flu_model_id=1).all()
                self.assertEqual(len(result_after), 2)

    def tearDown(self):
        DB.drop_all(app=self.app)

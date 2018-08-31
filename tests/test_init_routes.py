from unittest import TestCase
from datetime import date, datetime

from app import create_app, DB
from app.models import FluModel, ModelScore, ModelFunction, DefaultFluModel


class InitRoutesTestCase(TestCase):
    """Test case for the app routes (app.__init__)"""

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_root_no_models(self):
        response = self.client().get('/')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def test_get_rool(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        datapoint = ModelScore()
        datapoint.region = 'e'
        datapoint.score_date = date(2018, 6, 29)
        datapoint.calculation_timestamp = datetime.now()
        datapoint.score_value = 1.23
        datapoint.confidence_interval_lower = 0.81
        datapoint.confidence_interval_upper = 1.65
        flumodel.model_scores = [datapoint]
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        default_model = DefaultFluModel()
        default_model.flu_model_id = 1
        with self.app.app_context():
            flumodel.save()
            model_function.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/')
        result = response.get_json()
        expected = {
            'id': 1,
            'name': 'Test Model',
            'hasConfidenceInterval': True,
            'datapoints': [
                {
                    'score_date': 'Fri, 29 Jun 2018 00:00:00 GMT',
                    'score_value': 1.23,
                    'confidence_interval_lower': 0.81,
                    'confidence_interval_upper': 1.65
                }
            ]
        }
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)

    def test_get_models(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        with self.app.app_context():
            flumodel.save()
        response = self.client().get('/models')
        result = response.get_json()
        expected = [{
            'id': 1,
            'name': 'Test Model'
        }]
        self.assertEqual(result,  expected)
        self.assertEqual(response.status_code, 200)

    def test_get_models_no_content(self):
        response = self.client().get('/models')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def test_get_scores_for_model(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        dates = [date(2018, 3, 20), date(2018, 5, 20), date(2018, 6, 20)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = '1.23'
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        with self.app.app_context():
            flumodel.save()
            model_function.save()
        response = self.client().get('/scores/1?startDate=2018-05-30&endDate=2018-06-30')
        result = response.get_json()
        expected = {
            'name': 'Test Model',
            'sourceType': 'google',
            'displayModel': True,
            'parameters': {
                'georegion': 'e',
                'smoothing': 1
            },
            'datapoints': [
                {
                    'score_date': 'Wed, 20 Jun 2018 00:00:00 GMT',
                    'score_value': 1.23
                }
            ]
        }
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)
        response = self.client().get('/scores/1?startDate=2018-07-30&endDate=2018-06-30')
        self.assertEqual(response.status_code, 400)

    def test_get_scores_no_content(self):
        response = self.client().get('/scores/1')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def tearDown(self):
        DB.drop_all(app=self.app)
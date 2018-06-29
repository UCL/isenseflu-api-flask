from unittest import TestCase
from datetime import date, datetime

from app import create_app, db
from app.models import FluModel, ModelScore


class InitRoutesTestCase(TestCase):
    """Test case for the app routes (app.__init__)"""

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        db.create_all(app=self.app)

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
        datapoint.score_date = date.today()
        datapoint.calculation_timestamp = datetime.now()
        datapoint.score_value = '1.23'
        flumodel.model_scores = [datapoint]
        with self.app.app_context():
            flumodel.save()
        response = self.client().get('/')
        result = response.data
        self.assertEqual(result, b'[{"name": "Test Model", "sourceType": "google", "displayModel": true, "parameters": {"georegion": "e", "smoothing": 1}, "datapoints": [{"score_date": "Fri, 29 Jun 2018 00:00:00 GMT", "score_value": 1.23}]}]')
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
        result = response.data
        self.assertEqual(result, b'[{"id": 1, "name": "Test Model"}]')
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        db.drop_all(app=self.app)
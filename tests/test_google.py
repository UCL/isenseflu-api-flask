from unittest import TestCase
from datetime import date, datetime

from app import create_app, db
from app.models import FluModel, ModelScore


class GoogleTestCase(TestCase):
    """Test case for the Google blueprint"""

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        with self.app.app_context():
            db.create_all()

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
        flumodel.save()
        response = self.client().get('/')
        result = response.data
        print(result)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        with self.app.app_context():
            db.session.close()
            db.session.remove()
            db.drop_all()

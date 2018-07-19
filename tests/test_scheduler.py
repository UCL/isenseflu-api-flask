"""
 Tests background tasks executed by the scheduler
"""

from datetime import date, datetime
from unittest import TestCase

from app import create_app, DB
from app.models import FluModel, ModelScore
from scheduler import Scheduler


class SchedulerTestCase(TestCase):
    """ Test case for the scheduler component (scheduler.__init__) """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_run_model_not_found(self):
        """
        Given FluModel does not exist
        Then ValueError is raised
        """
        with self.app.app_context():
            scheduler = Scheduler(self.app)
            with self.assertRaises(ValueError):
                scheduler.run_model(1, None)

    def test_run_model(self):
        flumodel = FluModel()
        flumodel.id = 1
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        datapoint = ModelScore()
        datapoint.region = 'e'
        datapoint.score_date = date(2018, 6, 29)
        datapoint.calculation_timestamp = datetime.now()
        datapoint.score_value = '1.23'
        flumodel.model_scores = [datapoint]
        with self.app.app_context():
            flumodel.save()
            scheduler = Scheduler(self.app)
            scheduler.run_model(flumodel.id, "* * * * *")

    def tearDown(self):
        DB.drop_all(app=self.app)

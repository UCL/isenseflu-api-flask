"""
 Background tasks controlled by a scheduler
"""

import logging

from datetime import date, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_api import FlaskAPI

from app.models_query_registry import has_model, get_last_score_date
from .score_calculator import run

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


class Scheduler(object):
    """
    Manages an instance of apscheduler
    """

    def __init__(self, app: FlaskAPI = None):
        self.flask_app = app
        self.scheduler = BlockingScheduler()

    def run_model(self, model_id: int, crontab: str):
        """ Adds the calculattion of model scores for an id to the scheduler """
        with self.flask_app.app_context():
            if not has_model(model_id):
                raise ValueError('Could not find model with that ID')
            start = get_last_score_date(model_id) + timedelta(days=1)
            end = date.today() - timedelta(days=2)
            self.scheduler.add_job(
                func=run,
                kwargs={"model_id": model_id, "start": start, "end": end},
                trigger=CronTrigger.from_crontab(crontab),
                misfire_grace_time=3600
            )
            if not self.scheduler.running:
                self.scheduler.start()

    def init_model(self, model_id: int, start_date: date, end_date: date):
        """ Calculates the initial batch of scores """
        with self.flask_app.app_context():
            if not has_model(model_id):
                raise ValueError('Could not find model with that ID')
            run(model_id, start_date, end_date)

    def __del__(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

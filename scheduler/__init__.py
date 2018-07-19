import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from flask_api import FlaskAPI

from app.models import has_model, get_last_score_date
from .score_calculator import run

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


class Scheduler(object):

    def __init__(self, app: FlaskAPI = None):
        self.flask_app = app
        self.scheduler = BlockingScheduler()

    def run_model(self, model_id: int, crontab: str):
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

    def __del__(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

# i-sense flu api: REST API, and data processors for the i-sense flu service from UCL.
# (c) 2019, UCL <https://www.ucl.ac.uk/
#
# This file is part of i-sense flu api
#
# i-sense flu api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# i-sense flu api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with i-sense flu api.  If not, see <http://www.gnu.org/licenses/>.

"""
 Background tasks controlled by a scheduler
"""

import logging

from datetime import date
from typing import List

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_api import FlaskAPI

from app.models_query_registry import has_model
from .score_calculator import run, runsched

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


class Scheduler(object):
    """
    Manages an instance of apscheduler
    """

    def __init__(self, app: FlaskAPI = None):
        self.flask_app = app
        self.scheduler = BlockingScheduler()

    def run_model(self, model_id_list: List[int], crontab: str):
        """ Adds the calculattion of model scores for an id to the scheduler """
        with self.flask_app.app_context():
            for model_id in model_id_list:
                if not has_model(model_id):
                    raise ValueError('Could not find model with that ID')
            self.scheduler.add_job(
                func=runsched,
                kwargs={"model_id_list": model_id_list, "app": self.flask_app},
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

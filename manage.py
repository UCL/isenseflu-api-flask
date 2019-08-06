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
Commandline options for database management and testing
"""

import os
import unittest
from datetime import datetime
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import create_app, DB
from scheduler import Scheduler

MIGRATE = Migrate()

CONFIG_NAME = os.getenv('APP_CONFIG', 'development')
APP = create_app(CONFIG_NAME)
MIGRATE.init_app(APP, DB)

MANAGER = Manager(APP)
MANAGER.add_command('db', MigrateCommand)


@MANAGER.command
def test():
    """ Runs the unit tests without test coverage. """
    tests = unittest.TestLoader().discover('./tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


@MANAGER.command
def run_model_sched(model_ids_input, cron):
    """ Runs a scheduler to calculate model scores. """
    scheduler = Scheduler(APP)
    model_ids = [int(m) for m in model_ids_input.split(',')]
    scheduler.run_model(model_ids, cron)


@MANAGER.command
def init_model(model_id, start_date, end_date):
    """ Calculates the first batch of scores """
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    scheduler = Scheduler(APP)
    scheduler.init_model(model_id, start, end)


if __name__ == '__main__':
    MANAGER.run()

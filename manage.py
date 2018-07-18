"""
Commandline options for database management and testing
"""

import os
import unittest
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import create_app, DB

MIGRATE = Migrate()

CONFIG_NAME = os.getenv('APP_CONFIG', 'development')
APP = create_app(CONFIG_NAME)
MIGRATE.init_app(APP, DB)

MANAGER = Manager(APP)
MANAGER.add_command('db', MigrateCommand)


@MANAGER.command
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover('./tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    MANAGER.run()

import os
import unittest
from flask_script import Manager
from flask_migrate import MigrateCommand, Migrate

from app import create_app, db

migrate = Migrate()

config_name=os.getenv('APP_CONFIG', 'development')
app = create_app(config_name)
with app.app_context():
    migrate.init_app(app, db)
    db.create_all()

manager = Manager(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def test():
    """Runs the unit tests without test coverage."""
    tests = unittest.TestLoader().discover('./tests', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()

import os


class Config(object):
    DEBUG = False
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class StagingConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    TESTING = False


class ProductionMultiNode(ProductionConfig):
    MATLAB_API_HOST = os.getenv('MATLAB_API_HOST')


app_config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production-single': ProductionConfig,
    'production-multi': ProductionMultiNode
}

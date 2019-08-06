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
Configuration classes for Flask
"""
import os


class Config:  # pylint: disable=too-few-public-methods
    """
    Base configuration class for Flask with defaults
    """
    DEBUG = False
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):  # pylint: disable=too-few-public-methods
    """
    Development configuration for Flask
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):  # pylint: disable=too-few-public-methods
    """
    Testing configuration for Flask. It uses an in-memory database.
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class StagingConfig(Config):  # pylint: disable=too-few-public-methods
    """
    Staging configuration for Flask
    """
    DEBUG = True


class ProductionConfig(Config):  # pylint: disable=too-few-public-methods
    """
    Production configuration for Flask. It uses a local installation of either
    GNU Octave or MATLAB
    """
    TESTING = False


class ProductionMultiNode(ProductionConfig):  # pylint: disable=too-few-public-methods
    """
    Production configuration for Flask. It uses a remote installation of MATLAB
    """
    MATLAB_API_HOST = os.getenv('MATLAB_API_HOST')


APP_CONFIG = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'staging': StagingConfig,
    'production-single': ProductionConfig,
    'production-multi': ProductionMultiNode
}

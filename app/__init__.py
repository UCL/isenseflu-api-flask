"""
Flask app entry point
"""

from datetime import date, timedelta, datetime
from flask import request
from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

DB = SQLAlchemy()


def create_app(config_name):
    """ Creates an instance of Flask based on the config name as found in instance/config.py """

    from app.models import FluModel, ModelScore

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.ini', silent=True)
    DB.init_app(app)

    @app.route('/', methods=['GET'])
    def root_route():
        """ Default route (/). Returns all public model scores """
        flu_models = FluModel.get_all_public()
        if flu_models is None:
            return '', status.HTTP_503_SERVICE_UNAVAILABLE
        elif not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        results = []
        for flu_model in flu_models:
            datapoints = []
            for score in flu_model.model_scores:
                child = {
                    'score_date': score.score_date,
                    'score_value': score.score_value
                }
                datapoints.append(child)
            model_parameters = flu_model.get_model_parameters()
            obj = {
                'name': flu_model.name,
                'sourceType': flu_model.source_type,
                'displayModel': flu_model.is_displayed,
                'parameters': {
                    'georegion': 'e',
                    'smoothing': model_parameters['average_window_size']
                },
                'datapoints': datapoints
            }
            results.append(obj)
        return results, status.HTTP_200_OK

    @app.route('/models', methods=['GET'])
    def models_route():
        """ Returns a catalogue of public models """
        flu_models = FluModel.get_all_public()
        if flu_models is None:
            return '', status.HTTP_503_SERVICE_UNAVAILABLE
        elif not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        results = []
        for flu_model in flu_models:
            obj = {
                'id': flu_model.id,
                'name': flu_model.name
            }
            results.append(obj)
        return results, status.HTTP_200_OK

    @app.route('/scores/<int:id>', methods=['GET'])
    def scores_route(id):
        """ Returns a list of model scores for a model id, start and end date """
        def_end_date = date.today() - timedelta(days=2)
        end_date = str(request.data.get('endDate', def_end_date.strftime('%Y-%m-%d')))
        def_start_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        start_date = str(request.data.get('startDate', def_start_date.strftime('%Y-%m-%d')))
        if start_date > end_date:
            return '', status.HTTP_400_BAD_REQUEST
        flu_model = FluModel.get_model_for_id(id)
        scores = None
        if flu_model is not None:
            scores = ModelScore.get_scores_for_dates(
                id,
                datetime.strptime(start_date, '%Y-%m-%d'),
                datetime.strptime(end_date, '%Y-%m-%d')
            )
        if scores is None:
            return '', status.HTTP_503_SERVICE_UNAVAILABLE
        elif not flu_model:
            return '', status.HTTP_204_NO_CONTENT
        datapoints = []
        for score in scores:
            child = {
                'score_date': score.score_date,
                'score_value': score.score_value
            }
            datapoints.append(child)
        model_parameters = flu_model.get_model_parameters()
        result = {
            'name': flu_model.name,
            'sourceType': flu_model.source_type,
            'displayModel': flu_model.is_displayed,
            'parameters': {
                'georegion': 'e',
                'smoothing': model_parameters['average_window_size']
            },
            'datapoints': datapoints
        }
        return result, status.HTTP_200_OK

    from .google import google_blueprint
    app.register_blueprint(google_blueprint)

    return app

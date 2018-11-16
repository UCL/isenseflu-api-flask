"""
Flask app entry point
"""

from datetime import date, timedelta, datetime
from numbers import Number
from flask import request
from flask_api import FlaskAPI, status
from flask_cors import CORS
from flask_csv import send_csv
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

DB = SQLAlchemy()


def create_app(config_name):
    """ Creates an instance of Flask based on the config name as found in instance/config.py """

    from app.models_query_registry import get_flu_model_for_id, get_public_flu_models, \
        get_model_scores_for_dates, get_model_function, get_default_flu_model, get_default_flu_model_30days, \
        get_rate_thresholds

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.ini', silent=True)
    DB.init_app(app)
    CORS(app)

    @app.route('/', methods=['GET'])
    def root_route():
        """ Default route (/). Returns the last 30 days of model scores for the default flu model """
        model_data, model_scores = get_default_flu_model_30days()
        flu_models = get_public_flu_models()
        if not model_data or not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        model_parameters = get_model_function(model_data['id'])
        datapoints = []
        for score in model_scores:
            child = {
                'score_date': score.score_date.strftime('%Y-%m-%d'),
                'score_value': score.score_value
            }
            if model_parameters.has_confidence_interval:
                confidence_interval = {
                    'confidence_interval_upper': score.confidence_interval_upper,
                    'confidence_interval_lower': score.confidence_interval_lower
                }
                child.update(confidence_interval)
            datapoints.append(child)
        rate_thresholds = get_rate_thresholds(model_data['start_date'])
        model_list = []
        for flu_model in flu_models:
            obj = {
                'id': flu_model.id,
                'name': flu_model.name
            }
            model_list.append(obj)
        result = {
            'id': model_data['id'],
            'name': model_data['name'],
            'hasConfidenceInterval': model_parameters.has_confidence_interval,
            'parameters': {
                'georegion': 'e',
                'smoothing': model_parameters.average_window_size
            },
            'model_list': model_list,
            'start_date': model_data['start_date'].strftime('%Y-%m-%d'),
            'end_date': model_data['end_date'].strftime('%Y-%m-%d'),
            'average_score': model_data['average_score'],
            'rate_thresholds': rate_thresholds,
            'datapoints': datapoints
        }
        return result, status.HTTP_200_OK

    @app.route('/models', methods=['GET'])
    def models_route():
        """ Returns a catalogue of public models """
        flu_models = get_public_flu_models()
        if not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        results = []
        for flu_model in flu_models:
            obj = {
                'id': flu_model.id,
                'name': flu_model.name
            }
            results.append(obj)
        return results, status.HTTP_200_OK

    @app.route('/scores', methods=['GET'])
    def scores_route():
        """ Returns a list of model scores for a model id, start and end date """
        id = int(request.args.get('id'))
        def_end_date = date.today() - timedelta(days=2)
        end_date = str(request.args.get('endDate', def_end_date.strftime('%Y-%m-%d')))
        def_start_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        start_date = str(request.args.get('startDate', def_start_date.strftime('%Y-%m-%d')))
        resolution = str(request.args.get('resolution', 'day'))
        smoothing = int(request.args.get('smoothing', 0))
        if start_date > end_date:
            return '', status.HTTP_400_BAD_REQUEST
        if resolution not in ['day', 'week']:
            return '', status.HTTP_400_BAD_REQUEST
        flu_model = get_flu_model_for_id(id)
        scores = None
        if flu_model is not None:
            scores = get_model_scores_for_dates(
                id,
                datetime.strptime(start_date, '%Y-%m-%d').date(),
                datetime.strptime(end_date, '%Y-%m-%d').date()
            )
        if scores is None:
            return '', status.HTTP_204_NO_CONTENT
        datapoints = []
        if resolution == 'week':
            scores = [s for s in scores if s.score_date.weekday() == 6]
        for score in scores:
            if smoothing == 0:
                score_value = score.score_value
                upper_conf = score.confidence_interval_upper
                lower_conf = score.confidence_interval_lower
            else:
                score_value, upper_conf, lower_conf = score.moving_avg(smoothing)
            child = {
                'score_date': score.score_date.strftime('%Y-%m-%d'),
                'score_value': score_value
            }
            if isinstance(score.confidence_interval_upper, Number) and \
                    isinstance(score.confidence_interval_upper, Number):
                confidence_interval = {
                    'confidence_interval_upper': upper_conf,
                    'confidence_interval_lower': lower_conf
                }
                child.update(confidence_interval)
            datapoints.append(child)
        model_parameters = get_model_function(flu_model.id)
        score_dates = [s.score_date for s in scores]
        rate_thresholds = get_rate_thresholds(min(score_dates))
        result = {
            'id': flu_model.id,
            'name': flu_model.name,
            'sourceType': flu_model.source_type,
            'displayModel': flu_model.is_displayed,
            'hasConfidenceInterval': model_parameters.has_confidence_interval,
            'parameters': {
                'georegion': 'e',
                'smoothing': model_parameters.average_window_size
            },
            'start_date': min(score_dates).strftime('%Y-%m-%d'),
            'end_date': max(score_dates).strftime('%Y-%m-%d'),
            'average_score': sum([s.score_value for s in scores]) / float(len(scores)),
            'rate_thresholds': rate_thresholds,
            'datapoints': datapoints
        }
        return result, status.HTTP_200_OK

    @app.route('/csv/<int:id>', methods=['GET'])
    def csv_route(id):
        """ Returns a list of model scores and dates for a model id, start and end date """
        def_end_date = date.today() - timedelta(days=2)
        end_date = str(request.args.get('endDate', def_end_date.strftime('%Y-%m-%d')))
        def_start_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        start_date = str(request.args.get('startDate', def_start_date.strftime('%Y-%m-%d')))
        if start_date > end_date:
            return '', status.HTTP_400_BAD_REQUEST
        flu_model = get_flu_model_for_id(id)
        scores = None
        if flu_model is not None:
            scores = get_model_scores_for_dates(
                id,
                datetime.strptime(start_date, '%Y-%m-%d').date(),
                datetime.strptime(end_date, '%Y-%m-%d').date()
            )
        if scores is None:
            return '', status.HTTP_204_NO_CONTENT
        datapoints = []
        hasConfidenceInterval = False
        for score in scores:
            child = {
                'score_date': score.score_date.strftime('%Y-%m-%d'),
                'score_value': score.score_value
            }
            if isinstance(score.confidence_interval_upper, Number) and \
                    isinstance(score.confidence_interval_upper, Number):
                confidence_interval = {
                    'confidence_interval_upper': score.confidence_interval_upper,
                    'confidence_interval_lower': score.confidence_interval_lower
                }
                child.update(confidence_interval)
                hasConfidenceInterval = True
            datapoints.append(child)
        fields = ['score_date', 'score_value']
        if hasConfidenceInterval:
            fields.extend(['confidence_interval_upper', 'confidence_interval_lower'])
        return send_csv(datapoints, filename='%s.csv' % flu_model.name, fields=fields), status.HTTP_200_OK

    return app

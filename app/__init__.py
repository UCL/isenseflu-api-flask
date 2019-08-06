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
Flask app entry point
"""

from copy import copy
from datetime import date, timedelta, datetime
from numbers import Number
from flask import request
from flask_api import FlaskAPI, status
from flask_csv import send_csv
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

import hashlib


DB = SQLAlchemy()


def create_app(config_name):
    """ Creates an instance of Flask based on the config name as found in instance/config.py """

    from app.models_query_registry import get_flu_model_for_id, get_public_flu_models, \
        get_model_scores_for_dates, get_model_function, get_default_flu_model, get_default_flu_model_30days, \
        get_rate_thresholds, get_flu_models_for_ids, has_valid_token, set_model_display, get_all_flu_models, \
        get_flu_model_for_model_region_and_dates, get_flu_model_for_model_id_and_dates
    from app.response_template_registry import build_root_plink_twlink_response, build_scores_response

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.ini', silent=True)
    DB.init_app(app)

    @app.route('/', methods=['GET'])
    def root_route():
        """ Default route (/). Returns the last 30 days of model scores for the default flu model """
        model_data, model_scores = get_default_flu_model_30days()
        flu_models = get_public_flu_models()
        if not model_data or not flu_models:
            return '', status.HTTP_204_NO_CONTENT
        response = build_root_plink_twlink_response(
            model_list=flu_models,
            rate_thresholds=get_rate_thresholds(model_data['start_date']),
            model_data=[(model_data, model_scores)]
        )
        if response:
            return response, status.HTTP_200_OK
        return '', status.HTTP_204_NO_CONTENT

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

    @app.route('/plink', methods=['GET'])
    def permalink_route():
        """ Returns the scores and metadata for one or more models in a specific time window """
        if not all(e in request.args for e in ['id', 'startDate', 'endDate']):
            return '', status.HTTP_400_BAD_REQUEST
        resolution = str(request.args.get('resolution', 'day'))
        if resolution not in ['day', 'week']:
            return '', status.HTTP_400_BAD_REQUEST
        smoothing = int(request.args.get('smoothing', 0))
        model_data = []
        start_dates = []
        for id in request.args.getlist('id'):
            mod_data, mod_scores = get_flu_model_for_model_id_and_dates(
                id,
                datetime.strptime(request.args.get('startDate'), '%Y-%m-%d').date(),
                datetime.strptime(request.args.get('endDate'), '%Y-%m-%d').date()
            )
            if resolution == 'week':
                mod_scores = [s for s in mod_scores if s.score_date.weekday() == 6]
            if smoothing != 0:
                smooth_scores = []
                for m in mod_scores:
                    c = copy(m)
                    c.score_value, c.confidence_interval_upper, c.confidence_interval_lower = m.moving_avg(smoothing)
                    smooth_scores.append(c)
                mod_scores = smooth_scores
            model_data.append((mod_data, mod_scores))
            start_dates.append(mod_data['start_date'])
        response = build_root_plink_twlink_response(
            model_list=get_public_flu_models(),
            rate_thresholds=get_rate_thresholds(min(start_dates)),
            model_data=model_data
        )
        if response:
            return response, status.HTTP_200_OK
        return '', status.HTTP_204_NO_CONTENT

    @app.route('/scores', methods=['GET'])
    def scores_route():
        """ Returns a list of model scores for a model id, start and end date """
        if not request.args.getlist('id'):
            return '', status.HTTP_400_BAD_REQUEST
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
        model_data = []
        for id in request.args.getlist('id'):
            mod_data, mod_scores = get_flu_model_for_model_id_and_dates(
                id,
                datetime.strptime(start_date, '%Y-%m-%d').date(),
                datetime.strptime(end_date, '%Y-%m-%d').date()
            )
            if not mod_data or not mod_scores:
                return '', status.HTTP_204_NO_CONTENT
            if resolution == 'week':
                mod_scores = [s for s in mod_scores if s.score_date.weekday() == 6]
            if smoothing != 0:
                smooth_scores = []
                for m in mod_scores:
                    c = copy(m)
                    c.score_value, c.confidence_interval_upper, c.confidence_interval_lower = m.moving_avg(smoothing)
                    smooth_scores.append(c)
                mod_scores = smooth_scores
            model_data.append((mod_data, mod_scores))
        response = build_scores_response(model_data=model_data)
        if response:
            return response, status.HTTP_200_OK
        return '', status.HTTP_204_NO_CONTENT

    @app.route('/twlink', methods=['GET'])
    def twitterlink_route():
        """ Returns the scores and metadata for a model linked from Twitter """
        if not all(e in request.args for e in ['start', 'end']) \
                and not any(e in request.args for e in ['id', 'model_regions-0']):
            return '', status.HTTP_400_BAD_REQUEST
        start_date = datetime.strptime(request.args.get('start'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.args.get('end'), '%Y-%m-%d').date()
        model_data, model_scores = None, None
        if 'id' in request.args:
            model_id = int(request.args.get('id'))
            model_data, model_scores = get_flu_model_for_model_id_and_dates(model_id, start_date, end_date)
        elif 'model_regions-0' in request.args:
            legacy_id = str(request.args.get('model_regions-0'))
            model_data, model_scores = get_flu_model_for_model_region_and_dates(legacy_id, start_date, end_date)
        model_data_list = [(model_data, model_scores)]
        if model_data_list == [(None, None)]:
            model_data_list = []
        response = build_root_plink_twlink_response(
            model_list=get_public_flu_models(),
            rate_thresholds=get_rate_thresholds(model_data['start_date']),
            model_data=model_data_list
        )
        if response:
            return response, status.HTTP_200_OK
        return '', status.HTTP_204_NO_CONTENT

    @app.route('/csv', methods=['GET'])
    def csv_route():
        """ Returns a list of model scores and dates for a model id, start and end date """
        ids = request.args.getlist('id')
        def_end_date = date.today() - timedelta(days=2)
        end_date = str(request.args.get('endDate', def_end_date.strftime('%Y-%m-%d')))
        def_start_date = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=30)
        start_date = str(request.args.get('startDate', def_start_date.strftime('%Y-%m-%d')))
        if start_date > end_date:
            return '', status.HTTP_400_BAD_REQUEST
        flu_models = get_flu_models_for_ids(ids)
        if flu_models is not None and len(flu_models) > 0:
            model_list = []
            date_list = []
            for model in flu_models:
                model_function = get_model_function(model.id)
                model_scores = get_model_scores_for_dates(
                    model.id,
                    datetime.strptime(start_date, '%Y-%m-%d').date(),
                    datetime.strptime(end_date, '%Y-%m-%d').date()
                )
                if model_scores is None:
                    return '', status.HTTP_204_NO_CONTENT
                model_datapoints = []
                for ms in model_scores:
                    child = {
                        'score_date': ms.score_date.strftime('%Y-%m-%d'),
                        'score_value': ms.score_value
                    }
                    if model_function.has_confidence_interval:
                        confidence_interval = {
                            'confidence_interval_upper': ms.confidence_interval_upper,
                            'confidence_interval_lower': ms.confidence_interval_lower
                        }
                        child.update(confidence_interval)
                    model_datapoints.append(child)
                model_list.append({
                    'name': model.name,
                    'datapoints': model_datapoints
                })
                date_list += [d.score_date.strftime('%Y-%m-%d') for d in model_scores if d.score_date not in date_list]
            if len(model_list) == 0:
                return '', status.HTTP_204_NO_CONTENT
            datapoints = []
            for dl in date_list:
                point = dict()
                point['score_date'] = dl
                for md in model_list:
                    score_key = 'score_%s' % md['name']
                    # TODO: should be in try/catch
                    score_value = next(s['score_value'] for s in md['datapoints'] if s['score_date'] == dl)
                    point[score_key] = score_value
                    if 'confidence_interval_upper' in md:
                        conf_upper_key = 'confidence_upper_%s' % md['name']
                        conf_lower_key = 'confidence_lower_%s' % md['name']
                        # TODO: should be in try/catch
                        conf_upper_val = next(
                            s['confidence_interval_upper'] for s in md['datapoints'] if s['score_date'] == dl
                        )
                        conf_lower_val = next(
                            s['confidence_interval_lower'] for s in md['datapoints'] if s['score_date'] == dl
                        )
                        point[conf_upper_key] = conf_upper_val
                        point[conf_lower_key] = conf_lower_val
                datapoints.append(point)
            fields = datapoints[0].keys()
            filename = 'RawScores-%d.csv' % round(datetime.now().timestamp() * 1000)
            return send_csv(datapoints, filename=filename, fields=fields), status.HTTP_200_OK
        return '', status.HTTP_204_NO_CONTENT

    @app.route('/config', methods=['POST'])
    def config_route():
        """ Sets configuration options for models """
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Token '):
            token = request.headers['Authorization'].split()[1]
            sha_token = hashlib.sha256()
            sha_token.update(token.encode('UTF-8'))
            if not has_valid_token(sha_token.hexdigest()):
                return '', status.HTTP_401_UNAUTHORIZED
            if 'model_id' not in request.form or 'is_displayed' not in request.form:
                return 'Parameters missing', status.HTTP_400_BAD_REQUEST
            if set_model_display(int(request.form['model_id']), request.form['is_displayed'] == 'True'):
                return '', status.HTTP_200_OK
        return '', status.HTTP_400_BAD_REQUEST

    @app.route('/allmodels', methods=['GET'])
    def all_models_route():
        """ Lists all models available, public and private """
        if 'Authorization' in request.headers and request.headers['Authorization'].startswith('Token '):
            token = request.headers['Authorization'].split()[1]
            sha_token = hashlib.sha256()
            sha_token.update(token.encode('UTF-8'))
            if not has_valid_token(sha_token.hexdigest()):
                return '', status.HTTP_401_UNAUTHORIZED
            flu_models = get_all_flu_models()
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
        return '', status.HTTP_400_BAD_REQUEST

    return app

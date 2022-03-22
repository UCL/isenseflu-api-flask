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
 Run calculation of Model Scores
"""

from datetime import date, timedelta
from logging import ERROR, INFO, WARNING, log, basicConfig
from os import getenv
from typing import List

from flask_api import FlaskAPI

from app.models_query_registry import get_last_google_date
from .calculator_builder import build_calculator, CalculatorType
from .google_api_client import GoogleApiClient
from .message_client import build_message_client
from .score_query_registry import get_date_ranges_google_score,\
    get_google_batch,\
    set_and_verify_google_dates,\
    set_google_scores,\
    get_dates_missing_model_score,\
    set_and_get_model_score, \
    get_matlab_function_attr,\
    get_moving_averages_or_scores,\
    set_google_scores_except

basicConfig(format='%(asctime)s %(levelname)s : %(message)s', level=INFO)


def run(model_id: int, start: date, end: date):  # pylint: disable=too-many-locals
    """ Calculate the model score for the date range specified """
    missing_google_range, missing_google_list = get_date_ranges_google_score(model_id, start, end)
    if missing_google_range and missing_google_list:
        batch = get_google_batch(model_id, missing_google_range)
        api_client = GoogleApiClient()
        if api_client.is_returning_non_zero_for_temperature(end):
            for terms, start_date, end_date in batch:
                batch_scores = api_client.fetch_google_scores(terms, start_date, end_date)
                if not batch_scores:
                    log(ERROR, 'Retrieval of Google scores failed')
                    raise RuntimeError('Retry call to Google API')
                set_google_scores(batch_scores)
            set_and_verify_google_dates(model_id, missing_google_list)  # Raise an error if missing data
        else:
            log(WARNING, 'Google API has returned zero for the term temperature. Not fetching scores')
    else:
        log(INFO, 'Google scores have already been collected for this time period')
    missing_model_dates = get_dates_missing_model_score(model_id, start, end)
    if missing_model_dates:
        model_function = get_matlab_function_attr(model_id)
        msg_score = None
        msg_date = None
        calculator_type = CalculatorType[getenv('CALCULATOR_TYPE', 'OCTAVE')]
        calculator_engine = build_calculator(calculator_type)
        for missing_model_date in missing_model_dates:
            scores_or_averages = get_moving_averages_or_scores(
                model_id,
                model_function['average_window_size'],
                missing_model_date
            )
            msg_score = set_and_get_model_score(
                model_id,
                calculator_engine,
                (model_function['matlab_function'], model_function['has_confidence_interval']),
                scores_or_averages,
                missing_model_date
            )
            msg_date = missing_model_date
        if getenv('TWITTER_ENABLED') and int(getenv('TWITTER_MODEL_ID')) == model_id:
            mq_client = build_message_client()
            mq_client.publish_model_score(msg_date, msg_score)
            log(INFO, 'Latest ModelScore value sent to message queue')
    else:
        log(INFO, 'Model scores have already been collected for this time period')


def _run_sched_for_model_no_set_dates(model_id:int):
    """ Run calculation of model_score for a particular model without setting dates """
    last_score_date = get_last_google_date(model_id)
    date_assert = date.today() - last_score_date
    assert date_assert.days < 66, "Number of days goes beyond the limit of 2,000 lines for 30 terms"
    expected_end_date = date.today() - timedelta(days=3)  # TODO: remove end date from the API call
    start = last_score_date + timedelta(days=1)
    if last_score_date < expected_end_date:
        missing_google_range, missing_google_list = get_date_ranges_google_score(model_id, start, expected_end_date)
        if missing_google_range and missing_google_list:
            batch = get_google_batch(model_id, missing_google_range)
            api_client = GoogleApiClient()
            for terms, start_date, end_date in batch:
                batch_scores = api_client.fetch_google_scores(terms, last_score_date, end_date)
                assert batch_scores, 'Retrieval of Google scores failed. Retry call to Google API'
                set_google_scores_except(batch_scores, last_score_date)
            set_and_verify_google_dates(model_id, missing_google_list)
    else:
        log(INFO, 'Google scores have already been collected for this time period')
    missing_model_dates = get_dates_missing_model_score(model_id, start, expected_end_date)
    if missing_model_dates:
        model_function = get_matlab_function_attr(model_id)
        msg_score = None
        msg_date = None
        calculator_type = CalculatorType[getenv('CALCULATOR_TYPE', 'OCTAVE')]
        calculator_engine = build_calculator(calculator_type)
        for missing_model_date in missing_model_dates:
            scores_or_averages = get_moving_averages_or_scores(
                model_id,
                model_function['average_window_size'],
                missing_model_date
            )
            msg_score = set_and_get_model_score(
                model_id,
                calculator_engine,
                (model_function['matlab_function'], model_function['has_confidence_interval']),
                scores_or_averages,
                missing_model_date
            )
            msg_date = missing_model_date
        if getenv('TWITTER_ENABLED') and int(getenv('TWITTER_MODEL_ID')) == model_id:
            mq_client = build_message_client()
            mq_client.publish_model_score(msg_date, msg_score)
            log(INFO, 'Latest ModelScore value sent to message queue')
    else:
        log(INFO, 'Model scores have already been collected for this time period')


def runsched(model_id_list: List[int], app: FlaskAPI):
    """ Calculate the model score for the date range specified inside the scheduler """
    with app.app_context():
        for model_id in model_id_list:
            _run_sched_for_model_no_set_dates(model_id)

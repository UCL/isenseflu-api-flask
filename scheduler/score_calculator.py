"""
 Run calculation of Model Scores
"""

from datetime import date
from logging import INFO, log

from .google_api_client import GoogleApiClient
from .score_query_registry import get_date_ranges_google_score,\
    get_google_batch,\
    set_and_verify_google_dates,\
    set_google_scores,\
    get_dates_missing_model_score,\
    set_and_get_model_score


def run(model_id: int, start: date, end: date):
    """ Calculate the model score for the date range specified """
    missing_google_range, missing_google_list = get_date_ranges_google_score(model_id, start, end)
    if missing_google_range and missing_google_list:
        batch = get_google_batch(model_id, missing_google_range)
        api_client = GoogleApiClient()
        for terms, start_date, end_date in batch:
            batch_scores = api_client.fetch_google_scores(terms, start_date, end_date)
            set_google_scores(batch_scores)
        set_and_verify_google_dates(model_id, missing_google_list)  # Raise an error if missing data
    else:
        log(INFO, 'Google scores have already been collected for this time period')
    missing_model_scores = get_dates_missing_model_score(model_id, start, end)
    if missing_model_scores:
        msg_score = None
        msg_date = None
        for missing_model_score in missing_model_scores:
            msg_score = set_and_get_model_score(model_id, missing_model_score)
            msg_date = missing_model_score
        if msg_score is not None and msg_date is not None:
            print(msg_score)
    else:
        log(INFO, 'Model scores have already been collected for this time period')

"""
 Run calculation of Model Scores
"""

from datetime import date

from .google_api_client import GoogleApiClient
from .score_query_registry import get_date_ranges_google_score,\
    get_google_batch,\
    set_and_verify_google_dates,\
    set_google_scores


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

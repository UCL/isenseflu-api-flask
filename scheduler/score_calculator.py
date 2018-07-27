"""
 Run calculation of Model Scores
"""

from datetime import date

from .google_api_client import GoogleApiClient
from .score_query_registry import get_date_ranges_google_score, get_google_batch


def run(model_id: int, start: date, end: date):
    """ Calculate the model score for the date range specified """
    missing_google_dates = get_date_ranges_google_score(model_id, start, end)
    if missing_google_dates:
        batch = get_google_batch(model_id, missing_google_dates)
        api_client = GoogleApiClient()
        for terms, start_date, end_date in batch:
            print("TEST")
        pass

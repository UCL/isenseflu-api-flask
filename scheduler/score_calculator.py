"""
 Run calculation of Model Scores
"""

from datetime import date

from .score_query_registry import get_dates_missing_google_score


def run(model_id: int, start: date, end: date):
    """ Calculate the model score for the date range specified """
    missing_google_dates = get_dates_missing_google_score(model_id, start, end)
    if missing_google_dates:
        pass

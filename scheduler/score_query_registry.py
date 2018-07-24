"""
 Registry of data access functions used in the calculation of model scores
"""

from datetime import date, timedelta

from app.models import get_existing_google_dates


def get_dates_missing_google_score(model_id: int, start: date, end: date) -> list:
    """
    Returns a list of dates within a range missing a Google score. It uses sets to remove duplicates
    """
    existing_google_dates = get_existing_google_dates(model_id, start, end)
    if existing_google_dates:
        known = [d[0] for d in existing_google_dates]
        requested = [start + timedelta(days=d) for d in range((end - start).days + 1)]
        return sorted(set(requested) - set(known))
    return []

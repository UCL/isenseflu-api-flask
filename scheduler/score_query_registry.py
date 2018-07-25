"""
 Registry of data access functions used in the calculation of model scores
"""

from datetime import date, timedelta
from typing import Iterator, List, Tuple

from app.models_query_registry import get_existing_google_dates, get_google_terms_for_model_id

_GOOGLE_TERMS_BATCH_SIZE = 30


def get_dates_missing_google_score(model_id: int, start: date, end: date) -> List[date]:
    """
    Returns a list of dates within a range missing a Google score. It uses sets to remove duplicates
    """
    existing_google_dates = get_existing_google_dates(model_id, start, end)
    if existing_google_dates:
        known = [d[0] for d in existing_google_dates]
        requested = [start + timedelta(days=d) for d in range((end - start).days + 1)]
        return sorted(set(requested) - set(known))
    return []


def get_google_batch(model_id: int, collect_dates: List[date]) -> Iterator[Tuple[List[str], date]]:
    """
    Returns a generator of a list of Google terms and dates to be collected from the API
    organised in batches of up to 30 terms as per API documentation
    """
    google_terms = [t[0] for t in get_google_terms_for_model_id(model_id)]
    for idx in range(0, len(google_terms), _GOOGLE_TERMS_BATCH_SIZE):
        batch = google_terms[idx:idx + _GOOGLE_TERMS_BATCH_SIZE]
        for collect_date in collect_dates:
            yield batch, collect_date

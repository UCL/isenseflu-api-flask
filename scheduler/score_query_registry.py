"""
 Registry of data access functions used in the calculation of model scores
"""

from datetime import date, datetime as dt, timedelta
from typing import Dict, Iterator, List, Tuple, Union

from app.models_query_registry import get_existing_google_dates, get_google_terms_for_model_id, \
    set_google_scores_for_term, set_google_date_for_model_id, get_existing_model_dates, \
    get_google_terms_and_scores, get_google_terms_and_averages, set_model_score, \
    set_model_score_confidence_interval, get_model_function
from .google_batch import GoogleBatch
from .matlab_client import MatlabClient


def get_days_missing_google_score(model_id: int, start: date, end: date) -> int:
    """
    Returns number of days within a range missing a Google score. It uses sets to remove duplicates
    """
    existing_google_dates = get_existing_google_dates(model_id, start, end)
    if existing_google_dates:
        known = [d[0] for d in existing_google_dates]
        requested = [start + timedelta(days=d) for d in range((end - start).days + 1)]
        return len(set(requested) - set(known))
    return 0


def get_date_ranges_google_score(
        model_id: int,
        start: date,
        end: date
) -> Tuple[List[Tuple[date, date]], List[date]]:
    """
    Returns a list of ranges (as tuples containing start and end date) for which the Google
    scores are missing, along with the same dates as a list (one date per item)
    It uses sets to remove duplicates
    """
    existing_google_dates = get_existing_google_dates(model_id, start, end)
    requested = [start + timedelta(days=d) for d in range((end - start).days + 1)]
    if existing_google_dates:
        known = [d[0] for d in existing_google_dates]
        date_list = sorted(set(requested) - set(known))
        if not date_list:
            return [], []
        start_id = 0
        date_ranges = []
        for idx in range(len(date_list) - 1):
            if (date_list[idx + 1] - date_list[idx]).days > 1:
                date_ranges.append((date_list[start_id], date_list[idx]))
                start_id = idx + 1
        date_ranges.append((date_list[start_id], date_list[len(date_list) - 1]))
        return date_ranges, list(date_list)
    dates_as_range = [(start, end)]
    return dates_as_range, requested


def get_google_batch(
        model_id: int,
        collect_dates: List[Tuple[date, date]]
) -> Iterator[Tuple[List[str], date, date]]:
    """
    Returns a generator of a list of Google terms and dates to be collected from the API
    organised in batches of up to 30 terms as per API documentation
    """
    google_terms = [t[0] for t in get_google_terms_for_model_id(model_id)]
    google_batch = GoogleBatch(google_terms, collect_dates)
    return google_batch.get_batch()


def set_google_scores(
        google_scores: List[Dict[str, Union[str, List[Dict[str, Union[str, float]]]]]]
):
    """
    Iterates through the batch item to reformat the data points from dictionary to a tuple
    before persisting the data. It parses the data converting it into a datetime.date
    """
    for batch_item in google_scores:
        points = [
            (dt.strptime(p['date'], '%b %d %Y').date(), p['value']) for p in batch_item['points']
        ]
        set_google_scores_for_term(batch_item['term'], points)


def set_and_verify_google_dates(model_id: int, google_dates: List[date]):
    """
    Persists the date of a complete set of scores if retrieved for all terms in a model
    """
    for google_date in google_dates:
        set_google_date_for_model_id(model_id, google_date)


def get_dates_missing_model_score(model_id: int, start: date, end: date) -> List[date]:
    """
    Returns all the dates within a range without a model score.
    """
    existing_model_dates = get_existing_model_dates(model_id, start, end)
    requested = [start + timedelta(days=d) for d in range((end - start).days + 1)]
    if existing_model_dates:
        known = [d[0] for d in existing_model_dates]
        return sorted(set(requested) - set(known))
    return requested


def get_moving_averages_or_scores(
        model_id: int,
        avg_window_size: int,
        for_date: date
) -> List[Tuple[str, float]]:
    """
    Calculates moving averages based on the average window configured in the model
    """
    if avg_window_size == 1:
        return get_google_terms_and_scores(model_id, for_date)
    return get_google_terms_and_averages(model_id, avg_window_size, for_date)


def set_and_get_model_score(
        model_id: int,
        matlab_client: MatlabClient,
        matlab_function: Tuple[str, bool],
        google_scores: List[Tuple[str, float]],
        score_date: date
) -> float:
    """
    Calculates and persists the model score for a date
    """
    with_confidence_interval = matlab_function[1]
    if not with_confidence_interval:
        score = matlab_client.calculate_model_score(matlab_function[0], google_scores)
        set_model_score(model_id, score_date, score)
        return score
    score, lower, upper = matlab_client.calculate_model_score_and_confidence(
        matlab_function[0],
        google_scores
    )
    set_model_score_confidence_interval(model_id, score_date, score, (lower, upper))
    return score


def get_matlab_function_attr(model_id: int) -> Dict[str, Union[str, float, bool]]:
    """
    Returns a dictionary with the definition parameters of the function used in Matlab
    to calculate the model score
    """
    model_function = get_model_function(model_id)
    return {
        'matlab_function': model_function.function_name,
        'average_window_size': model_function.average_window_size,
        'has_confidence_interval': model_function.has_confidence_interval
    }

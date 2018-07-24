"""
 Run calculation of Model Scores
"""

import datetime

from app.models import get_existing_google_dates


def run(model_id: int, start: datetime.date, end: datetime.date):
    if get_existing_google_dates(model_id, start, end):
        return
    pass

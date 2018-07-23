"""
 Run calculation of Model Scores
"""

import datetime

from app.models import has_missing_google_scores


def run(model_id: int, start: datetime.date, end: datetime.date):
    if has_missing_google_scores(model_id, start, end):
        return
    pass

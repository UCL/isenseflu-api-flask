"""
 Registry of data access functions used to retrieve data from the ORM definitions
 in models.py
"""

from datetime import date, timedelta
from typing import Dict, List, Tuple, Union

from sqlalchemy.sql import func

from app import DB
from app.models import FluModel, ModelScore, GoogleDate, GoogleScore, GoogleTerm, FluModelGoogleTerm, \
    ModelFunction


def get_flu_model_for_id(model_id: int) -> FluModel:
    """ Searches a model by its id """
    return FluModel.query.filter_by(id=model_id).first()


def get_public_flu_models() -> List[FluModel]:
    """ Returns all public models """
    return FluModel.query.filter_by(is_public=True).all()


def get_model_scores_for_dates(model_id: int, start_date: date, end_date: date) -> List[ModelScore]:
    """ Returns a list of model scores for a model id, start and end date """
    return ModelScore.query.filter(
        ModelScore.flu_model_id == model_id,
        ModelScore.score_date >= start_date,
        ModelScore.score_date <= end_date
    ).all()


def has_model(model_id) -> bool:
    """ Checks if the model exists """
    return DB.session.query(FluModel.query.filter_by(id=model_id).exists()).scalar()


def get_last_score_date(model_id) -> DB.Date:
    """ Returns the last score date for a particular model """
    return ModelScore.query.filter_by(flu_model_id=model_id)\
        .order_by(ModelScore.score_date.desc())\
        .first()\
        .score_date


def get_existing_google_dates(model_id: int, start: date, end: date) -> List[Tuple[date]]:
    """ Returns dates with existing Google scores for a particular model ID between two dates """
    return DB.session.query(GoogleDate.score_date).distinct()\
        .filter(GoogleDate.flu_model_id == model_id)\
        .filter(GoogleDate.score_date >= start)\
        .filter(GoogleDate.score_date <= end)\
        .all()


def get_google_terms_for_model_id(model_id: int) -> List[Tuple[str]]:
    """ Returns Google terms for which a model was created against """
    return DB.session.query(GoogleTerm.term)\
        .join(FluModelGoogleTerm)\
        .filter(FluModelGoogleTerm.flu_model_id == model_id)\
        .all()


def set_google_scores_for_term(term: str, points: List[Tuple[date, float]]):
    """ Persists score data (date, score) for a particular term """
    term_id = GoogleTerm.query.filter_by(term=term).first().id
    for point in points:
        entity_exists = GoogleScore.query\
            .filter(GoogleScore.score_date == point[0])\
            .filter(GoogleScore.term_id == term_id).exists()
        if not DB.session.query(entity_exists).scalar():
            google_score = GoogleScore(term_id=term_id, score_date=point[0], score_value=point[1])
            DB.session.add(google_score)
    DB.session.commit()


def set_google_date_for_model_id(model_id: int, google_date: date):
    """ Persists the score date if scores have been retrieved successfully for all terms """
    query_terms = FluModelGoogleTerm.query.filter_by(flu_model_id=model_id).count()
    query_dates = DB.session.query(GoogleScore.term_id).distinct()\
        .join(GoogleTerm)\
        .join(FluModelGoogleTerm)\
        .filter(FluModelGoogleTerm.flu_model_id == model_id)\
        .filter(GoogleScore.score_date == google_date)\
        .count()
    if query_terms != query_dates:
        raise ValueError('Terms with missing scores for date %s' % google_date)
    google_date = GoogleDate(model_id, google_date)
    google_date.save()


def get_existing_model_dates(model_id: int, start: date, end: date) -> List[Tuple[date]]:
    """ Returns dates with existing model scores for a particular model ID between two dates """
    return DB.session.query(ModelScore.score_date).distinct()\
        .filter(ModelScore.flu_model_id == model_id)\
        .filter(ModelScore.score_date >= start)\
        .filter(ModelScore.score_date <= end)\
        .all()


def set_model_score(model_id: int, score_date: date, score_value: float):
    """ Persists a model score entity """
    model_score = ModelScore()
    model_score.flu_model_id = model_id
    model_score.region = 'e'  # Default for Google data
    model_score.score_date = score_date
    model_score.score_value = score_value
    model_score.save()


def set_model_score_confidence_interval(
        model_id: int,
        score_date: date,
        score_value: float,
        confidence_interval: Tuple[float, float]
):
    """ Persists a model score entity including its confidence interval """
    model_score = ModelScore()
    model_score.flu_model_id = model_id
    model_score.region = 'e'  # Default for Google data
    model_score.score_date = score_date
    model_score.score_value = score_value
    model_score.confidence_interval_lower = confidence_interval[0]
    model_score.confidence_interval_upper = confidence_interval[1]
    model_score.save()


def get_model_function(model_id: int) -> ModelFunction:
    """ Return the model parameters """
    return ModelFunction.query.filter_by(flu_model_id=model_id).first()


def get_google_terms_and_scores(model_id: int, score_date: date) -> List[Tuple[str, float]]:
    """ Returns the scores for each term for a date """
    return DB.session.query(GoogleTerm.term, GoogleScore.score_value)\
        .join(GoogleScore)\
        .join(FluModelGoogleTerm)\
        .filter(GoogleScore.score_date == score_date)\
        .filter(FluModelGoogleTerm.flu_model_id == model_id)\
        .all()


def get_google_terms_and_averages(
        model_id: int,
        window_size: int,
        score_date:date
) -> List[Tuple[str, float]]:
    """ Returns the average scores for each term for a date window """
    start_date = score_date - timedelta(days=window_size)
    return DB.session.query(GoogleTerm.term, func.avg(GoogleScore.score_value).label('avg_score'))\
        .join(GoogleScore)\
        .join(FluModelGoogleTerm)\
        .filter(GoogleScore.score_date > start_date)\
        .filter(GoogleScore.score_date <= score_date)\
        .filter(FluModelGoogleTerm.flu_model_id == model_id)\
        .group_by(GoogleTerm.term)\
        .all()

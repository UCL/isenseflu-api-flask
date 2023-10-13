# i-sense flu api: REST API, and data processors for the i-sense flu service from UCL.
# (c) 2019, UCL <https://www.ucl.ac.uk/
#
# This file is part of i-sense flu api
#
# i-sense flu api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# i-sense flu api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with i-sense flu api.  If not, see <http://www.gnu.org/licenses/>.

"""
 Registry of data access functions used to retrieve data from the ORM definitions
 in models.py
"""

# pylint: disable=no-member
from datetime import date, timedelta
from typing import List, Tuple, Dict

from sqlalchemy.sql import func

from app import DB
from app.models import FluModel, ModelScore, GoogleDate, GoogleScore, GoogleTerm, \
    FluModelGoogleTerm, ModelFunction, DefaultFluModel, RateThresholdSet, TokenInfo


def get_default_flu_model_half_year() -> Tuple[Dict, List[ModelScore]]:
    """ Returns the last half a year of data for the default Flu Model """
    default_flu_model = FluModel.query.filter_by(is_public=True, is_displayed=True)\
        .join(DefaultFluModel)\
        .filter(DefaultFluModel.flu_model_id == FluModel.id)\
        .first()
    if not default_flu_model:
        return None, None
    model_scores = ModelScore.query.filter(ModelScore.flu_model_id == default_flu_model.id)\
        .order_by(ModelScore.score_date.desc())\
        .limit(182)\
        .all()
    if not model_scores:
        return None, None
    flu_model_meta = __build_flu_model_meta(default_flu_model, model_scores)
    return flu_model_meta, model_scores


def get_flu_model_for_model_region_and_dates(
        model_region_id: str,
        start_date: date,
        end_date: date
) -> Tuple[Dict, List[ModelScore]]:
    """ Returns model data for the period start_date to end_date
    and corresponding model_region_id
    """
    flu_model = FluModel.query.filter_by(
        is_public=True, is_displayed=True, model_region_id=model_region_id
    ).first()
    if not flu_model:
        return None, None
    model_scores = ModelScore.query.filter(
        ModelScore.flu_model_id == flu_model.id,
        ModelScore.score_date >= start_date,
        ModelScore.score_date <= end_date
    ).order_by(ModelScore.score_date.desc()).all()
    if not model_scores:
        return None, None
    flu_model_meta = __build_flu_model_meta(flu_model, model_scores)
    return flu_model_meta, model_scores


def get_flu_model_for_model_id_and_dates(
        model_id: int,
        start_date: date,
        end_date: date
) -> Tuple[Dict, List[ModelScore]]:
    """ Returns model data for the period start_date to end_date and corresponding model_id """
    flu_model = FluModel.query.filter_by(is_public=True, is_displayed=True, id=model_id).first()
    if not flu_model:
        return None, None
    model_scores = ModelScore.query.filter(
        ModelScore.flu_model_id == flu_model.id,
        ModelScore.score_date >= start_date,
        ModelScore.score_date <= end_date
    ).order_by(ModelScore.score_date.desc()).all()
    if not model_scores:
        return None, None
    flu_model_meta = __build_flu_model_meta(flu_model, model_scores)
    return flu_model_meta, model_scores


def get_default_flu_model() -> FluModel:
    """ Returns the default Flu Model """
    return FluModel.query.filter_by(is_public=True, is_displayed=True)\
        .join(DefaultFluModel)\
        .filter(DefaultFluModel.flu_model_id == FluModel.id)\
        .first()


def get_flu_model_for_id(model_id: int) -> FluModel:
    """ Searches a model by its id """
    return FluModel.query.filter_by(id=model_id).first()


def get_flu_models_for_ids(model_ids: [int]) -> List[FluModel]:
    """ Searches flu models by ids """
    return FluModel.query.filter(FluModel.id.in_(model_ids)).all()


def get_public_flu_models() -> List[FluModel]:
    """ Returns all public models """
    return FluModel.query.filter_by(is_public=True).all()


def get_all_flu_models() -> List[FluModel]:
    """ Returns all models, public and private """
    return FluModel.query.all()


def get_model_scores_for_dates(model_id: int, start_date: date, end_date: date) -> List[ModelScore]:
    """ Returns a list of model scores for a model id, start and end date """
    return ModelScore.query.filter(
        ModelScore.flu_model_id == model_id,
        ModelScore.score_date >= start_date,
        ModelScore.score_date <= end_date
    ).order_by(ModelScore.score_date.desc()).all()


def has_model(model_id) -> bool:
    """ Checks if the model exists """
    return DB.session.query(FluModel.query.filter_by(id=model_id).exists()).scalar()


def get_last_score_date(model_id) -> DB.Date:
    """ Returns the last score date for a particular model """
    return ModelScore.query.filter_by(flu_model_id=model_id)\
        .order_by(ModelScore.score_date.desc())\
        .first()\
        .score_date


def get_last_google_date(model_id: int) -> DB.Date:
    """ Returns the last Google date for a particular model """
    return GoogleDate.query.filter_by(flu_model_id=model_id)\
        .order_by(GoogleDate.score_date.desc())\
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
        score_date: date
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


def get_rate_thresholds(
        start_date: date
) -> Dict[str, Dict]:
    """ Returns the current set of rate thresholds """
    result_set = DB.session.query(
        RateThresholdSet.low_value,
        RateThresholdSet.medium_value,
        RateThresholdSet.high_value,
        RateThresholdSet.very_high_value)\
        .filter(RateThresholdSet.valid_from <= start_date)\
        .filter(
            (RateThresholdSet.valid_until >= start_date) | (RateThresholdSet.valid_until.is_(None))
        )\
        .first()
    if result_set is not None:
        return {
            "low_value": {
                "label": "Low epidemic rate",
                "value": result_set[0]
            },
            "medium_value": {
                "label": "Medium epidemic rate",
                "value": result_set[1]
            },
            "high_value": {
                "label": "High epidemic rate",
                "value": result_set[2]
            },
            "very_high_value": {
                "label": "Very high epidemic rate",
                "value": result_set[3]
            }
        }
    return {}


def has_valid_token(token: str) -> bool:
    """ Checks if token is valid """
    return DB.session.query(TokenInfo.query.filter_by(token=token, is_valid=True).exists()).scalar()


def set_model_display(model_id: int, display: bool) -> bool:
    """ Configures model to be displayed or hidden on/from the website """
    rows = FluModel.query.filter_by(id=model_id).update(dict(is_public=display))
    DB.session.commit()
    if rows == 1:
        return True
    return False


def __build_flu_model_meta(flu_model: FluModel, model_scores: List[ModelScore]) -> Dict:
    scores = [s.score_value for s in model_scores]
    model_function = ModelFunction.query.filter_by(flu_model_id=flu_model.id).first()
    return {
        'id': flu_model.id,
        'name': flu_model.name,
        'average_score': sum(scores) / float(len(scores)),
        'has_confidence_interval': model_function.has_confidence_interval,
        'start_date': model_scores[-1].score_date,
        'end_date': model_scores[0].score_date
    }

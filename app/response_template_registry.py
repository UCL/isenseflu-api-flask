"""
 Registry of templating functions for the construction of JSON responses to be returned by the Flask API
"""

from typing import Dict, List, Tuple

from app.models import FluModel, ModelScore


def build_root_plink_twlink_response(
        model_list: List[FluModel],
        rate_thresholds: Dict[str, Dict],
        model_data: List[Tuple[Dict, List[ModelScore]]]) -> Dict:
    """
    Constructs response for a message that contains the list of all public models, rate thresholds and the metadata
    and scores selected
    :param model_list: as returned by app.models_query_registry.get_public_flu_models
    :param rate_thresholds:
    :param model_data:
    :return: a dictionary with the data in serialisable form
    """
    flu_model_list = []
    for flu_model in model_list:
        obj = {
            'id': flu_model.id,
            'name': flu_model.name
        }
        flu_model_list.append(obj)
    response = {
        'model_list': flu_model_list,
        'rate_thresholds': rate_thresholds,
        'model_data': __build_model_data(model_data)
    }
    return response


def build_scores_response(model_data: List[Tuple[Dict, List[ModelScore]]]) -> Dict:
    """
    Constructs response for a message that contains metadata and scores for a list of flu models
    :param model_data:
    :return: a dictionary with the data in serialisable form
    """
    response = {
        'model_data': __build_model_data(model_data)
    }
    return response


def __build_model_data(model_data: List[Tuple[Dict, List[ModelScore]]]) -> List:
    """
    Constructs list of dictionaries containing metadata and scores from flu models
    :param model_data:
    :return: a list with the model metadata and scores
    """
    flu_model_data = []
    for model_data_item, model_scores_item in model_data:
        converted_model_scores = [
            {
                'score_date': s.score_date.strftime('%Y-%m-%d'),
                'score_value': s.score_value,
                'confidence_interval_lower': s.confidence_interval_lower,
                'confidence_interval_upper': s.confidence_interval_upper
            } for s in model_scores_item
        ]
        model_data_item['data_points'] = converted_model_scores
        model_data_item['start_date'] = model_data_item['start_date'].strftime('%Y-%m-%d')
        model_data_item['end_date'] = model_data_item['end_date'].strftime('%Y-%m-%d')
        flu_model_data.append(model_data_item)
    return flu_model_data

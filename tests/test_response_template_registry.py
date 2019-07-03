"""
 Test templating functions for the construction of JSON responses to be returned by the Flask API
"""

from datetime import date
from unittest import TestCase

from app.models import FluModel, ModelScore
from app.response_template_registry import build_root_plink_twlink_response, build_scores_response


class ResponsesTestCase(TestCase):
    """ Test case for response_template_registry.py """

    def test_build_root_plink_twlink_response(self):
        model_list = [
            {'id': 1, 'name': 'Test Model'},
            {'id': 2, 'name': 'Another Test Model'}
        ]
        rate_thresholds = {
            'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4},
            'high_value': {'label': 'High epidemic rate', 'value': 0.3},
            'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
            'low_value': {'label': 'Low epidemic rate', 'value': 0.1}
        }
        data_points = [
            {'score_date': '2019-01-01', 'score_value': 0.2, 'confidence_interval_lower': 0.1,
             'confidence_interval_upper': 0.5},
            {'score_date': '2019-01-02', 'score_value': 0.4, 'confidence_interval_lower': 0.1,
             'confidence_interval_upper': 0.5}
        ]
        model_data = [{
            'id': 1,
            'name': 'Test Model',
            'start_date': '2019-01-01',
            'end_date': '2019-01-02',
            'average_score': 0.3,
            'has_confidence_interval': True,
            'data_points': data_points
        }]
        expected = {
            'model_list': model_list,
            'rate_thresholds': rate_thresholds,
            'model_data': model_data
        }
        flu_model_1, flu_model_2 = FluModel(), FluModel()
        flu_model_1.id, flu_model_2.id = 1, 2
        flu_model_1.name, flu_model_2.name = 'Test Model', 'Another Test Model'
        flu_model_list = [flu_model_1, flu_model_2]
        flu_model_score_1, flu_model_score_2 = ModelScore(), ModelScore()
        flu_model_score_1.score_date, flu_model_score_2.score_date = date(2019, 1, 1), date(2019, 1, 2)
        flu_model_score_1.score_value, flu_model_score_2.score_value = 0.2, 0.4
        flu_model_score_1.confidence_interval_lower, flu_model_score_2.confidence_interval_lower = 0.1, 0.1
        flu_model_score_1.confidence_interval_upper, flu_model_score_2.confidence_interval_upper = 0.5, 0.5
        flu_model_data = [(
            {
                'id': 1,
                'name': 'Test Model',
                'start_date': date(2019, 1, 1),
                'end_date': date(2019, 1, 2),
                'has_confidence_interval': True,
                'average_score': 0.3
            },
            [flu_model_score_1, flu_model_score_2]
        )]
        result = build_root_plink_twlink_response(flu_model_list, rate_thresholds, flu_model_data)
        self.assertEquals(result, expected)

    def test_build_scores_response(self):
        data_points = [
            {'score_date': '2019-01-01', 'score_value': 0.2, 'confidence_interval_lower': 0.1,
             'confidence_interval_upper': 0.5},
            {'score_date': '2019-01-02', 'score_value': 0.4, 'confidence_interval_lower': 0.1,
             'confidence_interval_upper': 0.5}
        ]
        model_data = [{
            'id': 1,
            'name': 'Test Model',
            'start_date': '2019-01-01',
            'end_date': '2019-01-02',
            'average_score': 0.3,
            'has_confidence_interval': True,
            'data_points': data_points
        }]
        expected = {'model_data': model_data}
        flu_model_score_1, flu_model_score_2 = ModelScore(), ModelScore()
        flu_model_score_1.score_date, flu_model_score_2.score_date = date(2019, 1, 1), date(2019, 1, 2)
        flu_model_score_1.score_value, flu_model_score_2.score_value = 0.2, 0.4
        flu_model_score_1.confidence_interval_lower, flu_model_score_2.confidence_interval_lower = 0.1, 0.1
        flu_model_score_1.confidence_interval_upper, flu_model_score_2.confidence_interval_upper = 0.5, 0.5
        flu_model_data = [(
            {
                'id': 1,
                'name': 'Test Model',
                'start_date': date(2019, 1, 1),
                'end_date': date(2019, 1, 2),
                'has_confidence_interval': True,
                'average_score': 0.3
            },
            [flu_model_score_1, flu_model_score_2]
        )]
        result = build_scores_response(flu_model_data)
        self.assertDictEqual(result, expected)

from unittest import TestCase
from datetime import date, datetime

from app import create_app, DB
from app.models import FluModel, ModelScore, ModelFunction, DefaultFluModel, TokenInfo, RateThresholdSet


class InitRoutesTestCase(TestCase):
    """Test case for the app routes (app.__init__)"""

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_root_no_models(self):
        response = self.client().get('/')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def test_get_rool(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        datapoint = ModelScore()
        datapoint.region = 'e'
        datapoint.score_date = date(2018, 6, 29)
        datapoint.calculation_timestamp = datetime.now()
        datapoint.score_value = 1.23
        datapoint.confidence_interval_lower = 0.81
        datapoint.confidence_interval_upper = 1.65
        flumodel.model_scores = [datapoint]
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        default_model = DefaultFluModel()
        default_model.flu_model_id = 1
        with self.app.app_context():
            flumodel.save()
            model_function.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/')
        result = response.get_json()
        expected = {
            'model_list': [{'id': 1, 'name': 'Test Model'}],
            'rate_thresholds': {},
            'model_data': [
                {
                    'id': 1,
                    'name': 'Test Model',
                    'average_score': 1.23,
                    'start_date': '2018-06-29',
                    'end_date': '2018-06-29',
                    'has_confidence_interval': True,
                    'data_points': [
                        {
                            'score_date': '2018-06-29',
                            'score_value': 1.23,
                            'confidence_interval_lower': 0.81,
                            'confidence_interval_upper': 1.65
                        }
                    ]
                }
            ]
        }
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)

    def test_get_models(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        with self.app.app_context():
            flumodel.save()
        response = self.client().get('/models')
        result = response.get_json()
        expected = [{
            'id': 1,
            'name': 'Test Model'
        }]
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)

    def test_get_models_no_content(self):
        response = self.client().get('/models')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def test_get_scores_for_model(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        dates = [date(2018, 3, 20), date(2018, 5, 20), date(2018, 6, 20)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = '1.23'
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        with self.app.app_context():
            flumodel.save()
            model_function.save()
        response = self.client().get('/scores?id=1&startDate=2018-05-30&endDate=2018-06-30')
        result = response.get_json()
        expected = {
            'modeldata': [
                {
                    'id': 1,
                    'name': 'Test Model',
                    'average_score': 1.23,
                    'hasConfidenceInterval': True,
                    'datapoints': [
                        {
                            'score_date': '2018-06-20',
                            'score_value': 1.23
                        }
                    ]
                }
            ],
            'start_date': '2018-06-20',
            'end_date': '2018-06-20',
            'rate_thresholds': {},
            'dates': ['2018-06-20']
        }
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)
        response = self.client().get('/scores?id=1&startDate=2018-07-30&endDate=2018-06-30')
        self.assertEqual(response.status_code, 400)

    def test_get_scores_resolution(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        dates = [date(2018, 6, d) for d in range(1, 30)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = '1.23'
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        with self.app.app_context():
            flumodel.save()
            model_function.save()
        response = self.client().get('/scores?id=1&startDate=2018-05-30&endDate=2018-06-30&resolution=week')
        result = response.get_json()
        self.assertEqual(len(result['modeldata'][0]['datapoints']), 4)

    def test_get_scores_smoothing(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        dates = [date(2018, 6, d) for d in range(1, 30)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = 1 + 10 / d.day
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        with self.app.app_context():
            flumodel.save()
            model_function.save()
        response = self.client().get('/scores?id=1&startDate=2018-06-10&endDate=2018-06-10&smoothing=3')
        result = response.get_json()
        expected = {
            'rate_thresholds': {},
            'modeldata': [
                {
                    'id': 1,
                    'name': 'Test Model',
                    'datapoints': [
                        {
                            'score_value': 2.0067340067340065,
                            'score_date': '2018-06-10',
                            'confidence_interval_lower': 0.0,   # should be None
                            'confidence_interval_upper': 0.0    # should be None
                        }
                    ],
                    'hasConfidenceInterval': True,
                    'average_score': 2.0
                }
            ],
            'start_date': '2018-06-10',
            'end_date': '2018-06-10',
            'dates': ['2018-06-10']
        }
        self.assertEqual(result, expected)

    def test_csv(self):
        flumodel = FluModel()
        flumodel.id = 1
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        dates = [date(2018, 6, d) for d in range(1, 30)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = 1 + 10 / d.day
            entry.confidence_interval_lower = 0
            entry.confidence_interval_upper = 2
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        with self.app.app_context():
            flumodel.save()
            model_function.save()
            response = self.client().get('/csv?id=1&tartDate=2018-06-10&endDate=2018-06-10')
            expected = r'attachment; filename=RawScores-\d{13}\.csv'
            self.assertRegexpMatches(response.headers['Content-Disposition'], expected)

    def test_post_config(self):
        flumodel = FluModel()
        flumodel.id = 1
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        token_info = TokenInfo()
        token_info.token_id = 1
        token_info.token = '79e11f5137ab996c5e202dc0166a68d4e3bece0af5b39c30705905210ee6e9a4'
        token_info.is_valid = True
        token_info.token_user = 'Test User'
        with self.app.app_context():
            flumodel.save()
            token_info.save()
        response = self.client().post(
            '/config',
            data=dict(model_id=1, is_displayed=True),
            headers={'Authorization': 'Token 5GOngP4EbHiwA4R32bv516tpKkBEAOl8'}
        )
        self.assertEqual(response.status_code, 200)

    def test_get_scores_no_content(self):
        response = self.client().get('/scores?id=1')
        result = response.data
        self.assertEqual(result, b'')
        self.assertEqual(response.status_code, 204)

    def test_get_all_models(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = False
        flumodel.is_displayed = False
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        token_info = TokenInfo()
        token_info.token_id = 1
        token_info.token = '79e11f5137ab996c5e202dc0166a68d4e3bece0af5b39c30705905210ee6e9a4'
        token_info.is_valid = True
        token_info.token_user = 'Test User'
        with self.app.app_context():
            flumodel.save()
            token_info.save()
        response = self.client().get('/allmodels', headers={'Authorization': 'Token 5GOngP4EbHiwA4R32bv516tpKkBEAOl8'})
        result = response.get_json()
        expected = [{
            'id': 1,
            'name': 'Test Model'
        }]
        self.assertEqual(result, expected)
        self.assertEqual(response.status_code, 200)

    def test_get_twlink_no_query_params(self):
        response = self.client().get('/twlink')
        self.assertEqual(response.status_code, 400)

    def test_get_twlink(self):
        flumodel = FluModel()
        flumodel.name = 'Test Model'
        flumodel.is_public = True
        flumodel.is_displayed = True
        flumodel.source_type = 'google'
        flumodel.calculation_parameters = 'matlab_model,1'
        flumodel.model_region_id = '1-e'
        dates = [date(2018, 6, d) for d in range(1, 30)]
        datapoints = []
        for d in dates:
            entry = ModelScore()
            entry.region = 'e'
            entry.score_date = d
            entry.calculation_timestamp = datetime.now()
            entry.score_value = 1.23
            entry.confidence_interval_lower = 0.81
            entry.confidence_interval_upper = 1.65
            datapoints.append(entry)
        flumodel.model_scores = datapoints
        model_function = ModelFunction()
        model_function.id = 1
        model_function.function_name = 'matlab_model'
        model_function.average_window_size = 1
        model_function.flu_model_id = 1
        model_function.has_confidence_interval = True
        default_model = DefaultFluModel()
        default_model.flu_model_id = 1
        rate_thresholds = RateThresholdSet()
        rate_thresholds.low_value = 0.1
        rate_thresholds.medium_value = 0.2
        rate_thresholds.high_value = 0.3
        rate_thresholds.very_high_value = 0.4
        rate_thresholds.valid_from = date(2010, 1, 1)
        with self.app.app_context():
            flumodel.save()
            model_function.save()
            rate_thresholds.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/twlink?model_regions-0=1-e&start=2018-06-01&end=2018-06-10')
        self.assertListEqual(response.get_json()['model_list'], [{'id': 1, 'name': 'Test Model'}])
        self.assertEqual(len(response.get_json()['model_data'][0]['data_points']), 10)
        expected = {
            'low_value': {'label': 'Low epidemic rate', 'value': 0.1},
            'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
            'high_value': {'label': 'High epidemic rate', 'value': 0.3},
            'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4}
        }
        self.assertDictEqual(response.get_json()['rate_thresholds'], expected)

    def test_get_plink_no_query_params(self):
        response = self.client().get('/plink')
        self.assertEqual(response.status_code, 400)

    def test_get_plink(self):
        with self.app.app_context():
            for idx in [1, 2]:
                flumodel = FluModel()
                flumodel.name = 'Test Model %d' % idx
                flumodel.is_public = True
                flumodel.is_displayed = True
                flumodel.source_type = 'google'
                flumodel.calculation_parameters = 'matlab_model,1'
                dates = [date(2018, 6, d) for d in range(1, 30)]
                datapoints = []
                for d in dates:
                    entry = ModelScore()
                    entry.region = 'e'
                    entry.score_date = d
                    entry.calculation_timestamp = datetime.now()
                    entry.score_value = 1.23 / idx
                    entry.confidence_interval_lower = 0.81
                    entry.confidence_interval_upper = 1.65
                    datapoints.append(entry)
                flumodel.model_scores = datapoints
                model_function = ModelFunction()
                model_function.id = idx
                model_function.function_name = 'matlab_model'
                model_function.average_window_size = 1
                model_function.flu_model_id = idx
                model_function.has_confidence_interval = True
                flumodel.save()
                model_function.save()
            default_model = DefaultFluModel()
            default_model.flu_model_id = 1
            rate_thresholds = RateThresholdSet()
            rate_thresholds.low_value = 0.1
            rate_thresholds.medium_value = 0.2
            rate_thresholds.high_value = 0.3
            rate_thresholds.very_high_value = 0.4
            rate_thresholds.valid_from = date(2010, 1, 1)
            rate_thresholds.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/plink?id=1&id=2&startDate=2018-06-01&endDate=2018-06-10')
        self.assertListEqual(
            response.get_json()['model_list'],
            [{'id': 1, 'name': 'Test Model 1'}, {'id': 2, 'name': 'Test Model 2'}]
        )
        self.assertEqual(len(response.get_json()['model_data'][0]['data_points']), 10)
        self.assertEqual(len(response.get_json()['model_data'][1]['data_points']), 10)
        expected = {
            'low_value': {'label': 'Low epidemic rate', 'value': 0.1},
            'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
            'high_value': {'label': 'High epidemic rate', 'value': 0.3},
            'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4}
        }
        self.assertDictEqual(response.get_json()['rate_thresholds'], expected)

    def test_get_plink_resolution(self):
        with self.app.app_context():
            for idx in [1, 2]:
                flumodel = FluModel()
                flumodel.name = 'Test Model %d' % idx
                flumodel.is_public = True
                flumodel.is_displayed = True
                flumodel.source_type = 'google'
                flumodel.calculation_parameters = 'matlab_model,1'
                dates = [date(2018, 6, d) for d in range(1, 30)]
                datapoints = []
                for d in dates:
                    entry = ModelScore()
                    entry.region = 'e'
                    entry.score_date = d
                    entry.calculation_timestamp = datetime.now()
                    entry.score_value = 1.23 / idx
                    entry.confidence_interval_lower = 0.81
                    entry.confidence_interval_upper = 1.65
                    datapoints.append(entry)
                flumodel.model_scores = datapoints
                model_function = ModelFunction()
                model_function.id = idx
                model_function.function_name = 'matlab_model'
                model_function.average_window_size = 1
                model_function.flu_model_id = idx
                model_function.has_confidence_interval = True
                flumodel.save()
                model_function.save()
            default_model = DefaultFluModel()
            default_model.flu_model_id = 1
            rate_thresholds = RateThresholdSet()
            rate_thresholds.low_value = 0.1
            rate_thresholds.medium_value = 0.2
            rate_thresholds.high_value = 0.3
            rate_thresholds.very_high_value = 0.4
            rate_thresholds.valid_from = date(2010, 1, 1)
            rate_thresholds.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/plink?id=1&id=2&startDate=2018-06-01&endDate=2018-06-10&resolution=week')
        self.assertListEqual(
            response.get_json()['model_list'],
            [{'id': 1, 'name': 'Test Model 1'}, {'id': 2, 'name': 'Test Model 2'}]
        )
        self.assertEqual(len(response.get_json()['model_data'][0]['data_points']), 2)
        self.assertEqual(len(response.get_json()['model_data'][1]['data_points']), 2)
        expected = {
            'low_value': {'label': 'Low epidemic rate', 'value': 0.1},
            'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
            'high_value': {'label': 'High epidemic rate', 'value': 0.3},
            'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4}
        }
        self.assertDictEqual(response.get_json()['rate_thresholds'], expected)

    def test_get_plink_smoothing(self):
        with self.app.app_context():
            for idx in [1, 2]:
                flumodel = FluModel()
                flumodel.name = 'Test Model %d' % idx
                flumodel.is_public = True
                flumodel.is_displayed = True
                flumodel.source_type = 'google'
                flumodel.calculation_parameters = 'matlab_model,1'
                dates = [date(2018, 6, d) for d in range(1, 30)]
                datapoints = []
                for d in dates:
                    entry = ModelScore()
                    entry.region = 'e'
                    entry.score_date = d
                    entry.calculation_timestamp = datetime.now()
                    entry.score_value = 1.23 / d.day
                    entry.confidence_interval_lower = 0.81
                    entry.confidence_interval_upper = 1.65
                    datapoints.append(entry)
                flumodel.model_scores = datapoints
                model_function = ModelFunction()
                model_function.id = idx
                model_function.function_name = 'matlab_model'
                model_function.average_window_size = 1
                model_function.flu_model_id = idx
                model_function.has_confidence_interval = True
                flumodel.save()
                model_function.save()
            default_model = DefaultFluModel()
            default_model.flu_model_id = 1
            rate_thresholds = RateThresholdSet()
            rate_thresholds.low_value = 0.1
            rate_thresholds.medium_value = 0.2
            rate_thresholds.high_value = 0.3
            rate_thresholds.very_high_value = 0.4
            rate_thresholds.valid_from = date(2010, 1, 1)
            rate_thresholds.save()
            DB.session.add(default_model)
            DB.session.commit()
        response = self.client().get('/plink?id=1&id=2&startDate=2018-06-01&endDate=2018-06-05&smoothing=3')
        self.assertListEqual(
            response.get_json()['model_list'],
            [{'id': 1, 'name': 'Test Model 1'}, {'id': 2, 'name': 'Test Model 2'}]
        )
        self.assertEqual(len(response.get_json()['model_data'][0]['data_points']), 5)
        self.assertEqual(len(response.get_json()['model_data'][1]['data_points']), 5)
        expected = {
            'low_value': {'label': 'Low epidemic rate', 'value': 0.1},
            'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
            'high_value': {'label': 'High epidemic rate', 'value': 0.3},
            'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4}
        }
        self.assertDictEqual(response.get_json()['rate_thresholds'], expected)
        list_expected = [0.252833, 0.321167, 0.444167, 0.751667, 0.922500]
        list_result = [round(s['score_value'],6) for s in response.get_json()['model_data'][0]['data_points']]
        self.assertListEqual(list_result, list_expected)

    def tearDown(self):
        DB.drop_all(app=self.app)

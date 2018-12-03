"""
 Tests query functions to access model data
"""

from datetime import date
from unittest import TestCase

from app import create_app, DB
from app.models import FluModelGoogleTerm, GoogleDate, GoogleScore, GoogleTerm, ModelScore, FluModel, \
    ModelFunction, DefaultFluModel, RateThresholdSet
from app.models_query_registry import get_existing_google_dates, get_google_terms_for_model_id, \
    set_google_date_for_model_id, set_google_scores_for_term, get_existing_model_dates, set_model_score, \
    get_model_function, get_google_terms_and_scores, get_google_terms_and_averages, \
    get_flu_model_for_id, get_public_flu_models, get_default_flu_model, get_default_flu_model_30days, \
    get_rate_thresholds, get_flu_models_for_ids, get_all_flu_models


class ModelsTestCase(TestCase):
    """ Test case for models_query_registry.py """

    def setUp(self):
        self.app = create_app(config_name='testing')
        self.client = self.app.test_client
        DB.create_all(app=self.app)

    def test_get_flu_model(self):
        """
        Scenario: Get a FluModel entity from its id
        """
        with self.app.app_context():
            flu_model = FluModel()
            flu_model.id = 1
            flu_model.name = 'Test model 1'
            flu_model.source_type = 'google'
            flu_model.is_public = True
            flu_model.is_displayed = True
            flu_model.calculation_parameters = 'matlab_function,1'
            flu_model.save()
            result = get_flu_model_for_id(1)
            self.assertIsNotNone(result)
            self.assertIsInstance(result, FluModel)

    def test_get_public_flu_models(self):
        """
        Scenario: Retrieve a list of public FluModel entities
        """
        with self.app.app_context():
            for idx in range(1, 3):
                flu_model = FluModel()
                flu_model.id = idx
                flu_model.name = 'Test model %d' % idx
                flu_model.source_type = 'google'
                flu_model.is_public = idx % 2 == 0
                flu_model.is_displayed = True
                flu_model.calculation_parameters = 'matlab_function,1'
                flu_model.save()
            result = get_public_flu_models()
            self.assertIsNotNone(result)
            self.assertEquals(len(result), 1)
            self.assertIsInstance(result[0], FluModel)

    def test_get_all_flu_models(self):
        """
        Scenario: Retrieve a list of all FluModel entities
        """
        with self.app.app_context():
            for idx in range(1, 3):
                flu_model = FluModel()
                flu_model.id = idx
                flu_model.name = 'Test model %d' % idx
                flu_model.source_type = 'google'
                flu_model.is_public = idx % 2 == 0
                flu_model.is_displayed = True
                flu_model.calculation_parameters = 'matlab_function,1'
                flu_model.save()
            result = get_all_flu_models()
            self.assertIsNotNone(result)
            self.assertEquals(len(result), 2)
            self.assertIsInstance(result[0], FluModel)

    def test_get_existing_google_dates(self):
        """
        Scenario: Get list of existing dates from GoogleScore
        Given a GoogleDate.flu_model_id value of 1 exists
        And GoogleScore.score_date with values '2018-01-02', '2018-01-03', '2018-01-05'
        When model_id = 1, start = '2018-01-01', end = '2018-01-02'
        Then the list contains one tuple for date '2018-01-02'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                google_date = GoogleDate(1, date(2018, 1, day))
                google_date.save()
            google_date.save()
            result = get_existing_google_dates(1, date(2018, 1, 1), date(2018, 1, 2))
            self.assertListEqual(result, [(date(2018, 1, 2),)])

    def test_get_google_terms_for_model(self):
        """
        Scenario: Get list of Google terms for which a particular flu model was created against
        Given a FluModelGoogleTerm.flu_model_id value of 1 exists
        And GoogleTerms values (1, 'Term 1'), (2, 'Term 2') and (3, 'Term 3') for flu_model_id 1
        When model_id = 1
        Then the list contains 'Term 1', 'Term 2' and 'Term 3' as tuples
        """
        with self.app.app_context():
            expected = []
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                expected.append(('Term %d' % i,))
            result = get_google_terms_for_model_id(1)
            self.assertListEqual(result, expected)

    def test_set_google_scores_for_term(self):
        """
        Scenario: Persist scores if they are not already in the database
        Given a Google term with no score value
        When an entity is saved for that term with a date of 2018-01-01
        Then the result count for a term of that definition and same date is 1
        """
        with self.app.app_context():
            google_term = GoogleTerm()
            google_term.id = 1
            google_term.term = 'Term 1'
            google_term.save()
            set_google_scores_for_term('Term 1', [(date(2018, 1, 1), 0.1)])
            result = GoogleScore.query.filter_by(term_id=1, score_date=date(2018, 1, 1)).count()
            self.assertEqual(result, 1)

    def test_set_google_date_for_model(self):
        """
        Scenario: Persist the date of retrieval of a complete set of scores from Google
        Given a flu model with a set of three terms
        And a score for each of them for one date
        Then the date is persisted on the database
        """
        with self.app.app_context():
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                google_score = GoogleScore(i, date(2018, 1, 1), 0.5 + i)
                google_score.save()
            set_google_date_for_model_id(1, date(2018, 1, 1))
            result = DB.session.query(
                DB.session.query(GoogleDate).filter_by(flu_model_id=1,
                                                       score_date=date(2018, 1, 1)
                                                       ).exists()
            ).scalar()
            self.assertTrue(result)
            """
            Scenario: Check if ValueError is raised if Google scores are incomplete
            """
            flu_model_google_term = FluModelGoogleTerm()
            flu_model_google_term.flu_model_id = 1
            flu_model_google_term.google_term_id = 3
            flu_model_google_term.save()
            google_term = GoogleTerm()
            google_term.id = 3
            google_term.term = 'Term 3'
            google_term.save()
            with self.assertRaises(ValueError):
                set_google_date_for_model_id(1, date(2018, 1, 1))

    def test_get_existing_model_dates(self):
        """
        Scenario: Get list of existing dates from ModelScore
        Given a ModelScore.flu_model_id value of 1 exists
        And ModelScore.score_date with values '2018-01-02', '2018-01-03', '2018-01-05'
        When model_id = 1, start = '2018-01-01', end = '2018-01-02'
        Then the list contains one tuple for date '2018-01-02'
        """
        with self.app.app_context():
            for day in (2, 3, 5):
                model_score = ModelScore()
                model_score.flu_model_id = 1
                model_score.score_date = date(2018, 1, day)
                model_score.score_value = 0.1 + day
                model_score.region = 'e'
                model_score.save()
            result = get_existing_model_dates(1, date(2018, 1, 1), date(2018, 1, 2))
            self.assertListEqual(result, [(date(2018, 1, 2),)])

    def test_set_model_score(self):
        """
        Scenario: Persist a model score entity
        Given a flu model with an id of 1
        And a score date of '2018-01-01'
        And a score value of float type
        When the entity is persisted
        Then a model score with a model id of 1 and score date '2018-01-01' is found
        in the database
        """
        with self.app.app_context():
            set_model_score(1, date(2018, 1, 1), 0.1)
            result = DB.session.query(
                DB.session.query(ModelScore).filter_by(flu_model_id=1,
                                                       score_date=date(2018, 1, 1)
                                                       ).exists()
            ).scalar()
            self.assertTrue(result)

    def test_get_model_function(self):
        """
        Scenario: Get the model configuration parameters (name of Matlab function and
        window for calculation of moving averages
        """
        with self.app.app_context():
            model_function = ModelFunction()
            model_function.id = 1
            model_function.flu_model_id = 1
            model_function.function_name = 'matlab_function'
            model_function.average_window_size = 1
            model_function.has_confidence_interval = True
            model_function.save()
            result = get_model_function(1)
            self.assertIsInstance(result, ModelFunction)

    def test_get_google_terms_and_scores(self):
        """
        Scenario: Get the Google terms for a model and their scores for a date
        """
        with self.app.app_context():
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                google_score = GoogleScore(i, date(2018, 1, 1), 0.5 + i)
                google_score.save()
            # Additional FluModel to verify the select works as expected
            flu_model_google_term_2 = FluModelGoogleTerm()
            flu_model_google_term_2.flu_model_id = 2
            flu_model_google_term_2.google_term_id = 3
            flu_model_google_term_2.save()
            google_term_2 = GoogleTerm()
            google_term_2.id = 3
            google_term_2.term = 'Term 3'
            google_term_2.save()
            google_score_2 = GoogleScore(3, date(2018, 1, 1), 1.5)
            google_score_2.save()
            result = get_google_terms_and_scores(1, date(2018, 1, 1))
            expected = [('Term 0', 0.5), ('Term 1', 1.5), ('Term 2', 2.5)]
            self.assertListEqual(result, expected)

    def test_get_google_terms_and_averages(self):
        """
        Scenario: Get the Google terms for a model and their average scores for a date window
        """
        with self.app.app_context():
            for i in range(3):
                flu_model_google_term = FluModelGoogleTerm()
                flu_model_google_term.flu_model_id = 1
                flu_model_google_term.google_term_id = i
                flu_model_google_term.save()
                google_term = GoogleTerm()
                google_term.id = i
                google_term.term = 'Term %d' % i
                google_term.save()
                google_score = GoogleScore(i, date(2018, 1, 1), 0.5 + i)
                google_score.save()
                google_score = GoogleScore(i, date(2018, 1, 2), 0.1 + i)
                google_score.save()
            # Additional FluModel to verify the select works as expected
            flu_model_google_term_2 = FluModelGoogleTerm()
            flu_model_google_term_2.flu_model_id = 2
            flu_model_google_term_2.google_term_id = 3
            flu_model_google_term_2.save()
            google_term_2 = GoogleTerm()
            google_term_2.id = 3
            google_term_2.term = 'Term 3'
            google_term_2.save()
            google_score_2 = GoogleScore(3, date(2018, 1, 1), 1.5)
            google_score_2.save()
            result = get_google_terms_and_averages(1, 2, date(2018, 1, 2))
            expected = [('Term 0', 0.3), ('Term 1', 1.3), ('Term 2', 2.3)]
            self.assertListEqual(result, expected)

    def test_get_default_flu_model(self):
        """
        Scenario: Get the default flu model
        """
        with self.app.app_context():
            flu_model = FluModel()
            flu_model.id = 1
            flu_model.is_displayed = True
            flu_model.is_public = True
            flu_model.calculation_parameters = ''
            flu_model.name = 'Model 1'
            flu_model.source_type = 'google'
            flu_model.save()
            default_model = DefaultFluModel()
            default_model.flu_model_id = 1
            DB.session.add(default_model)
            DB.session.commit()
            result = get_default_flu_model()
            self.assertEqual(result.name, 'Model 1')

    def test_get_default_model_30days(self):
        """
        Scenario: Get the last 30 days of data of the default flu model
        """
        with self.app.app_context():
            flu_model = FluModel()
            flu_model.id = 1
            flu_model.is_displayed = True
            flu_model.is_public = True
            flu_model.calculation_parameters = ''
            flu_model.name = 'Model 1'
            flu_model.source_type = 'google'
            flu_model.save()
            default_model = DefaultFluModel()
            default_model.flu_model_id = 1
            DB.session.add(default_model)
            DB.session.commit()
            for i in range(1, 32):
                model_score = ModelScore()
                model_score.flu_model_id = 1
                model_score.score_date = date(2018, 1, i)
                model_score.score_value = i/(10+i)
                model_score.region = 'e'
                model_score.save()
            result = get_default_flu_model_30days()
            self.assertEqual(result[0]['average_score'], 0.5723146873461765)
            self.assertEqual(result[0]['start_date'], date(2018, 1, 2))
            self.assertEqual(result[0]['end_date'], date(2018, 1, 31))
            self.assertEqual(result[0]['name'], 'Model 1')
            self.assertEqual(result[0]['id'], 1)
            self.assertEqual(len(result[1]), 30)

    def test_get_rate_thresholds(self):
        """
        Scenario: Get the current set of rate thresholds
        """
        with self.app.app_context():
            rate_threshold = RateThresholdSet()
            rate_threshold.threshold_set_id = 1
            rate_threshold.low_value = 0.1
            rate_threshold.medium_value = 0.2
            rate_threshold.high_value = 0.3
            rate_threshold.very_high_value = 0.4
            rate_threshold.valid_from = date(2018, 1, 1)
            rate_threshold.valid_until = None
            rate_threshold.save()
            result = get_rate_thresholds(date(2018, 2, 1))
            expected = {
                'very_high_value': {'label': 'Very high epidemic rate', 'value': 0.4},
                'high_value': {'label': 'High epidemic rate', 'value': 0.3},
                'medium_value': {'label': 'Medium epidemic rate', 'value': 0.2},
                'low_value': {'label': 'Low epidemic rate', 'value': 0.1}
            }
            self.assertDictEqual(result, expected)

    def test_get_flu_models_for_ids(self):
        """
        Scenario: Get a list of FluModels from an array of ids
        """
        with self.app.app_context():
            for idx in range(1, 4):
                flu_model = FluModel()
                flu_model.id = idx
                flu_model.name = 'Test model %d' % idx
                flu_model.source_type = 'google'
                flu_model.is_public = True
                flu_model.is_displayed = True
                flu_model.calculation_parameters = 'matlab_function,1'
                flu_model.save()
            result = get_flu_models_for_ids([1, 2])
            self.assertEqual(len(result), 2)

    def tearDown(self):
        DB.drop_all(app=self.app)

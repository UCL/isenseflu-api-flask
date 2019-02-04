import sys
from os import makedirs
from pathlib import Path
from shutil import copy2, rmtree, which
from unittest import TestCase

from scheduler.calculator_builder import CalculatorType, build_calculator


class CalculatorBuilderTestCase(TestCase):
    """ Test case for module scheduler.calculator_builder """

    def test_calculation_in_matlab(self):
        if 'matlab' not in sys.modules:
            pass

    def test_calculation_in_octave(self):
        if which('octave') is not None:
            makedirs("octave/gpml", exist_ok=True)
            Path("octave/gpml/startup.m").touch()
            engine = build_calculator(CalculatorType['OCTAVE'])
            copy2('tests/mfiles/model_score_octave.m', 'octave')
            val = engine.calculate_model_score('model_score_octave', [('term1', 1.0), ('term2', 2.0)])
            rmtree("octave")
            self.assertEqual(val, 1.0)

    def test_calculation_and_confidence_in_octave(self):
        if which('octave') is not None:
            makedirs("octave/gpml", exist_ok=True)
            Path("octave/gpml/startup.m").touch()
            engine = build_calculator(CalculatorType['OCTAVE'])
            copy2('tests/mfiles/model_score_and_confidence_octave.m', 'octave')
            val = engine.calculate_model_score_and_confidence(
                'model_score_and_confidence_octave',
                [('term1', 1.0), ('term2', 2.0)]
            )
            rmtree("octave")
            self.assertEqual(val, (1.0, 0.1, 1.5))

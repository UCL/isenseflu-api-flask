"""
 Builds caller to Matlab, Octave or any other remote engine for numerical calculation
"""
from abc import ABC, abstractmethod
from enum import Enum
from numpy import array
from tempfile import NamedTemporaryFile
from typing import List, Tuple


class CalculatorType(Enum):
    """
    Enum used to specify the type of NATLAB client to build
    """
    MATLAB, OCTAVE, REMOTE = range(3)


class Calculator(ABC):
    """
    Abstract base class to define methods available in MATLAB/OCTAVE clients
    """

    @abstractmethod
    def calculate_model_score(self,
                              matlab_function: str,
                              averages: List[Tuple[str, float]]
                              ) -> float:
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        pass

    @abstractmethod
    def calculate_model_score_and_confidence(self,
                                             matlab_function: str,
                                             averages: List[Tuple[str, float]]
                                             ) -> Tuple[float, float, float]:
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        pass


class MatlabCalculator(Calculator):
    """
    Caller to a local installation of Matlab
    """

    def __init__(self):
        from matlab import engine
        self.engine = engine.start_matlab("-nodisplay -nojvm")
        self.engine.cd("matlab")
        self.engine.run("gpml/startup.m", nargout=0)

    def __del__(self):
        self.engine.quit()

    def calculate_model_score(self,
                              matlab_function: str,
                              averages: List[Tuple[str, float]]
                              ) -> float:
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        fhin, fhout = self._write_tempfile(averages)
        self.engine.evalc("fin = '%s'" % fhin.name, nargout=0)
        self.engine.evalc("fout = '%s'" % fhout.name, nargout=0)
        self.engine.run("%s(fin,fout)" % matlab_function, nargout=0)
        value = float(open(fhout.name).read().strip())
        fhin.close()
        fhout.close()
        return value

    def calculate_model_score_and_confidence(self,
                                             matlab_function: str,
                                             averages: List[Tuple[str, float]]
                                             ) -> Tuple[float, float, float]:
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        fhin, fhout = self._write_tempfile(averages)
        self.engine.evalc("fin = '%s'" % fhin.name, nargout=0)
        self.engine.evalc("fout = '%s'" % fhout.name, nargout=0)
        self.engine.run("%s(fin,fout)" % matlab_function, nargout=0)
        value = str(open(fhout.name).read().strip()).split(",")
        fhin.close()
        fhout.close()
        return float(value[0]), float(value[1]), float(value[2])

    def _write_tempfile(self, averages):
        fhin = NamedTemporaryFile(mode='w+t', prefix='isenseflu-matlab-input.')
        fhout = NamedTemporaryFile(mode='w+t', prefix='isenseflu-matlab-output.')
        fhin.write('\n'.join('%s,%f' % a for a in averages))
        fhin.flush()
        return fhin, fhout


class OctaveCalculator(Calculator):
    """
    Caller to a local installation of GNU Octave
    """

    def __init__(self):
        from oct2py import Oct2Py
        self.engine = Oct2Py()
        self.engine.cd("octave")
        self.engine.run("gpml/startup.m")

    def __del__(self):
        self.engine.exit()

    def calculate_model_score(self,
                              matlab_function: str,
                              averages: List[Tuple[str, float]]
                              ) -> float:
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        terms = array([[s[0] for s in averages]], dtype=object).T
        scores = array([[s[1] for s in averages]]).T
        self.engine.push('terms', terms)
        self.engine.push('scores', scores)
        self.engine.eval("y_inf = %s(terms,scores)" % (matlab_function))
        score = self.engine.pull('y_inf')
        return float(score)

    def calculate_model_score_and_confidence(self,
                                             matlab_function: str,
                                             averages: List[Tuple[str, float]]
                                             ) -> Tuple[float, float, float]:
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        terms = array([[s[0] for s in averages]], dtype=object).T
        scores = array([[s[1] for s in averages]]).T
        self.engine.push('terms', terms)
        self.engine.push('scores', scores)
        self.engine.eval("[y_inf, y_inf_lower, y_inf_upper] = %s(terms,scores)" % matlab_function)
        score = self.engine.pull(['y_inf', 'y_inf_lower', 'y_inf_upper'])
        return float(score[0]), float(score[1]), float(score[2])


class RemoteCalculator(Calculator):
    """
    Caller to a remote engine via REST APIs (not yet implemented)
    """

    def calculate_model_score(self,
                              matlab_function: str,
                              averages: List[Tuple[str, float]]
                              ) -> float:
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        raise NotImplementedError

    def calculate_model_score_and_confidence(self,
                                             matlab_function: str,
                                             averages: List[Tuple[str, float]]
                                             ) -> Tuple[float, float, float]:
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        raise NotImplementedError


def build_calculator(calculator_type: CalculatorType) -> Calculator:
    """
    Builds a caller to a calculation engine
    :param calculator_type: a CalculatorType enum member, either MATLAB, OCTAVE or REMOTE
    :return: An implementation of Calculator
    """
    if calculator_type is CalculatorType.MATLAB:
        return MatlabCalculator()
    if calculator_type is CalculatorType.REMOTE:
        return RemoteCalculator()
    if calculator_type is CalculatorType.OCTAVE:
        return OctaveCalculator()

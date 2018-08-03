"""
 Interacts with a local or remote installation of MATLAB
"""

from abc import ABC, abstractmethod
from enum import Enum
import tempfile


class MatlabType(Enum):
    """
    Enum used to specify the type of NATLAB client to build
    """
    LOCAL, REMOTE = range(2)


class BaseMatlab(ABC):
    """
    Abstract base class to define methods available in MATLAB clients
    """

    @abstractmethod
    def calculate_model_score(self, matlab_function, averages):
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        pass

    @abstractmethod
    def calculate_model_score_and_confidence(self, matlab_function, averages):
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        pass


class LocalMatlab(BaseMatlab):
    """
    Interface to a instance of MATLAB running on the same host
    """

    def __init__(self):
        from matlab import engine
        self.conf = MatlabType.LOCAL
        self.engine = engine.start_matlab("-nodisplay -nojvm")
        self.engine.cd("matlab")
        self.engine.run("gpml/startup.m", nargout=0)

    def __del__(self):
        self.engine.quit()

    def calculate_model_score(self, matlab_function, averages) -> float:
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

    def calculate_model_score_and_confidence(self, matlab_function, averages):
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
        return value[0], value[1], value[3]

    @staticmethod
    def _write_tempfile(averages):
        fhin = tempfile.NamedTemporaryFile(prefix='fludetector-matlab-input.')
        fhout = tempfile.NamedTemporaryFile(prefix='fludetector-matlab-output.')
        fhin.write('\n'.join('%s,%f' % a for a in averages))
        fhin.flush()
        return fhin, fhout


class RemoteMatlab(BaseMatlab):
    """
    Interface to a remote installation of MATLAB
    """

    def calculate_model_score(self, matlab_function, averages):
        """
        Calculates the model score from a list average reference scores
        It returns a single float corresponding to the score without confidence
        intervals
        """
        raise NotImplementedError

    def calculate_model_score_and_confidence(self, matlab_function, averages):
        """
        Calculates the model score from a list average reference scores
        It returns a tuple containing the model sscore followed by the lower
        and the upper bound confidence interval
        """
        raise NotImplementedError


def build_matlab_client(matlab_type: MatlabType):
    """
    Creates a new instance of the MATLAB client used to calculate model scores
    """
    if matlab_type is MatlabType.LOCAL:
        return LocalMatlab()
    if matlab_type is MatlabType.REMOTE:
        return RemoteMatlab()
    return None

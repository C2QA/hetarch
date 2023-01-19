
import qiskit
import numpy as np


class InputModule():
    """
    InputModule class

    Resposnibilities of the InputModule include catching a photon from the line and transducing into a transmon

    attributes:
        - Density Matrix : 4x4 Numpy array representing the density matrix of a remote entangled EPR pair
        - Time : Time for module to catch the photon
    """
    def __init__(self, time: float):
        self.density_matrix = None
        self.time = time

    def input(self, rho: np.array):
        self.density_matrix = rho

    def output(self):
        assert self.density_matrix is not None
        return self.density_matrix, self.time


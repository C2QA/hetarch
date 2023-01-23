import qiskit
import numpy as np
from HarchSim.StandardCell.EPRGenerator import EPRGenerator


class InputModule:
    """
    InputModule class

    Responsibilities of the InputModule include catching a photon from the line and transducing into a transmon
    TODO: This does not do the full functionality. This just is a pathway for a EPR Entangler right now.
    attributes:
        - Density Matrix : 4x4 Numpy array representing the density matrix of a remote entangled EPR pair
        - Time : Time for module to catch the photon
    """

    def __init__(self,
                 epr_gen: list[EPRGenerator]):
        self.epr_gen = epr_gen
        self.locked_epr_gen = {}
        self.density_matrix = None
        self.time = None
        self.clock = None

    def is_input_available(self):
        for epr in self.epr_gen:
            return True

    def get_input(self):
        for epr in self.epr_gen:
            self.locked_epr_gen[epr] = {}
            self.locked_epr_gen[epr]["time"] = self.clock.clock
            self.locked_epr_gen[epr]["compute_time"] = 500e-9
            self.epr_gen.remove(epr)
            return epr.output()

    def bind_clock_to_modules(self):
        for module in self.epr_gen:
            module.clock = self.clock

    def input(self, rho: np.array = None):
        if rho is None:
            # TODO: Abstract this away. This is not flexible. We only will use one though.
            self.density_matrix =  self.epr_gen[0].output()
        else:
            self.density_matrix = rho
        # self.density_matrix = rho

    def output(self):
        assert self.density_matrix is not None
        return self.density_matrix, self.time

    def check_unlock(self):
        keys = list(self.locked_epr_gen.keys())
        for key in keys:
            if self.clock.clock - self.locked_epr_gen[key]["time"] > self.locked_epr_gen[key]["compute_time"]:
                self.epr_gen.append(key)
                self.locked_epr_gen.pop(key)
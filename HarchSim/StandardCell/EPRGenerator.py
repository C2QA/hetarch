import numpy as np
from HarchSim.Device.Cavity import Cavity
from HarchSim.Device.Transmon import Transmon


class EPRGenerator:
    """
    This describes the catching of a photon and transducing it into microwave regime. It does not contain info
    regarding movement from that to memory.
    """

    def __init__(self,
                 qb1: Transmon,
                 qb2: Transmon,
                 cav1: Cavity,
                 cav2: Cavity,
                 t_catch: float):
        self.qb1 = qb1
        self.qb2 = qb2
        self.cav1 = cav1
        self.cav2 = cav2
        self.time = t_catch
        self.state = None
        self.dm = None
        self.cx = np.array([[1, 0, 0, 0],
                            [0, 1, 0, 0],
                            [0, 0, 0, 1],
                            [0, 0, 1, 0]])
        self.entangle()

    def entangle(self):
        self.qb1.apply_gate("h")
        self.dm = np.kron(self.qb1.dm, self.qb2.dm)
        self.dm = self.cx @ self.dm @ self.cx.conj().transpose()

    def output(self):
        return self.dm, self.time


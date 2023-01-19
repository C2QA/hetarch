import numpy as np
from HarchSim.Device.BaseDevice import BaseDevice


class Transmon(BaseDevice):
    def __init__(self,
                 t1: int,
                 t2: int):
        """
        Initalise a transmon. Initial state is |g><g|. Can be set.
        :param t1: T1 time describing device. Units are s
        :param t2: T2 time describing device. Units are s
        """
        super().__init__(t1, t2)
        self.dm = np.array([[1, 0],
                            [0, 0]])

    def set_state(self,
                  state: np.array):
        """
        Update initial state of transmon to a specific state. Default is ground state
        :param state: Density matrix representing state.
        :return: None
        """
        self.dm = state



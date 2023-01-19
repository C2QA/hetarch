import numpy as np
from HarchSim.Device.BaseDevice import BaseDevice


class Cavity(BaseDevice):
    def __init__(self,
                 t1: int,
                 t2: int,
                 levels: int,
                 modes: int):
        """
        :param t1: T1 time describing device. Units are s
        :param t2: T2 time describing device. Units are s
        :param levels: Number of levels describing the cavity
        :param modes: Number of modes being simulated in the cavity for each photon .
        """
        super().__init__(t1, t2)
        self.levels = levels
        self.modes = modes
        self.mode_memory = {}
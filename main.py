from HarchSim.Modules.InputModule import InputModule
from HarchSim.Modules.MemoryModule import MemoryModule
from HarchSim.Modules.DistillationModule import DistillationModule
from HarchSim.Device.Transmon import Transmon
from HarchSim.Device.Cavity import Cavity
from HarchSim.StandardCell.EPRGenerator import EPRGenerator
from HarchSim.StandardCell.MemoryCell import MemoryCell
from HarchSim.StandardCell.DistillationCell import DistillationCell
from HarchSim.EntanglementDistillationController import EntanglementDistillationController

from copy import copy

import numpy as np

""" Set an initial pure state of a bell pair in the state of |00> + |11> """

"Set up transmon properties"
qb = Transmon(1e-6, 1e-6)
h = (1/np.sqrt(2))*np.array([[1, 1],
                             [1, -1]])
qb.add_gateset('h',h)

"Set up cavity properties"
cav = Cavity(1e-6, 1e-6, 2, 2)

"Set up EPR generator"
epr_gen = EPRGenerator(copy(qb), copy(qb), copy(cav), copy(cav), 1e-6)
epr_gen.entangle()

"Set up memory cell"
memory = MemoryCell(copy(cav), copy(qb))

"Set Up Distillation cell"
distillation = DistillationCell(copy(qb), copy(qb))

module = EntanglementDistillationController()
module.modules = {"input": InputModule([epr_gen]),
            "memory": MemoryModule([memory]),
            "distillation": DistillationModule([distillation])}

module.run()
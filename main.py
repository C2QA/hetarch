from HarchSim.Modules.InputModule import InputModule
from HarchSim.Modules.MemoryModule import MemoryModule
from HarchSim.Modules.DistillationModule import DistillationModule
from HarchSim.Device.Transmon import Transmon
from HarchSim.Device.Cavity import Cavity
from HarchSim.StandardCell.EPRGenerator import EPRGenerator
from HarchSim.StandardCell.MemoryCell import MemoryCell
from HarchSim.EntanglementDistillationController import EntanglementDistillationController
import numpy as np

""" Set an initial pure state of a bell pair in the state of |00> + |11> """


qb1 = Transmon(1e-6, 1e-6)
qb2 = Transmon(1e-6, 1e-6)
h = (1/np.sqrt(2))*np.array([[1, 1],
                             [1, -1]])
qb1.add_gateset('h',h)
qb2.add_gateset('h',h)
epr_gen = EPRGenerator(qb1, qb2)
epr_gen.entangle()
cavity = Cavity(1e-6,1e-6,2,2)
memory = MemoryCell(cavity,qb1)

module = EntanglementDistillationController()

module.modules = {"input": InputModule(epr_gen),
            "memory": MemoryModule(memory),
            "distillation": DistillationModule()}

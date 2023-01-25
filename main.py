import HarchSim
import numpy as np
from HarchSim.Device import BaseDevice, Cavity, Transmon
from HarchSim.StandardCell import MemoryCell, EPRGenerator, DistillationCell
from HarchSim.Modules import InputModule, MemoryModule, DistillationModule, DistilledMemoryModule
from HarchSim.EntanglementDistillationController import EntanglementDistillationController, MODULE
import numpy as np
import matplotlib.pyplot as plt

# Load ARQUIN M2O Density Matrices.
mats = np.load('dm_m2o.npy')
dm = np.array(mats[:, :, 25])

# ===========================
# Qubit and Cavity properties
# ===========================
T1 = T2 = 100e-6

# ===========================
# Set times below for each operation
# ===========================
T_INPUT_LOAD = 300e-9
T_MEMORY_LOAD = 500e-9
T_MEMORY_READ = 500e-9
T_DISTILL = 500e-9
# ===========================
# Constructing an input module
# ===========================
# Build 2 Transmon, 2 Cavity, into EPR generator, into InputModule
T1_cavity = T2_cavity = 500e-6
qb1 = Transmon.Transmon(t1=T1,
                        t2=T2)
qb2 = Transmon.Transmon(t1=T1,
                        t2=T2)
qb1.add_gateset("h", (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))
qb2.add_gateset("h", (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))
cavity1 = Cavity.Cavity(t1=T1_cavity,
                        t2=T2_cavity,
                        levels=8,
                        modes=2)
cavity2 = Cavity.Cavity(t1=T1_cavity,
                        t2=T2_cavity,
                        levels=8,
                        modes=2)
epr_generator = EPRGenerator.EPRGenerator(qb1,
                                          qb2,
                                          cavity1,
                                          cavity2,
                                          T_INPUT_LOAD)
epr_generator.set_dm(dm)
epr_generators = [epr_generator]
input_module = InputModule.InputModule(epr_generators)

# ===========================
# Constructing a memory module
# ===========================
cavity_memory = Cavity.Cavity(t1=T1_cavity,
                              t2=T2_cavity,
                              levels=8,
                              modes=2)
transmon_memory = Transmon.Transmon(t1=T1,
                                    t2=T2)

memory_cell1 = MemoryCell.MemoryCell(cavity_memory,
                                     transmon_memory,
                                     load_time=T_MEMORY_LOAD,
                                     read_time=T_MEMORY_READ)
memory_cell1.initalize_memory()
# Build Memory Module 2
cavity_memory2 = Cavity.Cavity(t1=T1_cavity,
                               t2=T2_cavity,
                               levels=10,
                               modes=2)
transmon_memory2 = Transmon.Transmon(t1=T1,
                                     t2=T2)
memory_cell2 = MemoryCell.MemoryCell(cavity_memory, transmon_memory)
memory_cell2.initalize_memory()

memory_module = MemoryModule.MemoryModule([memory_cell1, memory_cell2])

# =====================================
# Constructing a distilled memory module
# ======================================
cavity_memory_dist = Cavity.Cavity(t1=T1_cavity,
                                   t2=T2_cavity,
                                   levels=10,
                                   modes=2)
transmon_memory_dist = Transmon.Transmon(t1=T1,
                                         t2=T2)
memory_cell_distilled = MemoryCell.MemoryCell(cavity_memory_dist, transmon_memory_dist)
memory_cell_distilled.initalize_memory()
memory_module_distilled = DistilledMemoryModule.DistilledMemoryModule([memory_cell_distilled])

# =====================================
# Constructing a distillation module
# ======================================
dist_qb1 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_qb2 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_cell1 = DistillationCell.DistillationCell(dist_qb1, dist_qb2, T_DISTILL)
dist_qb3 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_qb4 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_cell2 = DistillationCell.DistillationCell(dist_qb3, dist_qb4, T_DISTILL)
dist_module = DistillationModule.DistillationModule([dist_cell1, dist_cell2])

# =====================================
# Construct the controller
# ======================================
controller = EntanglementDistillationController(clock_speed=1e-6)
controller.set_input_module(input_module)
controller.set_memory_module(memory_module)
controller.set_distillation_module(dist_module)
controller.set_distilled_memory_module(memory_module_distilled)
controller.bind_clock_to_modules()

# Run the controller.
controller.run()

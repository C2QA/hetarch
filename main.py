import copy
import os
import pickle
from datetime import datetime

import numpy as np

from HarchSim.Device import Cavity, Transmon
from HarchSim.EntanglementDistillationController import EntanglementDistillationController
from HarchSim.Modules import InputModule, MemoryModule, DistillationModule, DistilledMemoryModule
from HarchSim.StandardCell import MemoryCell, EPRGenerator, DistillationCell

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
# You cant pickle a reference to a function. You need to define this within the InputModule
def T_INPUT_FN():
    # Random number between 150e-9 and 300e-9
    return np.random.rand() * 150e-9 + 150e-9


T_INPUT_LOAD = T_INPUT_FN
T_SWAP_INTO_MEMORY = 500e-9
T_SWAP_OUT_MEMORY = 500e-9
T_READ_INTO_DISTILLATION = 300e-9
T_READ_OUT_DISTILLATION = 300e-9

LOAD_TIMES = {"t_catch": T_INPUT_FN,
              "t_swap_into_memory": T_SWAP_INTO_MEMORY,
              "t_swap_out_memory": T_SWAP_OUT_MEMORY,
              "t_read_into_distillation": T_READ_INTO_DISTILLATION,
              "t_read_out_distillation": T_READ_OUT_DISTILLATION}
N_CAVITY_LEVELS = 8
# ===========================
# Constructing an input module
# ===========================
# Build 2 Transmon, 2 Cavity, into EPR generator, into InputModule
T1_cavity = T2_cavity = 800e-6
# For simulation of a transmon as a "cavity", we set its T1 to 100, and then levels = 3 ( 3 qubits), and 2 modes
# T1_cavity = T2_cavity = 100e-6

qb1 = Transmon.Transmon(t1=T1,
                        t2=T2)
qb2 = Transmon.Transmon(t1=T1,
                        t2=T2)
qb1.add_gateset("h", (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))
qb2.add_gateset("h", (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]]))
cavity1 = Cavity.Cavity(t1=T1_cavity,
                        t2=T2_cavity,
                        levels=N_CAVITY_LEVELS,
                        modes=2)
cavity2 = Cavity.Cavity(t1=T1_cavity,
                        t2=T2_cavity,
                        levels=N_CAVITY_LEVELS,
                        modes=2)
qb3 = copy.copy(qb1)
qb4 = copy.copy(qb2)
cavity3 = copy.copy(cavity1)
cavity4 = copy.copy(cavity2)
epr_generator = EPRGenerator.EPRGenerator(qb1,
                                          qb2,
                                          cavity1,
                                          cavity2,
                                          T_INPUT_LOAD)
epr_generator2 = EPRGenerator.EPRGenerator(qb3,
                                           qb4,
                                           cavity3,
                                           cavity4,
                                           T_INPUT_LOAD)
epr_generator.set_dm(dm)
# 2 epr generatores doesnt work for some reason
# TODO: Fix this bug
epr_generators = [epr_generator]

input_module = InputModule.InputModule(epr_generators)

# ===========================
# Constructing a memory module
# ===========================
cavity_memory = Cavity.Cavity(t1=T1_cavity,
                              t2=T2_cavity,
                              levels=N_CAVITY_LEVELS,
                              modes=2)
transmon_memory = Transmon.Transmon(t1=T1,
                                    t2=T2)

memory_cell1 = MemoryCell.MemoryCell(cavity_memory,
                                     transmon_memory)

memory_cell1.initalize_memory()
# Build Memory Module 2
cavity_memory2 = Cavity.Cavity(t1=T1_cavity,
                               t2=T2_cavity,
                               levels=N_CAVITY_LEVELS,
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
                                   levels=N_CAVITY_LEVELS,
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
dist_cell1 = DistillationCell.DistillationCell(dist_qb1, dist_qb2)
dist_qb3 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_qb4 = Transmon.Transmon(t1=T1,
                             t2=T2)
dist_cell2 = DistillationCell.DistillationCell(dist_qb3, dist_qb4)
dist_module = DistillationModule.DistillationModule([dist_cell1, dist_cell2])

# =====================================
# Construct the controller
# ======================================
controller = EntanglementDistillationController(clock_speed=1e-8)
controller.set_input_module(input_module)
controller.set_memory_module(memory_module)
controller.set_distillation_module(dist_module)
controller.set_distilled_memory_module(memory_module_distilled)
controller.set_sim_times(LOAD_TIMES)
controller.bind_clock_to_modules()
# Run the controller.
controller.run()

# Save statistics of performance
if not os.path.isdir("results"):
    os.mkdir("results")

with open(f"results/{str(datetime.now()).replace(' ', '_')}", 'wb') as f:
    pickle.dump(controller, f)

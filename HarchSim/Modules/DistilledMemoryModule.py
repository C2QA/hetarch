from HarchSim.Modules.MemoryModule import MemoryModule
import qiskit
import numpy as np
from datetime import datetime
import qiskit.quantum_info as qi
from HarchSim.StandardCell.MemoryCell import MemoryCell


class DistilledMemoryModule(MemoryModule):
    def __init__(self, memory: list[MemoryCell]):
        super().__init__(memory)
        self.avg_fidelity = []
        self.max_fidelity = []
        self.psi_plus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.psi_minus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, -1, 0], [0, -1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.phi_plus = qi.DensityMatrix(np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]) / 2)
        self.phi_minus = qi.DensityMatrix(np.array([[1, 0, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, 1]]) / 2)

    def track_fidelity(self):
        fids = []
        for cell in self.memory:
            for i in range(cell.cavity.levels):
                if cell.memory[i]["dm"] is not None:
                    fids.append(qi.state_fidelity(cell.memory[i]["dm"], self.psi_plus))
        if len(fids) != 0:
            self.avg_fidelity.append(np.mean(fids))
            self.max_fidelity.append(np.max(fids))

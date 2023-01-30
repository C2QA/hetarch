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
            avg_fid = np.mean(fids)
            if len(self.avg_fidelity) < 5:
                self.avg_fidelity.append(np.mean(avg_fid))
            else:
                l1 = self.avg_fidelity[:-5]
                l1.append(avg_fid)
                new_avg = np.mean(l1)
                self.avg_fidelity.append(new_avg)
            if len(self.max_fidelity) > 0 and np.max(fids) < np.max(self.max_fidelity):
                self.max_fidelity.append(np.max(self.max_fidelity))
            else:
                self.max_fidelity.append(np.max(fids))

    def is_two_qubit_available_at_same_fidelity(self):
        n_avail = 0
        for module in self.memory:
            if module.n_qb_in_memory() > 0:
                n_avail += module.n_qb_in_memory()
        if n_avail < 2:
            return False
        else:
            return True

from HarchSim.Modules.MemoryModule import MemoryModule
import qiskit
import numpy as np
from datetime import datetime
import qiskit.quantum_info as qi
from HarchSim.StandardCell.MemoryCell import MemoryCell
from qiskit_aer.noise import (NoiseModel, QuantumError, ReadoutError,
                              pauli_error, depolarizing_error, thermal_relaxation_error)


class DistilledMemoryModule(MemoryModule):
    def __init__(self, memory: list[MemoryCell]):
        """
        Initialise the DistilledMemoryModule object. Very similar to MemoryModule, just with ancilla
        tracking features implemented
        :param memory: List of memory cells
        """
        super().__init__(memory)
        self.sim = qiskit.Aer.get_backend('aer_simulator_density_matrix')
        self.avg_fidelity = []
        self.max_fidelity = []
        self.psi_plus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.psi_minus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, -1, 0], [0, -1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.phi_plus = qi.DensityMatrix(np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]) / 2)
        self.phi_minus = qi.DensityMatrix(np.array([[1, 0, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, 1]]) / 2)

    def track_fidelity(self):
        """
        Logic for tracking fidelity over the distilled memory module.
        Current logic takes in the entire memory module, and reports the average fidelity across the system
        as well as the maximum currently available pair.
        Any pair consumed for output or currently being distilled will not be part of the calculation.
        :return: None
        """
        fids = []
        for cell in self.memory:
            for i in range(cell.cavity.levels):
                if cell.memory[i]["dm"] is not None:
                    t_delta = self.clock.clock - cell.memory[i]["time"]
                    print(t_delta)
                    dm = cell.memory[i]["dm"]
                    if t_delta > 0:
                        t1 = cell.cavity.t1
                        t2 = cell.cavity.t2
                        error_distill = thermal_relaxation_error(t1, t2, t_delta)
                        noise_model_distill = NoiseModel()
                        noise_model_distill.add_all_qubit_quantum_error(error_distill, ['id'])
                        circuit = qiskit.QuantumCircuit(2)
                        circuit.set_density_matrix(dm)
                        circuit.id(0)
                        circuit.id(1)
                        circuit.save_density_matrix()
                        job = qiskit.execute(circuit, self.sim,
                                             noise_model=noise_model_distill,
                                             optimization_level=0)
                        dm_noisy = job.result().data()['density_matrix']
                        fids.append(qi.state_fidelity(dm_noisy, self.psi_plus))
                    else:
                        fids.append(qi.state_fidelity(dm, self.psi_plus))

        if len(fids) != 0:
            avg_fid = np.mean(fids)
            if len(self.avg_fidelity) < 5:
                self.avg_fidelity.append(np.mean(avg_fid))
            else:
                l1 = self.avg_fidelity[:-5]
                l1.append(avg_fid)
                new_avg = np.mean(l1)
                self.avg_fidelity.append(new_avg)
            # if len(self.max_fidelity) > 0 and np.max(fids) < np.max(self.max_fidelity):
            #     self.max_fidelity.append(np.max(self.max_fidelity))
            # else:
            self.max_fidelity.append(np.max(fids))

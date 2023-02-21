import qiskit
import numpy as np
from datetime import datetime
import qiskit.quantum_info as qi
from qiskit import QuantumCircuit
import copy
from qiskit_aer.noise import (NoiseModel, thermal_relaxation_error)


class DistillationCell:
    """
    MemoryModule class

    Responsibilities of the MemoryModule include transducing a transmon qubit into a cavity.
    The cavity must keep track of the qubits order such that for distillation we utilise oldest
    qubits first due to decoherence.


    attributes:
        - Density Matrix : 4x4 Density matrix representing the EPR pair between two remote chips.
                            For entanglement distillation, multiple density matrices are fed into
                            the chiplet and distilled.
        == TO BE IMPLEMENTED ==
        - noise_model : Entanglement distillation protocols require single qubit gate and dual qubit gate
                        operations. A noise model can be passed to incorporate this noise over the distillation
                        procedure.
        - Protocol : Entanglement distillation protocol. This is the entire protocol that describes the purification
                     procedure.
    """

    def __init__(self, qb1, qb2):
        """
        :param protocol: String variable describing the protocol. e.g. Deutsch
        """
        self.available = True
        self.output_dm = None
        self.qb1 = qb1
        self.qb2 = qb2
        self.PENDING = False
        self.psi_plus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.psi_minus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, -1, 0], [0, -1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.phi_plus = qi.DensityMatrix(np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]) / 2)
        self.phi_minus = qi.DensityMatrix(np.array([[1, 0, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, 1]]) / 2)
        self.sim = qiskit.Aer.get_backend('aer_simulator_density_matrix')
        t1 = qb1.t1
        t2 = qb2.t2
        error_load = thermal_relaxation_error(self.qb1.t1, self.qb1.t1, 500e-9) # 500ns for 1 distillation round
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(error_load, ['id'])
        self.NOISE_MODEL_DISTILL = noise_model

    def QPA_circuit(self, rho_1, rho_2):
        # https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.77.2818
        rho_1 = qi.DensityMatrix(rho_1)
        rho_2 = qi.DensityMatrix(rho_2)
        rho_full = rho_1.tensor(rho_2)
        c = QuantumCircuit(4)
        c.sx(0)
        c.sxdg(1)
        c.sx(2)
        c.sxdg(3)
        c.cnot(2, 0)
        c.cnot(3, 1)
        rho_corrected = rho_full.evolve(c)

        rho_measure = qi.partial_trace(rho_corrected, [2, 3])
        success_prob = rho_measure.probabilities_dict()['11'] + rho_measure.probabilities_dict()['00']

        measured_state, measured_rho = rho_corrected.measure([0, 1])
        rho_final = qi.partial_trace(measured_rho, [0, 1])
        # ===========================
        # Now apply decay over time it takes to evolve. Can probably just switch this to a circuit noise
        # ============================
        circuit = qiskit.QuantumCircuit(2)
        circuit.set_density_matrix(rho_final)
        circuit.id(0)
        circuit.id(1)
        circuit.save_density_matrix()
        job = qiskit.execute(circuit, self.sim,
                             noise_model=self.NOISE_MODEL_DISTILL,
                             optimization_level = 0)
        dm_noisy = job.result().data()['density_matrix']
        # ============================
        return measured_state, rho_final, success_prob

    # Distillation function for any register
    def distill(self):
        distill_result = self.QPA_circuit(self.qb1.dm,
                                          self.qb2.dm)
        outcome = distill_result[0]
        if outcome == '11' or outcome == '00':
            return distill_result[1]
        return None

    # Get average fidelity of pairs in register
    def get_fidelity(self, state):
        fidel = qi.state_fidelity(state, self.phi_plus)
        return fidel

    def is_pending_output(self):
        if self.output_dm is not None:
            return True
        return False

    def is_available(self):
        if self.output_dm is not None:
            return False
        else:
            return True

    def set_available(self):
        self.available = True

    def apply_noise(self,rho1, rho2, time):
        """
        :param rho1: Density Matrix 1 representing EPR pair 1 state
        :param rho2: Density Matrix 2 representing EPR pair 2 state
        :param time: Time for noise to apply
        :return:
        """
        error_load = thermal_relaxation_error(self.qb1.t1, self.qb1.t1, time)
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(error_load, ['id'])
        circuit = qiskit.QuantumCircuit(2)
        circuit.set_density_matrix(rho1)
        circuit.id(0)
        circuit.id(1)
        circuit.save_density_matrix()
        job = qiskit.execute(circuit, self.sim,
                             noise_model=noise_model,
                             optimization_level=0)
        rho1_noisy = job.result().data()['density_matrix']
        circuit = qiskit.QuantumCircuit(2)
        circuit.set_density_matrix(rho2)
        circuit.id(0)
        circuit.id(1)
        circuit.save_density_matrix()
        job = qiskit.execute(circuit, self.sim,
                             noise_model=noise_model,
                             optimization_level=0)
        rho2_noisy = job.result().data()['density_matrix']
        return rho1_noisy, rho2_noisy

    def input(self, rho1, rho2, time):
        """
        :param time: Time it takes to SWAP in
        :param rho1: Density matrix of Qubit 1 to be distilled
        :param rho2: Density matrix of Qubit 2 to be distilled
        :return: Purified Density matrix
        """
        rho1_noisy, rho2_noisy = self.apply_noise(rho1, rho2, time)
        self.qb1.set_state(rho1_noisy)
        self.qb2.set_state(rho2_noisy)
        self.output_dm = self.distill()

    def apply_noise_transmon(self, dm, time):
        """
        Apply noise model based on Cavity T1/T2 for time 'time'
        :param dm: Density matrix (4x4) that noise model will be applied to
        :param time: Time for T1/T2 decay
        :return: Noisy density matrix
        """
        error_load = thermal_relaxation_error(self.qb1.t1, self.qb1.t2, time)
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(error_load, ['id'])
        # Noise model for read time
        # ============================
        circuit = qiskit.QuantumCircuit(2)
        circuit.set_density_matrix(dm)
        circuit.i(0)
        circuit.i(1)
        circuit.save_density_matrix()
        job = qiskit.execute(circuit, self.sim,
                             noise_model=noise_model,
                             optimization_level=0)
        dm_noisy = job.result().data()['density_matrix']
        return dm_noisy

    def output(self,
               readout_time):
        """
        :param readout_time: Time to readout. Apply T1/T2 decay accordingly
        :return: Output density matrix
        """
        out = copy.copy(self.output_dm)
        out = self.apply_noise_transmon(out, readout_time)
        self.output_dm = None
        return out

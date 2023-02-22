from HarchSim.Device import Cavity, Transmon
import copy
from enum import Enum
import qiskit
import numpy as np
import qiskit.quantum_info as qi
# Import from Qiskit Aer noise module
from qiskit_aer.noise import (NoiseModel, QuantumError, ReadoutError,
                              pauli_error, depolarizing_error, thermal_relaxation_error)


class MemoryMode(Enum):
    LOADING = "loading data"
    READING = "reading data"
    IDLE = "available"
    PENDING_OUTPUT = "data read, pending collection"


class MemoryCell:
    def __init__(self,
                 cavity: Cavity,
                 transmon: Transmon):
        """
        MemoryCell initialisation. MemoryCells are comprised of one transmon coupled to a cavity. Information
        exchange occurs through SWAP operation, whereby data is SWAPped in and out of memory.
        :param cavity: Multimode bosonic Mode cavity describing memory
        :param transmon: Transmon coupled to the Multimode bosonic Mode
        """
        self.cavity = cavity
        self.transmon = transmon
        self.exta_tags = []
        self.available = True
        self.memory = {}
        self.sim = qiskit.Aer.get_backend('aer_simulator_density_matrix')
        self.psi_plus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.psi_minus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, -1, 0], [0, -1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.phi_plus = qi.DensityMatrix(np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]) / 2)
        self.phi_minus = qi.DensityMatrix(np.array([[1, 0, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, 1]]) / 2)

    def initalize_memory(self,
                         extra_tags: list = None):
        """
        Generate a dictionary for self.memory that describes
        :param extra_tags: Extra memory flags if needed. For example, Entanglement Distillation needs a flag
        for number of rounds that have already been distilled.
        :return: None
        """
        for i in range(self.cavity.levels):
            self.memory[i] = {"dm": None,
                              "time": None}
            if extra_tags is not None:
                for tag in extra_tags:
                    self.extra_tags.append(tag)
                    self.memory[i][tag] = None

    def n_slots_available(self):
        """
        Check number of empty modes in memory
        :return: Num empty modes
        """
        avail = 0
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is None:
                avail += 1
        return avail

    def is_slot_available(self):
        """
        Check number of empty modes in memory
        :return: Num empty modes
        """
        avail = 0
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is None:
                return True
        return False

    def qb_in_memory(self):
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                return True
        return False

    def n_qb_in_memory(self):
        """
        Get number of qb in memory
        :return: Num empty modes
        """
        qb = 0
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                qb += 1
        return qb

    def load_into_memory(self,
                         dm,
                         time,
                         extra_info=None):
        """
        Given a DM, transduce into cavity of lowest level available.
        :param extra_info:
        :param time:
        :param dm:
        :return:
        """
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                continue
            else:
                self.memory[i]["dm"] = dm
                self.memory[i]["time"] = time
                if extra_info is not None:
                    assert len(self.extra_tags) == len(extra_info)
                    for val, tag in zip(extra_info, self.extra_tags):
                        self.memory[i][tag] = val
                break
                return True
        return False

    def get_oldest_qubit(self, time):
        # DOES NOT WORK YET
        oldest_qubit_time = -1
        oldest_qubit_index = None
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                t_qubit = time - self.memory[i]["time"]
                if t_qubit > oldest_qubit_time:
                    oldest_qubit_index = i
                    oldest_qubit_time = t_qubit
        return oldest_qubit_index, oldest_qubit_time

    def get_qubit(self):
        """
        Find a qubit in a given memory cell
        :return: Returns index of a level in the cavity that has a qubit
        """
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                return i

    def input(self, dm, time):
        if self.is_slot_available():
            # Noise model for load time
            # ============================
            dm_noisy = self.apply_noise_transmon(dm, time)
            self.load_into_memory(dm_noisy, self.clock.clock + time)
            return True
        print(f"Failed to load into memory, No slots available")
        return False

    def get_list_of_fidelities(self):
        """
        Compare the fidelity of each state in memory with a corresponding bell state.
        Used for finding an appropriate pair to distill together
        :return: List of fidelities
        """
        fids = {}
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                fids[i] = qi.state_fidelity(self.memory[i]["dm"], self.psi_plus)
        return fids

    def output(self, t):
        """
        Get qubit out of memory, apply noise channel to it.
        :return:
        """
        # Get qubit, decay according to the difference in time between clock + time of read and when it was loaded.
        index = self.get_qubit()
        dm = self.memory[index]['dm']
        time = self.memory[index]['time']
        dm_noisy = self.apply_noise_cavity(dm, t + self.clock.clock - time)
        # ============================
        self.memory[index]["time"] = None
        self.memory[index]["dm"] = None
        return dm_noisy, time

    def apply_noise_cavity(self, dm, time):
        """
        Apply noise model based on Cavity T1/T2 for time 'time'
        :param dm: Density matrix (4x4) that noise model will be applied to
        :param time: Time for T1/T2 decay
        :return: Noisy density matrix
        """
        error_load = thermal_relaxation_error(self.cavity.t1, self.cavity.t2, time)
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

    def apply_noise_transmon(self, dm, time):
        """
        Apply noise model based on Cavity T1/T2 for time 'time'
        :param dm: Density matrix (4x4) that noise model will be applied to
        :param time: Time for T1/T2 decay
        :return: Noisy density matrix
        """
        error_load = thermal_relaxation_error(self.transmon.t1, self.transmon.t2, time)
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

    def output_addressed(self, index, t_readout):
        """
        Get qubit out of memory, apply noise channel to it.
        :return:
        """
        # Get qubit, decay according to the difference in time between clock + time of read and when it was loaded.
        dm = self.memory[index]['dm']
        time = self.memory[index]['time']
        dm_noisy = self.apply_noise_cavity(dm, t_readout + self.clock.clock - time)
        # ============================
        self.memory[index]["time"] = None
        self.memory[index]["dm"] = None
        return dm_noisy, time

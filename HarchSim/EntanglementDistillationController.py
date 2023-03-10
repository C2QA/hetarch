from HarchSim.clock import Clock
from enum import Enum
import qiskit.quantum_info as qi
import numpy as np


class MODULE:
    INPUT = "input module"
    MEMORY = "memory module"
    DISTILLATION = "distillation_cell"
    DIST_MEMORY = "distilled memory"


class EntanglementDistillationController:
    """
        EntanglementDistillationController class

        EntanglementDistillationController consumes multiple modules and is the parent microarchitecture controller
        for entanglement distillation. Responsibilities of the controller are to keep track of global information,
        such as distillation progress. Modules must not be able to communicate with each other, and only keep track
        of their local properties. Controllers do data handling and movement of data.

        """

    def __init__(self, clock_speed=1e-9):
        """
        Initialize EntanglementDistillationController object with a dictionary of modules, and a clock
        :param clock_speed: Clock speed in seconds. Lock/unlock checks are done once per cycle
        """
        self.modules = {}
        self.clock = Clock(clock_speed=clock_speed)
        # Set target bell pair states
        self.psi_plus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.psi_minus = qi.DensityMatrix(np.array([[0, 0, 0, 0], [0, 1, -1, 0], [0, -1, 1, 0], [0, 0, 0, 0]]) / 2)
        self.phi_plus = qi.DensityMatrix(np.array([[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]]) / 2)
        self.phi_minus = qi.DensityMatrix(np.array([[1, 0, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [-1, 0, 0, 1]]) / 2)
        self.CYCLES = 5000  # Default Cycle count
        # Set times for operations
        self.T_Catch = None
        self.T_SWAP_INTO_MEMORY = None
        self.T_SWAP_OUT_MEMORY = None
        self.T_READ_INTO_DISTILLATION = None
        self.T_READ_OUT_DISTILLATION = None

    def set_sim_times(self,
                      times: dict):
        """
        Pass a dictionary with the time parameters, which are read and then set for the simulation
        :param times: Dictionary with the keys
        :return:  None
        """
        self.T_Catch = times['t_catch']
        self.T_SWAP_INTO_MEMORY = times['t_swap_into_memory']
        self.T_SWAP_OUT_MEMORY = times['t_swap_out_memory']
        self.T_READ_INTO_DISTILLATION = times['t_read_into_distillation']
        self.T_READ_OUT_DISTILLATION = times['t_read_out_distillation']

    def set_input_module(self, input_module):
        """
        Sets self.modules INPUT to appropriate input module.
        :param input_module: InputModule object representing the Input Module under Modules to the system
        :return: None
        """
        self.modules[MODULE.INPUT] = input_module

    def set_memory_module(self, memory_module):
        """
        Sets self.modules MEMORY to appropriate input module.
         param memory_module: memory_module object representing
        the Memory Module to the system under Modules, comprising a list of memory cells
        :return: None
        """
        self.modules[MODULE.MEMORY] = memory_module

    def set_distillation_module(self, distillation_module):
        """
        Sets self.modules DISTILLATION to appropriate distillation module.
        :param distillation_module: Distillation module object representing the Distillation Module to the system under
        Modules
        :return: None
        """
        self.modules[MODULE.DISTILLATION] = distillation_module

    def set_distilled_memory_module(self, memory_module):
        """
        Sets self.modules DISTILLED MEMORY to appropriate input module.
        :param memory_module: memory_module object representing
        the distilled Memory Module to the system under Modules, comprising a list of memory cells
        :return: None
        """
        self.modules[MODULE.DIST_MEMORY] = memory_module

    def bind_clock_to_modules(self):
        """
        The clock bound to the EntanglementDistillationController is globally available to all modules,
        hence we bind the object to each connected module object
        :return: None
        """
        for module in self.modules.values():
            module.clock = self.clock
            module.bind_clock_to_modules()

    def fetch_raw_epr_pair(self):
        """
        :return: Returns a raw epr pair out of memory
        """
        return self.modules[MODULE.MEMORY].output()

    def distill(self, qubit1, qubit2):
        """
        :param qubit1: Qubit 1 to be distilled
        :param qubit2: Qubit 2 to be distilled
        :return:  Return a distilled single qubit from the distillation protocol
        """
        self.modules[MODULE.DISTILLATION].input(qubit1, qubit2)
        return self.modules[MODULE.DISTILLATION].output()

    def distill_system(self):
        qubit1 = self.fetch_raw_epr_pair()
        qubit2 = self.fetch_raw_epr_pair()
        distilled_qubit = self.distill(qubit1, qubit2)
        self.modules[MODULE.DIST_MEMORY].input(distilled_qubit, 1)

    def tick(self):
        self.clock.tick()

    def summary(self):
        print(f"=== Module Objects ===")
        print(f"=== Input Modules ====\n{self.modules[MODULE.INPUT]}\n" + "=" * 20)
        print(f"=== Memory Module ====\n{self.modules[MODULE.MEMORY]}\n" + "=" * 20)
        print(f"=== Distillation Modules ====\n{self.modules[MODULE.DISTILLATION]}\n" + "=" * 20)
        print(f"=== Distilled Memory Modules ====\n{self.modules[MODULE.DIST_MEMORY]}\n" + "=" * 20)
        print(f"===" * 20)
        print(f"=== Cell Objects ===")
        print(f" ### INPUT ###")
        print(f"=== Input Cells Available ====\n{self.modules[MODULE.INPUT].epr_gen}\n" + "=" * 20)
        print(f"=== Input Cells Locked  ====\n{self.modules[MODULE.INPUT].locked_epr_gen}\n" + "=" * 20)
        print(f" ### MEMORY ###")
        print(f"=== Memory Cells Available  ====\n{self.modules[MODULE.MEMORY].memory}\n" + "=" * 20)
        print(f"=== Memory Cells Locked ====\n{self.modules[MODULE.MEMORY].locked_memory}\n" + "=" * 20)
        print(f" ### DISTILLATION ###")
        print(
            f"=== Distillation Cells Available ====\n{self.modules[MODULE.DISTILLATION].distillation_cells}\n" + "=" * 20)
        print(f"=== Distillation Cells Locked ====\n{self.modules[MODULE.DISTILLATION].locked_cells}\n" + "=" * 20)
        print(f" ### Distilled Memory ###")
        print(f"=== Distilled Memory Cells Available  ====\n{self.modules[MODULE.DIST_MEMORY].memory}\n" + "=" * 20)
        print(f"=== Distilled Memory Cells Locked  ====\n{self.modules[MODULE.DIST_MEMORY].locked_memory}\n" + "=" * 20)

        print(f"===" * 20)

    def summary_memory(self):
        print(f" ===== Input EPR Memory Status ====== ")
        for key,value in self.modules[MODULE.MEMORY].get_n_epr().items():
            print(f"{key} #n EPR: {value}")
        print(f" ===== Distilled EPR Memory Status ====== ")
        for key, value in self.modules[MODULE.MEMORY].get_n_epr().items():
            print(f"{key} #n EPR : {value}")
        print('-'*20)

    def get_fidelity(self, state):
        fidel = qi.state_fidelity(state, self.phi_plus)
        return fidel

    def distilled_to_memory(self):
        """
        Logic implementation for taking a distilled qubit out of a distillation cell, and moving it into
        distilled memory.
        First step of this is to check if this operation can be done at this clock cycle.

        :return: None
        """
        distilled_pending = self.modules[MODULE.DISTILLATION].is_qubit_pending()
        memory_pending = self.modules[MODULE.DIST_MEMORY].is_cell_available()
        if memory_pending and distilled_pending:
            print(f" === D2M FIRING ===")
            dm = self.modules[MODULE.DISTILLATION].get_output(self.T_READ_OUT_DISTILLATION)
            self.modules[MODULE.DIST_MEMORY].input(dm, self.T_SWAP_INTO_MEMORY)

    def distilled_memory_to_distillation(self):
        """
        Logic implementation for taking a distilled pair of qubits, and moving them into a distillation cell.
        First step of this is to check if this operation can be done at this clock cycle.
        :return: None
        """
        ERROR = 0.02
        qubit_available = self.modules[MODULE.DIST_MEMORY].is_same_fidelities(error=ERROR)
        cell_available = self.modules[MODULE.DISTILLATION].is_cell_available()
        if qubit_available and cell_available:
            print(f" === DM2D FIRING ===")
            module1, i, module2, j = self.modules[MODULE.DIST_MEMORY].get_same_fidelities(self.T_SWAP_OUT_MEMORY,
                                                                                          error=ERROR)
            cell = self.modules[MODULE.DISTILLATION].get_available_cell(self.T_READ_INTO_DISTILLATION)
            if module1 == module2:
                dm1, t_qubit1 = module1.output_addressed(i, self.T_SWAP_OUT_MEMORY)
                dm2, t_qubit2 = module2.output_addressed(j, 2 * self.T_SWAP_OUT_MEMORY)
            else:
                dm1, t_qubit1 = module1.output_addressed(i, self.T_SWAP_OUT_MEMORY)
                dm2, t_qubit2 = module2.output_addressed(j, self.T_SWAP_OUT_MEMORY)
            cell.input(dm1, dm2, self.T_SWAP_INTO_MEMORY)

    def check_unlock(self):
        """
        Check if any module needs to be unlocked. This is done by checking if compute_time + lock_time > current_time
        :return:  None
        """
        self.modules[MODULE.MEMORY].check_unlock()
        self.modules[MODULE.DIST_MEMORY].check_unlock()
        self.modules[MODULE.DISTILLATION].check_unlock()
        self.modules[MODULE.INPUT].check_unlock()

    def input_to_memory(self):
        """
        Logic implementation for taking an input pair, and moving it into memory.
        First step of this is to check if this operation can be done at this clock cycle.
        :return:
        """
        input_available = self.modules[MODULE.INPUT].is_input_available()
        cell_available = self.modules[MODULE.MEMORY].is_cell_available()
        if input_available and cell_available:
            # Generate a random catch time
            t_catch = self.T_Catch()
            print(f"I2M FIRING")
            cell = self.modules[MODULE.MEMORY].get_empty_available_memory(self.T_SWAP_INTO_MEMORY)
            input = self.modules[MODULE.INPUT].get_input(t_catch)
            cell.input(input, self.T_SWAP_INTO_MEMORY)

    def memory_to_distillation(self):
        """
        Logic implementation for taking a pair from non-distilled memory,
         and moving it into a distillation cell where it will be distilled.
        First step of this is to check if this operation can be done at this clock cycle.
        :return: None
        """
        qubit_available = self.modules[MODULE.MEMORY].is_two_qubit_available()
        cell_available = self.modules[MODULE.DISTILLATION].is_cell_available()
        if qubit_available and cell_available:
            print(f" === M2D FIRING ===")
            modules = self.modules[MODULE.MEMORY].find_two_qubit_address(self.T_SWAP_INTO_MEMORY)
            cell = self.modules[MODULE.DISTILLATION].get_available_cell(self.T_READ_OUT_DISTILLATION)
            if len(modules) == 1:
                dm1, t_qubit1 = modules[0].output(self.T_SWAP_OUT_MEMORY)
                dm2, t_qubit2 = modules[0].output(self.T_SWAP_OUT_MEMORY)
            else:
                dm1, t_qubit1 = modules[0].output(self.T_SWAP_OUT_MEMORY)
                dm2, t_qubit2 = modules[1].output(self.T_SWAP_OUT_MEMORY)
            cell.input(dm1, dm2, self.T_READ_INTO_DISTILLATION)

    def check_fidelity(self):
        self.modules[MODULE.DIST_MEMORY].track_fidelity()

    def entanglement_distillation_controller_output(self,
                                                    target_fidelity: 0.93):
        """
        :param: target_fidelity: Fidelity you are targetting to distill to. If this is not attainable,
        and memory gets filled, we will just send out the highest fidelity pair.
        Entanglement distillation controller output represents the output of the module.
        Modeled as a steady state system, with an input recieving EPR pair, and an output requester.
        :return: density_matrix
        """
        have_fidelity = self.modules[MODULE.DIST_MEMORY].have_fidelity(target_fidelity)
        if have_fidelity:
            dm = self.modules[MODULE.DIST_MEMORY].get_fidelity_qubit(target_fidelity, self.T_SWAP_OUT_MEMORY)
            print(f"Outputted Density Matrix: {dm}")

    def set_cycles(self, cycles):
        """
        Set number of cycles to sim over
        :param cycles: Num cycles to sim over
        :return: None
        """
        self.CYCLES = cycles

    def run(self):
        """
        This function is responsible for all logic, and distilling the system. All logic is computed etc.

        Each Module has both a list of cells, and a dictionary of locked cells. When a cell is used, it
        becomes locked until it passes a check_unlock. Once it is locked, the modules will not
        check properties of them such as if a qubit is available. This architecture lends to a sequential
        priority check for operations.

        Current implementation is below, where we check once for each operation. If it is desired to do
        each operation as many times as possible, a wrapper in a while True can be implemented until no
        change in the modules occurs.

        """
        for _ in range(self.CYCLES):
            # Conveyor belt model -> We want to distill up to a
            # point of fidelity. If we hit it, we can remove it
            # from memory. If memory gets full, we can just say
            # that there is no way to distill further. Sending out
            # the highest fidelity.
            for _ in range(3):
                self.entanglement_distillation_controller_output(target_fidelity=0.94)
            # ==================================================
            # == Begin by checking highest priority operation ==
            # ====== HighPrio : Check if dmm->distilled    =====
            # ==================================================
            for _ in range(3):
                self.distilled_memory_to_distillation()
            # ==================================================
            # ==        2nd highest priority operation        ==
            # ====== HighPrio : Check if distilled->memory =====
            # ==================================================
            for _ in range(3):
                self.distilled_to_memory()
            # ==================================================
            # ==== Now check 3rd priority operation          ===
            # ===== 3rd Prio : Check if Memory->Distillation ===
            # ==================================================
            for _ in range(3):
                self.memory_to_distillation()
            # ==================================================
            # ==== Now start checking 4th priority operation ===
            # ====== 4th Prio:Check if Input->memory avail =====
            # ==================================================
            for _ in range(3):
                self.input_to_memory()
            # Now we check if we can unlock anything
            self.tick()
            self.check_unlock()
            self.check_fidelity()
            self.summary_memory()
            #print(f"Time: {self.clock.clock}")

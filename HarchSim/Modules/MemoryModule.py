import qiskit
import numpy as np
from datetime import datetime
from HarchSim.StandardCell.MemoryCell import MemoryCell


class MemoryModule:
    """
    MemoryModule class
    """

    def __init__(self, memory: list[MemoryCell]):
        self.memory = memory
        self.locked_memory = {}
        self.clock = None
        # ANALYTICS FUNCTION - This will keep track of if a module is processing or sitting idle.
        for memory in self.memory:
            memory.ACTIVE = []

    def find_empty_available_memory(self):
        for module in self.memory:
            if module.is_slot_available():
                return module
        return False

    def get_empty_available_memory(self):
        for module in self.memory:
            if module.is_slot_available():
                self.locked_memory[module] = {}
                self.locked_memory[module]["time"] = self.clock.clock
                self.locked_memory[module]["compute_time"] = 100e-9
                self.memory.remove(module)
                return module
        return False

    def is_cell_available(self):
        for module in self.memory:
            if module.n_slots_available() > 0:
                return True
        return False

    def is_qubit_available(self):
        for module in self.memory:
            if module.available and module.n_qb_in_memory() > 0:
                return True

    def bind_clock_to_modules(self):
        for module in self.memory:
            module.clock = self.clock

    def is_two_qubit_available(self):
        # To do a distillation round, we have to check two flags.
        # 1. Two qubits available
        # 2. Distillation available. If this is the case, we will lock the 3 and do the compute.
        n_avail = 0
        for module in self.memory:
            if module.n_qb_in_memory() > 0:
                n_avail += module.n_qb_in_memory()
        if n_avail < 2:
            return False
        else:
            return True

    def find_two_qubit_address(self):
        assert self.is_two_qubit_available()
        modules = []
        # We first check if there are two separate memories with 2
        for module in self.memory:
            if module.n_qb_in_memory() > 0:
                modules.append(module)
            if len(modules) == 2:
                break
        # If we return a len(1) list, we know that the 2 qubits exist in that module.
        for module in modules:
            # If it is a len(1) list, you know you have 2 qubits in 1 memory, and hence
            # must lock for 2t
            if len(modules) == 1:
                t = 2
            else:
                t = 1
            self.locked_memory[module] = {}
            self.locked_memory[module]["time"] = self.clock.clock
            self.locked_memory[module]["compute_time"] = module.READ_TIME * t
            self.memory.remove(module)
        return modules

    def is_same_fidelities(self):
        fids = {}
        error = 0.005
        for module in self.memory:
            fids[module] = module.get_list_of_fidelities()
        for cell in fids.keys():
            for i, (key, value) in enumerate(fids[cell].items()):
                for cell2 in fids.keys():
                    for j, (key2, value2) in enumerate(fids[cell2].items()):
                        if i == j and cell == cell2:
                            continue
                        if np.abs(value - value2) < error:
                            return True
        return False

    def have_fidelity(self, fidelity):
        error = 0.005
        for module in self.memory:
            mem = module.get_list_of_fidelities()
            for i, (key, value) in enumerate(mem.items()):
                if fidelity - value < error:
                    return True
        return False

    def get_fidelity_qubit(self, fidelity):
        error = 0.005
        for module in self.memory:
            mem = module.get_list_of_fidelities()
            for i, (key, value) in enumerate(mem.items()):
                if fidelity - value < error:
                    dm = module.output_addressed(i)
                    self.locked_memory[module] = {}
                    self.locked_memory[module]["time"] = self.clock.clock
                    self.locked_memory[module]["compute_time"] = module.READ_TIME
                    self.memory.remove(module)
                    return dm
        return False

    def get_same_fidelities(self):
        fids = {}
        error = 0.005
        for module in self.memory:
            fids[module] = module.get_list_of_fidelities()
        for cell in fids.keys():
            for i, (key, value) in enumerate(fids[cell].items()):
                for cell2 in fids.keys():
                    for j, (key2, value2) in enumerate(fids[cell2].items()):
                        if key == key2 and cell == cell2:
                            continue
                        if np.abs(value - value2) < error:
                            return cell, key, cell2, key2
        return False

    def find_available_qubit(self, clock):
        oldest_memory = None
        oldest_qubit_index = None
        oldest_qubit_time = 0
        for module in self.memory:
            if module.available and module.qb_in_memory():
                index, time = module.get_oldest_qubit(clock)
                if time > oldest_qubit_time:
                    oldest_memory = module
                    oldest_qubit_index = index
                    oldest_qubit_time = time
        if oldest_memory is not None:
            return oldest_memory, oldest_qubit_index, oldest_qubit_time

    def check_unlock(self):
        keys = list(self.locked_memory.keys())
        for key in keys:
            # THIS IS AN ANALYTICAL LINE - THIS WILL APPEND TO MEMORY IF IT WAS COMPUTING. CAN BE REMOVED
            key.ACTIVE.append(1)
            # ====================================
            if self.clock.clock - self.locked_memory[key]["time"] > self.locked_memory[key]["compute_time"]:
                self.memory.append(key)
                self.locked_memory.pop(key)
        # ANALYTICAL LINE - NOT PART OF FUNCTIONALITY
        for memory in self.memory:
            memory.ACTIVE.append(0)
        # ====================================

    def input(self, dm):
        module = self.find_empty_available_memory()
        self.locked_memory[module] = {}
        self.locked_memory[module]["time"] = self.clock.clock
        self.locked_memory[module]["compute_time"] = 100e-9
        self.memory.remove(module)
        module.input(dm)

    # def output(self):
    #     def find_available_qubit(self, clock):
    #         oldest_memory = None
    #         oldest_qubit_index = None
    #         oldest_qubit_time = 0
    #         for module in self.memory:
    #             if module.available and module.qb_in_memory():
    #                 index, time = module.get_oldest_qubit(clock)
    #                 if time > oldest_qubit_time:
    #                     oldest_memory = module
    #                     oldest_qubit_index = index
    #                     oldest_qubit_time = time
    #         if oldest_memory is not None:
    #             return oldest_memory, oldest_qubit_index, oldest_qubit_time

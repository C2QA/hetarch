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

    def find_empty_available_memory(self):
        for module in self.memory:
            if module.is_slot_available() and module.available:
                return module
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
            self.locked_memory[module] = {}
            self.locked_memory[module]["time"] = self.clock.clock
            self.locked_memory[module]["compute_time"] = 500e-9 # Just set this process to be 500us.. oh well
            self.memory.remove(module)
        return modules

    def find_available_qubit(self,clock):
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
            if self.clock.clock - self.locked_memory[key]["time"] > self.locked_memory[key]["compute_time"]:
                self.memory.append(key)
                self.locked_memory.pop(key)

    def input(self, dm):
        module = self.find_empty_available_memory()
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
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
        self.clock = None

    def find_empty_available_memory(self):
        for module in self.memory:
            if module.is_slot_available() and module.available:
                return module
        raise MemoryError("Out of memory in all cavities, or no memory block is available")

    def is_qubit_available(self):
        for module in self.memory:
            if module.available and module.n_qb_in_memory() > 0:
                return True

    def bind_clock_to_modules(self):
        for module in self.memory:
            module.clock = self.clock

    def is_two_qubit_available(self):
        n_avail = 0
        for module in self.memory:
            if module.available and module.n_qb_in_memory() > 0:
                n_avail += 1
        if n_avail < 2:
            return False
        else:
            return True

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
        else:
            return False, False, False

    def find_ready_qubit(self):
        for module in self.memory:
            if module.is_pending():
                return module
        return False

    def check_status_all_modules(self):
        for module in self.memory:
            module.check_status()

    def input(self, dm):
        module = self.find_empty_available_memory()
        module.input(dm)

    def output_request(self, clock):
        mem, index, t = self.find_available_qubit()
        mem.output_request(index)

    def check_status_all_modules(self):
        for module in self.memory:
            module.check_status()

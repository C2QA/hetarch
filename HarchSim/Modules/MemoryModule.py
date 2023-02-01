import qiskit
import numpy as np
from datetime import datetime
from HarchSim.StandardCell.MemoryCell import MemoryCell


class MemoryModule:
    """
    MemoryModule class
    """

    def __init__(self,
                 memory: list[MemoryCell]):
        """
        Initialize a base memory module comprising a list of memory cells
        :param memory: List of MemoryCell objects
        """
        self.memory = memory
        self.locked_memory = {}
        self.clock = None
        # ANALYTICAL FUNCTION - This will keep track of if a module is processing or sitting idle.
        for memory in self.memory:
            memory.ACTIVE = []

    def find_empty_available_memory(self):
        """
        Check if any memory in the self.memory list (if it is in this list, it is unlocked), for an available
        address. If it finds one, return the module that has an available slot. Otherwise, return false
        :return: Memory cell if it has the available slot, otherwise False
        """
        for module in self.memory:
            if module.is_slot_available():
                return module
        return False

    def get_empty_available_memory(self):
        """
        Find a memory that has a slot available, and pull it from the available list. It will lock the memory into
        the locked memory dictionary. The module is now locked
        :return: The module with an available slot. If none available, return False.
        """
        for module in self.memory:
            if module.is_slot_available():
                self.locked_memory[module] = {}
                self.locked_memory[module]["time"] = self.clock.clock
                self.locked_memory[module]["compute_time"] = module.LOAD_TIME
                self.memory.remove(module)
                return module
        return False

    def is_cell_available(self):
        """
        Check if there exists a memory with at least 1 slot available
        :return: True if available, False otherwise
        """
        for module in self.memory:
            if module.n_slots_available() > 0:
                return True
        return False

    def is_qubit_available(self):
        """
        Check if there is a qubit available in one of the available memory
        :return: True if available, False otherwise
        """
        for module in self.memory:
            if module.available and module.n_qb_in_memory() > 0:
                return True
        return False

    def bind_clock_to_modules(self):
        for module in self.memory:
            module.clock = self.clock

    def is_two_qubit_available(self):
        """
        Check if two qubits are available in memory. Preferentially, we do it in parallel,
        but if it is not available, we can pull two qubits from memory.
        :return: True if available, False if not.
        """
        n_avail = 0
        for module in self.memory:
            if module.n_qb_in_memory() > 0:
                n_avail += module.n_qb_in_memory()
        if n_avail < 2:
            return False
        else:
            return True

    def find_two_qubit_address(self):
        """
        Find and retrieve the location of two qubits. If two modules are available and have a qubit available,
        just return the two modules. Otherwise, get two qubits from one memory. This can be seen thgrough
        the length of the modules list (len(modules)). Preferntially, we would like to get two modules,
        however we can fall back on 1 if need be.
        We lock the cells for the length required. If we are reading two out, we will lock the memory module
        for 2*readout length.
        :return: A list of modules with the qubits
        """
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
        """
        For successful distillation, we need to have two pairs at similar fidelities. Hence, we must check
        if we have two qubits at a similar fidelity. Currently, we do O(n^2) checks, but this can be improved
        if memory grows substantially.
        :return: If we have two at similar fidelity, return True, otherwise False
        """
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

    def have_fidelity(self,
                      fidelity,
                      error=0.005):
        """
        Check if a fidelity exists in a memory cell. Logic loops over each memory available and checks
        if it exists
        :param error: Error tolerance for fidelity.
        :param fidelity: Target fidelity within tollerance error
        :return: True if have it, false if not.
        """
        for module in self.memory:
            mem = module.get_list_of_fidelities()
            for i, (key, value) in enumerate(mem.items()):
                if fidelity - value < error:
                    return True
        return False

    def get_fidelity_qubit(self,
                           fidelity,
                           error=0.005):
        """
        Retrieve qubit at fidelity. This will erase it from memory, and return the density
        matrix representing it.
        :param error: Error tolerance for fidelity
        :param fidelity: Target fidelity within tolerance error.
        :return: Density matrix representing qubit. False if no qubit available that is at fidelity.
        """

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
        """
        For the distillation of a distilled pair, we want to make sure that we are distilling an appropriate
        pair. For that, we find the first pair of qubits that are at the same fidelity, and distill them
        :return:cell - the MemoryCell containing qubit1 , key refers to the index of MemoryCell for Qubit1.
        To Access MemoryCell1's Qubit, you use MemoryCell.output_indexed type formatting with the key
        KEY. cell2 is MemoryCell2, and key2 is the key for the qubit in MemoryCell2.
        """
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

    def check_unlock(self):
        """
        Check if any of the MemoryModules need to be unlocked
        :return: None
        """
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
        """
        Input a density matrix to an available memory. Module will become locked for LOAD_TIME
        :param dm: Density matrix representing the qubit being loaded
        :return: None
        """
        module = self.find_empty_available_memory()
        self.locked_memory[module] = {}
        self.locked_memory[module]["time"] = self.clock.clock
        self.locked_memory[module]["compute_time"] = module.LOAD_TIME
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

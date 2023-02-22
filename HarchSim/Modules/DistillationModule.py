from HarchSim.StandardCell.DistillationCell import DistillationCell
import numpy as np


class DistillationModule:
    def __init__(self,
                 distillation_cells: list[DistillationCell]):
        self.distillation_cells = distillation_cells
        self.clock = None
        self.locked_cells = {}

    def find_available_cell(self):
        """
        Loop over each available distillation cell and check whether it is available for distillation
        :return: DistillationCell object if it exists, None if there is no available address
        """
        for cell in self.distillation_cells:
            if cell.is_available():
                return cell
        return None

    def is_cell_available(self):
        """
        Loop over each distillation cell currently unlocked, and check if there is a pending qubit output
        :return: True if no pending qubit in unlocked cells, False if all available cells have
         pending qubits
        """
        for cell in self.distillation_cells:
            if not cell.is_pending_output():
                return True
        return False

    def get_available_cell(self,time):
        """
        Find a distillation cell that is available, and lock it for the compute time of a distillation routine
        :return: DistillationCell object
        """
        for cell in self.distillation_cells:
            if cell.is_available():
                valid_cell = cell
                break
        self.locked_cells[valid_cell] = {}
        self.locked_cells[valid_cell]["time"] = self.clock.clock
        self.locked_cells[valid_cell]["compute_time"] = time
        self.distillation_cells.remove(valid_cell)
        return valid_cell

    def is_qubit_pending(self):
        """
        Opposite of is_cell_available. Checks if there is a pending qubit to be read out
        :return: True if there is a qubit pending, False if no qubits pending
        """
        for cell in self.distillation_cells:
            if cell.is_pending_output():
                return True
        return False

    def bind_clock_to_modules(self):
        """
        Bind the clock object to each individual distillation cell
        :return: True, indicating successful binding
        """
        for module in self.distillation_cells:
            module.clock = self.clock
        return True

    def check_unlock(self):
        """
        Check if the time elapsed since a cell got locked is greater than the compute time. If it is, unlock
        Else, remains locked
        :return: None
        """
        keys = list(self.locked_cells.keys())
        for key in keys:
            if self.clock.clock - self.locked_cells[key]["time"] > self.locked_cells[key]["compute_time"]:
                self.distillation_cells.append(key)
                self.locked_cells.pop(key)

    def input(self,
              qb1: np.array,
              qb2: np.array,
              time):
        """
        :param time: Time to load in
        :param qb1: Density matrix representing EPR Pair of Qubit 1
        :param qb2: Density matrix representing EPR Pair of Qubit 2
        :return: True if available cell to distill. This is only called when we have an available cell.
        This is checked in other functions before calling the logic
        """
        cell = self.find_available_cell()
        if cell is not None:
            cell.input(qb1, qb2, time)
            return True
        return False

    def get_output(self,readout_time):
        """
        Find a distillation cell that is pending a qubit output (through use of cell.is_pending_output()).
        Return the density matrix of one if it is pending, and lock if for the LOAD_TIME
        :return: Density matrix representing a distilled pair.
        """
        for cell in self.distillation_cells:
            if cell.is_pending_output():
                dm = cell.output(readout_time)
                self.locked_cells[cell] = {}
                self.locked_cells[cell]["time"] = self.clock.clock
                self.locked_cells[cell]["compute_time"] = readout_time
                self.distillation_cells.remove(cell)
                return dm

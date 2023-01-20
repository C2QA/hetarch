from HarchSim.Device import Cavity, Transmon
import copy
from enum import Enum

class MemoryMode(Enum):
    LOADING = "loading data"
    READING = "reading data"
    IDLE = "available"
    PENDING_OUTPUT = "data read, pending collection"

class MemoryCell:
    def __init__(self,
                 cavity: Cavity,
                 transmon: Transmon,
                 load_time = 300e-9):
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
        self.LOAD_TIME = load_time

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
                         extra_info = None):
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
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                return i


    def input(self, dm):
        if self.is_slot_available():
            self.load_into_memory(dm, self.clock.clock + self.LOAD_TIME)
            return True
        print(f"Failed to load into memory, No slots available")
        return False

    def output(self):
        index = self.get_qubit()
        dm = self.memory[index]['dm']
        time = self.memory[index]['time']
        self.memory[index]["time"] = None
        self.memory[index]["dm"] = None
        return dm, time


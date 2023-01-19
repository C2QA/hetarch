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
        self.LOCK = None
        self.PENDING_OUTPUT = None
        self.cavity = cavity
        self.transmon = transmon
        self.exta_tags = []
        self.available = True
        self.memory = {}
        self.LOAD_TIME = load_time
        self.PENDING = False
        self.MODE = MemoryMode.IDLE

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
        oldest_qubit_time = 0
        oldest_qubit_index = None
        for i in range(self.cavity.levels):
            if self.memory[i]["dm"] is not None:
                t_qubit = time - self.memory[i]["time"]
                if t_qubit > oldest_qubit_time:
                    oldest_qubit_index = i
                    oldest_qubit_time = t_qubit
        return oldest_qubit_index, oldest_qubit_time

    def set_available(self):
        self.available = True

    def set_unavailable(self):
        self.available = False

    def is_pending(self):
        if self.MODE == MemoryMode.PENDING_OUTPUT:
            return True

    def input(self, dm):
        if self.available is True and self.is_slot_available():
            loaded = self.load_into_memory(dm, self.clock.clock + self.LOAD_TIME)
            self.LOCK = copy.copy(self.clock.clock)
            self.PENDING = False
            self.available = False
            self.MODE = MemoryMode.LOADING
            return True
        print(f"Failed to load into memory, No slots available, or controller unavailable")
        return False

    def input_loading(self):
        if self.LOCK is not None and\
                self.clock.clock - self.LOCK >= self.LOAD_TIME and\
                self.available is False:
            self.PENDING = False
            self.LOCK = None
            self.set_available()
            self.MODE = MemoryMode.IDLE

    def check_status(self):
        if self.MODE is MemoryMode.LOADING:
            self.input_loading()
        elif self.MODE is MemoryMode.READING:
            self.output_pending_check()

    def output_request(self,index):
        if self.available and self.qb_in_memory():
            dm = self.memory[index]['dm']
            time = self.memory[index]['time']
            self.LOCK = copy.copy(self.clock.clock)
            self.set_unavailable()
            self.memory[index]["time"] = None
            self.memory[index]["dm"] = None
            self.PENDING_OUTPUT = (dm, time)
            self.MODE = MemoryMode.READING
            return True
        return False

    def output_pending_check(self):
        if self.LOCK is not None and \
                self.clock.clock - self.LOCK >= self.LOAD_TIME:
            self.PENDING = True
            self.LOCK = None
            self.MODE = MemoryMode.PENDING_OUTPUT

    def output(self):
        if self.MODE is MemoryMode.PENDING_OUTPUT:
            out = copy.copy(self.PENDING_OUTPUT)
            self.PENDING_OUTPUT = None
            self.available = True
            self.PENDING = False
            return out
        else:
            return False


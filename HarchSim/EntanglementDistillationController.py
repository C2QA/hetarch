from HarchSim.clock import Clock

class EntanglementDistillationController:
    """
        EntanglementDistillationController class

        EntanglementDistillationController consumes multiple modules and is the parent microarchitecture controller
        for entanglement distillation. Responsibilities of the controller are to keep track of global information,
        such as distillation progress. Modules must not be able to communicate with each other, and only keep track
        of their local properties. Controllers do data handling and movement of data.

        """

    def __init__(self,clock_speed = 1e-9):
        self.modules = {}
        self.clock = Clock()

    def set_input_module(self, input_module):
        self.modules["input"] = input_module

    def set_memory_module(self,memory_module):
        self.modules["memory"] = memory_module

    def set_distillation_module(self,distillation_module):
        self.modules["distillation"] = distillation_module

    def set_distilled_memory_module(self,memory_module):
        self.modules["distilled_memory"] = memory_module

    def bind_clock_to_modules(self):
        for module in self.modules.values():
            module.clock = self.clock
            module.bind_clock_to_modules()

    def store_raw_epr_pair(self):
        """
        Loads a raw EPR pair into memory
        """
        dm, time = self.modules["input"].output()
        self.modules["memory"].input(dm)

    def fetch_raw_epr_pair(self):
        """
        :return: Returns a raw epr pair out of memory
        """
        return self.modules["memory"].output()

    def distill(self, qubit1, qubit2):
        """
        :param qubit1: Qubit 1 to be distilled
        :param qubit2: Qubit 2 to be distilled
        :return:  Return a distilled single qubit from the distillation protocol
        """
        self.modules["distillation"].input(qubit1, qubit2)
        return self.modules["distillation"].output()

    def distill_system(self):
        qubit1 = self.fetch_raw_epr_pair()
        qubit2 = self.fetch_raw_epr_pair()
        distilled_qubit = self.distill(qubit1, qubit2)
        self.modules["distilled_memory"].input(distilled_qubit, 1)

    def tick(self):
        self.clock.tick()

    def summary(self):
        print(f"=== Input Modules ====\n{self.modules['input']}\n"+"="*20)
        print(f"=== Memory Module ====\n{self.modules['memory']}\n"+"="*20)
        print(f"=== Distillation Modules ====\n{self.modules['distillation']}\n"+"="*20)
        print(f"=== Distilled Memory Modules ====\n{self.modules['distilled_memory']}\n"+"="*20)

    def run(self):
        """
        This function is responsible for all logic, and distilling the system. All logic is computed etc.

        Logic is priority based, and clock based.
        Each loop will check for the highest priority operation, and then in decreasing order of priority continue.
        Highest priority is to move a distilled pair from Distillation Module into the Distillation Memory
            Logic for this to be available is both Modules Distillation to have an AVAILABLE flag, and
            memory to have two qubit available flags. If this is true, we distill. There is a preference in distillation
            of choosing the highest priority pair to distill. So we begin by computing that.
        Second-highest priority is to move from the Memory Module into the Distillation Module
        The Lowest priority is to call the Input Module and move a uqbit into the Memory Module.
        :return:
        """
        MEMORY_TO_DISTILL = 100e-9
        DISTILL_TO_MEMORY = 100e-9
        INPUT_TO_MEMORY = 100e-9
        for _ in range(1000):
            self.tick()
            # ==================================================
            # == Begin by checking highest priority operation ==
            # ====== HighPrio : Check if distilled->memory =====
            # ==================================================
            distilled_pending = self.modules["distillation"].is_qubit_pending()
            memory_pending = self.modules["distilled_memory"].is_cell_available()
            if memory_pending and distilled_pending:
                dm = self.modules['distillation'].get_output()
                self.modules["distilled_memory"].input(dm)
            # ==================================================
            # ==== Begin by checking 2nd  priority operation ===
            # ====== 2nd Prio : Check if distilled->memory =====
            # ==================================================
            qubit_available = self.modules["memory"].is_two_qubit_available()
            cell_available = self.modules["distillation"].is_cell_available()
            if qubit_available and cell_available:
                modules = self.modules["memory"].find_two_qubit_address()
                cell = self.modules["distillation"].get_available_cell()
                if len(modules) == 1:
                    dm1, t_qubit1 = modules[0].output()
                    dm2, t_qubit2= modules[0].output()
                else:
                    dm1, t_qubit1 = modules[0].output()
                    dm2, t_qubit2 = modules[1].output()
                cell.input(dm1,dm2)
            # Now we check if we can unlock anything
            self.modules["memory"].check_unlock()
            print(f"Time: {self.clock.clock}")

import numpy as np


class BaseDevice:
    def __init__(self,
                 t1: int,
                 t2: int):
        """
        :param t1: T1 time describing device. Units are s
        :param t2: T2 time describing device. Units are s
        """
        self.t1 = t1
        self.t2 = t2
        self.GATESET = {}
        self.dm = None

    def add_gateset(self, gate, matrix):
        """
        Add a specific gate to the Transmon gate set
        Only single qubit gates.
        :param gate:  Single gate name, such as 'X','Z','SX'
        :param matrix: Matrix representing respective gate, such as [[0,1],[1,0]] in numpy form
        :return: None
        """
        self.GATESET[gate] = matrix

    def add_gatesets(self,
                     gates: list[str],
                     matrices: list[np.array]):
        """
        Add a list of gates to the Transmon gate set
        Only single qubit gates.
        :param gates: List of gate names, such as ['X','Z','SX']
        :param matrices: Matrices representing each respective gate. Indices must be equal.
        :return:
        """
        for gate,matrix in zip(gates,matrices):
            self.GATESET[gate] = matrix

    def apply_gate(self,
                   gate):
        if gate not in self.GATESET.keys():
            print(f"Failed to apply {gate}, not part of gate set")
        else:
            self.dm = self.GATESET[gate]@self.dm@self.GATESET[gate].transpose().conjugate()

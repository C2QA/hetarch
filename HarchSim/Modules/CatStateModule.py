import qiskit
import numpy as np
from datetime import datetime
import qiskit.quantum_info as qi
from qiskit import QuantumCircuit
import copy
from qiskit_aer.noise import (NoiseModel, thermal_relaxation_error)

class CatStateModule:
    def __init__(self):
        pass
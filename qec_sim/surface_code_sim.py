import numpy as np
import stim
import sinter

class DataQubit():

    def __init__(self, name, coords) -> None:
        self.name = name
        self.coords = coords

    def __repr__(self) -> str:
        return f'{self.name}, Coords: {self.coords}'

class MeasureQubit():

    def __init__(self, name, coords, data_qubits, basis) -> None:
        self.name = name
        self.coords = coords
        self.data_qubits = data_qubits
        self.basis = basis

    def __repr__(self):
        return f'|{self.name}, Coords: {self.coords}, Basis: {self.basis}, Data Qubits: {self.data_qubits}|'

#TODO: change all the noises
class LogicalQubit():
    def __init__(self, d: int, gate2_err:float, params:dict) -> None:
        self.d = d
        
        self.gate2_err = gate2_err
        #decide whether to add readout time and error
        self.err_multipler = gate2_err/params['data_ancilla_2q_err']
        self.readout_err = params['readout_err'] * self.err_multipler
        self.gate1_err_syn = params['ancilla_1q_err'] * self.err_multipler
        #self.reset_err = params['reset_err'] * self.err_multipler
        self.data_T1 = params['data_T1']
        self.data_T2 = params['data_T2']
        self.ancilla_T1 = params['ancilla_T1']
        self.ancilla_T2 = params['ancilla_T2']
        self.time_measurement_ancilla = params['time_measurement_ancilla']
        #self.time_reset_ancilla = params['time_reset_ancilla']
        self.time_1q_ancilla = params['time_1q_ancilla']
        self.time_2q = params['time_2q']

        self.data = [DataQubit((d*x + y), (2*x, 2*y)) for x in range(d) for y in range(d)]
        data_matching = [[None for _ in range(2*d)] for _ in range(2*d)]
        for data_q in self.data:
            data_matching[data_q.coords[0]][data_q.coords[1]] = data_q
        q = d*d
        self.x_ancilla = []
        self.z_ancilla = []
        for x in range(-1, d):
            for y in range(-1, d):
                if (x + y) % 2 == 1 and x != -1 and x != d - 1:# is X syndrome
                    coords = (2*x + 1, 2*y + 1)
                    data_qubits = []
                    if y != d - 1: # not on right edge
                        data_qubits += [data_matching[coords[0] + 1][coords[1] + 1], data_matching[coords[0] - 1][coords[1] + 1]]
                    else:
                        data_qubits += [None, None]
                    if y != -1: # not on left edge
                        data_qubits += [data_matching[coords[0] + 1][coords[1] - 1], data_matching[coords[0] - 1][coords[1] - 1]]
                    else:
                        data_qubits += [None, None]
                    measure_q = MeasureQubit(q, coords, data_qubits, "X")
                    self.x_ancilla.append(measure_q)
                elif (x + y) % 2 == 0 and y != -1 and y != d - 1:# is Z syndrome
                    coords = (2*x + 1, 2*y + 1)
                    data_qubits = []
                    if x != d - 1: # not on lower edge
                        data_qubits += [data_matching[coords[0] + 1][coords[1] + 1], data_matching[coords[0] + 1][coords[1] - 1]]
                    else:
                        data_qubits += [None, None]
                    if x != -1: # not on upper edge
                        data_qubits += [data_matching[coords[0] - 1][coords[1] + 1], data_matching[coords[0] - 1][coords[1] - 1]]
                    else:
                        data_qubits += [None, None]
                    measure_q = MeasureQubit(q, coords, data_qubits, "Z")
                    self.z_ancilla.append(measure_q)
                q += 1

        self.all_qubits = ([measure.name for measure in self.x_ancilla]+
                            [measure.name for measure in self.z_ancilla]+
                            [data.name for data in self.data])
        self.all_qubits.sort()

        self.observable = []
        for x in range(d):
            self.observable.append(data_matching[2*x][0])

        self.meas_record = []

    def apply_1gate(self, circ, gate, qubits):
        circ.append(gate, qubits)
        if self.faulty_qubits:
            if self.faulty_factor > 1:
                circ.append("DEPOLARIZE1", self.faulty_qubits, self.faulty_factor * self.gate1_err)
            else:
                circ.append("DEPOLARIZE1", self.faulty_qubits, self.faulty_factor * 0.75)
        non_faulty_qs = [q for q in self.all_qubits if self.faulty_qubits is None or q not in self.faulty_qubits]
        circ.append("DEPOLARIZE1", non_faulty_qs, self.gate1_err)
        circ.append("TICK")

    def apply_2gate(self, circ, gate, qubits):
        circ.append(gate, qubits)
        faulty_qs = []
        if self.faulty_qubits:
            for i in range(len(qubits) // 2):
                if qubits[2*i] in self.faulty_qubits or qubits[2*i+1] in self.faulty_qubits:
                    faulty_qs += [qubits[2*i],qubits[2*i+1]]
        non_faulty_qs = [q for q in qubits if q not in faulty_qs]
        circ.append("DEPOLARIZE2", non_faulty_qs, self.gate2_err)
        if len(faulty_qs) > 0:
            if self.faulty_factor > 1:
                circ.append("DEPOLARIZE2", faulty_qs, self.faulty_factor * self.gate2_err)
            else:
                circ.append("DEPOLARIZE2", faulty_qs, self.faulty_factor * 15./16.)

        #apply 1Q depolarizing errors on idle qubits
        if len(qubits) < len(self.all_qubits):
            idle_qubits = list(set(self.all_qubits) - set(qubits))
            faulty_idle_qs = [q for q in idle_qubits if self.faulty_qubits and q in self.faulty_qubits]
            non_faulty_idle_qs = [q for q in idle_qubits if self.faulty_qubits is None or q not in self.faulty_qubits]
            circ.append("DEPOLARIZE1", non_faulty_idle_qs, self.gate1_err)
            if len(faulty_idle_qs) > 0:
                if self.faulty_factor > 1:
                    circ.append("DEPOLARIZE1", faulty_idle_qs, self.faulty_factor * self.gate1_err)
                else:
                    circ.append("DEPOLARIZE1", faulty_idle_qs, self.faulty_factor * 0.75)
        circ.append("TICK")

    def reset_meas_qubits(self, circ, op, qubits, last=False):
        if op == "R":
            circ.append(op, qubits)
        faulty_qs = [q for q in qubits if self.faulty_qubits and q in self.faulty_qubits]
        non_faulty_qs = [q for q in qubits if self.faulty_qubits is None or q not in self.faulty_qubits]
        circ.append("X_ERROR", non_faulty_qs, self.readout_err)
        if len(faulty_qs) > 0:
            if self.faulty_factor > 1:
                circ.append("X_ERROR", faulty_qs, self.faulty_factor * self.readout_err)
            else:
                circ.append("X_ERROR", faulty_qs, self.faulty_factor * 0.5)
        if op == "M" or op == "MR":
            circ.append(op, qubits)
            # Update measurement record indices
            meas_round = {}
            for i in range(len(qubits)):
                q = qubits[-(i + 1)]
                meas_round[q] = -(i + 1)
            for round in self.meas_record:
                for q, idx in round.items():
                    round[q] = idx - len(qubits)
            self.meas_record.append(meas_round)
        if not last and len(qubits) < len(self.all_qubits):
            idle_qubits = list(set(self.all_qubits) - set(qubits))
            faulty_idle_qs = [q for q in idle_qubits if self.faulty_qubits and q in self.faulty_qubits]
            non_faulty_idle_qs = [q for q in idle_qubits if self.faulty_qubits is None or q not in self.faulty_qubits]
            circ.append("DEPOLARIZE1", non_faulty_idle_qs, self.gate1_err)
            if len(faulty_idle_qs) > 0:
                if self.faulty_factor > 1:
                    circ.append("DEPOLARIZE1", faulty_idle_qs, self.faulty_factor * self.gate1_err)
                else:
                    circ.append("DEPOLARIZE1", faulty_idle_qs, self.faulty_factor * 0.75)


    def get_meas_rec(self, round_idx, qubit_name):
        return stim.target_rec(self.meas_record[round_idx][qubit_name])

    def syndrome_round(self, circ: stim.Circuit, first=False, double=False) -> None:
        all_syn = ([measure.name for measure in self.x_ancilla]+
                  [measure.name for measure in self.z_ancilla])
        if first:
            self.reset_meas_qubits(circ, "R", self.all_qubits)
        else:
            self.reset_meas_qubits(circ, "R", all_syn)
        circ.append("TICK")
        self.apply_1gate(circ, "H", [measure.name for measure in self.x_ancilla])

        for i in range(4):
            err_qubits = []
            for measure_x in self.x_ancilla:
                if measure_x.data_qubits[i] != None:
                    err_qubits += [measure_x.name, measure_x.data_qubits[i].name]
            for measure_z in self.z_ancilla:
                if measure_z.data_qubits[i] != None:
                    err_qubits += [measure_z.data_qubits[i].name, measure_z.name]
            self.apply_2gate(circ,"CX",err_qubits)

        self.apply_1gate(circ, "H", [measure.name for measure in self.x_ancilla])

        self.reset_meas_qubits(circ, "M", all_syn)

        if not first:
            circ.append("SHIFT_COORDS", [], [0.0, 0.0, 1.0])
            for ancilla in self.x_ancilla + self.z_ancilla:
                circ.append("DETECTOR", [self.get_meas_rec(-1, ancilla.name), self.get_meas_rec(-2, ancilla.name)], ancilla.coords + (0,))
        else:
            for ancilla in self.z_ancilla:
                circ.append("DETECTOR", self.get_meas_rec(-1, ancilla.name), ancilla.coords + (0,))
        circ.append("TICK")
        return circ

    def generate_stim(self, rounds) -> stim.Circuit:
        all_data = [data.name for data in self.data]
        circ = stim.Circuit()

        # Coords
        for data in self.data:
            circ.append("QUBIT_COORDS", data.name, data.coords)
        for x_ancilla in self.x_ancilla:
            circ.append("QUBIT_COORDS", x_ancilla.name, x_ancilla.coords)
        for z_ancilla in self.z_ancilla:
            circ.append("QUBIT_COORDS", z_ancilla.name, z_ancilla.coords)

        self.syndrome_round(circ, first=True)
        circ.append(stim.CircuitRepeatBlock(rounds - 1, self.syndrome_round(stim.Circuit())))

        self.reset_meas_qubits(circ, "M", all_data,last=True)
        circ.append("SHIFT_COORDS", [], [0.0, 0.0, 1.0])

        for ancilla in self.z_ancilla:
            circ.append("DETECTOR", [self.get_meas_rec(-1, data.name) for data in ancilla.data_qubits if data is not None] +\
                        [self.get_meas_rec(-2, ancilla.name)], ancilla.coords + (0,))

        circ.append("OBSERVABLE_INCLUDE", [self.get_meas_rec(-1, data.name) for data in self.observable], 0)

        return circ
# ----------------------------------------------------------------------
# QASMBench: A Low-level OpenQASM Benchmark Suite
# ----------------------------------------------------------------------
# Samuel Stein, Ang Li
# Pacific Northwest National Laboratory(PNNL), U.S.
# BSD Lincese.
# Created 06/10/2021.
# PNNL IPID: 31924-E, IR: PNNL-SA-153380, PNNL-SA-162867, ECCN:EAR99
# ----------------------------------------------------------------------

import networkx as nx
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.converters import circuit_to_dag
from qiskit.transpiler.passes import RemoveBarriers

# Metrics required for QASM Bench:
# - Binary matrix representing circuit
# - Depth of each Qubit (Number of operations on each qubit)
# - Number of Qubits in the circuit
# - Number of 2-Qubit gates
# - Number of measurements
# - Number of 1-Qubit gates


# TODO: Refactor for a cleaner code
# TODO⚠: revise metric definitions
class DAGMetric:
    """
    QMetric describes the metric class for analysing QASM. On calling ".evaluate_qasm", the QASM will be evaluated
    through each of the "compute_...." clauses below under ".evaluate_qasm". To change any of the tags that it generates,
    or if you need to change the metrics being calculated, look under evaluate_qasm().
    """

    def __init__(self, qasm, user_defined_gates: list = []):
        """
        QMetric initialisation function.
        :param qasm: QASM string representing the circuit to be analysed.
        """
        self.USER_DEFINED_GATES = user_defined_gates
        self.qasm = qasm

        self.get_circuit()
        self.get_dag()

    def get_circuit(self, decompose=True, remove_barriers=True):
        self.circuit = QuantumCircuit.from_qasm_str(self.qasm)
        if remove_barriers:
            self.circuit = RemoveBarriers()(self.circuit)
        if decompose and len(self.USER_DEFINED_GATES) > 0:
            self.decompose_circuit()

    def decompose_circuit(self):
        self.circuit = self.circuit.decompose(
            gates_to_decompose=self.USER_DEFINED_GATES
        )

    def get_dag(self):
        self.dag = circuit_to_dag(self.circuit)

    # PROPERTIES
    @property
    def width(self):
        return self.dag.num_qubits()

    @property
    def clbit_count(self):
        return self.dag.num_clbits()

    @property
    def depth(self):
        return self.dag.depth()

    @property
    def gate_count(self):
        return len(self.dag.gate_nodes())

    @property
    def measurement_count(self):
        self.dag_operations = self.dag.count_ops()
        return self.dag_operations["measure"]

    @property
    def dual_gate_count(self):
        return len(self.dag.two_qubit_ops())

    @property
    def single_gate_count(self):
        return self.gate_count - self.dual_gate_count

    @property
    def total_gate_count(self):
        return self.dual_gate_count + self.single_gate_count

    @property
    def qubit_depths(self):
        qubit_depths = {}
        for _iqubit in range(self.dag.num_qubits()):
            qubit_depths[_iqubit] = 0
        layers = list(self.dag.layers())  # Convert generator to list

        for i, layer in enumerate(layers):
            layer_depth = i + 1  # Depth is 1-based index

            op_nodes = layer["graph"].op_nodes(include_directives=False)
            for op_node in op_nodes:
                # op_node.qargs gives a list of Qubit objects involved in the operation
                for qarg in op_node.qargs:
                    dag_index = self.dag.find_bit(qarg).index
                    if dag_index in qubit_depths:
                        qubit_depths[dag_index] = layer_depth

        return qubit_depths

    @property
    def circuit_matrix(self):
        """
        Generate a matrix representing the time evolution of the circuit. 1 represents a qubit being active, 0 inactive.
        :return:
        """
        circ_matrix = np.zeros((self.width, self.depth))
        for i, layer in enumerate(self.dag.layers()):
            for op in layer["partition"]:
                for qubit in op:
                    circ_matrix[qubit._index, i] = 1
        return circ_matrix

    @property
    def maximum_qubit_depth(self):
        qubit_depths = self.qubit_depths
        max_value = max(qubit_depths.values())  # maximum value
        max_keys = [k for k, v in qubit_depths.items() if v == max_value]
        return max_keys, max_value

    @property
    def max_dual_qubit_depth(self):
        return self.dual_gate_count_id[self.maximum_qubit_depth[0][0]]

    @property
    def dual_gate_count_id(self):
        qubit_twoqubit_gates = {}
        for _iqubit in range(self.width):
            qubit_twoqubit_gates[_iqubit] = 0

        for node in self.dag.op_nodes(include_directives=False):
            if isinstance(node.op, Gate) and len(node.qargs) == 2:
                q1_obj, q2_obj = node.qargs
                try:
                    idx1 = self.dag.find_bit(q1_obj).index
                    idx2 = self.dag.find_bit(q2_obj).index
                except:
                    print(
                        f"Warning: Could not find qubit {q1_obj} or {q2_obj} "
                        f"from DAG node '{node.op.name}' in circuit. Skipping node."
                    )
                    continue  # Skip this node if qubit can't be found

                qubit_twoqubit_gates[idx1] += 1
                qubit_twoqubit_gates[idx2] += 1

        return qubit_twoqubit_gates

    # METRIC DEFINITIONS:
    # ----------------------------
    # Calculate Gate Density,
    # ----------------------------
    def calc_operation_density(self):
        """
        Compute Operation Density and set self.operation_density (Known as Gate Density in QASMBench)
        :return: None
        """
        self.entanglement = len(self.dag.two_qubit_ops()) / len(self.dag.gate_nodes())
        self.operation_density = (self.single_gate_count + 2 * self.dual_gate_count) / (
            self.depth * self.width
        )

    # ----------------------------
    # Calculate Measurement Density,
    # ----------------------------
    def calc_measurement_density(self):
        """
        Compute Measurement Density and set self.measurement_density (Known as Measurement Ratio in QASMBench)
        :return: None
        """
        self.measurement_ratio = (
            np.log(self.circuit_matrix.shape[0] * self.depth) / self.measurement_count
        )

    # ----------------------------
    # Calculate Retention Lifespan
    # ----------------------------
    def calc_fdm(self):
        """
        Compute Retention Lifespan from QASMBench and set self.fdm
        :return: None
        """
        self.fdm = np.log(self.depth)

    def calc_size_factor(self):
        """
        Compute Size Factor of circuit
        :return:  None
        """
        self.size_factor = np.log(self.gate_count)

    # ----------------------------
    # Calculate Quantum Area
    # ----------------------------
    def calc_quantum_area(self):
        """
        Compute Application Time in time steps (number of "evolutions"), and compute the circuit area
        :return: None
        """
        self.application_time = self.circ_matrix.shape[1]
        self.quantum_area = self.application_time * self.width

    # ----------------------------
    # Calculate described entanglement variance from QASMBench
    # ----------------------------
    def calc_entanglement_variance(self):
        """
        Compute Entanglement Variance as described in QASMBench
        :return: None
        """
        avg_cnot = 2 * self.dual_gate_count / self.width
        print(self.dual_gate_count)
        print(self.dual_gate_count_id)
        numerator = 0
        for value in list(self.dual_gate_count_id.values()):
            numerator += np.square(value - avg_cnot)
        numerator = np.log(numerator + 1)
        self.entanglement_variance = numerator / self.width

    def compute_communication(self):
        """
        Compute Communication metric as described in SupermarQ
        :return: None
        """
        num_qubits = self.width
        graph = nx.Graph()
        for op in self.dag.two_qubit_ops():
            q1, q2 = op.qargs
            graph.add_edge(q1._index, q2._index)
        degree_sum = sum([graph.degree(n) for n in graph.nodes])
        self.communication = degree_sum / (num_qubits * (num_qubits - 1))

    def compute_liveness(self):
        """
        Compute Liveness metric as described in SupermarQ
        :return: None
        """
        num_qubits = self.width
        activity_matrix = np.zeros((num_qubits, self.dag.depth()))
        for i, layer in enumerate(self.dag.layers()):
            for op in layer["partition"]:
                for qubit in op:
                    activity_matrix[qubit._index, i] = 1
        self.liveness = np.sum(activity_matrix) / (num_qubits * self.dag.depth())

    def compute_parallelism(self):
        """
        Compute Parallelism metric as described in SupermarQ
        :return: None
        """
        self.dag.remove_all_ops_named("barrier")
        self.parallelism = max(
            1 - (self.circuit.depth() / len(self.dag.gate_nodes())), 0
        )

    def compute_measurement(self):
        """
        Compute Measurement metric as described in SupermarQ
        :return: None
        """
        temporary_circuit = self.circuit.copy()
        temporary_circuit.remove_final_measurements()
        dag = circuit_to_dag(temporary_circuit)
        reset_moments = 0
        gate_depth = dag.depth()
        for layer in dag.layers():
            reset_present = False
            for op in layer["graph"].op_nodes():
                if op.name == "reset":
                    reset_present = True
            if reset_present:
                reset_moments += 1

        self.measurement = reset_moments / gate_depth

    def compute_entanglement(self):
        """
        Compute Entanglement metric as described in SupermarQ
        :return: None
        """
        self.entanglement = len(self.dag.two_qubit_ops()) / len(self.dag.gate_nodes())

    def compute_depth(self):
        """
        Compute Depth metric as described in SupermarQ
        :return: None
        """
        n_ed = 0
        two_q_gates = set([op.name for op in self.dag.two_qubit_ops()])
        for name in two_q_gates:
            try:
                n_ed += self.dag.count_ops_longest_path()[name]
            except KeyError:
                continue
        n_e = len(self.dag.two_qubit_ops())
        if n_ed == 0:
            self.supermarq_depth = 0
        if n_e == 0:
            self.supermarq_depth = 0
        else:
            self.supermarq_depth = n_ed / n_e

    # COMPUTE METRICS
    def evaluate_qasm(self):
        """
        Call this function on a QMetric object to compute metrics.
        :return: A dictionary containing information about the QASM, and respective metrics from SupermarQ and QASMBench
        """
        self.calc_operation_density()
        self.calc_measurement_density()
        self.calc_fdm()
        self.calc_size_factor()
        self.calc_entanglement_variance()
        self.compute_communication()
        self.compute_depth()
        self.compute_liveness()
        self.compute_entanglement()
        self.compute_measurement()
        self.compute_parallelism()
        print("-" * 10 + "Baseline Metrics" + "-" * 10)
        print(f"Qubit Count: {self.width}")
        print(f"Maximum Qubit Depth: {self.maximum_qubit_depth[1]}")
        print(f"Maximum Qubit Depth ID: {self.maximum_qubit_depth[0][0]}")
        print(f"Single Gate Count: {self.single_gate_count}")
        print(f"Dual Gate Count: {self.dual_gate_count}")
        print("-" * 10 + "Calculated Metrics" + "-" * 10)
        print(f"---QASMBENCH METRICS---")
        print(
            f"Gate Density: {self.operation_density:.3f}\n"
            f"Retention Lifespan: {self.fdm:.3f}\n"
            f"Measurement Density: {self.measurement_ratio:.3f}\n"
            f"Entanglement Variance : {self.entanglement_variance:.3f}\n"
        )
        print(f"---SUPERMARQ METRICS---")
        print(
            f"Communication: {self.communication}\n"
            f"Liveness: {self.liveness}\n"
            f"Parallelism: {self.parallelism}\n"
            f"Entanglement: {self.entanglement}\n"
            f"Depth: {self.supermarq_depth}\n"
            f"Measurement: {self.measurement}"
        )
        return {
            "qubit_count": self.width,
            # Circuit depth is defined in calculations below, therefore we need not a function, same as width
            "circuit_depth": self.depth,
            "circuit_width": self.width,
            "retention_lifespan": self.fdm,
            "gate_density": self.operation_density,
            "dual_gate_count": self.dual_gate_count,
            "measurement_density": self.measurement_ratio,
            "size_factor": self.size_factor,
            "gate_count": self.total_gate_count,
            "entanglement_variance": self.entanglement_variance,
            "circuit_depth": self.circuit_matrix.shape[1],
            "communication_supermarq": self.communication,
            "measurement_supermarq": self.measurement,
            "depth_supermarq": self.supermarq_depth,
            "entanglement_supermarq": self.entanglement,
            "parallelism_supermarq": self.parallelism,
            "liveness_supermarq": self.liveness,
        }

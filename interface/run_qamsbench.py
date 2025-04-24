from qasmbenchmark import QASMBenchmark

# path to the root directory of QASMBench
path = "./"

# selected category for QASMBench
category = "small"

# select only the circuits with the number of qubits in the list
num_qubits_list = list(range(3, 5))

# whether to remove the final measurement in the circuit
remove_final_measurements = True

# whether use qiskit.transpile() to transpile the circuits (note: must provide qiskit backend)
do_transpile = True

# arguments for qiskit.transpile(). backend should be provide at least
transpile_args = {}

bm = QASMBenchmark(
    path,
    category,
    num_qubits_list=num_qubits_list,
    remove_final_measurements=remove_final_measurements,
    do_transpile=do_transpile,
    **transpile_args,
)

for _circuit_name in bm.circ_name_list:
    _circuit = bm.get(_circuit_name)
    print(_circuit_name)
    # FIXME: plot is not shown
    _circuit.draw()

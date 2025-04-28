import os

from qasmbenchmark import QASMBenchmark

_pwd = os.getcwd()

# path to the root directory of QASMBench
path = _pwd

# selected category for QASMBench
category = "small"

# select only the circuits with the number of qubits in the list
num_qubits_list = list(range(3, 4))

# whether to remove the final measurement in the circuit
remove_final_measurements = True

# whether use qiskit.transpile() to transpile the circuits (note: must provide qiskit backend)
do_transpile = True

# arguments for pyqcc
# FIXME: execution does work always, depends on the type of circuit
SERVICE_OR_SDK = "qiskit"
COMPILER_NAME = "qiskit"
OPTIMIZATION_LEVEL = 2
EXECUTION_TYPE = "off"
PLOT_OUTPUT = True

# FIXME: There is weird bug with IQM
providers_backends = {
    "aqt": "offline_simulator_noise",
    "ibmq": "fake_lima",
    "iqm": "fake_deneb",
}

for provider, backend in providers_backends.items():
    output_dir = f"compiled/{provider}_{backend}/{category}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.chdir(output_dir)

    transpile_args = {
        "service_or_sdk": SERVICE_OR_SDK,
        "provider_name": provider,
        "backend_name": backend,
        "compiler_name": COMPILER_NAME,
        "optimization_level": OPTIMIZATION_LEVEL,
        "execution_type": EXECUTION_TYPE,
        "plot_output": PLOT_OUTPUT,
        "no_pyqcc_env": False,
        "container": False,
    }

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

    os.chdir(_pwd)

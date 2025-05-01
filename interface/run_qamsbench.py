import concurrent.futures
import os

from qasmbenchmark import QASMBenchmark

_pwd = os.getcwd()

# path to the root directory of QASMBench
path = _pwd

# selected category for QASMBench
category = "programs/small"

# select only the circuits with the number of qubits in the list
num_qubits_list = list(range(3, 5))

# whether to remove the final measurement in the circuit
remove_final_measurements = False

# whether use qiskit.transpile() to transpile the circuits (note: must provide qiskit backend)
do_transpile = True

# arguments for pyqcc
SERVICE_OR_SDK = "qiskit"
COMPILER_NAME = "qiskit"
OPTIMIZATION_LEVEL = 2
EXECUTION_TYPE = "off"
PLOT_OUTPUT = True

PROVIDERS_BACKENDS = {
    "aqt": "offline_simulator_noise",
    "ibmq": "fake_lima",
    "iqm": "fake_apollo",
}

# max workers
MAX_WORKERS = 3


def process_provider_backend(provider, backend):
    output_dir = f"{path}/compiled/{provider}_{backend}/{category}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    original_dir = os.getcwd()
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

    os.chdir(original_dir)


with concurrent.futures.ProcessPoolExecutor(MAX_WORKERS) as executor:
    list(
        executor.map(
            process_provider_backend,
            PROVIDERS_BACKENDS.keys(),
            PROVIDERS_BACKENDS.values(),
        )
    )

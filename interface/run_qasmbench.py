import argparse
import os

from qasmbenchmark import QASMBenchmark


def tuple_of_ints(arg: str) -> tuple[int, int]:
    _map = map(int, arg.split(","))
    return tuple(_map)


parser = argparse.ArgumentParser(description="Process QASMBenchmark settings")

# Add arguments for variables
parser.add_argument(
    "--service_or_sdk", type=str, default="qiskit", help="Service or SDK to use"
)
parser.add_argument("--provider", type=str, default="ibmq", help="Provider to use")
parser.add_argument("--backend", type=str, default="fake_lima", help="Backend to use")
parser.add_argument(
    "--compiler_name", type=str, default="qiskit", help="Compiler name to use"
)
parser.add_argument(
    "--optimization_level",
    type=int,
    default=2,
    help="Optimization level for transpilation",
)
parser.add_argument(
    "--category", type=str, default="small", help="Category qasmbench to use"
)
parser.add_argument(
    "--qubits_range",
    nargs="+",
    default=(3, 5),
    type=tuple_of_ints,
    help="Qubits range",
)

# Parse the arguments
args = parser.parse_args()

SERVICE_OR_SDK = args.service_or_sdk
PROVIDER = args.provider
BACKEND = args.backend
COMPILER_NAME = args.compiler_name
OPTIMIZATION_LEVEL = args.optimization_level
CATEGORY = args.category
QUBITS_RANGE = args.qubits_range

# Actual path
_pwd = os.getcwd()
PATH = _pwd

# selected category for QASMBench
CATEGORY = f"programs/{CATEGORY}"

# select only the circuits with the number of qubits in the list
NUM_QUBITS_LIST = list(range(*QUBITS_RANGE))

# whether to remove the final measurement in the circuit
REMOVE_FINAL_MEASUREMENTS = False

# arguments for pyqcc
SERVICE_OR_SDK = "qiskit"
COMPILER_NAME = "qiskit"
OPTIMIZATION_LEVEL = 2
EXECUTION_TYPE = "off"
PLOT_OUTPUT = False
# max workers
MAX_WORKERS = 1

# setup
output_dir = f"{PATH}/compiled/{PROVIDER}_{BACKEND}/{CATEGORY}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
original_dir = os.getcwd()
os.chdir(output_dir)

transpile_args = {
    "service_or_sdk": SERVICE_OR_SDK,
    "provider_name": PROVIDER,
    "backend_name": BACKEND,
    "compiler_name": COMPILER_NAME,
    "optimization_level": OPTIMIZATION_LEVEL,
    "execution_type": EXECUTION_TYPE,
    "plot_output": PLOT_OUTPUT,
    "no_pyqcc_env": False,
    "container": False,
}

bm = QASMBenchmark(
    PATH,
    CATEGORY,
    num_qubits_list=NUM_QUBITS_LIST,
    remove_final_measurements=REMOVE_FINAL_MEASUREMENTS,
    do_transpile=True,
    **transpile_args,
)

for _circuit_name in bm.circ_name_list:
    _circuit = bm.get(_circuit_name)

os.chdir(original_dir)

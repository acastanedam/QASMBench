#!/usr/bin/env bash

# TODO: add alicebob
service_or_sdk=("qiskit" "qiskit" "qiskit" "qiskit")
providers=("aqt" "ibmq" "ionq" "iqm")
backends=("offline_simulator_noise" "fake_kolkata" "ionq_qpu" "fake_apollo")
compilers=("qiskit" "pytket")
optimization_levels=(1 2 3)
categories=("small")
qubits_range="3,6"

base_command="python interface/run_qasmbench.py"

output_dir="./logs"
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
fi

for ((i=0; i<${#service_or_sdk[@]}; i++)); do
    sod="${service_or_sdk[i]}"
    prov="${providers[i]}"
    bck="${backends[i]}"
    command="$base_command --service_or_sdk $sod --provider $prov --backend $bck"
    for cnm in "${compilers[@]}"; do
        for optl in "${optimization_levels[@]}"; do
            for cat in "${categories[@]}"; do
                command="$command --compiler_name $cnm --optimization_level $optl --category $cat"
                log_file="$output_dir/$sod-$prov-$bck-$cnm-$optl-$cat.log"
                err_file="$output_dir/$sod-$prov-$bck-$cnm-$optl-$cat.err"
                echo "Running: $command" 

                ( $command 2>&1 1>/dev/tty | tee -a $err_file ) | tee -a "$log_file"
            done
        done
    done
done




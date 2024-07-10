import subprocess
import os
import argparse

results_dir = '/home/albus/gem5-results'

parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
parser.add_argument('benchmarks', nargs='*', help='List of benchmarks to simulate')
args = parser.parse_args()

if args.benchmarks:
    benchmarks = args.benchmarks
else:
    with open('/home/albus/gem5/scripts/all_compiled_spec2017.txt', 'r') as f:
        benchmarks = [line.strip() for line in f]

for benchmark in benchmarks:
    dir = os.path.join(results_dir, 'spec2017_simpoint_simpoints', benchmark)
    i_file = os.path.join(results_dir, 'spec2017_simpoint_profile', benchmark, 'simpoint.bb.gz')
    simpoint_dir = os.path.join(dir, 'simpoints')
    weight_dir = os.path.join(dir, 'weights')
    
    if not os.path.isdir(dir):
        os.makedirs(dir)
   
    command = [
        '/home/albus/SimPoint.3.2/bin/simpoint',
        '-loadFVFile', i_file,
        '-maxK', '30',
        '-saveSimpoints', simpoint_dir,
        '-saveSimpointWeights', weight_dir,
        '-inputVectorsGzipped'
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Command for benchmark '{benchmark}' executed successfully.")
        print("Output:", result.stdout.decode())
    except subprocess.CalledProcessError as e:
        print(f"Error executing command for benchmark '{benchmark}': {e.stderr.decode()}")

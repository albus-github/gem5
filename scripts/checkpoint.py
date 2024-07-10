#!/usr/bin/env python3

import os
import re
import sys
import random
import sh
import time
from os.path import join as pjoin
from os.path import expanduser as uexp
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool
import common as c


# Please set to the directory where gem5-generated bbvs stored and
# ensure that you have performed simpoint clustering on them
simpoint_profile_dir = '/home/albus/gem5-results/spec2017_simpoint_profile/'
assert simpoint_profile_dir != 'deadbeaf'

# Please set to the directory where to store gem5-generated checkpoints
outdir = '/home/albus/gem5-results/spec2017_simpoint_cpts/'
assert outdir != 'deadbeaf'


def take_cpt_for_benchmark(benchmark, simpoint_file, weight_file, outdir_b):

    gem5_dir = '/home/albus/gem5'

    interval = 10000000
    warmup = 2000000

    exec_dir = c.run_dir(benchmark)
    os.chdir(exec_dir)

    options = [
            '--outdir=' + outdir_b,
            pjoin(gem5_dir, 'configs/spec_2017/se_spec2017.py'),
            '-b',
            '{}'.format(benchmark),
            '--maxinsts=100000000',
            '--benchmark_stdout={}/out'.format(outdir_b),
            '--benchmark_stderr={}/err'.format(outdir_b),
            '--cpu-type=AtomicSimpleCPU',
            '--mem-type=DRAMsim3',
            '--mem-size=8GB',
            '--take-simpoint-checkpoint={},{},{},{}'.format(
                simpoint_file, weight_file, interval, warmup)
            ]
    print(options)
    gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
    # sys.exit(0)
    gem5(
            _out=pjoin(outdir_b, 'gem5_out.txt'),
            _err=pjoin(outdir_b, 'gem5_err.txt'),
            *options
            )


def run(benchmark):
    outdir_b = pjoin(outdir, benchmark)
    if not os.path.isdir(outdir_b):
        os.makedirs(outdir_b)

    simpoint_dir_b = pjoin('/home/albus/gem5-results/spec2017_simpoint_simpoints/', benchmark)

    simpoint_file = pjoin(simpoint_dir_b, 'simpoints')
    weight_file = pjoin(simpoint_dir_b, 'weights')

    profiled = os.path.isfile(simpoint_file) and os.path.isfile(weight_file)

    if profiled:
        print('simpoint weight file found in {},'.format(simpoint_dir_b),
                'is going take simpoint cpt')
        c.avoid_repeated(take_cpt_for_benchmark, outdir_b, None,
                benchmark, simpoint_file, weight_file, outdir_b)
    else:
        print('simpoint weight file not found in {}, abort'.format(
            simpoint_dir_b))


def main():
    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmarks', nargs='*', help='List of benchmarks to simulate')
    args = parser.parse_args()

    if args.benchmarks:
        benchmarks = args.benchmarks
    else:
        benchmarks_file = './all_compiled_spec2017.txt'
        with open(benchmarks_file) as f:
            benchmarks = [line.strip() for line in f]

    # num_thread = 22
    # if num_thread > 1:
    #     p = Pool(num_thread)
    #     p.map(run, benchmarks)
    # else:
    #     run(benchmarks[0])

    if benchmarks:
        with ThreadPoolExecutor(max_workers=min(8, len(benchmarks))) as executor:
            futures = []
            for benchmark in benchmarks:
                futures.append(executor.submit(run, (benchmark)))
            
            for future in as_completed(futures):
                future.result()  # Check for exceptions and wait for thread completion


if __name__ == '__main__':
    main()

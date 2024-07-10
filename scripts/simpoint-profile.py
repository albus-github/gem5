#!/usr/bin/env python3

import os
import sys
import sh
import argparse
from os.path import join as pjoin
from multiprocessing import Pool
import common as c
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Directory to store gem5-generated bbvs
simpoint_profile_dir = '/home/albus/gem5-results/spec2017_simpoint_profile'
assert simpoint_profile_dir != 'deadbeaf'

def simpoint_profile(benchmark, cmd_timestamp=None):
    gem5_dir = '/home/albus/gem5'
    outdir = pjoin(simpoint_profile_dir, benchmark)

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    if cmd_timestamp:
        output_timestamp_file = pjoin(outdir, 'done')
        if os.path.isfile(output_timestamp_file):
            file_m_time = os.path.getmtime(output_timestamp_file)
            if file_m_time > cmd_timestamp:
                logging.info(f'Command is older than output of {benchmark}, skip!')
                return

    exec_dir = c.run_dir(benchmark)
    try:
        os.chdir(exec_dir)
    except OSError as e:
        logging.error(f'Failed to change directory: {e}')
        return

    options = [
        '--outdir=' + outdir,
        pjoin(gem5_dir, 'configs/spec_2017/se_spec2017.py'),
        '-b', benchmark,
        '--maxinsts=100000000',
        '--benchmark_stdout={}/out'.format(outdir),
        '--benchmark_stderr={}/err'.format(outdir),
        '--cpu-type=NonCachingSimpleCPU',
        '--mem-size=8GB',
        '--simpoint-profile',
        '--simpoint-interval={}'.format(10000000),
    ]
    logging.info(f'Running gem5 with options: {options}')
    gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
    try:
        gem5(_out=pjoin(outdir, 'gem5_out.txt'), _err=pjoin(outdir, 'gem5_err.txt'), *options)
    except sh.ErrorReturnCode as e:
        logging.error(f'gem5 failed: {e}')
        return

    sh.touch(pjoin(outdir, 'done'))

def run(benchmark, cmd_timestamp=None):
    outdir_b = pjoin(simpoint_profile_dir, benchmark)
    if not os.path.isdir(outdir_b):
        os.makedirs(outdir_b)

    c.avoid_repeated(simpoint_profile, outdir_b, pjoin('/home/albus/gem5/build/X86/gem5.fast'), benchmark, cmd_timestamp)

def main():
    benchmarks = []
    cmd_timestamp = None

    cmd_timestamp_file = './ts-simprofile'
    if os.path.isfile(cmd_timestamp_file):
        cmd_timestamp = os.path.getmtime(cmd_timestamp_file)
        logging.info(f'Command timestamp: {cmd_timestamp}')

    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmarks', nargs='*', help='List of benchmarks to simulate or "uncompiled" to read from uncompiled.txt')
    args = parser.parse_args()

    if args.benchmarks:
        if args.benchmarks == ['uncompiled']:
            with open('/home/albus/gem5/scripts/uncompiled.txt') as f:
                benchmarks = [line.strip() for line in f]
        else:
            benchmarks = args.benchmarks
    else:
        with open('/home/albus/gem5/scripts/all_compiled_spec2017.txt') as f:
            benchmarks = [line.strip() for line in f]

    num_threads = min(len(benchmarks), os.cpu_count())
    logging.info(f'Starting simulation with {num_threads} threads.')
    
    if benchmarks:
        with Pool(num_threads) as pool:
            pool.starmap(run, [(benchmark, cmd_timestamp) for benchmark in benchmarks])
    else:
        logging.warning('No benchmarks to run.')

if __name__ == '__main__':
    main()

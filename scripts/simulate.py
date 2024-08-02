#!/usr/bin/env python3

import os
import sh
import argparse
from os.path import join as pjoin
from os.path import expanduser as uexp
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as c
from functools import partial

default_outdir  = '/home/albus/gem5-results/spec2017_results'
gem5_dir        = '/home/albus/gem5'

def sim(benchmark, some_extra_args, outdir_b):

    options = [
            '--outdir=' + outdir_b,
            pjoin(gem5_dir, 'configs/spec_2017/se_spec2017.py'),
            '-b',
            '{}'.format(benchmark),
            '--benchmark_stdout={}/out'.format(outdir_b),
            '--benchmark_stderr={}/err'.format(outdir_b),
            '--maxinsts=100000000',
            '--mem-size=8GB'
            ]
    cpu_model = 'OoO'
    if cpu_model == 'TimingSimple':
        options += [
                '--cpu-type=TimingSimpleCPU',
                '--mem-type=SimpleMemory',
                ]
    elif cpu_model == 'OoO':
        options += [
            '--cpu-type=X86O3CPU',
            '--cpu-clock=3GHz',
            '--mem-type=DRAMsim3',

            '--caches',
            '--cacheline_size=64',

            '--l1i_size=32kB',
            '--l1d_size=32kB',
            '--l1i_assoc=4',
            '--l1d_assoc=4',

            '--l2cache',
            '--l2_size=256kB',
            '--l2_assoc=8',

            '--l3cache',
            '--l3_size=16MB',
            ]
    else:
        assert False      

    hwp = False
    if hwp:
        options += [
            '--l2-hwp-type=StridePrefetcher'
        ]

    try:
        gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
        gem5(
            _out=pjoin(outdir_b, 'gem5_out.txt'),
            _err=pjoin(outdir_b, 'gem5_err.txt'),
            *options
        )
    except sh.ErrorReturnCode as e:
        print(f"Error executing gem5: {e}")

def run(args):
    benchmark, outdir_b = args
    exec_dir = c.run_dir(benchmark)
    os.chdir(exec_dir)

    prerequisite = True
    some_extra_args = None

    if prerequisite:
        print('prerequisite satisfied, is going to run gem5 on', benchmark)
        c.avoid_repeated(sim, outdir_b, None,
                benchmark, some_extra_args, outdir_b)
        print(f'Benchmark {benchmark} complete simulation')
    else:
        print('prerequisite not satisfied, abort on', benchmark)

def main():
    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmarks', nargs='*', help='List of benchmarks to simulate')
    parser.add_argument('--outdir', type=str, help='Output directory')
    args = parser.parse_args()

    outdir = args.outdir if args.outdir else default_outdir

    if args.benchmarks:
        benchmarks = args.benchmarks
    else:
        with open("/home/albus/gem5/scripts/all_compiled_spec2017.txt", 'r') as f:
            benchmarks = [line.strip() for line in f]

    if benchmarks:
        with ThreadPoolExecutor(max_workers=min(8, len(benchmarks))) as executor:
            futures = []
            for benchmark in benchmarks:
                outdir_b = pjoin(outdir, benchmark)
                if not os.path.isdir(outdir_b):
                    os.makedirs(outdir_b)
                futures.append(executor.submit(run, (benchmark, outdir_b)))
            
            for future in as_completed(futures):
                future.result()  # Check for exceptions and wait for thread completion

if __name__ == '__main__':
    main()

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
from multiprocessing import Pool
import common as c


outdir = '/home/albus/gem5-results/spec2017_simpoint_restore'
gem5_dir = '/home/albus/gem5'

def count_ctps(benchmark):
    dir = '/home/albus/gem5-results/spec2017_simpoint_simpoints/'+benchmark+'/weights'
    try:
        with open(dir, 'r') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        print(f"The file {dir} does not exist.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

def example_to_restore_cpt(benchmark, some_extra_args, outdir_b):

    interval = 10000000
    warmup = 20*10**6

    r = count_ctps(benchmark)

    exec_dir = c.run_dir(benchmark)
    os.chdir(exec_dir)

    for i in range(1, r):
        cpt_dir = f"{benchmark}_cpt{i}"
        restore_dir = pjoin(outdir_b, cpt_dir)
        if not os.path.isdir(restore_dir):
            os.makedirs(restore_dir)

        options = [
                '--outdir=' + restore_dir,
                pjoin(gem5_dir, 'configs/spec_2017/se_spec2017.py'),
                '-b',
                '{}'.format(benchmark),
                '--benchmark_stdout={}/out'.format(restore_dir),
                '--benchmark_stderr={}/err'.format(restore_dir),
                '--maxinsts=10000000000',
                '--mem-size=8GB',
                '--restore-simpoint-checkpoint',
                '-r {}'.format(i),
                '--checkpoint-dir=/home/albus/gem5-results/spec2017_simpoint_cpts/{}'.format(benchmark),
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
        print(options)
        gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
        # sys.exit(0)
        gem5(
                _out=pjoin(restore_dir, 'gem5_out.txt'),
                _err=pjoin(restore_dir, 'gem5_err.txt'),
                *options
                )


def run(benchmark):
    outdir_b = pjoin(outdir, benchmark)
    if not os.path.isdir(outdir_b):
        os.makedirs(outdir_b)

    prerequisite = True
    some_extra_args = None

    if prerequisite:
        print('prerequisite satisified, is going to run gem5 on', benchmark)
        c.avoid_repeated(example_to_restore_cpt, outdir_b, None,
                benchmark, some_extra_args, outdir_b)
    else:
        print('prerequisite not satisified, abort on', benchmark)


def main():
    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmarks', nargs='*', help='List of benchmarks to simulate')
    args = parser.parse_args()

    if args.benchmarks:
        benchmarks = args.benchmarks
    else:
        benchmarks_file = './integer.txt'
        with open(benchmarks_file) as f:
            benchmarks = [line.strip() for line in f]

    num_thread = len(benchmarks)
    if num_thread > 1:
        p = Pool(num_thread)
        p.map(run, benchmarks)
    else:
        run(benchmarks[0])


if __name__ == '__main__':
    main()
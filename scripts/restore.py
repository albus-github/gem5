#!/usr/bin/env python3

import os
import sh
import argparse
from os.path import join as pjoin
from os.path import expanduser as uexp
from multiprocessing import Pool
import common as c
from functools import partial

outdir = '/home/albus/gem5-results/spec2017_simpoint_restore'
gem5_dir = '/home/albus/gem5'

def count_ctps(benchmark):
    weight_file_path = os.path.join('/home/albus/gem5-results/spec2017_simpoint_simpoints', benchmark, 'weights')
    try:
        with open(weight_file_path, 'r') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        print(f"The file {weight_file_path} does not exist.")
        return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

def restore_cpt(benchmark, some_extra_args, restore_dir, i):

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
            '-r {}'.format(i+1),
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

    try:
        gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
        gem5(
            _out=pjoin(restore_dir, 'gem5_out.txt'),
            _err=pjoin(restore_dir, 'gem5_err.txt'),
            *options
        )
    except sh.ErrorReturnCode as e:
        print(f"Error executing gem5: {e}")

def run(args):
    benchmark, i, outdir_b = args
    exec_dir = c.run_dir(benchmark)
    os.chdir(exec_dir)

    cpt_dir = f"{benchmark}_cpt{i}"
    restore_dir = pjoin(outdir_b, cpt_dir)
    if not os.path.isdir(restore_dir):
        os.makedirs(restore_dir)

    prerequisite = True
    some_extra_args = None

    if prerequisite:
        print('prerequisite satisified, is going to run gem5 on', benchmark)
        c.avoid_repeated(restore_cpt, restore_dir, None,
                benchmark, some_extra_args, restore_dir, i)
    else:
        print('prerequisite not satisified, abort on', benchmark)

def main():
    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmark', nargs='+', help='List of benchmarks to simulate')
    args = parser.parse_args()

    for benchmark in args.benchmark:
        outdir_b = pjoin(outdir, benchmark)
        if not os.path.isdir(outdir_b):
            os.makedirs(outdir_b)

        num_thread = count_ctps(benchmark)
        if num_thread > 1:
            with Pool(num_thread) as pool:
                pool.map(run, [(benchmark, i, outdir_b) for i in range(num_thread)])
        else:
            run((benchmark, 0, outdir_b))

if __name__ == '__main__':
    main()

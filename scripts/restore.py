#!/usr/bin/env python3

import os
import sh
import argparse
from os.path import join as pjoin
from os.path import expanduser as uexp
from concurrent.futures import ThreadPoolExecutor, as_completed
import common as c
from functools import partial

default_outdir  = '/home/albus/gem5-results/spec2017_simpoint_restore'
gem5_dir        = '/home/albus/gem5'

def cases(benchmark, r):
    if benchmark=="namd_r" and r==3: return True
    if benchmark=="imagick_r" and r==3: return True
    return False

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
        print('prerequisite satisfied, is going to run gem5 on', benchmark)
        c.avoid_repeated(restore_cpt, restore_dir, None,
                benchmark, some_extra_args, restore_dir, i)
    else:
        print('prerequisite not satisfied, abort on', benchmark)

def main():
    parser = argparse.ArgumentParser(description='Simulate SPEC 2017 benchmarks and generate checkpoints.')
    parser.add_argument('benchmark', nargs='+', help='List of benchmarks to simulate')
    parser.add_argument('-r', type=int, help='Specific checkpoint index to restore')
    parser.add_argument('--outdir', type=str, help='Output directory')
    args = parser.parse_args()

    outdir = args.outdir if args.outdir else default_outdir

    for benchmark in args.benchmark:
        outdir_b = pjoin(outdir, benchmark)
        if not os.path.isdir(outdir_b):
            os.makedirs(outdir_b)

        if args.r is not None:
            if cases(benchmark, args.r):
                continue
            run((benchmark, args.r - 1, outdir_b))
        else:
            num_thread = count_ctps(benchmark)
            if num_thread > 0:
                with ThreadPoolExecutor(max_workers=8) as executor:
                    futures = [
                        executor.submit(run, (benchmark, i, outdir_b))
                        for i in range(num_thread)
                        if not cases(benchmark, i + 1)
                    ]
                    for future in as_completed(futures):
                        future.result()  # Check for exceptions and wait for thread completion

if __name__ == '__main__':
    main()

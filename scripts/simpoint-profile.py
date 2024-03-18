#!/usr/bin/env python3

import os
import re
import sys
import random
import sh
import time
from os.path import join as pjoin
from os.path import expanduser as uexp
from multiprocessing import Pool
import common as c

cmd_timestamp = None

# Please set to the directory where to store gem5-generated bbvs
simpoint_profile_dir = '/home/albus/gem5-results/spec2017_simpoint_profile'
assert simpoint_profile_dir != 'deadbeaf'

def simpoint_profile(benchmark, dont_care, outdir_b):
    global cmd_timestamp

    gem5_dir = '/home/albus/gem5'
    outdir = pjoin(simpoint_profile_dir, benchmark)

    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    if cmd_timestamp:
        output_timestamp_file = pjoin(outdir, 'done')
        if os.path.isfile(output_timestamp_file):
            file_m_time = os.path.getmtime(output_timestamp_file)
            if file_m_time > cmd_timestamp:
                print('Command is older than output of {}, skip!'.format(
                    benchmark))
                return

    exec_dir = c.run_dir(benchmark)
    os.chdir(exec_dir)

    options = [
            '--outdir=' + outdir,
            pjoin(gem5_dir, 'configs/spec_2017/se_spec2017.py'),
            '-b',
            '{}'.format(benchmark),
            '--benchmark_stdout={}/out'.format(outdir),
            '--benchmark_stderr={}/err'.format(outdir),
            '--cpu-type=NonCachingSimpleCPU',
            '--mem-size=16GB'
            '--simpoint-profile',
            '--simpoint-interval={}'.format(100000000),
            '-I {}'.format(1200*10**9),
            ]
    print(options)
    gem5 = sh.Command('/home/albus/gem5/build/X86/gem5.fast')
    # sys.exit(0)
    gem5(
            _out=pjoin(outdir, 'gem5_out.txt'),
            _err=pjoin(outdir, 'gem5_err.txt'),
            *options
            )

    sh.touch(pjoin(outdir, 'done'))

def run(benchmark):
    outdir_b = pjoin(simpoint_profile_dir, benchmark)
    if not os.path.isdir(outdir_b):
        os.makedirs(outdir_b)

    c.avoid_repeated(simpoint_profile, outdir_b, pjoin('/home/albus/gem5/build/X86/gem5.fast'),
            benchmark, None, outdir_b)

def main():
    num_thread = 50

    benchmarks = []

    cmd_timestamp_file = './ts-simprofile'
    global cmd_timestamp
    if os.path.isfile(cmd_timestamp_file):
        cmd_timestamp = os.path.getmtime(cmd_timestamp_file)
        print(cmd_timestamp)


    with open('/home/albus/gem5/scripts/all_compiled_spec2017.txt') as f:
        for line in f:
            benchmarks.append(line.strip())
    # print benchmarks

    if num_thread > 1:
        p = Pool(num_thread)
        p.map(run, benchmarks)
    else:
        run(benchmarks[0])


if __name__ == '__main__':
    main()

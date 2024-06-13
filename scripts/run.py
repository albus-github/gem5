import subprocess
import argparse
import os

default_stats_dir   = '/home/albus/gem5-results/spec2017_simpoint_restore'
script_dir          = '/home/albus/gem5/scripts/'
task_dir            = '/home/albus/gem5/scripts/' 
int_task            = task_dir + 'integer.txt'
float_task          = task_dir + 'floating.txt'
fail_task           = task_dir + 'fail.txt'
all_task            = task_dir + 'all_compiled_spec2017.txt'

def run_scripts(benchmark, stats_dir):
    scripts_with_args = [
        (f'{script_dir}restore.py',  [benchmark]),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'system.switch_cpus.cpi']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'system.switch_cpus.ipc']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_reads_done', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_read_row_hits', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_read_cmds', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'average_read_latency', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'average_bandwidth', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'Prefetch_count', '--prefetch']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'Prefetch_hit', '--prefetch']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'Prefetch_accuracy', '--prefetch'])
    ]

    for script, args in scripts_with_args:
        try:
            # 使用subprocess.run来执行脚本，并传递参数
            result = subprocess.run(['python3', script] + args, check=True)
            print(f"{script} executed successfully with return code {result.returncode}")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while executing {script}: {e}")
            break  # 如果脚本执行出错，停止后续脚本的执行

def main():
    parser = argparse.ArgumentParser(description='Run benchmark scripts')
    parser.add_argument('benchmark', type=str, nargs='?', default=None, help='benchmark to run')
    parser.add_argument('--stats_dir', type=str, help='stats 文件目录')

    args = parser.parse_args()

    if args.stats_dir:
        stats_dir = '--stats_dir=' + args.stats_dir
    else:
        stats_dir = '--stats_dir=' + default_stats_dir

    if args.benchmark:
        if args.benchmark == 'integer':
            if os.path.exists(int_task):
                with open(int_task, 'r') as file:
                    benchmarks = file.readlines()
                for benchmark in benchmarks:
                    benchmark = benchmark.strip()
                    if benchmark:  # 跳过空行
                        run_scripts(benchmark, stats_dir)
        elif args.benchmark == 'floating':
            if os.path.exists(float_task):
                with open(float_task, 'r') as file:
                    benchmarks = file.readlines()
                for benchmark in benchmarks:
                    benchmark = benchmark.strip()
                    if benchmark:  # 跳过空行
                        run_scripts(benchmark, stats_dir)
        elif args.benchmark == 'fail':
            if os.path.exists(fail_task):
                with open(fail_task, 'r') as file:
                    benchmarks = file.readlines()
                for benchmark in benchmarks:
                    benchmark = benchmark.strip()
                    if benchmark:  # 跳过空行
                        run_scripts(benchmark, stats_dir)
        else:
            run_scripts(args.benchmark, stats_dir)
    else:
        if os.path.exists(all_task):
            with open(all_task, 'r') as file:
                benchmarks = file.readlines()
            for benchmark in benchmarks:
                benchmark = benchmark.strip()
                if benchmark:  # 跳过空行
                    run_scripts(benchmark, stats_dir)
        else:
            print("task.txt file not found and no benchmark provided as an argument.")

if __name__ == "__main__":
    main()

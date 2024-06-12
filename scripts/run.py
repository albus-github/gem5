import subprocess
import argparse
import os

stats_dir   = '/home/albus/gem5-results/spec2017_simpoint_restore'
script_dir  = '/home/albus/gem5/scripts/'
task_dir    = '/home/albus/gem5/scripts/' 
int_task    = task_dir + 'integer.txt'
float_task  = task_dir + 'floating.txt'
all_task    = task_dir + 'run.txt'

def run_scripts(benchmark):
    scripts_with_args = [
        (f'{script_dir}restore.py',  [benchmark]),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'system.switch_cpus.cpi']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'system.switch_cpus.ipc']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_reads_done', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_read_row_hits', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'num_read_cmds', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'average_read_latency', '--dram']),
        (f'{script_dir}weight.py',   [benchmark, stats_dir, 'average_bandwidth', '--dram'])
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

    args = parser.parse_args()

    if args.benchmark:
        if args.benchmark == 'integer':
            if os.path.exists(int_task):
                with open(int_task, 'r') as file:
                    benchmarks = file.readlines()
                for benchmark in benchmarks:
                    benchmark = benchmark.strip()
                    if benchmark:  # 跳过空行
                        run_scripts(benchmark)
        elif args.benchmark == 'floating':
            if os.path.exists(float_task):
                with open(float_task, 'r') as file:
                    benchmarks = file.readlines()
                for benchmark in benchmarks:
                    benchmark = benchmark.strip()
                    if benchmark:  # 跳过空行
                        run_scripts(benchmark)
        else:
            run_scripts(args.benchmark)
    else:
        if os.path.exists(all_task):
            with open(all_task, 'r') as file:
                benchmarks = file.readlines()
            for benchmark in benchmarks:
                benchmark = benchmark.strip()
                if benchmark:  # 跳过空行
                    run_scripts(benchmark)
        else:
            print("task.txt file not found and no benchmark provided as an argument.")

if __name__ == "__main__":
    main()

import subprocess
import argparse
import os

default_stats_dir   = '/home/albus/gem5-results/spec2017_simpoint_restore'
script_dir          = '/home/albus/gem5/scripts/'
task_dir            = '/home/albus/gem5/scripts/' 
int_task            = task_dir + 'integer.txt'
float_task          = task_dir + 'floating.txt'
test_task           = task_dir + 'test.txt'
all_task            = task_dir + 'all_compiled_spec2017.txt'

def run_scripts(benchmark, stats_dir):
    scripts_with_args = [
        (f'{script_dir}restore.py', [benchmark]),
        (f'{script_dir}analyse.py', [benchmark])
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

    run_scripts(args.benchmark, stats_dir)
    # if args.benchmark:
    #     if args.benchmark == 'integer':
    #         if os.path.exists(int_task):
    #             with open(int_task, 'r') as file:
    #                 benchmarks = file.readlines()
    #             for benchmark in benchmarks:
    #                 benchmark = benchmark.strip()
    #                 if benchmark:  # 跳过空行
    #                     run_scripts(benchmark, stats_dir)
    #     elif args.benchmark == 'floating':
    #         if os.path.exists(float_task):
    #             with open(float_task, 'r') as file:
    #                 benchmarks = file.readlines()
    #             for benchmark in benchmarks:
    #                 benchmark = benchmark.strip()
    #                 if benchmark:  # 跳过空行
    #                     run_scripts(benchmark, stats_dir)
    #     elif args.benchmark == 'test':
    #         if os.path.exists(test_task):
    #             with open(test_task, 'r') as file:
    #                 benchmarks = file.readlines()
    #             for benchmark in benchmarks:
    #                 benchmark = benchmark.strip()
    #                 if benchmark:  # 跳过空行
    #                     run_scripts(benchmark, stats_dir)
    #     else:
    #         run_scripts(args.benchmark, stats_dir)
    # else:
    #     if os.path.exists(all_task):
    #         with open(all_task, 'r') as file:
    #             benchmarks = file.readlines()
    #         for benchmark in benchmarks:
    #             benchmark = benchmark.strip()
    #             if benchmark:  # 跳过空行
    #                 run_scripts(benchmark, stats_dir)
    #     else:
    #         print("task.txt file not found and no benchmark provided as an argument.")

if __name__ == "__main__":
    main()

# import subprocess
# import argparse
# import os
# from concurrent.futures import ThreadPoolExecutor, as_completed

# default_stats_dir = '/home/albus/gem5-results/spec2017_simpoint_restore'
# script_dir = '/home/albus/gem5/scripts/'
# task_dir = '/home/albus/gem5/scripts/'
# int_task = task_dir + 'integer.txt'
# float_task = task_dir + 'floating.txt'
# test_task = task_dir + 'test.txt'
# all_task = task_dir + 'all_compiled_spec2017.txt'

# def run_restore(benchmark, stats_dir):
#     try:
#         result = subprocess.run(['python3', f'{script_dir}restore.py', benchmark, '--outdir', stats_dir], check=True)
#         print(f"restore.py for {benchmark} executed successfully with return code {result.returncode}")
#     except subprocess.CalledProcessError as e:
#         print(f"Error occurred while executing restore.py for {benchmark}: {e}")
#         return False
#     return True

# def run_analyse(benchmark, stats_dir):
#     try:
#         result = subprocess.run(['python3', f'{script_dir}analyse.py', benchmark, '--outdir', stats_dir], check=True)
#         print(f"analyse.py for {benchmark} executed successfully with return code {result.returncode}")
#     except subprocess.CalledProcessError as e:
#         print(f"Error occurred while executing analyse.py for {benchmark}: {e}")

# def process_benchmark(benchmark, stats_dir):
#     if run_restore(benchmark, stats_dir):
#         run_analyse(benchmark, stats_dir)

# def main():
#     parser = argparse.ArgumentParser(description='Run benchmark scripts')
#     parser.add_argument('benchmark', type=str, nargs='?', default=None, help='benchmark to run')
#     parser.add_argument('--stats_dir', type=str, help='stats 文件目录')

#     args = parser.parse_args()

#     if args.stats_dir:
#         stats_dir = args.stats_dir
#     else:
#         stats_dir = default_stats_dir

#     benchmarks = []

#     if args.benchmark:
#         if args.benchmark == 'integer' and os.path.exists(int_task):
#             with open(int_task, 'r') as file:
#                 benchmarks = file.readlines()
#         elif args.benchmark == 'floating' and os.path.exists(float_task):
#             with open(float_task, 'r') as file:
#                 benchmarks = file.readlines()
#         elif args.benchmark == 'test' and os.path.exists(test_task):
#             with open(test_task, 'r') as file:
#                 benchmarks = file.readlines()
#         else:
#             benchmarks = [args.benchmark]
#     else:
#         if os.path.exists(all_task):
#             with open(all_task, 'r') as file:
#                 benchmarks = file.readlines()
#         else:
#             print("task.txt file not found and no benchmark provided as an argument.")
#             return

#     benchmarks = [benchmark.strip() for benchmark in benchmarks if benchmark.strip()]

#     with ThreadPoolExecutor(max_workers=2) as executor:
#         futures = {}
#         for benchmark in benchmarks:
#             future = executor.submit(process_benchmark, benchmark, stats_dir)
#             futures[future] = benchmark

#         for future in as_completed(futures):
#             benchmark = futures[future]
#             try:
#                 future.result()  # Check for exceptions
#             except Exception as e:
#                 print(f"Error occurred while processing {benchmark}: {e}")

# if __name__ == "__main__":
#     main()
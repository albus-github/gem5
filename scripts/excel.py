import os
import pandas as pd
import argparse

default_base_dir = '/home/albus/gem5-results'

def read_results_file(file_path):
    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Skip empty lines
                parts = line.split()
                if len(parts) == 2:
                    key, value = parts
                    try:
                        data[key] = float(value)
                    except ValueError:
                        # 如果不能将值转换为浮点数，则跳过该行
                        continue
    return data

def collect_data(base_dir, benchmark_name):
    all_data = []

    def recursive_search(current_dir, config_name):
        for entry in os.listdir(current_dir):
            entry_path = os.path.join(current_dir, entry)
            if os.path.isdir(entry_path):
                if entry == benchmark_name:
                    result_file_path = os.path.join(entry_path, 'results.txt')
                    if os.path.isfile(result_file_path):
                        data['Task'] = benchmark_name
                        data['Config'] = config_name
                        data = read_results_file(result_file_path)
                        all_data.append(data)
                else:
                    recursive_search(entry_path, config_name)

    for root_dir in os.listdir(base_dir):
        root_dir_path = os.path.join(base_dir, root_dir)
        if os.path.isdir(root_dir_path):
            recursive_search(root_dir_path, root_dir)

    return all_data

def main():
    parser = argparse.ArgumentParser(description='Generate benchmark data summary')
    parser.add_argument('--base_dir', type=str, help='Base directory containing the results')
    parser.add_argument('benchmark', type=str, help='Name of the benchmark to summarize')
    args = parser.parse_args()
    
    if args.base_dir:
        base_dir = args.base_dir
    else:
        base_dir = default_base_dir

    data = collect_data(base_dir, args.benchmark)
    
    if not data:
        print(f"No data found for benchmark: {args.benchmark}")
        return
    
    df = pd.DataFrame(data)
    
    # 将 DataFrame 写入 Excel 文件
    output_file = f'{base_dir}/{args.benchmark}_summary.xlsx'
    df.to_excel(output_file, index=False)
    print(f"Data has been written to {output_file}")

if __name__ == "__main__":
    main()

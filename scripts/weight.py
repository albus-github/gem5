import os
import argparse

simpoints_dir = "/home/albus/gem5-results/spec2017_simpoint_simpoints"

def read_simpoints(filename):
    simpoints = []
    with open(filename, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) != 2:
                print(f"Skipping invalid line in simpoints file: {line.strip()}")
                continue
            try:
                size, idx = map(int, parts)
                simpoints.append((size, idx))
            except ValueError as e:
                print(f"Error parsing line in simpoints file: {line.strip()} - {e}")
                continue  # 添加跳过错误行的处理
    simpoints = sorted(simpoints, key=lambda x: x[0])
    return simpoints


def read_weights(filename):
    weights = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split()
            if len(parts) != 2:
                print(f"Skipping invalid line in weights file: {line.strip()}")
                continue
            try:
                weight, idx = parts
                weights[int(idx)] = float(weight)
            except ValueError as e:
                print(f"Error parsing line in weights file: {line.strip()} - {e}")
    return weights

def read_stats(filename, keyword, is_dram):
    data = None
    matched_string = None
    try:
        with open(filename, 'r') as file:
            for line in file:
                if keyword in line:
                    if is_dram:
                        parts = line.strip().split('=')
                        if len(parts) >= 2:
                            value = parts[1].split('#')[0].strip()
                            data = float(value)
                            matched_string = parts[0].strip()
                    else:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            value = parts[1].split('#')[0].strip()
                            data = float(value)
                            matched_string = parts[0]
    except FileNotFoundError:
        print(f"stats file not found: {filename}")
    except ValueError as e:
        print(f"Error parsing line in stats file {filename}: {line.strip()} - {e}")
    return data, matched_string

def weighted_calculation(simpoints_file, weights_file, benchmark, stats_dir, key_word, dram):
    simpoints = read_simpoints(simpoints_file)
    weights = read_weights(weights_file)
    
    total_weighted_value = 0
    total_weight = 0
    matched_strings = []

    for i, (size, idx) in enumerate(simpoints):
        stats_filename = os.path.join(stats_dir, benchmark, f'{benchmark}_cpt{i}', 'dramsim3.txt' if dram else 'stats.txt') 
        target_value, matched_strings = read_stats(stats_filename, key_word, dram)

        weight = weights.get(idx, 0)
        total_weighted_value += target_value * weight
        total_weight += weight

    if total_weight == 0:
        return 0
    return total_weighted_value / total_weight, matched_strings

def main(benchmark, stats_dir, key_word, dram, outdir):
    simpoints = os.path.join(simpoints_dir, benchmark, 'simpoints')
    weights = os.path.join(simpoints_dir, benchmark, 'weights')
    result, matched_strings = weighted_calculation(simpoints, weights, benchmark, stats_dir, key_word, dram)
    
    if outdir:
        out_dir = os.path.join(outdir, 'results.txt') 
    else :
        out_dir = os.path.join(stats_dir, benchmark, 'results.txt')    
    with open(out_dir, 'a') as file:
        file.write(f'{matched_strings}        {result}\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='加权计算脚本')
    parser.add_argument('benchmark', type=str, help='benchmark result to caculate')
    parser.add_argument('stats_dir', type=str, help='stats 文件目录')
    parser.add_argument('key_word', type=str, help='key_work to caculate')
    parser.add_argument('--dram', action='store_true', help='analyse dramsim3.txt')
    parser.add_argument('--outdir', type=str, help='output directory')

    args = parser.parse_args()

    main(args.benchmark, args.stats_dir, args.key_word, args.dram, args.outdir)

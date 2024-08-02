import os
import argparse

simpoints_dir = "/home/albus/gem5-results/spec2017_simpoint_simpoints"
default_stats_dir = "/home/albus/gem5-results/spec2017_simpoint_restore"

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
                continue
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
                            if data == 0:
                                data = None
                            matched_string = parts[0].strip()
                    else:
                        parts = line.strip().split()
                        if parts[0] == keyword:
                            if len(parts) >= 2:
                                value = parts[1].split('#')[0].strip()
                                data = float(value)
                                matched_string = parts[0]
    except FileNotFoundError:
        print(f"Stats file not found: {filename}")
    except ValueError as e:
        print(f"Error parsing line in stats file {filename}: {line.strip()} - {e}")
    return data, matched_string

def weighted_calculation(simpoints_file, weights_file, benchmark, stats_dir, key_word, file):
    simpoints = read_simpoints(simpoints_file)
    weights = read_weights(weights_file)
    
    total_weighted_value = 0
    total_weight = 0
    matched_strings = set()

    for i, (size, idx) in enumerate(simpoints):
        stats_filename = os.path.join(stats_dir, benchmark, f'{benchmark}_cpt{i}', file)
        target_value, matched_string = read_stats(stats_filename, key_word, file=='dramsim3.txt')

        if target_value is not None:
            weight = weights.get(idx, 0)
            total_weighted_value += target_value * weight
            total_weight += weight
            if matched_string:
                matched_strings.add(matched_string)

    if total_weight == 0:
        return 0, matched_strings
    return total_weighted_value / total_weight, matched_strings

def main(benchmark, stats_dir, key_word, file, outdir):
    simpoints = os.path.join(simpoints_dir, benchmark, 'simpoints')
    weights = os.path.join(simpoints_dir, benchmark, 'weights')
    result, matched_strings = weighted_calculation(simpoints, weights, benchmark, stats_dir, key_word, file)
    
    if outdir:
        out_dir = os.path.join(outdir, 'results.txt')
    else:
        out_dir = os.path.join(stats_dir, benchmark, 'results.txt')
    
    with open(out_dir, 'a') as file:
        if len(matched_strings) == 1:
            matched_string_output = next(iter(matched_strings))  # Get the single element
        else:
            matched_string_output = ", ".join(matched_strings)
        if matched_string_output != '':
            file.write(f'{matched_string_output}        {result}\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Weighted calculation script')
    parser.add_argument('benchmark', type=str, help='Benchmark result to calculate')
    parser.add_argument('--stats_dir', type=str, help='Directory of stats files')
    parser.add_argument('key_word', type=str, help='Keyword to calculate')
    parser.add_argument('--dram', action='store_true', help='Analyze dramsim3.txt')
    parser.add_argument('--prefetch', action='store_true', help='Analyze prefetch_info')
    parser.add_argument('--outdir', type=str, help='Output directory')

    args = parser.parse_args()
    
    stats_dir = args.stats_dir if args.stats_dir else default_stats_dir

    if args.dram:
        file = 'dramsim3.txt'
    elif args.prefetch:
        file = 'prefetch_info'
    else:
        file = 'stats.txt'

    main(args.benchmark, stats_dir, args.key_word, file, args.outdir)

from collections import Counter

def process_trace_file(file_path):
    tag_positions = {}
    with open(file_path, 'r') as f:
        for line_number, line in enumerate(f, start=1):
            mask = 0xFFFF
            parts = line.split()
            addr = (int(parts[0], 16) >> 12) & mask
            if addr not in tag_positions:
                tag_positions[addr] = []
            tag_positions[addr].append(line_number)
    return tag_positions

def calculate_distances(tag_positions):
    tag_distances = {}
    for tag, positions in tag_positions.items():
        if len(positions) > 1:
            distances = [positions[i] - positions[i - 1] for i in range(1, len(positions))]
            distance_counter = Counter(distances)
            tag_distances[tag] = {
                'max_distance': max(distances),
                'min_distance': min(distances),
                'distance_counts': distance_counter
            }
    return tag_distances

def main():
    file_path = "./read_mix.trace"
    tag_positions = process_trace_file(file_path)
    tag_distances = calculate_distances(tag_positions)

    # 打印详细信息
    for tag, distances_info in tag_distances.items():
        print(f"Tag: {hex(tag)}")
        print(f"  Max Distance: {distances_info['max_distance']}")
        print(f"  Min Distance: {distances_info['min_distance']}")
        print("  Distance Counts:")
        for distance, count in distances_info['distance_counts'].items():
            print(f"    {distance}: {count}")

if __name__ == '__main__':
    main()

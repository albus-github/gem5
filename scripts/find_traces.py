import sys

def extract_lines_with_keyword(input_file_path, output_file_path, keyword):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            lines = input_file.readlines()

            matching_lines = [line.strip() for line in lines if keyword in line]

            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                output_file.write('\n'.join(matching_lines))

    except FileNotFoundError:
        print(f"Error: File '{input_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# 使用 sys.argv 获取命令行参数
if len(sys.argv) == 4: # 需要三个参数，第一个是脚本名
    input_file_path = sys.argv[1] # 第一个参数是输入文件路径
    output_file_path = sys.argv[2] # 第二个参数是输出文件路径
    keyword = sys.argv[3] # 第三个参数是关键词
    extract_lines_with_keyword(input_file_path, output_file_path, keyword)
else:
    print("Usage: python script.py input_file output_file keyword")

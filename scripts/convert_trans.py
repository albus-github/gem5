# 导入 sys 模块
import sys

# 定义一个函数，接受一行文本作为参数，返回转换后的结果
def convert(text):
  # 使用逗号分隔文本，得到三个部分
  parts = text.split(",")
  # 从第一个部分中提取Cycle的值，去掉空格和冒号
  cycle = parts[0].replace(" ", "").replace("Cycle:", "")
  # 从第二个部分中提取Addr的值，去掉空格和冒号
  addr = parts[1].replace(" ", "").replace("ADD_Trans:Addr:", "")
  # 从第三个部分中提取IsWrite的值，去掉空格和冒号
  is_write = parts[2].replace(" ", "").replace("IsWrite:", "").replace("\n","")
  # 将Addr的值从十进制转换为十六进制，并在前面加上0x
  hex_addr = "0x" + format(int(addr), "X")
  # 根据IsWrite的值，如果是0，则表示读取，如果是1，则表示写入
  if is_write == "0":
    rw = "READ"
  elif is_write == "1":
    rw = "WRITE"
  else:
    rw = "ERROR"
  # 将三个部分拼接起来，用空格分隔
  result = hex_addr + " " + rw + " " + cycle
  # 返回结果
  return result
  
  
# 获取命令行参数
input_file = sys.argv[1]
output_file = sys.argv[2]

# 打开输入文件和输出文件
with open(input_file, "r") as fin, open(output_file, "w") as fout:
  # 对每一行文本进行转换
  for line in fin:
    result = convert(line)
    # 将结果写入输出文件
    fout.write(result + "\n")
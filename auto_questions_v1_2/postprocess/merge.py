# encoding: utf8
# 用途：将一个文件夹下的所有json文件合并到一个json文件中

import json
from pathlib import Path

if __name__ == '__main__':
    # 输入json文件所在的文件夹路径
    input_path = input("请输入json文件所在的文件夹路径：")
    # 读取文件夹下所有json文件
    jsons = Path(input_path).glob('*.json')
    # 读取所有json文件的内容
    data = []
    for j in jsons:
        with j.open(encoding="utf8") as f:
            data.extend(json.load(f))
    # 将所有json文件的内容合并到一个json文件中
    with open(Path(input_path).parent / "merged.json", 'w', encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
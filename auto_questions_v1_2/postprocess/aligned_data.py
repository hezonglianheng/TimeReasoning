# encoding: utf8
# date: 2025-04-19

"""根据已有文件中的试题，抽取与其对齐的试题"""

import json
from pathlib import Path
import sys
from typing import Any

# 将父目录加入到sys.path中
sys.path.append(str(Path(__file__).resolve().parent.parent))

import proposition.config as config

if __name__ == "__main__":
    src_path = input("请输入作为抽取源的json文件路径：")
    src_path = Path(src_path)
    src_lang = input("请输入作为抽取源的json文件语言：")
    src_lang = src_lang.strip()
    std_path = input("请输入作为标准的json文件路径：")
    std_path = Path(std_path)
    std_lang = input("请输入作为标准的json文件语言：")
    std_lang = std_lang.strip()
    # 读取json文件
    with src_path.open(encoding="utf8") as f:
        src_data: list[dict[str, Any]] = json.load(f) # 待抽取的json文件中的数据
    with std_path.open(encoding="utf8") as f:
        std_data: list[dict[str, Any]] = json.load(f) # 作为标准的json文件中的数据
    std_id: list[str] = list([i[config.ID] for i in std_data]) # 作为抽取标准json文件中试题的ID
    extracted_data = [] # 存储抽取的试题
    for id in std_id:
        new_id = id.replace(std_lang, src_lang) # 将标准试题的ID转换为抽取源试题的ID
        # 在抽取源试题中查找对应的试题
        for i in src_data:
            if i[config.ID] == new_id:
                extracted_data.append(i) # 如果找到，则添加到抽取的试题中
                print(f"抽取试题：{i[config.ID]}成功")
                break
        # print(f"抽取试题：{new_id}失败")
    # 输出json文件
    output_path = src_path.parent / f"align_extracted.json"
    with output_path.open("w", encoding="utf8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)
    print(f"抽取的试题已保存到{output_path}")
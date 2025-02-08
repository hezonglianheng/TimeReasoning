# encoding: utf8
# date: 2025-01-25
# 按照一定的比例和规则筛选问题

import json
from pathlib import Path
import random
import sys
from typing import Any
from functools import reduce

# 将父目录加入到sys.path中
sys.path.append(str(Path(__file__).resolve().parent.parent))

import proposition.config as config

TOTAL_NUM = 600 # 总题目数量
RATE = {
    1: 1,
    2: 2,
    3: 3,
}

random.seed(0) # 设置随机种子

if __name__ == "__main__":
    # 输入json文件路径
    input_path = input("请输入json文件路径：")
    input_path = Path(input_path)
    # 读取json文件
    with input_path.open(encoding="utf8") as f:
        data: list[dict[str, Any]] = json.load(f)
    filtered_data = []
    # 读取语言种类
    lang_type: set[str] = set([i[config.LANGUAGE] for i in data])
    # 按照列表中两个一组为data中元素分组
    groups = [data[i:i + len(lang_type)] for i in range(0, len(data), 2)]
    # 读取场景类型
    scene_type: set[str] = set([i[config.QUES_INFO][config.SCENE_TYPE] for i in data])
    # 根据等级对命题进行筛选
    for level in RATE:
        # num = round(TOTAL_NUM * RATE[level] / sum(RATE.values()))
        level_groups = [group for group in groups if group[0][config.LEVEL] == level]
        for scene in scene_type:
            scene_groups = [group for group in level_groups if group[0][config.QUES_INFO][config.SCENE_TYPE] == scene]
            scene_num = round(len(scene_groups) * (TOTAL_NUM * RATE[level] / sum(RATE.values())) / len(level_groups))
            try:
                scene_data = random.sample(scene_groups, scene_num)
            except ValueError:
                print(f"{scene}在等级{level}的数量{len(scene_groups)}少于所需数量{scene_num}")
                exit(1)
            filtered_data.extend(scene_data)
    # 输出json文件
    result = reduce(lambda x, y: x + y, filtered_data)
    output_path = input_path.parent / f"filtered.json"
    with output_path.open("w", encoding="utf8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
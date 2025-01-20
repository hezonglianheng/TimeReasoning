# encoding: utf8
# usage: 给同一文件中的试题编号，给试题中的group字段编号，去除临时字段group

import json
from pathlib import Path
import sys

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.config as config

GROUP = "group"

if __name__ == "__main__":
    # 输入json文件路径
    file_path = input("请输入json文件路径：")
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)
    
    # 给试题编号
    # 1-13修订：将试题的编号修改为domain-num-language格式
    data = [{config.ID: f"{d[config.DOMAIN]}-{i}-{d[config.LANGUAGE]}", **d} for i, d in enumerate(data, start=1)]

    # 领域模板编号
    # 获得试题中的group字段
    groups: list[str] = []
    for d in data:
        if d[GROUP] not in groups:
            groups.append(d[GROUP])
    # 给groups编号
    group_dict: dict[str, int] = {g: i for i, g in enumerate(groups, start=1)}
    # 获得domain
    domain: str = data[0][config.DOMAIN]
    # 将编号写入试题中
    for d in data:
        d[f"{domain}_{config.ID}"] = group_dict[d[GROUP]]
        del d[GROUP] # 删除group字段
    
    # 将试题写入文件中
    with open(file_path, 'w', encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
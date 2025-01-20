# encoding: utf8
# date: 2025-01-14

import json
from pathlib import Path
import sys
from typing import Any

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.config as config

def simplify(dic: dict[str, Any]) -> dict[str, Any]:
    """从试题字典中抽取必要的字段，返回简化后的字典

    Args:
        dic (dict[str, Any]): 试题字典

    Returns:
        dict[str, Any]: 简化后的试题字典
    """
    simplified = {
        config.ID: dic[config.ID],
        config.DOMAIN: dic[config.DOMAIN],
        config.TEXT: dic[config.TEXT],
        config.QUESTION: dic[config.QUESTION],
        config.OPTIONS: dic[config.OPTIONS],
        config.ANSWER: dic[config.ANSWER],
        config.LEVEL: dic[config.LEVEL],
        config.LANGUAGE: dic[config.LANGUAGE],
    }
    return simplified

if __name__ == "__main__":
    # 输入json文件路径
    file_path = input("请输入json文件路径：")
    # 将输入的文件路径转换为Path对象
    file_path = Path(file_path)
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)

    # 简化试题
    new_data = [simplify(d) for d in data]
    # 写入新的文件中
    new_path = file_path.parent / f"{file_path.stem}_simplified{file_path.suffix}"
    with open(new_path, 'w', encoding="utf8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
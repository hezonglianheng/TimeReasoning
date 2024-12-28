# encoding: utf8
# 用途：将不同语言的试题进行分离，编号后生成新的json文件

import json
from pathlib import Path

LANGUAGE = "lang"

if __name__ == '__main__':
    # 输入json文件路径
    file_path = input("请输入json文件路径：")
    # 输入领域类型
    domain = input("请输入领域类型：")
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)
    # 获得试题中包含的语言类型
    langs: list[str] = []
    for d in data:
        lang: str = d[LANGUAGE]
        if lang not in langs:
            langs.append(lang)
    # 将不同语言的试题分离
    for lang in langs:
        with open(Path(file_path).parent / (Path(file_path).stem + f"_{lang}.json"), 'w', encoding="utf8") as f:
            # 获得特定语言的试题
            spec_lang_data = [d for d in data if d[LANGUAGE] == lang]
            # 给试题编号
            for i, d in enumerate(spec_lang_data, start=1):
                d["No"] = f"{domain}-{i}"
            # 将试题写入文件中
            json.dump(spec_lang_data, f, indent=4, ensure_ascii=False)
# encoding: utf8
# 用途：将不同语言的试题进行分离，生成新的json文件

import json
from pathlib import Path
import sys
import datetime

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.config as config

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
        # 12-29修改：修改为config.LANGUAGE
        lang: str = d[config.LANGUAGE]
        if lang not in langs:
            langs.append(lang)
    # 将不同语言的试题分离
    for lang in langs:
        # 12-29修订：先筛选出特定语言的试题，为后续计算题量做准备，再写入文件
        # 12-29修改：修改为config.LANGUAGE
        spec_lang_data = [d for d in data if d[config.LANGUAGE] == lang]
        # 12-29新增：将领域名称写入试题字典中
        spec_lang_data = [{config.DOMAIN: domain, **d} for d in spec_lang_data]
        # 12-29新增：新的文件名称
        # 1-14修改：文件名称与最终要求靠近
        file_name: str = f"{domain}-{lang}-{len(spec_lang_data)}-{datetime.date.today().isoformat()}.json"
        
        # 12-29修改：使用新的文件名称
        # with open(Path(file_path).parent / (Path(file_path).stem + f"_{lang}.json"), 'w', encoding="utf8") as f:
        with open(Path(file_path).parent / file_name, 'w', encoding="utf8") as f:
            # spec_lang_data = [d for d in data if d[config.LANGUAGE] == lang]
            # 12-29移除：将试题编号部分移除，另外进行试题的编号整理
            '''
            # 给试题编号
            for i, d in enumerate(spec_lang_data, start=1):
                d["No"] = f"{domain}-{i}"
            '''
            # 将试题写入文件中
            json.dump(spec_lang_data, f, indent=4, ensure_ascii=False)
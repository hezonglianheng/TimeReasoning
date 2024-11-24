# encoding: utf8
# author: Qin Yuhang

"""
从试题文件中进行随机抽样的函数与脚本\n
目前能够进行的抽取是按照单选题和多选题的比例进行抽取\n
"""

import config
import random
import json
from pathlib import Path

def main(file_path: str, encoding: str = "utf-8"):
    filep = Path(file_path)
    with filep.open(mode="r", encoding=encoding) as f:
        data: list[dict] = json.load(f)

    # 分成单选题和多选题
    single = [({'index': n} | i) for n, i in enumerate(data) if len(i['answers']) == 1] # 单选题列表
    plural = [({'index': n} | i) for n, i in enumerate(data) if len(i['answers']) > 1] # 多选题列表
    # 按比例采样
    single_sample = random.sample(single, k=round(config.question_num * len(single) / len(data)))
    plural_sample = random.sample(plural, k=round(config.question_num * len(plural) / len(data)))
    # 索引
    single_indexes = [i['index'] for i in single_sample]
    plural_indexes = [i['index'] for i in plural_sample]
    # 未被采样的文件
    single_out = [i for i in single if i['index'] not in single_indexes]
    plural_out = [i for i in plural if i['index'] not in plural_indexes]
    # 文件路径
    sample_file = filep.parent / (filep.stem + "_sample" + filep.suffix)
    others_file = filep.parent / (filep.stem + "_others" + filep.suffix)
    # 存入
    with sample_file.open(mode="w", encoding=encoding) as f:
        json.dump(single_sample + plural_sample, f, ensure_ascii=False, indent=4)
    with others_file.open(mode="w", encoding=encoding) as f:
        json.dump(single_out + plural_out, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=str, help='path to the file')
    parser.add_argument('--encoding', type=str, default='utf-8', help='encoding of the file')
    args = parser.parse_args()
    main(args.path, args.encoding)
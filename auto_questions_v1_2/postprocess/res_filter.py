# encoding: utf8
# date: 2025-03-29

"""根据一定的规则过滤LLM输出结果
"""

import json
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Any
import random

random.seed(0) # 设置随机种子，确保结果可复现

# 定义过滤规则，过滤规则是以字符串表示的Python表达式
FILTER_EXPS: list[str] = [
    "len(item['correct_answer']) > 1", # 答案数量大于1
    "len(item['extracted_answer']) == 1", # 提取的答案数量等于1
    # "search_output(item['model_answer'])", # 输出文本中包含特定的正则表达式模式
]
NUM_LIMIT: int | None = 20 # 答案数量限制，None表示不限制
"""答案数量限制，None表示不限制"""
TAR_PATH: Path # 输出文件夹路径
OUTPUT_SEARCH_PATTERNS = [
    r"只能有一个正确选项", 
    r"答案应该是([A-Z]、)+[A-Z]",
    r"答案应该是([A-Z]、)+[A-Z]",
    r"答案应该是[A-Z]和[A-Z]", 
    r"选项([A-Z]、)+[A-Z][都均].{0,2}正确", 
    r"选项([A-Z]、)+[A-Z][都均].{0,2}错误", 
    r"正确选项是[A-Z]和[A-Z]", 
    r"不正确的选项有([A-Z]、)+[A-Z]", 
    r"选项[A-Z]和[A-Z].{0,2}不正确",
    r"选项[A-Z]和[A-Z].{0,2}错误",
    r"选项[A-Z]和[A-Z]都存在错误", 
    r"选项都(是错误的|是正确的|不正确)", 
    r"根据题目要求，答案应该是完全匹配的一个选项",
    r"更准确的选择", 
    r"未明确说明.*多选题", 
    r"正确答案包括选项([A-Z]、)+和[A-Z]",
    r"单选", 
    r"选择一个", 
    r"最直接", 
    r"只能有一个答案", 
    r"[A-Z]也.{0,2}(不正确|错误)", 
    r"most relevant", 
    r"[A-Z] and [A-Z] are correct", 
    r"Option [A-Z] might be correct", 
    r"Option [A-Z] seemed plausible", 
    r"best match", 
]

# 报告文件记录
MODEL_REPORTS: dict[str, int] = {}
"""模型名称和数量的字典"""
USE_REPORT: bool = True # 是否使用报告文件
"""是否使用报告文件"""

def search_output(output_text: str) -> bool:
    """检查输出文本中是否包含特定的正则表达式模式\n
    该函数用于检查输出文本中是否包含特定的正则表达式模式

    Args:
        output_text (str): 输出文本

    Returns:
        bool: 如果输出文本中包含任何一个模式，则返回True，否则返回False
    """
    return any([re.search(pattern, output_text) for pattern in OUTPUT_SEARCH_PATTERNS])

def answer_filter(json_file: Path):
    """对json文件进行处理，筛选出符合规则的答案

    Args:
        json_file (Path): json文件路径
    """
    with open(json_file, encoding="utf8") as f:
        data: list[dict[str, Any]] = json.load(f)
    # 筛选出符合规则的答案
    filtered_data = [item for item in data if all([eval(exp.strip()) for exp in FILTER_EXPS])]
    if NUM_LIMIT is not None:
        filtered_data = random.sample(filtered_data, min(len(filtered_data), NUM_LIMIT))
    res_path = TAR_PATH / json_file.name
    if res_path.exists():
        res_path.unlink() # 删除已存在的文件
    # 将筛选后的数据写入新的json文件，若为0条数据则返回
    if not filtered_data:
        print(f"处理文件{json_file}，没有符合规则的答案，跳过")
        return
    # 将模型名称添加到MODEL_NAMES中
    # 这里假设json文件名的格式为"{model_name}_{field}.json"
    model_name = json_file.stem
    global MODEL_REPORTS
    if model_name not in MODEL_REPORTS:
        MODEL_REPORTS[model_name] = len(filtered_data)
    # 将筛选后的数据写入新的json文件
    with open(res_path, "w", encoding="utf8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4)
    print(f"处理文件{json_file}，筛选出{len(filtered_data)}条符合规则的答案，保存到{res_path}")

def write_report(dir_path: Path):
    """将模型报告写入文件

    Args:
        dir_path (Path): 输出文件夹路径
    """
    report_path = dir_path / "model_report.json"
    with open(report_path, "w", encoding="utf8") as f:
        json.dump(MODEL_REPORTS, f, ensure_ascii=False, indent=4)
    print(f"模型报告已保存到{report_path}")

def main():
    # 输入包含json文件的文件夹的路径
    dir_path = Path(input("请输入包含json文件的文件夹的路径："))
    # 输入领域类型
    field = input("请输入领域类型：")
    # 获得输出路径
    global TAR_PATH
    TAR_PATH = Path(input("请输入输出文件夹的路径："))
    # 创建输出文件夹
    TAR_PATH.mkdir(parents=True, exist_ok=True)
    # 在dir_path下按照规则筛选json文件
    json_files = list(dir_path.glob(f"*_{field}_*.json"))
    if not json_files:
        print(f"没有找到符合条件的json文件，退出")
        return
    # 使用多线程处理json文件
    with ThreadPoolExecutor() as executor:
        for f in json_files:
            try:
                executor.submit(answer_filter, f)
            except Exception as e:
                print(f"处理文件{f}时发生错误：{e}")
    # 写入模型报告
    if USE_REPORT:
        write_report(TAR_PATH)

if __name__ == "__main__":
    main()
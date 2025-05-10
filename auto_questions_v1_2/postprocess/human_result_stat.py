# encoding: utf8
# date: 2025-05-08

import pandas as pd
import json
import sys
from pathlib import Path
from typing import Any, Literal
from string import ascii_uppercase
from collections import Counter

# 将上级目录加入到sys.path中
sys.path.append(str(Path(__file__).absolute().parents[1].as_posix()))

import proposition.config as config

QUESTION = "题目"
ANSWER = "答案"
HUMAN_NAMES =  ["程雅宁", "郭子煊", "李抒桦", "李璇", "林华晖", "吴楚格", "夏聆溪", "岳君佳俞"]
JSON_DATA: list[dict[str, Any]] = []
TAG_COUNTER = Counter()
ALL_TAG_COUNTER = Counter()

def get_question_type(question_text: str) -> Literal["correct", "incorrect", "precise"]:
    """判断题目类型

    Args:
        question_text: 题目文本

    Returns:
        str: 返回值类型为字符串，表示题目类型
        - "correct": 正确选项
        - "incorrect": 错误选项
        - "precise": 精确选项
    """
    if question_text == config.LANG_CONFIG["zh"][config.ASK_RIGHT] or question_text == config.LANG_CONFIG["en"][config.ASK_RIGHT]:
        return "correct"
    elif question_text == config.LANG_CONFIG["zh"][config.ASK_WRONG] or question_text == config.LANG_CONFIG["en"][config.ASK_WRONG]:
        return "incorrect"
    else:
        return "precise"

def get_wrong_answers(row: pd.Series) -> list[str]:
    """获取错误答案

    Args:
        row (pd.Series): 一行数据，表示一道题目的所有人类答案

    Returns:
        list[str]: 返回错误答案的列表
    """
    row_answer: set[str] = set(row[ANSWER])
    wrong_answers: list[str] = []
    for name in HUMAN_NAMES:
        name_answer: set[str] = set(row[name])
        set1 = name_answer - row_answer
        set2 = row_answer - name_answer
        wrong_answers.extend(list(set1))
        wrong_answers.extend(list(set2))
    return list(set(wrong_answers))

def get_wrong_answer_tag(question_id: str, wrong_answers: list[str]):
    """获取并统计错误答案的标签

    Args:
        question_id (str): 题目id
        wrong_answers (list[str]): 错误答案列表

    Raises:
        ValueError: 如果题目类型未知，则抛出异常
    """
    global TAG_COUNTER
    info_with_id = [i for i in JSON_DATA if i[config.ID] == question_id]
    assert len(info_with_id) == 1, f"检索id为{question_id}的题目时，返回了{len(info_with_id)}条数据，请检查题目id是否正确"
    info = info_with_id[0]
    question_text = info[config.QUESTION]
    question_type = get_question_type(question_text)
    question_tags = info[config.QUES_INFO][config.QUESTION_TYPE]
    if question_type == "precise":
        assert len(question_tags) == 1, f"题目{question_id}的题目类型为精确选项，但返回了{len(question_tags)}个标签，请检查题目类型是否正确"
        question_tags = question_tags[0]
        TAG_COUNTER[question_tags] += len(wrong_answers)
        ALL_TAG_COUNTER[question_tags] += len(info[config.OPTIONS])
    elif question_type == "correct" or question_type == "incorrect":
        for i in range(len(question_tags)):
            ALL_TAG_COUNTER[question_tags[i]] += 1
        for ans in wrong_answers:
            idx = ascii_uppercase.index(ans)
            if idx < len(question_tags):
                curr_tag = question_tags[idx]
                TAG_COUNTER[curr_tag] += 1
    else:
        raise ValueError(f"未知的题目类型: {question_type}")

def question_stat(row: pd.Series):  
    question_id: str = row[QUESTION]
    wrong_answers: list[str] = get_wrong_answers(row)
    get_wrong_answer_tag(question_id, wrong_answers)

def main():
    global JSON_DATA
    # load the result excel
    result_excel = input("请输入结果excel文件路径: ")
    sheet_name = input("请输入sheet名称: ")
    sheet_name = sheet_name if len(sheet_name) > 0 else 1
    df = pd.read_excel(result_excel, sheet_name=sheet_name)
    # 除去df的最后一行
    df = df.iloc[:-1, :]
    # load the json file
    json_path = input("请输入json文件路径: ")
    with open(json_path, "r", encoding="utf-8") as f:
        JSON_DATA = json.load(f)
    # 遍历df的每一行
    for index, row in df.iterrows():
        question_stat(row)
    # 输出统计结果
    human_acc = {t: 1 - (TAG_COUNTER[t] / ALL_TAG_COUNTER[t]) for t in TAG_COUNTER}
    res_dir = input("请输入结果文件夹路径: ")
    res_dir = Path(res_dir)
    res_dir.mkdir(parents=True, exist_ok=True)
    # 将统计结果保存到文件
    with open(res_dir / "stat.json", "w", encoding="utf-8") as f:
        json.dump(human_acc, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
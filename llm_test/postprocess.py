# encoding: utf8
# date: 2024-11-15
# 对生成结果进行后处理

import config
import pandas as pd
import json
from pathlib import Path
from string import ascii_uppercase
import re
from typing import Literal
import operator

def get_answer(output: str) -> str:
    """从输出中提取答案

    Args:
        output (str): 生成的文本

    Returns:
        str: 答案
    """
    if output[-1] in ascii_uppercase:
        return output[-1]
    elif (found := re.findall(r'答案是[A-Z][:：]', output)):
        if found:
            return found[-1][-2]
        else:
            return ""
    elif (found := re.findall(r'答案是[:：]\s[A-Z]', output)):
        if found:
            return found[-1][-1]
        else:
            return ""
    elif (found := re.search(r'[A-Z]:\s.', output)):
        return found.group()[0]
    else:
        return ""

def get_score(pd: pd.DataFrame, mode: Literal['strict', 'fuzzy']='strict') -> dict[str, float]:
    """计算得分

    Args:
        pd (pd.DataFrame): 整理的数据
        mode (Literal[&#39;strict&#39;, &#39;fuzzy&#39;], optional): 计算得分的模式. 'strict'表示严格匹配，'fuzzy'表示模糊匹配. Defaults to 'strict'.

    Returns:
        dict[str, float]: 得分
    """

    def char_contain(chars: str, string: str) -> bool:
        for char in chars:
            if char in string:
                return True
        return False

    score_dict: dict[str, float] = dict()
    for model in config.model_names:
        answer_column = pd['answer']
        model_column = pd[model]
        if mode == 'strict':
            score = sum(map(operator.eq, answer_column, model_column)) / len(answer_column)
        else:
            score = sum(map(char_contain, model_column, answer_column)) / len(answer_column)
        score_dict[model] = score
    
    return score_dict

def main(file: str):
    path = Path(file) # 转换为Path对象
    with path.open(mode='r', encoding='utf8') as f:
        data: list[dict] = json.load(f)
    records: list[dict] = [] # 保存处理后的结果
    for item in data:
        # item题目的基础信息
        text = item['info']['text']
        question = item['info']['question']
        option_a = item['info']['options']['A']
        option_b = item['info']['options']['B']
        option_c = item['info']['options']['C']
        option_d = item['info']['options']['D']
        answer = item['info']['answers']
        record = {
            'text': text,
            'question': question,
            'A': option_a,
            'B': option_b,
            'C': option_c,
            'D': option_d,
            'answer': ';'.join(answer)
        }
        for res in item['results']:
            for k, v in res.items():
                output = v['choices'][0]['message']['content']
                record[k] = get_answer(output)
        records.append(record)

    excel_path = path.with_suffix('.xlsx')
    excel_writer = pd.ExcelWriter(excel_path)
    df = pd.DataFrame(records)
    df.to_excel(excel_writer, index=False, sheet_name='LLM结果')

    score_strict = get_score(df, 'strict')
    score_fuzzy = get_score(df, 'fuzzy')
    score_strict['模型'] = 'strict'
    score_fuzzy['模型'] = 'fuzzy'
    # 答案只有1个的dataframe
    single_df = df.loc[df['answer'].str.len() == 1]
    score_single_strict = get_score(single_df, 'strict')
    plural_df = df.loc[df['answer'].str.len() > 1]
    score_plural_strict = get_score(plural_df, 'fuzzy')
    score_single_strict['模型'] = 'single_strict'
    score_plural_strict['模型'] = 'plural_fuzzy'
    score_df = pd.DataFrame([score_strict, score_fuzzy, score_single_strict, score_plural_strict])
    # score_df = pd.DataFrame([score_strict, score_fuzzy]).transpose()
    score_df.to_excel(excel_writer, index=False, sheet_name='得分')

    excel_writer.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='输入的json文件')
    args = parser.parse_args()
    main(args.file)
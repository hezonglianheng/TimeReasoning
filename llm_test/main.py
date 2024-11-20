# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-15

import config
import callapi
from tqdm import tqdm
import json
import os
from typing import Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def item2question(item: dict[str, Any]) -> str:
    """将item转换为问题

    Args:
        item (dict[str, Any]): 问题的item

    Returns:
        str: 问题的文本
    """
    text: str = item['text'] # 问题的文本
    question: str = item['question'] # 问题的答案
    options: dict[str, str] = item['options'] # 问题的选项
    options_str: str = " ".join([f"{k}: {v}" for k, v in options.items()])
    return f"{text}\n请问：{question}\n{options_str}"

def main(file: str, use_shot: bool = False) -> None:
    # 读取文件
    path = Path(file)
    with path.open(mode="r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 获取api回答
    results: list[dict[str, Any]] = []
    for item in tqdm(data, desc="获取api回答", total=len(data)):
        # 生成问题
        question = item2question(item)
        # 选择是否使用few-shot
        if use_shot:
            text = config.system_text + f"{config.few_shot}\n{question}"
        else:
            text = config.system_text + question
        # 调用api
        question_results: list[dict[str, dict]] = []
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            for model_name in config.model_names:
                # 提交任务
                future = executor.submit(callapi.callapi, text, model_name)
                # 获取结果
                question_results.append({model_name: future.result()})
        
        results.append({"info": item, "results": question_results})

    # 保存结果
    if use_shot: # 使用few-shot
        new_path = path.with_name(f"{path.stem}_results_shot.json")
    else: # 不使用few-shot
        new_path = path.with_name(f"{path.stem}_results.json")
    with new_path.open(mode="w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="调用api获取结果")
    parser.add_argument("file", type=str, help="输入的文件")
    parser.add_argument("--use_shot", action="store_true", help="是否使用few-shot")
    args = parser.parse_args()
    main(args.file, args.use_shot)
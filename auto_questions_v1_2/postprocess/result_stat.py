# encoding: utf8

"""对模型输出的结果进行统计分析"""

import json
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(str(Path(__file__).absolute().parents[1].as_posix()))

import proposition.config as config

CORRECT_ANSWER = "correct_answer"
EXTRACTED_ANSWER = "extracted_answer"

def answer_ignore(records: list[dict]) -> str:
    """统计忽略正确选项的情况

    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """

    def is_ignore(correct: list[str], extract: list[str]) -> bool:
        """判断提取的答案是否忽略了正确选项

        Args:
            correct (list[str]): 正确答案
            extract (list[str]): 提取的答案

        Returns:
            bool: 是否忽略了正确选项
        """
        if len(correct) < 2:
            return False
        diff = set(correct) - set(extract)
        return len(diff) > 0

    # 提取多选题
    multiple_choice: list[dict] = [r for r in records if len(r[CORRECT_ANSWER]) > 1]
    # 判断是否忽略了正确选项
    ignore_judges: list[bool] = [is_ignore(i[CORRECT_ANSWER], i[EXTRACTED_ANSWER]) for i in multiple_choice]
    # 统计忽略正确选项的比例
    ratio = sum(ignore_judges) / len(ignore_judges)
    # 生成报告
    report: str = f"""忽略正确选项统计：
    多选题数量：{len(multiple_choice)}
    忽略正确选项的数量：{sum(ignore_judges)}
    忽略正确选项的比例：{ratio}"""
    return report

def main():
    # 输入json文件路径
    file_path = input("请输入json文件路径：")
    file_path = Path(file_path)
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)

    reports = [
        answer_ignore(data), 
    ]

    # 输出报告
    print("\n\n".join(reports))
    report_path = file_path.with_name(file_path.stem + "_report.txt")
    with open(report_path, "w", encoding="utf8") as f:
        f.write("\n\n".join(reports))

if __name__ == "__main__":
    main()
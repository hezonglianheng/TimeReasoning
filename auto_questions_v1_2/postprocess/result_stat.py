# encoding: utf8

"""对模型输出的结果进行统计分析"""

import json
import sys
from pathlib import Path
from collections import Counter

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
        diff = set(correct) - set(extract)
        return len(diff) > 0

    # 判断是否忽略了正确选项
    ignore_judges: list[bool] = [is_ignore(i[CORRECT_ANSWER], i[EXTRACTED_ANSWER]) for i in records]
    # 统计忽略正确选项的比例
    ratio = sum(ignore_judges) / len(ignore_judges)
    # 生成报告
    report: str = f"""忽略正确选项统计：
    忽略正确选项的数量：{sum(ignore_judges)}
    忽略正确选项的比例：{ratio}"""
    return report

def extra_answer(records: list[dict]) -> str:
    """统计多余答案的情况

    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """

    def is_extra(correct: list[str], extract: list[str]) -> bool:
        """判断提取的答案是否多余

        Args:
            correct (list[str]): 正确答案
            extract (list[str]): 提取的答案

        Returns:
            bool: 是否多余
        """
        diff = set(extract) - set(correct)
        return len(diff) > 0

    # 判断是否多余
    extra_judges: list[bool] = [is_extra(i[CORRECT_ANSWER], i[EXTRACTED_ANSWER]) for i in records]
    # 统计多余答案的比例
    ratio = sum(extra_judges) / len(extra_judges)
    # 生成报告
    report: str = f"""多余答案统计：
    多余答案的数量：{sum(extra_judges)}
    多余答案的比例：{ratio}"""
    return report

def info_analysis(records: list[dict]) -> str:
    """对试题的详细信息进行分析

    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 分析报告
    """

    def scene_type(records: list[dict]) -> str:
        """统计各个场景类型的数量和正确率

        Args:
            records (list[dict]): 数据记录

        Returns:
            str: 场景类型统计报告
        """
        scene = Counter()
        cor_scene = Counter()
        for i, (r, s) in enumerate(zip(records, standard_data), start=1):
            assert r[config.ID] == s[config.ID], f"第{i}条数据记录与标准答案不匹配"
            scene[s[config.QUES_INFO][config.SCENE_TYPE]] += 1
            if r["is_cor"]:
                cor_scene[s[config.QUES_INFO][config.SCENE_TYPE]] += 1

        report = "场景类型正确数量及正确率统计：\n\t" + "\n\t".join([f"{k}: 数量{v}, 正确数量{cor_scene[k]}, 正确率{cor_scene[k]/v}" for k, v in scene.items()])
        return report

    def question_type(records: list[dict]) -> str:
        """统计各个问题类型的数量和正确率

        Args:
            records (list[dict]): 数据记录

        Returns:
            str: 问题类型统计报告
        """
        qtype = Counter()
        cor_qtype = Counter()
        for i, (r, s) in enumerate(zip(records, standard_data), start=1):
            assert r[config.ID] == s[config.ID], f"第{i}条数据记录与标准答案不匹配"
            qtypes: list[str] = s[config.QUES_INFO][config.QUESTION_TYPE]
            for q in qtypes:
                qtype[q] += 1
                if r["is_cor"]:
                    cor_qtype[q] += 1

        report = "问题类型正确数量及正确率统计：\n\t" + "\n\t".join([f"{k}: 数量{v}, 正确数量{cor_qtype[k]}, 正确率{cor_qtype[k]/v}" for k, v in qtype.items()])
        return report
        
    standard_path = Path(input("请输入标准答案文件路径："))
    with standard_path.open(encoding="utf8") as f:
        standard_data: list[dict] = json.load(f)

    reports = [
        scene_type(records),
        question_type(records),
    ]
    return "\n\n".join(reports)

def main():
    # 输入json文件路径
    file_path = input("请输入json文件路径：")
    file_path = Path(file_path)
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)

    reports = [
        answer_ignore(data), 
        # 2-12新增：统计多余答案的情况和对试题的详细信息进行分析
        extra_answer(data),
        info_analysis(data),
    ]

    # 输出报告
    print("\n\n".join(reports))
    report_path = file_path.with_name(file_path.stem + "_report.txt")
    with open(report_path, "w", encoding="utf8") as f:
        f.write("\n\n".join(reports))

if __name__ == "__main__":
    main()
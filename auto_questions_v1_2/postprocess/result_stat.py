# encoding: utf8
# date: 2025-02-12

"""对模型输出的结果进行统计分析"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from functools import reduce

# 将上级目录加入到sys.path中
sys.path.append(str(Path(__file__).absolute().parents[1].as_posix()))

import proposition.config as config

CORRECT_ANSWER = "correct_answer"
EXTRACTED_ANSWER = "extracted_answer"
ENGLISH_SCENARIO = {
    "线性时间场景": "Linear Scenario", 
    "循环时间场景": "Cyclic Scenario", 
}

# 程序目前支持的语言
LANGS = [config.LANG_CONFIG[n][config.LANG_NAME] for n in config.CURR_LANGS]

MODEL_NAMES = [
    "claude-3-5-sonnet-20241022", 
    # "deepseek-chat",
    # "deepseek-r1-distill-qwen-32b", 
    "deepseek-reasoner", 
    # "glm-4-plus", 
    # "glm-zero-preview", 
    "gpt-4o", 
    # "Llama-3.3-70B-Instruct", 
    "o1-mini", 
    "o1-preview", 
    # "o3-mini", 
    "qwen-25-72B", 
    "qwen-max", 
    # "qwq-32B", 
]

def answer_ignore(records: list[dict]) -> dict[str, dict[str, float]]:
    """统计忽略正确选项的情况

    Args:
        records (list[dict]): 数据记录

    Returns:
        dict[str, dict[str, float]]: 统计报告
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
    report = {"miss": {"ratio": ratio, "num": sum(ignore_judges)}}
    return report

def extra_answer(records: list[dict]) -> dict[str, dict[str, float]]:
    """统计多余答案的情况

    Args:
        records (list[dict]): 数据记录

    Returns:
        dict[str, dict[str, float]]: 统计报告
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
    report: dict = {"extra": {"ratio": ratio, "num": sum(extra_judges)}}
    return report

def info_analysis(records: list[dict], standard_path: Path) -> dict[str, dict[str, float]]:
    """对试题的详细信息进行分析

    Args:
        records (list[dict]): 数据记录
        standard_path (Path): 标准答案文件路径

    Returns:
        dict[str, dict[str, float]]: 试题详细信息分析报告
    """

    def scene_type(records: list[dict]) -> dict[str, dict[str, float]]:
        """统计各个场景类型的数量和正确率

        Args:
            records (list[dict]): 数据记录

        Returns:
            dict[str, dict[str, float]]: 场景各类型正确率
        """
        scene = Counter()
        cor_scene = Counter()
        for i, (r, s) in enumerate(zip(records, standard_data), start=1):
            assert r[config.ID] == s[config.ID], f"第{i}条数据记录与标准答案不匹配"
            scene[s[config.QUES_INFO][config.SCENE_TYPE]] += 1
            if r["is_cor"]:
                cor_scene[s[config.QUES_INFO][config.SCENE_TYPE]] += 1

        # report = "场景类型正确数量及正确率统计：\n\t" + "\n\t".join([f"{k}: 数量{v}, 正确数量{cor_scene[k]}, 正确率{cor_scene[k]/v}" for k, v in scene.items()])
        report = {ENGLISH_SCENARIO[k]: cor_scene[k]/v for k, v in scene.items()}
        return {"knowledge_attribute": report}

    def question_type(records: list[dict]) -> dict[str, dict[str, float]]:
        """统计各个问题类型的数量和正确率

        Args:
            records (list[dict]): 数据记录

        Returns:
            dict[str, dict[str, float]]: 问题类型正确率
        """
        qtype = Counter()
        cor_qtype = Counter()
        for i, (r, s) in enumerate(zip(records, standard_data), start=1):
            assert r[config.ID] == s[config.ID], f"第{i}条数据记录与标准答案不匹配"
            question: str = r[config.QUESTION]
            curr_type = "Precise Event"
            if question == config.LANG_CONFIG["zh"][config.ASK_RIGHT] or question == config.LANG_CONFIG["en"][config.ASK_RIGHT]:
                curr_type = "Correct Statements"
            elif question == config.LANG_CONFIG["zh"][config.ASK_WRONG] or question == config.LANG_CONFIG["en"][config.ASK_WRONG]:
                curr_type = "Incorrect Statements"
            qtype[curr_type] += 1
            if r["is_cor"]:
                cor_qtype[curr_type] += 1

        report = {k: cor_qtype[k]/v for k, v in qtype.items()}
        return {"question_type": report}
    
    def question_tag(records: list[dict]) -> dict[str, dict[str, float]]:
        """统计各个问题标签的数量和正确率

        Args:
            records (list[dict]): 数据记录

        Returns:
            dict[str, dict[str, float]]: 问题类型正确率
        """
        qtag = Counter()
        cor_qtag = Counter()
        for i, (r, s) in enumerate(zip(records, standard_data), start=1):
            assert r[config.ID] == s[config.ID], f"第{i}条数据记录与标准答案不匹配"
            qtags: list[str] = s[config.QUES_INFO][config.QUESTION_TYPE]
            for q in qtags:
                qtag[q] += 1
                if r["is_cor"]:
                    cor_qtag[q] += 1

        # report = "问题类型正确数量及正确率统计：\n\t" + "\n\t".join([f"{k}: 数量{v}, 正确数量{cor_qtype[k]}, 正确率{cor_qtype[k]/v}" for k, v in qtype.items()])
        report = {k: cor_qtag[k]/v for k, v in qtag.items()}
        return {"question_tag": report}
        
    # standard_path = Path(input("请输入标准答案文件路径："))
    with standard_path.open(encoding="utf8") as f:
        standard_data: list[dict] = json.load(f)

    reports = [
        scene_type(records),
        question_type(records),
        question_tag(records),
    ]
    # return "\n\n".join(reports)
    report = {}
    for r in reports:
        report.update(r)
    return report

def reports4single_model(dir: Path, model_name: str, field: str, lang: str, standard_path: Path) -> dict[str, dict[str, float]] | None:
    """对单个模型的结果进行统计分析

    Args:
        dir (Path): 结果所在文件夹路径
        model_name (str): 模型名称
        field (str): 领域类型
        lang (str): 语言参数
        standard_path (Path): 标准答案文件路径

    Returns:
        dict[str, dict[str, float]]: 统计报告
    """
    # 输入json文件路径
    # file_path = input("请输入json文件路径：")
    # file_path = Path(file_path)
    # 构建文件路径
    file_path = dir / f"{model_name}_{field}_{lang}.json"
    if not file_path.exists():
        print(f"文件{file_path}不存在，跳过")
        return None
    # 读取json文件
    with open(file_path, encoding="utf8") as f:
        data: list[dict] = json.load(f)

    reports = [
        # 暂时不统计漏选、多选的情况
        # answer_ignore(data), 
        # 2-12新增：统计多余答案的情况和对试题的详细信息进行分析
        # extra_answer(data),
        info_analysis(data, standard_path),
    ]

    """
    # 输出报告
    print("\n\n".join(reports))
    report_path = file_path.parents[1] / (file_path.stem + "_report.txt")
    with open(report_path, "w", encoding="utf8") as f:
        f.write("\n\n".join(reports))
    """
    # 报告合并
    report = {}
    for r in reports:
        report.update(r)
    return report

def lang_report(dir_path: Path, lang: str, field: str) -> dict[str, dict[str, float]]:
    """对不同语言的结果进行统计分析

    Args:
        dir_path (Path): 包含json文件的文件夹的路径
        lang (str): 语言参数
        field (str): 领域类型

    Returns:
        dict[str, dict[str, float]]: 统计报告
    """
    # 输入标准答案文件路径
    standard_path = Path(input(f"请输入语言{lang}标准答案文件路径："))
    # 遍历模型类型
    total_report = defaultdict(dict)
    for m in MODEL_NAMES:
        if (report := reports4single_model(dir_path, m, field, lang, standard_path)) is None:
            continue
        for k1 in report:
            for k2 in report[k1]:
                total_report[k1][f"{k2}_{lang}_{m}"] = report[k1][k2]
    return total_report

def main():
    # 输入包含json文件的文件夹的路径
    dir_path = Path(input("请输入包含json文件的文件夹的路径："))
    # 输入领域类型
    field = input("请输入领域类型：")
    reports = [lang_report(dir_path, lang, field) for lang in LANGS]
    report = {}
    for key in reports[0]:
        curr_report = reduce(lambda x, y: x | y, [r[key] for r in reports])
        report[key] = curr_report

    res_path = dir_path.parents[1] / (field + "_report.json")
    with res_path.open("w", encoding="utf8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
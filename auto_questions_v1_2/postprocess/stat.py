# encoding: utf8
# 用于统计时间推理题的数据情况

import statistics
from pathlib import Path
from collections import Counter
import sys
from functools import reduce

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import scene
# 1-11新增：引入配置文件
import proposition.config

def basic_stat(data: list[int]) -> tuple[int, int, float, float]:
    """基础统计函数，统计数据的最大值、最小值、均值和方差

    Args:
        data (list[int]): 数据

    Returns:
        tuple[int, int, float, float]: 最大值、最小值、均值和方差
    """
    maximum = max(data) # 最大值
    minimum = min(data) # 最小值
    mean = statistics.mean(data) # 均值
    variance = statistics.variance(data) # 方差
    return maximum, minimum, mean, variance

def init_num_stat(records: list[dict]) -> str:
    """初始命题统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    # 1-11修订：改为读取text.split()的长度
    data: list[int] = [len(r["text"].split()) for r in records]
    # data: list[int] = [len(r["statements"]) for r in records]
    # 统计数据
    maximum, minimum, mean, variance = basic_stat(data)
    # 生成报告
    report: str = f"""初始命题统计：
    最大值：{maximum}
    最小值：{minimum}
    均值：{mean}
    方差：{variance}"""
    return report

def chain_length_stat(records: list[dict]) -> str:
    """链长统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    # 1-11修订：应数据结构修改要求修改数据读取方式
    # data: list[int] = [r[scene.CHAIN_LENGTH] for r in records]
    data: list[int] = [r[proposition.config.QUES_INFO][scene.CHAIN_LENGTH] for r in records]
    # 统计数据
    maximum, minimum, mean, variance = basic_stat(data)
    # 生成报告
    report: str = f"""链长统计：
    最大值：{maximum}
    最小值：{minimum}
    均值：{mean}
    方差：{variance}"""
    return report

def scene_type_stat(records: list[dict]) -> str:
    """场景类型统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    # 1-11修订：应数据结构修改要求修改数据读取方式
    # data: list[str] = [r[scene.SCENE_TYPE] for r in records]
    data: list[str] = [r[proposition.config.QUES_INFO][scene.SCENE_TYPE] for r in records]
    # 统计数据
    counter = Counter(data)
    # 生成报告
    report: str = "场景类型统计：\n\t" + "\n\t".join([f"{k}：{v}" for k, v in counter.items()])
    return report

def level_stat(records: list[dict]) -> str:
    """难度统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    data: list[int] = [r[scene.LEVEL] for r in records]
    # 统计数据
    counter = Counter(data)
    # 将counter中的键值对按照键的大小排序
    counter = dict(sorted(counter.items()))
    mean = statistics.mean(data)
    variance = statistics.variance(data)
    # 生成报告
    report: str = f"\t难度统计：\n\t平均值：{mean}\n\t方差：{variance}\n\t各难度等级试题数：\n\t" 
    report += "\n\t".join([f"{k}：{v}" for k, v in counter.items()])
    return report

def statements_tag_stat(records: list[dict]) -> str:
    """命题类型标签统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    data: list[list[str]] = [r[proposition.config.QUES_INFO][proposition.config.STATEMENTS_TYPE] for r in records]
    # 将二维列表转换为一维列表
    data = reduce(lambda x, y: x + y, data)
    # 统计数据
    counter = Counter(data)
    result = counter.most_common()
    # 生成报告
    report: str = "命题类型标签统计：\n\t" + "\n\t".join([f"{k}：{v}" for k, v in result])
    return report

# 1-18修改：修改问题类型标签统计函数逻辑
def question_tag_stat(records: list[dict]) -> str:
    """问题类型标签统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    """
    # 尝试读取typetags数据，如果没有则返回空统计报告
    try:
        example_tag = records[0][proposition.config.QUESTION_TYPE]
    except KeyError:
        return ""
    """
    # 读取typetags数据
    # 1-11修订：应数据结构修改要求修改数据读取方式
    # data: list[str] = [tag for r in records for tag in r["typetags"]]
    # data: list[list[str]] = [tag for r in records for tag in r[proposition.config.QUES_INFO][proposition.config.QUESTION_TYPE]]
    data: list[list[str]] = [r[proposition.config.QUES_INFO][proposition.config.QUESTION_TYPE] for r in records]
    # 将二维列表转换为一维列表
    data = reduce(lambda x, y: x + y, data)
    # 统计数据
    counter = Counter(data)
    result = counter.most_common()
    # 生成报告
    report: str = "问题类型标签统计：\n\t" + "\n\t".join([f"{k}：{v}" for k, v in result])
    return report

def answer_num_stat(records: list[dict]) -> str:
    """选项数量统计
    
    Args:
        records (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    # 读取数据
    data: list[int] = [len(r[proposition.config.ANSWER]) for r in records]
    # 统计每个数量的试题量
    counter = Counter(data)
    sorted_data = counter.most_common()
    # 生成报告
    report: str = "选项数量统计：\n\t" + "\n\t".join([f"选项数量{k}：{v}" for k, v in sorted_data])
    return report

def stat(data: list[dict]) -> str:
    """统计数据
    
    Args:
        data (list[dict]): 数据记录

    Returns:
        str: 统计报告
    """
    reports = [
        init_num_stat(data), 
        # 1-22新增：增加选项数量统计
        answer_num_stat(data),
        chain_length_stat(data), 
        scene_type_stat(data), 
        level_stat(data), 
        statements_tag_stat(data),
        question_tag_stat(data), 
    ]
    return "\n\n".join(reports)

if __name__ == "__main__":
    import json
    # 输入数据文件名
    data_file = input("请输入数据文件名：")
    # 读取数据
    with open(Path(data_file), "r", encoding="utf8") as f:
        data = json.load(f)
    # 统计数据
    report = stat(data)
    # 在控制台输出报告
    print(report)
    # 输出到文件
    with open(Path(data_file).parent / "data_report.txt", "w", encoding="utf8") as f:
        f.write(report)